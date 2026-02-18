"""
Barcode service — QR code generation, unique barcode ID sequencing,
and label PDF rendering for stock cartons.
"""

import io
import logging
from datetime import date, datetime
from typing import Optional

import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.models import StockItem, Product

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────

QR_PREFIX = "RJ"
ERROR_CORRECTION_MAP = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}
DEFAULT_ERROR_CORRECTION = "M"

# Label layout: 2 columns x 5 rows = 10 labels per A4 page
LABELS_PER_ROW = 2
LABELS_PER_COL = 5
LABELS_PER_PAGE = LABELS_PER_ROW * LABELS_PER_COL

# Label dimensions (in mm)
PAGE_WIDTH, PAGE_HEIGHT = A4  # in points (already)
LABEL_WIDTH = 90 * mm
LABEL_HEIGHT = 50 * mm
MARGIN_X = 15 * mm
MARGIN_Y = 12 * mm
GAP_X = 10 * mm
GAP_Y = 6 * mm

# Colours
PINK_BG = colors.HexColor("#FFB6C1")
YELLOW_BG = colors.HexColor("#FFEB3B")


# ── Colour Short Codes ──────────────────────────────────────────────

COLOUR_SHORT_OVERRIDES = {
    "black": "BLK",
    "white": "WHT",
    "yellow": "YEL",
    "natural": "NAT",
    "red": "RED",
    "blue": "BLU",
    "green": "GRN",
    "grey": "GRY",
    "gray": "GRY",
    "orange": "ORG",
    "brown": "BRN",
    "clear": "CLR",
}


def get_colour_short(colour: str) -> str:
    """Derive a 3-character uppercase short code from a colour name."""
    normalised = colour.strip().lower()
    if normalised in COLOUR_SHORT_OVERRIDES:
        return COLOUR_SHORT_OVERRIDES[normalised]
    return colour.strip()[:3].upper()


# ── Barcode ID Generation ───────────────────────────────────────────

def generate_barcode_ids(
    db: Session,
    product_code: str,
    colour: str,
    count: int,
    production_date: Optional[date] = None,
) -> list[str]:
    """
    Generate `count` unique barcode IDs for the given product+colour+date.

    Format: RJ-{PRODUCT_CODE}-{COLOUR_SHORT}-{YYYYMMDD}-{SEQ}
    Sequence resets daily per product+colour combination.
    """
    if production_date is None:
        production_date = date.today()

    colour_short = get_colour_short(colour)
    date_str = production_date.strftime("%Y%m%d")
    prefix = f"{QR_PREFIX}-{product_code}-{colour_short}-{date_str}-"

    # Find the max existing sequence for this prefix today
    max_seq = (
        db.query(func.max(StockItem.barcode_id))
        .filter(StockItem.barcode_id.like(f"{prefix}%"))
        .scalar()
    )

    if max_seq:
        # Extract sequence number from the last barcode
        try:
            current_max = int(max_seq.split("-")[-1])
        except (ValueError, IndexError):
            current_max = 0
    else:
        current_max = 0

    barcode_ids = []
    for i in range(1, count + 1):
        seq = current_max + i
        barcode_id = f"{prefix}{seq:03d}"
        barcode_ids.append(barcode_id)

    return barcode_ids


# ── QR Code Image Generation ────────────────────────────────────────

def generate_qr_image(data: str, error_correction: str = DEFAULT_ERROR_CORRECTION) -> io.BytesIO:
    """Generate a QR code PNG image as a BytesIO buffer."""
    ec_level = ERROR_CORRECTION_MAP.get(error_correction, ERROR_CORRECT_M)

    qr = qrcode.QRCode(
        version=None,  # auto-size
        error_correction=ec_level,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# ── Stock Item Creation ─────────────────────────────────────────────

def create_stock_items(
    db: Session,
    barcode_ids: list[str],
    product_code: str,
    colour: str,
    quantity_per_carton: int,
    box_type: str,
    production_date: Optional[date] = None,
) -> list[StockItem]:
    """Create StockItem records with status 'pending_scan'."""
    items = []
    for barcode_id in barcode_ids:
        item = StockItem(
            barcode_id=barcode_id,
            product_code=product_code,
            colour=colour,
            quantity=quantity_per_carton,
            box_type=box_type,
            status="pending_scan",
            production_date=production_date or date.today(),
        )
        db.add(item)
        items.append(item)

    db.flush()  # assign IDs without committing
    return items


# ── Label PDF Rendering ─────────────────────────────────────────────

def _draw_label(
    c: canvas.Canvas,
    x: float,
    y: float,
    barcode_id: str,
    product_code: str,
    colour: str,
    quantity: int,
    production_date: date,
    box_type: str,
):
    """Draw a single label at position (x, y) — bottom-left corner."""
    bg_colour = PINK_BG if box_type == "full" else YELLOW_BG
    box_label = "FULL BOX" if box_type == "full" else "PARTIAL BOX"

    # Background rectangle
    c.setFillColor(bg_colour)
    c.setStrokeColor(colors.grey)
    c.setLineWidth(0.5)
    c.roundRect(x, y, LABEL_WIDTH, LABEL_HEIGHT, 3 * mm, fill=1, stroke=1)

    # QR code image
    qr_size = 30 * mm
    qr_x = x + 4 * mm
    qr_y = y + LABEL_HEIGHT - qr_size - 8 * mm
    qr_buf = generate_qr_image(barcode_id)
    qr_img = ImageReader(qr_buf)
    c.drawImage(qr_img, qr_x, qr_y, width=qr_size, height=qr_size)

    # Text area (right of QR code)
    text_x = qr_x + qr_size + 4 * mm
    text_y = y + LABEL_HEIGHT - 10 * mm

    c.setFillColor(colors.black)

    # Product code (large, bold)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(text_x, text_y, product_code)
    text_y -= 14

    # Colour
    c.setFont("Helvetica", 10)
    c.drawString(text_x, text_y, colour)
    text_y -= 13

    # Quantity
    c.setFont("Helvetica-Bold", 10)
    c.drawString(text_x, text_y, f"Qty: {quantity}")
    text_y -= 13

    # Production date
    c.setFont("Helvetica", 9)
    c.drawString(text_x, text_y, production_date.strftime("%Y-%m-%d"))

    # Barcode ID (bottom of label, small)
    c.setFont("Helvetica", 7)
    c.drawString(x + 4 * mm, y + 10 * mm, barcode_id)

    # Box type indicator
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x + 4 * mm, y + 3 * mm, box_label)


