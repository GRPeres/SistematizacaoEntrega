"""Migration 1: cria tabela cafes.

Revision ID: 0001
Revises:
"""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cafes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=80), nullable=False, unique=True),
        sa.Column("preco", sa.Numeric(precision=8, scale=2), nullable=False),
    )


def downgrade():
    op.drop_table("cafes")
