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

## 5. Result: the diagnosis holds

After the threat-model change, `py/command-line-injection` fires on both A and B. Reproduced locally as well, so the mechanism is confirmed rather than inferred:

| Control | Source class | Remote only (C1) | Local + remote (C2) | Local reproduction |
| --- | --- | --- | --- | --- |
| A `_probe_a.py` | `sys.argv` | none | **`py/command-line-injection`** | line 6 |
| B `_probe_b.py` | `os.environ` | none | **`py/command-line-injection`** | line 7 |
| C `_probe_c.py` | library parameter | none | none | none, suite limitation |

Configuration **C2 is validated**: controls fire, so the gate is really looking.

Control C still does not fire, which matches the earlier finding that `py/shell-command-constructed-from-input` is not in the default 43-rule suite. That is a suite effect, not a threat-model effect, and it is available in C3 if the sweep needs it.

### The unexpected part, and the most interesting one

Enabling local sources surfaced **two pre-existing `py/path-injection` alerts in click's own `src/click/utils.py`** — code that the default configuration had reported as clean for the entire baseline. The baseline was one alert; after the change it is three.

So the default gate did not merely miss planted defects. It missed *real findings in a widely used, heavily reviewed library*, because those findings depend on data arriving from local input.

Two consequences:

1. **G2 is C2.** The rung is defined as (threat model = local + remote, suite = default, severity policy as configured). Five rungs, 180 runs. C1's blindness becomes a primary finding rather than a caveat: "the gate as shipped cannot see local-source vulnerabilities, and enabling local sources surfaced two findings in a library with this much scrutiny behind it."
2. **Those two alerts need adjudication, and that is already the study in miniature.** click is a file-opening library; opening a caller-supplied path is its documented purpose. An alert that is technically true but semantically by-design is exactly the false positive that gate yield must count. Adjudicate both before the pilot and record the verdict, because they are the first real data point for RQ3.

### Adjudication of the three pre-existing alerts

All five open alerts inspected on 31 Oct 2026. The two planted probes are true positives by construction; the three pre-existing ones are not what the gate implies they are.

| # | Rule | Location | What the code does | Verdict |
| --- | --- | --- | --- | --- |
| 1 | `py/clear-text-logging-sensitive-data` | `utils.py:345` `file.write(out)` | `echo()` writing to an output stream, which is the documented purpose of the function | **False positive** (semantic) |
| 4 | `py/path-injection` | `utils.py:598` `os.path.exists(path)` | `_detect_program_name()`; `path` defaults to `sys.argv[0]`, and the only call site (`core.py:1544`) passes nothing | **False positive** (benign) |
| 5 | `py/path-injection` | `utils.py:599` `os.path.exists(f"{path}.exe")` | The adjacent branch of the same expression, on Windows | **False positive**, duplicate of 4 |

Reasoning for 4 and 5: an existence check on the path of the script that is already running reveals nothing to an attacker, who by controlling `argv[0]` has already chosen the invocation. The dataflow is real — `sys.argv[0]` is a `commandargs` source and `os.path.exists` is a sink — but the security consequence is nil. This is a genuine dataflow finding and a meaningless defect.

**Three numbers matter here, and they are not the same number:**

| Unit | Count | How it is counted |
| --- | --- | --- |
| Alerts | 5 | What the API returns |
| Distinct findings | 4 | Alerts 4 and 5 are one expression |
| Actionable defects | 2 | The two planted probes |

RQ3 must be phrased in terms of the third. Gate yield computed on alert counts would credit this gate with five findings when it produced two, and would also charge it with three failures it did not really commit — the FPs are cheap to dismiss, not costly to fix.

One further point for the writeup: **the default configuration reported exactly one of these three, and it was the one least connected to local input.** So C1's "clean" baseline was not quiet, it was under-instrumented.

### Two discrepancies to record honestly

- **The API readback said `threat_model: "remote"` immediately after the change was applied**, while the next analysis clearly behaved as though local sources were on. The readback and the behaviour disagree. Record the effective configuration from the UI and from behaviour, not just the API field, and note the discrepancy.
- **Local reproduction is not identical to GitHub.** The local CLI (queries 1.8.13) reproduces the command-injection alerts but *not* the two path-injection ones that GitHub reports, so GitHub runs a different, presumably newer query pack. Where the two disagree, **GitHub is authoritative**: the gate is what GitHub does, and the local CLI is a convenience.

---

## 6. Remaining steps

**Step 1 — adjudicate the two `py/path-injection` alerts** in `src/click/utils.py`. Get their details:

```fish
gh api "repos/RealNarcissus/click-probe/code-scanning/alerts?state=open&per_page=100" \
  | jq -r '.[] | select(.rule.id=="py/path-injection") | "\(.number)  line \(.most_recent_instance.location.start_line)"'

for n in 2 3
    gh api "repos/RealNarcissus/click-probe/code-scanning/alerts/$n" | jq -r '.most_recent_instance.message.text'
end
```

Record: line, message, true positive or by-design. This is RQ3 data, not housekeeping.

**Step 2 — the five defects under C2.** One commit each, reverting between:

| # | Defect | Source class | Expect |
| --- | --- | --- | --- |
| D1 | Editor invocation as interpolated string, `shell=True` | `EDITOR` env | `py/command-line-injection` |
| D2 | Pager invocation as interpolated string, `shell=True` | `PAGER` env | `py/command-line-injection` |
| D3 | `open_url` builds a shell string from its argument | function parameter | likely none at C2 |
| D4 | File open path joined to CWD unchecked | function parameter | uncertain; same class as the utils.py alerts |
| D5 | `eval()` on an option value | parsed CLI value | `py/code-injection` if local sources reach it |

**Step 3 — only if C2 yields fewer than 2 of 5**, repeat under C3 (extended suite), where the library-input query exists. Do not run three configurations on five defects by default.

Keep the probe repository public, one branch per defect. The alerts page and the matrix are part of the replication package.

---

## 7. Status

| Item | State |
| --- | --- |
| Baseline under C1 | 1 alert; all three controls silent |
| C2 validated | controls A and B fire, locally and on GitHub |
| Rung definition | **G2 = C2** (local + remote threat model, default suite) |
| Ladder | five rungs, 180 pilot runs |
| Pre-existing alerts | adjudicated: 3 of 3 false positives; 5 alerts = 4 findings = 2 actionable defects |
| Pending | run D1-D5 under C2 |
