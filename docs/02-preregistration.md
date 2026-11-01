# Preregistration

**Version 0.2 — DRAFT. Not yet frozen. No data collected.**

Freeze protocol: when the open parameters are fixed, tag the commit `prereg-v1` and record the hash below. After the tag this document is immutable; every departure goes in `deviations.md` with date, reason, and whether data had been collected at the time.

| Field | Value |
| --- | --- |
| Frozen commit | *(not yet frozen)* |
| Frozen at | *(not yet)* |
| Deviation log | `deviations.md` |

Rationale: [scope](00-scope.md), [ADR](adr/0001-guardrail-ablation-not-agent-benchmark.md), [subject repository](03-subject-repo.md).

**Version 0.2 changes** (from 0.1, after review): a held-out scoring oracle for *all* tiers replacing the shared gate oracle (§4.2); a pilot-first design replacing the 1,068-run sweep (§3); gate-escape as the primary escaped-defect metric (§6); G2 conditional on an empirical pre-check (§3.6); feedback and vendor arms deferred out of v1.

---

## 1. Research questions

- **RQ1 (primary)** How does cumulative guardrail strictness affect task completion, measured independently of the gate?
- **RQ2 (primary)** How many human minutes, and of what kind, does each rung require per merged change?
- **RQ3 (primary)** Of changes blocked by each gate, what fraction were true positives?
- **RQ4 (secondary)** How does strictness affect gate escapes and post-merge defects?
- **RQ5 (secondary)** What is the fully loaded cost, including gate latency, per completed task?

RQ6 from v0.1 (feedback access as a crossed factor) is **deferred**; see §11.

---

## 2. Hypotheses

Tested in Phase M only (§3). Each has a falsifier.

| ID | Hypothesis | Falsified if |
| --- | --- | --- |
| H1 | Completion is non-increasing in strictness across the rungs | Any rung completes significantly more than its predecessor |
| H2 | The largest completion drop is G0 -> G1; the security rung adds little, and only on security-class tasks | The security rung's drop exceeds G1's |
| H3 | The AI-review rung raises round trips and latency without a material reduction in gate escapes; its yield is low (<30%) | Its yield exceeds 50%, or escapes fall materially versus the previous rung |
| H4 | At the human-review rung, human minutes are dominated by guidance-class interventions, reproducing the MSR 2026 field proportions (~58% guidance) | Direct code edits dominate |
| H5 | Gate escape is better explained by task tier than by rung, because tier determines whether the gate has relevant coverage | Rung explains more variance than tier |
| H6 | The security rung is the only rung whose yield differs between security-class and logic-class tasks | Yield is uniform across classes |

H3 and H5 are the hypotheses whose confirmation would make this project matter.

---

## 3. Design

### 3.1 Two phases

| Phase | Purpose | Tasks | Runs | Analysis |
| --- | --- | --- | --- | --- |
| **P — pilot** | Validate the harness; measure variance; find broken tasks; estimate effect sizes | 12 | **180** (12 x 5 rungs x k=3) | **Descriptive only. No hypothesis tests** |
| **M — main** | Test the hypotheses | N from power analysis | to be fixed after P | Inferential, per §8 |

The pilot is deliberately not a test of the hypotheses. Its job is to make the main sweep affordable and correctly sized. Reporting a p-value from 12 tasks x 3 repetitions would be the error this document exists to prevent.

**Budget envelope:** the Go plan ($10/month), with DeepSeek V4.1 Flash as the primary worker and Claude Haiku 5.5 as the G3 reviewer. At off-peak prices the pilot's estimated spend is a few dollars against a $100 model allowance, so budget is not the binding constraint; capability and calendar time are. Details, prerequisites and the worker selection rule are in [05-run-configuration.md](05-run-configuration.md).

### 3.2 The rung ladder

Cumulative. G0 none; G1 required CI; G2 required static analysis (CodeQL); G3 required AI review; G4 required human review, CODEOWNERS, protected environment.

**G2 is conditional** (§3.6). If it fails its pre-check, the ladder is four rungs (G0, G1, G3, G4), N=144 runs in the pilot, and every downstream reference to "the security rung" is removed rather than reinterpreted.

### 3.3 Pilot composition

12 tasks, balanced 4/4/4 across tiers, of which **3 are security-class**: two in tier 2 (environment-sourced, `EDITOR` and `PAGER`) and one in tier 1 (a library-parameter flow, kept as a **known-blind control**). Tier is balanced; the logic/security label is not crossed, because 12 tasks cannot support a balanced 2x2 and pretending otherwise would produce uninterpretable cells.