def generate_single_label_pdf(
    barcode_id: str,
    product_code: str,
    colour: str,
    quantity: int,
    production_date: date,
    box_type: str = "partial",
) -> bytes:
    """Render a single-label PDF (e.g. for a partial box yellow label). Returns PDF bytes."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"Label - {barcode_id}")

    # Centre the single label on the page
    x = MARGIN_X
    y = PAGE_HEIGHT - MARGIN_Y - LABEL_HEIGHT

    _draw_label(
        c, x, y,
        barcode_id=barcode_id,
        product_code=product_code,
        colour=colour,
        quantity=quantity,
        production_date=production_date,
        box_type=box_type,
    )

    c.save()
    return buf.getvalue()


def generate_label_pdf(
    barcode_ids: list[str],
    product_code: str,
    colour: str,
    quantity_per_carton: int,
    production_date: date,
    box_type: str,
) -> bytes:
    """Render a multi-page A4 PDF with QR code labels. Returns PDF bytes."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"Labels - {product_code} {colour}")

    total_labels = len(barcode_ids)
    label_idx = 0

    while label_idx < total_labels:
        # Draw labels on current page
        for row in range(LABELS_PER_COL):
            for col in range(LABELS_PER_ROW):
                if label_idx >= total_labels:
                    break

                x = MARGIN_X + col * (LABEL_WIDTH + GAP_X)
                # Top-down: first row at top of page
                y = PAGE_HEIGHT - MARGIN_Y - (row + 1) * LABEL_HEIGHT - row * GAP_Y

                _draw_label(
                    c, x, y,
                    barcode_id=barcode_ids[label_idx],
                    product_code=product_code,
                    colour=colour,
                    quantity=quantity_per_carton,
                    production_date=production_date,
                    box_type=box_type,
                )
                label_idx += 1

            if label_idx >= total_labels:
                break

        if label_idx < total_labels:
            c.showPage()

    c.save()
    return buf.getvalue()


# ── Orchestrator ─────────────────────────────────────────────────────

def generate_labels(
    db: Session,
    product_code: str,
    colour: str,
    quantity_per_carton: int,
    number_of_labels: int,
    box_type: str = "full",
    production_date: Optional[date] = None,
) -> tuple[bytes, list[str]]:
    """
    Full label generation pipeline:
    1. Validate product exists
    2. Generate unique barcode IDs
    3. Create StockItem records (status: pending_scan)
    4. Render label PDF
    5. Return (pdf_bytes, barcode_ids)
    """
    if production_date is None:
        production_date = date.today()

    # Validate product exists and is stockable
    product = db.query(Product).filter(
        Product.product_code == product_code,
        Product.is_active == True,
    ).first()
    if not product:
        raise ValueError(f"Product '{product_code}' not found or inactive")
    if not product.is_stockable:
        raise ValueError(f"Product '{product_code}' is not stockable")

    # Generate barcode IDs
    barcode_ids = generate_barcode_ids(
        db, product_code, colour, number_of_labels, production_date
    )
    logger.info("Generated %d barcode IDs for %s/%s", len(barcode_ids), product_code, colour)

    # Create stock items
    create_stock_items(
        db, barcode_ids, product_code, colour,
        quantity_per_carton, box_type, production_date,
    )
    logger.info("Created %d StockItem records (pending_scan)", len(barcode_ids))

    # Render PDF
    pdf_bytes = generate_label_pdf(
        barcode_ids, product_code, colour,
        quantity_per_carton, production_date, box_type,
    )
    logger.info("Label PDF generated: %d bytes, %d labels", len(pdf_bytes), len(barcode_ids))

    # Commit the stock items
    db.commit()

    return pdf_bytes, barcode_ids
