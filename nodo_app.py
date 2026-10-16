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
  · AUTENTICIDAD (P2, firma D5 del 2026-10-11). El rack no firma nada (IronClaw); la cedula la firma
    el SOBERANO con `ssh-keygen -Y sign -n preceptoros-cedula` (el mismo mecanismo que su registro) y
    va en `firma_ssh`. La app la verifica por SUBPROCESO con `ssh-keygen -Y verify` contra un
    `allowed_signers`: cero dependencias nuevas. Sin firma, sin `allowed_signers` o sin `ssh-keygen`
    en el aparato: NO_DATA con su causa, nunca un OK fingido. Firma que no verifica: RECHAZADA.
  · AGENTE DELEGADO (P1, firma D4). Un dispositivo `tipo: agente` lleva `ambito` (subconjunto de las
    capacidades del rack) y `caduca` (TTL de 30 min a 8 h, patron Artemis). `agente()` dice si puede
    tocar ESA capacidad AHORA. La delegacion nunca sube niveles: el agente no es cuenta nodo.
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
CAPACIDADES_NODO = ("memoria_compartida", "conectar_ia", "herramientas", "aportar_datos")   # las de nodos.py
TTL_MAX_S = 8 * 3600                                                                          # Artemis: 30 min-8 h
NS_CEDULA = "preceptoros-cedula"
FUERA_DE_LA_FIRMA = ("sha256", "firma_ssh", "firma", "autenticidad")


def cuerpo_firmado(cedula):
    """Lo que firma el Soberano: la cedula sin su hash, sin la firma y sin la etiqueta de autenticidad."""
    c = {k: v for k, v in cedula.items() if k not in FUERA_DE_LA_FIRMA}
    return json.dumps(c, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def autenticidad(cedula, signers=None):
    """('OK'|'NO_DATA'|'RECHAZADA', texto). Verifica por subproceso; nunca lanza."""
    import shutil
    import subprocess
    import tempfile
    sig = cedula.get("firma_ssh")
    if not sig:
        return "NO_DATA", "NO_DATA · declaracion del rack, sin firma (la cedula no va firmada)"
    ruta = Path(signers) if signers else None
    if ruta is None:
        try:
            import casa
            ruta = Path(casa.asegurar()) / "allowed_signers_cedula"
        except Exception:
            ruta = None
    if not ruta or not ruta.is_file():
        return "NO_DATA", "NO_DATA · firmada, pero este aparato no tiene allowed_signers para verificarla"
    if not shutil.which("ssh-keygen"):
        return "NO_DATA", "NO_DATA · firmada, pero este aparato no tiene ssh-keygen (Termux: pkg install openssh)"
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "firma.sig"
        f.write_text(str(sig))
        r = subprocess.run(["ssh-keygen", "-Y", "verify", "-f", str(ruta), "-I", "soberano", "-n", NS_CEDULA, "-s", str(f)],
                           input=cuerpo_firmado(cedula), capture_output=True, timeout=20)
    if r.returncode == 0:
        return "OK", f"OK · firmada por el Soberano (ssh-ed25519, {NS_CEDULA})"
    return "RECHAZADA", "la firma de la cedula no verifica contra el allowed_signers de este aparato"


def _forma(cedula):
    """None si la forma vale; si no, el resultado de rechazo. Comun a lee() y agente()."""
    if not isinstance(cedula, dict) or cedula.get("esquema") != "preceptoros.cedula-nodo/1":
        return {"estado": "RECHAZADA", "causa": "no es una preceptoros.cedula-nodo/1"}
    if not NOMBRE.match(str(cedula.get("nodo", ""))):
        return {"estado": "RECHAZADA", "causa": "nombre de nodo mal formado"}
    disp = cedula.get("dispositivos")
    if not isinstance(disp, list) or any(not isinstance(d, dict) or not HEX64.match(str(d.get("clave", ""))) or d.get("estado") not in ESTADOS
                                         for d in disp):
        return {"estado": "RECHAZADA", "causa": "dispositivos mal formados"}
    cuerpo = {k: v for k, v in cedula.items() if k != "sha256"}
    if cedula.get("sha256") != hashlib.sha256(json.dumps(cuerpo, sort_keys=True, separators=(",", ":")).encode()).hexdigest():
        return {"estado": "FALLO_INTEGRIDAD", "causa": "el hash de la cedula no casa: se toco por el camino"}
    return None
NIVELES = {1: "visitante", 2: "firmante", 3: "contribuyente (cuenta nodo)"}


def lee(cedula, codigo_soberano, signers=None):
    """Lo que la cedula dice de ESTE aparato. Nunca lanza: devuelve estado y causa."""
    mal = _forma(cedula)
    if mal:
        return mal
    disp = [d for d in cedula["dispositivos"] if d.get("tipo") != "agente"]   # un agente no es un aparato humano
    est, aut = autenticidad(cedula, signers)
    if est == "RECHAZADA":
        return {"estado": "RECHAZADA", "causa": aut, "nodo": cedula["nodo"]}
    base = {"nodo": cedula["nodo"], "cedula_sha256": cedula["sha256"], "autenticidad": aut}
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


def _fecha(texto):
    from datetime import datetime, timezone
    return datetime.strptime(str(texto), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def agente(cedula, clave, capacidad, ahora=None, signers=None):
    """P1 · ¿puede el agente de clave `clave` tocar `capacidad` AHORA? Nunca lanza."""
    from datetime import datetime, timezone
    mal = _forma(cedula)
    if mal:
        return mal
    est, aut = autenticidad(cedula, signers)
    if est == "RECHAZADA":
        return {"estado": "RECHAZADA", "causa": aut}
    ahora = ahora or datetime.now(timezone.utc)
    suyo = [d for d in cedula["dispositivos"] if d.get("clave") == clave and d.get("tipo") == "agente"]
    if not suyo:
        return {"estado": "RECHAZADA", "causa": "esa clave no es un agente delegado en esta cedula"}
    d = suyo[0]
    if d["estado"] == "revocado":
        return {"estado": "RECHAZADA", "causa": "agente revocado: sin delegacion desde ya"}
    if d["estado"] != "linkeado":
        return {"estado": "RECHAZADA", "causa": "agente aun no aceptado por el admin (falta la segunda firma)"}
    ambito = d.get("ambito")
    if not isinstance(ambito, list) or not ambito or any(a not in CAPACIDADES_NODO for a in ambito):
        return {"estado": "RECHAZADA", "causa": "ambito mal formado o con capacidades que el nodo no declara"}
    if capacidad not in ambito:
        return {"estado": "RECHAZADA", "causa": f"'{capacidad}' esta fuera del ambito delegado {ambito}"}
    try:
        cad = _fecha(d.get("caduca"))
    except (TypeError, ValueError):
        return {"estado": "RECHAZADA", "causa": "caducidad mal formada"}
    if cad <= ahora:
        return {"estado": "RECHAZADA", "causa": "delegacion caducada: el agente ya no puede actuar"}
    if (cad - ahora).total_seconds() > TTL_MAX_S:
        return {"estado": "RECHAZADA", "causa": "TTL fuera de la ventana Artemis (30 min-8 h): ningun permiso permanente"}
    return {"estado": "OK", "agente": clave, "capacidad": capacidad, "ambito": ambito, "caduca": d["caduca"],
            "autenticidad": aut, "nodo": cedula["nodo"]}


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
