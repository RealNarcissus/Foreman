"""M2 smoke test: worker selection on holdout tasks. Descriptive, not a sweep.

3 models x 2 holdout tasks x 4 attempts = 24 runs, all at G0 so the gate cannot
help and the oracle alone decides.
"""
import json, pathlib, sys, traceback

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tasks"))
sys.path.insert(0, str(ROOT / "tools"))

from harness import runner
from holdout import HOLDOUT

MODELS = ["opencode:deepseek-v4.1-flash", "opencode:claude-haiku-5-5", "opencode:mimo-v2.6-flash"]
TASKS = ["H1", "H2"]
ATTEMPTS = 4
OUT = ROOT / "ledger" / "smoke.json"

by_id = {t["id"]: t for t in HOLDOUT}
rows = []


def flush():
    OUT.write_text(json.dumps(rows, indent=2) + "\n")


for model in MODELS:
    for tid in TASKS:
        for attempt in range(ATTEMPTS):
            try:
                r = runner.run(by_id[tid], "G0", model, attempt)
                rows.append({
                    "model": model, "task": tid, "attempt": attempt,
                    "completion": r["completion"], "oracle_passed": r["oracle_passed"],
                    "valid": r["valid"], "seconds": r["seconds"],
                    "cost_usd": r["action"].get("cost_usd"),
                    "tokens": r["action"].get("tokens"),
                    "timed_out": r["action"].get("timed_out"),
                    "infra_error": r["action"].get("infra_error"),
                })
            except Exception as exc:
                rows.append({"model": model, "task": tid, "attempt": attempt,
                             "error": f"{type(exc).__name__}: {exc}"})
            flush()
            print(f"{model:32} {tid} #{attempt} "
                  f"done={rows[-1].get('completion')} cost={rows[-1].get('cost_usd')}",
                  flush=True)
print("SMOKE DONE", flush=True)
