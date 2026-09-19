#!/usr/bin/env python3
# Frente E · la clave de tema, el Juez de Conflictos y el Cahier que ya estaba.
# sistema: MVP · solo biblioteca estandar.
#
# Lo que estas pruebas vigilan, y por que cada una:
#
#  · La migracion parte de una base con el esquema VIEJO y CON DATOS DENTRO.
#    Migrar una base recien creada no prueba lo que duele: el caso que rompe
#    es el de la memoria que ya tiene recuerdos y no vuelve a pasar por
#    `crear()` nunca mas.
#  · El Cahier NO se duplica. `que/por_que/donde/aprendido` YA son
#    `what/why/where_ref/learned`. Dos sitios para lo mismo acaban diciendo
#    cosas distintas.
#  · Cerrar una contradiccion exige una CIFRA. Es la regla de
#    `bandeja_firmas.md` puesta en el esquema en vez de en la buena voluntad.
from __future__ import annotations

import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memory as M  # noqa: E402

VIEJO = """
create table engrams (
    id integer primary key autoincrement,
    what text not null, why text not null default 'NO_DATA',
    where_ref text not null default 'NO_DATA',
    learned text not null default '',
    origin text not null default 'persona',
    status text not null default 'activo',
    created_at text not null default (datetime('now')),
    updated_at text not null default (datetime('now')));
"""


def _base_vieja():
    ruta = os.path.join(tempfile.mkdtemp(prefix="frente_e_"), "memoria.db")
    c = sqlite3.connect(ruta)
    c.executescript(VIEJO)
    c.execute("insert into engrams (what, why) values (?,?)",
              ("el rack genera 16,1 tok/s agregados", "medido 2026-09-19"))
    c.commit()
    c.close()
    return ruta


def _migrada():
    ruta = _base_vieja()
    M.crear(ruta)
    return ruta


def test_la_migracion_no_pierde_recuerdos():
    ruta = _migrada()
    with sqlite3.connect(ruta) as c:
        n = c.execute("select count(*) from engrams").fetchone()[0]
    assert n == 1, f"habia 1 recuerdo y quedan {n}"


def test_una_base_vieja_gana_topic_key():
    ruta = _migrada()
    with sqlite3.connect(ruta) as c:
        cols = {r[1] for r in c.execute("PRAGMA table_info(engrams)")}
    assert "topic_key" in cols, "sin topic_key el Juez no puede ni empezar"


def test_nacen_las_dos_tablas_del_frente_e():
    ruta = _migrada()
    with sqlite3.connect(ruta) as c:
        t = {r[0] for r in c.execute(
            "select name from sqlite_master where type='table'")}
    assert {"topic_keys", "contradicciones"} <= t, f"faltan: {{'topic_keys','contradicciones'}} - {t}"


def test_el_cahier_no_se_duplico():
    """Cuatro columnas en castellano al lado de las cuatro inglesas serian dos
    sitios donde escribir lo mismo. El mapeo se documenta; el esquema no."""
    ruta = _migrada()
    with sqlite3.connect(ruta) as c:
        cols = {r[1] for r in c.execute("PRAGMA table_info(engrams)")}
    assert {"what", "why", "where_ref", "learned"} <= cols, "falta el Cahier ingles"
    gemelas = {"que", "por_que", "donde", "aprendido"} & cols
    assert not gemelas, f"se duplico el Cahier: {gemelas}"


def test_dos_cifras_del_mismo_tema_dejan_fila_pendiente():
    ruta = _migrada()
    with sqlite3.connect(ruta) as c:
        c.execute("insert into topic_keys (clave, etiqueta) values (?,?)",
                  ("rack.throughput", "velocidad agregada del rack"))
        c.execute("update engrams set topic_key='rack.throughput' where id=1")
        c.execute("insert into engrams (what, why, topic_key) values (?,?,?)",
                  ("el rack genera 5 tok/s agregados", "de memoria, sin medir",
                   "rack.throughput"))
        pares = c.execute(
            "select a.id, b.id from engrams a join engrams b "
            "on a.topic_key = b.topic_key and a.id < b.id "
            "where a.topic_key is not null and a.what <> b.what").fetchall()
        for a, b in pares:
            c.execute("insert into contradicciones (clave, engrama_a, engrama_b)"
                      " values ('rack.throughput', ?, ?)", (a, b))
        n = c.execute("select count(*) from contradicciones "
                      "where veredicto='pendiente'").fetchone()[0]
    assert n == 1, f"el choque no se anoto: {n} filas pendientes"


