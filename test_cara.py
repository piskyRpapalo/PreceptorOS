#!/usr/bin/env python3
"""M2 · la cara · lo que tiene que ser verdad de una interfaz sin red.

sistema: MVP · solo biblioteca estandar.

La cara se GENERA: `cara.py` lee la memoria y escribe un HTML autocontenido.
Por eso casi todos estos casos son sobre el fichero generado y no sobre el
codigo que lo genera — lo que le llega a la persona es el HTML, y es ahi
donde una llamada de red o una palabra de la casa harian dano.

Ninguna prueba toca la memoria real: todas pasan --db a una base temporal.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import memory as M                          # noqa: E402
import textos as TX                         # noqa: E402

CASOS = []
TEMPORALES = []


def caso(nombre):
    def envoltorio(fn):
        CASOS.append((nombre, fn))
        return fn
    return envoltorio


# --- lo que no puede aparecer en la cara ----------------------------------

# El vocabulario de la casa. Vive en los comentarios del codigo interno, que
# lee el equipo; no puede vivir en la cara, que lee cualquiera (D67).
LEXICO_PRIVADO = ("soberano", "preceptor", "ironclaw", "hexelion")

# Todo lo que abre un socket. La cara se abre con doble clic desde el disco y
# tiene que funcionar entera sin una sola conexion (D68).
RED = (r"fetch\s*\(", r"XMLHttpRequest", r"WebSocket", r"EventSource",
       r"navigator\.sendBeacon", r"import\s*\(", r"https?://")

ASSETS = ("aurelius-talks.png", "aurelius-up.png")


def tmp_dir():
    d = tempfile.mkdtemp(prefix="aurelius_cara_")
    TEMPORALES.append(d)
    return d


def base_con_recuerdos(idioma=None):
    """Una memoria pequena pero con las dos cosas que importan: texto real y
    un hueco declarado."""
    ruta = os.path.join(tmp_dir(), "memory.db")
    M.crear(ruta)
    with M.abrir(ruta) as c:
        M.escribir_engrama(c, what="la impresora funciono al cambiar un cable",
                           why="llevaba un mes sin imprimir")
        M.escribir_engrama(c, what="recupere la base de datos de una copia")
        M.escribir_perfil(c, "device", "el portatil de la cocina")
        if idioma:
            M.escribir_perfil(c, "language", idioma)
    return ruta


def generar(ruta, extra=()):
    salida = os.path.join(tmp_dir(), "cara.html")
    proc = subprocess.run(
        [sys.executable, "cara.py", "--db", ruta, "--out", salida, *extra],
        cwd=AQUI, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, \
        f"cara.py fallo ({proc.returncode}): {proc.stderr[-500:]}"
    return open(salida, encoding="utf-8").read(), salida


# --- los cinco que pidio la mision ----------------------------------------

@caso("1 · la cara no lleva ni una palabra del vocabulario de la casa")
def t1():
    html, _ = generar(base_con_recuerdos())
    bajo = html.lower()
    encontradas = [p for p in LEXICO_PRIVADO if p in bajo]
    assert not encontradas, f"la cara publica dice {encontradas}"


@caso("2 · la cara no hace ni una llamada de red, ni carga nada de fuera")
def t2():
    html, _ = generar(base_con_recuerdos())
    for patron in RED:
        hallado = re.findall(patron, html, re.I)
        assert not hallado, f"la cara llama a la red: {patron} -> {hallado[:3]}"
    # Y nada se carga de fuera del fichero: ni script, ni hoja, ni imagen.
    for etiqueta, atributo in (("script", "src"), ("link", "href"),
                               ("img", "src")):
        for valor in re.findall(rf'<{etiqueta}[^>]*\s{atributo}="([^"]*)"',
                                html, re.I):
            assert valor.startswith("data:"), \
                f"<{etiqueta}> carga algo de fuera: {valor[:60]}"


@caso("3 · la Pizarra lleva los recuerdos y se los puede llevar la persona")
def t3():
    ruta = base_con_recuerdos()
    html, _ = generar(ruta)
    with M.abrir(ruta) as c:
        filas = [dict(r) for r in c.execute("select what, why from engrams")]
    for fila in filas:
        assert fila["what"] in html, f"la Pizarra no lleva el recuerdo {fila['what']!r}"
    # El hueco declarado se ve declarado, no como celda vacia.
    assert M.AUSENTE in html, "la Pizarra esconde los huecos en vez de decirlos"
    # Y exportar es del navegador, sin servidor: un enlace con download.
    assert re.search(r'download\s*=', html, re.I), \
        "no hay forma de llevarse los recuerdos sin pedirselos a un servidor"


@caso("4 · el selector cambia las cadenas, y arranca en el idioma del perfil")
def t4():
    html, _ = generar(base_con_recuerdos(idioma="es"))
    # Las dos columnas viajan dentro del fichero: cambiar de idioma no puede
    # depender de ir a buscar la traduccion a ningun sitio.
    assert TX.TEXTOS["es"]["recuerdo_que"] in html, "el español no viaja en la cara"
    assert TX.TEXTOS["en"]["recuerdo_que"] in html, "el ingles no viaja en la cara"
    # Y arranca en lo que dice el perfil, no en lo que le apetezca a la cara.
    assert re.search(r'IDIOMA_INICIAL\s*=\s*"es"', html), \
        "la cara ignora el idioma que la persona ya eligio"
    en, _ = generar(base_con_recuerdos(idioma="en"))
    assert re.search(r'IDIOMA_INICIAL\s*=\s*"en"', en), \
        "la cara no respeta el ingles del perfil"


@caso("5 · ASSETS.md declara el mapa de fotogramas y el contrato de animacion")
def t5():
    ruta = os.path.join(AQUI, "ASSETS.md")
    assert os.path.exists(ruta), "no hay ASSETS.md"
    doc = open(ruta, encoding="utf-8").read()
    for nombre in ASSETS:
        assert nombre in doc, f"ASSETS.md no declara {nombre}"
    # Los cuatro fotogramas de cada hoja, descritos uno a uno.
    for trozo in ("boca abierta", "boca en \"o\"", "sonrisa",
                  "sin romper", "trozos volando"):
        assert trozo in doc, f"el mapa de fotogramas no describe: {trozo}"
    # El contrato, en el mismo sitio que el mapa.
    for trozo in ("up[1]", "up[1→2→3→4]", "talks[4]", "talks[1→2→3]"):
        assert trozo in doc, f"el contrato de animacion no menciona {trozo}"
    assert "local" in doc.lower(), "el contrato no dice que la animacion es local"


# --- lo que la mision implica y conviene fijar ----------------------------

@caso("6 · los dos assets existen con su nombre canonico y son PNG")
def t6():
    for nombre in ASSETS:
        ruta = os.path.join(AQUI, "assets", nombre)
        assert os.path.exists(ruta), f"falta assets/{nombre}"
        with open(ruta, "rb") as fh:
            assert fh.read(8) == b"\x89PNG\r\n\x1a\n", f"{nombre} no es un PNG"


@caso("7 · la cara respeta el contrato de animacion, y lo hace sin red")
def t7():
    html, _ = generar(base_con_recuerdos())
    # Los dos sprites viajan incrustados, no enlazados.
    assert html.count("data:image/png;base64,") >= 2, \
        "los sprites no viajan dentro del fichero"
    # El contrato, tal como se escribio: dormido, despertar una vez, reposo,
    # bucle al hablar. Se comprueba que el codigo nombra los cuatro estados.
    for estado in ("dormido", "despertar", "reposo", "hablando"):
        assert estado in html, f"la cara no implementa el estado {estado!r}"
    # Despertar ocurre UNA vez: el codigo tiene que apagar su propia bandera.
    assert re.search(r"despertado\s*=\s*true", html, re.I), \
        "nada impide que el despertar se repita en cada frase"


@caso("8 · la cara se genera sin tocar la memoria real de la persona")
def t8():
    import inspect
    assert '"--db", ruta' in inspect.getsource(generar), \
        "generar() dejo de fijar la base: una prueba podria ir a la memoria real"
    real = os.path.expanduser("~/.aurelius")

    def foto():
        if not os.path.isdir(real):
            return None
        return sorted((n, os.stat(os.path.join(real, n)).st_mtime_ns)
                      for n in os.listdir(real))

    antes = foto()
    generar(base_con_recuerdos())
    assert foto() == antes, "generar la cara toco la memoria real"


@caso("9 · el modo formulario escribe lo que la cara recogio, sin borrar nada")
def t9():
    ruta = base_con_recuerdos()
    with M.abrir(ruta) as c:
        antes = c.execute("select count(*) from engrams").fetchone()[0]
        resumen = M.aplicar_formulario(c, {
            "language": "es",
            "profile": {"name": "David"},
            "engrams": [{"what": "un recuerdo que llego por el formulario",
                         "why": "", "where_ref": "", "learned": ""}],
        })
        despues = c.execute("select count(*) from engrams").fetchone()[0]
        assert despues == antes + 1, f"el formulario escribio {despues - antes} filas"
        assert M.leer_perfil(c, "language") == "es", "el idioma no llego al perfil"
        assert M.leer_perfil(c, "name") == "David", "el perfil no recogio el nombre"
        assert resumen["engrams"] == 1, f"el resumen miente: {resumen}"
        # Lo que ya estaba sigue estando: un formulario no es un reemplazo.
        primeros = [r[0] for r in c.execute("select what from engrams order by id")]
        assert primeros[0] == "la impresora funciono al cambiar un cable", \
            "el formulario piso lo que ya habia"


@caso("10 · el formulario no borra ni archiva, pase lo que pase")
def t10():
    import inspect
    fuente = inspect.getsource(M.aplicar_formulario)
    for prohibido in ("delete", "drop", "truncate"):
        assert prohibido not in fuente.lower(), \
            f"el modo formulario contiene {prohibido!r}"
    # Un formulario vacio no es una orden de vaciar: no escribe nada y lo dice.
    ruta = base_con_recuerdos()
    with M.abrir(ruta) as c:
        antes = c.execute("select count(*) from engrams").fetchone()[0]
        resumen = M.aplicar_formulario(c, {})
        despues = c.execute("select count(*) from engrams").fetchone()[0]
    assert antes == despues, "un formulario vacio cambio la memoria"
    assert resumen["engrams"] == 0, f"el resumen miente: {resumen}"


@caso("11 · la cara no inventa recuerdos: sin memoria, lo dice y no rellena")
def t11():
    ruta = os.path.join(tmp_dir(), "memory.db")
    M.crear(ruta)
    html, _ = generar(ruta)
    assert "0" in html, "una memoria vacia no declara su recuento"
    for inventado in ("la impresora", "lorem ipsum", "example memory"):
        assert inventado not in html.lower(), \
            f"la cara trae un recuerdo de ejemplo: {inventado!r}"


def main():
    fallos = 0
    print("── M2 · LA CARA " + "─" * 50)
    for nombre, fn in CASOS:
        try:
            fn()
            print(f"  ok    · {nombre}")
        except AssertionError as e:
            fallos += 1
            print(f"  FALLO · {nombre}\n          -> {e}")
        except Exception as e:
            fallos += 1
            print(f"  ERROR · {nombre}\n          -> {type(e).__name__}: {e}")
    for d in TEMPORALES:
        shutil.rmtree(d, ignore_errors=True)
    total = len(CASOS)
    print(f"\nRESULTADO: {total - fallos}/{total} correctos, {fallos} fallo(s)")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
