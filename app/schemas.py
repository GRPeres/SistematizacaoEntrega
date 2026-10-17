"""Contratos HTTP e validação dos pedidos."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CafeCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=80)
    preco: Decimal = Field(gt=0, max_digits=8, decimal_places=2)


class CafeOut(CafeCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    origem: str | None = None