All 12 are authored and verified in `tasks/` — each oracle fails on the seeded state and passes on the pristine or reference state (`tasks/verification.json`). Three tasks leave click's own suite green and are therefore invisible to G1: `T1-04` (by design), `T2-S2` (a genuine gap in click's tests), and the four tier-3 features (no coverage exists).

### 3.4 Authoring budget

Each task may cost at most **45 minutes** of authoring, including its hidden oracle and 60-word spec. Tasks that exceed it are dropped, not simplified. Twelve well-made tasks beat sixty mediocre ones, and the pilot's purpose is task quality feedback before the expensive phase.

### 3.5 Task suite

| Tier | Construction | Gate visibility |
| --- | --- | --- |
| 1 | Single-file, single-function mutation; an existing test fails | Gate can detect |
| 2 | Multi-file mutation requiring a call path; an existing test fails | Gate can detect |
| 3 | Small feature against a written spec; no visible test exists | **Gate is blind** |

Tier 3 is not a harder version of tier 1. It is the cell where the gate has no relevant coverage at all, which is why tier predicts gate escape (H5). This is by design, not an oversight: it keeps the visible/hidden oracle distinction inside the existing factor instead of adding a fourth one.

Acceptance criteria per task: a hidden oracle that fails on the seeded state and passes on the reference solution; a spec of at most 60 words with no implementation hints, paths or test names; no shared root cause with another task; reproducible from a generator plus a recorded seed.

### 3.6 G2 pre-check

Run the procedure in [04-g2-precheck.md](04-g2-precheck.md) §4: GitHub default code scanning on a public fork of `8.5.0`, then five planted defects.

**Precondition:** a positive control must fire. If a canonical `os.system("echo " + sys.argv[1])` sample produces no alert, the configuration is unvalidated and nothing downstream counts. A local CLI run already failed this test; see [04](04-g2-precheck.md) §3.

**Then:** the five defects run under the announced configurations, and the rung follows from the result. The rung is a triple, not a name:

> **G2 = (threat model, query suite, severity policy)**

**Resolved and frozen on 31 Oct 2026: G2 = C2** (threat model *Remote and local sources*, query suite *Default*, five rungs, 180 pilot runs). Evidence is in [04-g2-precheck.md](04-g2-precheck.md).

The reason the rung needed a triple: GitHub's shipped default is `threat_model: remote`, and `commandargs`, `environment`, `stdin` and `file` are all classified as **local** sources. Under the default, a library reading local input has no coverage at all. Measured on four planted defect classes:

| Configuration | Controls fired | Planted recall | Actionable findings | Precision over alerts |
| --- | --- | --- | --- | --- |
| C1 remote, default suite | 0 of 2 | 0 of 4 | 0 | 0 of 1 |
| C2 local + remote, default suite | 2 of 2 | **2 of 4** | **2** | 2 of 5 |

Two constraints follow, and both are binding on task authoring:

1. **Security-class defects must be environment-sourced** (`EDITOR`, `PAGER`, or a config/XDG variable). Library-parameter defects are invisible at C2: the library-input shell query is absent from the default suite, and `py/path-injection` does not model library parameters here. Verified by three planted attempts that produced no alert.
2. **Gate yield is computed on actionable findings, not alerts.** Five alerts deduplicated to four findings and two actionable defects; one expression produced two alerts and all three pre-existing alerts were false positives.

One library-parameter security task is retained as a *known-blind control*, expected to score as a gate escape, so the paper reports coverage as well as yield.

---

## 4. Measurement independence

This section is the correction that matters most.

### 4.1 The circularity

If the scoring oracle is the same suite the gate runs and the agent can read and iterate on, then "success" means "the agent made CI green", and there is nothing left to detect what the gate missed. Every result would be a restatement of gate behaviour.

### 4.2 Two oracles

| | Gate suite | Scoring oracle |
| --- | --- | --- |
| Lives in | The subject repository | The harness (`oracle/<task-id>/`) |
| Visible to agent | Yes | **Never** |
| Run by | CI at G1 and above | Harness, after the gate decision |
| Determines | The rung's behaviour | Task success, gate escape |

**Oracle requirements.** Hidden for every tier, not just tier 3. Contains at least one assertion the gate suite does not make. Asserts only public behaviour, so the agent is not failed for legitimate internal design choices.

**Authoring self-test, per task:** oracle fails on the seeded state; oracle passes on the reference solution; oracle passes on unmodified upstream code where the task is a mutation.

