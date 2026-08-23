#!/usr/bin/env python3
"""proyectos.py · el cuaderno de accesos rápidos. **Solo stdlib.**

QUÉ ES Y QUÉ NO
---------------
Una lista de cosas que la persona quiere volver a encontrar: un título y una
ruta. **No es un gestor de ficheros.** No copia, no mueve, no borra nada del
disco, y no comprueba que la ruta siga existiendo cada vez -- eso convertiría
una lista en un vigilante, y un vigilante que se equivoca da miedo sin motivo.

Lo que sí hace: guardar el par, y decir la verdad cuando la ruta ya no está.

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

LARGO_MAX = 500


def asegurar(c):
    """Crea la tabla si falta. Una memoria anterior a esto no puede reventar."""
    c.executescript(ESQUEMA_PROYECTOS)


def anadir(c, titulo, ruta="", nota=""):
    """Devuelve el id, o None. Un título vacío no es una entrada."""
    titulo = (titulo or "").strip()
    if not titulo or len(titulo) > LARGO_MAX:
        return None
    try:
        asegurar(c)
        cur = c.execute(
            "insert into proyectos (titulo, ruta, nota) values (?, ?, ?)",
            (titulo, (ruta or "NO_DATA").strip()[:LARGO_MAX],
             (nota or "NO_DATA").strip()[:LARGO_MAX]))
        return cur.lastrowid
    except sqlite3.Error:
        return None


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
    for pid, cuando, titulo, ruta, nota in c.execute(
            "select id, cuando, titulo, ruta, nota from proyectos order by id desc"):
        real = os.path.expanduser(ruta) if ruta and ruta != "NO_DATA" else ""
        fuera.append({
            "id": pid, "cuando": cuando, "titulo": titulo,
            "ruta": ruta, "nota": nota,
            "existe": bool(real) and os.path.exists(real),
        })
    return fuera


def recuento(c):
    asegurar(c)
    fila = c.execute("select count(*) from proyectos").fetchone()
    return {"proyectos": fila[0]}
