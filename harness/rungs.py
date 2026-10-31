"""The rung ladder as data, so the treatment is a file rather than a branch in code."""
import json
import pathlib

from .config import ROOT

DIR = ROOT / "configs" / "rungs"


def load(rung_id: str) -> dict:
    return json.loads((DIR / f"{rung_id}.json").read_text())


def all_rungs() -> list[str]:
    return [p.stem for p in sorted(DIR.glob("G*.json"))]
