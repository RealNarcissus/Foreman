# G4 human-review protocol (proposed, not yet collected)

G4 is the only rung that cannot be produced by the harness alone: it needs a
person. This document is the protocol that must be frozen **before** the 36 runs
are collected, in the same way the reviewer prompt was frozen before G3. Nothing
here has been run yet.

## What the reviewer sees

For each run, one screen containing:

1. the task specification the agent was given;
2. the full unified diff;
3. the CI result (pass/fail plus the failing test names);
4. the static-analysis result (new alerts, if any);
5. the automated reviewer's verdict and its findings, attributed as a machine
   opinion.

The hidden oracle, the task's `seed`, the reference implementation and every
other run's records are **not** shown. The reviewer judges the change, not the
answer key.

## Allowed actions

| Action | Meaning | Effect on the run |
| --- | --- | --- |
| `approve` | merge as-is | `gate_green=True`, counted as accepted |
| `reject` | block the change | `gate_green=False`, reason recorded |
| `reject_and_edit` | block, then the human edits the code themselves | recorded separately as human-authored; **not** a gate outcome |
| `timeout` | no decision within the limit | treated as reject, flagged |

There is no "approve with comments": a decision that changes the code is a
different treatment (human as author), and mixing it with gate review would make
"human minutes" meaningless.

## Time limit

The timer starts when the materials are displayed and stops when the decision is
submitted. Limit **10 minutes per run**, matching the pilot's review budget.
The timer is visible to the reviewer, and the elapsed minutes are recorded to
0.1. A timeout is a decision, not missing data: it fails closed and is reported
as `timeout`.

## What counts as an intervention

Any action other than `approve`. Interventions are the primary human-cost
quantity (RQ2): count, minutes, and the reason class (defect, uncertainty,
missing context, process). Reading time with an `approve` is also recorded, so
that "minutes" means review effort, not only rejection effort.

## Order and blindness

Runs are presented in a fixed order derived from the sweep ids, not sorted by
outcome, so the reviewer cannot infer expected results from the sequence. The
reviewer does not see the rung label. G4 is therefore blind in the same sense as
the automated gates, though it is not blind to the task set.

## Calibration (plumbing only)

Before the 36, two known cases are run through the console:

- a clean reference change, which should be approvable in under two minutes;
- a change with a seeded regression, which should be rejected.

These check that the console renders, the timer works and decisions persist.
They are **not** evidence that human review is effective, exactly as the
reviewer's three plumbing diffs are not evidence about the reviewer.

## What is recorded per run

`runs/<id>/human.json`: decision, elapsed seconds, reason class, free-text
rationale, whether the reviewer opened the diff or the CI output, and the two
calibration results. The ledger keeps `human_minutes` and `intervention` as
columns so they can be joined to the same run ids as the machine rungs.

## Known threats

| Threat | Handling |
| --- | --- |
| One reviewer, not a sample of reviewers | Reported as a case study; no claim about reviewers in general |
| The reviewer is the developer who wrote the tasks | Disclosed; blindness to rung and oracle limits but does not remove it |
| Time pressure from the visible timer | Minutes reported alongside decisions so readers can reprice |
| Learning across 36 runs | Fixed order; the task set is small, so learning cannot be eliminated, only disclosed |
| Fatigue | Runs are chunked with breaks; chunk boundaries recorded |

## Why this is not being simulated

A scripted "human" that approves or rejects by rule would be a fifth automated
gate wearing a human label — the same error as a stub reviewer reporting
`ok=True`. The 36 G4 runs therefore require an actual person. Either the
developer runs the console, or a designated reviewer does, and the deviation is
logged. Until then G4 stays uncollected, and the sweep reports 144 of 180.
