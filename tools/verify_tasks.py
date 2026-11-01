"""Verify every task: oracle fails on the seed, passes on the reference.

Run with `--write` to regenerate `tasks/verification.json`.
"""
import json, sys, pathlib, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "tasks"))

from tasklib import apply, fresh, patch, run_oracle, run_own_suite
from tasks import TASKS
from revision import REVISION


rows = []
for t in TASKS + REVISION:
    root = pathlib.Path(tempfile.mkdtemp()) / t["id"]
    fresh(root)
    notes = []
    ok = True
    record = {
        "id": t["id"], "tier": t["tier"], "cls": t["cls"],
        "source": t["source"], "spec": t["spec"],
        "oracle_fails_on_seed": None, "oracle_passes_on_reference": None,
        "own_suite_green_on_seed": None, "reference_suite_green": None,
        "gate_expectation": t.get("gate_expectation", "n/a"), "verified": False,
    }

    if t["seed"]:
        record["seed_file"] = t["seed"]["file"]
        try:
            patch(root, t["seed"])
        except LookupError as e:
            rows.append(record)
            print(f"{t['id']:6}  PATCH-MISS  {str(e)[:70]}")
            continue
        oracle_fails_on_seed = not run_oracle(root, t["oracle"])
        suite_green_on_seed = run_own_suite(root)
        record["oracle_fails_on_seed"] = oracle_fails_on_seed
        record["own_suite_green_on_seed"] = suite_green_on_seed
        if not oracle_fails_on_seed:
            ok = False; notes.append("oracle did NOT fail on seed")
        if t["cls"] == "logic" and suite_green_on_seed:
            ok = False; notes.append("existing suite stayed green (logic task must be visible)")
        notes.append("suite:" + ("green" if suite_green_on_seed else "red"))
        # pristine: oracle must pass
        p2 = pathlib.Path(tempfile.mkdtemp()) / t["id"]
        fresh(p2)
        if not run_oracle(p2, t["oracle"]):
            ok = False; notes.append("oracle failed on pristine")
    else:
        record["seed_file"] = None
        if run_oracle(root, t["oracle"]):
            ok = False; notes.append("oracle passed without the feature")
        if not t["reference"]:
            ok = False; notes.append("no reference implementation")
        else:
            try:
                apply(root, t["reference"])
            except Exception as e:
                ok = False; notes.append(f"reference failed: {e}")
            oracle_ok = run_oracle(root, t["oracle"])
            record["oracle_passes_on_reference"] = oracle_ok
            if not oracle_ok:
                ok = False; notes.append("oracle failed with reference")
            # A reference that breaks click's own suite is not a valid solution:
            # the worker has to keep the existing behaviour working.
            suite_green = run_own_suite(root)
            record["reference_suite_green"] = suite_green
            notes.append("ref-suite:" + ("green" if suite_green else "red"))
            if not suite_green:
                ok = False; notes.append("reference broke the existing suite")

    record["verified"] = ok
    rows.append(record)
    print(f"{t['id']:6}  {'PASS' if ok else 'FAIL':6}  {'; '.join(notes)}")

print()
print("passed:", sum(1 for r in rows if r["verified"]), "/", len(rows))

if "--write" in sys.argv:
    out = pathlib.Path(__file__).parent.parent / "tasks" / "verification.json"
    out.write_text(json.dumps(rows, indent=2) + "\n")
    print("wrote", out)

