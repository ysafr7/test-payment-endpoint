"""add payments table

Revision ID: e4e2a4dbd937
Revises: 
Create Date: 2026-09-17 13:56:35.639226

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'e4e2a4dbd937'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "payments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("cart_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("carts.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.CHAR(3), nullable=False),
        sa.Column("status", sa.Text, nullable=False, server_default="pending"),
        sa.Column("provider_reference", sa.Text),
        sa.Column("failure_reason", sa.Text),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("amount >= 0", name="ck_payments_amount_non_negative"),
        sa.CheckConstraint("status IN ('pending', 'succeeded', 'failed')", name="ck_payments_status"),
    )
    op.create_index("idx_payments_cart_id", "payments", ["cart_id"])
    # At most one non-failed payment per cart, so a concurrent retry can't
    # charge the same cart twice.
    op.create_index(
        "idx_payments_active_per_cart",
        "payments",
        ["cart_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('pending', 'succeeded')"),
    )


def downgrade():
    op.drop_table("payments")
