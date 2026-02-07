"""
Tests for Phase 3: LLM extraction pipeline.

Run inside Docker:
    docker exec eezy_peezy_backend python -m pytest tests/test_extraction.py -v
"""

import json
import uuid
from decimal import Decimal
from unittest.mock import patch, MagicMock

import anthropic
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db, SessionLocal
from app.core.models import (
    Order, OrderLineItem, IncomingEmail, EmailAttachment, Product,
)
from app.services.extraction_service import (
    prepare_email_content,
    parse_excel_to_text,
    extract_order_from_email,
    create_order_from_extraction,
    process_single_email,
    process_unprocessed_emails,
    _parse_extraction_json,
    ExtractionError,
)

client = TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# Canned extraction response matching the schema from MASTER_BUILD.md
MOCK_EXTRACTION = {
    "customer_name": {"value": "Test Customer Pty Ltd", "confidence": 0.98},
    "po_number": {"value": "PO-12345", "confidence": 0.99},
    "po_date": {"value": "2026-02-07", "confidence": 0.95},
    "delivery_date": {"value": None, "confidence": 0.0},
    "special_instructions": {"value": "Handle with care", "confidence": 0.90},
    "line_items": [
        {
            "product_code": {"value": "LOCAP2", "confidence": 0.96},
            "description": {"value": "LOUVRE END CAP 152mm", "confidence": 0.94},
            "quantity": {"value": 1000, "confidence": 0.99},
            "colour": {"value": "Black", "confidence": 0.90},
            "unit_price": {"value": 1.32, "confidence": 0.88},
        },
        {
            "product_code": {"value": "UNKNOWNPROD", "confidence": 0.70},
            "description": {"value": "Unknown widget", "confidence": 0.65},
            "quantity": {"value": 500, "confidence": 0.95},
            "colour": {"value": "White", "confidence": 0.80},
            "unit_price": {"value": 2.50, "confidence": 0.75},
        },
    ],
    "overall_confidence": 0.92,
}


def _create_test_email(db: Session, processed: bool = False) -> IncomingEmail:
    """Helper to create a test email in the database."""
    email = IncomingEmail(
        gmail_message_id=f"test-msg-{uuid.uuid4().hex[:8]}",
        sender="test@example.com",
        subject="Purchase Order PO-12345",
        body_text="Please process this order for 1000x LOCAP2 Black.",
        processed=processed,
    )
    db.add(email)
    db.commit()
    db.refresh(email)
    return email


def _cleanup_test_data(db: Session, email_ids: list[int]):
    """Clean up test emails and associated orders."""
    for eid in email_ids:
        orders = db.query(Order).filter(Order.email_id == eid).all()
        for order in orders:
            db.query(OrderLineItem).filter(OrderLineItem.order_id == order.id).delete()
            db.delete(order)
        db.query(EmailAttachment).filter(EmailAttachment.email_id == eid).delete()
        db.query(IncomingEmail).filter(IncomingEmail.id == eid).delete()
    db.commit()


# ── Model Tests ──────────────────────────────────────────────────────

class TestOrderModels:
    def test_create_order(self, db):
        email = _create_test_email(db)
        try:
            order = Order(
                email_id=email.id,
                status="pending",
                customer_name="Test Co",
                po_number="PO-001",
                extraction_confidence=Decimal("0.95"),
            )
            db.add(order)
            db.commit()
            db.refresh(order)

            assert order.id is not None
            assert order.status == "pending"
            assert order.customer_name == "Test Co"
            assert order.email_id == email.id

            # Clean up
            db.delete(order)
            db.commit()
        finally:
            _cleanup_test_data(db, [email.id])

    def test_create_order_with_line_items(self, db):
        email = _create_test_email(db)
        try:
            order = Order(
                email_id=email.id,
                status="pending",
                customer_name="Test Co",
            )
            db.add(order)
            db.flush()

            item = OrderLineItem(
                order_id=order.id,
                line_number=1,
                product_code="LOCAP2",
                quantity=100,
                unit_price=Decimal("1.32"),
                line_total=Decimal("132.00"),
            )
            db.add(item)
            db.commit()
            db.refresh(order)

            assert len(order.line_items) == 1
            assert order.line_items[0].product_code == "LOCAP2"
            assert order.line_items[0].quantity == 100

            # Clean up
            db.query(OrderLineItem).filter(OrderLineItem.order_id == order.id).delete()
            db.delete(order)
            db.commit()
        finally:
            _cleanup_test_data(db, [email.id])

    def test_cascade_delete(self, db):
        email = _create_test_email(db)
        try:
            order = Order(email_id=email.id, status="pending")
            db.add(order)
            db.flush()

            item = OrderLineItem(
                order_id=order.id,
                line_number=1,
                product_code="TEST",
                quantity=1,
            )
            db.add(item)
            db.commit()

            order_id = order.id
            db.delete(order)
            db.commit()

            # Line items should be cascade-deleted
            remaining = db.query(OrderLineItem).filter(
                OrderLineItem.order_id == order_id
            ).count()
            assert remaining == 0
        finally:
            _cleanup_test_data(db, [email.id])

    def test_order_email_relationship(self, db):
        email = _create_test_email(db)
        try:
            order = Order(email_id=email.id, status="pending")
            db.add(order)
            db.commit()
            db.refresh(order)

            assert order.email is not None
            assert order.email.id == email.id

            db.delete(order)
            db.commit()
        finally:
            _cleanup_test_data(db, [email.id])


