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

Good news for the odds, verified locally against the 43-rule default suite: `py/command-line-injection`, `py/path-injection`, `py/code-injection` and `py/unsafe-deserialization` are all in it. The default configuration is sufficient; there is no need to select the extended suite and no need to introduce that as a confound.

Cost: CodeQL default setup on public repositories does not consume Actions minutes. The only cost is wall clock, roughly 30-60 minutes including analysis waits.

### Runbook

**Step 1 — probe repository.** Do not fork: a fork carries the upstream's settings and tags may not come along.

```sh
git clone --branch 8.5.0 --depth 1 https://github.com/pallets/click /tmp/click-probe
cd /tmp/click-probe && rm -rf .git && git init -b main
git add -A && git commit -m "click 8.5.0 snapshot"
gh repo create click-probe --public --source=. --remote=origin --push
```

**Step 2 — enable default setup.**

```sh
gh api -X PATCH repos/OWNER/click-probe/code-scanning/default-setup \
  -f state=configured -f query_suite=default
```

Or in the UI: Settings, Code security, Code scanning, CodeQL analysis, Set up, Default. The first analysis takes a few minutes.

**Step 3 — baseline.**

```sh
gh api "repos/OWNER/click-probe/code-scanning/alerts?state=open&per_page=100" \
  | jq -r '.[].rule.id' | sort | uniq -c | sort -rn
```

Record it. This is the noise floor; only alerts beyond it are attributable to a planted defect.

**Step 4 — two positive controls, before any defect.** The second one matters more than the first, because the click defects in the table depend on environment variables rather than argv.

```sh
# control A: argv-sourced command construction
cat > src/click/_probe_a.py <<'EOF'
import os, sys
def run():
    os.system("echo " + sys.argv[1])
run()
EOF

# control B: environment-sourced command construction (the class D1/D2 rely on)
cat > src/click/_probe_b.py <<'EOF'
import os, subprocess
def run():
    editor = os.environ.get("EDITOR", "vi")
    subprocess.Popen(f"{editor} file.txt", shell=True)
run()
EOF
git add -A && git commit -m "probe: positive controls" && git push
```

Then wait for analysis and re-read the alerts. Interpretation is strict:

| Result | Meaning | Action |
| --- | --- | --- |
| Both controls alert | Configuration is sound | Proceed to step 5 |
| Only A alerts | Environment variables are not modelled as sources | D1/D2 cannot fire; click has no argv entry point, so G2 likely cannot fire on realistic defects. Expect to drop G2 |
| Neither alerts | Configuration invalid, as it was locally | **Stop.** Do not interpret any defect result |

**Step 5 — the five defects**, one commit each, reverting between them so the alert delta is attributable:

```sh
# for each defect: apply, then
git add -A && git commit -m "probe: D1" && git push
# wait for the analysis to finish, re-read alerts, record the delta
```

**Step 6 — keep the artifact.** Leave the probe repository public and leave one branch per defect (`probe-d1` ... `probe-d5`). The alerts page and the defect table are released with the replication package; a publicity objection is not a problem here, the defects are synthetic.

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

- [ ] Step 4 controls run: record which of A and B fires
- [ ] Step 5 defect table completed
- [ ] Rung count decided from §5
- [ ] Version-matched CLI retry only if step 4 fails and GitHub is somehow unavailable (it should not be)
