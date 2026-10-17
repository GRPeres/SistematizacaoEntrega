"""Upgrade real de 0002 para 0003 em banco descartável, nunca produção."""

import os
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


@pytest.fixture
def migration_database(tmp_path):
    test_url = os.getenv("TEST_DATABASE_URL", "")
    if not test_url or test_url.startswith("sqlite"):
        yield f"sqlite:///{(tmp_path / 'migration-test.db').as_posix()}"
        return

    # O CI usa PostgreSQL. Um banco NOVO separa as migrations dos testes de API.
    database_name = f"cafe_migration_test_{uuid4().hex}"
    admin = create_engine(test_url, isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{database_name}"'))
        try:
            yield make_url(test_url).set(database=database_name).render_as_string(
                hide_password=False
            )
        finally:
            with admin.connect() as connection:
                connection.execute(text(f'DROP DATABASE "{database_name}"'))
    finally:
        admin.dispose()


def test_upgrade_preserva_cardapio_e_registro_existente(migration_database, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", migration_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0002")
    engine = create_engine(migration_database)
    try:
        with engine.begin() as connection:
            connection.execute(
                text("INSERT INTO cafes (nome, preco) VALUES ('Café preservado', 27.45)")
            )
            before = connection.execute(
                text("SELECT id, nome, preco FROM cafes ORDER BY id")
            ).all()
        assert len(before) == 6

        command.upgrade(config, "head")
        command.upgrade(config, "head")  # Reiniciar o container não reaplica o seed.

        with engine.begin() as connection:
            # Esta projeção também comprova compatibilidade com o código antigo.
            after = connection.execute(
                text("SELECT id, nome, preco FROM cafes ORDER BY id")
            ).all()
            assert after == before
            assert connection.execute(
                text("SELECT DISTINCT origem FROM cafes")
            ).scalars().all() == ["Não informada"]
            assert connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one() == "0003"
            connection.execute(
                text("INSERT INTO cafes (nome, preco) VALUES ('Café novo', 31.50)")
            )
            assert connection.execute(
                text("SELECT origem FROM cafes WHERE nome = 'Café novo'")
            ).scalar_one() == "Não informada"
    finally:
        engine.dispose()
