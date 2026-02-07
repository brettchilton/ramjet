#!/usr/bin/env python3
"""
Seed PostgreSQL product catalog from the demonstrator SQLite database.

Usage:
  Inside Docker:   python scripts/seed_products.py
  From repo root:  DB_HOST=localhost python backend/scripts/seed_products.py

The script auto-detects running inside Docker (DB_HOST=db) and adjusts the
SQLite source path accordingly.
"""

import os
import sys
import sqlite3
from datetime import date

# Ensure we can import the backend app package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal
from app.core.models import (
    Base,
    Product,
    ManufacturingSpec,
    MaterialSpec,
    PackagingSpec,
    Pricing,
)

# Allow override via env var; otherwise resolve relative to this script
SQLITE_PATH = os.environ.get(
    "SQLITE_SOURCE",
    os.path.join(os.path.dirname(__file__), "..", "..", "docs", "feature_plans", "demonstrator", "ramjet_products.db"),
)


def seed():
    sqlite_path = os.path.abspath(SQLITE_PATH)
    if not os.path.exists(sqlite_path):
        print(f"ERROR: SQLite file not found at {sqlite_path}")
        sys.exit(1)

    db: Session = SessionLocal()

    # Idempotent: skip if products already exist
    existing = db.query(Product).count()
    if existing > 0:
        print(f"Products table already has {existing} rows — skipping seed.")
        db.close()
        return

    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row

    # ── 1. Products ──────────────────────────────────────────────────────
    rows = conn.execute("SELECT * FROM products").fetchall()
    print(f"Found {len(rows)} products in SQLite")

    for row in rows:
        product = Product(
            product_code=row["product_code"],
            product_description=row["product_description"],
            customer_name=row["customer"],
            is_active=True,
        )
        db.add(product)

        # Manufacturing spec (split from products table)
        mfg = ManufacturingSpec(
            product_code=row["product_code"],
            mould_no=row["mould_no"],
            cycle_time_seconds=row["cycle_time_seconds"],
            shot_weight_grams=row["shot_weight_grams"],
            num_cavities=row["num_cavities"],
            product_weight_grams=row["product_weight_grams"],
            estimated_running_time_hours=row["estimated_running_time_hours"],
            machine_min_requirements=row["machine_min_requirements"],
        )
        db.add(mfg)

    # ── 2. Packaging specs ───────────────────────────────────────────────
    pkg_rows = conn.execute("SELECT * FROM packaging_specs").fetchall()
    print(f"Found {len(pkg_rows)} packaging specs in SQLite")

    for row in pkg_rows:
        pkg = PackagingSpec(
            product_code=row["product_code"],
            qty_per_bag=row["qty_per_bag"],
            bag_size=row["bag_size"],
            qty_per_carton=row["qty_per_carton"],
            carton_size=row["carton_size"],
            cartons_per_pallet=row["cartons_per_pallet"],
            cartons_per_layer=row["cartons_per_layer"],
        )
        db.add(pkg)

    # ── 3. Material specs ────────────────────────────────────────────────
    mat_rows = conn.execute("SELECT * FROM material_specs").fetchall()
    print(f"Found {len(mat_rows)} material specs in SQLite")

    for row in mat_rows:
        mat = MaterialSpec(
            product_code=row["product_code"],
            colour=row["colour"],
            material_grade=row["material_grade"],
            material_type=row["material_type"],
            colour_no=row["colour_no"],
            colour_supplier=row["colour_supplier"],
            mb_add_rate=row["mb_add_rate"],
            additive=row["additive"],
            additive_add_rate=row["additive_add_rate"],
            additive_supplier=row["additive_supplier"],
        )
        db.add(mat)

    # ── 4. Pricing ───────────────────────────────────────────────────────
    price_rows = conn.execute("SELECT * FROM pricing").fetchall()
    print(f"Found {len(price_rows)} pricing rows in SQLite")

    for row in price_rows:
        price = Pricing(
            product_code=row["product_code"],
            colour=row["colour"],
            unit_price=row["unit_cost"],
            currency="AUD",
            effective_date=date.today(),
        )
        db.add(price)

    conn.close()

    db.commit()
    final_count = db.query(Product).count()
    print(f"\nSeed complete — {final_count} products inserted into PostgreSQL.")
    db.close()


if __name__ == "__main__":
    seed()
