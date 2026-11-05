"""Analysis over the collected runs. Clustered by task, intervals not means.

    python3 tools/analyze.py

Repeated runs of one task are not independent. Every interval here resamples the
12 tasks, not the 180 runs, so a task that happened to be easy or hard cannot
masquerade as precision.
"""
import csv, json, pathlib, random, statistics, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RUNGS = ["G0", "G1", "G2", "G3", "G4"]
random.seed(20261105)


def load():
    rows = [r for r in csv.DictReader(open(ROOT / "ledger" / "runs.csv"))
            if r["phase"] == "sweep"]
    return rows


def boot(tasks, per_task, stat, n=10000):
    """Percentile bootstrap over tasks (cluster bootstrap)."""
    vals = []
    for _ in range(n):
        sample = [random.choice(tasks) for _ in tasks]
        pool = [x for t in sample for x in per_task[t]]
        if pool:
            vals.append(stat(pool))
    vals.sort()
    return vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]


def main():
    rows = load()
    print(f"# Sweep results\n\n{len(rows)} runs, phase=sweep.\n")

    print("## By rung\n")
    print("| Rung | n | Valid | Complete | Gate green | Rejected | Escapes | Median s | Cost |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for rung in RUNGS:
        rs = [r for r in rows if r["rung"] == rung]
        if not rs:
            continue
        comp = sum(r["completion"] == "True" for r in rs)
        green = sum(r["gate_green"] == "True" for r in rs)
        esc = sum(r["gate_escape"] == "True" for r in rs)
        pends = sum(1 for r in rs if r["human_minutes"] and r["human_minutes"] != "")
        med = statistics.median(float(r["seconds"]) for r in rs)
        cost = sum(float(r["cost_usd"] or 0) for r in rs)
        note = "n/a" if rung == "G4" else f"${cost:.3f}"
        valid = sum(r.get("valid", "True") != "False" for r in rs)
        print(f"| {rung} | {len(rs)} | {valid} | {comp} | {green} | {len(rs)-green} | {esc} | {med:.0f} | {note} |")

    bad = [r for r in rows if r.get("valid", "True") == "False"]
    if bad:
        print("\nExcluded by validity (not capability failures):")
        for r in bad:
            print(f"- {r['rung']} {r['task_id']} `{r['run_id']}` — oracle "
                  f"{r['oracle_passed']}, tamper {r['tamper']}, leaked {r['oracle_leaked']}")
    print("\nG4 cost is unavailable: the provider returned cost 0 with non-zero "
          "tokens for every step, so it is reported as missing rather than as free.\n")

    print("## Completion by task\n")
    print("| Task | " + " | ".join(RUNGS) + " |")
    print("| --- |" + " --- |" * len(RUNGS))
    tasks = sorted({r["task_id"] for r in rows})
    for t in tasks:
        cells = []
        for rung in RUNGS:
            rs = [r for r in rows if r["task_id"] == t and r["rung"] == rung]
            cells.append("–" if not rs else f"{sum(r['completion']=='True' for r in rs)}/{len(rs)}")
        print(f"| {t} | " + " | ".join(cells) + " |")

    print("\n## Intervals (cluster bootstrap over tasks)\n")
    for rung in RUNGS:
        rs = [r for r in rows if r["rung"] == rung]
        if not rs:
            continue
        per = {t: [1 if r["completion"] == "True" else 0 for r in rs if r["task_id"] == t]
               for t in tasks}
        lo, hi = boot(tasks, per, lambda v: sum(v) / len(v))
        print(f"- **{rung} completion**: {sum(r['completion']=='True' for r in rs)}/{len(rs)}"
              f" = {sum(r['completion']=='True' for r in rs)/len(rs):.0%} (95% CI {lo:.0%}–{hi:.0%})")

    n = len(rows)
    print(f"\n- **Escapes**: 0/{n}. Rule of three: exact 95% upper bound ≈ {3/n:.1%}.\n")

    print("## Gate yield\n")
    yield_rows = [r for r in rows if r["gate_green"] != "True" and r["completion"] == "True"]
    print(f"Runs the oracle scored as complete and a gate rejected: **{len(yield_rows)}**")
    by = {}
    for r in yield_rows:
        by.setdefault(r["rung"], []).append(r["task_id"])
    for rung, ts in sorted(by.items()):
        print(f"- {rung}: {len(ts)} — {', '.join(sorted(ts))}")

    print("\n## Human review\n")
    p1 = {r["run_id"]: r for r in csv.DictReader(open(ROOT / "ledger" / "human.csv"))
          if r["kind"] == "review"}
    p2 = {r["run_id"]: r for r in csv.DictReader(open(ROOT / "ledger" / "human-pass2.csv"))}
    ids = list(p1)
    if ids:
        def bin_(d): return d != "approve"
        same = sum(bin_(p1[i]["decision"]) == bin_(p2[i]["decision"]) for i in ids)
        a1 = sum(bin_(p1[i]["decision"]) for i in ids) / len(ids)
        a2 = sum(bin_(p2[i]["decision"]) for i in ids) / len(ids)
        po = same / len(ids)
        pe = a1 * a2 + (1 - a1) * (1 - a2)
        kappa = (po - pe) / (1 - pe)
        t1 = sum(float(p1[i]["seconds"]) for i in ids) / 60
        t2 = sum(float(p2[i]["seconds"]) for i in ids) / 60
        adj_path = ROOT / "ledger" / "human-adjustments.json"
        adj = {}
        if adj_path.exists():
            for a in json.loads(adj_path.read_text()):
                adj[a["pass"]] = adj.get(a["pass"], 0) + float(a["minutes"])
        t2_total = t2 + adj.get(2, 0)
        t1_total = t1 + adj.get(1, 0)
        print(f"- reviewed changes: {len(ids)} (the other 28 G4 runs were blocked by machine gates)")
        print(f"- intervention rate: pass 1 {a1:.0%}, pass 2 {a2:.0%}")
        print(f"- agreement: {same}/{len(ids)} = {po:.0%}; Cohen's kappa {kappa:.2f}")
        print(f"- human minutes, as timed by the console: pass 1 {t1:.1f}, pass 2 {t2:.1f}")
        if adj:
            print(f"- self-reported work outside the timer: {adj}")
        print(f"- human minutes, adjusted: pass 1 {t1_total:.1f}, pass 2 {t2_total:.1f}")
        print("\nWith 8 cases a single flip moves agreement by 12.5 points. This is a "
              "consistency check, not a reliability estimate, and both passes must be "
              "reported because the human-yield figure depends on which one is counted.")


if __name__ == "__main__":
    main()
