# Scope: Foreman

**What guardrails cost, and what they buy, in agentic software delivery.**

Status: design phase, agreed direction. Details marked *(M1)* or *(M2)* are deliberately open and will be fixed when the harness and task suite exist. Nothing here is a result.

---

## 1. The problem

The original framing was two projects: a guardrailed pipeline (issue -> agent PR -> CI/CodeQL/review filters -> release) and a benchmark harness that runs agents against closed issues and scores them. Both are sound ideas. Neither is worth the effort as stated, for concrete reasons.

### 1.1 The pipeline half is configuration, not engineering

As of 2026, Copilot coding agent assigned from an issue, Actions CI, CodeQL, rulesets, CODEOWNERS, protected environments and automated release are documented setup. The work is real but it is onboarding, not contribution. There is a second, structural problem: an agent opening pull requests into a repository whose only consumer is the agent is circular. A reader notices immediately.

### 1.2 The benchmark half is crowded, and you lose on its terms

| Prior work | What it does |
| --- | --- |
| SWE-bench Verified / Pro / Multimodal | The reference task suites and scoring convention |
| SWE-bench-Live, SWE-PolyBench | Continuously refreshed, multi-language task sets with verification |
| HAL (Princeton) | Model-agnostic eval harness plus public leaderboard |
| Red Hat `coding_agent_bench` | Reproducible runs, published cost-per-run leaderboards |
| Long tail of GitHub repos | Live "agents on real issues" leaderboards, updated weekly |

"Turn closed issues into tasks, run agents, publish a leaderboard" is a solved problem with better-resourced incumbents. The first question from any informed reader is "how is this not a worse SWE-bench?" and there is no good answer.

### 1.3 The gap that is actually open

A cluster of 2025-2026 empirical work measures **agent output** in the field:

- Developer interventions in agent-authored PRs, with a 42-action taxonomy — most human effort is guidance-level (58%), not code correction (MSR 2026 mining challenge).
- Rejection of agent fixes: ~46% rejected, 14 reasons in 4 categories (MSR 2026).
- Post-merge outcomes across five vendor agents: revert rates, review latency, security smells (37k provenance-labelled PRs).
- AI reviewers recover only 1.3-3.9% of the concerns humans raise (on agent *instruction files*, not code).

All of it is observational. **None of it ablates the guardrail.** Nobody isolates "what happens to throughput and defect escape when I add a required human review?" and publishes the number. Guardrail policy is being set on vendor assertion, and the cost side — review latency, round trips, false blocks — is invisible.

That gap is small enough for one person to occupy and broad enough to be worth occupying.

---

## 2. The reframe

The pipeline is the instrument. Guardrail strictness is the treatment. The measurement is the product.

> **Foreman: What Guardrails Cost, and What They Buy, in Agentic Software Delivery**

The word doing the work in the original title was "Guardrailed"; "with Measured Evaluation" was a hedge appended at the end. This scope makes the measurement the subject.

### Why this is robust to a boring result

Negative and null results are publishable here because the question is genuinely open. "The first gate captures nearly all of the value and later gates mostly convert agent time into review latency" is as useful as the optimistic outcome. A programme whose worst case is still a result is worth the weekends.

---

## 3. Research questions

| ID | Question | Role |
| --- | --- | --- |
| RQ1 | How does cumulative guardrail strictness affect task completion (acceptance tests pass, no regressions, no human repair)? | Primary |
| RQ2 | How much human effort per merged change, and what *kind* of effort? | Primary |
| RQ3 | Of changes blocked by each gate, what fraction were true positives? (**gate yield**) | Primary |
| RQ4 | How does strictness affect escaped defects after merge? | Secondary |
| RQ5 | What is the fully loaded cost per completed task? | Secondary |
| RQ6 | Does giving the agent sight of, and retries against, gate failures change RQ1-RQ3? | Secondary (interaction) |

RQ3 is the one nobody reports and the one teams actually want before adopting a review bot.

---

## 4. Treatment: the guardrail ladder

Cumulative rungs. Each adds one gate; nothing is removed.

| Rung | Gate added |
| --- | --- |
| G0 | None. Agent commits to the default branch |
| G1 | Required CI: build, lint, existing tests |
| G2 | + required CodeQL / security scan |
| G3 | + required AI reviewer (one vendor, held fixed) |
| G4 | + required human review, CODEOWNERS, protected environment for release |

