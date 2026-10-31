# G2 pre-check: status

**Result: INCONCLUSIVE. The local run is void.** No conclusion about click's code, and no decision about the rung, may be drawn from it. The pre-check has to run in GitHub's default code-scanning configuration instead.

This document exists so the failure is on the record with enough detail to continue, rather than being quietly retried until it produces a preferred answer.

---

## 1. What was installed

| Component | Version |
| --- | --- |
| CodeQL CLI | 2.27.3 (bundle, `/tmp/cql/codeql`) |
| `codeql/python-queries` | 1.8.13 |
| `codeql/python-all` | 7.2.8 |
| Host | x86_64 Linux, 12 cores |

Installed cleanly, unauthenticated, no registry problems. Cost: 400 MB download, one-time.

---

## 2. What ran

Database creation for `pallets/click` @ `8.5.0` (79 files): about 5s. Analysis with the default code-scanning suite: 18s. **The pipeline is cheap enough to run per task**; that part of the design is fine.

Suites, and the number of rules each actually executed:

| Suite | Rules |
| --- | --- |
| `python-code-scanning.qls` (GitHub default) | 43 |
| `python-security-extended.qls` | 50 |
| `python-security-and-quality.qls` | 172 |

Baseline on unmodified click: **1 alert**, `py/clear-text-logging-sensitive-data`.

---

## 3. Why the result is void

The baseline of 1 alert is not evidence that click is clean. It is evidence that the dataflow half of the analysis is not working on this host.

Positive control, a file containing the canonical pattern:

```python
import os, sys
def run():
    os.system("echo " + sys.argv[1])
    subprocess.call(sys.argv[1], shell=True)
    return open(sys.argv[2]).read()
if __name__ == "__main__":
    run()
```

Run under all three suites, plus the CWE-078 query file executed directly: **0 results**. Four result sets in the `.bqrs`, zero rows in `#select`. The rule `py/command-line-injection` is present in the SARIF driver rules — so the query compiles and evaluates — but the taint path is never found.

Contrast: purely AST-shaped queries do fire, `py/file-not-closed` on the control and `py/clear-text-logging-sensitive-data` on click. So extraction and evaluation work; **source-to-sink dataflow does not**.

Attempted before concluding: installing the missing `python-all` library pack, running the query directly outside the suite, adding a `__main__` entry point, and re-creating the database. None changed the result.

**Most likely cause:** a version mismatch between CLI 2.27.3 and the shipped Python query pack, or an environment issue with the source/sink model packs that I could not isolate here. The expected fix is a version-matched CLI, which means another 400 MB download and is not obviously worth it when §4 is the configuration the study would actually use.

---

## 4. The mechanism: the default threat model excludes local sources

**Run of 31 Oct 2026. All three positive controls produced zero alerts; the only open alert is the pre-existing baseline.** The CodeQL analysis did run on the probe commit (`043040e`, analysis `41188957632`, conclusion success), so this is not a cache or staleness problem.

The cause is in the default-setup configuration itself:

```json
{ "state": "configured", "languages": ["actions","python"],
  "query_suite": "default", "threat_model": "remote" }
```

`threat_model: remote`. In the Python model pack, source *kinds* are assigned to threat models, and these are the assignments that matter:

| Source kind | Produced by | Threat model |
| --- | --- | --- |
| `commandargs` | `sys.argv`, `argparse` | **local** |
| `environment` | `os.environ`, `os.getenv` | **local** |
| `stdin` | `input()`, `sys.stdin` | **local** |
| `file` | `os.read` | **local** |

Source: `codeql/python-all` `Stdlib.model.yml` for the kinds, and `codeql/threat-models` `threat-model-grouping.model.yml` for the grouping.

So under the shipped default, **command-line arguments, environment variables, stdin and files are not threat sources at all.** Every sink is still modelled, and no data can reach one. A CLI tool or a library that reads local input therefore gets zero coverage of command injection, path injection and the rest, not because the queries are missing but because the sources are switched off.

That fully explains the three zeros, and it explains why the local CLI run behaved identically: same threat model, same silence.

### Why this is a result, not an obstacle

The original plan treated G2 as "the static analysis rung", assuming a gate either sees a defect or does not. The truth is that **the gate's threat model decides what exists as a defect**, and the shipped default is configured for web services rather than for libraries and CLIs. A repository like click, which takes its input from arguments and environment variables, is structurally outside the default gate's scope.

This is exactly the class of finding the study is for: not "the gate missed a bug", but "the gate was never looking". It also means the rung has to be defined as a triple, not a name:

> **G2 = (threat model, query suite, severity policy)**

Configurations worth measuring, in order of realism:

