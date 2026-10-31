# Subject repository: candidates and recommendation

Fixes open parameter §4.3 of the [preregistration](02-preregistration.md). This is a **recommendation**, not a recorded decision — nothing is frozen yet.

The subject repository is the substrate for the controlled layer. It is the one choice that can invalidate the design after the work is done, because a bad choice produces one of two failures that look like findings but are not:

- **No oracle.** If tests are sparse, a seeded defect passes silently, so "the agent completed the task" means nothing.
- **No material.** If the codebase has no conventions and no security surface, the G3 and G2 rungs have nothing to catch, so gate yield is low *by construction* and H2/H3 are confirmed trivially rather than empirically.

Both are avoidable by choosing deliberately. That is what this document does.

---

## 1. Hard requirements

| # | Requirement | Why it is hard |
| --- | --- | --- |
| R1 | Dense, fast test suite | The suite is the oracle and also the G1 gate. It runs roughly a thousand times. Tests per source LOC predicts how many mutations are detectable |
| R2 | Suite under ~10s | 1,068 planned runs x runtime. At 60s the sweep is 18 hours of pure test time before agent time |
| R3 | Hermetic, no network, no services | Determinism is the whole point; a flaky harness makes flake look like agent failure |
| R4 | 30+ independent mutation sites across 3 difficulty tiers | Below this, N is too small for the six hypotheses |
| R5 | Multi-module call paths | Tier 2 requires tracing, not just localising |
| R6 | Security-relevant surface | G2 (CodeQL) must be able to fire, or H2 is true by construction |
| R7 | Rich conventions | G3 and G4 need material to comment on, or gate yield is zero by construction |
| R8 | Permissive licence | Forking and publishing mutated variants |
| R9 | Cheap container image | One image build, reused for every rung |

---

## 2. Measured candidates

Shallow clone of each default branch, `uv` venv, editable install plus `pytest hypothesis`, wall clock on 12 cores. Numbers are what the harness would actually face.

| Repo | Lang | Src LOC | Test files | Tests | Suite | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `pallets/click` | Python | 12,208 | 62 | 2,262 | **4.7s** | clean on 3.14 |
| `andialbrecht/sqlparse` | Python | 4,976 | 29 | 506 | **2.3s** | clean on 3.14 |
| `python-attrs/attrs` | Python | 7,593 | 39 | 1,402 | 11.1s | 2 failures on 3.14 |
| `pallets/jinja` | Python | 14,240 | 36 | n/a | n/a | needs `trio` |
| `pypa/packaging` | Python | 14,906 | 55 | 9,444 | n/a | needs `pretend`, `tomli_w` |
| `Python-Markdown` | Python | 9,120 | 333 | 1,232 | n/a | needs `yaml` |
| `micromatch/picomatch` | JS | 20,033 | — | 1,998 | 4.2s (+`npm i`) | clean |
| `validatorjs/validator.js` | JS | 24,281 | — | 323 | 13.2s (+`npm i`) | clean |
| `tidwall/gjson` | Go | 6,582 | — | all pkgs | 19.8s incl. compile | clean |

Fairness note: the jinja, packaging and markdown failures are **missing test dependencies in my install command**, not broken projects. They would pass with their own `requirements/tests.txt`. They are ranked on fit below, not on that column.

---

## 3. Scoring

Weights reflect what actually determines whether the study works.

| Criterion | Weight |
| --- | --- |
| R1 oracle density (tests per src LOC) | 25% |
| R2 suite runtime | 20% |
| R4/R5 task diversity and call paths | 20% |
| R6 security surface | 15% |
| R7 convention richness | 10% |
| R3/R9 hermeticity and toolchain | 10% |

| Repo | R1 | R2 | R4/5 | R6 | R7 | R3/9 | Weighted |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `click` | 5 | 5 | 5 | 4 | 5 | 5 | **4.85** |
| `picomatch` | 5 | 4 | 3 | 5 | 4 | 3 | 4.05 |
| `sqlparse` | 4 | 5 | 3 | 4 | 3 | 5 | 3.95 |
| `jinja` | 4 | 4 | 5 | 5 | 4 | 4 | 4.35 |
| `packaging` | 5 | 4 | 4 | 1 | 5 | 5 | 4.05 |
| `validator.js` | 2 | 3 | 4 | 4 | 3 | 3 | 3.05 |
| `markdown` | 3 | 4 | 4 | 4 | 3 | 4 | 3.60 |
| `gjson` | 3 | 2 | 3 | 3 | 4 | 5 | 3.15 |
| `attrs` | 4 | 3 | 3 | 2 | 4 | 4 | 3.35 |

`packaging` scores well until R6: it is pure version-string arithmetic with no security surface at all, so the G2 rung would be decoration. `jinja` is the strongest on paper (autoescape, sandbox, HTML output) and remains the right second choice if the Python arm needs a security-heavy substrate; it lost only on setup friction and on being a weaker fit for 30 diverse single-site mutations.

---

## 4. Recommendation

### Primary: `pallets/click` at tag `8.5.0`

Why it wins, in the order it matters:

1. **2262 tests in 4.7 seconds** against 12.2k source LOC. One test per 5.4 lines. That is the densest oracle in the set at the lowest runtime, which is exactly the R1/R2 tradeoff that decides feasibility.
2. **18 source modules, 62 test files.** Enough independent sites for 30+ non-overlapping tasks without contorting the codebase.
3. **`CliRunner` in `testing.py`** invokes CLIs in-process. Tier-3 acceptance tests need no subprocess, no shell, no port. Determinism for free.
4. **Real security-shaped surface.** `shell_completion.py` builds bash/zsh/fish/powershell scripts by interpolating `complete_var` and completion values, with a `safe_name` sanitiser at line 325. `types.py` and `utils.py` do path handling and lazy file opening. `_compat.py` handles ANSI escapes on untrusted input.
5. **Strict conventions to review against.** Typed, deprecation shims in `_compat.py`, and `filterwarnings = error` in the pytest config, so hygiene violations fail CI the way they do in real projects.
6. Pure Python, one image, installs in seconds.

Operational note: `pyproject.toml` sets `addopts = "-m 'not stress'"`, which deselects ~31,000 stress-marked parameterisations. The harness must never override that, or the suite time explodes.

### Secondary: `andialbrecht/sqlparse`

Smaller oracle (506 tests, 2.3s) but a different failure mode: lexer, keyword tables, formatter. Useful as a robustness check on a second, smaller substrate if budget allows, and cheap because the image is nearly identical.

### If G2 fidelity becomes the blocker: `micromatch/picomatch`

ReDoS is the bug class CodeQL's JS queries are best at, so this is where the security gate would demonstrably fire. The costs are real: `npm i` per fresh container, lockfile drift across a multi-week sweep, and a single-concern codebase that makes 30 diverse tasks harder. Take this only if the Python arm cannot produce a credible G2 true positive.

---

## 5. Contamination, honestly

click is popular, so it is almost certainly in training data. That matters less than it looks, and the distinction needs to be fixed now:

- **Tier 1 and 2 tasks are seeded mutations injected at run time.** The defect is novel even though the surrounding code is memorised. Memorisation may help the agent navigate, which is realistic and is the point of a *repository-level* task.
- **Tier 3 tasks are the risk**, because a feature lifted from the project's own history may be recalled verbatim. Rules: never take a feature from click's git history or changelog; write specs for features that do not exist upstream; prefer features whose acceptance test is hidden, so even a recalled design must satisfy the actual check.
- Add a small **cross-module stratum**: mutations that invert a contract between two modules, which are not recallable because they did not exist.

The holdout set (prereg §4.4) provides the post-hoc check on whether contamination flattered the results.

---

## 6. Task-source map for click

Starting points for the M2 generator. Each cell is meant to widen into several tasks.

| Tier | Modules | Example shapes |
| --- | --- | --- |
| 1 | `_textwrap.py`, `formatting.py`, `parser.py`, `types.py`, `exceptions.py` | Off-by-one in chunk wrapping; usage width miscalculation; `nargs` unpacking edge case; `IntRange` boundary inclusivity; exception attribute ordering |
| 2 | `core.py` + `parser.py`, `decorators.py` + `core.py`, `types.py` + `core.py` | Combined short-flag parsing (`-abc`); option chain default propagation through context; deferred open in `File` type; completion var resolution through environment |
| 3 | `core.py`, `types.py`, `decorators.py` | Separator-tolerant tuple type; case-insensitive choice normalisation; per-command env prefix override; context setting to suppress the help option |
| **Security** | `shell_completion.py`, `_compat.py`, `utils.py`, `types.py` | Weaken or bypass `safe_name` before interpolation into shell source; ANSI escape handling on untrusted input; path joining without a common-prefix check |

The security stratum is a **design requirement, not a bonus**. G2 is meaningful only if the suite contains defects of the class that gate exists to catch. Whether CodeQL actually catches them is itself a result: a false negative on a planted shell-injection-shaped defect is a finding about gate coverage, and it would be reported as such rather than as a flaw in the study.

This needs to go into the preregistration as a pre-freeze revision of §4.1 (a fourth, non-difficulty-stratified axis: `logic` vs `security`). Nothing is frozen, so this is a normal revision, not a deviation.

---

## 7. Risks specific to this choice

| Risk | Handling |
| --- | --- |
| `filterwarnings = error` means warning hygiene failures appear at G1 | Keep it: realistic. Report warning-caused gate failures as a separate count so "correctness" is not conflated with "cleanliness" |
| click is a dependency of many agent-adjacent tools; the agent may have strong priors about its internals | Stated as a limitation; holdout set; cross-module stratum |
| Version drift if upstream moves during the sweep | Pin `subject-v1` = tag `8.5.0` plus a recorded commit hash; the sweep never pulls |
| 12k LOC is small enough that an agent can read most of it | Accept. 30-minute timebox and turn cap bound exploration; this is a repository-level but not large-repository study, and that goes in the limitations paragraph |
| Sole-author repository means conventions are not a community's | Partly mitigated: click's conventions are external and documented, so the reviewer is applying someone else's standard rather than inventing one |

---

## 8. To record at M1

- `subject-v1` tag and commit hash
- Base image digest and install command
- Exact test invocation, including the `not stress` marker
- The four candidate task strata and, after M2, the generator seeds
