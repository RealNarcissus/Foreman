# Pilot task suite

Twelve tasks, 4 per tier, each with a hidden oracle that is never present in the
agent's worktree.

| Tier | Count | What it is |
| --- | --- | --- |
| 1 | 4 | Single-function mutation; click's own suite fails |
| 2 | 4 | Cross-cutting mutation across call paths |
| 3 | 4 | Small additive feature; click's suite says nothing |

Security class (orthogonal to tier): **T1-04, T2-S1, T2-S2**.

- `T2-S1` editor via `EDITOR`, `T2-S2` pager via `PAGER` — environment-sourced,
  the only shape G2 has been observed to catch.
- `T1-04` is the **known-blind control**: a library-parameter flow that G2 could
  not see in any configuration tested. Expected to score as a gate escape.

Verification: `python3 tools/verify_tasks.py`. Every task must fail its oracle on
the seeded state and pass on the pristine or reference state. `verification.json`
holds the recorded result; `ledger/tasks.csv` is the flat summary.

Two facts from verification worth keeping:

- `T2-S1` and `T1-02`, `T1-01`, `T1-03`, `T2-01`, `T2-02` make click's own suite
  fail, so G1 can see them.
- `T1-04`, `T2-S2` and all four tier-3 tasks leave click's suite green, so G1
  cannot see them. For `T1-04` that is the point; for `T2-S2` it is a genuine
  gap in click's tests, and it means only G2 has a chance at that defect.
