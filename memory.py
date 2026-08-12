#!/usr/bin/env python3
"""M2 · el Agua · la memoria de Aurelius.

sistema: MVP · solo biblioteca estandar (python3 + sqlite3).
Un unico fichero .db que la persona se lleva consigo.

Tres invariantes que este modulo no negocia:
  1. Ausente, vacia y con datos son tres estados distintos. Nunca se confunden.
  2. La redaccion ocurre en la FRONTERA (exportar), jamas al escribir en disco.
     La memoria guarda las palabras de la persona tal cual: es su maquina.
  3. Archivar es una columna, no una carpeta. Cero DELETE en este fichero.

Los textos visibles para la persona van en ingles de industria (Canon §4).
Los comentarios y nombres internos, en espanol, porque su lector es el equipo.
"""
from __future__ import annotations

import contextlib
import os
import sqlite3

AUSENTE = "NO_DATA"          # marca visible de ausencia declarada
CAMPOS_HUECO = ("why", "where_ref", "learned")

# El marco, que no es contenido. Donde corre Aurelius y como quiere la persona
# que la llamen no son recuerdos: un recuerdo es algo que le paso y decidio
# escribir. Guardarlos como engramas metería dos filas que nadie escribio en el
# recuento de huecos, y daria la mision por cumplida sin que la persona hubiera
# escrito nada suyo. Por eso viven en una tabla aparte, clave-valor.
CLAVES_PERFIL = ("device", "name")

