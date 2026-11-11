"""Exact, reviewable local energy-query intent.

A deliberately small allowlist, not a model planner or implicit tool grant.
Unknown/mixed instructions stay in the normal verified-memory chat path.
"""
from __future__ import annotations

import re
import unicodedata

INTENTS = frozenset({
    # ES
    "energia", "energia del rack", "estado de la energia",
    "estado de la energia del rack", "como esta la energia",
    "como esta la energia del rack", "cuanto consume el rack",
    "cuantos vatios consume el rack", "cuanto consume el enchufe",
    "cuanta bateria queda", "cuanta bateria solar queda",
    "estado de la bateria", "estado de la bateria solar",
    "estado del solar", "energia solar del rack",
    "que energia nos queda", "cuanta energia nos queda",
    # EN
    "rack energy", "rack energy status", "energy status",
    "how much power does the rack use", "what is the rack power",
    "rack power", "what is the energy status",
    "battery status", "solar battery status", "solar energy status",
    # PT
    "energia do rack", "estado da energia do rack",
    "quanta energia resta", "estado da bateria solar",
    "quanto consome o rack",
})


def es_consulta(text):
    if type(text) is not str or not 0 < len(text) <= 600:
        return False
    norm = unicodedata.normalize("NFKD", text.casefold())
    norm = "".join(c for c in norm if not unicodedata.combining(c))
    # Only surrounding question punctuation; no commands, multiple turns,
    # injected instructions, extra tokens, or free-text approximate matching.
    norm = norm.strip().strip("¿?¡! .")
    norm = re.sub(r"\s+", " ", norm)
    return norm in INTENTS
