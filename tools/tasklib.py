"""Task patching and verification helpers."""
import shutil, subprocess, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

PRISTINE = pathlib.Path("/tmp/click_tag")


from harness.patching import block, patch  # noqa: E402,F401


def fresh(dst: pathlib.Path) -> pathlib.Path:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(PRISTINE, dst, ignore=shutil.ignore_patterns(
        ".git", ".v", "__pycache__", "*.pyc"))
    return dst


def _env(root: pathlib.Path) -> dict:
    import os
    e = dict(os.environ)
    e["PYTHONPATH"] = str(root / "src")
    return e


def run_oracle(root: pathlib.Path, oracle_src: str) -> bool:
    """True if the oracle test passes."""
    d = root / "tests" / "test_oracle_hidden.py"
    d.write_text(oracle_src)
    r = subprocess.run(["python3", "-m", "pytest", "-q", "tests/test_oracle_hidden.py",
                        "-p", "no:cacheprovider"],
                       cwd=root, capture_output=True, text=True, env=_env(root))
    d.unlink()
    return r.returncode == 0


def run_own_suite(root: pathlib.Path) -> bool:
    """True if click's own suite still passes (i.e. the defect is invisible to it)."""
    r = subprocess.run(["python3", "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                       cwd=root, capture_output=True, text=True, env=_env(root))
    return r.returncode == 0
