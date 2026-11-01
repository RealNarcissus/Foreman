# Revision saturation check

**Written before the runs.** This applies §8.1's rule to the one permitted task-set
revision (`R3-01`..`R3-04`, [02](02-preregistration.md) §8.2). The rule was fixed
before the first pre-check and is not being restated: if this revision also
saturates, saturation is the finding and difficulty is not escalated further.

## What is being measured

Four revised tier-3 tasks, one attempt each, **G0 only**, worker
`opencode:deepseek-v4.1-flash`. Same procedure as [08](08-saturation-check.md):
the 12 pre-check runs are the comparator, not a baseline to beat. Nothing about
model, timebox, rungs or oracle changes here. This is not a new phase of the
pilot and produces no data for the sweep; it decides only whether the revised
tasks are informative at G0.

Why G0 and only G0: the pre-check saturated *at the loosest rung*. If a task
cannot be completed at G0, stricter rungs have something to measure. If it is
completed at G0, the ladder has no headroom on that task regardless of rung.

## What each outcome would change

| Outcome (G0, k=1) | Reading | What changes |
| --- | --- | --- |
| 4/4 complete, oracle passes | Revision also saturates | Saturation becomes the finding. No further escalation, no second revision. M3 proceeds unchanged on gate yield (RQ3) and human cost (RQ2); completion stays descriptive |
| 3/4 | One task carries the headroom | M3 proceeds; report which contract defeated it and treat any rung effect as resting on one task |
| ≤2/4 | The revision found headroom | M3 proceeds; completion is informative again for those tasks and is reported per task, not pooled |
| Any run with `infra_error` set, or a failed sandbox probe | Not evidence about capability | Re-run that task once. A second occurrence is recorded as an infrastructure failure and excluded from the count, as in M2 |

In no case does this diagnostic change the task set a second time, tighten the
timebox, or alter a rung. A flat result is reportable; the pre-check already
demonstrated that saturation is informative rather than null.

## Why these four tasks, in one line each

Each revision task requires coordinated edits at several sites and leaves click's
own suite green, so G1 has no signal and G2 has none by construction (no new
sinks). They test whether *shape* rather than *subject* was the reason the
original tier-3 stratum saturated.

## Result

Run 2026-11-01. Four runs, one attempt each, G0, `opencode:deepseek-v4.1-flash`.
Records: `ledger/revision-saturation.json`; each run also carries
`phase=diagnostic-revision` in `ledger/runs.csv`.

| Task | Contract | Completion | Oracle | Valid | Probe | Seconds | Cost |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R3-01 | aliases across resolution and help | yes | pass | yes | ok | 226.5 | $0.024 |
| R3-02 | Examples section in help | yes | pass | yes | ok | 147.0 | $0.013 |
| R3-03 | `split` for multi-value parameters | yes | pass | yes | ok | 374.2 | $0.043 |
| R3-04 | `Duration` type | yes | pass | yes | ok | 50.7 | $0.004 |

**4/4.** Per the table above, this is the first row: the revision also saturates,
so saturation is the finding and difficulty is not escalated further. No second
revision, no timebox change, no rung change. M3 proceeds on the scope already
applied in [02](02-preregistration.md) §8.1: gate yield (RQ3) and human cost
(RQ2) primary, completion descriptive.

What this does and does not establish:

- It does establish that *shape* was not the reason the tier-3 stratum saturated.
  These four contracts required coordinated edits at several sites, and none of
  them produced a failure in this worker at the loosest rung.
- It does not establish that this worker "can do anything", nor that harder tasks
  do not exist. It is n=1 per task, one model, one attempt. The claim is about
  this task set at this rung, which is exactly the claim the pilot needs; it is
  in the limitations as a task-set result, not a capability result.
- It says nothing about stricter rungs. Completion at G0 bounds headroom from
  below only: the gates still have to be measured for what they catch and what
  they cost in human minutes, which is now the primary outcome.

The original twelve remain the ceiling control. Both saturated sets are kept and
reportable; neither is deleted or re-scored.
