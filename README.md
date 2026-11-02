# Foreman

**What guardrails cost, and what they buy, in agentic software delivery.**

A coding agent solves a fixed task suite under progressively stricter delivery
gates. The harness measures completion, latency, cost, round trips, human
minutes and **gate escapes** — changes a gate accepted that are still wrong.

The pipeline is not the deliverable. The measurement is.

## Status

**The sweep is 144 of 180 runs complete.** G0–G3 are collected at k=3; G4 needs
a human reviewer and has a frozen protocol but no data. Analysis, the power
analysis and the experience report are pending. No result in this repository is
final, and the numbers below are interim.

## Why

Agentic delivery pipelines are specified far faster than they are measured.
Required review, blocking security scans, AI review bots and CODEOWNERS gates
are adopted on vendor assertion. Foreman treats the pipeline as an *instrument*
and guardrail strictness as the independent variable, so that "what does this
gate actually buy?" has a number attached to it.

## Findings so far

Interim, with the sample sizes stated, and reported separately from one another:

1. **GitHub's default CodeQL configuration cannot see a library's inputs.** In
the pre-check, four planted probes produced zero alerts; the three pre-existing
alerts are not what the gate implies they are. The extended suite raises recall
to 2 of 4 without fixing the blind spot. This result is independent of the
sweep.
2. **Completion and correctness are different outcomes.** Twelve G3 runs are
`completion=True, gate_green=False`: the task oracle passed and the review gate
rejected them for behavioural regressions the oracle does not check.
3. **Gate yield came from review, not static analysis.** Across 144 runs there
were zero escapes at every rung; the entire yield is 12 rejections at G3, on
runs whose oracle passed.

Completion saturated at every rung measured (G0 36/36), so a flat completion
curve is uninformative rather than a finding that gates do nothing. The
pre-registration's scope note records that shift before these results existed.

## The ladder

| Rung | Treatment | Runs | Complete | Gate green |
| --- | --- | --- | --- | --- |
| G0 | nothing | 36 | 36 | 36 |
| G1 | project CI | 36 | 35¹ | 36 |
| G2 | CI + CodeQL (frozen config) | 36 | 36 | 36 |
| G3 | G2 + frozen automated review | 36 | 36 | 24 |
| G4 | G3 + human review | — | — | — |

¹ one run excluded by containment: the worker tried to look up the benchmark
online. The run is kept in the ledger with its reason.

## Task suite

Twelve tasks, four per tier, each with a hidden oracle that never enters the
agent's worktree:

- **Tier 1** — single-function mutation; click's own suite fails.
- **Tier 2** — cross-cutting mutation across call paths; includes the security
  tasks, two of which click's own tests cannot see.
- **Tier 3** — the hardening revision: features whose contract spans several
  call sites, checked against an oracle *and* "click's own suite stays green".

`T1-04` is the known-blind control: a library-parameter flow no CodeQL
configuration tested here could see. See [tasks/README.md](tasks/README.md).

## Repository layout

```
configs/rungs/     G0..G4 as data — the treatment is a file, not a branch
tasks/            task suite, seeds, references, hidden oracles
harness/          runner, sandbox, gates, reviewer, oracle, ledger writer
tools/            verification, sweep driver, saturation and reviewer checks
ledger/           run ledger, phase classification, archived diagnostics
docs/             preregistration, pre-checks, progress records, protocol
```

## Reproducing

Requirements: Python 3.11+, `bwrap`, `opencode` with a provider credential, and
optionally CodeQL for G2 and above. The subject is `pallets/click` at commit
`8b19813`, checked out by default at `/tmp/click_tag`.

```bash
python3 -m harness.cli selfcheck                  # 4 containment controls, no model spend
python3 tools/verify_tasks.py                     # every oracle fails on seed, passes on reference
FOREMAN_CODEQL=$HOME/.codeql/codeql/codeql FOREMAN_CODEQL_ENABLE=1 \
  python3 tools/sweep.py --rungs G0,G1,G2,G3 --dry-run
```

Credentials are never stored in the repository: `opencode auth export` writes
outside the tree and the sandbox imports it per run. See
[ledger/README.md](ledger/README.md) for the `phase` column, which separates
sweep data from validation, diagnostics and void runs.

## Documents

| Document | Purpose |
| --- | --- |
| [docs/00-scope.md](docs/00-scope.md) | Problem, research questions, design, milestones, kill criteria |
| [docs/adr/0001](docs/adr/0001-guardrail-ablation-not-agent-benchmark.md) | Why this is a guardrail ablation, not another leaderboard |
| [docs/01-lit-check.md](docs/01-lit-check.md) | Literature check and novelty criteria |
| [docs/02-preregistration.md](docs/02-preregistration.md) | Pre-registered design, hypotheses, analysis plan, scope note |
| [docs/03-subject-repo.md](docs/03-subject-repo.md) | Subject selection |
| [docs/04-g2-precheck.md](docs/04-g2-precheck.md) | G2 pre-check: the CodeQL finding |
| [docs/05-run-configuration.md](docs/05-run-configuration.md) | Worker and reviewer configuration |
| [docs/06-m2-containment.md](docs/06-m2-containment.md) | Containment failure and root cause |
| [docs/07-containment-controls.md](docs/07-containment-controls.md) | Controls added, and how they fail closed |
| [docs/07-m2-result.md](docs/07-m2-result.md) | Worker-selection result |
| [docs/08-saturation-check.md](docs/08-saturation-check.md) | Saturation diagnostic |
| [docs/09-revision-saturation-check.md](docs/09-revision-saturation-check.md) | The hardening revision and its result |
| [docs/10-m3-sweep.md](docs/10-m3-sweep.md) | Sweep results, the G2 defect, containment |
| [docs/11-g4-protocol.md](docs/11-g4-protocol.md) | Human-review protocol for G4 |

Milestone numbering drifted: `docs/00` calls the 180-run pilot M2, while
`docs/10` calls the sweep M3 because worker selection had been using M2. Stage
names are used in prose for that reason.

## Limitations

One repository, one worker, k=3 per cell. Repeated runs of a task are not
independent observations. Nothing here is a claim about models in general or
about reviewers in general, and nothing here shows that guardrails do not work —
it measures what this ladder cost and bought on this task set.

## License

Not yet declared. Until a licence is chosen, the default is all rights reserved,
which is not a suitable state for a public repository.

