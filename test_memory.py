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


# --- criterio 3 · va primero, por orden de quien firma ----------------------

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


# --- perfil · quien eres y donde estoy, que NO son recuerdos ---------------
# Dispositivo y nombre no son engramas. Un recuerdo es algo que a la persona le
# paso y decidio escribir; el aparato donde corre Aurelius y como quiere que la
# llamen son el marco, no el contenido. Meterlos en engrams contaminaria el
# recuento de huecos con dos filas que la persona nunca escribio, y la mision
# ("con UN recuerdo basta") se daria por cumplida sola. Tabla aparte.

ESQUEMA_VIEJO = """
create table if not exists engrams (
    id         integer primary key autoincrement,
    what       text not null check (length(trim(what)) > 0),
    why        text not null default 'NO_DATA',
    where_ref  text not null default 'NO_DATA',
    learned    text not null default '',
    origin     text not null default 'persona'
               check (origin in ('persona', 'intencion', 'importado')),
    status     text not null default 'activo'
               check (status in ('activo', 'archivado')),
    created_at text not null default (datetime('now')),
    updated_at text not null default (datetime('now'))
);
create table if not exists links (
    id          integer primary key autoincrement,
    from_engram integer not null references engrams(id),
    to_engram   integer not null references engrams(id),
    label       text not null default 'NO_DATA',
    created_at  text not null default (datetime('now'))
);
"""


@caso("11 · el perfil guarda clave-valor; lo que no se dijo queda en NO_DATA")
def t11():
    ruta = tmp_ruta()
    M.crear(ruta)
    with M.abrir(ruta) as c:
        # Antes de decir nada, el perfil no esta vacio: esta declarado ausente.
        assert M.leer_perfil(c, "device") == M.AUSENTE, "un perfil sin decir no da NO_DATA"
        assert M.leer_perfil(c) == {k: M.AUSENTE for k in M.CLAVES_PERFIL}
        M.escribir_perfil(c, "device", "el portatil de la cocina")
        assert M.leer_perfil(c, "device") == "el portatil de la cocina"
        # El resto sigue ausente: contestar una pregunta no rellena las otras.
        assert M.leer_perfil(c, "name") == M.AUSENTE
        # Enter en la pregunta es ausencia declarada, igual que en un recuerdo.
        M.escribir_perfil(c, "name", "")
        assert M.leer_perfil(c, "name") == M.AUSENTE, "el vacio se guardo como celda en blanco"
        # El perfil no es un recuerdo: no toca engrams ni el recuento.
        assert c.execute("select count(*) from engrams").fetchone()[0] == 0, \
            "el perfil escribio en engrams"
        assert M.mision_completa(c) is False, "el perfil dio la mision por cumplida"


@caso("12 · la cabecera de perfil sale en las TRES vistas, NO_DATA incluido")
def t12():
    ruta = tmp_ruta()
    M.crear(ruta)
    with M.abrir(ruta) as c:
        M.escribir_engrama(c, what="un recuerdo cualquiera")
        M.escribir_perfil(c, "device", "el portatil de la cocina")
        vistas = {"tabla": M.vista_tabla(c), "arbol": M.vista_arbol(c),
                  "recuento": M.vista_recuento(c)}
    for nombre, v in vistas.items():
        assert "el portatil de la cocina" in v, f"la vista {nombre} no lleva el dispositivo"
        # Lo que no se contesto se VE que no se contesto. Una cabecera que solo
        # muestra lo relleno miente por omision: la persona no puede echar de
        # menos una pregunta que nadie le enseño que existia.
        assert M.AUSENTE in v, f"la vista {nombre} esconde la clave sin contestar"


