# Containment controls

The detector had never been asked to catch anything deliberately. It had fired
seven times by accident, all before the sandbox existed, and every zero-hit run
afterwards was indistinguishable from a check that did not run.

This adds four controls and makes the harness fail closed.

## What changed

| Change | Why |
| --- | --- |
| **Fail closed** — a worker that needs the sandbox refuses to run without it | The old code fell back to running unsandboxed and reported the result as clean |
| **Per-run sandbox probe** | Turns a one-off manual check into per-run evidence: asserts `pwd` is `/work`, the host home is absent, and the worktree is mounted |
| **Log contract** (`writes_log`) | A worker that promises `worker.log` and writes none is marked invalid, instead of the check silently returning `[]` |
| **`harness selfcheck`** | Four scenarios, no model spend, run in seconds |
| **Separate ledger** | Controls write to `ledger/selfcheck.csv`, never to the analysis ledger |

## The controls

```
$ python3 -m harness.cli selfcheck
scenario        result  detail
positive-leak   PASS    hits=1 valid=False
negative-clean  PASS    hits=0 valid=True probe_ok=True
log-missing     PASS    error='worker.log missing: containment check could not run' valid=False
fail-closed     PASS    refused=True
4/4 passed
```

`positive-leak` uses a canary file containing a marker string and a worker that
reads and logs it. That is the test the earlier work never performed.

## Evidence from a real run

```
valid: True | probe ok: True | hits: 0 | containment_error: None
probe detail: /work | HOSTHOME_ABSENT | WORKTREE_OK
```

So the probe records, per run, that the mount namespace was what we think it is.
A run with a broken sandbox now fails `valid` rather than passing quietly.

## What this does and does not license

It licenses calling a run valid **when the probe recorded a good sandbox and the
log scan found nothing**. It does not retroactively validate runs made before the
probe existed — those have no per-run evidence, only a one-off manual check.

The 4/4 and the other smoke results stay **provisional** until re-run under this
harness. The re-run is cheap (roughly $0.50) and unattended.

## Disk note

`/tmp` filled during construction because each sandbox home carried a full copy
of the OpenCode config tree. Homes are per run and disposable; on a 7.5 GB tmpfs,
24 runs will need the older ones cleaned as they go. Worth handling before the
pilot rather than discovering it at run 15.
