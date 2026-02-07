"""
Integration tests for Phase 1: Product catalog API + enrichment service.

Run inside Docker:
    docker exec eezy_peezy_backend python -m pytest tests/test_products.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db, SessionLocal
from app.services.enrichment_service import (
    get_product_full_specs,
    calculate_material_requirements,
    search_products,
    match_product_code,
)

client = TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ── Enrichment Service Tests ────────────────────────────────────────────

class TestEnrichmentService:
    def test_get_product_full_specs(self, db):
        specs = get_product_full_specs(db, "LOCAP2", "Black")
        assert specs is not None
        assert specs["product_code"] == "LOCAP2"
        assert specs["product_description"] == "LOUVRE END CAP 152mm"
        assert specs["customer"] == "Shape Aluminium"
        assert specs["material"]["colour"] == "Black"
        assert specs["material"]["material_grade"] == "PP H520"
        assert specs["packaging"]["qty_per_carton"] == 200

    def test_get_product_not_found(self, db):
        specs = get_product_full_specs(db, "NONEXISTENT", "Black")
        assert specs is None

    def test_calculate_material_requirements(self, db):
        result = calculate_material_requirements(db, "LOCAP2", "Black", 1000)
        assert result is not None
        assert result["product_code"] == "LOCAP2"
        assert result["quantity"] == 1000

        mat = result["material_requirements"]
        assert mat["total_material_kg"] == 44.1
        assert mat["base_material_kg"] == 42.56
        assert mat["masterbatch_kg"] == 1.1
        assert mat["additive_kg"] == 0.44
        assert mat["material_grade"] == "PP H520"

        pkg = result["packaging_requirements"]
        assert pkg["bags_needed"] == 20
        assert pkg["cartons_needed"] == 5

        assert result["estimated_cost"] == 1320.0

    def test_search_products(self, db):
        results = search_products(db, "CAP")
        assert len(results) > 0
        codes = [r["product_code"] for r in results]
        assert "LOCAP2" in codes

    def test_search_empty(self, db):
        results = search_products(db, "ZZZZNOTHING")
        assert len(results) == 0


class TestFuzzyMatching:
    def test_exact_match(self, db):
        matches = match_product_code(db, "LOCAP2")
        assert len(matches) == 1
        assert matches[0]["confidence"] == 1.0
        assert matches[0]["match_type"] == "exact"

    def test_case_insensitive_match(self, db):
        matches = match_product_code(db, "locap2")
        assert len(matches) == 1
        assert matches[0]["confidence"] == 0.9
        assert matches[0]["match_type"] == "case_insensitive"
        assert matches[0]["product_code"] == "LOCAP2"

    def test_partial_match(self, db):
        matches = match_product_code(db, "LOUVRE")
        assert len(matches) > 0
        assert all(m["confidence"] == 0.6 for m in matches)
        assert all(m["match_type"] == "partial" for m in matches)

    def test_no_match(self, db):
        matches = match_product_code(db, "XYZNONEXIST999")
        assert len(matches) == 0

    def test_empty_input(self, db):
        matches = match_product_code(db, "")
        assert len(matches) == 0


# ── API Endpoint Tests ──────────────────────────────────────────────────

class TestProductsAPI:
    def test_list_products(self):
        resp = client.get("/api/products/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 57

    def test_list_products_search(self):
        resp = client.get("/api/products/?search=CAP")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        assert any(p["product_code"] == "LOCAP2" for p in data)

    def test_list_products_customer_filter(self):
        resp = client.get("/api/products/?customer=Shape")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        assert all("Shape" in p["customer_name"] for p in data)

    def test_get_product(self):
        resp = client.get("/api/products/LOCAP2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["product_code"] == "LOCAP2"
        assert data["manufacturing"]["mould_no"] == "M-LC152"
        assert len(data["materials"]) > 0
        assert data["packaging"]["qty_per_carton"] == 200

    def test_get_product_404(self):
        resp = client.get("/api/products/NONEXISTENT")
        assert resp.status_code == 404

    def test_calculate(self):
        resp = client.get("/api/products/LOCAP2/calculate?quantity=1000&colour=Black")
        assert resp.status_code == 200
        data = resp.json()
        assert data["product_code"] == "LOCAP2"
        assert data["quantity"] == 1000
        assert data["material_requirements"]["total_material_kg"] == 44.1
        assert data["estimated_cost"] == 1320.0

    def test_calculate_404(self):
        resp = client.get("/api/products/NONEXISTENT/calculate?quantity=100&colour=Black")
        assert resp.status_code == 404

    def test_match_endpoint(self):
        resp = client.get("/api/products/match?code=LOCAP2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["confidence"] == 1.0