ESQUEMA = """
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

# Se declara aparte del resto del esquema a proposito: es lo unico que puede
# faltarle a una base creada antes de que el perfil existiera, y es lo unico
# que hace falta anadir. Crear la tabla que falta no es migrar: engrams no se
# toca, no se copia y no se recrea, asi que sus CHECK siguen siendo los suyos.
ESQUEMA_PERFIL = """
create table if not exists profile (
    key        text primary key,
    value      text not null default 'NO_DATA',
    updated_at text not null default (datetime('now'))
);
"""


class FronteraSinFiltro(Exception):
    """Se intento exportar sin filtro de redaccion. Falla cerrado."""


# --- componente 1 · memory_state ------------------------------------------

def estado(ruta):
    """('SIN_ESQUEMA'|'VACIA'|'CON_DATOS', recuentos). Nunca adivina."""
    recuentos = {"engrams": 0, "links": 0, "archivados": 0}
    if not os.path.exists(ruta):
        return "SIN_ESQUEMA", recuentos
    try:
        with abrir(ruta) as c:
            tablas = {r[0] for r in c.execute(
                "select name from sqlite_master where type='table'")}
            if not {"engrams", "links"} <= tablas:
                return "SIN_ESQUEMA", recuentos
            recuentos["engrams"] = c.execute(
                "select count(*) from engrams where status='activo'").fetchone()[0]
            recuentos["archivados"] = c.execute(
                "select count(*) from engrams where status='archivado'").fetchone()[0]
            recuentos["links"] = c.execute("select count(*) from links").fetchone()[0]
    except sqlite3.DatabaseError:
        return "SIN_ESQUEMA", recuentos
    total = recuentos["engrams"] + recuentos["archivados"]
    return ("VACIA" if total == 0 else "CON_DATOS"), recuentos


def mensaje_estado(est, recuentos):
    """Texto visible. Ausente y vacia dicen cosas distintas, a proposito."""
    if est == "SIN_ESQUEMA":
        return ("I have no memory yet. Nothing has been created on this machine. "
                "I can create it now, if you say so.")
    if est == "VACIA":
        return ("My memory exists and it is empty. 0 memories. "
                "Nothing is missing: nothing has been written yet.")
    n, a, l = recuentos["engrams"], recuentos["archivados"], recuentos["links"]
    return (f"{n} memories, {l} links"
            + (f", {a} archived" if a else "")
            + ". Everything shown comes from what you wrote.")


# --- componente 2 · memory_init -------------------------------------------

def crear(ruta):
    """Crea el esquema. Solo se llama tras confirmacion explicita."""
    carpeta = os.path.dirname(os.path.abspath(ruta))
    os.makedirs(carpeta, exist_ok=True)
    with abrir(ruta) as c:
        c.executescript(ESQUEMA + ESQUEMA_PERFIL)
    return ruta


@contextlib.contextmanager
def abrir(ruta):
    """Conexion con diario WAL: un corte de luz no corrompe el fichero."""
    con = sqlite3.connect(ruta)
    con.row_factory = sqlite3.Row
    try:
        con.execute("pragma journal_mode=wal")
        con.execute("pragma foreign_keys=on")
        yield con
        con.commit()
    except BaseException:
        con.rollback()
        raise
    finally:
        con.close()


# --- componente 3 · engram_write ------------------------------------------

def _o_ausente(v):
    """None o cadena vacia -> ausencia DECLARADA, no celda en blanco."""
    return AUSENTE if v is None or str(v).strip() == "" else v


def escribir_engrama(c, what, why=None, where_ref=None, learned="",
                     origin="persona"):
    """Inserta un recuerdo con las palabras de la persona, sin normalizar.
    `what` es obligatorio; el resto puede quedar en NO_DATA y el recuerdo
    sigue siendo valido: un recuerdo sin motivo declarado es informacion."""
    if what is None or str(what).strip() == "":
        raise ValueError("what es obligatorio: un recuerdo sin qué no es un recuerdo")
    cur = c.execute(
        "insert into engrams (what, why, where_ref, learned, origin) "
        "values (?, ?, ?, ?, ?)",
        (what, _o_ausente(why), _o_ausente(where_ref), learned or "", origin))
    return leer_engrama(c, cur.lastrowid)


def leer_engrama(c, ident):
    fila = c.execute("select * from engrams where id=?", (ident,)).fetchone()
    return dict(fila) if fila else None


def escribir_enlace(c, desde, hacia, label=None):
    """La etiqueta es texto libre: las palabras de la persona, no una lista."""
    cur = c.execute(
        "insert into links (from_engram, to_engram, label) values (?, ?, ?)",
        (desde, hacia, _o_ausente(label)))
    return cur.lastrowid


def archivar(c, ident):
    """Sale de la vista por defecto. Sigue en la tabla. No se borra nada."""
    c.execute("update engrams set status='archivado', "
              "updated_at=datetime('now') where id=?", (ident,))


def desarchivar(c, ident):
    c.execute("update engrams set status='activo', "
              "updated_at=datetime('now') where id=?", (ident,))


# --- componente 3b · el perfil --------------------------------------------

def _hay_perfil(c):
    return c.execute("select name from sqlite_master where type='table' "
                     "and name='profile'").fetchone() is not None


def leer_perfil(c, clave=None):
    """Con clave, su valor; sin clave, el perfil entero como diccionario.

    Nunca devuelve celda en blanco ni None: lo que no se contesto sale como
    NO_DATA, igual que en un recuerdo. Y nunca escribe: una base creada antes
    de que el perfil existiera se puede mirar sin que mirarla la modifique.
    """
    if not _hay_perfil(c):
        return AUSENTE if clave else {k: AUSENTE for k in CLAVES_PERFIL}
    guardado = {r["key"]: r["value"] for r in c.execute("select key, value from profile")}
    if clave:
        return guardado.get(clave) or AUSENTE
    perfil = {k: guardado.get(k) or AUSENTE for k in CLAVES_PERFIL}
    for k in sorted(set(guardado) - set(CLAVES_PERFIL)):
        perfil[k] = guardado[k]
    return perfil


def escribir_perfil(c, clave, valor):
    """Guarda una respuesta del perfil. Contestar dos veces corrige en sitio.

    La tabla se crea aqui si falta: es el unico sitio que la necesita, y asi la
    actualizacion del esquema ocurre cuando la persona contesta, no al abrir.
    Corregir es actualizar la fila, no borrarla y volver a escribirla: la regla
    de cero DELETE no tiene una excepcion para cuando es una sola fila.
    """
    if clave is None or str(clave).strip() == "":
        raise ValueError("una clave de perfil vacia no identifica nada")
    # execute y no executescript: executescript confirma lo que hubiera pendiente
    # antes de correr, y aqui no toca decidir por la transaccion de quien llama.
    c.execute(ESQUEMA_PERFIL)
    c.execute("insert into profile (key, value) values (?, ?) "
              "on conflict(key) do update set value=excluded.value, "
              "updated_at=datetime('now')",
              (str(clave).strip(), _o_ausente(valor)))
    return {"key": str(clave).strip(), "value": leer_perfil(c, str(clave).strip())}


# --- componente 4 · memory_view -------------------------------------------

def _filas(c, incluir_archivados=False):
    q = "select * from engrams"
    if not incluir_archivados:
        q += " where status='activo'"
    return [dict(r) for r in c.execute(q + " order by id")]


def vista_perfil(c):
    """Cabecera de una linea: el marco de esta memoria, huecos incluidos.

    Las claves sin contestar se muestran en NO_DATA en vez de esconderse. Una
    cabecera que solo ensenara lo relleno mentiria por omision: nadie echa de
    menos una pregunta que no sabe que existe.
    """
    perfil = leer_perfil(c)
    return "profile · " + " · ".join(f"{k}: {v}" for k, v in perfil.items())


def _con_perfil(c, cuerpo):
    """Toda vista se lee bajo su cabecera: quien es y donde, antes del que."""
    return f"{vista_perfil(c)}\n\n{cuerpo}"


def vista_tabla(c, incluir_archivados=False):
    """Una fila por recuerdo. NO_DATA escrito, nunca celda en blanco."""
    filas = _filas(c, incluir_archivados)
    if not filas:
        return _con_perfil(c, "(no memories yet)")
    cols = ("id", "what", "why", "where_ref", "learned", "origin", "status")
    ancho = {k: max(len(k), *(len(str(f[k]) or "") for f in filas)) for k in cols}
    ancho["what"] = min(ancho["what"], 40)
    ancho["learned"] = min(ancho["learned"], 24)

    def celda(v, k):
        s = AUSENTE if v is None or str(v) == "" else str(v)
        s = s.replace("\n", "\\n").replace("\t", "\\t")
        return (s[:ancho[k] - 1] + "…") if len(s) > ancho[k] else s.ljust(ancho[k])

    cab = " | ".join(k.upper().ljust(ancho[k]) for k in cols)
    sep = "-+-".join("-" * ancho[k] for k in cols)
    cuerpo = "\n".join(" | ".join(celda(f[k], k) for k in cols) for f in filas)
    return _con_perfil(c, f"{cab}\n{sep}\n{cuerpo}")


def vista_arbol(c):
    """Recuerdos como raices; sus enlaces como hijos indentados dos espacios.
    Un recuerdo sin enlaces aparece como raiz suelta, y eso es informacion."""
    filas = {f["id"]: f for f in _filas(c)}
    if not filas:
        return _con_perfil(c, "(no memories yet)")
    enlaces = [dict(r) for r in c.execute("select * from links order by id")]
    hijos = {}
    for e in enlaces:
        hijos.setdefault(e["from_engram"], []).append(e)
    salida = []
    for ident, f in filas.items():
        marca = " [archived]" if f["status"] == "archivado" else ""
        salida.append(f"{f['what']}{marca}")
        for e in hijos.get(ident, []):
            destino = filas.get(e["to_engram"])
            nombre = destino["what"] if destino else AUSENTE
            salida.append(f"  --({e['label']})--> {nombre}")
    return _con_perfil(c, "\n".join(salida))


def recuento_huecos(c):
    """Cuantos campos quedan en NO_DATA. La cifra que mide el avance real."""
    filas = _filas(c)
    rec = {k: 0 for k in CAMPOS_HUECO}
    for f in filas:
        for k in CAMPOS_HUECO:
            if f[k] == AUSENTE or str(f[k]).strip() == "":
                rec[k] += 1
    rec["total"] = sum(rec[k] for k in CAMPOS_HUECO)
    rec["engrams"] = len(filas)
    return rec


def vista_recuento(c):
    r = recuento_huecos(c)
    l = c.execute("select count(*) from links").fetchone()[0]
    lineas = [f"memories: {r['engrams']}", f"links:    {l}", "gaps (NO_DATA):"]
    lineas += [f"  {k:<10} {r[k]}" for k in CAMPOS_HUECO]
    lineas.append(f"  {'total':<10} {r['total']}")
    return _con_perfil(c, "\n".join(lineas))


def mision_completa(c):
    """Con UN recuerdo basta. Si la persona paro en uno, funciono."""
    return c.execute(
        "select count(*) from engrams where status='activo'").fetchone()[0] >= 1


# --- componente 5 · la frontera -------------------------------------------

def exportar(c, redactor=None, incluir_archivados=False):
    """Markdown legible para llevarselo. La redaccion ocurre AQUI y solo aqui.

    `redactor` es la funcion del producto (guardrails): texto -> (texto, hallazgos).
    No se importa ni se copia desde otro arbol: se inyecta.
    Sin redactor NO se devuelve texto. Falla cerrado.
    """
    if redactor is None:
        raise FronteraSinFiltro(
            "export blocked: no redaction filter provided. "
            "Nothing leaves this machine unfiltered.")
    filas = _filas(c, incluir_archivados)
    partes = ["# My memory", "", vista_recuento(c), "", "## Memories", ""]
    for f in filas:
        partes += [f"### {f['what']}",
                   f"- why: {f['why']}",
                   f"- where: {f['where_ref']}",
                   f"- learned: {f['learned'] or AUSENTE}",
                   f"- origin: {f['origin']}", ""]
    enlaces = [dict(r) for r in c.execute("select * from links order by id")]
    if enlaces:
        partes += ["## Links", ""]
        idx = {f["id"]: f["what"] for f in _filas(c, True)}
        for e in enlaces:
            partes.append(f"- {idx.get(e['from_engram'], AUSENTE)} "
                          f"--({e['label']})--> {idx.get(e['to_engram'], AUSENTE)}")
    crudo = "\n".join(partes)
    # Un filtro ausente y un filtro roto son el mismo riesgo: en los dos casos
    # nadie ha redactado el texto. Sin este try la excepcion del redactor se
    # propaga tal cual — el export no devuelve nada, pero el fallo llega como
    # traza de un modulo interno y no como frontera cerrada. Se bloquea con el
    # mismo tipo que la ausencia, conservando la causa con `from e` para que el
    # diagnostico no se pierda.
    try:
        texto, hallazgos = redactor(crudo)
        return texto, hallazgos
    except Exception as e:
        raise FronteraSinFiltro(
            f"export blocked: redaction filter failed ({type(e).__name__}). "
            "Nothing leaves this machine with a broken filter."
        ) from e
