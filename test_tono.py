#!/usr/bin/env python3
# M2 · tono de juego antiguo. Tests primero. Solo biblioteca estandar.
# Invariante central: el TONO es del producto; el CARACTER es del Preceptor.
# El tono no toca esquema, no toca frontera, y no sabe de ningun modelo.
from __future__ import annotations

import io
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["AURELIUS_RITMO"] = "0"      # sin esperas en test: se fija ANTES
import tono as T                        # noqa: E402

CASOS = []


def caso(nombre):
    def deco(fn):
        CASOS.append((nombre, fn))
        return fn
    return deco


def capturar(fn, *a, **kw):
    buf, antes = io.StringIO(), sys.stdout
    sys.stdout = buf
    try:
        r = fn(*a, **kw)
    finally:
        sys.stdout = antes
    return buf.getvalue(), r


def con_entrada(texto, fn, *a, **kw):
    antes = sys.stdin
    sys.stdin = io.StringIO(texto)
    try:
        return capturar(fn, *a, **kw)
    finally:
        sys.stdin = antes


# --- el que importa: el ritmo no puede hacer lento un test ----------------

@caso("1 · con AURELIUS_RITMO=0 no hay esperas: el tono no ralentiza la suite")
def t1():
    frase = "una linea de longitud razonable para medir el coste"
    t0 = time.perf_counter()
    salida, _ = capturar(T.despacio, frase)
    T.pausa(5)          # cinco segundos nominales
    T.pausa(5)
    transcurrido = time.perf_counter() - t0
    # Precondicion: sin esto, el test pasa con un despacio() que no imprime.
    assert frase in salida, "despacio no imprimio nada: el test pasaria por vacio"
    assert transcurrido < 0.2, \
        f"el tono duerme aunque el ritmo sea 0: {transcurrido:.2f}s"


@caso("2 · el texto sale identico con ritmo 0 y con ritmo normal")
def t2():
    texto = "Camión, señora Ñuño — «comillas» y\nsegunda línea"
    salida_rapida, _ = capturar(T.despacio, texto)
    T.fijar_ritmo(0.0001)
    salida_lenta, _ = capturar(T.despacio, texto)
    T.fijar_ritmo(0)
    assert salida_rapida == salida_lenta, "el ritmo altera el texto"
    assert texto in salida_rapida, "el texto no sale entero"


# --- eleccion -------------------------------------------------------------

@caso("3 · eleccion acepta el numero y devuelve la clave, no el indice")
def t3():
    op = [("si", "Yes, seal it"), ("no", "Not now")]
    salida, r = con_entrada("1\n", T.eleccion, "Seal today?", op)
    assert r == "si", f"devolvio {r!r} en vez de la clave"
    assert "Yes, seal it" in salida and "Not now" in salida, \
        "no muestra las opciones"
    assert "1" in salida and "2" in salida, "no numera las opciones"


@caso("4 · entrada invalida vuelve a preguntar, no elige por la persona")
def t4():
    op = [("si", "Yes"), ("no", "No")]
    salida, r = con_entrada("banana\n9\n2\n", T.eleccion, "Choose", op)
    assert r == "no", f"devolvio {r!r}: eligio por su cuenta"
    assert salida.count("Choose") >= 2, "no repitio la pregunta tras el error"


@caso("5 · Enter sin escribir NO elige: vuelve a preguntar")
def t5():
    op = [("si", "Yes"), ("no", "No")]
    salida, r = con_entrada("\n\n2\n", T.eleccion, "Choose", op)
    assert r == "no", "un Enter vacio eligio la primera opcion"


@caso("6 · fin de entrada devuelve None, no una opcion inventada")
def t6():
    op = [("si", "Yes"), ("no", "No")]
    salida, r = con_entrada("", T.eleccion, "Choose", op)
    # Precondicion: devolver None sin haber preguntado nada no prueba nada.
    assert "Choose" in salida, "no llego a preguntar: el test pasaria por vacio"
    assert r is None, f"sin entrada devolvio {r!r} en vez de None"


# --- separacion de sistemas: el caracter no viaja -------------------------

def _codigo_sin_documentacion(ruta):
    """Devuelve identificadores y literales de cadena del modulo, SIN los
    docstrings ni los comentarios.

    Motivo: el invariante es sobre el CODIGO, no sobre su explicacion. Este
    modulo documenta en su cabecera que no sabe de modelos, y prohibir la
    palabra en prosa haria imposible explicar el invariante. Es el mismo falso
    positivo que prohibir la palabra DELETE en un docstring que dice
    'cero DELETE'. Los literales de cadena SI se miran: una ruta a un fichero
    de caracter seria una fuga real, no una explicacion.
    """
    import ast
    arbol = ast.parse(open(ruta, encoding="utf-8").read())
    docstrings = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            d = ast.get_docstring(nodo, clean=False)
            if d is not None:
                docstrings.add(d)
    piezas = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Name):
            piezas.append(nodo.id)
        elif isinstance(nodo, ast.Attribute):
            piezas.append(nodo.attr)
        elif isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
            if nodo.value not in docstrings:
                piezas.append(nodo.value)
        elif isinstance(nodo, (ast.Import, ast.ImportFrom)):
            piezas.append(getattr(nodo, "module", "") or "")
            piezas += [a.name for a in nodo.names]
    return "\n".join(piezas)


