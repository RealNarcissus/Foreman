"""The twelve pilot tasks.

Each entry is a specification plus a machine-applicable seed (the defect) or
reference (the feature). Verification is `tools/verify_tasks.py`; nothing here
counts until it passes.

Design note: security-class tasks are expected NOT to fail click's own suite.
That is not a defect in the task, it is the reason G2 exists. Their tier still
reflects difficulty; their class reflects which gate is being tested.
"""

TASKS = [
    # ---------------- tier 1: single-file logic mutations ----------------
    dict(
        id="T1-01", tier=1, cls="logic", source="n/a",
        spec="echo() must still write a trailing newline when the message is empty.",
        seed=dict(file="src/click/utils.py", fn="def echo(",
                  old="    if nl:", new="    if nl and message:"),
        oracle="""
import click
from click.testing import CliRunner

@click.command()
def cli():
    click.echo("")

def test_empty_message_gets_newline():
    assert CliRunner().invoke(cli).output == "\\n"
""",
    ),
    dict(
        id="T1-02", tier=1, cls="logic", source="n/a",
        spec="join_options() must separate option names with a comma and a space, shortest prefix first.",
        seed=dict(file="src/click/formatting.py", fn="def join_options(",
                  old='    return ", ".join(x[1] for x in rv), any_prefix_is_slash',
                  new='    return " ".join(x[1] for x in rv), any_prefix_is_slash'),
        oracle="""
from click.formatting import join_options
def test_joined_with_comma():
    assert join_options(["--foo", "-f"])[0] == "-f, --foo"
""",
    ),
    dict(
        id="T1-03", tier=1, cls="logic", source="n/a",
        spec="BOOL must reject values it does not recognise instead of treating them as false.",
        seed=dict(file="src/click/types.py", fn="class BoolParamType",
                  old="        if normalized is None:",
                  new="        if not normalized:"),
        oracle="""
import click, pytest
from click.types import BoolParamType
@pytest.mark.parametrize("bad", ["yes please", "2", "nope"])
def test_rejects_unknown(bad):
    with pytest.raises(click.BadParameter):
        BoolParamType().convert(bad, None, None)

@pytest.mark.parametrize("falsey", ["false", "no", "0", "off"])
def test_accepts_falsey(falsey):
    assert BoolParamType().convert(falsey, None, None) is False
""",
    ),
    dict(
        id="T1-04", tier=1, cls="security", source="library parameter (known-blind control)",
        gate_expectation="fire",
        spec="Launching a URL must pass it to the helper as a single argument, never as part of a shell command.",
        seed=dict(file="src/click/_termui_impl.py", fn="def open_url(",
                  old='        c = subprocess.Popen(["xdg-open", url])',
                  new='        c = subprocess.Popen(f"xdg-open {url}", shell=True)'),
        oracle="""
import subprocess
from click._termui_impl import open_url
def test_url_not_shelled(monkeypatch):
    seen = {}
    def fake(args, **k):
        seen["args"] = args; seen.update(k)
        class C:
            def wait(self): return 0
        return C()
    monkeypatch.setattr(subprocess, "Popen", fake)
    open_url("https://example.com")
    assert not seen.get("shell", False), "url must not be interpolated into a shell command"
""",
    ),
    # ---------------- tier 2: cross-cutting logic + security ----------------
    dict(
        id="T2-01", tier=2, cls="logic", source="n/a",
        spec="An option's environment variable takes precedence over the automatic prefix, including when its value is empty.",
        seed=dict(file="src/click/core.py", fn="def resolve_envvar_value(self, ctx: Context) -> str | None:", nth=1,
                  old="            rv = os.environ.get(envvar)\n\n            if rv:",
                  new="            rv = os.environ.get(envvar)\n\n            if rv is not None:"),
        oracle="""
import click
from click.testing import CliRunner

@click.command()
@click.option("--name", default="default-val")
def cli(name):
    click.echo(repr(name))

def test_empty_autoenv_falls_back_to_default():
    r = CliRunner().invoke(cli, env={"CLI_NAME": ""}, auto_envvar_prefix="CLI")
    assert r.output.strip() == "'default-val'"
""",
    ),
    dict(
        id="T2-02", tier=2, cls="logic", source="n/a",
        spec="A parameter with several environment variables uses the first one that is set and non-empty.",
        seed=dict(file="src/click/core.py", fn="def resolve_envvar_value(self, ctx: Context) -> str | None:",
                  old="            rv = os.environ.get(self.envvar)\n\n            if rv:",
                  new="            rv = os.environ.get(self.envvar)\n\n            if rv is not None:"),
        oracle="""
import click
from click.testing import CliRunner

@click.command()
@click.option("--name", envvar="EMPTY_ONE", default="default-val")
def cli(name):
    click.echo(repr(name))

def test_empty_envvar_uses_default():
    r = CliRunner().invoke(cli, env={"EMPTY_ONE": ""})
    assert r.output.strip() == "'default-val'"
""",
    ),
    dict(
        id="T2-S1", tier=2, cls="security", source="EDITOR",
        gate_expectation="fire",
        spec="Opening files in the user's editor must not interpret shell metacharacters from the EDITOR variable.",
        seed=dict(file="src/click/_termui_impl.py", fn="    def edit_files(",
                  old="            c = subprocess.Popen(\n                args=shlex.split(editor) + list(filenames),\n                env=environ,\n            )",
                  new="            c = subprocess.Popen(\n                f\"{editor} {' '.join(str(f) for f in filenames)}\",\n                shell=True,\n                env=environ,\n            )"),
        oracle="""
import subprocess, click
from click._termui_impl import Editor
def test_editor_does_not_use_shell(monkeypatch):
    seen = {}
    def fake(*a, **k):
        seen.update(k); seen["args"] = a
        class C:  # minimal Popen stand-in
            def wait(self): return 0
        return C()
    monkeypatch.setattr(subprocess, "Popen", fake)
    Editor(editor="vi").edit_files(["f.txt"])
    assert not seen.get("shell", False), "editor must not be run through a shell"
""",
    ),
    dict(
        id="T2-S2", tier=2, cls="security", source="PAGER",
        gate_expectation="fire",
        spec="The pager must never be run through a shell, whatever PAGER contains.",
        seed=dict(file="src/click/_termui_impl.py", fn="def _tempfilepager(",
                  old="        subprocess.call([str(cmd_path), *cmd_params, f.name])",
                  new="        pager = os.environ.get(\"PAGER\", \"more\")\n        subprocess.call(f\"{pager} {f.name}\", shell=True)"),
        oracle="""
import subprocess
from click._termui_impl import _tempfilepager
def test_pager_does_not_use_shell(monkeypatch):
    seen = {}
    def fake(args, **k):
        seen["args"] = args; seen.update(k); return 0
    monkeypatch.setattr(subprocess, "call", fake)
    with _tempfilepager(["more"], "less", True):
        pass
    assert not seen.get("shell", False), "pager must not be run through a shell"
""",
    ),
    # ---------------- tier 3: features ----------------
    dict(
        id="T3-01", tier=3, cls="feature", source="n/a",
        spec="Add PositiveInt, a ParamType accepting only integers greater than zero and failing otherwise.",
        seed=None,
        reference=dict(file="src/click/types.py", append='''

class PositiveInt(IntParamType):
    """An integer that must be greater than zero."""

    name = "positive integer"

    def convert(self, value, param, ctx):
        rv = super().convert(value, param, ctx)
        if rv <= 0:
            self.fail(f"{rv} is not a positive integer.", param, ctx)
        return rv
'''),
        oracle="""
import click, pytest
def test_positive_ok():
    assert click.types.PositiveInt().convert("3", None, None) == 3
@pytest.mark.parametrize("bad", ["0", "-1"])
def test_positive_rejects(bad):
    with pytest.raises(click.BadParameter):
        click.types.PositiveInt().convert(bad, None, None)
""",
    ),
    dict(
        id="T3-02", tier=3, cls="feature", source="n/a",
        spec="Add Percent, a ParamType accepting 0-100 inclusive and exposing the value as given, rejecting anything outside that range.",
        seed=None,
        reference=dict(file="src/click/types.py", append='''

class Percent(IntParamType):
    """An integer percentage from 0 to 100 inclusive."""

    name = "percent"

    def convert(self, value, param, ctx):
        rv = super().convert(value, param, ctx)
        if not 0 <= rv <= 100:
            self.fail(f"{rv} is not between 0 and 100.", param, ctx)
        return rv
'''),
        oracle="""
import click, pytest
def test_percent_bounds_ok():
    t = click.types.Percent()
    assert t.convert("0", None, None) == 0
    assert t.convert("100", None, None) == 100
@pytest.mark.parametrize("bad", ["-1", "101"])
def test_percent_rejects(bad):
    with pytest.raises(click.BadParameter):
        click.types.Percent().convert(bad, None, None)
""",
    ),
    dict(
        id="T3-03", tier=3, cls="feature", source="n/a",
        spec="Add truncate_middle(text, width) to click.utils, keeping the start and end of a long string and inserting an ellipsis.",
        seed=None,
        reference=dict(file="src/click/utils.py", append='''

def truncate_middle(text: str, width: int) -> str:
    """Shorten ``text`` to ``width`` characters, keeping both ends."""
    if width < 5:
        return text[:width]
    if len(text) <= width:
        return text
    keep = width - 3
    head = keep // 2 + keep % 2
    tail = keep // 2
    return f"{text[:head]}...{text[-tail:] if tail else ''}"
'''),
        oracle="""
from click.utils import truncate_middle
def test_short_unchanged():
    assert truncate_middle("abc", 5) == "abc"
def test_long_truncated():
    out = truncate_middle("abcdefghij", 7)
    assert len(out) == 7 and out.startswith("ab") and out.endswith("ij") and "..." in out
""",
    ),
    dict(
        id="T3-04", tier=3, cls="feature", source="n/a",
        spec="Add HexColor, a ParamType turning #rrggbb into an (r, g, b) tuple and rejecting malformed input.",
        seed=None,
        reference=dict(file="src/click/types.py", append='''

class HexColor(ParamType):
    """A colour written as #rrggbb, converted to an (r, g, b) tuple."""

    name = "hex color"

    def convert(self, value, param, ctx):
        if not isinstance(value, str) or len(value) != 7 or not value.startswith("#"):
            self.fail(f"{value!r} is not a #rrggbb colour.", param, ctx)
        try:
            return tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))
        except ValueError:
            self.fail(f"{value!r} is not a #rrggbb colour.", param, ctx)
'''),
        oracle="""
import click, pytest
def test_parses_colour():
    assert click.types.HexColor().convert("#ff8000", None, None) == (255, 128, 0)
@pytest.mark.parametrize("bad", ["ff8000", "#ff80", "#gggggg"])
def test_rejects(bad):
    with pytest.raises(click.BadParameter):
        click.types.HexColor().convert(bad, None, None)
""",
    ),
]
