"""Verify every task: oracle fails on the seed, passes on the reference."""
import sys, pathlib, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "tasks"))

from tasklib import fresh, patch, run_oracle, run_own_suite
from tasks import TASKS

rows = []
for t in TASKS:
    root = pathlib.Path(tempfile.mkdtemp()) / t["id"]
    fresh(root)
    notes = []
    ok = True

    if t["seed"]:
        try:
            patch(root, t["seed"])
        except LookupError as e:
            rows.append((t["id"], "PATCH-MISS", str(e)[:70])); continue
        oracle_fails_on_seed = not run_oracle(root, t["oracle"])
        suite_green_on_seed = run_own_suite(root)
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
        if run_oracle(root, t["oracle"]):
            ok = False; notes.append("oracle passed without the feature")
        if not t["reference"]:
            ok = False; notes.append("no reference implementation")
        else:
            try:
                patch(root, {"file": t["reference"]["file"], "fn": None, "old": None, "new": None}) if False else None
                p = root / t["reference"]["file"]
                p.write_text(p.read_text() + t["reference"]["append"])
            except Exception as e:
                ok = False; notes.append(f"reference failed: {e}")
            if not run_oracle(root, t["oracle"]):
                ok = False; notes.append("oracle failed with reference")

    rows.append((t["id"], "PASS" if ok else "FAIL", "; ".join(notes)))

w = max(len(r[0]) for r in rows)
print(f"{'task'.ljust(w)}  result  notes")
for r in rows:
    print(f"{r[0].ljust(w)}  {r[1]:6}  {r[2]}")
print()
print("passed:", sum(1 for r in rows if r[1] == "PASS"), "/", len(rows))
