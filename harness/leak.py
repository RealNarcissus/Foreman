"""Leak and tamper checks. A run that leaks or tampers does not count."""
import pathlib

TAMPER_MARKERS = ("pytest.mark.skip", "pytest.skip(", "conftest.py", "xfail")
TEST_PATHS = ("tests/", "conftest.py")


def oracle_leaked(worktree: pathlib.Path, oracle_src: str) -> bool:
    if (worktree / "tests" / "test_oracle_hidden.py").exists():
        return True
    needle = "test_oracle_hidden"
    for p in worktree.rglob("*.py"):
        try:
            if needle in p.read_text(errors="ignore"):
                return True
        except OSError:
            pass
    return False


def tampered(diff: str) -> tuple[bool, str]:
    for line in diff.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        if any(t in line for t in TAMPER_MARKERS):
            return True, line.strip()[:120]
        for tp in TEST_PATHS:
            pass
    files = [l for l in diff.splitlines() if l.startswith("diff --git")]
    for f in files:
        if "tests/" in f or f.endswith("conftest.py"):
            return True, f
    return False, ""
