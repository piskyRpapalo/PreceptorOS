"""lab_avisos.py · Lab notices: registry `evidencia` events as acho/1 frames that age.

Loop 8 of the F0 plan (odd/tasks/f0-one-loop-20261107.md): a signed proof lands in the
single registry as an `evidencia` event; the Lab shows it as a notice. This module only
READS (through `lab.eventos`, which opens the registry with mode=ro) and renders. It never
writes, never acts and never touches the network: reading is not executing, so a notice
carries no actions.

Each notice is a frame under 1,024 UTF-8 bytes, mirroring the web `state_frames.js`
shape, plus `seal`, `since` and `cause`. The seal ages honestly:
  age <= TTL_S       -> LIVE
  age <= 4 * TTL_S   -> STALE
  older              -> NO_DATA, cause "aged_out"
  unreadable/future  -> NO_DATA, cause "timestamp_invalid"
The clock is injected (`ahora`); there is no clock inside.
"""
from __future__ import annotations

import datetime as _dt
import json

import lab as _lab

# decision mia (sin firma): one hour of freshness. The registry heartbeat cadence is
# minutes, a benchmark receipt is published per run; one hour keeps a run LIVE for its
# session and lets it fall to STALE, then NO_DATA, without anyone deleting it.
TTL_S = 3600
STALE_FACTOR = 4
LIMITE_BYTES = 1024
TIPO = "evidencia"
SOUND = "NO_DATA: no waves declared for this notice"
SOUND_CAUSE = "no harmonic table; nothing is invented"


def tamano(frame):
    """UTF-8 size of the compact JSON frame."""
    return len(json.dumps(frame, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def _sello(t, ahora, ttl_s):
    f = _lab._fecha(t)
    if f is None:
        return "NO_DATA", "timestamp_invalid"
    edad = (ahora - f).total_seconds()
    if edad < 0:
        return "NO_DATA", "timestamp_invalid"
    if edad <= ttl_s:
        return "LIVE", ""
    if edad <= STALE_FACTOR * ttl_s:
        return "STALE", ""
    return "NO_DATA", "aged_out"


def _frame(ident, frase, since, seal, cause):
    return {"v": "preceptoros.acho/1", "id": ident, "t": 0, "cv": [320, 96],
            "atoms": [{"k": ident, "r": frase, "i": []}],
            "bands": ["paper", "ink", "cyan"], "change": [frase],
            "sound": SOUND, "soundCause": SOUND_CAUSE,
            "seal": seal, "since": since, "cause": cause}


def aviso(evento, ahora, ttl_s=TTL_S):
    """One registry event -> one notice frame (< 1,024 B), or a NO_DATA notice."""
    ident = f"{TIPO}-{int(evento.get('n') or 0)}"
    since = str(evento.get("t") or "")[:64]
    seal, cause = _sello(since, ahora, ttl_s)
    frase = str(evento.get("texto") or "").strip() or f"{TIPO} without a readable sentence"
    frame = _frame(ident, frase, since, seal, cause)
    # Trim the sentence by characters until the frame fits; the sentence appears twice
    # (atom and change), so each removed character saves its bytes twice.
    while tamano(frame) >= LIMITE_BYTES and len(frase) > 1:
        exceso = tamano(frame) - LIMITE_BYTES + 1
        frase = frase[:max(1, len(frase) - max(1, exceso // 2))].rstrip() or frase[:1]
        frame = _frame(ident, frase + "…", since, seal, cause)
        if tamano(frame) < LIMITE_BYTES:
            return frame
    if tamano(frame) >= LIMITE_BYTES:
        return _frame(ident, f"{TIPO} too large to show", since, "NO_DATA", "frame_too_large")
    return frame


def avisos(base, ahora, ttl_s=TTL_S):
    """Registry evidence events -> (state, notices). Read-only; NO_DATA keeps its cause."""
    if not isinstance(ahora, _dt.datetime) or ahora.tzinfo is None:
        return _lab.nd("clock_invalid"), []
    if type(ttl_s) is not int or ttl_s <= 0:
        return _lab.nd("ttl_invalid"), []
    estado, eventos = _lab.eventos(base)
    if estado.get("estado") != "MEDIDO":
        return estado, []
    lista = [aviso(e, ahora, ttl_s) for e in eventos if e.get("tipo") == TIPO]
    return {"estado": "MEDIDO", "avisos": len(lista), "modo": "solo lectura",
            "ttl_s": ttl_s}, lista
