# Harness

One command per run: provision a worktree from the pinned subject, apply the
task seed, let the worker act, evaluate the rung's gates, score with the hidden
oracle out of band, record everything.

```sh
python3 -m harness.cli run --task T2-S2 --rung G2 --worker scripted:null
python3 -m harness.cli demo --tasks T1-01,T3-01 --rungs G0,G1
```

## Status

| Piece | State |
| --- | --- |
| Worktree provisioning, seed application, diff capture | working |
| G0/G1 gates (no gate, click's suite) | working, validated |
| G2 (CodeQL) | working, **conformant with the cloud gate** (see below) |
| G3 (automated review) | stub, blocked on the pinned prompt |
| G4 (human review) | returns `needs_human`; the timed review CLI is not built |
| Hidden oracle, applied out of band | working, `--noconftest` so a repo conftest cannot disable it |
| Leak check, tamper check | working |
| Ledger, per-run artifacts | working |

## Two things this caught before any model spend

1. **The seed was never applied.** The first demo showed `scripted:null`
   "completing" every mutation task, because the worktree was pristine. Fixed in
   `runner.prepare`.
2. **A tampering worker could disable the oracle.** A root `conftest.py` that
   skips all tests also skipped the hidden oracle, so a broken submission scored
   as correct. The oracle now runs with `--noconftest`.

## The threat-model translation

GitHub's UI label is **"Remote and local sources"**. The CodeQL CLI has no
threat model by that name, and `--threat-model=remote_and_local` silently
enables nothing — the analysis then looks clean while being blind. The CLI needs
the models named separately:

```sh
--threat-model=local --threat-model=remote
```

`config.THREAT_MODELS` holds the tuple and `gates.py` expands it. This is the
same failure mode as the original finding, one layer down: a plausible
configuration string that quietly disables the thing it is supposed to enable.

## Conformance with the real gate

Measured on `T2-S2` (a suite-blind `PAGER` defect):

| Case | Local baseline | Result |
| --- | --- | --- |
| Pristine click | 3 alerts: `py/clear-text-logging-sensitive-data` at `utils.py:345`, `py/path-injection` at `utils.py:598` and `:599` | **identical to the three alerts GitHub reports** |
| Defect present | + `py/command-line-injection` | gate blocks, 1 new security alert |
| Defect fixed | 3 alerts, 0 new | gate passes |

That is the M1 acceptance criterion: the harness's G2 reproduces the cloud
gate's baseline and its detection on a defect we know the cloud gate sees.

## Not yet true

- G3 has no prompt and no model call; it passes everything by construction.
- G4 has no review session or timer.
- The worker is scripted only. No credentials are wired here on purpose.