@caso("13 · un esquema viejo se actualiza sin perder ni un recuerdo")
def t13():
    # El caso que protege la memoria REAL que ya existe en disco. Una base
    # creada antes de que el perfil existiera no tiene esa tabla: si el codigo
    # nuevo la exigiera al abrir, o si "actualizar" significara recrear engrams,
    # el primer recuerdo de verdad se perderia. Se exige lo contrario: la tabla
    # aparece sola y engrams no se toca.
    ruta = tmp_ruta("vieja.db")
    con = sqlite3.connect(ruta)
    con.executescript(ESQUEMA_VIEJO)
    con.execute("insert into engrams (what, why) values (?, ?)",
                ("Hoy publique algo que funciona", "es la primera vez"))
    con.commit()
    tablas_antes = {r[0] for r in con.execute(
        "select name from sqlite_master where type='table'")}
    con.close()
    assert "profile" not in tablas_antes, "la base de prueba ya traia perfil: no prueba nada"

    est, rec = M.estado(ruta)
    assert est == "CON_DATOS" and rec["engrams"] == 1, f"la base vieja no se lee: {est}"

    with M.abrir(ruta) as c:
        # Leer no exige la tabla: una base vieja se mira sin escribirle nada.
        assert M.leer_perfil(c, "device") == M.AUSENTE, "leer el perfil rompe en base vieja"
        assert "Hoy publique algo que funciona" in M.vista_tabla(c)
        M.escribir_perfil(c, "device", "la misma maquina de siempre")

    with M.abrir(ruta) as c:
        fila = M.leer_engrama(c, 1)
        assert fila["what"] == "Hoy publique algo que funciona", "el recuerdo cambio"
        assert fila["why"] == "es la primera vez", "el motivo se perdio"
        assert c.execute("select count(*) from engrams").fetchone()[0] == 1, \
            "engrams tiene otro numero de filas tras la actualizacion"
        assert M.leer_perfil(c, "device") == "la misma maquina de siempre"
        # engrams sigue siendo la tabla de antes, con sus CHECK intactos: no se
        # recreo ni se copio. Si se hubiera migrado a mano, esto pasaria.
        fallo = False
        try:
            c.execute("insert into engrams (what, origin) values ('x', 'inventado')")
        except sqlite3.IntegrityError:
            fallo = True
        assert fallo, "los CHECK de engrams se perdieron al actualizar el esquema"


@caso("14 · contestar dos veces corrige en sitio: ni duplica ni borra")
def t14():
    ruta = tmp_ruta()
    M.crear(ruta)
    with M.abrir(ruta) as c:
        M.escribir_perfil(c, "name", "Davi")
        M.escribir_perfil(c, "name", "David")   # se corrige la errata
        assert M.leer_perfil(c, "name") == "David", "la correccion no se guardo"
        n = c.execute("select count(*) from profile where key='name'").fetchone()[0]
    assert n == 1, f"la clave quedo duplicada: {n} filas para el mismo nombre"
    # Cero DELETE tambien aqui: corregir es actualizar, no borrar y volver a
    # escribir. La regla no admite una excepcion "pero si es una sola fila".
    import re
    fuente = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "memory.py"), encoding="utf-8").read()
    sentencias = re.findall(r"delete\s+from\s+\w+", fuente, re.IGNORECASE)
    assert not sentencias, f"memory.py ejecuta DELETE: {sentencias}"


# --- la puerta · durabilidad. Devolver es prometer -------------------------
# El §6.2 del plan —«Saved solo tras commit»— no se prueba mirando la salida:
# un test en la MISMA conexion ve la fila aunque no este confirmada, asi que
# comprobaria exactamente el error. La unica prueba que separa durabilidad de
# visibilidad local es una SEGUNDA conexion.


@caso("15 · la fila es visible desde otra conexion antes de cerrar")
def test_la_fila_es_visible_desde_otra_conexion_antes_de_cerrar():
    ruta = tmp_ruta()
    M.crear(ruta)
    with M.abrir(ruta) as c:
        M.escribir_engrama(c, what="visible desde fuera o no esta escrito")
        # Sin salir del bloque: la sesion de la persona sigue abierta, que es
        # justo el momento en el que el producto ya imprimio "Saved".
        otra = sqlite3.connect(ruta)
        try:
            n = otra.execute("select count(*) from engrams").fetchone()[0]
            dentro = c.execute("select count(*) from engrams").fetchone()[0]
        finally:
            otra.close()
    assert dentro == 1, "ni la propia conexion ve la fila: el insert no corrio"
    assert n == 1, (
        f"otra conexion ve {n} filas: la escritura vive solo en la transaccion "
        "de la sesion. 'Saved' es verdad dentro y mentira fuera")