@caso("7 · el codigo del tono no usa ningun modelo ni fichero de caracter")
def t7():
    codigo = _codigo_sin_documentacion(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "tono.py"))
    prohibidos = ("temple", "ollama", "llama", "gguf", "model",
                  "inference", "transformers", "openai", "anthropic")
    encontrados = [p for p in prohibidos if p in codigo.lower()]
    assert not encontrados, \
        f"el codigo del producto usa el caracter del Preceptor: {encontrados}"


@caso("8 · el tono no importa nada fuera de la biblioteca estandar")
def t8():
    fuente = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "tono.py"), encoding="utf-8").read()
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", fuente, re.M)
    estandar = {"os", "sys", "time", "shutil", "textwrap", "random", "__future__"}
    fuera = [m for m in imports if m.split(".")[0] not in estandar]
    assert not fuera, f"dependencias fuera de la biblioteca estandar: {fuera}"


@caso("9 · el tono no toca esquema ni frontera: cero SQL, cero redaccion")
def t9():
    fuente = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "tono.py"), encoding="utf-8").read()
    sql = re.findall(r"\b(select|insert|update|delete|create table)\b",
                     fuente, re.IGNORECASE)
    assert not sql, f"el tono ejecuta SQL: {sql}"
    for palabra in ("redact", "guardrails", "export", "sanitize"):
        assert palabra not in fuente.lower(), \
            f"el tono toca la frontera: menciona {palabra}"


# --- el paso 8 · la oferta de sellar --------------------------------------

@caso("10 · la oferta de sellar es opcional y no rompe si falta manifest")
def t10():
    salida, r = con_entrada("2\n", T.ofrecer_sello, disponible=False)
    assert r is False, "ofrecio sellar sin manifiesto disponible"
    assert "not available" in salida.lower() or "no disponible" in salida.lower(), \
        "no declara que el sellado no esta disponible"


@caso("11 · con manifiesto disponible, elegir no NO sella")
def t11():
    salida, r = con_entrada("2\n", T.ofrecer_sello, disponible=True)
    # Precondicion: la oferta tiene que haberse mostrado de verdad.
    assert "seal" in salida.lower(), "no ofrecio nada: el test pasaria por vacio"
    assert r is False, "un no acabo sellando"


@caso("12 · con manifiesto disponible, elegir si devuelve True")
def t12():
    salida, r = con_entrada("1\n", T.ofrecer_sello, disponible=True)
    assert r is True, "un si no sello"


# --- sabotaje -------------------------------------------------------------

SABOTAJES = (
    # El interruptor del ritmo esta protegido DOS veces: la salida temprana y
    # la multiplicacion por _RITMO. Romper solo una no cambia la conducta, asi
    # que el sabotaje tiene que romper la funcion entera. Se descubrio porque
    # la version anterior de este sabotaje no era detectada: el fallo estaba
    # en el sabotaje, no en el codigo, y esa distincion es el punto del modo.
    ("el ritmo ignora el interruptor",
     "tono.py",
     "    if _RITMO <= 0:\n        return\n    time.sleep(segundos * _RITMO)",
     "    time.sleep(segundos)"),
    ("la eleccion elige sola con entrada vacia",
     "tono.py",
     "        if not linea:\n            continue",
     "        if not linea:\n            return opciones[0][0]"),
    ("la oferta de sello ignora la disponibilidad",
     "tono.py",
     "    if not disponible:",
     "    if False:"),
)


def _sha(ruta):
    import hashlib
    return hashlib.sha256(open(ruta, "rb").read()).hexdigest()


def main_sabotaje():
    import shutil
    import subprocess
    import tempfile
    print("── M2 · TONO · MODO SABOTAJE · se EXIGE rojo " + "─" * 22)
    aqui = os.path.dirname(os.path.abspath(__file__))
    sha_antes = _sha(os.path.join(aqui, "tono.py"))
    no_detectados = []
    for nombre, fichero, ancla, sustitucion in SABOTAJES:
        destino = os.path.join(tempfile.mkdtemp(prefix="sab_tono_"), "arbol")
        shutil.copytree(aqui, destino)
        ruta = os.path.join(destino, fichero)
        s = open(ruta, encoding="utf-8").read()
        if ancla not in s:
            print(f"  AVISO · {nombre}: ancla perdida")
            no_detectados.append(nombre + " (ancla perdida)")
            continue
        open(ruta, "w", encoding="utf-8").write(s.replace(ancla, sustitucion, 1))
        r = subprocess.run([sys.executable, "test_tono.py"], cwd=destino,
                           capture_output=True, text=True)
        if r.returncode == 0:
            print(f"  VERDE · {nombre} · NO DETECTADO")
            no_detectados.append(nombre)
        else:
            fallo = next((l for l in r.stdout.splitlines()
                          if l.strip().startswith(("FALLO", "ERROR"))), "")
            print(f"  roja  · {nombre}\n          {fallo.strip()[:86]}")
    if _sha(os.path.join(aqui, "tono.py")) != sha_antes:
        print("  CRITICO: el sabotaje escribio en el arbol original")
        no_detectados.append("original mutado")
    else:
        print(f"\nMODULO ORIGINAL INTACTO (sha256 {sha_antes[:16]}…)")
    total = len(SABOTAJES)
    print(f"\nRESULTADO SABOTAJE: {total - len(no_detectados)}/{total} detectadas")
    return 1 if no_detectados else 0


def main():
    fallos = 0
    print("── M2 · TONO DE JUEGO ANTIGUO " + "─" * 36)
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
    total = len(CASOS)
    print(f"\nRESULTADO: {total - fallos}/{total} correctos, {fallos} fallo(s)")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main_sabotaje() if "--sabotaje" in sys.argv[1:] else main())
