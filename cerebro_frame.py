"""N4 · project the first frame (app side). The model catalogue becomes Acho frames, byte for byte the same
as the web's public/game/brain_frame.js + state_frames.js, so one sha256 names the same frame on both sides.

Pure: no network, no clock, no randomness. Live residency is never claimed: it stays NO_DATA, with the
same cause the console already declares (consola.CAUSA_RESIDENTE) kept beside it, not inside the frame.
"""
import hashlib
import json
import re

LIMITE_BYTES = 1024           # a frame is a syllable: under 1,024 UTF-8 bytes (docs/acho-language.md §1)
RIM = [[58, 66], [36, 94], [92, 72]]
_ID = re.compile(r"^[a-z0-9-]{1,40}$")


def canonical(value):
    """The shared canon: sorted keys, compact, every non-printable or non-ASCII escaped (web canon.js)."""
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("ascii")


def huella(frame):
    """sha256 hex of the canonical bytes; the same hex as canon.huella(frame) in the web."""
    return hashlib.sha256(canonical(frame)).hexdigest()


def _state_frame(ident, sentence):
    return {"v": "preceptoros.acho/1", "id": ident, "t": 0, "cv": [320, 96],
            "atoms": [{"k": ident, "r": sentence,
                       "i": [{"o": "ribbon", "pts": [list(p) for p in RIM], "closed": True,
                              "f": "paper", "s": "ink", "lw": 3}]}],
            "bands": ["paper", "ink", "cyan"], "change": [sentence],
            "sound": "NO_DATA: no waves declared for this state",
            "soundCause": "no harmonic table in this state; nothing is invented"}


def valida(frame):
    problemas = []
    n = len(json.dumps(frame, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    if n >= LIMITE_BYTES:
        problemas.append("frame of %d bytes, limit %d" % (n, LIMITE_BYTES))
    for i, a in enumerate(frame.get("atoms") or []):
        if not isinstance(a, dict) or not isinstance(a.get("r"), str) or not a["r"].strip():
            problemas.append("atom %d has no sentence (r)" % i)
    if not isinstance(frame.get("sound"), str) or not frame["sound"]:
        problemas.append("sound not declared")
    return problemas


def _flag(value, yes, no):
    return (yes if value else no) if isinstance(value, bool) else "NO_DATA (field absent)"


def project(catalog):
    """{"ok": True, "frames": [...]} sorted by id, or {"ok": False, "cause": ...}. Mirrors brain_frame.project."""
    if not isinstance(catalog, dict) or catalog.get("esquema") != 1 or not isinstance(catalog.get("cerebros"), list):
        return {"ok": False, "cause": "catalogue schema or model list is unavailable"}
    seen, frames = set(), []
    for model in catalog["cerebros"]:
        ident = model.get("id") if isinstance(model, dict) else None
        if not isinstance(ident, str) or not _ID.match(ident) or ident in seen:
            return {"ok": False, "cause": "model id is missing, invalid or repeated"}
        seen.add(ident)
        sentence = ("model " + ident + " · door " + _flag(model.get("puerta"), "yes", "no") +
                    " · signature " + _flag(model.get("firmado"), "signed", "unsigned") +
                    " · base NO_DATA (not separately declared) · adapter NO_DATA (not declared)"
                    " · permissions NO_DATA (not declared) · requires signature NO_DATA (not declared)"
                    " · residency NO_DATA (catalogue has no live residency measure)")
        frame = _state_frame("brain-" + ident, sentence)
        frame["seal"] = "NO_DATA"
        frame["atoms"][0]["k"] = "NO_DATA"
        frame["change"] = ["residency"]
        frame["bands"] = ["NO_DATA.base", "NO_DATA.contorno"]
        frame["atoms"][0]["i"][0]["f"] = "NO_DATA.base"
        frame["atoms"][0]["i"][0]["s"] = "NO_DATA.contorno"
        frame["sound"] = "NO_DATA: model frames declare no measured harmonic table"
        frame["soundCause"] = "no harmonic table in this catalogue"
        if valida(frame):
            return {"ok": False, "cause": "model frame breaks the Acho frame law"}
        frames.append(frame)
    frames.sort(key=lambda f: f["id"])
    return {"ok": True, "frames": frames}
