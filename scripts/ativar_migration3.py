"""Após o primeiro deploy, copia a migration 3 para o Alembic.

Execute e faça commit em uma NOVA pull request, nunca antes da primeira produção.
"""

from pathlib import Path
import shutil

root = Path(__file__).resolve().parent.parent
source = root / "extras" / "migration3" / "0003_add_origem.py"
target = root / "migrations" / "versions" / source.name
if target.exists():
    raise SystemExit("Migration 3 já foi ativada.")
shutil.copy2(source, target)
print(f"Migration ativada: {target}")
print("Abra novo PR após v1.0.0 entrar em produção. Não faça alembic downgrade.")
