#!/usr/bin/env python3
"""canales.py · el adaptador de la app sobre el canal ÚNICO: `eventos.db` del registro.

**Solo biblioteca estándar. Sin sockets.**

POR QUÉ CAMBIÓ (2026-10-04, regla de unificación del Soberano)
---------------------------------------------------------------
Este módulo nació escribiendo sus propios `<casa>/canales/<canal>.jsonl`, y eso
hacía cuatro canales de mensajes en la misma casa (la Sala, el Acta, estos
ficheros y el registro). El canal canónico es UNO: `<casa>/registro/eventos.db`,
de solo anexar, saneado, y que leen todos los agentes. Así que esto ya no es un
almacén: es la VISTA de la app sobre ese canal. Un mensaje es un evento de tipo
`mensaje` cuyo cuerpo dice en qué hilo va (orquesta, app, web, lab). Los
`.jsonl` viejos quedan como archivo, en lectura.

    python3 canales.py di <hilo> <voz> "texto" [--sello S] [--rol R] [--maquina JSON]
    python3 canales.py lee <hilo> [--desde N]

LAS GARANTÍAS, QUE NO CAMBIAN
-----------------------------
* **Un mensaje no es autoridad.** No concede permisos ni cuenta como firma. Este
  módulo solo toca la tabla `eventos`; la base de autoridad no la nombra.
* **El actor `soberano` no se toma, se tiene.** `di()` lo rechaza siempre, con
  mayúsculas, tildes o un cero por o. Solo `di_soberano()` lo usa, y solo la
  llama la puerta de la app a la que escribe la persona.
* **Nada entra sin pasar por guardrails**, y después por los patrones privados
  del registro: si aún quedara algo privado, no se anexa (falla cerrado).
* **Una fila entera o ninguna.** Se anexa bajo `flock` exclusivo sobre el
  fichero de la base y dentro de una transacción inmediata de SQLite; el `n`
  lo da la propia tabla. Dos escritores a la vez no se pisan.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

import casa as _casa
import guardrails as G

try:
    import fcntl
except ImportError:                                  # pragma: no cover
    fcntl = None

ESQUEMA = "preceptoros.canal/2"
TIPO = "mensaje"
CANALES = ("orquesta", "app", "web", "lab")          # hilos dentro del canal único
SELLOS = ("MEDIDO", "EMULADO", "NO_DATA", "PROPUESTA", "REQUIERE_FIRMA", "DECLARADO")
VOZ_RESERVADA = "soberano"
_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,60}$")     # el mismo `SLUG` del registro
TOPE_TEXTO = 8000
TOPE_MAQUINA = 4000
TOPE_LECTURA = 200

# Los mismos patrones que el registro usa para rechazar lo privado. Copia
# DECLARADA (el registro vive fuera de este repo público): test_canales cruza
# las dos listas cuando el registro está en la máquina.
PRIVADO = [
    (re.compile(r"\b100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b"), "IP de la tailnet"),
    (re.compile(r"/home/[A-Za-z0-9_.-]+"), "ruta /home/<usuario>"),
    (re.compile(r"ssh-(ed25519|rsa|ecdsa)\S*\s+AAAA"), "clave SSH"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "clave privada"),
    (re.compile(r"ed25519:[1-9A-HJ-NP-Za-km-z]{40,}"), "clave NEAR"),
]

# El esquema de la tabla, idéntico al del registro, por si la casa aún no lo
# tiene. Solo `create ... if not exists`: nunca se altera una tabla que exista.
ESQUEMA_EVENTOS = """
create table if not exists eventos (
  n            integer primary key autoincrement,
  ts           text not null,
  maquina      text not null,
  tipo         text not null,
  actor        text not null,
  cuerpo_json  text not null,
  no_data_json text not null,
  bloquea_json text
);
create trigger if not exists eventos_sin_update before update on eventos
  begin select raise(abort, 'canal: solo anexar'); end;
create trigger if not exists eventos_sin_delete before delete on eventos
  begin select raise(abort, 'canal: se archiva, no se borra'); end;
