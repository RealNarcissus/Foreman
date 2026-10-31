"""Gate implementations. Each returns a decision plus the raw evidence."""
import json
import os
import pathlib
import subprocess

from . import config


def _env(worktree: pathlib.Path) -> dict:
    e = dict(os.environ)
    e["PYTHONPATH"] = str(worktree / "src")
    return e


def ci(worktree: pathlib.Path) -> dict:
    r = subprocess.run([config.PYTHON, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                       cwd=worktree, capture_output=True, text=True, env=_env(worktree))
    tail = "\n".join((r.stdout or r.stderr).strip().splitlines()[-3:])
    return {"gate": "ci", "ok": r.returncode == 0, "detail": tail}


def _baseline(worktree: pathlib.Path) -> dict:
    """Alerts present in the pristine subject. Computed once and cached."""
    cache = config.RUNS / "_codeql_baseline.json"
    if cache.exists():
        return json.loads(cache.read_text())
    tmp = worktree.parent / "_baseline_db"
    sarif = worktree.parent / "_baseline.sarif"
    subprocess.run([config.CODEQL, "database", "create", str(tmp), "--language=python",
                    f"--source-root={config.SUBJECT}", "--overwrite"],
                   check=True, capture_output=True)
    subprocess.run([config.CODEQL, "database", "analyze", str(tmp),
                    f"codeql/python-queries:codeql-suites/{config.QUERY_SUITE}",
                    *[f"--threat-model={tm}" for tm in config.THREAT_MODELS],
                    "--format=sarif-latest", f"--output={sarif}"],
                   check=True, capture_output=True)
    alerts = []
    for run in json.loads(sarif.read_text()).get("runs", []):
        for res in run.get("results", []):
            loc = (res.get("locations") or [{}])[0].get("physicalLocation", {})
            alerts.append({"rule": res.get("ruleId"),
                           "path": loc.get("artifactLocation", {}).get("uri"),
                           "line": loc.get("region", {}).get("startLine")})
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"alerts": alerts}, indent=2) + "\n")
    return {"alerts": alerts}


def static_analysis(worktree: pathlib.Path, baseline: dict | None = None) -> dict:
    """CodeQL with the frozen G2 configuration. Disabled unless FOREMAN_CODEQL_ENABLE=1."""
    if os.environ.get("FOREMAN_CODEQL_ENABLE") != "1":
        return {"gate": "static_analysis", "ok": True, "detail": "skipped (FOREMAN_CODEQL_ENABLE!=1)"}
    db = worktree.parent / "_codeql_db"
    sarif = worktree.parent / "_codeql.sarif"
    subprocess.run([config.CODEQL, "database", "create", str(db), "--language=python",
                    f"--source-root={worktree}", "--overwrite"],
                   check=True, capture_output=True)
    subprocess.run([config.CODEQL, "database", "analyze", str(db),
                    f"codeql/python-queries:codeql-suites/{config.QUERY_SUITE}",
                    *[f"--threat-model={tm}" for tm in config.THREAT_MODELS],
                    "--format=sarif-latest", f"--output={sarif}"],
                   check=True, capture_output=True)
    alerts = []
    d = json.loads(sarif.read_text())
    for run in d.get("runs", []):
        for res in run.get("results", []):
            loc = (res.get("locations") or [{}])[0].get("physicalLocation", {})
            alerts.append({
                "rule": res.get("ruleId"),
                "path": loc.get("artifactLocation", {}).get("uri"),
                "line": loc.get("region", {}).get("startLine"),
            })
    baseline = baseline or _baseline(worktree)
    base = {(a["rule"], a["path"]) for a in baseline.get("alerts", [])}
    new = [a for a in alerts if (a["rule"], a["path"]) not in base]
    security = [a for a in new if a["rule"] and a["rule"].startswith("py/")]
    return {"gate": "static_analysis", "ok": not security, "alerts": alerts,
            "new": new, "detail": f"{len(alerts)} alerts, {len(security)} new security"}


def ai_review(worktree: pathlib.Path, reviewer: dict | None) -> dict:
    """Stub until the reviewer prompt is committed and hashed."""
    return {"gate": "ai_review", "ok": True,
            "detail": "stub: reviewer prompt not yet pinned", "comments": []}


def human_review(worktree: pathlib.Path) -> dict:
    return {"gate": "human_review", "ok": False, "detail": "needs_human",
            "decision": "pending"}


IMPLEMENTATIONS = {
    "ci": ci,
    "static_analysis": static_analysis,
    "ai_review": ai_review,
    "human_review": human_review,
}


def run(rung: dict, worktree: pathlib.Path) -> list[dict]:
    results = []
    for name in rung["requires"]:
        fn = IMPLEMENTATIONS[name]
        if name == "ai_review":
            results.append(ai_review(worktree, rung.get("reviewer")))
        else:
            results.append(fn(worktree))
        if not results[-1]["ok"]:
            break
    return results
