"""Add email monitoring tables

Revision ID: a1b2c3d4e5f6
Revises: 853ac57bb136
Create Date: 2026-02-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '853ac57bb136'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── incoming_emails ──────────────────────────────────────────────
    op.create_table('incoming_emails',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('gmail_message_id', sa.String(length=255), nullable=False),
        sa.Column('sender', sa.String(length=255), nullable=True),
        sa.Column('subject', sa.Text(), nullable=True),
        sa.Column('body_text', sa.Text(), nullable=True),
        sa.Column('body_html', sa.Text(), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('gmail_message_id'),
    )
    op.create_index('idx_incoming_emails_gmail_id', 'incoming_emails', ['gmail_message_id'], unique=False)
    op.create_index('idx_incoming_emails_processed', 'incoming_emails', ['processed'], unique=False)

    # ── email_attachments ────────────────────────────────────────────
    op.create_table('email_attachments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=True),
        sa.Column('content_type', sa.String(length=100), nullable=True),
        sa.Column('file_data', sa.LargeBinary(), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['email_id'], ['incoming_emails.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_email_attachments_email_id', 'email_attachments', ['email_id'], unique=False)

    # ── email_monitor_status (singleton) ─────────────────────────────
    op.create_table('email_monitor_status',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('is_running', sa.Boolean(), nullable=True),
        sa.Column('last_poll_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('emails_processed_total', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # Insert singleton row
    op.execute(
        "INSERT INTO email_monitor_status (id, is_running, emails_processed_total) "
        "VALUES (1, FALSE, 0)"
    )


def downgrade() -> None:
    op.drop_index('idx_email_attachments_email_id', table_name='email_attachments')
    op.drop_table('email_attachments')
    op.drop_index('idx_incoming_emails_processed', table_name='incoming_emails')
    op.drop_index('idx_incoming_emails_gmail_id', table_name='incoming_emails')
    op.drop_table('incoming_emails')
    op.drop_table('email_monitor_status')
