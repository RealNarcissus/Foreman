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

---

# Re-run with per-run proofs (the record)

The earlier table in this document predates the sandbox probe and is provisional.
This is the run that counts: 24 runs, every one with `sandbox_probe.ok = true`,
**zero containment failures, zero infrastructure failures**.

| Model | Completion | Valid | Infra | Spend | Mean run |
| --- | --- | --- | --- | --- | --- |
| DeepSeek V4.1 Flash | **8 / 8** | 8/8 | 0 | $0.083 | 249s |
| Claude Haiku 5.5 | **8 / 8** | 8/8 | 0 | $0.018 | 23s |
| MiMo-V2.6 Flash | **8 / 8** | 8/8 | 0 | $0.044 | 219s |

| Model | H1 (mutation) | H2 (feature) |
| --- | --- | --- |
| DeepSeek V4.1 Flash | 4/4 | 4/4 |
| Claude Haiku 5.5 | 4/4 | 4/4 |
| MiMo-V2.6 Flash | 4/4 | 4/4 |

## The finding: a ceiling effect

Every model solves every holdout task, first attempt, with no retries. The
holdout cannot discriminate capability at all. The earlier 6/8 for Haiku was two
`provider.no-route` failures; with a healthy provider it is 8/8.

This is the mirror image of the floor effect the preregistration guarded against,
and nothing in the design anticipated it. It has three consequences:

1. **Worker selection degenerates to cost and speed.** The preregistered
   tie-break (largest allowance) still selects DeepSeek V4.1 Flash, and that is
   what stands — but the rule is now choosing on allowance because capability
   produced no signal. Haiku is 10x faster (23s vs 249s) and 5x cheaper
   ($0.0023 vs $0.0104 per run) while matching completion.
2. **The pilot may saturate too.** If DeepSeek completes all 12 tasks at G0, then
   completion is 100% at every rung, H1 and H2 are untestable, and the ladder can
   only be measured on cost, latency and round trips. That is a real risk to the
   study's primary outcomes and must be checked before 180 runs are spent.
3. **The obvious remedy is more difficult tasks, not a different model.** Adding
   difficulty is a task-authoring change; changing the model would not help,
   since all three saturate.

## Proposed pre-check before M3

Run the 12 pilot tasks once each at **G0** with the selected worker (12 runs,
roughly one hour). If completion is at or near 12/12, the task set is saturated
and must be hardened before the sweep — most cheaply by adding tier-3 tasks whose
oracles check behaviour the existing suite does not constrain. If it is not
saturated, proceed to M3 as planned.

This is a deviation only in the sense that it was not in the original milestone
list; it costs one hour and it protects the primary outcome. It should be recorded
as such.