# ── Content Preparation Tests ────────────────────────────────────────

class TestContentPreparation:
    def test_text_only_email(self, db):
        email = _create_test_email(db)
        try:
            blocks = prepare_email_content(email)
            assert len(blocks) == 1
            assert blocks[0]["type"] == "text"
            assert "EMAIL BODY" in blocks[0]["text"]
            assert "LOCAP2" in blocks[0]["text"]
        finally:
            _cleanup_test_data(db, [email.id])

    def test_email_with_pdf(self, db):
        email = _create_test_email(db)
        try:
            # Add a fake PDF attachment (minimal valid PDF)
            pdf_bytes = b"%PDF-1.4 fake pdf content"
            att = EmailAttachment(
                email_id=email.id,
                filename="order.pdf",
                content_type="application/pdf",
                file_data=pdf_bytes,
                file_size_bytes=len(pdf_bytes),
            )
            db.add(att)
            db.commit()
            db.refresh(email)

            blocks = prepare_email_content(email)
            assert len(blocks) == 2
            # First block is email body text
            assert blocks[0]["type"] == "text"
            # Second block is the PDF document
            assert blocks[1]["type"] == "document"
            assert blocks[1]["source"]["media_type"] == "application/pdf"
        finally:
            _cleanup_test_data(db, [email.id])

    def test_email_with_image(self, db):
        email = _create_test_email(db)
        try:
            att = EmailAttachment(
                email_id=email.id,
                filename="order.png",
                content_type="image/png",
                file_data=b"\x89PNG\r\n\x1a\n",
                file_size_bytes=8,
            )
            db.add(att)
            db.commit()
            db.refresh(email)

            blocks = prepare_email_content(email)
            assert len(blocks) == 2
            assert blocks[1]["type"] == "image"
            assert blocks[1]["source"]["media_type"] == "image/png"
        finally:
            _cleanup_test_data(db, [email.id])

    def test_empty_email(self, db):
        email = IncomingEmail(
            gmail_message_id=f"empty-{uuid.uuid4().hex[:8]}",
            sender="test@example.com",
            subject="Empty",
            body_text="",
            processed=False,
        )
        db.add(email)
        db.commit()
        db.refresh(email)
        try:
            blocks = prepare_email_content(email)
            assert len(blocks) == 1  # fallback block
            assert "No extractable content" in blocks[0]["text"]
        finally:
            _cleanup_test_data(db, [email.id])


# ── JSON Parsing Tests ───────────────────────────────────────────────

class TestJsonParsing:
    def test_clean_json(self):
        raw = json.dumps(MOCK_EXTRACTION)
        result = _parse_extraction_json(raw)
        assert result["po_number"]["value"] == "PO-12345"

    def test_json_in_code_fence(self):
        raw = f"Here is the extraction:\n```json\n{json.dumps(MOCK_EXTRACTION)}\n```"
        result = _parse_extraction_json(raw)
        assert result["po_number"]["value"] == "PO-12345"

    def test_json_with_surrounding_text(self):
        raw = f"I found this order:\n{json.dumps(MOCK_EXTRACTION)}\nHope that helps!"
        result = _parse_extraction_json(raw)
        assert result["po_number"]["value"] == "PO-12345"

    def test_invalid_json_raises(self):
        with pytest.raises(ExtractionError):
            _parse_extraction_json("This is not JSON at all")


# ── Extraction Service Tests (mocked Anthropic) ─────────────────────

