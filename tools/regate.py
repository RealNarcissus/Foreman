"""Re-evaluate the gate chain on an existing run's stored diff, without an agent.

Used when a rung's gate configuration was wrong but the worker artifact is fine:
the diff is the treatment input, so re-running the gates on it is the same
operation as re-running CI on a saved patch. The agent's cost and duration stay
untouched; only `gates` and gate-derived flags change.

    FOREMAN_CODEQL_ENABLE=1 FOREMAN_CODEQL=$HOME/.codeql/codeql/codeql \
      python3 tools/regate.py --rung G4
"""
import argparse, json, pathlib, shutil, subprocess, sys, tempfile
import concurrent.futures as cf

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tasks"))

from harness import config, gates, runner, rungs, sandbox
from revision import SWEEP

BY_ID = {t["id"]: t for t in SWEEP}


def regate(run_id, task_id, rung_id):
    base = config.RUNS / run_id
    diff = (base / "diff.patch").read_text()
    wt = pathlib.Path(tempfile.mkdtemp(prefix="regate-")) / "worktree"
    runner.prepare(wt, None)
    patch_file = wt.parent / "change.patch"
    patch_file.write_text(diff)
    p = subprocess.run(["git", "apply", "--whitespace=nowarn", str(patch_file)],
                       cwd=wt, capture_output=True, text=True)
    if p.returncode != 0:
        return {"run_id": run_id, "error": f"git apply: {p.stderr.strip()[:120]}"}
    home = sandbox.home_for(f"regate-{run_id}")
    try:
        res = gates.run(rungs.load(rung_id), wt, diff=diff,
                        spec=BY_ID[task_id]["spec"], home=home)
    finally:
        # Each sandbox HOME carries a credential tree (~150MB); 36 of them fill
        # the tmpfs that every worktree also lives on.
        shutil.rmtree(home, ignore_errors=True)
    rec_path = base / "record.json"
    rec = json.loads(rec_path.read_text())
    rec["gates"] = res
    rec["regate_at"] = __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc).isoformat()
    rec_path.write_text(json.dumps(rec, indent=2) + "\n")
    shutil.rmtree(wt.parent, ignore_errors=True)
    return {"run_id": run_id, "gates": [(g["gate"], g["ok"], g.get("decision")) for g in res]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rung", default="G4")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    import csv
    rows = [r for r in csv.DictReader(open(ROOT / "ledger" / "runs.csv"))
            if r["phase"] == "sweep" and r["rung"] == a.rung]
    if a.limit:
        rows = rows[: a.limit]
    print(f"re-gating {len(rows)} runs at {a.rung}")
    with cf.ThreadPoolExecutor(max_workers=a.concurrency) as pool:
        for res in pool.map(lambda r: regate(r["run_id"], r["task_id"], a.rung), rows):
            print(res, flush=True)


if __name__ == "__main__":
    main()