"""


_REGISTRO = {}


def _registro():
    """El módulo del Registro Único, si esta máquina lo tiene y ya conoce el tipo
    `mensaje`. Vive fuera de este repo público: se busca en PRECEPTOROS_REGISTRO_PY
    o en su sitio del rack. Sin él, el adaptador anexa con el mismo esquema."""
    ruta = os.environ.get("PRECEPTOROS_REGISTRO_PY") or str(Path.home() / "p0x" / "registro" / "registro.py")
    if ruta in _REGISTRO:
        return _REGISTRO[ruta]
    mod = None
    if os.path.isfile(ruta):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("registro_unico", ruta)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if TIPO not in getattr(mod, "TIPOS_EVENTO", ()):
                mod = None
        except Exception:
            mod = None
    _REGISTRO[ruta] = mod
    return mod


class CanalRechazado(ValueError):
    """El mensaje no se anexa. La causa va en el texto de la excepción."""


def ruta_canal(base=None):
    return Path(base or _casa.raiz()) / "registro" / "eventos.db"


def _hilo(canal):
    if canal not in CANALES:
        raise CanalRechazado(f"hilo desconocido: {canal!r} (son {', '.join(CANALES)})")
    return canal


def es_soberano(voz):
    t = unicodedata.normalize("NFKD", str(voz or "")).lower().strip()
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.replace("0", "o") == VOZ_RESERVADA


def _limpio(texto, casa):
    if casa and casa != "/" and casa in texto:
        texto = texto.replace(casa, "~")
    try:
        return G.redactar_salida(texto)[0]
    except Exception as e:                           # el filtro no terminó: no hay escritura
        raise CanalRechazado(f"el filtro no pudo terminar ({type(e).__name__})") from None


def _limpia_maquina(valor, casa):
    if isinstance(valor, str):
        return _limpio(valor, casa)
    if isinstance(valor, dict):
        return {str(k)[:64]: _limpia_maquina(v, casa) for k, v in valor.items()}
    if isinstance(valor, list):
        return [_limpia_maquina(v, casa) for v in valor]
    if valor is None or isinstance(valor, (bool, int, float)):
        return valor
    return _limpio(str(valor), casa)


def _anexar(canal, actor, texto, sello, rol, maquina, base):
    hilo = _hilo(canal)
    if not isinstance(texto, str) or not texto.strip():
        raise CanalRechazado("hace falta texto")
    if len(texto) > TOPE_TEXTO:
        raise CanalRechazado(f"el texto pasa de {TOPE_TEXTO} caracteres")
    if sello not in SELLOS:
        raise CanalRechazado(f"sello fuera del vocabulario: {sello!r}")
    maquina = maquina if maquina is not None else {}
    if not isinstance(maquina, dict):
        raise CanalRechazado("`maquina` es un objeto")
    if len(json.dumps(maquina, ensure_ascii=False)) > TOPE_MAQUINA:
        raise CanalRechazado(f"`maquina` pasa de {TOPE_MAQUINA} caracteres")
    if fcntl is None:
        raise CanalRechazado("esta plataforma no tiene flock: sin cerrojo no se escribe")
    casa = os.path.expanduser("~")
    cuerpo = {"hilo": hilo, "texto": _limpio(texto, casa),
              "rol": _limpio(str(rol or ""), casa)[:120], "sello": sello,
              "maquina": _limpia_maquina(maquina, casa)}
    crudo = json.dumps(cuerpo, ensure_ascii=False, sort_keys=True)
    for patron, que in PRIVADO:                       # segunda puerta, la del registro
        if patron.search(crudo):
            raise CanalRechazado(f"lleva {que}: el canal no guarda lo privado")
    destino = ruta_canal(base)
    destino.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    no_data = [{"campo": "bloquea", "causa": "el adaptador de la app no calcula bloqueos"}]
    # Solo se pasa por el registro si su canal YA existe: `Registro.inicializar`
    # crearía también la base de autoridad, y la app no crea nada ahí.
    reg = _registro() if destino.is_file() else None
    fd = os.open(destino, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        if reg is not None:
            r = reg.Registro(destino.parent).anexar_evento(TIPO, actor, cuerpo)
            if r.get("estado") != "OK":
                raise CanalRechazado(f"el registro no lo anexó: {r.get('causa')}")
            filas = _filas(base, "select n, ts from eventos where tipo = ? and actor = ? and cuerpo_json = ?"
                                 " order by n desc limit 1", (TIPO, actor, crudo))
            if not filas:
                raise CanalRechazado("el registro dijo OK y la fila no aparece")
            (n, ts), via = filas[0], "registro.anexar_evento"
        else:
            con = sqlite3.connect(destino, timeout=30, isolation_level=None)
            try:
                con.executescript(ESQUEMA_EVENTOS)
                con.execute("begin immediate")
                cur = con.execute(
                    "insert into eventos (ts, maquina, tipo, actor, cuerpo_json, no_data_json, bloquea_json)"
                    " values (?,?,?,?,?,?,NULL)",
                    (ts, os.uname().nodename, TIPO, actor, crudo, json.dumps(no_data, ensure_ascii=False)))
                n = cur.lastrowid
                con.execute("commit")
            finally:
                con.close()
            via = "adaptador (mismo esquema; registro.py no disponible aquí)"
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
    return {"n": n, "t": ts, "canal": hilo, "voz": actor, "via": via,
            **{k: cuerpo[k] for k in ("rol", "texto", "maquina", "sello")}}


def di(canal, voz, texto, sello="DECLARADO", rol="", maquina=None, base=None):
    """Un agente anexa un mensaje. Nunca con el actor `soberano`."""
    if not isinstance(voz, str) or es_soberano(voz):
        raise CanalRechazado("la voz soberano no la toma ningún agente")
    if not _SLUG.match(voz):
        raise CanalRechazado("el actor es un slug en minúsculas ([a-z0-9][a-z0-9-]*)")
    return _anexar(canal, voz, texto, sello, rol, maquina, base)


def di_soberano(canal, texto, sello="DECLARADO", base=None):
    """La persona escribe desde la app. Solo la llama la puerta de la PWA.
    Tampoco esto concede nada: una frase no es una firma."""
    return _anexar(canal, VOZ_RESERVADA, texto, sello, "persona", {"via": "app"}, base)


def _filas(base, sql, args):
    destino = ruta_canal(base)
    if not destino.is_file():
        return None
    con = sqlite3.connect(f"file:{destino}?mode=ro", uri=True, timeout=5)
    try:
        return con.execute(sql, args).fetchall()
    finally:
        con.close()


def lee(canal, desde=0, base=None, tope=TOPE_LECTURA):
    """{canal, mensajes, corruptas, ultimo}. Solo lectura (mode=ro)."""
    hilo = _hilo(canal)
    try:
        filas = _filas(base, "select n, ts, actor, cuerpo_json from eventos where tipo = ?"
                             " order by n", (TIPO,))
    except sqlite3.Error as e:
        return {"canal": hilo, "estado": "NO_DATA", "causa": f"el canal no se pudo leer ({type(e).__name__})",
                "mensajes": [], "corruptas": 0, "ultimo": 0}
    if filas is None:
        return {"canal": hilo, "estado": "NO_DATA", "causa": "el canal aún no tiene mensajes",
                "mensajes": [], "corruptas": 0, "ultimo": 0}
    mensajes, corruptas, ultimo = [], 0, 0
    for n, ts, actor, cj in filas:
        try:
            c = json.loads(cj)
        except ValueError:
            corruptas += 1
            continue
        if not isinstance(c, dict) or c.get("hilo") != hilo:
            continue
        ultimo = max(ultimo, n)
        if n > desde:
            mensajes.append({"n": n, "t": ts, "canal": hilo, "voz": actor,
                             "rol": c.get("rol", ""), "texto": c.get("texto", ""),
                             "maquina": c.get("maquina") or {}, "sello": c.get("sello")})
    return {"canal": hilo, "estado": "MEDIDO", "mensajes": mensajes[-tope:],
            "recortados": max(0, len(mensajes) - tope), "corruptas": corruptas, "ultimo": ultimo}


def resumen(base=None):
    return [{"canal": c, "ultimo": lee(c, desde=10 ** 12, base=base)["ultimo"], "corruptas": 0}
            for c in CANALES]


def archivo(base=None):
    """Los almacenes viejos, SOLO como archivo en lectura: la Sala, los
    `.jsonl` de la primera versión de este módulo y, si la casa lo declara con
    PRECEPTOROS_ACTA, el Acta. Nada de aquí se escribe."""
    raiz = Path(base or _casa.raiz())
    fuentes = [("sala", raiz / "laboratorio" / "sala.jsonl")]
    fuentes += [(f"canales-v1:{p.stem}", p) for p in sorted((raiz / "canales").glob("*.jsonl"))]
    acta = os.environ.get("PRECEPTOROS_ACTA")
    if acta:
        fuentes.append(("acta", Path(acta)))
    salida = []
    for nombre, ruta in fuentes:
        try:
            with open(ruta, "r", encoding="utf-8") as fh:
                lineas = fh.readlines()[-TOPE_LECTURA:]
        except OSError:
            continue
        for linea in lineas:
            try:
                m = json.loads(linea)
            except ValueError:
                continue
            if not isinstance(m, dict):
                continue
            salida.append({"origen": f"archivo:{nombre}", "n": m.get("n") or m.get("id"),
                           "t": m.get("t") or m.get("ts"), "voz": m.get("voz") or m.get("de"),
                           "texto": m.get("texto") or m.get("humano") or "",
                           "sello": m.get("sello") or "DECLARADO", "maquina": {"archivo": nombre}})
    return salida


def _cli(argv=None):
    p = argparse.ArgumentParser(prog="canales.py", description="la app sobre el canal único")
    sub = p.add_subparsers(dest="orden", required=True)
    d = sub.add_parser("di")
    d.add_argument("canal")
    d.add_argument("voz")
    d.add_argument("texto")
    d.add_argument("--sello", default="DECLARADO")
    d.add_argument("--rol", default="")
    d.add_argument("--maquina", default="{}")
    l_ = sub.add_parser("lee")
    l_.add_argument("canal")
    l_.add_argument("--desde", type=int, default=0)
    a = p.parse_args(argv)
    try:
        if a.orden == "di":
            try:
                maquina = json.loads(a.maquina)
            except ValueError:
                raise CanalRechazado("--maquina no es JSON") from None
            print(json.dumps(di(a.canal, a.voz, a.texto, a.sello, a.rol, maquina), ensure_ascii=False))
        else:
            print(json.dumps(lee(a.canal, a.desde), ensure_ascii=False, indent=1))
    except CanalRechazado as e:
        print(f"RECHAZADO · {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
