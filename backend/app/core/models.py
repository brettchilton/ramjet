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
    role = Column(String(50), default="inspector")  # inspector, admin, viewer
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


# ── Order Models ──────────────────────────────────────────────────────

class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    email_id = Column(Integer, ForeignKey("incoming_emails.id"), nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending | approved | rejected | error
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


Index('idx_order_line_items_order_id', OrderLineItem.order_id)