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

## 4. What to run instead

G2 is not "CodeQL, the tool". It is **GitHub's default code-scanning configuration for a public repository**, which is what a real gate applies. Running it anywhere else is a proxy, and this proxy has now demonstrably failed to validate itself.

Procedure:

1. Fork `pallets/click` to a public repository at tag `8.5.0`. Public is required: CodeQL is free for public repositories, not private ones.
2. Settings, Code security, Code scanning, enable **Default** setup for Python. Wait for the first analysis.
3. Record the alert count by rule id. This is the baseline.
4. On a branch, plant one defect at a time from the table below, push, and record which rule fires.
5. Keep the fork's alerts page as the artifact.

Cost: no CodeQL minutes are consumed for public repositories under default setup, so the only cost is wall clock.

### Defect table

| # | Defect | Source class | Expected surface |
| --- | --- | --- | --- |
| D1 | Editor invocation replaced with an interpolated string and `shell=True` | `EDITOR` environment variable | command injection |
| D2 | Pager invocation replaced with an interpolated string and `shell=True` | `PAGER` environment variable | command injection |
| D3 | `open_url` builds a shell string from its `url` argument | function parameter | command injection |
| D4 | File open path joined to CWD without validation | function parameter | path injection |
| D5 | `eval()` on an option value | parsed CLI value | code injection |

D1-D5 are shapes an agent could plausibly introduce while "simplifying" the code, not contrived patterns. `_termui_impl.py` already carries a comment about resolving unqualified commands through `shutil.which` for security reasons, so regressing it is realistic.

---

## 5. Decision rule

Unchanged in substance, tightened in one respect:

- **Precondition:** a positive control must fire. If the canonical `os.system("echo " + sys.argv[1])` sample produces no alert in the target configuration, the configuration is not validated and nothing downstream counts.
- **Then:** if fewer than 2 of the 5 planted defects produce a *security* rule alert, **G2 is dropped** and the ladder is four rungs (G0, G1, G3, G4). Pilot cost falls from 180 to 144 runs.
- The full table is released either way, including the defects that were missed.

Two smaller findings to carry into the design:

- **Suites differ by a lot.** 43 rules versus 172 between the default and extended suites. Which suite the gate runs is a configuration variable that changes what the gate can see, and it must be recorded as part of the rung definition rather than assumed.
- **Quality rules will fire on agent changes for reasons unrelated to security.** `py/file-not-closed` fired on a five-line control. Gate yield must therefore be adjudicated separately for security-class and quality-class alerts, or the AI/static-analysis rungs will look productive when they are only busy.

---

## 6. Open

- [ ] Version-matched CLI retry, or abandon local CodeQL in favour of §4
- [ ] §4 run on a public fork; baseline and defect table recorded
- [ ] Rung count decided from §5
