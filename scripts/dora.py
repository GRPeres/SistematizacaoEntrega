"""DORA a partir de jobs produtivos verificados; exclui builds sem deploy.

Uso: python scripts/dora.py DONO/REPO [--output arquivo.json]
Os incidentes precisam de registro humano; rollback de exercício não é incidente.
"""

import argparse
import datetime as dt
import json
import os
import statistics
import urllib.request
from pathlib import Path


def github_json(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "cafe-dora"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request("https://api.github.com" + path, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def pages(path, key):
    page = 1
    while True:
        separator = "&" if "?" in path else "?"
        batch = github_json(f"{path}{separator}per_page=100&page={page}")[key]
        yield from batch
        if len(batch) < 100:
            return
        page += 1


def parse_time(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def completed_production_job(jobs):
    names = {"production / deploy", "aprovar-e-implantar-producao"}
    return next(
        (job for job in jobs if job["name"] in names
         and job["status"] == "completed" and job["conclusion"] == "success"),
        None,
    )


def verification_time(job, names):
    for step in job.get("steps", []):
        if step["name"] in names and step["conclusion"] == "success":
            return step["completed_at"]
    return job["completed_at"]


def collect(repo):
    prefix = f"/repos/{repo}"
    registry_path = Path(__file__).resolve().parent.parent / "docs/incident-register.json"
    registry = json.loads(registry_path.read_text("utf-8-sig")) if registry_path.exists() else None
    deployments = []
    excluded = []
    for run in pages(prefix + "/actions/workflows/cd.yml/runs", "workflow_runs"):
        if run["status"] != "completed":
            continue
        jobs = list(pages(prefix + f"/actions/runs/{run['id']}/jobs", "jobs"))
        job = completed_production_job(jobs)
        if job is None:
            excluded.append({"run_id": run["id"], "url": run["html_url"],
                             "reason": "No successful production deployment job"})
            continue
        commit = github_json(prefix + f"/commits/{run['head_sha']}")
        committed_at = commit["commit"]["committer"]["date"]
        verified_at = verification_time(
            job, {"Wait for Watchtower and verify public API", "Smoke test em produção"}
        )
        deployments.append({
            "run_id": run["id"], "url": run["html_url"], "sha": run["head_sha"],
            "commit_time_utc": committed_at, "verified_time_utc": verified_at,
            "lead_seconds": (parse_time(verified_at) - parse_time(committed_at)).total_seconds(),
        })
    drills = []
    for run in pages(prefix + "/actions/workflows/rollback.yml/runs", "workflow_runs"):
        if run["conclusion"] != "success":
            continue
        jobs = list(pages(prefix + f"/actions/runs/{run['id']}/jobs", "jobs"))
        for job in jobs:
            if job["conclusion"] != "success":
                continue
            verified_at = verification_time(job, {"Verify recovery"})
            drills.append({
                "run_id": run["id"], "url": run["html_url"],
                "requested_at_utc": run["created_at"], "verified_at_utc": verified_at,
                "request_to_verified_seconds": (
                    parse_time(verified_at) - parse_time(run["created_at"])
                ).total_seconds(),
                "classification": (
                    "rollback exercise, not a recorded production incident"
                    if registry and run["id"] in registry.get("rollback_drill_run_ids", [])
                    else "unclassified rollback; requires incident review"
                ),
            })
    incident_ids = {
        incident["deployment_run_id"] for incident in registry.get("incidents", [])
    } if registry else set()
    failed_changes = len(incident_ids & {event["run_id"] for event in deployments})
    return {
        "repository": repo,
        "collected_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "method": "Successful production job; commit committer time to smoke completion",
        "production_deployments": sorted(deployments, key=lambda item: item["verified_time_utc"]),
        "deployment_count": len(deployments),
        "mean_lead_seconds": statistics.mean(item["lead_seconds"] for item in deployments)
        if deployments else None,
        "excluded_cd_runs": excluded,
        "rollback_drills": drills,
        "registered_production_incidents": failed_changes if registry else None,
        "change_failure_rate_percent": 100 * failed_changes / len(deployments)
        if registry is not None and deployments else None,
        "failed_deployment_recovery_time": None,
        "incident_note": "Based on docs/incident-register.json; never infer incidents from rollback count",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = collect(args.repository)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
