"""opencode adapter. One process per run, wall-clock bounded."""
import json
import subprocess
import time

from . import config, sandbox
from .workers import Worker

PROMPT = """You are working inside a Python repository. Make the requested change.

Rules:
- Change source files only. Do not edit anything under tests/.
- Do not add or modify a conftest.py.
- When the change is complete, stop.

Requested change:
{spec}
"""


class OpenCode(Worker):
    def __init__(self, model: str, timeout: int | None = None):
        self.model = model
        self.timeout = timeout or config.TIMEBOX_SECONDS
        short = model.split("/")[-1]
        self.name = f"opencode:{short}"

    def act(self, worktree, task):
        prompt = PROMPT.format(spec=task["spec"])
        # --standalone starts a private server rooted at this cwd. Without it,
        # `run` attaches to a shared background service whose project root is
        # wherever that service started, and the worktree is ignored entirely.
        cmd = ["opencode", "run", "--standalone", "--model", self.model, "--auto",
               "--format", "json", prompt]
        if sandbox.available():
            home = sandbox.home_for(worktree.parent.name)
            cmd = sandbox.wrap(["/opencode-bin/bin/opencode", *cmd[1:]], worktree, home)
            self.sandboxed = True
        else:
            self.sandboxed = False
        t0 = time.time()
        timed_out = False
        try:
            p = subprocess.run(cmd, cwd=worktree, capture_output=True,
                               text=True, timeout=self.timeout)
            rc, out, err = p.returncode, p.stdout, p.stderr
        except subprocess.TimeoutExpired as e:
            rc, timed_out = None, True
            out = (e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
            err = (e.stderr or b"").decode(errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        duration = round(time.time() - t0, 1)

        session, texts, cost, tokens = None, [], 0.0, {"input": 0, "output": 0}
        infra_error = None
        for line in (out or "").splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            session = session or ev.get("sessionID")
            part = ev.get("part", {})
            if ev.get("type") == "error":
                infra_error = (ev.get("error") or {}).get("type") or "error"
            if ev.get("type") == "text":
                texts.append(part.get("text", ""))
            if part.get("type") == "step-finish":
                cost += float(part.get("cost") or 0)
                tk = part.get("tokens") or {}
                tokens["input"] += int(tk.get("input") or 0)
                tokens["output"] += int(tk.get("output") or 0)

        import pathlib
        pathlib.Path(worktree).parent.joinpath("worker.log").write_text(
            f"model: {self.model}\nreturncode: {rc}\ntimed_out: {timed_out}\n"
            f"duration_s: {duration}\nsession: {session}\n\n"
            f"--- stdout ---\n{out}\n\n--- stderr ---\n{err}\n")
        return {"action": "agent_ran", "model": self.model, "returncode": rc,
                "cost_usd": round(cost, 6), "tokens": tokens,
                "infra_error": infra_error,
                "timed_out": timed_out, "duration_s": duration,
                "session": session, "said": " ".join(texts)[-400:]}
