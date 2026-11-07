#!/usr/bin/env python3
"""rendimiento_vista.py · la tabla de rendimiento de la pestaña Harness. **Solo stdlib.**

Lectura pura. Entra lo que devuelve `captura.rendimiento(...)` (una lista de
dicts por modelo x tarea, captura.py:438-470) y sale un documento pequeño que
la app pinta. No abre base de datos, no escribe, no decide nada sobre el modelo:
ordena, nombra y recorta.

Reglas que no se negocian:
* Sin juzgar no es fallado. `juzgados == 0` -> NO_DATA, `tasa` None, causa
  `no_judged_turns`. Jamas 0.
* Tasa baja con contexto fuera alto no es un modelo malo: se anota
  `context_short_not_model` y el estado sigue MEASURED.
* El documento ocupa como mucho 1023 bytes (JSON compacto, UTF-8). Lo que no
  cabe se recorta por el final, y se dice en `no_data`.
* Nunca lanza ante entrada malformada: la fila se omite y se cuenta.
"""

import json

ESQUEMA = "preceptoros.rendimiento-vista/1"
TOPE = 1023
MEASURED = "MEASURED"
NO_DATA = "NO_DATA"


def _real(x):
    """Numero real finito. Un booleano no cuenta como numero."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x == x


def _entero(x):
    return isinstance(x, int) and not isinstance(x, bool) and x >= 0


def _fila(f):
    """Fila de captura -> fila de vista. ValueError si la forma no sirve."""
    if not isinstance(f, dict):
        raise ValueError("no es dict")
    modelo, tarea = f.get("modelo"), f.get("tarea")
    turnos, juzgados = f.get("turnos"), f.get("juzgados")
    tasa, ctx = f.get("tasa"), f.get("ctx_fuera_medio")
    if not (isinstance(modelo, str) and modelo and
            isinstance(tarea, str) and tarea):
        raise ValueError("modelo o tarea")
    if not (_entero(turnos) and _entero(juzgados)):
        raise ValueError("turnos o juzgados")
    if tasa is not None and not (_real(tasa) and 0 <= tasa <= 1):
        raise ValueError("tasa")
    if ctx is not None and not (_real(ctx) and ctx >= 0):
        raise ValueError("ctx_fuera_medio")
    if juzgados == 0:
        estado, tasa_out, causa = NO_DATA, None, "no_judged_turns"
    elif tasa is None:
        estado, tasa_out, causa = NO_DATA, None, "no_rate"
    else:
        estado, tasa_out = MEASURED, round(float(tasa), 3)
        causa = None
        if ctx is not None and ctx > 1.0 and tasa < 0.5:
            causa = "context_short_not_model"
    return {"modelo": modelo, "tarea": tarea, "estado": estado,
            "tasa": tasa_out, "juzgados": juzgados, "turnos": turnos,
            "causa": causa}


def _clave(r):
    t = r["tasa"]
    return (t is None, -t if t is not None else 0, r["modelo"], r["tarea"])


def _doc(filas, no_data):
    return {"esquema": ESQUEMA, "filas": filas, "no_data": no_data}


def _bytes(doc):
    return len(json.dumps(doc, separators=(",", ":"),
                          ensure_ascii=False).encode("utf-8"))


def vista(filas):
    """Documento de la pestaña Harness a partir de las filas de rendimiento."""
    try:
        entrada = list(filas)
    except Exception:  # noqa: BLE001 - entrada no iterable: se trata como vacia
        entrada = []
    if not entrada:
        return _doc([], [{"campo": "rendimiento", "causa": "no_rows"}])
    buenas, malas = [], 0
    for f in entrada:
        try:
            buenas.append(_fila(f))
        except Exception:  # noqa: BLE001 - fila malformada: se omite y se cuenta
            malas += 1
    buenas.sort(key=_clave)
    base_nd = []
    if malas == 1:
        base_nd.append({"campo": "fila", "causa": "malformed_row"})
    elif malas > 1:
        base_nd.append({"campo": "fila", "causa": "malformed_row:%d" % malas})
    k = len(buenas)
    while True:
        nd = list(base_nd)
        if k < len(buenas):
            nd.append({"campo": "filas", "causa": "frame_over_1024"})
        doc = _doc(buenas[:k], nd)
        if k == 0 or _bytes(doc) <= TOPE:
            return doc
        k -= 1
