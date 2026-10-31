# Preregistration

**Version 0.1 — DRAFT. Not yet frozen. No data collected.**

Freeze protocol: when the open parameters (§3.4, §4.3) are fixed, tag the commit `prereg-v1` and record the commit hash below. After the tag, this document is immutable; every departure goes in `deviations.md` with date, reason, and whether data had been collected at the time.

| Field | Value |
| --- | --- |
| Frozen commit | *(not yet frozen)* |
| Frozen at | *(not yet)* |
| Deviation log | `deviations.md` |

Design rationale is in [the scope](00-scope.md) and [the ADR](adr/0001-guardrail-ablation-not-agent-benchmark.md). This document is the operational contract.

---

## 1. Research questions

- **RQ1 (primary)** How does cumulative guardrail strictness affect task completion?
- **RQ2 (primary)** How many human minutes, and of what kind, does each rung require per merged change?
- **RQ3 (primary)** Of changes blocked by each gate, what fraction were true positives?
- **RQ4 (secondary)** How does strictness affect escaped defects after merge?
- **RQ5 (secondary)** What is the fully loaded cost per completed task?
- **RQ6 (secondary)** Does agent visibility of, and retries against, gate failures change RQ1-RQ3?

---

## 2. Hypotheses

Each has a falsifier. Reporting is against these six only; anything else is labelled exploratory.

| ID | Hypothesis | Falsified if |
| --- | --- | --- |
| H1 | Completion is non-increasing in strictness across G0-G4 | Any rung completes significantly more than its predecessor |
| H2 | The largest completion drop is G0 -> G1; G1 -> G2 is small (<5pp), because security scans rarely fire on non-security tasks | Drop at G2 exceeds the drop at G1 |
| H3 | **G3 (AI review) raises round trips and latency without a material reduction in escaped defects; its gate yield is low (<30%)** | G3 yield > 50%, or escaped defects at G3 fall materially versus G2 |
| H4 | At G3/G4, human minutes are dominated by guidance-class interventions, reproducing the MSR 2026 field proportions (~58% guidance) | Direct code edits dominate human minutes |
| H5 | Escaped defect rate is better explained by task difficulty tier than by rung | Rung explains more variance than tier |
| H6 | Feedback plus retries recovers most of the completion loss at G1, but not at G3, because AI review comments are frequently non-actionable | Retries recover G3 as well as G1 |

H3 and H6 are the hypotheses whose confirmation would make this project matter. H1 is expected to hold and is included for completeness and to anchor the comparison.

---

## 3. Design

### 3.1 Factors

**Factor A — guardrail rung (5 levels, cumulative).** G0 none; G1 required CI; G2 + required CodeQL; G3 + required AI reviewer; G4 + required human review with CODEOWNERS and protected environment.

**Factor B — agent feedback access (3 levels).** `blind` (single submission, no gate output), `retry1`, `retry3`. Default for the main sweep is `retry1`, chosen because it is the common production configuration. Factor B is crossed with rungs G1-G3 only, since G0 has no gate and G4's feedback is human.

### 3.2 Conditions

| Sweep | Cells | Purpose |
| --- | --- | --- |
| Main | 5 rungs x N tasks x k=3 at `retry1` | RQ1-RQ5 |
| Feedback interaction | 3 rungs (G1-G3) x 2 modes (`blind`, `retry3`) x N x k=2 | RQ6 |
| Vendor arm | 4 rungs (G1-G4) x 12 tasks x k=2 | External validity of the primary agent |

### 3.3 Sample size

N is the number of controlled tasks. Target **N = 36**, minimum **N = 30**, tier-balanced (12/12/12 target, 10/10/10 minimum). Planned run counts at N=36: main 540, interaction 432, vendor 96; approximately 1,068 agent runs.

### 3.4 Budget cap and degradation order

A hard budget cap covering inference, CI minutes and Actions quota is set at M1 and recorded here **before the first sweep run**. When the cap is reached, degrade in this order and no other:

1. Reduce k from 3 to 2 in the main sweep.
2. Drop the `blind` mode from the interaction sweep.
3. Reduce the vendor arm from 12 to 8 tasks.
4. Drop tier-3 tasks from the interaction sweep.

