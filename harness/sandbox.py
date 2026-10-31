"""Process isolation for the worker.

bwrap gives the agent a mount namespace containing only its worktree, a private
HOME and the toolchain. The project directory is not mounted at all, so reading
an oracle or another run is impossible rather than merely detectable.
"""
import os
import pathlib
import shutil
import subprocess

HOMES = pathlib.Path("/tmp/foreman-home")


def available() -> bool:
    return shutil.which("bwrap") is not None and os.environ.get("FOREMAN_SANDBOX", "1") != "0"


def home_for(run_id: str) -> pathlib.Path:
    """A private HOME carrying only the credentials the agent needs.

    Credentials arrive through opencode's own `auth export`/`auth import`, not by
    copying the state directory: the state directory holds session transcripts,
    which would leak prior runs (and their task text) into the sandbox.
    """
    home = HOMES / run_id
    (home / ".config" / "opencode").mkdir(parents=True, exist_ok=True)
    (home / ".local" / "share" / "opencode").mkdir(parents=True, exist_ok=True)
    real = pathlib.Path.home()
    cfg = real / ".config/opencode/opencode.json"
    if cfg.exists():
        shutil.copyfile(cfg, home / ".config/opencode/opencode.json")
    export = pathlib.Path(os.environ.get(
        "FOREMAN_AUTH_EXPORT", real / ".foreman" / "auth-export.json"))
    if export.exists():
        env = dict(os.environ, HOME=str(home), XDG_DATA_HOME=str(home / ".local/share"))
        subprocess.run(["opencode", "auth", "import", "--standalone", str(export)],
                       env=env, capture_output=True, timeout=120)
    return home


def wrap(cmd: list[str], worktree: pathlib.Path, home: pathlib.Path) -> list[str]:
    real = pathlib.Path.home()
    binds = []
    for ro in ("/usr", "/bin", "/lib", "/lib64", "/etc"):
        if pathlib.Path(ro).exists():
            binds += ["--ro-bind", ro, ro]
    return ["bwrap", *binds,
            "--ro-bind", str(real / ".opencode"), "/opencode-bin",
            "--bind", str(home), "/home/agent",
            "--bind", str(worktree), "/work",
            "--chdir", "/work",
            "--tmpfs", "/tmp", "--proc", "/proc", "--dev", "/dev",
            "--unshare-pid",
            "--setenv", "HOME", "/home/agent",
            "--setenv", "PATH", "/opencode-bin/bin:/usr/bin:/bin",
            "--", *cmd]


def probe(worktree: pathlib.Path, home: pathlib.Path) -> dict:
    """Per-run evidence that the mount namespace is what we think it is.

    A one-off manual check is not enough: this runs before every run and its
    result is recorded, so a misconfigured sandbox cannot pass as clean.
    """
    if not available():
        return {"ran": False, "ok": False, "detail": "sandbox unavailable"}
    real = pathlib.Path.home()
    script = (
        "pwd; "
        f"if [ -e '{real}' ]; then echo HOSTHOME_VISIBLE; else echo HOSTHOME_ABSENT; fi; "
        "if [ -d /work/src/click ]; then echo WORKTREE_OK; else echo WORKTREE_MISSING; fi"
    )
    try:
        r = subprocess.run(wrap(["/bin/sh", "-c", script], worktree, home),
                           capture_output=True, text=True, timeout=120)
    except Exception as exc:
        return {"ran": True, "ok": False, "detail": f"{type(exc).__name__}: {exc}"}
    out = (r.stdout or "") + (r.stderr or "")
    ok = ("HOSTHOME_ABSENT" in out and "WORKTREE_OK" in out and "/work" in out)
    return {"ran": True, "ok": ok, "detail": out.strip()[:400]}
