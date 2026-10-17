"""Testes unitários: regras sem HTTP/banco."""

import math

import pytest

from app.main import preco_com_desconto


@pytest.mark.parametrize(
    "preco,pct,esperado",
    [(10.0, 0, 10.0), (10.0, 10, 9.0), (8.5, 50, 4.25), (100, 25, 75)],
)
def test_desconto_valido(preco, pct, esperado):
    assert preco_com_desconto(preco, pct) == esperado


@pytest.mark.parametrize("desconto", [51, 80, -1, math.inf, math.nan])
def test_desconto_invalido(desconto):
    with pytest.raises(ValueError, match="desconto inválido"):
        preco_com_desconto(10.0, desconto)


@pytest.mark.parametrize("preco", [-10, math.nan, math.inf])
def test_preco_invalido(preco):
    with pytest.raises(ValueError, match="preço inválido"):
        preco_com_desconto(preco, 10)


def test_desconto_respeita_limite_configurado(monkeypatch):
    monkeypatch.setenv("DESCONTO_MAXIMO", "25")
    assert preco_com_desconto(10, 25) == 7.5
    with pytest.raises(ValueError, match="desconto inválido"):
        preco_com_desconto(10, 26)
