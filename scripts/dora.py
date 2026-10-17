"""Estimativa transparente de métricas DORA usando execuções reais de GitHub Actions.

Uso: python scripts/dora.py DONO/NOME-REPOSITORIO
Opcional: GITHUB_TOKEN para evitar rate limit da API.
Não fabrica números: use somente após execuções efetivas da pipeline.
"""

import datetime as dt
import json
import os
import sys
import urllib.request


def github_json(path):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "cafe-com-deploy-dora-academico",
            **(
                {"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"]}
                if os.getenv("GITHUB_TOKEN")
                else {}
            ),
        },
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)


def parse_time(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def main(repo):
    cd = github_json(f"/repos/{repo}/actions/workflows/cd.yml/runs?per_page=100")
    roll = github_json(f"/repos/{repo}/actions/workflows/rollback.yml/runs?per_page=100")
    successes = [r for r in cd.get("workflow_runs", []) if r.get("conclusion") == "success"]
    rollbacks = [r for r in roll.get("workflow_runs", []) if r.get("conclusion") == "success"]
    lead_hours = []
    for run in successes:
        commit = run.get("head_commit") or {}
        submitted = parse_time(commit.get("timestamp"))
        delivered = parse_time(run.get("updated_at"))
        if submitted and delivered and delivered >= submitted:
            lead_hours.append((delivered - submitted).total_seconds() / 3600)
    print("DORA (amostra de até 100 runs por workflow)")
    print("Deploys concluídos em produção:", len(successes))
    print("Lead time médio, commit -> fim do workflow:",
          f"{sum(lead_hours) / len(lead_hours):.2f} h" if lead_hours else "N/D")
    print("Rollbacks concluídos:", len(rollbacks))
    print("ATENÇÃO: taxa de falha e tempo de recuperação exigem registro manual")
    print("de quais deploys foram falhos e dos instantes da detecção/restauração;")
    print("não inferir só contando rollbacks (pode haver mais de um por incidente).")
    print("Dados consultados em:", dt.datetime.now(dt.timezone.utc).isoformat())


if __name__ == "__main__":
    if len(sys.argv) != 2 or "/" not in sys.argv[1]:
        raise SystemExit("Uso: python scripts/dora.py DONO/REPO")
    main(sys.argv[1])
