"""Hidden scoring oracle. Applied out of band, in a copy the worker never saw."""
import os
import pathlib
import shutil
import subprocess

from . import config


def score(worktree: pathlib.Path, oracle_src: str, dest: pathlib.Path) -> dict:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(worktree, dest, ignore=shutil.ignore_patterns("_codeql_db", "_codeql.sarif"))
    test = dest / "tests" / "test_oracle_hidden.py"
    test.write_text(oracle_src)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(dest / "src")
    r = subprocess.run([config.PYTHON, "-m", "pytest", "-q", "tests/test_oracle_hidden.py",
                        "--noconftest", "-p", "no:cacheprovider"],
                       cwd=dest, capture_output=True, text=True, env=env)
    return {"passed": r.returncode == 0,
            "detail": "\n".join((r.stdout or r.stderr).strip().splitlines()[-3:])}