class TestExtractionService:
    @patch("app.services.extraction_service.anthropic.Anthropic")
    def test_extract_order_from_email(self, mock_anthropic_cls, db):
        email = _create_test_email(db)
        try:
            # Set up the mock
            mock_client = MagicMock()
            mock_anthropic_cls.return_value = mock_client

            mock_response = MagicMock()
            mock_text_block = MagicMock()
            mock_text_block.type = "text"
            mock_text_block.text = json.dumps(MOCK_EXTRACTION)
            mock_response.content = [mock_text_block]

            mock_client.messages.create.return_value = mock_response

            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
                result = extract_order_from_email(email)

            assert result["po_number"]["value"] == "PO-12345"
            assert result["overall_confidence"] == 0.92
            assert len(result["line_items"]) == 2
        finally:
            _cleanup_test_data(db, [email.id])

    def test_extract_without_api_key(self, db):
        email = _create_test_email(db)
        try:
            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": ""}, clear=False):
                # Remove the key if present
                import os
                old_key = os.environ.pop("ANTHROPIC_API_KEY", None)
                try:
                    with pytest.raises(ExtractionError, match="ANTHROPIC_API_KEY"):
                        extract_order_from_email(email)
                finally:
                    if old_key:
                        os.environ["ANTHROPIC_API_KEY"] = old_key
        finally:
            _cleanup_test_data(db, [email.id])

    @patch("app.services.extraction_service.anthropic.Anthropic")
    def test_api_error_handling(self, mock_anthropic_cls, db):
        email = _create_test_email(db)
        try:
            mock_client = MagicMock()
            mock_anthropic_cls.return_value = mock_client
            mock_client.messages.create.side_effect = anthropic.APIError(
                message="Rate limited",
                request=MagicMock(),
                body=None,
            )

            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
                with pytest.raises(ExtractionError, match="Anthropic API error"):
                    extract_order_from_email(email)
        except ImportError:
            pytest.skip("anthropic not installed")
        finally:
            _cleanup_test_data(db, [email.id])


# ── Order Creation Tests ─────────────────────────────────────────────

class TestOrderCreation:
    def test_create_order_from_extraction(self, db):
        email = _create_test_email(db)
        try:
            order = create_order_from_extraction(db, email, MOCK_EXTRACTION)

            assert order.id is not None
            assert order.status == "pending"
            assert order.customer_name == "Test Customer Pty Ltd"
            assert order.po_number == "PO-12345"
            assert order.extraction_confidence == Decimal("0.92")
            assert len(order.line_items) == 2
            assert email.processed is True

            # First line item — LOCAP2 should match
            item1 = next(i for i in order.line_items if i.line_number == 1)
            assert item1.product_code == "LOCAP2"
            assert item1.quantity == 1000
            assert item1.line_total == Decimal("1320.00")

            # Second line item — UNKNOWNPROD should not match
            item2 = next(i for i in order.line_items if i.line_number == 2)
            assert item2.product_code == "UNKNOWNPROD"
            assert item2.needs_review is True
            assert item2.matched_product_code is None

            # Clean up
            db.query(OrderLineItem).filter(OrderLineItem.order_id == order.id).delete()
            db.delete(order)
            db.commit()
        finally:
            _cleanup_test_data(db, [email.id])

    def test_create_order_from_error_extraction(self, db):
        email = _create_test_email(db)
        try:
            error_extraction = {
                "error": "No purchase order found",
                "overall_confidence": 0.0,
            }
            order = create_order_from_extraction(db, email, error_extraction)

            assert order.status == "error"
            assert order.extraction_confidence == Decimal("0.00")
            assert email.processed is True

            db.delete(order)
            db.commit()
        finally:
            _cleanup_test_data(db, [email.id])


# ── Product Matching in Context ──────────────────────────────────────