Never go below N=20 or k=2. Any degradation is recorded in `deviations.md` with the run counts achieved. The order is fixed now so the cap cannot be used to drop inconvenient cells after seeing results.

---

## 4. Task suite

### 4.1 Tiers

| Tier | Construction | Rationale |
| --- | --- | --- |
| 1 | Single-file, single-function mutation; one existing test fails | Localisation is the only work |
| 2 | Multi-file mutation; requires tracing a call path; one existing test fails | Adds navigation and coupling |
| 3 | Small feature: implement to a written spec (~60 words) plus a hidden acceptance test | Adds specification interpretation |

### 4.1a Orthogonal stratum: logic vs security

Tier measures difficulty. A second, independent label records the defect class: `logic` or `security`. Security-class tasks plant defects of the kind a gate is supposed to catch (injection-shaped interpolation, unvalidated paths, unsafe deserialisation), so that G2 has something to detect.

Without this stratum the G2 result is true by construction: a suite of pure logic bugs cannot be caught by a security scanner, and H2 would hold for trivial reasons. The ratio is targeted at roughly 20-25% security-class, distributed across tiers 1 and 2. Whether CodeQL actually detects them is an outcome, not an assumption; a false negative is reported as a finding about gate coverage.

### 4.2 Acceptance criteria for every task

1. A deterministic acceptance test that fails on the seeded state and passes on the reference solution.
2. A spec of at most 60 words, containing no implementation hints, no file paths, and no test names.
3. No two tasks share a root cause.
4. Reproducible from a generator script plus a seed recorded in the task manifest.

### 4.3 Open parameters (to fix at M2)

- Subject repository and language. **Proposed: `pallets/click` at tag `8.5.0`**, with measurements and rejected alternatives in [03-subject-repo.md](03-subject-repo.md). Awaiting sign-off.
- The mutation operator list, which must be recorded in the manifest so the suite can be extended by others.
- CLIs and pinned versions for the primary agent and the G3 reviewer.

### 4.4 Holdout

25% of generated tasks are held out and are not used in any sweep. After the main sweep they are run once at G0 and G4 only, as a confirmatory check. The holdout result is reported whether it confirms or contradicts.

### 4.5 Test-integrity rule

The agent never receives the acceptance test, hidden tests, or the reference patch. Shortcuts are checked for:

- Deleting or weakening existing test assertions or skipping tests -> **test tampering**, counted as non-completion in the strict variant and reported separately.
- Modifying CI configuration to pass a gate -> same treatment.
- Adding new tests is permitted and ignored by scoring.

---

## 5. Run procedure

1. Reset the subject repository to tag `subject-v1`.
2. Apply the task's seed deterministically; assert the acceptance test fails.
3. Apply rung configuration from `configs/rung-*/` by script, never by hand.
4. Dispatch the agent with the spec only. Timebox: 30 minutes wall clock and a fixed turn cap.
5. Capture: full trajectory, token counts, wall clock, first diff, tool calls.
6. Where the feedback mode permits, expose gate output and allow the configured number of retries.
7. Record each gate decision with its raw reason strings.
8. Merge automatically when rung < G4 and gates pass; record blocked state otherwise.
9. At G4, review per §7 with a timer running; record intervention class per intervention.
10. Post-merge: watch window for escaped defect signals (§6).
11. Archive everything under `runs/<run-id>/` and tear down.

**Order handling.** Run order is randomised per task by a seed derived from the task ID, interleaving rungs rather than batching by rung. Vendor and model behaviour drifts across a multi-week sweep; batching by rung would confound drift with the treatment.

---

## 6. Metrics

