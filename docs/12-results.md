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

Of 36 G4 runs, 28 were blocked by machine gates before a person saw them. Two
reviewers therefore saw the same **8** changes — a sample conditioned on machine
approval, which is what a real pipeline produces. The reviews were independent
and concurrent; they were not two passes by one person.

| Reviewer | Conditions | Interventions | Timed | Total |
| --- | --- | --- | --- | --- |
| R1 | console materials only | 2/8 (25%) | 19.6 | 19.6 |
| R2 | console materials + independent verification against the real click repo | 6/8 (75%) | 7.7 | **22.7** |

R2's console time is an undercount: 15 minutes of independent verification
happened while R1 was reviewing, and is recorded as a self-reported adjustment
in `ledger/human-adjustments.json` rather than smeared across per-item timings.
`ledger/human-reviewers.json` records who saw what.

**Inter-rater agreement: 4/8 (50%), Cohen's kappa 0.20.** The four disagreements
are all in one direction — R1 approved four changes that R2 rejected or edited.
Consequences:

- The human yield is a **range of 25–75%** depending on who reviews, not a
  property of the rung. `gate_green` is 6 under R1's verdicts and 2 under R2's.
  R1 is the decision of record; both are reported.
- At n=8 a single flip moves agreement 12.5 points. This is a consistency check
  between two people, not a reliability estimate, and no claim about human
  reviewers in general follows from it. What it does establish is that a single
  human verdict is not a gold label.
- The reviewers were not symmetric: R2 had the task questions on hand and
  verified against the upstream repository, while R1 saw only what the console
  showed. That difference in evidence is a plausible explanation for the gap and
  is not separable from the difference between the people.
- R2's two rejections of `R3-04` were substantive: bare integers accepted where
  the spec says they must fail, and a `ValueError` instead of `BadParameter`
  past Python's 4300-digit limit. The oracle checks neither, so these are real
  human yield that the machines missed — visible in the record, and swamped in
  aggregate by the reviewer's 30.

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
