from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON, Index, Numeric, Date, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    
    # User profile information
    email = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    mobile = Column(String(20))  # Mobile/phone number
    
    # Authentication - password for simple auth, Kratos ID for production
    password_hash = Column(String(255))  # For simple auth in development
    kratos_identity_id = Column(String(255), unique=True)  # Kratos identity ID for production
    
    # Authorization
    role = Column(String(50), default="warehouse")  # warehouse, admin
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Create indexes for User
Index('idx_user_email', User.email)
Index('idx_user_kratos_identity', User.kratos_identity_id)
Index('idx_user_active', User.is_active)


# ── Product Catalog Models ──────────────────────────────────────────────

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    product_code = Column(String(50), unique=True, nullable=False)
    product_description = Column(Text, nullable=False)
    customer_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_stockable = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    manufacturing_spec = relationship("ManufacturingSpec", back_populates="product", uselist=False, cascade="all, delete-orphan")
    material_specs = relationship("MaterialSpec", back_populates="product", cascade="all, delete-orphan")
    packaging_spec = relationship("PackagingSpec", back_populates="product", uselist=False, cascade="all, delete-orphan")
    pricing = relationship("Pricing", back_populates="product", cascade="all, delete-orphan")


Index('idx_product_code', Product.product_code)
Index('idx_product_customer', Product.customer_name)
Index('idx_product_active', Product.is_active)


class ManufacturingSpec(Base):
    __tablename__ = "manufacturing_specs"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    product_code = Column(String(50), ForeignKey("products.product_code"), unique=True, nullable=False)
    mould_no = Column(String(50))
    cycle_time_seconds = Column(Integer)
    shot_weight_grams = Column(Numeric(10, 2))
    num_cavities = Column(Integer)
    product_weight_grams = Column(Numeric(10, 2))
    estimated_running_time_hours = Column(Numeric(10, 2))
    machine_min_requirements = Column(String(100))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    product = relationship("Product", back_populates="manufacturing_spec")


Index('idx_mfg_product_code', ManufacturingSpec.product_code)


class MaterialSpec(Base):
    __tablename__ = "material_specs"
    __table_args__ = (
        Index('uq_material_product_colour', 'product_code', 'colour', unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    product_code = Column(String(50), ForeignKey("products.product_code"), nullable=False)
    colour = Column(String(100), nullable=False)
    material_grade = Column(String(100))
    material_type = Column(String(100))
    colour_no = Column(String(50))
    colour_supplier = Column(String(100))
    mb_add_rate = Column(Numeric(5, 2))
    additive = Column(String(100))
    additive_add_rate = Column(Numeric(5, 2))
    additive_supplier = Column(String(100))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    product = relationship("Product", back_populates="material_specs")


Index('idx_material_product_code', MaterialSpec.product_code)


class PackagingSpec(Base):
    __tablename__ = "packaging_specs"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    product_code = Column(String(50), ForeignKey("products.product_code"), unique=True, nullable=False)
    qty_per_bag = Column(Integer)
    bag_size = Column(String(50))
    qty_per_carton = Column(Integer)
    carton_size = Column(String(50))
    cartons_per_pallet = Column(Integer)
    cartons_per_layer = Column(Integer)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    product = relationship("Product", back_populates="packaging_spec")


Index('idx_packaging_product_code', PackagingSpec.product_code)


class Pricing(Base):
    __tablename__ = "pricing"
    __table_args__ = (
        Index('uq_pricing_product_colour', 'product_code', 'colour', unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    product_code = Column(String(50), ForeignKey("products.product_code"), nullable=False)
    colour = Column(String(100), nullable=False)
    customer_name = Column(String(255))
    unit_price = Column(Numeric(10, 4), nullable=False)
    currency = Column(String(10), default="AUD")
    effective_date = Column(Date)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    product = relationship("Product", back_populates="pricing")


Index('idx_pricing_product_code', Pricing.product_code)


# ── Email Monitoring Models ───────────────────────────────────────────

class IncomingEmail(Base):
    __tablename__ = "incoming_emails"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gmail_message_id = Column(String(255), unique=True, nullable=False)
    sender = Column(String(255))
    subject = Column(Text)
    body_text = Column(Text)
    body_html = Column(Text)
    received_at = Column(DateTime(timezone=True))
    processed = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    attachments = relationship("EmailAttachment", back_populates="email", cascade="all, delete-orphan")


Index('idx_incoming_emails_gmail_id', IncomingEmail.gmail_message_id)
Index('idx_incoming_emails_processed', IncomingEmail.processed)


class EmailAttachment(Base):
    __tablename__ = "email_attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_id = Column(Integer, ForeignKey("incoming_emails.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255))
    content_type = Column(String(100))
    file_data = Column(LargeBinary)
    file_size_bytes = Column(Integer)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    email = relationship("IncomingEmail", back_populates="attachments")


Index('idx_email_attachments_email_id', EmailAttachment.email_id)


class EmailMonitorStatus(Base):
    __tablename__ = "email_monitor_status"

    id = Column(Integer, primary_key=True, default=1)
    is_running = Column(Boolean, default=False)
    last_poll_at = Column(DateTime(timezone=True))
    last_error = Column(Text)
    emails_processed_total = Column(Integer, default=0)


# ── System Settings ──────────────────────────────────────────────────

class SystemSettings(Base):
    __tablename__ = "system_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


# ── Order Models ──────────────────────────────────────────────────────

class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    email_id = Column(Integer, ForeignKey("incoming_emails.id"), nullable=True)
    status = Column(String(30), nullable=False, default="pending")  # pending | approved | rejected | error | verified | works_order_generated
    customer_name = Column(String(255))
    po_number = Column(String(100))
    po_date = Column(Date)
    delivery_date = Column(Date)
    special_instructions = Column(Text)
    extraction_confidence = Column(Numeric(3, 2))  # 0.00 to 1.00
    extraction_raw_json = Column(JSONB)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True))
    rejected_reason = Column(Text)
    office_order_file = Column(LargeBinary)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    email = relationship("IncomingEmail", backref="orders")
    line_items = relationship("OrderLineItem", back_populates="order", cascade="all, delete-orphan")
    approver = relationship("User", foreign_keys=[approved_by])
    stock_verifications = relationship("StockVerification", back_populates="order")