| Metric | Operational definition |
| --- | --- |
| Completion, strict (primary) | Acceptance test passes AND existing suite passes AND merged without any human code edit |
| Completion, lenient | Merged at all, by any means |
| Wall clock | Dispatch -> PR opened |
| Round trips | Review submissions in changes-requested state before merge |
| Human minutes (RQ2) | Timed review sessions: reading, commenting, editing. Timer started and stopped by the reviewer |
| Intervention class | One label per intervention: `guidance`, `decision`, `direct_code`, `operational`, following the MSR 2026 taxonomy, plus free text |
| Gate yield (RQ3) | Blocked changes adjudicated true/false positive. True positive = the change was genuinely invalid, insecure or non-compliant. False positive = an acceptable change a reasonable reviewer would have accepted. Adjudicate 100% of G3/G4 blocks and a 20% tier-stratified sample of G1/G2 blocks |
| Escaped defect (RQ4) | Within a window of 14 days or 50 commits, whichever first: (a) revert of the merge, or (b) a later commit modifying at least one line the merge introduced, or (c) a test added later that fails on the merged state. Report (a) and (b) separately; do not collapse them |
| Rework ratio | Lines changed during review / lines in the first submitted diff |
| Scope adherence | Fraction of changed files outside the paths implied by the spec |
| Cost (RQ5) | Reported as three separate numbers: agent tokens at a recorded price table, CI minutes, human minutes. No composite in the primary reporting |
| Latency decomposition | Issue -> PR, PR -> first review, review -> merge; reported separately |

### Intent-to-treat

Primary analysis is intent-to-treat: infrastructure failures count as non-completion. A per-protocol analysis excluding them is reported alongside, with the excluded run inventory. This choice is fixed now so that hard runs cannot be excluded after the fact.

---

## 7. Human review protocol

- A written rubric scores correctness, scope adherence and convention compliance, with examples, committed before the sweep.
- The reviewer is the author. This is disclosed as a limitation, not hidden.
- A second reviewer scores a 20% random subset blind to rung. Agreement is reported as Cohen's kappa per intervention class. If kappa < 0.6, report it and collapse intervention categories to two (`guidance` vs `code_change`) in the analysis, saying so.
- Review sessions are timed in one sitting where possible; interruptions are recorded.

---

## 8. Analysis plan

**Primary model.** Mixed-effects logistic regression: `success ~ rung + tier + feedback_mode + (1 | task)`. Rung treated as categorical for marginal means. Report marginal means with 95% confidence intervals.

**Paired comparisons.** Each task appears under every rung, so comparisons are paired: McNemar for completion, Wilcoxon signed-rank for continuous outcomes, Holm correction across the six hypotheses.

**Effect sizes.** Report absolute percentage-point differences primarily (that is what practitioners use), with odds ratios and Cliff's delta as secondary. Confidence intervals on every estimate; no bare point estimates.

**Gate yield.** Proportions with Wilson intervals, per rung.

**Reporting rule.** All five rungs and all three tiers are reported, always. No subgroup is dropped for being uninteresting. Exploratory analyses appear in a separate, clearly labelled section.

**Preregistered figures.**

1. Completion by rung, with CIs, faceted by tier
2. Gate yield by rung
3. Human minutes by rung, stacked by intervention class
4. Latency decomposition by rung
5. Cost per completed task by rung

**No optional stopping.** N and k are fixed before the sweep. If a run crashes, retry once; a second failure is recorded as an infrastructure failure and included per intent-to-treat.

---

## 9. Threats to validity

| Threat | Handling |
| --- | --- |
| Non-determinism | k repetitions; distributions, never single runs |
| Contamination | Own repository; date-stamped tasks; holdout set |
| CI flake | Run the suite 5x per task before the sweep; exclude tests failing more than once; record the exclusion list |
| Human gate noise and drift | Rubric, blind second reviewer on 20%, kappa reported |
| Reviewer knows the hypothesis | He is the author; disclosed. Blind re-scoring on the subset is the only available mitigation |
| Self-timed review minutes | Disclosed. Human minutes are reported as measured by a single reviewer, and readers can reprice |
| Vendor and model drift | Randomised interleaving; pinned versions recorded per run |
| Test gaming | §4.5 integrity checks, reported as a separate count |
| Single repository, single author | Framed as an experience report, not a general result. The field layer addresses external validity only |
| Publication bias | The preregistration and the released artifacts make the null result as publishable as the positive one |

---

## 10. Released artifacts

Preregistration tag, deviation log, harness, task generators and manifests, run artifacts (trajectories, gate reasons, diffs), adjudication labels, analysis scripts, and the command that regenerates every figure and table from the artifacts.

---

## 11. Open items before freeze

- [ ] §3.4 budget cap set
- [ ] §4.3 subject repository, language, mutation operators, pinned agent and reviewer versions
- [ ] §7 rubric committed
- [ ] Lit-check outcome incorporated (§2 may need revision)
- [ ] Venue and deadline identified