**Leak check, per run:** assert the oracle path is absent from the agent's worktree and from the submitted diff. A run failing this check is void and reported as a harness defect.

**Application:** the gate decision is recorded first, then the submitted state is copied into a clean `subject-v1` checkout, the oracle is injected there, and the suite is run in the same pinned image. The oracle never exists in the repository the agent worked in.

---

## 5. Run procedure

1. Reset the subject repository to `subject-v1` (tag `8.5.0`, commit `8b19813`).
2. Apply the task seed deterministically; assert the gate suite fails where the task says it should.
3. Apply rung configuration from `configs/rung-*/` by script, never by hand.
4. Dispatch the agent with the spec only. Timebox 30 minutes wall clock and a fixed turn cap.
5. Capture trajectory, token counts, wall clock, first diff, tool calls.
6. Where the rung has a gate, record the gate decision and its raw reason strings.
7. Record whether the agent had sight of gate output (v0.2: always yes, one retry, matching a normal production setup).
8. At the human rung, review per §7 with a timer running.
9. Run the hidden oracle out of band (§4.2). Record the result before any other analysis.
10. Archive under `runs/<run-id>/`; tear down.

**Order handling.** Run order is randomised per task by a seed derived from the task ID, interleaving rungs rather than batching by rung, so that vendor drift does not align with the treatment.

---

## 6. Metrics

| Metric | Definition |
| --- | --- |
| **Completion, independent (primary)** | Hidden oracle passes AND no test tampering AND merged without human code edit |
| Completion, gate-green | Visible gate suite passes. Reported alongside, never instead |
| **Gate escape (primary, RQ4)** | Gate passed AND hidden oracle failed. Immediate, independent, no waiting |
| Post-merge defect (secondary, RQ4) | Within 14 days or 50 commits: revert of the merge, or a later commit modifying a line the merge introduced. Reported separately from gate escape |
| Wall clock | Dispatch -> PR opened; plus gate latency measured separately |
| **Gate latency** | Time from PR open to gate verdict, including checkout, install and queue. This is where CI cost actually lives |
| Round trips | Review submissions in changes-requested state before merge |
| Human minutes (RQ2) | Timed review sessions: reading, commenting, editing |
| Intervention class | One label per intervention: `guidance`, `decision`, `direct_code`, `operational`, following the MSR 2026 taxonomy, plus free text |
| Gate yield (RQ3) | Blocked changes adjudicated true/false positive. True positive = genuinely invalid, insecure or non-compliant. False positive = an acceptable change a reasonable reviewer would accept. All builds blocked at the AI and human rungs adjudicated; 20% tier-stratified sample at the CI and static-analysis rungs |
| Rework ratio | Lines changed during review / lines in the first submitted diff |
| Scope adherence | Fraction of changed files outside paths implied by the spec |
| Cost (RQ5) | Three separate numbers: agent tokens at a recorded price table, CI minutes, human minutes. No composite in primary reporting |
| Test tampering | Weakening or skipping existing assertions, or editing CI config to pass a gate. Counted as non-completion in the independent metric and reported separately |

### Intent-to-treat

Primary analysis counts infrastructure failures as non-completion. Per-protocol is reported alongside with the excluded run inventory. Fixed now so hard runs cannot be excluded later.

---

## 7. Human review protocol

- Written rubric covering correctness, scope adherence and convention compliance, with examples, committed before the pilot.
- The reviewer is the author. Disclosed as a limitation; this is a weakness of the study, not of the repository.
- A second reviewer scores a 20% random subset blind to rung. Cohen's kappa per intervention class reported. If kappa < 0.6, report it and collapse classes to `guidance` vs `code_change`, saying so.
- Sessions are timed in one sitting where possible; interruptions recorded.

---

## 8. Analysis plan

### Phase P (pilot) — descriptive only

Point estimates with confidence intervals. Variance and transition-rate estimates for the power analysis. A task-quality review: any task where the oracle or the reference solution is ambiguous is repaired or dropped. **No hypothesis tests. No p-values reported as findings.**

### Power analysis at the end of P

From the pilot's paired transition rates, compute the number of tasks needed to detect the pilot's observed effect at 80% power for the primary comparison. That N, not the 1,068 from v0.1, sets Phase M. If the required N exceeds the budget, the honest outcome is a larger effect threshold, stated openly, not a smaller study described as conclusive.

### Phase M — inferential

