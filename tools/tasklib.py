"""Task patching and verification helpers."""
import re, shutil, subprocess, textwrap, pathlib

PRISTINE = pathlib.Path("/tmp/click_tag")


def block(text: str, start: str, nth: int = 0) -> tuple[int, int]:
    """Return (start,end) line offsets of the nth block whose stripped line begins with `start`."""
    lines = text.splitlines(keepends=True)
    hits = [i for i, ln in enumerate(lines) if ln.strip().startswith(start.strip())]
    if len(hits) <= nth:
        raise LookupError(f"block not found: {start!r} (nth={nth}, hits={len(hits)})")
    i = hits[nth]
    indent = len(lines[i]) - len(lines[i].lstrip())
    for j in range(i + 1, len(lines)):
        l = lines[j]
        if l.strip() and (len(l) - len(l.lstrip())) <= indent and re.match(r"\s*(def |class |@)", l):
            return i, j
    return i, len(lines)


def patch(root: pathlib.Path, spec: dict) -> None:
    """spec: {file, fn, old, new} — replace first `old` inside the `fn` block."""
    p = root / spec["file"]
    text = p.read_text()
    a, b = block(text, spec["fn"], spec.get("nth", 0))
    lines = text.splitlines(keepends=True)
    seg = "".join(lines[a:b])
    if spec["old"] not in seg:
        raise LookupError(f"{spec['file']}: {spec['old']!r} not in {spec['fn']}")
    p.write_text(text.replace(seg, seg.replace(spec["old"], spec["new"], 1), 1))


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
