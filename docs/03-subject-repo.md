# Subject repository: candidates and recommendation

Fixes open parameter §4.3 of the [preregistration](02-preregistration.md). Status: **recommendation, conditional on the pre-check in §6.** Nothing is frozen.

The subject repository is the substrate for the controlled layer. Two failures look like findings but are not:

- **No oracle.** Sparse tests mean seeded defects pass silently, so "task complete" is unmeasured.
- **No material.** No sink-shaped code and no conventions mean the G2 and G3 rungs cannot fire, so gate yield is low *by construction*.

Selection is therefore driven by measured oracle density and by whether a gate can physically detect a planted defect. It is not driven by a weighted score: those weights would be my judgment wearing a number, and an earlier version of this document did exactly that.

---

## 1. Hard requirements

| # | Requirement | Why it is hard |
| --- | --- | --- |
| R1 | Dense test suite | Predicts how many mutations are detectable at all |
| R2 | Suite fast enough that gate latency is dominated by infrastructure, not tests | Threshold, not a ranking criterion; see §4 |
| R3 | Hermetic, no network, no services | Flake would look like agent failure |
| R4 | 30+ independent mutation sites | Below this, the pilot has nothing to draw from |
| R5 | Multi-module call paths | Tier 2 must require tracing, not just localising |
| R6 | Sink-shaped code, so a static-analysis gate could physically fire | Without it G2 is decoration; see §6 |
| R7 | Rich conventions | G3/G4 need material, or gate yield is zero *by construction* |
| R8 | Permissive licence | Forking and publishing mutated variants |
| R9 | **Public repository** | CodeQL is free for public repos and not for private ones |

---

## 2. Measured candidates

Shallow clone, `uv` venv, editable install plus `pytest hypothesis`, single wall-clock measurement each on a 12-core machine. **One measurement, not a benchmark.** Runtimes move between runs; treat these as order-of-magnitude, and re-measure before quoting.

| Repo | Lang | Src LOC | Tests | Suite (pytest) | Status |
| --- | --- | --- | --- | --- | --- |
| **`pallets/click` @ `8.5.0`** | Python | 12,674 | 1,991 | 6.95s (8.7s wall) | clean on 3.14 |
| `pallets/click` @ HEAD (8.6.0.dev) | Python | 12,208 | 2,262 | 4.68s | clean on 3.14 |
| `andialbrecht/sqlparse` | Python | 4,976 | 506 | 2.25s | clean on 3.14 |
| `python-attrs/attrs` | Python | 7,593 | 1,402 | 11.09s | 2 failures on 3.14 |
| `micromatch/picomatch` | JS | 20,033 | 1,998 | 4.2s + `npm i` | clean |
| `validatorjs/validator.js` | JS | 24,281 | 323 | 13.2s + `npm i` | clean |
| `tidwall/gjson` | Go | 6,582 | not counted | 19.8s incl. compile | clean |
| `pallets/jinja` | Python | 14,240 | unmeasured | unmeasured | needs `trio` |
| `pypa/packaging` | Python | 14,906 | 9,444 collected | unmeasured | needs `pretend`, `tomli_w` |
| `Python-Markdown` | Python | 9,120 | 1,232 | unmeasured | needs `yaml` |

Correction from the first version of this document: I quoted HEAD numbers while recommending a tag. At the tag the suite is **271 tests smaller and ~50% slower**. Both rows are shown so the difference is not hidden.

Fairness note: the unmeasured rows failed because my install command omitted their test dependency files, not because the projects are broken.

---

## 3. The only two measurements that discriminate

**Oracle density** (tests per 1k source LOC):

| Repo | Density |
| --- | --- |
| `packaging` | ~634 |
| `attrs` | ~185 |
| **`click` @ 8.5.0** | **157** |
| `markdown` | ~135 |
| `sqlparse` | ~102 |
| `picomatch` | ~100 |
| `validator.js` | **~13** |

Density disqualifies `validator.js` outright: 323 tests against 24k LOC means most seeded defects would pass silently, and "completion" would be unmeasured.

**Gate viability** (§6) disqualifies `packaging` despite the best density in the set: it is version-string arithmetic with no sink-shaped code, so a static-analysis gate over it can never fire and the G2 rung would be decoration.

