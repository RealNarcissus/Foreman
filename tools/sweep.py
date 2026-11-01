"""M3 sweep driver: rungs x tasks x k, resumable, phase="sweep".

Resumability is by (task, rung, repeat) read back from the ledger, not by run id:
run ids carry a timestamp, so a resume would otherwise re-run completed work.

    python3 tools/sweep.py --rungs G0,G1,G2 --dry-run
    python3 tools/sweep.py --rungs G0,G1,G2 --limit 20

Each invocation runs at most `--limit` jobs, so a chunk fits inside a terminal
call; the next invocation picks up where this one stopped.
"""
import argparse, collections, csv, pathlib, sys, threading
import concurrent.futures as cf

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tasks"))

from harness import runner
from revision import SWEEP

WORKER = "opencode:deepseek-v4.1-flash"
ALL_RUNGS = ["G0", "G1", "G2", "G3", "G4"]
print_lock = threading.Lock()


def completed() -> set:
    path = ROOT / "ledger" / "runs.csv"
    if not path.exists():
        return set()
    out = set()
    for row in csv.DictReader(path.open()):
        if row.get("phase") != "sweep":
            continue
        rep = row["run_id"].rsplit("_r", 1)[-1].split("_")[0]
        out.add((row["task_id"], row["rung"], rep))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rungs", default="G0,G1,G2")
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0, help="0 = all remaining")
    ap.add_argument("--max-usd", type=float, default=0.0, help="0 = no cap")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    rungs = [r for r in a.rungs.split(",") if r]
    unknown = [r for r in rungs if r not in ALL_RUNGS]
    if unknown:
        sys.exit(f"unknown rung(s): {unknown}")

    done = completed()
    by_id = {t["id"]: t for t in SWEEP}
    jobs = [(by_id[t], r, str(i))
            for r in rungs for t in by_id for i in range(a.k)
            if (t, r, str(i)) not in done]

    print(f"plan: {len(rungs)} rungs x {len(by_id)} tasks x k={a.k} "
          f"= {len(rungs) * len(by_id) * a.k} runs")
    print(f"already recorded as sweep: {len(done)}; remaining: {len(jobs)}")
    if a.dry_run or not jobs:
        for r in rungs:
            n = sum(1 for j in jobs if j[1] == r)
            print(f"  {r}: {n} remaining")
        return

    total_remaining = len(jobs)
    if a.limit:
        jobs = jobs[: a.limit]

    totals = collections.Counter()
    spend = [0.0]
    lock = threading.Lock()

    def work(job):
        task, rung, repeat = job
        with lock:
            if a.max_usd and spend[0] >= a.max_usd:
                return None
        try:
            r = runner.run(task, rung, WORKER, repeat=int(repeat), phase="sweep")
        except Exception as exc:
            return (task["id"], rung, repeat, None, f"{type(exc).__name__}: {exc}")
        cost = r["action"].get("cost_usd") or 0.0
        with lock:
            spend[0] += cost
        return (task["id"], rung, repeat, r, None)

    with cf.ThreadPoolExecutor(max_workers=a.concurrency) as pool:
        for res in pool.map(work, jobs):
            if res is None:
                continue
            tid, rung, repeat, r, err = res
            with print_lock:
                if err:
                    totals["error"] += 1
                    print(f"{tid:6} {rung} r{repeat}  ERROR {err[:90]}", flush=True)
                else:
                    ok = r["completion"]
                    infra = r["action"].get("infra_error")
                    totals["infra" if infra else
                           "complete" if ok else
                           "incomplete"] += 1
                    totals["escape"] += bool(r["gate_escape"])
                    print(f"{tid:6} {rung} r{repeat}  "
                          f"done={ok} escape={r['gate_escape']} "
                          f"infra={bool(infra)} {r['seconds']}s "
                          f"${(r['action'].get('cost_usd') or 0):.4f} "
                          f"| total ${spend[0]:.3f}", flush=True)

    print("\nthis chunk:", dict(totals))
    ran = sum(totals.values())
    print(f"ran in this chunk: {ran}; remaining: {total_remaining - ran + totals['error']}")


if __name__ == "__main__":
    main()
