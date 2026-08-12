#!/usr/bin/env python3
# M2 · el Agua · los diez criterios del plan firmado, como tests.
# Escritos ANTES de memory.py. Deben fallar todos antes de la implementacion.
# sistema: MVP · solo biblioteca estandar.
from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memory as M  # noqa: E402


# --- utilidades de prueba -------------------------------------------------

def tmp_ruta(nombre="memoria.db"):
    return os.path.join(tempfile.mkdtemp(prefix="m2_"), nombre)


def redactor_de_prueba(texto):
    """Sustituto minimo de guardrails para probar la DIRECCION, no las reglas.
    El guardrails real lo aporta el modulo del producto; aqui solo hace falta
    algo determinista que demuestre que la salida se redacta y el disco no."""
    marcado = texto.replace("clave-secreta-de-prueba", "[API_KEY]")
    n = texto.count("clave-secreta-de-prueba")
    return marcado, ([{"policy": "API_KEY", "count": n}] if n else [])


CASOS = []


def caso(nombre):
    def deco(fn):
        CASOS.append((nombre, fn))
        return fn
    return deco


# --- criterio 3 · va primero, por orden del Soberano ----------------------

@caso("3 · ida y vuelta byte a byte, con acentos y saltos de linea")
def t3():
    ruta = tmp_ruta()
    M.crear(ruta)
    texto = "Camión de la señora Ñuño\nsegunda línea\ttabulada\ny «comillas» — guion largo"
    with M.abrir(ruta) as c:
        fila = M.escribir_engrama(c, what=texto)
        leida = M.leer_engrama(c, fila["id"])
    assert leida["what"] == texto, "el texto no volvio identico"
    assert leida["what"].encode() == texto.encode(), "difiere a nivel de bytes"


# --- criterio 1 y 2 · los tres estados ------------------------------------

@caso("1 · arranque en frio: sin fichero, estado SIN_ESQUEMA")
def t1():
    ruta = tmp_ruta("no_existe.db")
    est, rec = M.estado(ruta)
    assert est == "SIN_ESQUEMA", f"esperaba SIN_ESQUEMA, dio {est}"
    assert rec["engrams"] == 0
    assert "no" in M.mensaje_estado(est, rec).lower()


@caso("2 · vacia no es ausente: esquema creado, cero filas, estado VACIA")
def t2():
    ruta = tmp_ruta()
    M.crear(ruta)
    est, rec = M.estado(ruta)
    assert est == "VACIA", f"esperaba VACIA, dio {est}"
    assert rec["engrams"] == 0 and rec["links"] == 0
    assert M.mensaje_estado("VACIA", rec) != M.mensaje_estado("SIN_ESQUEMA", rec), \
        "vacia y ausente muestran el mismo mensaje"


# --- criterio 4 · NO_DATA visible -----------------------------------------

@caso("4 · NO_DATA sobrevive y se muestra literalmente, no como celda vacia")
def t4():
    ruta = tmp_ruta()
    M.crear(ruta)
    with M.abrir(ruta) as c:
        fila = M.escribir_engrama(c, what="un recuerdo", why=None, where_ref=None)
        assert fila["why"] == "NO_DATA" and fila["where_ref"] == "NO_DATA"
        tabla = M.vista_tabla(c)
    assert tabla.count("NO_DATA") >= 2, "NO_DATA no aparece visible en la tabla"


# --- criterio 5 · recuento de huecos ---------------------------------------

@caso("5 · el recuento de huecos por columna es exacto")
def t5():
    ruta = tmp_ruta()
    M.crear(ruta)
    with M.abrir(ruta) as c:
        M.escribir_engrama(c, what="a", why=None, where_ref=None)      # 2 huecos
        M.escribir_engrama(c, what="b", why="porque", where_ref=None)  # 1 hueco
        M.escribir_engrama(c, what="c", why=None, where_ref="ref")     # 1 hueco
        rec = M.recuento_huecos(c)
    # El spec §4 cuenta huecos en las TRES columnas rellenables: why,
    # where_ref y learned. Los tres recuerdos dejan learned vacio, asi que
    # learned suma 3. La cifra 4 de la primera version de este test olvidaba
    # esa columna: era una resta mal hecha en el test, no un fallo del codigo.
    assert rec["why"] == 2, f"why: esperaba 2, dio {rec['why']}"
    assert rec["where_ref"] == 2, f"where_ref: esperaba 2, dio {rec['where_ref']}"
    assert rec["learned"] == 3, f"learned: esperaba 3, dio {rec['learned']}"
    assert rec["total"] == 7, f"total: esperaba 7, dio {rec['total']}"


