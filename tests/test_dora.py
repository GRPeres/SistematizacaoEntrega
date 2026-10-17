"""Um workflow verde sem produção não pode inflar a frequência de deploy."""

import pytest

from scripts.dora import completed_production_job


@pytest.mark.parametrize("conclusion", ["skipped", "failure", "success"])
def test_conta_somente_job_produtivo_concluido_com_sucesso(conclusion):
    job = {"name": "production / deploy", "status": "completed", "conclusion": conclusion}
    assert completed_production_job([job]) == (job if conclusion == "success" else None)