| # | Threat model | Suite | Meaning |
| --- | --- | --- | --- |
| C1 | `remote` | default | What a team gets by pressing the button |
| C2 | local + remote | default | Deliberately configured for local input |
| C3 | local + remote | extended | As C2, plus the library-input query |

---

## 5. Configuration resolved

The UI and the API disagree, and the UI is right:

| Source | Reports |
| --- | --- |
| Settings, Advanced Security, CodeQL default configuration | Threat model: **"Remote and local sources"**, Query suite: Default, Languages: Actions + Python |
| `GET .../code-scanning/default-setup` | `"threat_model": "remote"` |
| Observed behaviour | Local sources active (controls A and B fire) |

Resolution: **the effective configuration is local + remote**, and the `default-setup` readback **lags the applied configuration by roughly one analysis cycle**. Observed twice, in both directions:

| Action | Immediate readback | After ~90s and one analysis |
| --- | --- | --- |
| set `threat_model` remote_and_local | `"remote"` | `"remote_and_local"` |
| set `query_suite` back to default | `"extended"` | `"default"` |

So the field is eventually consistent, not stale in the sense of wrong. Two rules follow:

- **Verify after a delay**, or behaviourally: extended-only alerts close on the next analysis after reverting the suite.
- **Never cite the readback taken immediately after a PATCH.** Cite the UI label plus a post-delay readback.

Configurations C1 and C2 are now stored as reproducible artifacts in [`configs/g2/`](../configs/g2/), each with the exact PATCH payload, the settings it produces, and the verification steps. They are configurations, not labels for runs.

**G2 definition, frozen:**

| Component | Value |
| --- | --- |
| Threat model | Remote and local sources |
| Query suite | Default (43 rules) |
| Severity policy | GitHub default setup, public repository |
| Scan events | Push and pull request to main; weekly schedule |

---

## 6. Adjudication of the three pre-existing alerts

All five open alerts inspected on 31 Oct 2026. The two planted probes are true positives by construction; the three pre-existing ones are not what the gate implies they are.

| # | Rule | Location | What the code does | Verdict |
| --- | --- | --- | --- | --- |
| 1 | `py/clear-text-logging-sensitive-data` | `utils.py:345` `file.write(out)` | `echo()` writing to an output stream, the documented purpose of the function | **False positive** (semantic) |
| 4 | `py/path-injection` | `utils.py:598` `os.path.exists(path)` | `_detect_program_name()`; `path` defaults to `sys.argv[0]`, and the only call site (`core.py:1544`) passes nothing | **False positive** (benign) |
| 5 | `py/path-injection` | `utils.py:599` `os.path.exists(f"{path}.exe")` | Adjacent branch of the same expression, Windows path | **False positive**, duplicate of 4 |

An existence check on the path of the process that is already running reveals nothing to an attacker who, by controlling `argv[0]`, has already chosen the invocation. The dataflow is real; the defect is not.

---

## 7. Planted-defect experiments

Each experiment is one commit on `main`, analysed after the push, with the previous defect reverted first so attribution is unambiguous.

| Commit | Experiment | Source class | Fired | Rule |
| --- | --- | --- | --- | --- |
| `043040e` | A: `os.system` on `sys.argv[1]` | `commandargs` | **yes** | `py/command-line-injection` |
| `043040e` | B: `Popen(f"{editor} f", shell=True)` on `os.environ` | `environment` | **yes** | `py/command-line-injection` |
| `043040e` | C: `Popen(f"xdg-open {url}", shell=True)` on a library parameter | library input | no | — |
| `6edb6e8` | D3: `open_url(url)` builds a shell string in `_termui_impl.py` | library input | no | — |
| `8f0159f` | D4: path joined to CWD via a resolve helper in `utils.py` | library input | no | — |
| `3fedb07` | E: `launch_browser(url)` → shell, **public module, extended suite** | library input | no | — |
| `3fedb07` | F: `read_entry(name)` → `open`, **public module, extended suite** | library input | no | — |

`7c99c07` is an artefact: a revert of D3 committed under a D4 message. The D4 content is `8f0159f`. The repository history is left unrewritten on purpose; provenance over tidiness.

E and F exist because the first pass on library-parameter defects had a confound: every probe module was named with a leading underscore, which marks it private and may disqualify its functions as library inputs. E and F are public modules with public functions, analysed under the **extended** suite. Both are silent.

### Two causes, separated

The original write-up ran these together. They are not the same claim, and only one survives the E/F test:

| Cause | Status | Evidence |
| --- | --- | --- |
| The library-input shell query (`py/shell-command-constructed-from-input`) is absent from the default suite | **Real, but not sufficient** | It is present in extended, and E still did not fire |
| `py/path-injection` does not model library parameters as sources | **Holds in both suites** | F did not fire under extended either |

