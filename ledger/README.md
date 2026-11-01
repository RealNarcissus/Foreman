# Ledger

`runs.csv` is the flat per-run record; `record.json` beside each run is the
source of truth. The `phase` column exists so runs with different purposes cannot
be silently pooled.

| phase | meaning |
| --- | --- | --- |
| `validation` | scripted workers and auth checks. Never evidence about a model |
| `void` | recorded before M3 and not part of any archived study record |
| `m2` | the 24-run M2 record (`smoke.json`) |
| `diagnostic-saturation` | the 12-run G0 saturation diagnostic (`saturation.json`) |
| `diagnostic-revision` | the four `R3-*` runs at G0 (`revision-saturation.json`) |
| `sweep` | M3 proper |

## Classification rule (applied 2026-11-01)

A pre-M3 run is citable only if it appears in an archived record: `smoke.json`
(M2, 24 runs) or `saturation.json` (12 runs). Runs listed in
`preprobe-runs.csv`, `smoke-void.json` or `smoke-preprobe.json`, and runs that
appear in no archive at all, are `void`. The rule is deliberately mechanical, so
that no row is classified by impression.

Matching was on `(task, seconds)`; the archives carry no run ids. The four
archive key sets are pairwise disjoint (checked: no `(task, seconds)` appears in
more than one archive), so no row was ambiguous. Result: 24 `m2`, 12
`diagnostic-saturation`, 41 `void`, 4 `validation`, 4 `diagnostic-revision` —
85 rows, none unclassified.

The `sweep` phase is written by the M3 driver. Any analysis must filter on it
rather than assuming that a row with a real worker is sweep data.

## Repair, 2026-11-01

`runs.csv` contained four lines of unresolved merge-conflict markers
(`<<<<<<< current`, `||||||| base`, `=======`, `>>>>>>> incoming`) that were
committed in an earlier merge. The markers are removed and no data row was lost:
84 rows before, 84 after, plus one auth-check run. Both sides of that conflict
are kept (the MiMo holdout rows and one extra DeepSeek row), since deleting
either would destroy evidence the project may need to explain.
