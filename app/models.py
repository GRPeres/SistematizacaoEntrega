"""Modelos do banco versionados pelas migrations do Alembic."""

from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Cafe(Base):
    __tablename__ = "cafes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    preco: Mapped[Decimal] = mapped_column(Numeric(8, 2, asdecimal=True), nullable=False)
    origem: Mapped[str | None] = mapped_column(
        String(100), nullable=True, server_default="Não informada"
    )