- Primary model: mixed-effects logistic regression, `success ~ rung + tier + (1 | task)`.
- Paired comparisons: McNemar for completion, Wilcoxon signed-rank for continuous outcomes, Holm correction across H1-H6.
- Effect sizes: percentage-point differences primarily, odds ratios and Cliff's delta secondary, CIs on every estimate.
- Gate yield: proportions with Wilson intervals, stratified by logic/security class.
- All rungs and all tiers reported. No subgroup dropped for being uninteresting.
- Pilot runs are **not pooled** into Phase M, because the harness will have changed.

### Preregistered figures

1. Completion (independent) by rung, with CIs, faceted by tier
2. Gate-green completion versus independent completion, by rung — the gap is the finding
3. Gate escape by rung and tier
4. Gate yield by rung, split by logic/security
5. Human minutes by rung, stacked by intervention class
6. Gate latency decomposition by rung
7. Cost per completed task by rung

---

### 8.1 Scope note after the saturation diagnostic

The 12 pilot tasks completed 12/12 at G0 on one attempt each (see
[08-saturation-check.md](08-saturation-check.md)), which was the pre-registered
trigger for this note.

**Primary outcome shifts to gate yield (RQ3) and human cost (RQ2)**, with
completion reported as a bounded quantity: with no observed headroom at G0, a flat
completion curve across rungs is uninformative rather than a finding that the
gates do nothing. RQ1 and RQ4 remain reported but are downgraded to descriptive.

One task-set revision is permitted (harder tier-3 tasks constraining behaviour
click's suite does not pin). The twelve saturating tasks are retained as the
ceiling control. If the revision also saturates, saturation is reported as the
finding and difficulty is not escalated further. The timebox is not an independent
variable and will not be tightened.

## 9. Threats to validity

| Threat | Handling |
| --- | --- |
| Shared gate and scoring oracle | Two oracles, §4.2; leak check per run |
| Non-determinism | k=3 in the pilot; distributions, never single runs |
| Contamination | Seeded mutations; no features from upstream history; holdout set |
| CI flake | Suite 5x per task before the pilot; exclude tests failing more than once; publish the exclusion list |
| Human gate noise and drift | Rubric; blind second reviewer on 20%; kappa reported |
| Author-reviewer bias | Disclosed; blind re-scoring on the subset is the only available mitigation |
| Self-timed review minutes | Disclosed; minutes reported alone so readers can reprice |
| Vendor drift | Randomised interleaving; pinned versions per run |
| Test gaming | §6 test tampering metric |
| Single repository, 12.7k LOC | Framed as an experience report; "repository-level, not large-repository" goes in the limitations |
| G2 cannot fire | §3.6 pre-check with a preregistered drop rule |
| Publication bias | Preregistration and released artifacts make a null result as reportable as a positive one |

---

## 10. Released artifacts

Preregistration tag, deviation log, harness, task generators and manifests, hidden oracles (released after the sweep), run artifacts, gate reason strings, adjudication labels, analysis scripts, and one command that regenerates every figure from the artifacts. Oracles are held back until the sweep closes, then released for replication.

---

## 11. Deferred, and why

| Item | Deferred to | Reason |
| --- | --- | --- |
| Feedback-access interaction (v0.1 RQ6) | after the main sweep | 432 runs for a secondary question. Calendar time and harness complexity, not cost: the allowance would cover it |
| Vendor arm (Copilot coding agent) | after the main sweep | Needs n=96 runs, a separate driver, and may be invalid at the two lowest rungs; also unverified cost |
| Field layer (AIDev) | after the main sweep | Corroboration only; the controlled layer must stand first |
| Second subject repository | after the main sweep | Robustness check, not needed for the pilot |

---

## 12. Open items before freeze

- [ ] G2 pre-check run in GitHub's default configuration, with a positive control that fires; rung count decided (5 or 4)
- [ ] Worker model chosen by the smoke test on holdout tasks, under the §3 selection rule ([05](05-run-configuration.md) §3)
- [ ] `Global` region enabled for DeepSeek in workspace privacy settings; `opencode` version pinned
- [ ] Reviewer prompt, model and blocking threshold committed and hashed ([05](05-run-configuration.md) §1)
- [ ] 12 tasks authored, each within the 45-minute budget, each passing the oracle self-test
- [ ] §7 rubric committed
- [ ] Pilot spend metered from `opencode.allowance` and recorded per run
- [ ] Lit-check outcome incorporated (§2 may need revision)
- [ ] Venue and deadline identified, or explicitly deferred
