# M2: containment failure and the fix

**Status: the first smoke test is void.** All 17 runs it produced are archived to
`ledger/smoke-void.json` and excluded. The cause is found and fixed; the smoke
test has not been re-run.

## What happened

The first real worker runs looked excellent: DeepSeek V4.1 Flash completed 8 of 8
holdout tasks, Claude Haiku 5.5 completed 0 of 8, MiMo-V2.6 Flash 1 of 1.

Haiku's failure text was the tell. It reported that `tasks/holdout.py` is
"documented as used ONLY for worker selection", and asked to be pointed at the
Click checkout. It had been reading the project, not its worktree.

Auditing every worker log confirmed it: **all 17 runs read `tasks/tasks.py`, which
contains every oracle, and several read `harness/oracle.py` directly.** The
successes are as contaminated as the failures.

## Cause

`opencode run` attaches to a **shared background server** unless told otherwise.
That server's project root is wherever it started, so the `cwd=` passed to the
subprocess was ignored and the agent worked inside the Foreman project instead of
the run worktree. opencode's own help names the fix:

```
--standalone   Run with a private server instead of the background service
```

## Fixes applied

| Fix | Detail |
| --- | --- |
| `--standalone` | Private server per run, rooted at the worktree |
| Worktrees moved out of the project | `/tmp/foreman-work/<run>/worktree`, so `..` reaches nothing sensitive |
| Oracle copy moved out of the worktree's parent | It previously sat in the run directory, one `..` away |
| Log path corrected | The adapter wrote `worker.log` to one root while the runner read another, so the containment check silently passed everything |
| Ledger schema | Header/row mismatch fixed; ledger rebuilt |

## Verification

One run after the fix: **0 containment hits, `valid=true`, oracle passed**,
$0.0089 and 45.6k input tokens, 82s.

## Consequence for the plan

Containment is a hard precondition, not a nicety: a run whose log mentions an
oracle, a task file or another run's artifacts is void regardless of its oracle
result. The check meant to enforce that had been dead for exactly the runs that
needed it.

The smoke test must be re-run from scratch before any worker is selected. Nothing
from the void run may be cited — including DeepSeek's apparent 100% ceiling, which
was not one.
