#!/usr/bin/env python3
# La vista `estudios` · lo que un turno puede ensenar, y lo que no sale de aqui.
# sistema: MVP · solo biblioteca estandar.
#
# La regla que mas sabotajes lleva es la de no exponer texto: una vista que
# ensene `prompt` o `respuesta` acaba copiada en un informe, en un log o en
# `loops.db`, y entonces el texto de una persona vive en un sitio del que no
# puede retirarlo. El texto lo ve su dueno; el laboratorio ve la forma.
from __future__ import annotations

import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import captura as C  # noqa: E402

TEXTO_SECRETO = "mi direccion es la calle de en medio numero trece"


def _base(filas=()):
    """Una memoria nueva con los turnos que se le pidan."""
    ruta = os.path.join(tempfile.mkdtemp(prefix="estudios_"), "m.db")
    c = sqlite3.connect(ruta)
    C.asegurar(c)
    for f in filas:
        cols = ", ".join(f)
        vals = ", ".join("?" for _ in f)
        c.execute(f"insert into turnos ({cols}) values ({vals})", tuple(f.values()))
    c.commit()
    return c


def _uno(**kw):
    base = {"prompt": TEXTO_SECRETO, "respuesta": "no lo se", "consent": 1}
    base.update(kw)
    return base


def estado_de(c, **kw):
    c.execute("delete from turnos")
    f = _uno(**kw)
    c.execute(f"insert into turnos ({', '.join(f)}) values ({', '.join('?' for _ in f)})",
              tuple(f.values()))
    return c.execute("select estado from estudios").fetchone()[0]


# --------------------------------------------------------------- los cuatro --
def test_sin_consentimiento_gana_a_todo():
    """Un turno sin consentimiento no es material de nadie, tenga la correccion
    que tenga. Si otra rama lo adelantara, un dato privado entraria al dataset
    por tener buena pinta."""
    c = _base()
    assert estado_de(c, consent=0, correccion="una respuesta buenisima") == "sin_consentimiento"
    assert estado_de(c, consent=0, tipo="reescritura") == "sin_consentimiento"
    assert estado_de(c, consent=0, veredicto="alucinacion") == "sin_consentimiento"


def test_entrenable_exige_material_de_mejora():
    c = _base()
    assert estado_de(c, correccion="la respuesta buena") == "entrenable"
    assert estado_de(c, tipo="reescritura") == "entrenable"


def test_diagnostico_es_lo_juzgado_sin_mejora():
    c = _base()
    for v in ("fallo", "alucinacion", "no_data", "traspaso", "mudo"):
        assert estado_de(c, veredicto=v) == "diagnostico", v


def test_acierto_sin_mejora_es_control_no_dataset():
    """`acierto` no es entrenable: no hay nada que corregir. Sirve de control."""
    c = _base()
    assert estado_de(c, veredicto="acierto") == "juzgado"


def test_no_data_y_traspaso_no_son_fallos():
    """La doctrina dentro del esquema: callarse bien no es fallar. Se clasifican
    como diagnostico --- material de calibracion --- y NUNCA como error."""
    c = _base()
    assert estado_de(c, veredicto="no_data") == "diagnostico"
    assert estado_de(c, veredicto="traspaso") == "diagnostico"


# ------------------------------------------------------------- el sabotaje --
def test_la_vista_NO_expone_texto_crudo():
    """El sabotaje principal. Se busca el texto EN TODA la fila, columna a
    columna: basta con que una lo devuelva para que la vista sea una fuga."""
    c = _base([_uno(correccion=TEXTO_SECRETO + " corregido")])
    cur = c.execute("select * from estudios")
    nombres = [d[0] for d in cur.description]
    fila = cur.fetchone()
    for nombre, valor in zip(nombres, fila):
        assert TEXTO_SECRETO not in str(valor), f"la columna {nombre} filtra el texto"
    for prohibida in ("prompt", "respuesta", "correccion"):
        assert prohibida not in nombres, f"la vista expone `{prohibida}` en crudo"


def test_los_largos_si_viajan_porque_no_son_el_texto():
    c = _base([_uno(correccion="abc")])
    f = c.execute("select prompt_len, respuesta_len, correccion_len from estudios").fetchone()
    assert f == (len(TEXTO_SECRETO), len("no lo se"), 3), f


def test_fue_corregido_es_si_o_no_no_la_fecha():
    """`corregido` guarda una FECHA. Medir su longitud daria 19 --- los
    caracteres de un datetime --- y ese 19 pareceria un dato."""
    c = _base([_uno(corregido="2026-09-19 20:15:25")])
    assert c.execute("select fue_corregido from estudios").fetchone()[0] == 1
    nombres = [d[0] for d in c.execute("select * from estudios").description]
    assert "corregido_len" not in nombres, "se mide el largo de una fecha"


def test_la_vista_es_determinista():
    """Dos lecturas seguidas dan lo mismo: no depende del reloj ni del orden."""
    c = _base([_uno(), _uno(veredicto="fallo"), _uno(consent=0)])
    a = c.execute("select turno_id, estado from estudios order by turno_id").fetchall()
    b = c.execute("select turno_id, estado from estudios order by turno_id").fetchall()
    assert a == b and len(a) == 3


def test_es_idempotente():
    """`asegurar` se llama en cada apertura. Dos veces no puede fallar ni
    duplicar."""
    c = _base([_uno()])
    C.asegurar(c); C.asegurar(c)
    assert c.execute("select count(*) from estudios").fetchone()[0] == 1
    vistas = c.execute(
        "select count(*) from sqlite_master where type='view' and name='estudios'"
    ).fetchone()[0]
    assert vistas == 1


def test_los_indices_no_cambian_el_conteo():
    c = _base([_uno() for _ in range(7)])
    antes = c.execute("select count(*) from turnos").fetchone()[0]
    C.asegurar(c)
    assert c.execute("select count(*) from turnos").fetchone()[0] == antes == 7
    idx = {r[0] for r in c.execute(
        "select name from sqlite_master where type='index' and sql is not null")}
    assert {"idx_turnos_estudio", "idx_turnos_tiempo_arnes"} <= idx, idx


def test_la_vista_no_escribe_nada():
    """Una vista es de solo lectura por definicion, y se comprueba: el dia que
    alguien la cambie por una tabla, esto se pone rojo."""
    c = _base([_uno()])
    try:
        c.execute("insert into estudios (turno_id) values (999)")
    except sqlite3.OperationalError:
        return
    raise AssertionError("se pudo escribir en la vista")


CASOS = [(f.__name__[5:].replace("_", " "), f) for f in (
    test_sin_consentimiento_gana_a_todo,
    test_entrenable_exige_material_de_mejora,
    test_diagnostico_es_lo_juzgado_sin_mejora,
    test_acierto_sin_mejora_es_control_no_dataset,
    test_no_data_y_traspaso_no_son_fallos,
    test_la_vista_NO_expone_texto_crudo,
    test_los_largos_si_viajan_porque_no_son_el_texto,
    test_fue_corregido_es_si_o_no_no_la_fecha,
    test_la_vista_es_determinista,
    test_es_idempotente,
    test_los_indices_no_cambian_el_conteo,
    test_la_vista_no_escribe_nada,
)]


def main():
    fallos = 0
    print("── LA VISTA DE ESTUDIOS " + "─" * 43)
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
    print(f"\nRESULTADO: {len(CASOS) - fallos}/{len(CASOS)} correctos, {fallos} fallo(s)")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
