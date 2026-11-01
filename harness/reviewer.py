"""The G3 reviewer: one model call, one verdict, fail-closed.

The prompt is a committed file and its sha256 is part of the treatment. If the
file and the hash recorded in the rung config disagree, the gate fails rather
than running a reviewer that nobody froze.

Failure semantics, deliberately blunt: a timeout, a non-zero exit, unparseable
output, a missing verdict or an unknown verdict all yield ``verdict=error`` and a
gate that does NOT pass. There is no path where a broken call becomes an
approval.
"""
import hashlib
import json
import pathlib
import re
import subprocess
import tempfile
import time

from . import sandbox

PROMPT_PATH = pathlib.Path(__file__).resolve().parent.parent / "configs" / "g3" / "reviewer_prompt.md"
SEVERITIES = ("critical", "major", "minor")


def prompt_text() -> str:
    return PROMPT_PATH.read_text()


def prompt_hash() -> str:
    return hashlib.sha256(PROMPT_PATH.read_bytes()).hexdigest()


def _parse_payload(text: str) -> dict:
    """Extract the single JSON object the prompt asks for."""
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError("no JSON object in reviewer output")
    data = json.loads(match.group(0))
    verdict = data.get("verdict")
    if verdict not in ("approve", "reject"):
        raise ValueError(f"unknown verdict: {verdict!r}")
    findings = data.get("findings")
    if not isinstance(findings, list):
        raise ValueError("findings is not a list")
    for f in findings:
        if not isinstance(f, dict) or f.get("severity") not in SEVERITIES:
            raise ValueError(f"bad finding: {f!r}")
    return {"verdict": verdict, "findings": findings}


def review(diff: str, spec: str, home: pathlib.Path, cfg: dict,
           scratch: pathlib.Path | None = None) -> dict:
    """Run the reviewer once and return evidence, never an implicit approval."""
    model = cfg.get("model", "opencode-go/claude-haiku-5-5")
    timeout = int(cfg.get("timeout_seconds", 180))
    scratch = scratch or pathlib.Path(tempfile.mkdtemp(prefix="foreman-review-"))
    prompt = prompt_text().replace("{spec}", spec).replace("{diff}", diff)
    cmd = ["/opencode-bin/bin/opencode", "run", "--standalone", "--model", model,
           "--auto", "--format", "json", prompt]
    wrapped = sandbox.wrap(cmd, scratch, home)

    t0 = time.time()
    out, err, rc, timed_out = "", "", None, False
    try:
        p = subprocess.run(wrapped, cwd=scratch, capture_output=True, text=True,
                           timeout=timeout)
        rc, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        timed_out = True
        out = (e.stdout or "") if isinstance(e.stdout, str) else (e.stdout or b"").decode(errors="replace")
        err = (e.stderr or "") if isinstance(e.stderr, str) else (e.stderr or b"").decode(errors="replace")
    except Exception as exc:  # sandbox missing, binary missing, ...
        return {"verdict": "error", "error": f"{type(exc).__name__}: {exc}",
                "invoked": False, "model": model, "prompt_hash": prompt_hash(),
                "diff_sha256": hashlib.sha256(diff.encode()).hexdigest(),
                "latency_s": round(time.time() - t0, 1)}

    texts, session, tokens, cost, invoke_evidence = [], None, {"input": 0, "output": 0}, 0.0, False
    for line in (out or "").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except Exception:
            continue
        part = ev.get("part", {})
        if ev.get("sessionID"):
            session = session or ev["sessionID"]
            invoke_evidence = True
        if part.get("type") == "step-finish":
            invoke_evidence = True
            cost += float(part.get("cost") or 0)
            tk = part.get("tokens") or {}
            tokens["input"] += int(tk.get("input") or 0)
            tokens["output"] += int(tk.get("output") or 0)
        if ev.get("type") == "text":
            texts.append(part.get("text", ""))

    base = {"model": model, "prompt_hash": prompt_hash(),
            "diff_sha256": hashlib.sha256(diff.encode()).hexdigest(),
            "session": session, "tokens": tokens, "cost_usd": round(cost, 6),
            "latency_s": round(time.time() - t0, 1),
            "invoked": bool(invoke_evidence and texts), "raw": "\n".join(texts)[:4000]}

    if timed_out:
        return {**base, "verdict": "error", "error": f"timeout after {timeout}s"}
    if rc != 0:
        return {**base, "verdict": "error",
                "error": f"exit {rc}: {(err or out)[-300:]}"}
    try:
        payload = _parse_payload("\n".join(texts))
    except Exception as exc:
        return {**base, "verdict": "error", "error": f"{type(exc).__name__}: {exc}"}
    return {**base, **payload}
