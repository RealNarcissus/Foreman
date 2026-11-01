"""Plumbing validation for the G3 reviewer.

This is NOT an effectiveness evaluation. Three hand-picked diffs prove the
wiring can distinguish an obviously bad change from an obviously clean one, and
that a broken call fails closed. They are the reviewer's smoke test.

    python3 tools/validate_reviewer.py
"""
import json, pathlib, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tasks"))

from harness import gates, runner, sandbox, rungs
from harness.patching import apply
from tasks import TASKS
from revision import REVISION

OUT = ROOT / "ledger" / "reviewer-validation.json"
cfg = rungs.load("G3")["reviewer"]
by_id = {t["id"]: t for t in TASKS + REVISION}


def diff_for(task_id: str, kind: str) -> str:
    task = by_id[task_id]
    wt = pathlib.Path(tempfile.mkdtemp(prefix="review-case-")) / "worktree"
    runner.prepare(wt, None)
    apply(wt, task["reference"] if kind == "reference" else task["seed"])
    return runner.diff_of(wt)


observed = sorted(pathlib.Path("/tmp/foreman-runs").glob(
    "T2-S1_G2_*_r0_*/diff.patch"))
observed_diff = observed[0].read_text() if observed else ""

cases = [
    ("known_good_R3-04", "approve", cfg, "R3-04",
     diff_for("R3-04", "reference"), "clean new feature"),
    ("known_bad_T2-S1_seed", "reject", cfg, "T2-S1",
     diff_for("T2-S1", "seed"), "shell injection introduced"),
    ("known_bad_observed_regression", "reject", cfg, "T2-S1",
     observed_diff, "real run: oracle-complete, 14 suite tests broken"),
    ("failure_semantics_bad_model", "error", {**cfg, "model": "opencode-go/does-not-exist"}, "R3-04",
     diff_for("R3-04", "reference"), "bogus model must never approve"),
]

results = []
for name, expect, c, spec_id, diff, why in cases:
    home = sandbox.home_for(f"review-{name}")
    wt = pathlib.Path(tempfile.mkdtemp(prefix="review-wt-"))
    gate = gates.ai_review(wt, c, diff=diff, spec=by_id[spec_id]["spec"], home=home)
    decision = gate.get("decision")
    ok = (decision == expect) if expect != "error" else (decision == "error" and not gate["ok"])
    results.append({"case": name, "expected": expect, "why": why, "spec": spec_id,
                    "decision": decision, "gate_ok": gate["ok"],
                    "detail": gate.get("detail"),
                    "prompt_hash": c["prompt_hash"],
                    "review": gate.get("review"), "pass": ok})
    print(f"{name:34} expected={expect:8} got={decision!s:8} gate_ok={gate['ok']} "
          f"{'PASS' if ok else 'FAIL'}")

# No model call: the freeze itself must refuse to run.
unpinned = gates.ai_review(pathlib.Path(tempfile.mkdtemp()), {**cfg, "prompt_hash": "UNPINNED"},
                           diff="x", spec="x", home=pathlib.Path("/nonexistent"))
mismatch = gates.ai_review(pathlib.Path(tempfile.mkdtemp()),
                           {**cfg, "prompt_hash": "0" * 64}, diff="x", spec="x",
                           home=pathlib.Path("/nonexistent"))
for label, gate in (("unpinned", unpinned), ("hash_mismatch", mismatch)):
    ok = gate["decision"] == label and not gate["ok"]
    results.append({"case": f"freeze_{label}", "expected": label, "decision": gate["decision"],
                    "gate_ok": gate["ok"], "detail": gate.get("detail"), "pass": ok})
    print(f"freeze_{label:27} expected={label:8} got={gate['decision']:8} gate_ok={gate['ok']} "
          f"{'PASS' if ok else 'FAIL'}")

OUT.write_text(json.dumps({"prompt_hash": cfg["prompt_hash"], "cases": results}, indent=2) + "\n")
print("\nwrote", OUT)
print("passed", sum(r["pass"] for r in results), "/", len(results))