# --- criterio 6 · el arbol -------------------------------------------------

@caso("6 · el enlace aparece indentado con su etiqueta; sin enlaces, raiz suelta")
def t6():
    ruta = tmp_ruta()
    M.crear(ruta)
    with M.abrir(ruta) as c:
        a = M.escribir_engrama(c, what="raiz con hijo")["id"]
        b = M.escribir_engrama(c, what="el hijo")["id"]
        M.escribir_engrama(c, what="raiz suelta")
        M.escribir_enlace(c, a, b, "lleva a")
        arbol = M.vista_arbol(c)
    assert "lleva a" in arbol, "la etiqueta de relacion no aparece"
    lineas = [l for l in arbol.splitlines() if l.strip()]
    hijas = [l for l in lineas if l.startswith("  ")]
    assert any("el hijo" in l for l in hijas), "el hijo no esta indentado"
    assert any(l.strip().startswith("raiz suelta") and not l.startswith("  ")
               for l in lineas), "la raiz suelta no aparece como raiz"


# --- criterio 7 · archivar no borra ---------------------------------------

@caso("7 · archivar oculta de la vista pero no borra; cero DELETE")
def t7():
    ruta = tmp_ruta()
    M.crear(ruta)
    with M.abrir(ruta) as c:
        i = M.escribir_engrama(c, what="para archivar")["id"]
        M.archivar(c, i)
        assert "para archivar" not in M.vista_tabla(c), "sigue en la vista por defecto"
        assert "para archivar" in M.vista_tabla(c, incluir_archivados=True), \
            "no se puede recuperar"
        n = c.execute("select count(*) from engrams").fetchone()[0]
    assert n == 1, "la fila se borro de la tabla"
    # Se busca la SENTENCIA SQL, no la palabra: memory.py menciona "Cero
    # DELETE" en su docstring, y prohibir la palabra en prosa es el mismo
    # falso positivo que prohibir ::1 en la guardia. Se comprueba el uso.
    import re
    fuente = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "memory.py"), encoding="utf-8").read()
    sentencias = re.findall(r"delete\s+from\s+\w+", fuente, re.IGNORECASE)
    assert not sentencias, f"memory.py ejecuta DELETE: {sentencias}"


# --- criterio 8 · sobrevive a un corte ------------------------------------

@caso("8 · modo diario WAL y ninguna fila a medias")
def t8():
    ruta = tmp_ruta()
    M.crear(ruta)
    with M.abrir(ruta) as c:
        modo = c.execute("pragma journal_mode").fetchone()[0]
        assert modo.lower() == "wal", f"modo de diario: {modo}, esperaba wal"
        try:
            M.escribir_engrama(c, what=None)  # invalido: what es obligatorio
        except Exception:
            pass
        n = c.execute("select count(*) from engrams").fetchone()[0]
    assert n == 0, "una insercion invalida dejo fila a medias"


# --- criterio 9 · guardrails solo en la frontera --------------------------

@caso("9 · el disco guarda sin redactar; la exportacion sale redactada")
def t9():
    ruta = tmp_ruta()
    M.crear(ruta)
    sensible = "mi token es clave-secreta-de-prueba y lo necesito entero"
    with M.abrir(ruta) as c:
        M.escribir_engrama(c, what=sensible)
    # Los bytes se leen FUERA del bloque: con diario WAL la fila vive en el
    # fichero -wal hasta que la conexion cierra y consolida. Leerlo dentro
    # miraba el fichero equivocado, no probaba nada sobre la redaccion.
    crudo = b"".join(open(ruta + s, "rb").read()
                     for s in ("", "-wal") if os.path.exists(ruta + s))
    assert b"clave-secreta-de-prueba" in crudo, \
        "el disco no guarda el texto tal cual: se redacto al escribir"
    with M.abrir(ruta) as c:
        salida, hallazgos = M.exportar(c, redactor=redactor_de_prueba)
    assert "clave-secreta-de-prueba" not in salida, "la exportacion no redacto"
    assert "[API_KEY]" in salida, "no aparece la marca de redaccion"
    assert hallazgos == [{"policy": "API_KEY", "count": 1}], \
        f"hallazgos mal formados: {hallazgos}"
    assert all(set(h) == {"policy", "count"} for h in hallazgos), \
        "un hallazgo lleva mas campos que policy y count"


