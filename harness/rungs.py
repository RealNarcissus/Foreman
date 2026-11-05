"""The rung ladder as data, so the treatment is a file rather than a branch in code."""
import json
import pathlib

from .config import ROOT

DIR = ROOT / "configs" / "rungs"


def load(rung_id: str) -> dict:
    data = json.loads((DIR / f"{rung_id}.json").read_text())
    # A rung that requires the reviewer must name one. G4 inherits G3's frozen
    # reviewer rather than copying its hash, so the two cannot drift apart; a
    # missing reference fails loudly instead of reaching the gate as None.
    if "ai_review" in data.get("requires", []) and "reviewer" not in data:
        ref = data.get("reviewer_ref")
        if not ref:
            raise KeyError(f"{rung_id} requires ai_review but defines no reviewer")
        data["reviewer"] = load(ref)["reviewer"]
    return data


def all_rungs() -> list[str]:
    return [p.stem for p in sorted(DIR.glob("G*.json"))]
