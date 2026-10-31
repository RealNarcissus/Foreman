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

## 5. Runbook

**Step 1 — re-run the controls under a local threat model.** No file changes: just change the configuration and re-trigger the analysis.

```fish
gh api -X PATCH repos/RealNarcissus/click-probe/code-scanning/default-setup \
  -f state=configured -f query_suite=default -f threat_model=remote_and_local

git commit --allow-empty -m "probe: re-analyse with local threat model"
git push
```

If the API rejects `remote_and_local`, use the UI: Settings, Code security, Code scanning, Default setup, Edit configuration, Threat model, and select the option that includes local sources. Record the exact string the API then reports.

Then wait and re-read:

```fish
gh run list --limit 3
gh api "repos/RealNarcissus/click-probe/code-scanning/alerts?state=open&per_page=100" \
  | jq -r '.[] | "\(.rule.id)  \(.most_recent_instance.location.path)"'
```

**Expected if the diagnosis is right:** `py/command-line-injection` on `_probe_a.py` and/or `_probe_b.py`. Control C may still need the extended suite, since `py/shell-command-constructed-from-input` is not in the default 43 rules.

**Step 2 — the five defects, under whichever configuration fired.** One commit each, reverting between:

| # | Defect | Source class |
| --- | --- | --- |
| D1 | Editor invocation as interpolated string, `shell=True` | `EDITOR` environment variable |
| D2 | Pager invocation as interpolated string, `shell=True` | `PAGER` environment variable |
| D3 | `open_url` builds a shell string from its argument | function parameter |
| D4 | File open path joined to CWD unchecked | function parameter |
| D5 | `eval()` on an option value | parsed CLI value |

**Step 3 — only if C2 yields fewer than 2 of 5,** repeat the five defects under C3 (extended suite). Do not run all three configurations on all five defects by default: 15 analyses for a decision that usually resolves in five.

Keep the probe repository public, one branch per defect. The alerts page and the matrix are part of the replication package.

### Decision

| C1 | C2 | Rung |
| --- | --- | --- |
| >= 2 of 5 | — | G2 = C1. Five rungs, 180 runs |
| < 2 of 5 | >= 2 of 5 | **G2 = C2, and the C1 blindness is reported as a primary finding.** Five rungs, 180 runs |
| < 2 of 5 | < 2 of 5 | G2 dropped. Four rungs, 144 runs |

The middle row is the likely outcome and the most valuable one: it converts an assumed control into a measured one, and says plainly that the default configuration does not cover a library's inputs.

## 6. Status and open items

Observed so far: C1 (remote threat model) sees none of the three controls, on GitHub and locally.

- [ ] Controls re-run under a local threat model; record which of A, B, C fires
- [ ] Defect table completed under the configuration that fired
- [ ] Rung count decided from §5
- [ ] Version-matched CLI retry only if step 4 fails and GitHub is somehow unavailable (it should not be)
