# Results

All 180 sweep runs collected: 5 rungs x 12 tasks x k=3, `phase=sweep`. This is
the pilot's descriptive record, not a hypothesis test. Intervals are cluster
bootstraps over the 12 tasks; with 12 clusters they are wide by construction.

## Headline

1. **Completion does not discriminate.** 180 runs, one worker, one repository:
   every rung is at or within one case of ceiling. A flat completion curve here
   means *uninformative*, not *gates do nothing*.
2. **Zero gate escapes in 180 runs** (95% upper bound ≈ 1.7%). No change passed a
   gate and then failed its oracle.
3. **All the yield is rejection, and it comes from the reviewer.** 12 rejections
   at G3 and 30 at G4, against 0 at G0–G2. Static analysis contributed none on
   this task set.
4. **The human gate is not stable.** The same reviewer, twice, on the same 8
   changes: 25% then 75% interventions, 50% agreement, kappa 0.20 — with
   carryover between passes, so this bounds single-pass reliability rather than
   estimating it.

## By rung

| Rung | n | Valid | Complete | Gate green | Rejected | Escapes | Median s | Cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G0 | 36 | 36 | 36 | 36 | 0 | 0 | 104 | $0.630 |
| G1 | 36 | 36 | 35 | 36 | 0 | 0 | 86 | $0.539 |
| G2 | 36 | 36 | 36 | 36 | 0 | 0 | 109 | $0.568 |
| G3 | 36 | 36 | 36 | 24 | 12 | 0 | 115 | $0.524 |
| G4 | 36 | 36 | 35 | 6 | 30 | 0 | 140 | n/a |

G4 cost is **missing, not zero**: the provider returned `"cost": 0` with non-zero
token counts on every step. It is not imputed from earlier rungs.

The two non-completions are different: G1's `T2-01` run was excluded by
containment (the worker searched for the benchmark online), and G4's `T2-S2` run
missed its oracle. Neither is a gate outcome, and both are listed in the ledger
with their reasons.

## Completion by task

Failure is not distributed evenly: 10 of 12 tasks are 3/3 at every rung. The two
non-completions are single events (`T2-01` at G1, `T2-S2` at G4), which is why
the per-rung difference is one case and not a trend.

| Task | G0 | G1 | G2 | G3 | G4 |
| --- | --- | --- | --- | --- | --- |
| R3-01..R3-04 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| T1-01..T1-04 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| T2-01 | 3/3 | 2/3 | 3/3 | 3/3 | 3/3 |
| T2-02 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| T2-S1 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| T2-S2 | 3/3 | 3/3 | 3/3 | 3/3 | 2/3 |

## Gate yield

Gate yield is the quantity RQ3 turns on: changes the task oracle scored as
complete that a gate nevertheless rejected. **41 runs**, all at G3 and G4.

| Rung | Rejected | Rejected by |
| --- | --- | --- |
| G0 | 0 | — |
| G1 | 0 | CI accepted every change the oracle accepted |
| G2 | 0 | CodeQL found no new alert on any completed change |
| G3 | 12 | the frozen reviewer |
| G4 | 30 | reviewer 28, human 2 |

Two observations that matter for interpretation:

- **The reviewer is not a stable instrument either.** The same prompt, model and
  threshold rejected 12 of 36 at G3 and 28 of 36 at G4. Different diffs, same
  tasks; a binomial with p≈0.33 would not produce 28 of 36. Either the reviewer's
  behaviour varies substantially between sessions, or something about the re-gate
  (fresh sandbox session) differs. The rejection *rate* is therefore reported as
  a range, not a property of the gate.
- **One G3 rejection was verified by hand** and is real: `T2-01` r0 fixed the
  requested precedence and also changed `if rv is not None:` to `if rv:` on the
  auto-prefix branch, dropping empty-but-set variables. CI and the oracle both
  miss it. Other rationales have not been adjudicated, and the reviewer is known
  to reject for partly wrong reasons even when the verdict is right.

Static analysis contributed **zero** rejections across 72 runs at G2 and above.
That is consistent with the pre-check: the default query suite is configured for
web services, and these tasks do not add sinks it can see.

## Human review (G4)

Of 36 G4 runs, 28 were blocked by machine gates before a person saw them. The
human therefore reviewed **8** changes — a sample conditioned on machine
approval, which is what a real pipeline produces.

| Pass | Interventions | Timed | Adjusted |
| --- | --- | --- | --- |
| 1 | 2/8 (25%) | 19.6 | 19.6 |
| 2 | 6/8 (75%) | 7.7 | **22.7** |

Pass 2's console time is an undercount: the reviewer was recording observations
and finalising later reviews while the script timed individual items, and
reported a further **15 minutes** of concurrent work. That is recorded as a
self-reported adjustment in `ledger/human-adjustments.json`, not smeared into
the per-item timings. With it, pass 2 was stricter *and* longer (22.7 vs 19.6
minutes), which is the intuitive direction and the opposite of what the raw
timer suggested.

Agreement: **4/8 (50%), Cohen's kappa 0.20**. The two passes are not independent:
the reviewer carried observations from the first pass into the second, which is
the learning threat the protocol listed. Kappa 0.20 therefore measures
intra-rater drift with carryover, not test-retest reliability of a naive
reviewer. Consequences:

- The G4 gate result depends on the pass: `gate_green` is 6 under pass 1 and 2
  under pass 2. Pass 1 is the decision of record; pass 2 is reported because the
  human-yield figure is a **range of 25–75%**, not a point.
- At n=8 a single flip moves agreement 12.5 points. This is a consistency check,
  not a reliability estimate, and no claim about human reviewers in general
  follows from it. What it does establish is narrower and still useful: a
  reviewer who sees the same change twice can reach opposite conclusions, so a
  single human verdict is not a gold label.
- Two human rejections in pass 1 were substantive: `R3-04` accepted bare integers
  that the spec says must fail, and one implementation raised `ValueError`
  instead of `BadParameter` past Python's 4300-digit limit. The oracle checked
  neither. That is human yield the machines did not get — visible in the record,
  and swamped in aggregate by the reviewer's 28.

## What these numbers do not support

- No claim that gates are useless: completion is at ceiling, so this task set
  cannot show a gate improving it, and the yield is real but concentrated in one
  noisy gate.
- No claim about models: one worker, chosen as the incumbent, and saturation
  means this suite does not separate models.
- No general claim about reviewers or humans: n=8 human cases, one reviewer, one
  repository.
- No cost comparison at G4: cost is missing there, and cost per run drifted
  downward within rungs as caching took effect, so a mean would mislead.

## Reproduce

```bash
python3 tools/analyze.py     # regenerates every number above from ledger/
```
