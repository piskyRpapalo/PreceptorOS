#!/usr/bin/env python3
"""proyectos.py · lo que la persona tiene entre manos. **Solo stdlib.**

QUÉ ES Y QUÉ NO
---------------
Nació como un cuaderno de accesos rápidos --un título y una ruta-- y desde el
2026-09-04 es lo que su nombre decía: los proyectos de quien usa esto. Un libro
a medias, una aplicación que se está montando, una idea que vuelve cada semana.

**No es un gestor de tareas y no quiere serlo.** No hay fechas límite, no hay
prioridades y no hay porcentajes de avance. Un proyecto personal que te
persigue con una fecha deja de ser tuyo; esto solo recuerda que existe y en qué
punto lo dejaste. La única presión que ejerce es la de estar escrito.

Tampoco es un gestor de ficheros: la `ruta` sigue ahí para las entradas que ya
la tenían, se muestra si está y nunca se exige. No copia, no mueve, no borra
nada del disco.

DÓNDE VIVE
----------
En la misma memoria que todo lo demás, con migración aditiva, como `captura`.
Un segundo fichero para once filas sería una segunda cosa que respaldar, que
restaurar y que perder.
"""
from __future__ import annotations

import os
import sqlite3

ESQUEMA_PROYECTOS = """
create table if not exists proyectos (
    id      integer primary key autoincrement,
    cuando  text not null default (datetime('now')),
    titulo  text not null,
    ruta    text not null default 'NO_DATA',
    nota    text not null default 'NO_DATA'
);
"""

# Columnas que llegaron después. Se añaden una a una y sin tocar las que ya
# estaban: una memoria escrita antes de hoy tiene que abrirse igual, con sus
# proyectos viejos dentro y sin perder una línea.
COLUMNAS_NUEVAS = (
    ("descripcion", "text not null default 'NO_DATA'"),
    ("estado", "text not null default 'activo'"),
    ("actualizado", "text not null default ''"),
)

# Vocabulario cerrado, y por el mismo motivo que el del avatar: un estado que
# se acepta tal cual llega es un campo de texto libre con nombre de enumeración,
# y la interfaz acaba pintando lo que le manden.
ESTADOS = ("activo", "pausado", "completado")

LARGO_MAX = 500
# La nota es el sitio de pensar en voz alta, así que no cabe en 500. Sigue
# habiendo tope: sin él, un pegado accidental mete un fichero entero en la fila.
LARGO_NOTA = 8000


def asegurar(c):
    """Crea la tabla si falta y le añade lo que le falte. Aditivo, nunca destructivo."""
    c.executescript(ESQUEMA_PROYECTOS)
    tiene = {f[1] for f in c.execute("pragma table_info(proyectos)")}
    for nombre, tipo in COLUMNAS_NUEVAS:
        if nombre not in tiene:
            c.execute(f"alter table proyectos add column {nombre} {tipo}")
    # `actualizado` vacío en una fila vieja no es un hueco que declarar: es que
    # nunca se editó. Se siembra con su fecha de creación, que es la verdad.
    c.execute("update proyectos set actualizado = cuando where actualizado = ''")


def _estado(valor):
    """Fuera del vocabulario no hay estado: hay None, y quien llama decide."""
    v = (valor or "").strip().lower()
    return v if v in ESTADOS else None


def anadir(c, titulo, ruta="", nota="", descripcion="", estado="activo"):
    """Devuelve el id, o None. Un título vacío no es una entrada."""
    titulo = (titulo or "").strip()
    if not titulo or len(titulo) > LARGO_MAX:
        return None
    est = _estado(estado)
    if est is None:
        return None
    try:
        asegurar(c)
        cur = c.execute(
            "insert into proyectos (titulo, ruta, nota, descripcion, estado, actualizado)"
            " values (?, ?, ?, ?, ?, datetime('now'))",
            (titulo, (ruta or "NO_DATA").strip()[:LARGO_MAX],
             (nota or "NO_DATA").strip()[:LARGO_NOTA],
             (descripcion or "NO_DATA").strip()[:LARGO_NOTA], est))
        return cur.lastrowid
    except sqlite3.Error:
        return None


def editar(c, pid, **campos):
    """Cambia lo que se le pase y sella la fecha. Lo que no se pasa no se toca.

    Se escribe así --y no con un `set` de los cinco campos-- porque la interfaz
    guarda el estado con un toque y el texto con un botón, en momentos distintos.
    Un guardado que reescribe los cinco campos cada vez convierte cualquier
    pantalla a medio rellenar en un borrado silencioso de lo que había.
    """
    asegurar(c)
    if not isinstance(pid, int):
        return False
    trozos, valores = [], []
    if "titulo" in campos:
        t = (campos["titulo"] or "").strip()
        if not t or len(t) > LARGO_MAX:
            return False
        trozos.append("titulo = ?"); valores.append(t)
    if "estado" in campos:
        est = _estado(campos["estado"])
        if est is None:
            return False
        trozos.append("estado = ?"); valores.append(est)
    for campo, tope in (("descripcion", LARGO_NOTA), ("nota", LARGO_NOTA),
                        ("ruta", LARGO_MAX)):
        if campo in campos:
            v = (campos[campo] or "").strip()[:tope]
            trozos.append(f"{campo} = ?"); valores.append(v or "NO_DATA")
    if not trozos:
        return False
    trozos.append("actualizado = datetime('now')")
    valores.append(pid)
    try:
        return c.execute(
            f"update proyectos set {', '.join(trozos)} where id = ?",
            valores).rowcount == 1
    except sqlite3.Error:
        return False


def quitar(c, pid):
    """Se borra la entrada, no el fichero. La ruta apuntaba; no era dueña."""
    asegurar(c)
    return c.execute("delete from proyectos where id = ?", (pid,)).rowcount == 1


def listar(c):
    """Las entradas, y si su ruta sigue estando.

    `existe` se mira AQUÍ y se devuelve como dato, para que la interfaz lo
    enseñe sin adivinar. Una ruta que ya no está no se borra sola: la persona
    decide si la arregla o la quita.
    """
    asegurar(c)
    fuera = []
    for pid, cuando, titulo, ruta, nota, desc, estado, actualizado in c.execute(
            "select id, cuando, titulo, ruta, nota, descripcion, estado, actualizado"
            " from proyectos order by actualizado desc, id desc"):
        real = os.path.expanduser(ruta) if ruta and ruta != "NO_DATA" else ""
        fuera.append({
            "id": pid, "cuando": cuando, "titulo": titulo,
            "ruta": ruta, "nota": nota,
            "descripcion": desc, "estado": estado,
            "actualizado": actualizado,
            "existe": bool(real) and os.path.exists(real),
        })
    return fuera


def recuento(c):
    """Cuántos hay, y cuántos de cada estado. La cifra sola no dice nada: tres
    proyectos activos y tres completados son dos situaciones distintas."""
    asegurar(c)
    total = c.execute("select count(*) from proyectos").fetchone()[0]
    por_estado = {e: 0 for e in ESTADOS}
    for est, n in c.execute("select estado, count(*) from proyectos group by estado"):
        if est in por_estado:
            por_estado[est] = n
    return {"proyectos": total, "por_estado": por_estado}
