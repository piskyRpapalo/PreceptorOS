"""Read model of the node's A2A boundary panel (the law A2A). Pure: reads two JSON files, never raises."""
import importlib.util
import json
from pathlib import Path

ESQUEMA = "preceptoros.politica-vista/1"
CANON = ["peaceful", "hostile", "cooperative", "closed", "open"]
RAIZ = Path(__file__).resolve().parent


def _no_data(causa):
    return {"state": "NO_DATA", "cause": causa}


def _validador(raiz):
    # Reuse the node policy validator (_read_policy) from mcp_thegame_server.py.
    # It reads politica_nodo.json next to itself, so load it from the root being read.
    ruta = raiz / "mcp_thegame_server.py"
    if not ruta.is_file():
        return None
    spec = importlib.util.spec_from_file_location("_politica_vista_validador", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _juego(raiz):
    try:
        raw = (raiz / "aiact_art14_game_policy.json").read_bytes()
    except OSError:
        return None, "game policy is unavailable"
    try:
        ca = json.loads(raw.decode("utf-8"))["conquista_a2a"]
        maquina, sin_firma = ca["maquina"], ca["sin_firma"]
        if not (isinstance(maquina, list) and all(isinstance(m, str) for m in maquina)
                and isinstance(sin_firma, str)):
            raise ValueError("bad machine")
    except (UnicodeDecodeError, ValueError, KeyError, TypeError):
        return None, "game policy has no valid conquista_a2a machine"
    return {"machine": maquina, "unsigned": sin_firma}, None


def _condicion(nombre, c):
    # A policy file DECLARES; it never measures. NO_DATA keeps the file's own cause; activo=false is OFF.
    if c.get("estado") == "NO_DATA":
        return {"id": nombre, "state": "NO_DATA", "cause": str(c.get("causa") or "condition declares NO_DATA")}
    if c.get("activo") is False:
        return {"id": nombre, "state": "OFF"}
    return {"id": nombre, "state": "DECLARED"}


def vista(raiz=None):
    raiz = RAIZ if raiz is None else Path(raiz).resolve()
    try:
        validador = _validador(raiz)
        if validador is None:
            return _no_data("node policy validator is unavailable")
        politica, causa = validador._read_policy()
        if politica is None:
            return _no_data(causa)
        juego, causa = _juego(raiz)
        if juego is None:
            return _no_data(causa)
        return {
            "esquema": ESQUEMA,
            "posture": {"state": "NO_DATA",
                        "cause": "no posture field in preceptoros.politica-nodo/1",
                        "canon": CANON},
            "conditions": [_condicion(k, v) for k, v in politica["condiciones"].items()],
            "caravans": {"state": "NO_DATA",
                         "cause": "no signed caravan contract; conquista_a2a requires signature",
                         "machine": juego["machine"], "unsigned": juego["unsigned"]},
            "signature": {"state": "NO_DATA", "cause": "policy file carries no owner signature"},
        }
    except Exception as exc:  # the panel must never raise
        return _no_data("policy view failed: " + type(exc).__name__)