class TestProductMatchingInExtraction:
    def test_exact_match_sets_matched_code(self, db):
        email = _create_test_email(db)
        try:
            extraction = {
                "customer_name": {"value": "Test", "confidence": 0.9},
                "po_number": {"value": "PO-1", "confidence": 0.9},
                "po_date": {"value": None, "confidence": 0.0},
                "delivery_date": {"value": None, "confidence": 0.0},
                "special_instructions": {"value": None, "confidence": 0.0},
                "line_items": [
                    {
                        "product_code": {"value": "LOCAP2", "confidence": 0.99},
                        "description": {"value": "Louvre end cap", "confidence": 0.95},
                        "quantity": {"value": 100, "confidence": 0.99},
                        "colour": {"value": "Black", "confidence": 0.95},
                        "unit_price": {"value": 1.32, "confidence": 0.90},
                    }
                ],
                "overall_confidence": 0.95,
            }
            order = create_order_from_extraction(db, email, extraction)

            item = order.line_items[0]
            assert item.matched_product_code == "LOCAP2"
            assert item.needs_review is False

            db.query(OrderLineItem).filter(OrderLineItem.order_id == order.id).delete()
            db.delete(order)
            db.commit()
        finally:
            _cleanup_test_data(db, [email.id])

    def test_unknown_code_sets_needs_review(self, db):
        email = _create_test_email(db)
        try:
            extraction = {
                "customer_name": {"value": "Test", "confidence": 0.9},
                "po_number": {"value": "PO-2", "confidence": 0.9},
                "po_date": {"value": None, "confidence": 0.0},
                "delivery_date": {"value": None, "confidence": 0.0},
                "special_instructions": {"value": None, "confidence": 0.0},
                "line_items": [
                    {
                        "product_code": {"value": "TOTALLYUNKNOWN999", "confidence": 0.60},
                        "description": {"value": "Mystery part", "confidence": 0.50},
                        "quantity": {"value": 50, "confidence": 0.99},
                        "colour": {"value": None, "confidence": 0.0},
                        "unit_price": {"value": None, "confidence": 0.0},
                    }
                ],
                "overall_confidence": 0.50,
            }
            order = create_order_from_extraction(db, email, extraction)

            item = order.line_items[0]
            assert item.matched_product_code is None
            assert item.needs_review is True

            db.query(OrderLineItem).filter(OrderLineItem.order_id == order.id).delete()
            db.delete(order)
            db.commit()
        finally:
            _cleanup_test_data(db, [email.id])


# ── Pipeline Tests (mocked Anthropic) ────────────────────────────────

class TestPipeline:
    @patch("app.services.extraction_service.anthropic.Anthropic")
    def test_process_single_email(self, mock_anthropic_cls, db):
        email = _create_test_email(db)
        try:
            mock_client = MagicMock()
            mock_anthropic_cls.return_value = mock_client

            mock_response = MagicMock()
            mock_text_block = MagicMock()
            mock_text_block.type = "text"
            mock_text_block.text = json.dumps(MOCK_EXTRACTION)
            mock_response.content = [mock_text_block]
            mock_client.messages.create.return_value = mock_response

            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
                order = process_single_email(db, email)

            assert order is not None
            assert order.status == "pending"
            assert order.customer_name == "Test Customer Pty Ltd"

            db.query(OrderLineItem).filter(OrderLineItem.order_id == order.id).delete()
            db.delete(order)
            db.commit()
        finally:
            _cleanup_test_data(db, [email.id])

    @patch("app.services.extraction_service.anthropic.Anthropic")
    def test_process_unprocessed_emails(self, mock_anthropic_cls, db):
        email1 = _create_test_email(db)
        email2 = _create_test_email(db)
        try:
            mock_client = MagicMock()
            mock_anthropic_cls.return_value = mock_client

            mock_response = MagicMock()
            mock_text_block = MagicMock()
            mock_text_block.type = "text"
            mock_text_block.text = json.dumps(MOCK_EXTRACTION)
            mock_response.content = [mock_text_block]
            mock_client.messages.create.return_value = mock_response

            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
                result = process_unprocessed_emails(db)

            assert result["orders_created"] >= 2
            assert result["errors"] == 0

            # Clean up
            for eid in [email1.id, email2.id]:
                orders = db.query(Order).filter(Order.email_id == eid).all()
                for o in orders:
                    db.query(OrderLineItem).filter(OrderLineItem.order_id == o.id).delete()
                    db.delete(o)
            db.commit()
        finally:
            _cleanup_test_data(db, [email1.id, email2.id])


# ── API Endpoint Tests ───────────────────────────────────────────────

class TestOrdersAPI:
    def test_list_orders(self):
        resp = client.get("/api/orders/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_orders_with_status_filter(self):
        resp = client.get("/api/orders/?status=pending")
        assert resp.status_code == 200
        data = resp.json()
        assert all(o["status"] == "pending" for o in data)

    def test_get_order_404(self):
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/api/orders/{fake_id}")
        assert resp.status_code == 404

    def test_process_email_404(self):
        resp = client.post("/api/orders/process-email/999999")
        assert resp.status_code == 404

    def test_reprocess_order_404(self):
        fake_id = str(uuid.uuid4())
        resp = client.post(f"/api/orders/{fake_id}/reprocess")
        assert resp.status_code == 404
