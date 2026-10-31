"""Process isolation for the worker.

bwrap gives the agent a mount namespace containing only its worktree, a private
HOME and the toolchain. The project directory is not mounted at all, so reading
an oracle or another run is impossible rather than merely detectable.
"""
import os
import pathlib
import shutil

HOMES = pathlib.Path("/tmp/foreman-home")


def available() -> bool:
    return shutil.which("bwrap") is not None and os.environ.get("FOREMAN_SANDBOX", "1") != "0"


def home_for(run_id: str) -> pathlib.Path:
    home = HOMES / run_id
    (home / ".config" / "opencode").mkdir(parents=True, exist_ok=True)
    (home / ".local" / "share" / "opencode").mkdir(parents=True, exist_ok=True)
    real = pathlib.Path.home()
    for src, dst in (
        (real / ".local/share/opencode/auth.json", home / ".local/share/opencode/auth.json"),
        (real / ".config/opencode/opencode.json", home / ".config/opencode/opencode.json"),
    ):
        if src.exists():
            shutil.copyfile(src, dst)
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