@caso("9b · exportar sin redactor falla cerrado: no devuelve texto")
def t9b():
    ruta = tmp_ruta()
    M.crear(ruta)
    with M.abrir(ruta) as c:
        M.escribir_engrama(c, what="algo")
        fallo = False
        try:
            M.exportar(c, redactor=None)
        except M.FronteraSinFiltro:
            fallo = True
        assert fallo, "exportar sin redactor devolvio texto en vez de bloquear"


@caso("9c · exportar con redactor que falla bloquea limpio")
def t9c():
    # 9b cubre el filtro AUSENTE. Este cubre el filtro PRESENTE Y ROTO, que es
    # el caso real: guardrails.py existe pero su policies.json esta corrupto o
    # falta. Sin esto la excepcion del redactor se propaga tal cual: el export
    # no devuelve texto, pero el fallo sale como traza de un modulo interno en
    # vez de como frontera cerrada, y quien lo lea no sabe que el filtro es el
    # que se rompio.
    ruta = tmp_ruta()
    M.crear(ruta)
    with M.abrir(ruta) as c:
        M.escribir_engrama(c, what="algo")

        def redactor_roto(texto):
            raise ValueError("policies.json corrupto")

        fallo = False
        try:
            M.exportar(c, redactor=redactor_roto)
        except M.FronteraSinFiltro as e:
            fallo = True
            assert "redaction filter failed" in str(e)
            # El tipo original se conserva en el mensaje: un bloqueo que no
            # dice de que murio el filtro obliga a adivinar en produccion.
            assert "ValueError" in str(e)
        assert fallo, "excepcion del redactor se propago en vez de bloquear"


# --- criterio 10 · hecho con un solo recuerdo -----------------------------

@caso("10 · con UN recuerdo la mision esta completa")
def t10():
    ruta = tmp_ruta()
    M.crear(ruta)
    with M.abrir(ruta) as c:
        M.escribir_engrama(c, what="el unico")
        assert M.mision_completa(c) is True, "un recuerdo no basta y deberia"
        assert M.vista_tabla(c) and M.vista_arbol(c) and M.vista_recuento(c)
    est, rec = M.estado(ruta)
    assert est == "CON_DATOS" and rec["engrams"] == 1


@caso("10b · con cero recuerdos la mision NO esta completa")
def t10b():
    ruta = tmp_ruta()
    M.crear(ruta)
    with M.abrir(ruta) as c:
        assert M.mision_completa(c) is False


# --- modo sabotaje · el rojo tambien se prueba ----------------------------
# Una suite verde solo demuestra que el codigo pasa la suite. Que la suite
# DETECTE la rotura es otra afirmacion distinta, y hasta ahora se comprobo a
# mano una sola vez: un gesto que no queda registrado en ninguna parte y que
# nadie repite. Este modo lo vuelve mecanica.
#
# Por cada invariante: se copia el arbol a un directorio temporal, se rompe la
# invariante EN LA COPIA, se corre la suite contra esa copia y se exige que
# falle. El modulo original no se toca nunca; su sha256 se compara al cerrar.
#
# Si la suite pasa con una invariante rota, ESE es el fallo: el test no vale.

RAIZ = os.path.dirname(os.path.abspath(__file__))

# (nombre, fichero, ancla exacta, sustitucion). El ancla debe aparecer UNA vez:
# un ancla que no aplica produciria una copia sana, una suite verde y la
# conclusion falsa de "invariante no detectada". Se verifica antes de romper.
SABOTAJES = (
    (
        "ausencia declarada · NO_DATA deja de escribirse",
        "memory.py",
        '    return AUSENTE if v is None or str(v).strip() == "" else v',
        '    return "" if v is None or str(v).strip() == "" else v',
    ),
    (
        "frontera cerrada · exportar sin filtro devuelve texto",
        "memory.py",
        '    if redactor is None:\n'
        '        raise FronteraSinFiltro(\n'
        '            "export blocked: no redaction filter provided. "\n'
        '            "Nothing leaves this machine unfiltered.")',
        '    if redactor is None:\n'
        '        def redactor(t):\n'
        '            return t, []',
    ),
    (
        "diario WAL · se desactiva",
        "memory.py",
        '        con.execute("pragma journal_mode=wal")',
        '        con.execute("pragma journal_mode=delete")',
    ),
)


