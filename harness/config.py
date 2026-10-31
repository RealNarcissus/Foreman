"""Paths and pinned constants. Nothing here is inferred at runtime."""
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SUBJECT = pathlib.Path(os.environ.get("FOREMAN_SUBJECT", "/tmp/click_tag"))
import tempfile
# Run worktrees live OUTSIDE the project so ../.. cannot reach
# tasks/, oracle sources, docs or other runs.
RUNS = pathlib.Path(os.environ.get("FOREMAN_RUNS", "/tmp/foreman-runs"))
# Worktrees get their own root so `..` from inside one reaches nothing sensitive.
WORK = pathlib.Path(os.environ.get("FOREMAN_WORK", "/tmp/foreman-work"))
LEDGER = ROOT / "ledger" / "runs.csv"
CODEQL = os.environ.get("FOREMAN_CODEQL", "/tmp/cql/codeql/codeql")
# Frozen G2 configuration (configs/g2/c2-local-in-scope.json).
# GitHub's UI label "Remote and local sources" is NOT a CodeQL CLI threat-model
# name: passing --threat-model=remote_and_local enables nothing. The CLI needs
# the two models named separately. This is a translation, not a synonym.
THREAT_MODELS = ("local", "remote")
QUERY_SUITE = "python-code-scanning.qls"
TIMEBOX_SECONDS = int(os.environ.get("FOREMAN_TIMEBOX", "1800"))
PYTHON = os.environ.get("FOREMAN_PYTHON", "python3")