@caso("16 · la escritura sobrevive a una interrupcion en mitad de la sesion")
def test_la_escritura_sobrevive_a_una_interrupcion():
    ruta = tmp_ruta()
    M.crear(ruta)
    interrumpio = False
    try:
        with M.abrir(ruta) as c:
            M.escribir_engrama(c, what="recuerdo uno")
            M.escribir_engrama(c, what="recuerdo dos")
            # Ctrl+C en "Add another?": para la persona esto no es un fallo,
            # es el modo normal de salir de una conversacion.
            raise KeyboardInterrupt
    except KeyboardInterrupt:
        interrumpio = True
    # La interrupcion tiene que SALIR del bloque. Un gestor que se la traga
    # deja a la persona dentro de una sesion de la que pidio salir.
    assert interrumpio, "abrir() se trago el KeyboardInterrupt en vez de relanzarlo"

    with M.abrir(ruta) as c:      # CONEXION NUEVA: lo unico que prueba disco
        filas = [r["what"] for r in c.execute(
            "select what from engrams order by id")]
    assert filas == ["recuerdo uno", "recuerdo dos"], \
        f"tras la interrupcion quedan {filas}: la sesion entera era una transaccion"


@caso("17 · devolver es prometer: si la escritura devuelve, otra conexion la ve")
def test_saved_no_se_imprime_sin_durabilidad():
    # La invariante en una linea. Se comprueba en los CINCO puntos de escritura,
    # no solo en el primero: un punto sin prueba es un punto que puede volver
    # a prometer sin cumplir.
    ruta = tmp_ruta()
    M.crear(ruta)

    def fuera(sql):
        otra = sqlite3.connect(ruta)
        try:
            return otra.execute(sql).fetchone()[0]
        finally:
            otra.close()

    with M.abrir(ruta) as c:
        fila = M.escribir_engrama(c, what="lo que la persona acaba de escribir")
        assert fuera("select count(*) from engrams where id=%d" % fila["id"]) == 1, \
            "escribir_engrama devolvio la fila y fuera no existe: 'Saved' miente"
        otra_fila = M.escribir_engrama(c, what="la segunda")
        M.escribir_enlace(c, fila["id"], otra_fila["id"], "lleva a")
        assert fuera("select count(*) from links") == 1, \
            "escribir_enlace devolvio y el enlace no esta en disco"
        M.archivar(c, otra_fila["id"])
        assert fuera("select count(*) from engrams where status='archivado'") == 1, \
            "archivar devolvio y el cambio no esta en disco"
        M.desarchivar(c, otra_fila["id"])
        assert fuera("select count(*) from engrams where status='archivado'") == 0, \
            "desarchivar devolvio y el cambio no esta en disco"


@caso("18 · una escritura invalida no arrastra a las validas")
def test_una_escritura_invalida_no_arrastra_a_las_validas():
    ruta = tmp_ruta()
    M.crear(ruta)
    try:
        with M.abrir(ruta) as c:
            M.escribir_engrama(c, what="la primera, valida")
            try:
                M.escribir_engrama(c, what="   ")      # invalida: what vacio
            except ValueError:
                pass
            M.escribir_engrama(c, what="la segunda, valida")
            raise KeyboardInterrupt
    except KeyboardInterrupt:
        pass
    with M.abrir(ruta) as c:
        filas = [r["what"] for r in c.execute(
            "select what from engrams order by id")]
    # Con transaccion de sesion esto perdia las tres: la valida, la invalida y
    # la que vino despues. El rollback solo debe alcanzar a la que fallo.
    assert filas == ["la primera, valida", "la segunda, valida"], \
        f"quedan {filas}: el rollback de una escritura se llevo por delante a las otras"


@caso("19 · el perfil tambien sobrevive: device y name no se evaporan")
def test_el_perfil_tambien_sobrevive():
    ruta = tmp_ruta()
    M.crear(ruta)
    try:
        with M.abrir(ruta) as c:
            M.escribir_perfil(c, "device", "el portatil de la cocina")
            M.escribir_perfil(c, "name", "David")
            raise KeyboardInterrupt
    except KeyboardInterrupt:
        pass
    with M.abrir(ruta) as c:
        assert M.leer_perfil(c, "device") == "el portatil de la cocina", \
            "el dispositivo se evaporo con la interrupcion"
        assert M.leer_perfil(c, "name") == "David", \
            "el nombre se evaporo con la interrupcion"


# --- el respaldo · lo que un `cp` del .db no copia -------------------------

