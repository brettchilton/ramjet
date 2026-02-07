"""Add order tables

Revision ID: c3d4e5f6g7h8
Revises: a1b2c3d4e5f6
Create Date: 2026-02-07 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6g7h8'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── orders ────────────────────────────────────────────────────────
    op.create_table('orders',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('email_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('customer_name', sa.String(length=255), nullable=True),
        sa.Column('po_number', sa.String(length=100), nullable=True),
        sa.Column('po_date', sa.Date(), nullable=True),
        sa.Column('delivery_date', sa.Date(), nullable=True),
        sa.Column('special_instructions', sa.Text(), nullable=True),
        sa.Column('extraction_confidence', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('extraction_raw_json', JSONB(), nullable=True),
        sa.Column('approved_by', UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_reason', sa.Text(), nullable=True),
        sa.Column('office_order_file', sa.LargeBinary(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['email_id'], ['incoming_emails.id']),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_orders_status', 'orders', ['status'], unique=False)
    op.create_index('idx_orders_email', 'orders', ['email_id'], unique=False)

    # ── order_line_items ──────────────────────────────────────────────
    op.create_table('order_line_items',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('order_id', UUID(as_uuid=True), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('product_code', sa.String(length=50), nullable=True),
        sa.Column('matched_product_code', sa.String(length=50), nullable=True),
        sa.Column('product_description', sa.String(length=255), nullable=True),
        sa.Column('colour', sa.String(length=100), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('line_total', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('confidence', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('needs_review', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('works_order_file', sa.LargeBinary(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['matched_product_code'], ['products.product_code']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_order_line_items_order_id', 'order_line_items', ['order_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_order_line_items_order_id', table_name='order_line_items')
    op.drop_table('order_line_items')
    op.drop_index('idx_orders_email', table_name='orders')
    op.drop_index('idx_orders_status', table_name='orders')
    op.drop_table('orders')
