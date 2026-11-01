"""Saturation diagnostic: 12 pilot tasks, one attempt each, G0. See docs/08."""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tasks"))

from harness import runner
from tasks import TASKS

OUT = ROOT / "ledger" / "saturation.json"
rows = []


def flush():
    OUT.write_text(json.dumps(rows, indent=2) + "\n")


for t in TASKS:
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
    print(f"{t['id']:6} tier{t['tier']} {rows[-1].get('completion')} "
          f"{rows[-1].get('seconds')}s", flush=True)
print("SATURATION DONE", flush=True)