Cross-cutting factor: **agent feedback access** — blind (one submission, sees nothing) / one retry / three retries. Feedback only exists where a gate produces it, so the interaction is measured at G1-G3 rather than across all rungs.

### Design decisions recorded here

- **Dependabot and secret scanning are in the reference pipeline but are not measured variables.** They are config with no per-task signal.
- **Release automation is demonstrated, not studied.** One tagged release proves the path end to end.
- **The vendor AI reviewer is held fixed for the whole study.** Comparing review bots is a different paper.

---

## 5. Evidence: two layers

### 5.1 Controlled layer (primary, quantitative)

12 tasks against a pinned fork, as a pilot: a repository we do not own, at a fixed tag. Each task is a seeded mutation or a small feature with a stated spec. Each carries a **hidden scoring oracle** that the agent never sees and CI never runs.

Why seeded tasks rather than real closed issues:

- **Contamination is bounded, not eliminated.** The subject repository (`pallets/click`) is in training data. Seeded defects are not, because they are injected at run time. Features are never lifted from upstream history. This is weaker than owning the repository and is disclosed as such.
- **Controlled difficulty.** Three tiers by construction, not by guesswork.
- **Cheap regeneration.** Task supply is not a bottleneck, and a holdout set is possible.
- **Deterministic oracle.** Pass/fail is a test, not a review conversation.
- **Independent oracle.** Success is measured off the gate path, so it cannot be reduced to "made CI green".

Why seeded tasks rather than *only* field data: field data cannot answer a causal question. There is no counterfactual for "this repo did not require review."

### 5.2 Field layer (corroboration, external validity) — **deferred**

A slice of the AIDev agent-PR corpus. Deferred until the controlled layer stands; see prereg §11. Field data would never supply the primary pass/fail signal.

### 5.3 Cheapest high-value artifact *(M0)*

For repositories receiving agent PRs, record which guardrails they actually have: rulesets, branch protection, CODEOWNERS, required checks, CodeQL, review bots. If no reusable dataset of guardrail adoption exists, this is a contribution in itself, costs an API script, and gives the field layer real teeth. Verify before assuming.

---

## 6. Metrics

Operational definitions live in the [preregistration](02-preregistration.md). Summary of the intent:

| Metric | Note |
| --- | --- |
| **Completion, independent** | Hidden oracle passes, no test tampering, no human repair. This is the primary outcome and it is measured off the gate path |
| Completion, gate-green | Visible suite passes. Reported beside the above; the gap between them is a finding in itself |
| **Gate escape** | Gate passed and the hidden oracle failed. Immediate and independent, unlike a post-merge watch |
| Post-merge defect | Secondary: revert, or a later fix touching the same lines |
| Human touch minutes and intervention class | Reuses the MSR 2026 four-category taxonomy rather than inventing one, and reports whether our controlled setting reproduces their field proportions |
| Review round trips | Changes-requested cycles before merge |
| Gate yield | True-positive fraction of blocks, human-adjudicated on a labelled subset |
| Latency, decomposed | Issue -> PR, PR -> first review, review -> merge. The human leg is expected to dominate |
| Cost, decomposed | Agent tokens, CI minutes, human minutes. Reported separately; a composite hides the finding |

**Rejected metric: diff size.** Smaller is not better. Replaced by rework ratio (review lines changed / first-diff lines) and scope adherence (did the diff touch files outside the stated scope). Scope adherence is the better fit anyway: guardrails are about containment.

---

## 7. Deliverables

| Artifact | What it demonstrates |
| --- | --- |
| Reference pipeline (the repo itself, under G4) | The full GitHub path works, on non-trivial code |
| Harness: task runner, artifact capture, **hidden scoring oracle**, gate-yield adjudication | Measurement independence; one command to regenerate every table |
| 12-task pilot suite with generators and hidden oracles | Reusable, extensible, contamination-free |
| Results table on Pages | Findings, regenerable from artifacts |
| Experience report with replication package | The writeup, framed as an experience report, not a proof |
| Guardrail-adoption dataset *(if M0 confirms it is missing)* | Cheapest independent contribution |

---

## 8. In and out of v1

| In v1 (pilot) | Out of v1 |
| --- | --- |
| One subject repository, one language | Multi-repo, multi-language |
| 12 tasks x 5 rungs x k=3 = 180 runs, one agent, one pinned version | Feedback-access interaction, vendor arm, model comparison |
| Hidden scoring oracle separate from the gate suite | Submission-based public leaderboard (other agents cannot be run fairly) |
| Gate-yield analysis and intervention taxonomy | AIDev field corroboration (deferred; see prereg §11) |
| One tagged release | Release automation as a research question |
| Dependabot and secret scanning present in the pipeline | Dependabot and secret scanning as measured variables |