@caso("20 · el respaldo se lleva lo que aun vive en el WAL; un cp del .db no")
def test_el_respaldo_incluye_lo_que_vive_en_el_wal():
    ruta = tmp_ruta()
    M.crear(ruta)
    with M.abrir(ruta) as c:
        M.escribir_engrama(c, what="el recuerdo que el cp perdia")
        M.escribir_perfil(c, "name", "David")
        # Con la sesion ABIERTA, como estaria al hacer el respaldo de verdad.
        ingenuo = ruta + ".cp-solo-db"
        shutil.copyfile(ruta, ingenuo)
        destino, rec = M.respaldar(ruta)

    # El cp del .db a secas: valido, legible y vacio. Es el respaldo que hubo.
    con = sqlite3.connect(ingenuo)
    perdidos = con.execute("select count(*) from engrams").fetchone()[0]
    con.close()
    assert perdidos == 0, \
        (f"el cp del .db ya trae {perdidos} filas: en esta maquina el WAL se "
         "consolido solo y el test no esta midiendo lo que dice medir")

    assert rec["engrams"] == 1 and rec["profile"] == 1, \
        f"el respaldo dice llevar {rec}"
    # Y se comprueba desde fuera, sin pasar por el codigo que lo escribio.
    con = sqlite3.connect(destino)
    filas = [r[0] for r in con.execute("select what from engrams")]
    nombre = con.execute("select value from profile where key='name'").fetchone()
    con.close()
    assert filas == ["el recuerdo que el cp perdia"], f"la copia lleva {filas}"
    assert nombre and nombre[0] == "David", "la copia perdio el perfil"
    # Un solo fichero: si el respaldo dejara su propio -wal fuera, la copia
    # tendria el mismo problema que vino a arreglar.
    assert not os.path.exists(destino + "-wal"), "el respaldo dejo un -wal suelto"


@caso("21 · un respaldo no pisa a otro, y sin memoria no inventa un fichero")
def test_el_respaldo_no_pisa_ni_inventa():
    ruta = tmp_ruta()
    M.crear(ruta)
    with M.abrir(ruta) as c:
        M.escribir_engrama(c, what="algo")
    destino, _ = M.respaldar(ruta)
    fallo = False
    try:
        M.respaldar(ruta, destino)      # el mismo nombre, otra vez
    except FileExistsError:
        fallo = True
    assert fallo, "un respaldo sobrescribio a otro: la copia buena se perdio"

    fallo = False
    try:
        M.respaldar(tmp_ruta("no_existe.db"))
    except FileNotFoundError:
        fallo = True
    assert fallo, "respaldar una memoria que no existe devolvio un fichero"


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
    # --- las tres de la puerta (M-D64) ---------------------------------------
    # La sustitucion no puede ser `con.commit = lambda: None`: el atributo es de
    # solo lectura en sqlite3.Connection. Se anula por subclase, que es la forma
    # exacta de dejar la base como estaba antes del arreglo: las escrituras no
    # confirman y el unico commit real vuelve a ser el del final de la sesion.
    (
        "durabilidad · el commit vuelve al final de abrir()",
        "memory.py",
        '    con = sqlite3.connect(ruta)\n'
        '    con.row_factory = sqlite3.Row\n'
        '    try:\n'
        '        con.execute("pragma journal_mode=wal")\n'
        '        con.execute("pragma foreign_keys=on")\n'
        '        yield con\n'
        '        con.commit()',
        '    class _SoloAlFinal(sqlite3.Connection):\n'
        '        def commit(self):\n'
        '            pass\n'
        '    con = sqlite3.connect(ruta, factory=_SoloAlFinal)\n'
        '    con.row_factory = sqlite3.Row\n'
        '    try:\n'
        '        con.execute("pragma journal_mode=wal")\n'
        '        con.execute("pragma foreign_keys=on")\n'
        '        yield con\n'
        '        sqlite3.Connection.commit(con)',
    ),
    (
        "durabilidad · escribir_engrama devuelve sin confirmar",
        "memory.py",
        '        (what, _o_ausente(why), _o_ausente(where_ref), learned or "", origin))\n'
        '    c.commit()      # durabilidad ANTES de devolver: si se devuelve, esta en disco\n'
        '    return leer_engrama(c, cur.lastrowid)',
        '        (what, _o_ausente(why), _o_ausente(where_ref), learned or "", origin))\n'
        '    return leer_engrama(c, cur.lastrowid)',
    ),
    (
        "salida limpia · la interrupcion se traga en vez de relanzarse",
        "memory.py",
        '    except BaseException:\n'
        '        con.rollback()\n'
        '        raise',
        '    except BaseException:\n'
        '        con.rollback()',
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