Everything else — convention richness, module layout, how pleasant the code is to review — is my judgment and is recorded as judgment, not scored.

---

## 4. Correcting the runtime weighting

An earlier version weighted suite runtime at 20%. That was wrong for two reasons.

A local `pytest` run is not a CI run. In Actions the check is dominated by checkout, toolchain setup, install and queueing, which for click is roughly 20-40s against a 7s suite. And a 12-core machine only helps if the suite runs in parallel, which stock `pytest` does not; click's config deselects ~31,000 stress-marked parameterisations rather than distributing them.

Runtime is therefore a **threshold**: fast enough that gate latency is dominated by infrastructure. Everything in the set except `gjson` (compile) and the `npm i` arms clears it. Gate latency itself becomes a *measured outcome* in RQ5's latency decomposition, which is where the interesting number lives.

---

## 5. Recommendation

### Primary: `pallets/click` at tag `8.5.0`

Verified: the tag exists, annotated tag object `9e17c52`, commit **`8b19813f2bfca99f1018a587a8cf54fc959f2e5d`**, `pyproject.toml` reads `version = "8.5.0"`, 17 source files, 12,674 source LOC, 1991 passed / 24 skipped / 1 xfailed in 6.95s.

Reasons, in the order they matter:

1. **Oracle density of 157 tests per 1k LOC** at a runtime that clears any reasonable threshold.
2. **17 source modules and 62 test files** — enough independent sites for a 12-task pilot with room to grow.
3. **`CliRunner` in `testing.py`** invokes CLIs in-process, so acceptance tests need no subprocess and no port. Determinism for free.
4. **Genuine sink-shaped code**, which §6 covers in detail — this is the criterion that separates click from `packaging`, and it turned out better than I first represented.
5. **Strict, external conventions**: typed, deprecation shims in `_compat.py`, `filterwarnings = error`, maintained by an organisation rather than a sole author. The reviewer applies someone else's standard instead of inventing one.
6. Pure Python, one image, installs in seconds.

Operational note: `pyproject.toml` sets `addopts = "-m 'not stress'"`. The harness must never override it, or the suite time explodes.

### Secondary: `andialbrecht/sqlparse`

Smaller oracle, different failure modes (lexer, keyword tables, formatter), near-identical image. Useful as a second substrate if the main sweep is extended; not needed for the pilot.

### If the §6 pre-check fails: `micromatch/picomatch`

ReDoS is the class CodeQL's JS queries detect best, and picomatch builds regexes from input. Costs: `npm i` per fresh container, lockfile drift, and a single-concern codebase that limits task diversity.

---

## 6. G2 viability: what a static-analysis gate could actually catch

This is the weakest part of the design and it needs an empirical answer, not an argument.

**What I can verify statically.** `shell_completion.py` generates bash/zsh/fish/powershell source by interpolating names into templates. Those are strings written to a file, not commands executed, so there is no CodeQL sink: a planted defect there will almost certainly produce no alert. My first version of this document leaned on that surface, and that lean was wrong.

**Where the real sinks are.** `_termui_impl.py` has actual command execution: pager resolution by `shutil.which` followed by `subprocess.Popen([path, *params])`, editor invocation, and `open_url` with `subprocess.Popen`/`subprocess.call`. The pager code even carries a security-motivated comment about resolving unqualified names through `shutil.which`. A planted regression that replaces the argv list with an interpolated string and `shell=True` is the textbook shape of an environment-driven command injection, which is what `py/shell-command-injection-from-environment` exists to find.

That is a reasoned expectation, not a measurement. CodeQL CLI is **not installed here**, so I could not test it, and the claim must not be treated as verified.

### Pre-check protocol (1-2 hours, before freezing)

1. Install the CLI: `gh extension install github/gh-codeql`, then `codeql pack download codeql/python-queries`.
2. Baseline on unmodified code:
   `codeql database create /tmp/db --language=python` in the `8.5.0` checkout, then
   `codeql database analyze /tmp/db codeql/python-queries --format=sarif-latest --output=/tmp/click.sarif`
3. Count alerts by rule id. Record the baseline; the baseline is the noise floor for every later comparison.
4. On a branch, plant five candidate defects from the security stratum, one at a time, and re-run.
5. Record which rule fired for each, if any.

**Decision rule.** If at least two of five planted defects produce a *security* rule alert, G2 is a real rung. If not:

