#!/usr/bin/env python3
"""canales.py · canales entre agentes, como ficheros de solo añadir. Sin sockets.

**Solo biblioteca estándar.**

POR QUÉ EXISTE
--------------
Los agentes (app, web, lab, el orquestador) se hablaban por la Sala, un
servidor con su puerto. Un canal no necesita un puerto: necesita un sitio donde
añadir una línea y de donde leerla. Aquí un canal ES un fichero
`<casa>/canales/<canal>.jsonl`, una línea por mensaje, y nada más.

    python3 canales.py di <canal> <voz> "texto" [--sello S] [--rol R] [--maquina JSON]
    python3 canales.py lee <canal> [--desde N]

LAS REGLAS, Y POR QUÉ
---------------------
* **Un canal no es autoridad.** Un mensaje no concede permisos, no cuenta como
  firma y no cambia nada del estado, del ledger ni de los interruptores, diga
  lo que diga su texto. Este módulo no importa nada que pueda cambiarlos: la
  frontera es lo que NO está importado, y una prueba lo comprueba.
* **La voz `soberano` no se toma, se tiene.** Ningún agente escribe con ella:
  `di()` la rechaza siempre. Solo `di_soberano()` la usa, y solo la llama la
  puerta de la app a la que la persona escribe desde su pantalla.
* **Nada sale sin pasar por guardrails.** Texto, rol y cada texto de `maquina`
  pasan por `redactar_salida` antes de tocar el disco. Si el filtro no puede
  terminar, no se escribe: falla cerrado.
* **Una línea entera o ninguna.** Se escribe bajo `flock` exclusivo, con `n`
  = último `n` + 1 leído bajo ese mismo cerrojo, en una sola llamada `write`
  sobre un fichero en modo añadir. Dos escritores a la vez no se pisan ni
  repiten número.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

import casa as _casa
import guardrails as G

# `fcntl` es POSIX. Sin el no hay cerrojo, y sin cerrojo no se escribe: leer
# sigue funcionando (la app no deja de arrancar en otra plataforma), escribir
# se rechaza con su causa en vez de arriesgar dos lineas con el mismo `n`.
try:
    import fcntl
except ImportError:                                  # pragma: no cover
    fcntl = None

ESQUEMA = "preceptoros.canal/1"
CANALES = ("orquesta", "app", "web", "lab")
SELLOS = ("MEDIDO", "EMULADO", "NO_DATA", "PROPUESTA", "REQUIERE_FIRMA", "DECLARADO")
VOZ_RESERVADA = "soberano"
_VOZ = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
TOPE_TEXTO = 8000
TOPE_MAQUINA = 4000
TOPE_LECTURA = 200          # mensajes por lectura: un canal no se vuelca entero


class CanalRechazado(ValueError):
    """El mensaje no se escribe. La causa va en el texto de la excepción."""


def directorio(base=None):
    return Path(base or _casa.raiz()) / "canales"


def ruta(canal, base=None):
    if canal not in CANALES:
        raise CanalRechazado(f"canal desconocido: {canal!r} (son {', '.join(CANALES)})")
    return directorio(base) / f"{canal}.jsonl"


def _normal(voz):
    t = unicodedata.normalize("NFKD", str(voz or "")).lower().strip()
    return "".join(c for c in t if not unicodedata.combining(c))


def es_soberano(voz):
    """«Soberano», « soberano », «Sóberano»: todas son la misma voz reservada."""
    return _normal(voz).replace("0", "o") == VOZ_RESERVADA


def _limpio(texto, casa):
    """Redacción de guardrails + la casa fuera. Falla cerrado."""
    if casa and casa != "/" and casa in texto:
        texto = texto.replace(casa, "~")
    try:
        tachado, _h = G.redactar_salida(texto)
    except Exception as e:                       # el filtro no terminó: no hay escritura
        raise CanalRechazado(f"el filtro no pudo terminar ({type(e).__name__})") from None
    return tachado


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


def _ultimo_n(fh):
    """El `n` de la última línea legible. Se lee bajo el cerrojo."""
    fh.seek(0, os.SEEK_END)
    tam = fh.tell()
    trozo = min(tam, 64 * 1024)
    fh.seek(tam - trozo)
    # En binario: un salto a mitad de un caracter UTF-8 no puede romper la
    # lectura; la primera linea del trozo puede salir cortada y se salta.
    for linea in reversed(fh.read(trozo).decode("utf-8", "replace").splitlines()):
        try:
            n = json.loads(linea).get("n")
        except (ValueError, AttributeError):
            continue
        if isinstance(n, int):
            return n
    if tam > trozo:                              # cola sin nada legible: se recorre entero
        fh.seek(0)
        ultimo = 0
        for linea in fh:
            try:
                n = json.loads(linea.decode("utf-8", "replace")).get("n")
            except (ValueError, AttributeError):
                continue
            if isinstance(n, int):
                ultimo = n
        return ultimo
    return 0


def _escribir(canal, voz, texto, sello, rol, maquina, base):
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
    destino = ruta(canal, base)
    mensaje = {
        "canal": canal, "voz": voz,
        "rol": _limpio(str(rol or ""), casa)[:120],
        "texto": _limpio(texto, casa),
        "maquina": _limpia_maquina(maquina, casa),
        "sello": sello,
    }
    destino.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(destino, os.O_RDWR | os.O_APPEND | os.O_CREAT, 0o600)
    with os.fdopen(fd, "r+b") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            n = _ultimo_n(fh) + 1
            t = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
            linea = json.dumps({"n": n, "t": t, **mensaje}, ensure_ascii=False) + "\n"
            fh.seek(0, os.SEEK_END)
            fh.write(linea.encode("utf-8"))       # una sola escritura, en modo añadir
            fh.flush()
            os.fsync(fh.fileno())
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)
    return {"n": n, "t": t, **mensaje}


def di(canal, voz, texto, sello="DECLARADO", rol="", maquina=None, base=None):
    """Un agente escribe en un canal. Nunca con la voz `soberano`."""
    if not isinstance(voz, str) or es_soberano(voz):
        raise CanalRechazado("la voz soberano no la toma ningún agente")
    if not _VOZ.match(voz):
        raise CanalRechazado("la voz es un nombre corto en minúsculas ([a-z][a-z0-9_-]*)")
    return _escribir(canal, voz, texto, sello, rol, maquina, base)


def di_soberano(canal, texto, sello="DECLARADO", base=None):
    """La persona escribe desde la app. Solo la llama la puerta de la PWA.

    Tampoco esto concede nada: un mensaje del Soberano en un canal es una
    frase, no una firma. Las firmas viven donde viven (ledger, interruptores,
    ritual), y este módulo no las toca.
    """
    return _escribir(canal, VOZ_RESERVADA, texto, sello, "persona", {"via": "app"}, base)


def lee(canal, desde=0, base=None, tope=TOPE_LECTURA):
    """{canal, mensajes, corruptas, ultimo}. Una línea rota se cuenta, no se pinta."""
    destino = ruta(canal, base)
    mensajes, corruptas, ultimo = [], 0, 0
    try:
        with open(destino, "r", encoding="utf-8") as fh:
            for linea in fh:
                try:
                    m = json.loads(linea)
                except ValueError:
                    corruptas += 1
                    continue
                if not isinstance(m, dict) or not isinstance(m.get("n"), int):
                    corruptas += 1
                    continue
                ultimo = max(ultimo, m["n"])
                if m["n"] > desde:
                    mensajes.append(m)
    except FileNotFoundError:
        return {"canal": canal, "estado": "NO_DATA", "causa": "el canal aún no tiene mensajes",
                "mensajes": [], "corruptas": 0, "ultimo": 0}
    return {"canal": canal, "estado": "MEDIDO", "mensajes": mensajes[-tope:],
            "recortados": max(0, len(mensajes) - tope), "corruptas": corruptas,
            "ultimo": ultimo}


def resumen(base=None):
    """Los canales que existen y su último `n`. Para la lista de la consola."""
    salida = []
    for c in CANALES:
        r = lee(c, desde=10 ** 12, base=base)
        salida.append({"canal": c, "ultimo": r["ultimo"], "corruptas": r["corruptas"]})
    return salida


def _cli(argv=None):
    p = argparse.ArgumentParser(prog="canales.py", description="canales de solo añadir")
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
            print(json.dumps(di(a.canal, a.voz, a.texto, a.sello, a.rol, maquina),
                             ensure_ascii=False))
        else:
            print(json.dumps(lee(a.canal, a.desde), ensure_ascii=False, indent=1))
    except CanalRechazado as e:
        print(f"RECHAZADO · {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