def _sha256(ruta):
    return hashlib.sha256(open(ruta, "rb").read()).hexdigest()


def _copia_del_arbol():
    """Copia de trabajo, siempre bajo un temporal recien creado."""
    destino = os.path.join(tempfile.mkdtemp(prefix="sabotaje_m2_"), "arbol")
    shutil.copytree(RAIZ, destino,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"))
    return destino


def _romper(destino, fichero, ancla, sustitucion):
    """Aplica la rotura en la copia. Devuelve None, o el motivo del rechazo."""
    ruta = os.path.join(destino, fichero)
    with open(ruta, encoding="utf-8") as f:
        fuente = f.read()
    veces = fuente.count(ancla)
    if veces != 1:
        return (f"el ancla aparece {veces} veces en {fichero}; el codigo cambio "
                "y este sabotaje ya no rompe nada")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(fuente.replace(ancla, sustitucion))
    return None


def _lineas_rojas(salida):
    return [l.strip() for l in salida.splitlines()
            if l.lstrip().startswith(("FALLO ·", "ERROR ·"))]


def main_sabotaje():
    print("── M2 · MODO SABOTAJE · se EXIGE que la suite se ponga roja " + "─" * 7)
    print(f"   original: {RAIZ}")
    print("   se rompe una copia temporal; el original no se toca\n")
    huella_antes = {f: _sha256(os.path.join(RAIZ, f))
                    for f in ("memory.py", "aurelius.py")}
    no_detectados = []

    for nombre, fichero, ancla, sustitucion in SABOTAJES:
        destino = _copia_del_arbol()
        try:
            motivo = _romper(destino, fichero, ancla, sustitucion)
            if motivo is not None:
                no_detectados.append((nombre, motivo))
                print(f"  SIN ROMPER · {nombre}\n               -> {motivo}")
                continue
            r = subprocess.run(
                [sys.executable, os.path.join(destino, os.path.basename(__file__))],
                cwd=destino, capture_output=True, text=True)
            if r.returncode == 0:
                no_detectados.append(
                    (nombre, "la suite quedo VERDE con la invariante rota"))
                print(f"  NO DETECTADO · {nombre}")
                print("                 -> la suite quedo VERDE con la invariante rota")
                continue
            print(f"  roja  · {nombre}")
            for l in _lineas_rojas(r.stdout):
                print(f"          detectado por: {l}")
            ultima = [l for l in r.stdout.strip().splitlines() if l.startswith("RESULTADO")]
            print(f"          {ultima[-1] if ultima else 'sin linea RESULTADO'}"
                  f" (exit {r.returncode})")
        finally:
            shutil.rmtree(os.path.dirname(destino), ignore_errors=True)

    huella_despues = {f: _sha256(os.path.join(RAIZ, f)) for f in huella_antes}
    intacto = huella_antes == huella_despues
    print(f"\nMODULO ORIGINAL {'INTACTO' if intacto else 'ALTERADO'} "
          f"(sha256 memory.py {huella_despues['memory.py'][:16]}…)")
    if not intacto:
        print("  CRITICO: el modo sabotaje escribio en el arbol original")

    total = len(SABOTAJES)
    print(f"\nRESULTADO SABOTAJE: {total - len(no_detectados)}/{total} roturas detectadas")
    for nombre, motivo in no_detectados:
        print(f"  NO DETECTADA · {nombre}\n                 -> {motivo}")
    if no_detectados:
        print("\n  PARADA: una invariante rota que la suite no ve significa que ese")
        print("  test no vale. Hay que reescribirlo antes de seguir.")
    return 1 if (no_detectados or not intacto) else 0


# --- corredor -------------------------------------------------------------

def main():
    fallos = 0
    print("── M2 · EL AGUA · DIEZ CRITERIOS " + "─" * 34)
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