def test_no_se_elige_ganador_solo():
    """La fila nace `pendiente`, no resuelta. Elegir cual de los dos vale es
    inventar un veredicto, y eso lo hace el carbono."""
    ruta = _migrada()
    with sqlite3.connect(ruta) as c:
        c.execute("insert into topic_keys (clave) values ('t')")
        c.execute("insert into contradicciones (clave, engrama_a, engrama_b) "
                  "values ('t', 1, 1)")
        v = c.execute("select veredicto from contradicciones").fetchone()[0]
    assert v == "pendiente", f"nacio como {v!r} en vez de pendiente"


def test_un_veredicto_inventado_lo_rechaza_el_esquema():
    ruta = _migrada()
    try:
        with sqlite3.connect(ruta) as c:
            c.execute("insert into topic_keys (clave) values ('t')")
            c.execute("insert into contradicciones (clave, engrama_a, engrama_b,"
                      " veredicto) values ('t', 1, 1, 'inventado')")
    except sqlite3.IntegrityError:
        return
    raise AssertionError("el CHECK dejo pasar un veredicto que no existe")


def test_cerrar_con_una_palabra_no_deja_medida():
    """`medida` nace en NO_DATA: cerrar sin tocarla se ve. No se puede impedir
    con un CHECK sin bloquear tambien a las filas recien nacidas, asi que lo
    que se garantiza es que la ausencia SE NOTA."""
    ruta = _migrada()
    with sqlite3.connect(ruta) as c:
        c.execute("insert into topic_keys (clave) values ('t')")
        c.execute("insert into contradicciones (clave, engrama_a, engrama_b) "
                  "values ('t', 1, 1)")
        c.execute("update contradicciones set veredicto='resuelta' where id=1")
        m = c.execute("select medida from contradicciones where id=1").fetchone()[0]
    assert m == "NO_DATA", f"una resuelta sin medida deberia decir NO_DATA, dice {m!r}"


def test_cerrar_con_cifra_queda_registrado():
    ruta = _migrada()
    with sqlite3.connect(ruta) as c:
        c.execute("insert into topic_keys (clave) values ('t')")
        c.execute("insert into contradicciones (clave, engrama_a, engrama_b) "
                  "values ('t', 1, 1)")
        c.execute("update contradicciones set veredicto='resuelta', "
                  "medida='RESUELTO · 16,1 tok/s medidos C=1,2,4,8', "
                  "cerrado=datetime('now') where id=1")
        v, m, cer = c.execute("select veredicto, medida, cerrado from "
                              "contradicciones where id=1").fetchone()
    assert v == "resuelta" and cer, "no quedo cerrada"
    assert any(ch.isdigit() for ch in m), f"cerrada sin una cifra: {m!r}"


CASOS = [(f.__name__[5:].replace("_", " "), f) for f in (
    test_la_migracion_no_pierde_recuerdos,
    test_una_base_vieja_gana_topic_key,
    test_nacen_las_dos_tablas_del_frente_e,
    test_el_cahier_no_se_duplico,
    test_dos_cifras_del_mismo_tema_dejan_fila_pendiente,
    test_no_se_elige_ganador_solo,
    test_un_veredicto_inventado_lo_rechaza_el_esquema,
    test_cerrar_con_una_palabra_no_deja_medida,
    test_cerrar_con_cifra_queda_registrado,
)]


def main():
    fallos = 0
    print("── FRENTE E · TEMA, CONFLICTO Y CAHIER " + "─" * 28)
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
    sys.exit(main())