Index('idx_orders_status', Order.status)
Index('idx_orders_email', Order.email_id)


class OrderLineItem(Base):
    __tablename__ = "order_line_items"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)
    product_code = Column(String(50))  # as extracted
    matched_product_code = Column(String(50), ForeignKey("products.product_code"), nullable=True)
    product_description = Column(String(255))
    colour = Column(String(100))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2))
    line_total = Column(Numeric(12, 2))
    confidence = Column(Numeric(3, 2))  # field-level confidence
    needs_review = Column(Boolean, default=False)
    works_order_file = Column(LargeBinary)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    order = relationship("Order", back_populates="line_items")
    matched_product = relationship("Product", foreign_keys=[matched_product_code])
    stock_verifications = relationship("StockVerification", back_populates="order_line_item")


Index('idx_order_line_items_order_id', OrderLineItem.order_id)


# ── Stock Tracking Models ────────────────────────────────────────────

class StockItem(Base):
    __tablename__ = "stock_items"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    barcode_id = Column(String(100), unique=True, nullable=False)
    product_code = Column(String(50), ForeignKey("products.product_code"), nullable=False)
    colour = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    box_type = Column(String(10), nullable=False)  # full | partial
    status = Column(String(20), nullable=False, default="in_stock")  # in_stock | picked | scrapped | consumed
    production_date = Column(Date)
    scanned_in_at = Column(DateTime(timezone=True))
    scanned_in_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    scanned_out_at = Column(DateTime(timezone=True), nullable=True)
    scanned_out_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    parent_stock_item_id = Column(UUID(as_uuid=True), ForeignKey("stock_items.id"), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    product = relationship("Product", foreign_keys=[product_code])
    scanned_in_user = relationship("User", foreign_keys=[scanned_in_by])
    scanned_out_user = relationship("User", foreign_keys=[scanned_out_by])
    order = relationship("Order", foreign_keys=[order_id])
    parent_stock_item = relationship("StockItem", remote_side="StockItem.id", foreign_keys=[parent_stock_item_id])
    movements = relationship("StockMovement", back_populates="stock_item")


Index('idx_stock_items_barcode', StockItem.barcode_id)
Index('idx_stock_items_product', StockItem.product_code, StockItem.colour)
Index('idx_stock_items_status', StockItem.status)
Index('idx_stock_items_order', StockItem.order_id)


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    stock_item_id = Column(UUID(as_uuid=True), ForeignKey("stock_items.id"), nullable=False)
    movement_type = Column(String(20), nullable=False)  # stock_in | stock_out | adjustment | stocktake_verified | partial_repack
    quantity_change = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    stocktake_session_id = Column(UUID(as_uuid=True), ForeignKey("stocktake_sessions.id"), nullable=True)
    performed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    stock_item = relationship("StockItem", back_populates="movements")
    order = relationship("Order", foreign_keys=[order_id])
    stocktake_session = relationship("StocktakeSession", foreign_keys=[stocktake_session_id])
    performer = relationship("User", foreign_keys=[performed_by])


Index('idx_stock_movements_item', StockMovement.stock_item_id)
Index('idx_stock_movements_type', StockMovement.movement_type)
Index('idx_stock_movements_date', StockMovement.created_at)
Index('idx_stock_movements_order', StockMovement.order_id)


class StockThreshold(Base):
    __tablename__ = "stock_thresholds"
    __table_args__ = (
        Index('uq_stock_threshold_product_colour', 'product_code', 'colour', unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    product_code = Column(String(50), ForeignKey("products.product_code"), nullable=False)
    colour = Column(String(100), nullable=True)  # NULL = all colours for this product
    red_threshold = Column(Integer, nullable=False, default=0)
    amber_threshold = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    product = relationship("Product", foreign_keys=[product_code])


class StockVerification(Base):
    __tablename__ = "stock_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    order_line_item_id = Column(UUID(as_uuid=True), ForeignKey("order_line_items.id"), nullable=False)
    product_code = Column(String(50), ForeignKey("products.product_code"), nullable=False)
    colour = Column(String(100), nullable=False)
    system_stock_quantity = Column(Integer, nullable=False)
    verified_quantity = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending | confirmed | expired
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    order = relationship("Order", back_populates="stock_verifications")
    order_line_item = relationship("OrderLineItem", back_populates="stock_verifications")
    product = relationship("Product", foreign_keys=[product_code])
    verifier = relationship("User", foreign_keys=[verified_by])


Index('idx_stock_verifications_order', StockVerification.order_id)
Index('idx_stock_verifications_status', StockVerification.status)
Index('idx_stock_verifications_line_item', StockVerification.order_line_item_id)


class StocktakeSession(Base):
    __tablename__ = "stocktake_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    name = Column(String(255))
    status = Column(String(20), nullable=False, default="in_progress")  # in_progress | completed | cancelled
    started_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    completed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    total_expected = Column(Integer, nullable=True)
    total_scanned = Column(Integer, nullable=True)
    total_discrepancies = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    starter = relationship("User", foreign_keys=[started_by])
    completer = relationship("User", foreign_keys=[completed_by])
    scans = relationship("StocktakeScan", back_populates="session")


class StocktakeScan(Base):
    __tablename__ = "stocktake_scans"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    session_id = Column(UUID(as_uuid=True), ForeignKey("stocktake_sessions.id"), nullable=False)
    barcode_scanned = Column(String(100), nullable=False)
    stock_item_id = Column(UUID(as_uuid=True), ForeignKey("stock_items.id"), nullable=True)
    scan_result = Column(String(20), nullable=False)  # found | not_in_system | already_scanned | wrong_status
    scanned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    scanned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    session = relationship("StocktakeSession", back_populates="scans")
    stock_item = relationship("StockItem", foreign_keys=[stock_item_id])
    scanner = relationship("User", foreign_keys=[scanned_by])


Index('idx_stocktake_scans_session', StocktakeScan.session_id)
Index('idx_stocktake_scans_barcode', StocktakeScan.barcode_scanned)


# ── Raw Material Models ──────────────────────────────────────────────

class RawMaterial(Base):
    __tablename__ = "raw_materials"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    material_code = Column(String(50), unique=True, nullable=False)
    material_name = Column(String(255), nullable=False)
    material_type = Column(String(50), nullable=False)  # resin | masterbatch | additive | packaging | other
    unit_of_measure = Column(String(20), nullable=False)  # kg | litres | units | rolls
    current_stock = Column(Numeric(12, 2), nullable=False, default=0)
    red_threshold = Column(Numeric(12, 2), nullable=False, default=0)
    amber_threshold = Column(Numeric(12, 2), nullable=False, default=0)
    default_supplier = Column(String(255), nullable=True)
    unit_cost = Column(Numeric(10, 2), nullable=True)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    movements = relationship("RawMaterialMovement", back_populates="raw_material")


Index('idx_raw_materials_code', RawMaterial.material_code)
Index('idx_raw_materials_type', RawMaterial.material_type)


class RawMaterialMovement(Base):
    __tablename__ = "raw_material_movements"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    raw_material_id = Column(UUID(as_uuid=True), ForeignKey("raw_materials.id"), nullable=False)
    movement_type = Column(String(20), nullable=False)  # received | used | adjustment | stocktake
    quantity = Column(Numeric(12, 2), nullable=False)
    unit_cost = Column(Numeric(10, 2), nullable=True)
    supplier = Column(String(255), nullable=True)
    delivery_note = Column(String(255), nullable=True)
    reason = Column(Text, nullable=True)
    performed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    raw_material = relationship("RawMaterial", back_populates="movements")
    performer = relationship("User", foreign_keys=[performed_by])


Index('idx_raw_material_movements_material', RawMaterialMovement.raw_material_id)
Index('idx_raw_material_movements_date', RawMaterialMovement.created_at)