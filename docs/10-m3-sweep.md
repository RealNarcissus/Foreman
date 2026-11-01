# M3 sweep — interim record

Started 2026-11-01. Driver: `tools/sweep.py`, resumable by `(task, rung,
repeat)`, `phase="sweep"` in `ledger/runs.csv`. Worker
`opencode:deepseek-v4.1-flash` (the incumbent, per [02](02-preregistration.md)
§3). Concurrency 4; each job has its own worktree and private `HOME`.

**108 of 180 runs complete: G0, G1, G2.** G3 and G4 are not run — see the
blocker below.

## Interim results

| Rung | Runs | Counted complete | Gate rejected | Gate escapes | Mean wall |
| --- | --- | --- | --- | --- | --- |
| G0 | 36 | 36 | 0 | 0 | 165s |
| G1 | 36 | 35 | 0 | 0 | 204s |
| G2 | 36 | 36 | 1 | 0 | 184s |

Total spend **$1.731**. Zero infrastructure failures; every run passed its
sandbox probe.

Three things in this table matter more than the completion column:

1. **G0 saturated again at k=3: 36/36.** The pre-check's 12/12 was not a
   small-sample artefact of one attempt each. Completion has no headroom at the
   loosest rung, which is what §8.1 already recorded.
2. **No gate escapes anywhere.** No run was accepted by a gate and then failed
   its oracle. A flat escape count is itself a measurement: on this task set the
   gates did not buy back any correctness that G0 lacked.
3. **One gate rejection is the first evidence about gate yield.** `T2-S1` at G2
   (run `T2-S1_G2_deepseek_v4_1_flash_r0_...`) fixed the behaviour the oracle
   checks and broke 14 cases of `tests/test_termui.py::test_editor_path_normalization`.
   The oracle called it complete; CI rejected it. That divergence — a task
   oracle that scores completion while the project's own suite regresses — is
   the mechanism RQ3 is meant to expose, and it is now observed once.

## Excluded run (containment, working as designed)

`T2-01_G1_..._r2` passed its oracle but is not counted: the worker log contains a
`curl` to the HuggingFace API searching for `swe-smith` — an attempt to find the
benchmark source from inside the run. The containment marker matched `oracle` in
that line. The run is `valid=False`, `completion=False`, and it stays in the
ledger with its reason rather than being deleted.

This is the first observed attempt to look up the task source online. It is
recorded as evidence about contamination pressure, not as a harness fault. The
sandbox had no network policy beyond the host's; a future revision should decide
whether egress is part of the treatment.

## Blocker: G3 and G4 are stubs

`harness/gates.py`:

```python
def ai_review(worktree, reviewer):
    """Stub until the reviewer prompt is committed and hashed."""
    return {"gate": "ai_review", "ok": True,
            "detail": "stub: reviewer prompt not yet pinned", "comments": []}
```

`configs/rungs/G3.json` carries `"prompt_hash": "UNPINNED"`, and the prereg
requires prompt, model and threshold to be committed before the sweep because
they *are* the treatment. Running G3 now would produce 36 runs labelled
"automated review" in which no reviewer ran — data that would later read as
"automated review catches nothing" when in fact nothing was tested. `G4`
returns `needs_human` with no session and no timer, so its 36 runs are
deterministic by construction.

That is why the sweep stopped at 108. The two options are:

- **Pin the reviewer** (write the prompt, hash it, wire `ai_review`, validate
  that it fires on a known-bad diff and passes a known-good one), then run the
  remaining 72.
- **Ship 108 runs over three rungs** and state plainly that the review and human
  rungs are out of scope for this report.

Neither is chosen here; the decision is the developer's, because the first
changes what the treatment is.

## Not claimable yet

k=3 per cell, one worker, one repository. Completion differences below ~10
points are not distinguishable at this size, and the prereg's power analysis is
still pending. Nothing here is a final result; it is the interim state of the
sweep.
