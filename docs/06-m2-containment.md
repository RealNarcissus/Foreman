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

---

## Sandbox: filesystem isolation works, credentials do not cross

`bwrap` is available (0.13.1) and the mount namespace behaves correctly:

```
ls $HOME/Desktop   ->  No such file or directory
pwd                          ->  /work
HOME                         ->  /home/agent
```

The project directory is not mounted, so an oracle is unreachable rather than
merely detectable. That part is solved.

**Authentication fails inside the sandbox**, and only there:

| Context | Result |
| --- | --- |
| Host, `--standalone` | works |
| Sandbox, copied `auth.json` + `account.json` | `401 api_key_expired` |
| Sandbox, DBus session bus bound | `401 api_key_expired` |
| Sandbox, `OPENCODE_API_KEY` passed through | `401 api_key_expired` |

So the working credential is not in `auth.json`, not in `account.json`, not on
the session bus and not in the process environment. The remaining candidate is
the 306 MB `opencode.db` in the host state directory, which the sandbox does not
have.

Binding that directory read-write would fix authentication and reintroduce a
leak: the database holds transcripts of every prior session, including the
contaminated runs that quoted task text and oracles.

**Therefore M2 is blocked, not finished.** The options, in order of cleanliness:

1. **Issue a fresh OpenCode Go API key for the harness and pass it in.** The
   sandbox then needs no host state at all, which is also the only option that
   makes the credential auditable. Recommended.
2. Copy a sanitised state directory per run. 306 MB per run, and it must be
   scrubbed of transcripts first.
3. Accept host-state binding and treat the sandbox as filesystem-only isolation.
   Not recommended: it defeats the point.

Until one is chosen, no worker selection can be made and no sweep can run.
