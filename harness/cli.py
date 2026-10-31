"""Command line entry point.

    python3 -m harness.cli run --task T1-01 --rung G1 --worker scripted:reference
    python3 -m harness.cli demo
    python3 -m harness.cli conformance
"""
import argparse
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "tasks"))

from tasks import TASKS
from . import runner

BY_ID = {t["id"]: t for t in TASKS}


def cmd_run(a):
    r = runner.run(BY_ID[a.task], a.rung, a.worker, a.repeat)
    print(f"{r['run_id']}")
    print(f"  gate_green={r['gate_green']} accepted={r['accepted']} "
          f"oracle={r['oracle_passed']} completion={r['completion']} "
          f"escape={r['gate_escape']} tamper={r['tamper']} leaked={r['oracle_leaked']} "
          f"{r['seconds']}s")
    for g in r["gates"]:
        print(f"    {g['gate']:16} ok={g['ok']}  {g.get('detail','')[:90]}")


def cmd_demo(a):
    tasks = a.tasks.split(",") if a.tasks else ["T1-01", "T2-S1", "T3-01"]
    rungs_ = a.rungs.split(",") if a.rungs else ["G0", "G1"]
    workers_ = a.workers.split(",") if a.workers else ["scripted:null", "scripted:reference", "scripted:tamper"]
    print(f"{'task':7} {'rung':5} {'worker':20} {'gate':5} {'oracle':7} {'done':5} {'escape':6} {'tamper':6}")
    for tid in tasks:
        for rid in rungs_:
            for w in workers_:
                r = runner.run(BY_ID[tid], rid, w)
                print(f"{tid:7} {rid:5} {w:20} {str(r['gate_green']):5} "
                      f"{str(r['oracle_passed']):7} {str(r['completion']):5} "
                      f"{str(r['gate_escape']):6} {str(r['tamper']):6}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="harness")
    sub = p.add_subparsers(required=True)

    r = sub.add_parser("run"); r.set_defaults(fn=cmd_run)
    r.add_argument("--task", required=True)
    r.add_argument("--rung", required=True)
    r.add_argument("--worker", default="scripted:reference")
    r.add_argument("--repeat", type=int, default=0)

    d = sub.add_parser("demo"); d.set_defaults(fn=cmd_demo)
    d.add_argument("--tasks"); d.add_argument("--rungs"); d.add_argument("--workers")

    a = p.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