- G2 is dropped and the ladder becomes **four rungs** (G0, G1, G3, G4). The study does not depend on it.
- The pre-check result is reported as a finding about gate coverage, with the planted-defect table attached.
- Do **not** keep a rung that cannot fire and call its yield a measurement.

`packaging` would have failed this pre-check at step 2 with zero security alerts. That is why R6 is a hard requirement and why the pre-check must run before anything freezes.

---

## 7. Contamination

click is popular, so the code is almost certainly in training data. The distinction that matters:

- **Tier 1 and 2 defects are seeded at run time.** The defect is novel even though the surrounding code is memorised. Navigation help from memorisation is realistic and is part of what a repository-level task tests.
- **Tier 3 is the risk**, because a feature recalled from the project's history would be reproduced from memory. Rules: never take a feature from click's history or changelog; write specs for features that do not exist upstream; keep the acceptance oracle hidden, so a recalled design still has to satisfy the actual check.
- Add a small **cross-module stratum**: mutations that invert a contract between two modules, which are not recallable because they never existed.

The holdout set (prereg §4.4) checks whether contamination flattered the result.

---

## 8. Task-source map for click

| Tier | Modules | Example shapes |
| --- | --- | --- |
| 1 | `_textwrap.py`, `formatting.py`, `parser.py`, `types.py`, `exceptions.py` | Chunk-wrapping boundary; usage width; `nargs` unpacking; `IntRange` inclusivity; exception attribute order |
| 2 | `core.py` + `parser.py`, `decorators.py` + `core.py`, `types.py` + `core.py` | Combined short flags (`-abc`); option-chain default propagation; deferred open in `File`; completion var resolution |
| 3 | `core.py`, `types.py`, `decorators.py` | Separator-tolerant tuple type; case-insensitive choice; per-command env prefix; suppress-help context setting |
| **Security** | `_termui_impl.py`, `utils.py`, `types.py` | Revert pager resolution to string interpolation with `shell=True`; weaken editor command handling; `open_url` argument handling; path joining without a common-prefix check |

**Measured constraint on this row (pre-check, 31 Oct):** only environment-sourced defects are detectable at G2. Library-parameter defects are invisible — the library-input shell query is absent from the default suite and path injection does not model library parameters. So the security stratum must plant env-sourced defects (`EDITOR`, `PAGER`, config/XDG variables), which for a CLI library is realistic rather than contrived. One library-parameter task stays in the suite as a known-blind control, expected to escape. See [04-g2-precheck.md](04-g2-precheck.md) §7.

The security stratum targets `_termui_impl.py` sinks rather than `shell_completion.py` templates, for the reason in §6. Whether the static-analysis gate detects them is decided by the pre-check, not assumed.

Logic vs security is an orthogonal label in prereg §4.1a, targeted at 3 of 12 pilot tasks.

---

## 9. Risks specific to this choice

| Risk | Handling |
| --- | --- |
| `filterwarnings = error` makes warning hygiene fail the gate | Keep it; realistic. Report warning-caused failures as a separate count so correctness is not conflated with cleanliness |
| click is a dependency of many agent-adjacent tools | Disclosed as a limitation; holdout set; cross-module stratum |
| Upstream drift during the sweep | Pin `subject-v1` = tag `8.5.0` + commit `8b19813`; the sweep never pulls |
| 12.7k LOC is small enough to read | Accept. Timebox and turn cap bound exploration; the limitation paragraph says "repository-level, not large-repository" |
| G2 cannot fire | Pre-check §6, preregistered contingency: four rungs |
| **Single-author study**: the reviewer is also the author, so the review gate is not independent | A limitation of the *study*, not of the repository. Mitigated by an external rubric, a blind second reviewer on a subset, and reported kappa |

The last row corrects an error in the first version: it claimed conventions were "not a community's", which is false for a Pallets project. The actual weakness is that the human gate is operated by the person testing the hypothesis.

---

## 10. To record at M1

- `subject-v1` tag `8.5.0`, commit `8b19813f2bfca99f1018a587a8cf54fc959f2e5d`
- Base image digest and install command
- Exact test invocation including `-m 'not stress'`
- Re-measured suite runtime, three runs, median reported
- §6 pre-check output: baseline alerts by rule, and the planted-defect table
