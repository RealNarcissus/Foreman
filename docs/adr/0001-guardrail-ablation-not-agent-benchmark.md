# 0001. Measure guardrails, not agents

- **Status:** Accepted
- **Date:** design phase
- **Supersedes:** the original framing of "guardrailed agentic SDLC on GitHub" plus "agent evaluation harness on GitHub" as two co-equal deliverables

## Context

The project was proposed as two halves. (A) A guardrailed delivery pipeline on GitHub: issue -> agent PR -> CI, CodeQL, AI review, human approval via rulesets and CODEOWNERS, protected release. (B) An evaluation harness that turns a repository's closed issues into tasks, runs agents against them in Actions, scores pass rate, diff size and review rounds, and publishes a leaderboard on Pages.

Both halves are sound in isolation. Neither survives comparison with what already exists.

For (A): every element is documented product setup. The assembly is a weekend of onboarding, and an agent PRing into a repository with no other consumer is circular. The artifact would demonstrate that the author can follow documentation.

For (B): the task-suite-and-leaderboard pattern is occupied by SWE-bench Verified/Pro/Multimodal, SWE-bench-Live, SWE-PolyBench, HAL, Red Hat's `coding_agent_bench`, and a long tail of auto-updating repos doing exactly this pitch. Competing on that axis means being asked "how is this not a worse SWE-bench?" with no retort. It also invites model comparison, which the project cannot win and which is a different paper.

Meanwhile, 2025-2026 empirical work measures agent output in the field but consistently stops short of the causal question: interventions in agent PRs, reasons for rejection, post-merge outcomes, and AI review recall on instruction files, all observational. Guardrail policy is being set across the industry on vendor assertion with the cost side — review latency, round trips, false blocks — largely invisible.

## Decision

Treat **guardrail strictness as the independent variable** and the pipeline as the instrument that produces the treatment. Five cumulative rungs (none, CI, CI+security, +AI review, +required human review) applied to a fixed task suite and a fixed agent, measuring completion, human effort, gate yield, escaped defects, latency and cost.

The pipeline is demoted from deliverable to apparatus. The measurement is the product.

Evidence comes in two layers: a controlled layer of seeded tasks in a repository we own (causal, contamination-free, deterministic oracle), and a field layer over the AIDev agent-PR corpus (external validity only, never the primary pass/fail signal).

## Alternatives considered

| Alternative | Why rejected |
| --- | --- |
| Build the pipeline as the deliverable | Documentation-following. Circular demo. Nothing to review |
| Build the benchmark harness as the deliverable | Occupied by better-resourced incumbents; forces an unwinnable model comparison; no novel claim |
| Closed issues of a popular OSS repo as the task corpus | Contamination, ambiguous specs, ground truth is a review conversation rather than a test, high cost per task |
| Purely observational study over AIDev | Cheap and high-n, but cannot answer a causal question: there is no counterfactual for a repository that did not require review |
| Survey or interview study of practitioners | Complementary and worth citing, but produces self-report rather than measured behaviour, and depends on a participant pool |

## Consequences

**Good.**

- The project has a claim rather than a demo, which is the difference between reviewable and un-reviewable work.
- Null and negative results remain publishable, so the investment is protected against an unexciting sweep.
- Every artifact is reusable: harness, task generators, adoption dataset, results table, writeup.
- The research question survives a change of agent or vendor, which is what makes the kill criteria safe.

**Bad.**

- One repository and one author means limited external validity. The report must frame itself as an experience report, not a proof.
- The design demands k repetitions per cell and randomised interleaving, which multiplies compute cost and calendar time relative to a demo.
- The human-review rung is the noisiest instrument in the study and is being operated by the author, so it needs a rubric, a second reviewer on a subset, and disclosure.
- Preregistration before the sweep adds a half day and constrains later freedom. That constraint is the point.

## Follow-ups

1. Literature check with an explicit novelty go/no-go ([docs/01-lit-check.md](../01-lit-check.md)).
2. Freeze the preregistration as a tagged commit before the main sweep; log all deviations afterwards.
3. Establish whether a reusable guardrail-adoption dataset already exists before building the scrape.
