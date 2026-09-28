#!/usr/bin/env python3
"""¿Es este aparato una CUENTA NODO? La app lo lee de la cedula del rack, sin inventarlo.

sistema: MVP · solo biblioteca estandar.

    python3 nodo_app.py importar CEDULA.json [--db RUTA]   # guarda lo que dice la cedula
    python3 nodo_app.py estado [--db RUTA]                  # que nivel tiene este aparato

DE DONDE SALE. En el rack, `nodos.py cedula <nodo>` escribe `preceptoros.cedula-nodo/1`: el nodo,
su admin y cada dispositivo con su CLAVE PUBLICA y su estado (solicitado, linkeado, revocado). La
persona se la trae a este aparato. Aqui se calcula el codigo de vinculo de cada clave con
`soberano.codigo_de` -- el mismo que la web y que el onboarding, una sola derivacion -- y se busca
el del Soberano declarado en este aparato (`soberano.quien`).

LO QUE AFIRMA Y LO QUE NO.
  · El hash del cuerpo se comprueba: si la cedula se toco por el camino, FALLO_INTEGRIDAD.
  · La cedula NO va firmada (el rack no firma nada), asi que su AUTENTICIDAD es NO_DATA: es una
    declaracion del rack, y se dice asi. Verificar firmas Ed25519 exige una dependencia que la
    biblioteca estandar no trae, y eso lo decide el Soberano.
  · Sin Soberano declarado en este aparato no hay a quien buscar: NO_DATA, nivel sin decidir.

DONDE SE GUARDA. En `<casa>/nodo.json` (0600): es un dato de la MAQUINA (a que nodo pertenece), no
de la persona, asi que no va a `memory.db`. Es una cache: manda la ultima cedula importada.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import soberano

NOMBRE = re.compile(r"^nodo\.[0-9]{1,6}\.[a-z0-9][a-z0-9-]{0,30}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ESTADOS = ("solicitado", "linkeado", "revocado")
NIVELES = {1: "visitante", 2: "firmante", 3: "contribuyente (cuenta nodo)"}


def lee(cedula, codigo_soberano):
    """Lo que la cedula dice de ESTE aparato. Nunca lanza: devuelve estado y causa."""
    if not isinstance(cedula, dict) or cedula.get("esquema") != "preceptoros.cedula-nodo/1":
        return {"estado": "RECHAZADA", "causa": "no es una preceptoros.cedula-nodo/1"}
    if not NOMBRE.match(str(cedula.get("nodo", ""))):
        return {"estado": "RECHAZADA", "causa": "nombre de nodo mal formado"}
    disp = cedula.get("dispositivos")
    if not isinstance(disp, list) or any(not HEX64.match(str(d.get("clave", ""))) or d.get("estado") not in ESTADOS
                                         for d in disp):
        return {"estado": "RECHAZADA", "causa": "dispositivos mal formados"}
    cuerpo = {k: v for k, v in cedula.items() if k != "sha256"}
    if cedula.get("sha256") != hashlib.sha256(json.dumps(cuerpo, sort_keys=True, separators=(",", ":")).encode()).hexdigest():
        return {"estado": "FALLO_INTEGRIDAD", "causa": "el hash de la cedula no casa: se toco por el camino"}
    base = {"nodo": cedula["nodo"], "cedula_sha256": cedula["sha256"],
            "autenticidad": "NO_DATA · declaracion del rack, sin firma (la cedula no va firmada)"}
    cod = soberano.normalizar(codigo_soberano) if codigo_soberano and codigo_soberano != "NO_DATA" else None
    if not cod:
        return dict(base, estado="NO_DATA", nivel=None, causa="no hay Soberano declarado en este aparato")
    mio = [d for d in disp if soberano.codigo_de(d["clave"]) == cod]
    if not mio:
        return dict(base, estado="OK", nivel=2, es=NIVELES[2], codigo=cod,
                    causa="el codigo de este aparato no esta en la cedula de ese nodo")
    e = mio[0]["estado"]
    n = 3 if e == "linkeado" else 2
    return dict(base, estado="OK", nivel=n, es=NIVELES[n], codigo=cod, dispositivo=e)


def ruta_nodo():
    import casa
    return Path(casa.asegurar()) / "nodo.json"


def importar(fichero, codigo_soberano, destino=None):
    try:
        ced = json.loads(Path(fichero).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return {"estado": "RECHAZADA", "causa": f"no se puede leer: {type(e).__name__}"}
    r = lee(ced, codigo_soberano)
    if r["estado"] in ("OK", "NO_DATA"):
        destino = Path(destino or ruta_nodo())
        destino.write_text(json.dumps({"cedula": ced, "lectura": r}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        os.chmod(destino, 0o600)
        r["guardada"] = str(destino)
    return r


def estado(codigo_soberano, origen=None):
    origen = Path(origen or ruta_nodo())
    if not origen.exists():
        return {"estado": "NO_DATA", "nivel": None, "causa": "ninguna cedula importada en este aparato"}
    return lee(json.loads(origen.read_text(encoding="utf-8"))["cedula"], codigo_soberano)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Is this device a node account? Read from the rack's node card.")
    ap.add_argument("--db", help="memory.db path (to read the declared Sovereign)")
    sub = ap.add_subparsers(dest="orden", required=True)
    sub.add_parser("importar").add_argument("cedula")
    sub.add_parser("estado")
    a = ap.parse_args(argv)
    codigo = None
    try:
        import casa
        import memory
        ruta = Path(a.db) if a.db else Path(casa.raiz()) / "memory.db"
        # Solo si ya existe: mirar el estado del nodo no debe crear una memoria vacia de paso.
        if ruta.exists():
            with memory.abrir(str(ruta)) as c:
                codigo = soberano.quien(c)
    except Exception:
        codigo = None
    r = importar(a.cedula, codigo) if a.orden == "importar" else estado(codigo)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