**Therefore: switching to the extended suite is not a fix for library-parameter blindness.** It was a plausible hypothesis, it was testable, and it failed. What extended actually bought on this repository was two additional alerts on pre-existing code — `py/overly-permissive-file` at `_compat.py:435` and `actions/untrusted-checkout/medium` at `.github/workflows/nightly.yaml:31` — neither related to the planted defects, and neither adjudicated yet. More throughput, same blind spot.

The remaining explanation is source modelling: CodeQL's library-input sources did not fire for a public function parameter in either suite, in either the shell or the path case. Stated as an observation about this repository and these probes, not as a general claim about CodeQL.

### What this means for the security stratum

**Only environment- and argv-sourced flows were catchable at C2.** The security-class pilot tasks must therefore plant defects whose source is an environment variable, with realistic variety rather than one repeated shape:

| Class | Source | Shape |
| --- | --- | --- |
| S1 | `EDITOR` | editor invocation loses `shlex.split`, gains `shell=True` |
| S2 | `PAGER` | pager command assembled as a string instead of argv |
| S3 | `XDG_*` / config-dir variable | base path taken from the environment without validation |
| S4 | tool-specific executable variable | resolved executable interpolated into a shell string |

S3 and S4 exist so the stratum is not three copies of one pattern. A gate that catches only "`EDITOR` plus `shell=True`" has not been shown to catch environment-sourced injection generally.

One further task is library-parameter-sourced **by design**, as a known-blind control, so the evaluation distinguishes genuine capability from a scanner's coverage boundary. Expect a gate escape; that is the measurement.

---

## 8. Recall, precision and deduplicated yield

Defined before computing, because the choice of denominator changes the answer:

- **Planted classes** — the four defect shapes actually run: argv-to-shell, env-to-shell, param-to-shell, param-to-path.
- **Alert** — one row from the API.
- **Distinct finding** — alerts deduplicated by rule and code expression; alerts 4 and 5 are one finding.
- **Actionable** — a finding a maintainer would act on, as adjudicated.

| Metric | C1 (default) | C2 (local + remote) |
| --- | --- | --- |
| **Observed probe-set recall** (n=4, see caveat) | **0 of 4 (0%)** | **2 of 4 (50%)** |
| Alerts raised | 1 | 5 |
| Distinct findings | 1 | 4 |
| Actionable findings | 0 | 2 |
| Precision over alerts | 0 of 1 (0%) | 2 of 5 (40%) |
| Precision over distinct findings | 0 of 1 (0%) | 2 of 4 (50%) |
| **Deduplicated actionable yield** | **0** | **2** |

Two readings that matter for the paper:

1. **The default configuration detected nothing real** — not the planted defects, and not the pre-existing findings that the local threat model surfaces. Its single alert was a false positive.
2. **Enabling local sources doubles nothing cleanly**: it lifts recall from 0% to 50% and precision from 0% to 50%. The gate becomes useful and noisy at the same time. That is a more honest and more interesting result than either "the gate works" or "the gate does not work".

**The 50% figure is observed probe-set recall, and nothing more.** It is the fraction of *these four probes* that fired. It is not an estimate of CodeQL's recall in general, and it must not be quoted as one: four probes, one repository, two of them environment-sourced by construction. The paper should carry the phrase "observed probe-set recall (n=4)" every time this number appears.

The same caution applies to the precision figures, though they are less susceptible to it because the adjudication is inspection of named lines rather than inference.

Caveat carried forward: n=4 planted classes and n=3 adjudicated pre-existing alerts on one repository. This is a configuration check, not an estimate. The pilot exists to turn it into one.

---

## 9. Decision

**G2 stands, defined as C2.** Five rungs, 180 pilot runs.

The rung is defensible on evidence rather than assertion: controls fire, two of four planted classes are detected, and the configuration is a documented, selectable GitHub setting rather than a bespoke local harness.

What the pre-check changed in the plan:

- The security stratum is now **env-sourced by constraint**, not by preference (§7).
- Gate yield is computed on **actionable findings**, not alerts (§8), or the gate would be credited for noise.
- The configuration record gains threat model as a required field.
- One library-parameter task is kept as a known-blind control, so the paper reports coverage as well as yield.

---

## 10. Status

| Item | State |
| --- | --- |
| Configuration | resolved: Remote and local sources, Default suite |
| Controls | A and B fire; C does not (suite limitation) |
| Defect experiments | D3 and D4 both silent; four classes tested |
| Pre-existing alerts | 3 of 3 adjudicated false positives |
| Recall / precision / yield | 50% / 40% of alerts / 2 actionable |
| G2 | **frozen as C2**, five rungs |
| Remaining | author 12 tasks with the env-sourced security constraint; smoke test; reviewer prompt |
