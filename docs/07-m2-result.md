# M2: worker selection

24 runs, 3 models x 2 holdout tasks x 4 attempts, all at **G0** so no gate can
help and the hidden oracle alone decides. Every run executed inside bwrap with a
private HOME; containment was asserted per run and **zero runs were contaminated**.

## Result

| Model | Completion | Valid | Spend | Mean run | Provider failures |
| --- | --- | --- | --- | --- | --- |
| **DeepSeek V4.1 Flash** | **8 / 8** | 8/8 | $0.135 | 315s | 0 |
| MiMo-V2.6 Flash | **8 / 8** | 8/8 | $0.039 | 192s | 0 |
| Claude Haiku 5.5 | 6 / 8 | 8/8 | $0.010 | 27s | 2 (`provider.no-route`) |

| Model | H1 (mutation) | H2 (feature) |
| --- | --- | --- |
| DeepSeek V4.1 Flash | 4 / 4 | 4 / 4 |
| MiMo-V2.6 Flash | 4 / 4 | 4 / 4 |
| Claude Haiku 5.5 | 2 / 4 | 4 / 4 |

## Reading it correctly

- **Haiku's two misses are infrastructure, not capability.** Both are
  `provider.no-route — Model unavailable`, zero cost, no tokens. Per
  intent-to-treat they count as non-completion; per protocol Haiku is 6/6 on the
  runs that actually reached the model. The harness now records `infra_error` so
  these are classified rather than silently counted as failures.
- **The tie is real.** DeepSeek and MiMo both completed 8/8, first attempt, no
  retries. Neither is distinguishable on this suite.
- **MiMo is 3.5x cheaper and 40% faster** ($0.039 vs $0.135; 192s vs 315s).

## Selection, per the preregistered rule

The rule was: floor of 2/8, then highest completion, tie broken by larger monthly
allowance. All three clear the floor; DeepSeek and MiMo tie at 8/8; DeepSeek has
the larger allowance ($100 vs $60).

**Selected: DeepSeek V4.1 Flash.**

**Recorded observation, not acted on:** MiMo matched completion at 29% of the
cost and 61% of the wall clock. The tie-break was written before the data existed,
so it stands — but if DeepSeek produces rate limiting or provider failures in M3,
MiMo is the pre-identified fallback and switching would be a logged deviation, not
an improvisation.

## Consequence for M3

- 180 runs at DeepSeek's observed cost is **~$24**, and at MiMo's **~$7** — both
  far inside the $100 allowance. Budget is not the constraint; wall clock is.
- At 315s mean, 180 runs is **~16 hours** serially. The pilot needs 3-4 concurrent
  runs, which the harness supports since each run has its own worktree and HOME.
- H2 (feature) is the expensive task type: 285-1161s against 45-180s for H1. The
  30-minute timebox is not binding, but the tier-3 tasks will dominate wall clock.
