# Foreman

**What guardrails cost, and what they buy, in agentic software delivery.**

Status: **design phase.** No results yet. The documents in `docs/` are the plan; anything claiming a finding is premature.

## Thesis

Agentic delivery pipelines are being specified far faster than they are being measured. Required human review, blocking security scans, AI review bots, and CODEOWNERS gates are adopted on vendor assertion. Foreman treats the pipeline as an *instrument* and guardrail strictness as the independent variable, so that the question "what does this gate actually buy?" has a number attached to it.

The pipeline is not the deliverable. The measurement is.

## Documents

| Document | Purpose |
| --- | --- |
| [docs/00-scope.md](docs/00-scope.md) | Problem, research question, design, in/out of scope, milestones, kill criteria |
| [docs/adr/0001](docs/adr/0001-guardrail-ablation-not-agent-benchmark.md) | Why this is a guardrail ablation and not another agent leaderboard |
| [docs/01-lit-check.md](docs/01-lit-check.md) | M0 literature check, with novelty go/no-go criteria |
| [docs/02-preregistration.md](docs/02-preregistration.md) | Pre-registered design, hypotheses, metrics, analysis plan (draft, to be frozen before the main sweep) |

## Status of each phase

- [ ] M0 — literature check, preregistration frozen
- [ ] M1 — harness runs one rung end to end
- [ ] M2 — controlled task suite
- [ ] M3 — main sweep
- [ ] M4 — field corroboration
- [ ] M5 — writeup and results table

## Non-goals

Foreman does not rank models, does not host a submission-based leaderboard, and does not claim to prove a general result from a single repository. See the limitations section of the scope document.
