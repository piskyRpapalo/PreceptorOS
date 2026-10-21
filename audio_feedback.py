"""Pure projection of orchestrator responses into the shared audio cue form."""
from __future__ import annotations

import math


_VERBS = {
    "DEPLOY_BUILDING": (0, "deploy", "Deploy"),
    "QUERY_STATE": (2, "state", "State"),
    "UPDATE_RAG": (4, "rag", "Sources"),
}
_STATES = {
    "MEASURED": (2, 20, 0.28, False, "measured"),
    "PROPOSED": (2, 35, 0.28, True, "proposed, waits a signature"),
    "STALE": (0.5, 60, 0.5, False, "stale"),
    "NO_DATA": (1.4, 180, 0.4, False, "NO_DATA"),
}
_PENTATONIC = (0, 2, 4, 7, 9)


def _round_hundred(value: float) -> float:
    return math.floor(value * 100 + 0.5) / 100


def _cause(value: object, state: str) -> str | None:
    cause = value[:120] if type(value) is str and value else None
    if state == "NO_DATA" and cause is None:
        return "cause not declared by the caller"
    return cause


def project(response: object) -> dict | None:
    """Return a deterministic cue descriptor, or None for an unknown route."""
    if type(response) is not dict:
        return None
    intent = response.get("intent")
    state = response.get("estado")
    if type(intent) is not str or intent not in _VERBS:
        return None
    if type(state) is not str or state not in _STATES:
        return None
    degree, verb, label = _VERBS[intent]
    ratio, index, duration, vibrato, state_label = _STATES[state]
    carrier = _round_hundred(220 * math.pow(2, _PENTATONIC[degree] / 12))
    cause = _cause(response.get("causa"), state)
    text = label + ": " + state_label + (" (" + cause + ")" if cause else "")
    return {
        "verbo": verb,
        "estado": state,
        "sonido": "INACTIVO",
        "sonido_causa": "sound is off until you turn it on",
        "motivo": {
            "portadora": carrier,
            "moduladora": _round_hundred(carrier * ratio),
            "indice": index,
            "dur": duration,
            "vibrato": vibrato,
        },
        "texto": text,
        "causa": cause,
    }
