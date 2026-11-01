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

Filled in after the runs; the decision above is copied unchanged into the
conclusion.
