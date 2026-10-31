"""Scoped source patching. One primitive, shared by task verification and the runner."""
import re
import pathlib


def block(text: str, start: str, nth: int = 0) -> tuple[int, int]:
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
    """Replace the first `old` inside the `fn` block of `file`."""
    if spec.get("append"):
        p = root / spec["file"]
        p.write_text(p.read_text() + spec["append"])
        return
    p = root / spec["file"]
    text = p.read_text()
    a, b = block(text, spec["fn"], spec.get("nth", 0))
    lines = text.splitlines(keepends=True)
    seg = "".join(lines[a:b])
    if spec["old"] not in seg:
        raise LookupError(f"{spec['file']}: {spec['old']!r} not in {spec['fn']}")
    p.write_text(text.replace(seg, seg.replace(spec["old"], spec["new"], 1), 1))
