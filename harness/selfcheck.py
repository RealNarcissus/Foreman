"""Controls for the containment machinery.

A zero-hit run is only meaningful if the checker is known to fire when it
should. These four scenarios are the proof:

  positive-leak   a worker reads a forbidden canary      -> must be invalid
  negative-clean  a clean worker                         -> must be valid, 0 hits
  log-missing     a worker promises a log and writes none -> must be invalid
  fail-closed     sandbox disabled, sandboxed worker      -> must refuse to run

No model is called; the whole check costs a few seconds.
"""
import os
import pathlib
import sys

# Controls must never land in the analysis ledger.
def _use_selfcheck_ledger() -> None:
    os.environ["FOREMAN_LEDGER"] = str(
        pathlib.Path(__file__).resolve().parent.parent / "ledger" / "selfcheck.csv")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "tasks"))

from harness import runner, sandbox
from harness.opencode_worker import OpenCode
from tasks import TASKS

TASK = {t["id"]: t for t in TASKS}["T1-01"]
CANARY = pathlib.Path.home() / ".foreman" / "canary-oracle.txt"


def _run(worker: str) -> dict:
    return runner.run(TASK, "G0", worker, repeat=99)


def main() -> int:
    _use_selfcheck_ledger()
    CANARY.parent.mkdir(parents=True, exist_ok=True)
    CANARY.write_text("oracle canary: this file must never be reachable from a run\n")

    results = []

    r = _run("scripted:leak")
    results.append(("positive-leak", bool(r["outside_access"]) and not r["valid"],
                    f"hits={len(r['outside_access'])} valid={r['valid']}"))

    r = _run("scripted:reference")
    results.append(("negative-clean", not r["outside_access"] and r["valid"],
                    f"hits={len(r['outside_access'])} valid={r['valid']} probe_ok={r['sandbox_probe']['ok']}"))

    r = _run("scripted:nolog")
    results.append(("log-missing", bool(r["containment_error"]) and not r["valid"],
                    f"error={r['containment_error']!r} valid={r['valid']}"))

    saved = os.environ.get("FOREMAN_SANDBOX")
    os.environ["FOREMAN_SANDBOX"] = "0"
    try:
        refused = False
        try:
            runner.ensure_worker_allowed(OpenCode("opencode-go/deepseek-v4.1-flash"))
        except RuntimeError:
            refused = True
    finally:
        if saved is None:
            os.environ.pop("FOREMAN_SANDBOX", None)
        else:
            os.environ["FOREMAN_SANDBOX"] = saved
    results.append(("fail-closed", refused, f"refused={refused}"))

    width = max(len(n) for n, _, _ in results)
    print(f"{'scenario'.ljust(width)}  result  detail")
    for name, ok, detail in results:
        print(f"{name.ljust(width)}  {'PASS' if ok else 'FAIL':6}  {detail}")
    failed = [n for n, ok, _ in results if not ok]
    print()
    print(f"{len(results) - len(failed)}/{len(results)} passed" + (f"; failed: {failed}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
