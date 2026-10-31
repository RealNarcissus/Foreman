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

30+ tasks in a repository we own. Each task is a seeded mutation (bug injection) or a small feature with a stated spec, and each has a deterministic acceptance test that fails before and passes after the reference solution.

Why own tasks rather than real closed issues:

- **No contamination.** The repository is not in training data.
- **Controlled difficulty.** Three tiers by construction, not by guesswork.
- **Cheap regeneration.** Task supply is not a bottleneck, and a holdout set is possible.
- **Deterministic oracle.** Pass/fail is a test, not a review conversation.

Why own tasks rather than *only* field data: field data cannot answer a causal question. There is no counterfactual for "this repo did not require review."

### 5.2 Field layer (corroboration, external validity)

A slice of the AIDev agent-PR corpus, used to check whether controlled findings resemble what happens where real projects live. Field data never supplies the primary pass/fail signal; it supplies a sanity check and a limitation paragraph that is honest.

### 5.3 Cheapest high-value artifact *(M0)*

For repositories receiving agent PRs, record which guardrails they actually have: rulesets, branch protection, CODEOWNERS, required checks, CodeQL, review bots. If no reusable dataset of guardrail adoption exists, this is a contribution in itself, costs an API script, and gives the field layer real teeth. Verify before assuming.

---

## 6. Metrics

Operational definitions live in the [preregistration](02-preregistration.md). Summary of the intent:

| Metric | Note |
| --- | --- |
| Completion rate | Strict variant requires no human repair, so "human fixed it" is not counted as agent success |
| Escaped defect rate | Post-merge: revert, or a later fix touching the same lines |
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
| Harness: task runner, artifact capture, scorer | Reproducibility; one command to regenerate every table |
| 30+ task suite with generators | Reusable, extensible, contamination-free |
| Results table on Pages | Findings, regenerable from artifacts |
| Experience report with replication package | The writeup, framed as an experience report, not a proof |
| Guardrail-adoption dataset *(if M0 confirms it is missing)* | Cheapest independent contribution |

---

## 8. In and out of v1

| In v1 | Out of v1 |
| --- | --- |
| One subject repository, one language | Multi-repo, multi-language |
| 5 rungs x 30+ tasks, plus a feedback-mode interaction on G1-G3 | Model-vs-model comparison |
| Gate-yield analysis and intervention taxonomy | Submission-based public leaderboard (other agents cannot be run fairly) |
| AIDev field corroboration | Custom-agent arm |
| One tagged release | Release automation as a research question |
| Dependabot and secret scanning present in the pipeline | Dependabot and secret scanning as measured variables |

---

## 9. Milestones and kill criteria

| M | Scope | Effort |
| --- | --- | --- |
| M0 | Literature check, preregistration frozen, AIDev guardrail scrape feasibility | half day |
| M1 | Harness plus one rung end to end, artifacts captured | one weekend |
| M2 | Controlled task suite with difficulty tiers | one weekend |
| M3 | Main sweep | compute-bound |
| M4 | Field corroboration | a few days |
| M5 | Writeup and Pages results | one to two weekends |

### Kill criteria, decided before the work rather than after

| If | Then |
| --- | --- |
| Copilot coding agent cannot be driven at acceptable cost per run after M1 | Drop the vendor arm. Keep CLI agent plus field data. **The guardrail question survives**, which is why this direction is safe to invest in |
| AIDev scrape shows guardrail adoption too sparse to correlate | Field layer becomes descriptive. Controlled layer carries the paper |
| M3 shows no measurable difference across rungs | Publish the null result with the replication package. It still counts |
| Infra failure rate stays above roughly 30% at M3 | The design is not viable as specified; revise before spending further |

---

## 10. Risks

| Risk | Mitigation |
| --- | --- |
| Non-determinism: same task, different outcome | k repetitions per cell; report distributions, never single runs. This is the field's most common error |
| Contamination | Own repository for the controlled layer; date-stamped tasks |
| CI flake polluting first-pass success | Detect flaky tests before the sweep and exclude them explicitly |
| Human gate noise and reviewer drift | Written rubric; second reviewer on a 20% subset; report agreement |
| Vendor drift over the sweep window | Randomised interleaving of condition order per task with a fixed seed, not rung-by-rung batches |
| Self-measured review time bias | Disclosed as a limitation; the field layer compensates on external validity |
| Actions minute quotas and runner variance | Local container is the default backend; Actions is one backend, not the host of the study |
| Credentials and cost | Budget cap preregistered, with a preregistered degradation order when exceeded |

---

## 11. Positioning and the honest limitation

Single-author, one-repository, controlled study means limited external validity. The report will say so in its own words and frame itself as an **experience report with a replication package**, not as proof of a general claim. Pre-empting that objection is worth more than any extra experiment, and it is what separates a credible negative result from an overclaim.

If a capstone rubric must be satisfied, the ladder exercises the GitHub Foundations and Copilot surface (rulesets, environments, CODEOWNERS, Actions, security features, agent mode, custom instructions, prompt files). That coverage needs an explicit objectives-to-artifact table in the README, because a grader will not infer it from architecture. The repository is not the credential; exam study is separate time.

---

## 12. Open decisions

| # | Decision | Needed by |
| --- | --- | --- |
| 1 | Subject repository and language — recommended: `pallets/click` 8.5.0, see [03-subject-repo.md](03-subject-repo.md) | M1 |
| 2 | CLI agent and pinned model version | M1 |
| 3 | Which vendor AI reviewer occupies the G3 gate | M2 |
| 4 | Repo hosting for the controlled layer (public, for reproducibility) | M2 |
| 5 | Whether the vendor arm is valid at G0/G1, where "merge directly" is not a native vendor operation | M1 |

Decision 5 is a known soft spot: the Copilot arm may only be comparable at G1-G4, which would make it a partial replication rather than a full arm. It will be reported as such.
