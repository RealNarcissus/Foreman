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
