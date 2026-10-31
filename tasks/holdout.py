"""Holdout tasks. Used ONLY for worker selection; excluded from every sweep.

They exist so the worker is not chosen on the tasks it will be measured against.
"""

HOLDOUT = [
    dict(
        id="H1", tier=1, cls="logic", source="n/a",
        spec="Option names are listed shortest prefix first, separated by a comma and a space.",
        seed=dict(file="src/click/formatting.py", fn="def join_options(",
                  old="    rv.sort(key=lambda x: x[0])\n",
                  new=""),
        oracle="""
from click.formatting import join_options
def test_shortest_first():
    assert join_options(["--foo", "-f"])[0] == "-f, --foo"
""",
    ),
    dict(
        id="H2", tier=3, cls="feature", source="n/a",
        spec="Add truncate_start(text, width) to click.utils, keeping the end of a long string and prefixing an ellipsis.",
        seed=None,
        reference=dict(file="src/click/utils.py", append='''

def truncate_start(text: str, width: int) -> str:
    """Shorten ``text`` to ``width`` characters, keeping its end."""
    if width < 4:
        return text[-width:]
    if len(text) <= width:
        return text
    return "..." + text[-(width - 3):]
'''),
        oracle="""
from click.utils import truncate_start
def test_short_unchanged():
    assert truncate_start("abc", 5) == "abc"
def test_keeps_end():
    out = truncate_start("abcdefghij", 7)
    assert len(out) == 7 and out.startswith("...") and out.endswith("hij")
""",
    ),
]
