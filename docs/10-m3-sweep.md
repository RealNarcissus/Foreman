# M3 sweep — interim record

Started 2026-11-01. Driver: `tools/sweep.py`, resumable by `(task, rung,
repeat)`, `phase="sweep"` in `ledger/runs.csv`. Worker
`opencode:deepseek-v4.1-flash` (the incumbent, per [02](02-preregistration.md)
§3). Concurrency 4; each job has its own worktree and private `HOME`.

**180 of 180 runs complete.** G4's human half was reviewed in two passes; the
final numbers, including the reliability result, are in
[12-results.md](12-results.md).

## Results

| Rung | Runs | Complete | Gate green | Gate rejected | Escapes | Spend |
| --- | --- | --- | --- | --- | --- | --- |
| G0 | 36 | 36 | 36 | 0 | 0 | $0.630 |
| G1 | 36 | 35 | 36 | 0 | 0 | $0.539 |
| G2 | 36 | 36 | 36 | 0 | 0 | $0.568 |
| G3 | 36 | 36 | 24 | 12 | 0 | $0.524 |

Total **$2.26**. Zero infrastructure failures; every run passed its sandbox
probe. One G1 run is counted as incomplete because it is `valid=False` (see the
containment note below), not because the worker failed.

Four things matter more than the completion column:

1. **G0 saturated at k=3: 36/36.** The pre-check's 12/12 was not an artefact of
   one attempt each.
2. **No gate escapes anywhere.** No run was accepted by a gate and then failed
   its oracle. On this task set the gates bought back no correctness that G0
   lacked — the yield is entirely in rejections.
3. **G3's reviewer rejected 12 of 36 runs whose oracle passed**, and the
   rationales hold up on inspection. Example: `T2-01` r0 fixed the requested
   envvar precedence but also changed the automatic-prefix branch from
   `if rv is not None:` to `if rv:`, silently dropping empty-but-set prefixed
   variables. CI and the oracle both miss that; the reviewer caught it. This is
   the first real gate yield in the sweep, and it points at automated review,
   not at static analysis.
4. **Completion and independent correctness are separate outcomes**, and are
   reported separately from here on. A run can be `completion=True` and
   `gate_green=False` (12 do), and a run can be complete with a broken project
   suite. Pooling them would erase the finding.

## Defect found during the sweep: 36 runs were G1 in disguise

`static_analysis` skipped itself when `FOREMAN_CODEQL_ENABLE` was unset and
returned `ok=True` while doing it. The sweep shell never had the variable, so
the first 36 G2 runs received G1 treatment while being recorded as G2. The
aggregates were plausible — 36/36, zero escapes — and only the per-gate detail
(`skipped (FOREMAN_CODEQL_ENABLE!=1)`) showed it.

Fixed fail-closed: the gate now fails when the variable is unset, and the runner
refuses to start a rung whose static analysis cannot be delivered. The 36
affected rows are marked `void-treatment` and kept. G2 was then re-run with
CodeQL 2.27.3 actually installed and the gate enabled; the numbers above are
the re-run. An earlier version of this document attributed a gate rejection to
G2; that rejection came from the invalidated batch and is a CI rejection, not a
static-analysis one.

CodeQL had been installed under `/tmp`, which is tmpfs here and did not survive.
It now lives outside the tmpfs and the per-run database is deleted after each
gate, because 36 databases would fill the same filesystem the worktrees live on.

## Excluded run (containment, working as designed)

`T2-01_G1_..._r2` passed its oracle but is not counted: the worker log contains a
`curl` to the HuggingFace API searching for `swe-smith` — an attempt to find the
benchmark source from inside the run. `valid=False`, `completion=False`, kept in
the ledger with its reason.

Two facts are being recorded separately here, per the review of this section:

- **Policy:** looking up the benchmark is a violation of the preregistered
  containment rule, so the run does not count.
- **Capability:** the sandbox does not restrict network egress. Detection is
  post-hoc, by matching the worker log.

Egress was left permissive for the sweep because changing it now would make
earlier rungs incomparable with later ones. It should be enforced technically
(namespace without a network, or a proxy allowlist) in any replication, and a
dedicated egress-off run would be a new treatment, not a cleanup.

## Not claimable yet

k=3 per cell, one worker, one repository. Differences below roughly 10 points are
not distinguishable at this size, and the prereg's power analysis is pending.
Repeated runs of one task are not independent observations: the analysis must be
clustered by task, paired across rungs, and must report intervals rather than
means. Runs are paired by `(task, repeat)` across rungs, which the ledger now
supports because `rung` and `repeat` are separate columns.

