"""Rotas da API e regra de desconto - demonstrativo educacional."""

import math
import os

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Cafe
from app.schemas import CafeCreate, CafeOut

app = FastAPI(title="Café com Deploy", version="1.0.0")


def preco_com_desconto(preco: float, pct: float) -> float:
    """Aplica desconto dentro do limite; lança ValueError quando inválido."""
    maximo = float(os.getenv("DESCONTO_MAXIMO", "50"))
    if not (math.isfinite(preco) and preco >= 0):
        raise ValueError("preço inválido")
    if not (math.isfinite(pct) and 0 <= pct <= maximo):
        raise ValueError("desconto inválido")
    return round(preco * (1 - pct / 100), 2)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"version": os.getenv("APP_VERSION", "dev")}


@app.get("/cafes", response_model=list[CafeOut])
def listar_cafes(db: Session = Depends(get_db)):
    return db.scalars(select(Cafe).order_by(Cafe.id)).all()


@app.post("/cafes", status_code=status.HTTP_201_CREATED, response_model=CafeOut)
def criar_cafe(novo: CafeCreate, db: Session = Depends(get_db)):
    cafe = Cafe(nome=novo.nome.strip(), preco=novo.preco)
    if len(cafe.nome) < 2:
        raise HTTPException(status_code=422, detail="nome muito curto")
    db.add(cafe)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="café já cadastrado") from None
    db.refresh(cafe)
    return cafe


@app.get("/cafes/{cafe_id}", response_model=CafeOut)
def obter_cafe(cafe_id: int, db: Session = Depends(get_db)):
    cafe = db.get(Cafe, cafe_id)
    if cafe is None:
        raise HTTPException(status_code=404, detail="café não encontrado")
    return cafe


@app.get("/cafes/{cafe_id}/preco")
def consultar_preco(
    cafe_id: int,
    desconto: float = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    cafe = db.get(Cafe, cafe_id)
    if cafe is None:
        raise HTTPException(status_code=404, detail="café não encontrado")
    try:
        preco = preco_com_desconto(float(cafe.preco), desconto)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"id": cafe.id, "nome": cafe.nome, "desconto": desconto, "preco_final": preco}
