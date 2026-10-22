"""Read-only projection of an explicit visual state into lexical fields."""
from collections.abc import Mapping
from typing import Any

from lexicon_state import LexiconState, measured, unavailable


_FRAME_FIELDS = ("id", "t", "sound", "motion", "atoms")
_ATOM_FIELDS = frozenset({"k", "i", "r"})
_ITEM_FIELDS = frozenset({"o", "tx", "x", "y", "r", "f", "as", "sz", "v", "max", "ch", "b", "causa"})


def _missing(value: Any) -> LexiconState | None:
    if not isinstance(value, Mapping):
        return unavailable("frame is not a mapping")
    absent = [name for name in _FRAME_FIELDS if name not in value]
    if absent:
        return unavailable("missing frame fields: " + ", ".join(absent))
    if not isinstance(value["atoms"], (list, tuple)):
        return unavailable("atoms is not an ordered list")
    for index, atom in enumerate(value["atoms"]):
        if not isinstance(atom, Mapping) or not {"k", "i"}.issubset(atom):
            return unavailable(f"atom {index} lacks k or i")
        if set(atom) - _ATOM_FIELDS or not isinstance(atom["i"], (list, tuple)):
            return unavailable(f"atom {index} has undeclared fields or invalid items")
        for item_index, item in enumerate(atom["i"]):
            if not isinstance(item, Mapping) or "o" not in item:
                return unavailable(f"item {index}.{item_index} lacks object type")
            if set(item) - _ITEM_FIELDS:
                return unavailable(f"item {index}.{item_index} has undeclared fields")
    for name in ("id", "t", "sound", "motion"):
        if not isinstance(value[name], str) or not value[name]:
            return unavailable(f"{name} is absent")
    return None


def project(frame: Any, status: str = "LIVE", cause: str | None = None) -> LexiconState:
    """Project only declared fields; missing measurements stay NO_DATA."""
    invalid = _missing(frame)
    if invalid is not None:
        return invalid
    if status in {"NO_DATA", "ERROR"}:
        return unavailable(cause or "frame state is " + status, status)
    if status != "LIVE":
        return unavailable("unsupported frame state: " + status)
    payload = {
        "id": frame["id"],
        "t": frame["t"],
        "sound": frame["sound"],
        "motion": frame["motion"],
        "n": len(frame["atoms"]),
        "a": [{"k": atom["k"],
               "i": [dict(item) for item in atom["i"]],
               **({"r": atom["r"]} if "r" in atom else {})}
              for atom in frame["atoms"]],
    }
    try:
        return measured(payload, status)
    except (TypeError, ValueError):
        return unavailable("frame contains unsupported JSON data")
