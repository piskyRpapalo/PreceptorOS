#!/usr/bin/env python3
"""A1 · el nodo PROPONE una jugada desde un vector compacto, por TUBERIA (plan de ronda 2026-10-11, P5).

sistema: MVP · solo biblioteca estandar (mas `node` para el motor de la web, fijado por sha256).

    python3 aiact_art14_node_decide.py < instantanea.json     # sale una atlas.accion/1 o NO_DATA

CONTRATO. Entra `atlas.instantanea/1` (el estado del juego en <1 KB: recursos, nucleo, grieta,
niveles; sin identidad, sin reloj). Sale UNA accion del enum validada por el propio motor, con la
huella del motor que decidio y `firma: null`: el nodo propone; firmar es de la persona (AI Act
art. 14, supervision humana). Hoy decide la REGLA FIJA (`atlas-piloto.js`); un modelo solo podra
sustituirla si le gana en el arnes y con la firma del Soberano (atlas_runner.py, `reemplaza: False`).

D68. Nada escucha en la red: el motor es un proceso hijo (`atlas/corre.mjs`) que habla por
entrada y salida estandar, y esta puerta tambien. La copia del motor es la de la web, fijada en
`atlas/MANIFIESTO.json`; si un fichero no casa, el motor no arranca: FALLO_INTEGRIDAD.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import atlas_runner as R

QUIEN = "regla fija (atlas-piloto.js)"


def decide(instantanea, motor=None):
    """Nunca lanza: OK con la accion y la huella, o NO_DATA/FALLO_INTEGRIDAD con su causa."""
    if not isinstance(instantanea, dict):
        return {"estado": "NO_DATA", "causa": "la entrada no es un objeto atlas.instantanea/1"}
    propio = motor is None
    try:
        mo = motor or R.Motor()
    except R.SinMotor as e:
        est = "FALLO_INTEGRIDAD" if "FALLO_INTEGRIDAD" in str(e) else "NO_DATA"
        return {"estado": est, "causa": str(e)}
    try:
        r = mo.orden(op="decide", instantanea=instantanea)
        man = json.loads((R.AQUI / "atlas" / "MANIFIESTO.json").read_text(encoding="utf-8"))
    finally:
        if propio:
            mo.cierra()
    if not r.get("ok"):
        return {"estado": r.get("estado", "NO_DATA"), "causa": r.get("motivo", "el motor no decidio")}
    return {"estado": "OK", "esquema": "atlas.accion/1", "accion": r["accion"], "quien": QUIEN, "firma": None,
            "motor": {"contenido_v": man["contenido_v"], "web_commit": man.get("web_commit"),
                      "piloto_sha256": man["ficheros"]["atlas-piloto.js"], "motor_sha256": man["ficheros"]["atlas-motor.js"]}}


POLITICA = R.AQUI / "aiact_art14_game_policy.json"


def politica(ruta=POLITICA):
    """La politica de juego del nodo, validada; None si falta o esta mal (fail-closed)."""
    try:
        p = json.loads(Path(ruta).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    ok = (isinstance(p, dict) and p.get("esquema") == "preceptoros.politica-juego/1" and p.get("capacidad") == "accion_de_juego"
          and isinstance(p.get("decide"), dict) and p["decide"].get("reemplaza") is False
          and isinstance(p.get("st"), dict) and isinstance(p["st"].get("max_bytes"), int) and p["st"]["max_bytes"] <= 150)
    return p if ok else None


def propone(instantanea, base=None, argv=None, ruta_politica=POLITICA):
    """La puerta completa: guardian (nivel) -> politica -> decision. Ante la duda, NO_DATA con causa."""
    import soberania as S
    if not S.verificar_permiso("accion_de_juego", base, argv=argv if argv is not None else []):
        return {"estado": "NO_DATA", "causa": S.causa("accion_de_juego", base, argv=argv if argv is not None else [])}
    pol = politica(ruta_politica)
    if pol is None:
        return {"estado": "NO_DATA", "causa": "sin politica de juego valida (aiact_art14_game_policy.json): no se propone nada"}
    r = decide(instantanea)
    if r.get("estado") == "OK":
        r["politica"] = pol["esquema"]
    return r


def main():
    try:
        ins = json.loads(sys.stdin.read() or "null")
    except ValueError:
        ins = None
    print(json.dumps(propone(ins, argv=sys.argv[1:]), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
