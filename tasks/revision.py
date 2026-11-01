"""The one hardening revision permitted by the preregistration.

Why these exist: every tier-3 task in ``tasks.py`` is a single ``append`` to one
module. A worker does not have to read existing code, find a call site, or keep
an invariant -- it writes a self-contained class and is done. That is the shape
that saturated in the pre-check, so the revision changes the shape, not the
subject: each task here requires edits at several sites that must agree, and
several require changing a constructor whose other callers must keep working.

Scope note: this is a task-set revision, not a difficulty dial. It is applied
once. If these also saturate, saturation is the finding.
"""

from tasks import TASKS

REVISION = [
    # ---------------- R3-01: aliases across resolution and help ----------------
    dict(
        id="R3-01", tier=3, cls="feature", source="n/a",
        spec=(
            "Add an aliases parameter to Command: a sequence of alternative names "
            "a group accepts for that command. Both the canonical name and every "
            "alias must run the command identically. The group's help must list "
            "each command once, under its canonical name, with aliases shown in "
            "parentheses after it (e.g. 'build (b)'); an alias must not create a "
            "separate row. Command.aliases defaults to an empty tuple. Unknown "
            "names still raise NoSuchCommand."
        ),
        seed=None,
        reference=[
            dict(file="src/click/core.py", fn="class Command:",
                 old="        deprecated: bool | str = False,\n    ) -> None:",
                 new="        deprecated: bool | str = False,\n"
                     "        aliases: cabc.Sequence[str] | None = None,\n"
                     "    ) -> None:"),
            dict(file="src/click/core.py", fn="class Command:",
                 old="        self.hidden = hidden\n        self.deprecated = deprecated",
                 new="        self.hidden = hidden\n        self.deprecated = deprecated\n"
                     "        self.aliases: tuple[str, ...] = tuple(aliases or ())"),
            dict(file="src/click/core.py", fn="class Group(Command):",
                 old='        return self.commands.get(cmd_name)',
                 new="        cmd = self.commands.get(cmd_name)\n\n"
                     "        if cmd is None:\n"
                     "            for candidate in self.commands.values():\n"
                     "                if cmd_name in candidate.aliases:\n"
                     "                    return candidate\n\n"
                     "        return cmd"),
            dict(file="src/click/core.py", fn="class Group(Command):",
                 old="            for subcommand, cmd in commands:\n"
                     "                help = cmd.get_short_help_str(limit)\n"
                     "                rows.append((subcommand, help))",
                 new="            for subcommand, cmd in commands:\n"
                     "                help = cmd.get_short_help_str(limit)\n"
                     "                if cmd.aliases:\n"
                     "                    subcommand = f\"{subcommand} ({', '.join(cmd.aliases)})\"\n"
                     "                rows.append((subcommand, help))"),
        ],
        oracle="""
import click
from click.testing import CliRunner

@click.group()
def cli():
    pass

@cli.command(aliases=["b"])
def build():
    click.echo("built")

@cli.command()
def clean():
    click.echo("cleaned")

def test_alias_runs():
    result = CliRunner().invoke(cli, ["b"])
    assert result.exit_code == 0, result.output
    assert result.output == "built\\n"

def test_canonical_still_runs():
    assert CliRunner().invoke(cli, ["build"]).output == "built\\n"

def test_help_lists_command_once_with_alias():
    out = CliRunner().invoke(cli, ["--help"]).output
    assert "build (b)" in out
    assert out.count("build") == 1

def test_no_aliases_by_default():
    assert cli.commands["clean"].aliases == ()

def test_unknown_command_still_errors():
    assert CliRunner().invoke(cli, ["nope"]).exit_code == 2
""",
    ),

    # ---------------- R3-02: an Examples section in help ----------------
    dict(
        id="R3-02", tier=3, cls="feature", source="n/a",
        spec=(
            "Add an examples parameter to Command: a sequence of (invocation, "
            "description) pairs rendered under an 'Examples:' section of --help. "
            "The section is written as a definition list (invocation, then its "
            "description) and appears after the options and before the epilog. A "
            "command with no examples must not show the heading at all. Text must "
            "be rendered literally: no percent- or brace-interpolation."
        ),
        seed=None,
        reference=[
            dict(file="src/click/core.py", fn="class Command:",
                 old="        deprecated: bool | str = False,\n    ) -> None:",
                 new="        deprecated: bool | str = False,\n"
                     "        examples: cabc.Sequence[tuple[str, str]] | None = None,\n"
                     "    ) -> None:"),
            dict(file="src/click/core.py", fn="class Command:",
                 old="        self.hidden = hidden\n        self.deprecated = deprecated",
                 new="        self.hidden = hidden\n        self.deprecated = deprecated\n"
                     "        self.examples: list[tuple[str, str]] = list(examples or ())"),
            dict(file="src/click/core.py", fn="class Command:",
                 old="        self.format_options(ctx, formatter)\n"
                     "        self.format_epilog(ctx, formatter)",
                 new="        self.format_options(ctx, formatter)\n"
                     "        self.format_examples(ctx, formatter)\n"
                     "        self.format_epilog(ctx, formatter)"),
            dict(file="src/click/core.py", fn="class Command:",
                 old="    def format_help_text(self, ctx: Context, formatter: HelpFormatter) -> None:",
                 new="    def format_examples(self, ctx: Context, formatter: HelpFormatter) -> None:\n"
                     "        if not self.examples:\n"
                     "            return\n\n"
                     "        with formatter.section(_(\"Examples\")):\n"
                     "            formatter.write_dl(list(self.examples))\n\n"
                     "    def format_help_text(self, ctx: Context, formatter: HelpFormatter) -> None:"),
        ],
        oracle="""
import click
from click.testing import CliRunner

@click.command(
    examples=[("mycli --fast", "skip the checks"), ("mycli --safe", "check first")],
    epilog="See the docs.",
)
def mycli():
    pass

def test_examples_rendered():
    out = CliRunner().invoke(mycli, ["--help"]).output
    assert "Examples:" in out
    assert "mycli --fast" in out
    assert "skip the checks" in out

def test_examples_after_options_before_epilog():
    out = CliRunner().invoke(mycli, ["--help"]).output
    assert out.index("Options:") < out.index("Examples:") < out.index("See the docs.")

def test_no_examples_no_heading():
    @click.command()
    def bare():
        pass

    assert "Examples:" not in CliRunner().invoke(bare, ["--help"]).output

def test_text_not_interpolated():
    @click.command(examples=[("x {0} %s", "literal {0} %s")])
    def other():
        pass

    out = CliRunner().invoke(other, ["--help"]).output
    assert "literal {0} %s" in out
""",
    ),

    # ---------------- R3-03: splitting multi-value parameters ----------------
    dict(
        id="R3-03", tier=3, cls="feature", source="n/a",
        spec=(
            "Add a split parameter to Parameter (and therefore to Option and "
            "Argument): when set to a separator string, every incoming string is "
            "divided on that separator before type conversion, but only for "
            "parameters that accept several values (multiple=True or nargs != 1). "
            "Empty segments are dropped. With split unset, behaviour is unchanged. "
            "The split pieces must be type-converted as usual, so split and type "
            "compose."
        ),
        seed=None,
        reference=[
            dict(file="src/click/core.py", fn="class Parameter(ABC):",
                 old="        deprecated: bool | str = False,\n    ) -> None:\n"
                     "        self.name, self.opts, self.secondary_opts = self._parse_decls(",
                 new="        deprecated: bool | str = False,\n"
                     "        split: str | None = None,\n"
                     "    ) -> None:\n"
                     "        self.name, self.opts, self.secondary_opts = self._parse_decls("),
            dict(file="src/click/core.py", fn="class Parameter(ABC):",
                 old="        self.nargs = nargs\n        self.multiple = multiple",
                 new="        self.nargs = nargs\n        self.multiple = multiple\n"
                     "        self.split = split"),
            dict(file="src/click/core.py", fn="class Parameter(ABC):",
                 old="        def check_iter(value: t.Any) -> cabc.Iterator[t.Any]:",
                 new="        if self.split is not None and (self.multiple or self.nargs != 1):\n"
                     "            items = [value] if isinstance(value, str) else list(value)\n"
                     "            value = [\n"
                     "                part\n"
                     "                for item in items\n"
                     "                for part in str(item).split(self.split)\n"
                     "                if part != \"\"\n"
                     "            ]\n\n"
                     "        def check_iter(value: t.Any) -> cabc.Iterator[t.Any]:"),
        ],
        oracle="""
import click
from click.testing import CliRunner

def test_argument_split_with_conversion():
    @click.command()
    @click.argument("nums", nargs=-1, type=int, split=",")
    def cli(nums):
        click.echo("|".join(str(n) for n in nums))

    assert CliRunner().invoke(cli, ["1,2", "3"]).output == "1|2|3\\n"

def test_option_multiple_split():
    @click.command()
    @click.option("--tag", multiple=True, split=",")
    def cli(tag):
        click.echo("|".join(tag))

    assert CliRunner().invoke(cli, ["--tag", "a,b", "--tag", "c"]).output == "a|b|c\\n"

def test_empty_segments_dropped():
    @click.command()
    @click.argument("xs", nargs=-1, split=",")
    def cli(xs):
        click.echo("|".join(xs))

    assert CliRunner().invoke(cli, [",1,,2,"]).output == "1|2\\n"

def test_default_unchanged():
    @click.command()
    @click.argument("xs", nargs=-1)
    def cli(xs):
        click.echo("|".join(xs))

    assert CliRunner().invoke(cli, ["1,2"]).output == "1,2\\n"
""",
    ),

    # ---------------- R3-04: a Duration type -----------------
    dict(
        id="R3-04", tier=3, cls="feature", source="n/a",
        spec=(
            "Add click.types.Duration and export it as click.DURATION. It parses a "
            "duration written as digits followed by h, m or s, in that order, with "
            "any subset of the three (e.g. '90s', '2m30s', '1h2m3s') and returns "
            "whole seconds. A bare number with no unit, an unknown unit, a missing "
            "number, a negative value and out-of-order units ('1s1h') must all fail "
            "with BadParameter. Its name is 'duration'."
        ),
        seed=None,
        reference=[
            dict(file="src/click/types.py", append='''

class Duration(ParamType):
    """A duration written as digits and ``h``, ``m`` or ``s``, in that order."""

    name = "duration"
    _units = {"h": 3600, "m": 60, "s": 1}

    def convert(self, value, param, ctx):
        if not isinstance(value, str) or not value.strip():
            self.fail(f"{value!r} is not a valid duration.", param, ctx)

        total = 0
        seen = []
        number = ""

        for char in value.strip():
            if char.isdigit():
                number += char
                continue

            if char not in self._units or not number:
                self.fail(f"{value!r} is not a valid duration.", param, ctx)

            unit = self._units[char]

            if seen and unit >= seen[-1]:
                self.fail(f"{value!r} is not a valid duration.", param, ctx)

            seen.append(unit)
            total += int(number) * unit
            number = ""

        if number:
            self.fail(f"{value!r} is not a valid duration.", param, ctx)

        return total


DURATION = Duration()
'''),
            dict(file="src/click/__init__.py", fn="from .types import BOOL as BOOL",
                 old="from .types import DateTime as DateTime\n",
                 new="from .types import DateTime as DateTime\n"
                     "from .types import DURATION as DURATION\n"
                     "from .types import Duration as Duration\n"),
        ],
        oracle="""
import click
import pytest
from click.types import Duration

@pytest.mark.parametrize(
    ("text", "seconds"),
    [("90s", 90), ("2m30s", 150), ("1h", 3600), ("1h2m3s", 3723)],
)
def test_parsed(text, seconds):
    assert Duration().convert(text, None, None) == seconds

@pytest.mark.parametrize("bad", ["", "10", "10x", "m10", "-5s", "1s1h"])
def test_rejected(bad):
    with pytest.raises(click.BadParameter):
        Duration().convert(bad, None, None)

def test_exported():
    assert click.DURATION.name == "duration"
    assert click.DURATION.convert("1m", None, None) == 60
""",
    ),
]


#: The task list the sweep runs: tiers 1 and 2 unchanged, tier 3 replaced by the
#: hardening revision. The original tier-3 tasks stay in ``tasks.py`` as the
#: ceiling control -- they are known to be solved 12/12 at G0 and are excluded
#: from the sweep, not deleted.
SWEEP = [t for t in TASKS if t["tier"] != 3] + REVISION
