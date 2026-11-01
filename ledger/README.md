# Ledger

`runs.csv` is the flat per-run record; `record.json` beside each run is the
source of truth. The `phase` column exists so runs with different purposes cannot
be silently pooled.

| phase | meaning |
| --- | --- | --- |
| `validation` | scripted workers (`scripted:null`, `scripted:reference`). Never evidence about a model |
| `diagnostic-revision` | the four `R3-*` runs at G0, 2026-11-01 |
| `pre-m3` | everything recorded before M3, **not yet classified** |
| `sweep` | M3 proper |

## Open item: the `pre-m3` block

The 77 `pre-m3` rows are still mixed together. They contain at least four
distinct things: void smoke attempts, the M2 24-run record, the 12-run saturation
diagnostic, and ad-hoc local runs. They are labelled `pre-m3` rather than sorted
because neither `ledger/saturation.json` nor `docs/07-m2-result.md` records run
ids, and timestamp-only matching would be a guess. Classifying this block against
the M2 and saturation records is a required step before any M3 analysis pools
it. Do not compute a pre-M3 statistic from this file until that is done.

## Repair, 2026-11-01

`runs.csv` contained four lines of unresolved merge-conflict markers
(`<<<<<<< current`, `||||||| base`, `=======`, `>>>>>>> incoming`) that were
committed in an earlier merge. The markers are removed and no data row was lost:
84 rows before, 84 after. Both sides of that conflict are kept (the MiMo holdout
rows and one extra DeepSeek row), since deleting either would destroy evidence
the project may need to explain.
