"""Generate the README figures from the ledger.

    python3 tools/make_figures.py

Every figure is derived from `ledger/`, so a rerun reproduces them exactly; none
of them are screenshots or hand-drawn. SVG so GitHub renders them crisply.
"""
import csv, json, pathlib, random, statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "figures"
RUNGS = ["G0", "G1", "G2", "G3", "G4"]
random.seed(20261105)

INK = "#1f2328"
MUTED = "#6e7781"
GREEN = "#2da44e"
RED = "#cf222e"
BLUE = "#0969da"
GREY = "#d0d7de"

plt.rcParams.update({
    "font.size": 10, "axes.edgecolor": GREY, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK, "text.color": INK,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white", "axes.facecolor": "white",
})


def headed(ax, title, sub=None):
    """Title with an optional subtitle underneath, never overlapping."""
    ax.set_title(title, loc="left", fontweight="bold", pad=24 if sub else 8)
    if sub:
        ax.text(0, 1.015, sub, transform=ax.transAxes, color=MUTED, fontsize=8)


def rows():
    return [r for r in csv.DictReader(open(ROOT / "ledger" / "runs.csv"))
            if r["phase"] == "sweep"]


def boot(tasks, per_task, stat, n=5000):
    vals = []
    for _ in range(n):
        s = [random.choice(tasks) for _ in tasks]
        pool = [x for t in s for x in per_task[t]]
        if pool:
            vals.append(stat(pool))
    vals.sort()
    return vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]


def fig_completion(rs):
    tasks = sorted({r["task_id"] for r in rs})
    fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=100)
    xs, ys, los, his = [], [], [], []
    for i, rung in enumerate(RUNGS):
        rr = [r for r in rs if r["rung"] == rung]
        per = {t: [1 if r["completion"] == "True" else 0 for r in rr if r["task_id"] == t]
               for t in tasks}
        p = sum(r["completion"] == "True" for r in rr) / len(rr)
        lo, hi = boot(tasks, per, lambda v: sum(v) / len(v))
        xs.append(i); ys.append(p * 100); los.append(p * 100 - lo * 100); his.append(hi * 100 - p * 100)
    ax.bar(xs, ys, color=GREEN, width=0.55, alpha=0.9)
    ax.errorbar(xs, ys, yerr=[los, his], fmt="none", ecolor=INK, capsize=4, lw=1)
    for x, y in zip(xs, ys):
        ax.text(x, y - 6, f"{y:.0f}%", ha="center", color="white", fontweight="bold")
    ax.set_xticks(xs, [f"{r}\n{sum(1 for r in rs if r['rung']==r_)} runs" for r, r_ in zip(RUNGS, RUNGS)])
    ax.set_ylim(0, 108); ax.set_ylabel("completion (%)")
    headed(ax, "Completion sits at the ceiling on every rung",
           "bars: observed; whiskers: cluster bootstrap over tasks (95%)")
    fig.tight_layout(); fig.savefig(OUT / "fig1-completion.svg", bbox_inches="tight"); plt.close(fig)


def fig_gates(rs):
    fig, ax = plt.subplots(figsize=(7.2, 3.2), dpi=100)
    green, rejected = [], []
    for rung in RUNGS:
        rr = [r for r in rs if r["rung"] == rung]
        g = sum(r["gate_green"] == "True" for r in rr)
        green.append(g); rejected.append(len(rr) - g)
    x = range(len(RUNGS))
    ax.bar(x, green, color=GREEN, width=0.55, label="gate green")
    ax.bar(x, rejected, bottom=green, color=RED, width=0.55, label="rejected")
    for i, (g, r) in enumerate(zip(green, rejected)):
        if r:
            ax.text(i, g + r / 2, str(r), ha="center", va="center", color="white", fontweight="bold")
    ax.set_xticks(list(x), RUNGS)
    ax.set_ylabel("runs")
    headed(ax, "All rejections happen at review, none at CI or static analysis")
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
    fig.tight_layout(); fig.savefig(OUT / "fig2-gate-outcomes.svg", bbox_inches="tight"); plt.close(fig)


def fig_cost_time(rs):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.4, 3.0), dpi=100)
    med = [statistics.median(float(r["seconds"]) for r in rs if r["rung"] == rung) for rung in RUNGS]
    a1.bar(RUNGS, med, color=BLUE, width=0.55)
    a1.set_ylabel("median wall time (s)")
    a1.set_title("Latency", loc="left", fontweight="bold")
    cost = [sum(float(r["cost_usd"] or 0) for r in rs if r["rung"] == rung) for rung in RUNGS]
    a2.bar(RUNGS, cost, color=BLUE, width=0.55)
    a2.text(4, 0.02, "cost not\nreported", ha="center", color=RED, fontsize=8)
    a2.set_ylabel("model spend (USD)")
    a2.set_title("Cost", loc="left", fontweight="bold")
    fig.suptitle("What each rung cost in time and money", x=0.01, y=1.04, ha="left",
                 fontweight="bold")
    fig.tight_layout(); fig.savefig(OUT / "fig3-cost-time.svg", bbox_inches="tight"); plt.close(fig)


def fig_reviewers():
    p1 = {r["run_id"]: r["decision"] for r in csv.DictReader(open(ROOT / "ledger" / "human.csv"))
          if r["kind"] == "review"}
    p2 = {r["run_id"]: r["decision"] for r in csv.DictReader(open(ROOT / "ledger" / "human-pass2.csv"))}
    ids = list(p1)
    fig, ax = plt.subplots(figsize=(7.2, 3.2), dpi=100)
    for i, rid in enumerate(ids):
        for j, (label, d) in enumerate((("R1", p1[rid]), ("R2", p2[rid]))):
            ok = d == "approve"
            ax.scatter(i, j, s=220, color=GREEN if ok else RED, marker="o" if ok else "X", zorder=3)
    ax.set_yticks([0, 1], ["R1", "R2"]); ax.set_ylim(-0.6, 1.6)
    ax.set_xticks(range(len(ids)), [""] * len(ids))
    ax.set_xlabel("the same 8 changes, in review order")
    ax.axhline(0.5, color=MUTED, lw=1)
    headed(ax, "Two independent reviewers, same changes: 4/8 agree (kappa 0.20)",
           "green circle = approve   red X = reject or edit")
    fig.tight_layout(); fig.savefig(OUT / "fig4-reviewers.svg", bbox_inches="tight"); plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rs = rows()
    fig_completion(rs); fig_gates(rs); fig_cost_time(rs); fig_reviewers()
    for p in sorted(OUT.glob("*.svg")):
        print(f"wrote {p.relative_to(ROOT)} ({p.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
