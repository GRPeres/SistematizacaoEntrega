"""Migration 3: SOMENTE após o primeiro deploy produtivo.

Revision ID: 0003
Revises: 0002
"""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    # Expand: coluna nova com valor padrão, sem remover/renomear as antigas.
    op.add_column(
        "cafes",
        sa.Column(
            "origem", sa.String(100), nullable=True, server_default="Não informada"
        ),
    )
    op.execute("UPDATE cafes SET origem = 'Não informada' WHERE origem IS NULL")


def downgrade():
    # Atenção: reverter o esquema apagaria a coluna; rollback de código NÃO executa downgrade.
    op.drop_column("cafes", "origem")
