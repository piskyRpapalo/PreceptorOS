"""Closed parser for the mini-model's quaternary decision labels.

This parser does not decide meaning or grant authority. It accepts one exact
label from the local model and converts every other output to cause-bearing
NO_DATA. The input envelope remains below the house's 1,024-byte ceiling.
"""
import re

MAX_BYTES = 1024
ETIQUETAS = frozenset({"SI", "NO", "CUANDO"})
CAUSAS = frozenset({"sin_fuente", "motor_no_disponible", "fuera_de_alcance",
                    "ambiguo"})
_NO_DATA = re.compile(r"^NO_DATA:([a-z_]+)$")


def parsear(salida):
    """Parse a model response into SI/NO/CUANDO or cause-bearing NO_DATA."""
    if isinstance(salida, bytes):
        try:
            salida = salida.decode("utf-8", errors="strict")
        except UnicodeError:
            return {"decision": "NO_DATA", "causa": "salida no es UTF-8"}
    if not isinstance(salida, str):
        return {"decision": "NO_DATA", "causa": "salida del modelo no es texto"}
    if len(salida.encode("utf-8")) >= MAX_BYTES:
        return {"decision": "NO_DATA", "causa": "salida alcanza el techo de 1.024 B"}
    if salida in ETIQUETAS:
        return {"decision": salida, "causa": None}
    match = _NO_DATA.fullmatch(salida)
    if match and match.group(1) in CAUSAS:
        return {"decision": "NO_DATA", "causa": match.group(1)}
    return {"decision": "NO_DATA", "causa": "salida fuera del vocabulario cuaternario"}
