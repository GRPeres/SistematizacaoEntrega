"""Migration 2: cardápio inicial com cinco cafés.

Revision ID: 0002
Revises: 0001
"""

from decimal import Decimal

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    tabela = sa.table(
        "cafes",
        sa.column("id", sa.Integer()),
        sa.column("nome", sa.String(80)),
        sa.column("preco", sa.Numeric(8, 2)),
    )
    op.bulk_insert(
        tabela,
        [
            {"id": 1, "nome": "Cerrado Mineiro", "preco": Decimal("16.90")},
            {"id": 2, "nome": "Chapada Diamantina", "preco": Decimal("19.90")},
            {"id": 3, "nome": "Mogiana", "preco": Decimal("15.50")},
            {"id": 4, "nome": "Sul de Minas", "preco": Decimal("17.00")},
            {"id": 5, "nome": "Mantiqueira", "preco": Decimal("23.00")},
        ],
    )
    # Corrige a sequência de IDs quando se usa PostgreSQL (inserções com IDs explícitos).
    connection = op.get_bind()
    if connection.dialect.name == "postgresql":
        connection.execute(
            sa.text("SELECT setval(pg_get_serial_sequence('cafes','id'), "
                    "(SELECT MAX(id) FROM cafes), true)")
        )


def downgrade():
    op.execute("DELETE FROM cafes WHERE id IN (1,2,3,4,5)")