---

## 9. Milestones and kill criteria

| M | Scope | Effort |
| --- | --- | --- |
| M0 | Lit check; **G2 pre-check**; 12 tasks authored within budget; rubric; prereg frozen | 1-2 days |
| M1 | Harness: image, rung configs, hidden-oracle runner, leak check, one rung end to end | one weekend |
| M2 | **Pilot: 180 runs**, artifacts captured | compute-bound, about a day of wall clock |
| M3 | Pilot writeup: descriptive results, task-quality review, power analysis for the main sweep | one weekend |
| M4 | Main sweep, sized by the power analysis | conditional on M3 |
| M5 | Field layer | conditional |

Pilot first, and the pilot is the deliverable until it is done. The 1,068-run design in an earlier version of this plan was not affordable, which made every downstream decision fake.

### Kill criteria, decided before the work rather than after

| If | Then |
| --- | --- |
| Fewer than 2 of 5 planted defects trigger a CodeQL security alert | Drop G2. Ladder becomes four rungs, 144 pilot runs. A rung that cannot fire is not a treatment |
| Infra failure rate stays above 10% in the pilot | Fix the harness before any main sweep. Do not interpret pilot numbers |
| The pilot's effect sizes cannot be powered at an affordable N | Publish the pilot as a feasibility and effect-size study, with the power calculation attached. That is a legitimate result |
| Pilot shows no measurable difference across rungs | Publish the null result with the replication package. It still counts |
| A task's hidden oracle is ambiguous | Repair or drop the task. Never reinterpret the oracle to fit the run |

---

## 10. Risks

| Risk | Mitigation |
| --- | --- |
| **Success and the gate share one oracle** (found in review) | Two oracles: a visible gate suite and a hidden scoring oracle the agent never sees and CI never runs. Leak check per run. This is the difference between measuring capability and measuring gate compliance |
| Non-determinism: same task, different outcome | k=3 in the pilot; distributions, never single runs |
| Contamination | Seeded mutations; no features from upstream history; holdout set |
| CI flake polluting gate results | Detect flaky tests before the pilot and exclude them explicitly |
| Human gate noise and reviewer drift | Written rubric; second reviewer on a 20% subset; report kappa |
| Reviewer is also the author | Disclosed. Blind re-scoring on the subset is the only available mitigation |
| Vendor drift over the sweep window | Randomised interleaving of condition order per task with a fixed seed, not rung-by-rung batches |
| Actions minute quotas and runner variance | Local container is the default backend; Actions is one backend, not the host of the study |
| Budget overrun | Cap recorded before the pilot; the pilot is fixed-size, so the exposure is bounded |

---

## 11. Positioning and the honest limitation

Single-author, one-repository, controlled study means limited external validity. The report will say so in its own words and frame itself as an **experience report with a replication package**, not as proof of a general claim. Pre-empting that objection is worth more than any extra experiment, and it is what separates a credible negative result from an overclaim.

If a capstone rubric must be satisfied, the ladder exercises the GitHub Foundations and Copilot surface (rulesets, environments, CODEOWNERS, Actions, security features, agent mode, custom instructions, prompt files). That coverage needs an explicit objectives-to-artifact table in the README, because a grader will not infer it from architecture. The repository is not the credential; exam study is separate time.

---

## 12. Open decisions

| # | Decision | Needed by |
| --- | --- | --- |
| 1 | Subject repository — recommended `pallets/click` @ `8.5.0` (commit `8b19813`), see [03-subject-repo.md](03-subject-repo.md). Conditional on decision 5 | M0 |
| 2 | Worker: `opencode` headless, DeepSeek V4.1 Flash, `omp` as the alternative client — settled in [05-run-configuration.md](05-run-configuration.md) | M0 |
| 3 | G3 reviewer: Claude Haiku 5.5 with a pinned prompt and severity threshold, per [05-run-configuration.md](05-run-configuration.md) | M0 |
| 4 | Public hosting for the subject fork — CodeQL is free on public repos, not private | M0 |
| 5 | Whether G2 survives its pre-check, or the ladder is four rungs | M0 |

Deferred with the vendor arm: whether the Copilot coding agent is comparable at G0 and G1, where "merge directly" is not a native vendor operation. If that arm returns, it will be reported as a partial replication rather than a full arm.
