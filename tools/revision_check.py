"""Revision saturation check: the four R3 tasks, one attempt each, G0.

The pre-registered decision table is docs/09-revision-saturation-check.md and is
written to be read before these results. Run: python3 tools/revision_check.py
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tasks"))

from harness import runner
from revision import REVISION

OUT = ROOT / "ledger" / "revision-saturation.json"
rows = []


def flush():
    OUT.write_text(json.dumps(rows, indent=2) + "\n")


for t in REVISION:
    try:
        r = runner.run(t, "G0", "opencode:deepseek-v4.1-flash")
        rows.append({"task": t["id"], "tier": t["tier"], "cls": t["cls"],
                     "completion": r["completion"], "oracle": r["oracle_passed"],
                     "valid": r["valid"], "infra": r["action"].get("infra_error"),
                     "probe_ok": r["sandbox_probe"]["ok"], "seconds": r["seconds"],
                     "cost_usd": r["action"].get("cost_usd")})
    except Exception as exc:
        rows.append({"task": t["id"], "error": f"{type(exc).__name__}: {exc}"})
    flush()
    print(f"{t['id']:6} {rows[-1].get('completion')} {rows[-1].get('seconds')}s "
          f"oracle={rows[-1].get('oracle')} infra={rows[-1].get('infra')}", flush=True)
print("REVISION CHECK DONE", flush=True)
