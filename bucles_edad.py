"""Edad por bucle del sensor de timers del Nexo. Modelo de lectura puro.

No lee el reloj: quien llama pasa `ahora_s` (segundos epoch). No abre red ni
disco. Lee las filas tal como las reenvia bin/preceptoros-pwa, _harness_leer
(linea 1208): `propios` con `unidad` y `ultima`. La marca de tiempo es `ultima`.

`ultima` llega como texto de systemd ("Sat 2026-11-07 03:11:34 WET", medido en el
sensor del Nexo 2026-11-07). Periodo: `periodo_s` si viene; si no, el que el propio
timer declara (`proxima` - `ultima`); sin ninguno, umbral fijo de 3600 s.
"""

import calendar
import datetime
import json
import math

ESQUEMA = "preceptoros.bucles-edad/1"
TOPE = 1023                 # bytes; la salida debe quedar por debajo de 1024
UMBRAL_SIN_PERIODO = 3600   # segundos
ORDEN = {"stale": 0, "fresh": 1, "NO_DATA": 2}


def _numero(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


# systemd prints "Sat 2026-11-07 03:11:34 WET" (measured on the Nexo sensor, 2026-11-07).
# Parsed with a fixed offset table; an unknown zone is NO_DATA, never a guess. No clock is read.
_ZONAS = {"UTC": 0, "GMT": 0, "WET": 0, "WEST": 3600, "CET": 3600, "CEST": 7200}


def _marca(x):
    """Epoch seconds from a number or a systemd timestamp; None when it cannot be read."""
    if _numero(x):
        return x
    if not isinstance(x, str):
        return None
    partes = x.split()
    if len(partes) != 4 or partes[3] not in _ZONAS:
        return None
    try:
        t = datetime.datetime.strptime(partes[1] + " " + partes[2], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
    return calendar.timegm(t.timetuple()) - _ZONAS[partes[3]]


def _nombre(fila):
    nombre = fila.get("unidad")
    return nombre if isinstance(nombre, str) else ""


def _bucle(fila, ahora_s):
    nombre = _nombre(fila)
    ultima = _marca(fila.get("ultima"))
    if ultima is None:
        return {"nombre": nombre, "edad_s": None, "estado": "NO_DATA", "causa": "no_last_run"}
    edad = ahora_s - ultima
    if edad < 0:
        return {"nombre": nombre, "edad_s": None, "estado": "NO_DATA", "causa": "clock_ahead"}
    periodo = fila.get("periodo_s")
    if not _numero(periodo):
        proxima = _marca(fila.get("proxima"))   # the period the timer itself declares: next minus last
        periodo = proxima - ultima if proxima is not None else None
    umbral = 2 * periodo if _numero(periodo) and periodo > 0 else UMBRAL_SIN_PERIODO
    if edad <= umbral:
        return {"nombre": nombre, "edad_s": edad, "estado": "fresh", "causa": "within_threshold"}
    return {"nombre": nombre, "edad_s": edad, "estado": "stale", "causa": "over_threshold"}


def _marco(bucles, no_data):
    return {"esquema": ESQUEMA, "bucles": bucles, "no_data": no_data}


def _bytes(d):
    return len(json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def _vista(fuente, ahora_s):
    if not isinstance(fuente, dict) or not isinstance(fuente.get("propios"), list):
        return _marco([], [{"campo": "bucles", "causa": "no_source"}])
    sin_reloj = not _numero(ahora_s)
    bucles, no_data = [], []
    for fila in fuente["propios"]:
        if not isinstance(fila, dict):
            no_data.append({"campo": "bucles", "causa": "row_invalid"})
            continue
        if sin_reloj:
            bucles.append({"nombre": _nombre(fila), "edad_s": None, "estado": "NO_DATA", "causa": "no_clock"})
        else:
            bucles.append(_bucle(fila, ahora_s))
    bucles.sort(key=lambda b: (ORDEN[b["estado"]], b["nombre"]))
    marco = _marco(bucles, no_data)
    if _bytes(marco) <= TOPE:
        return marco
    # Recorte desde el final: primero bucles (los NO_DATA caen antes), luego avisos.
    marca = [{"campo": "bucles", "causa": "frame_over_1024"}]
    while bucles or no_data:
        if bucles:
            bucles.pop()
        else:
            no_data.pop()
        marco = _marco(bucles, no_data + marca)
        if _bytes(marco) <= TOPE:
            break
    return marco


def vista(fuente, ahora_s):
    """Devuelve el dict {esquema, bucles, no_data}. Nunca lanza excepcion."""
    try:
        return _vista(fuente, ahora_s)
    except Exception:
        return _marco([], [{"campo": "bucles", "causa": "internal_error"}])
