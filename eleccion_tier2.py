"""Valida la forma del tier 2; no ejecuta modelos ni concede autoridad.

Reusa hexelion.eleccion.tier2/1 y p_bp del productor. La probabilidad
normalizada es p_bp/10000. Suma decimal exacta: EPSILON=0; no es un umbral
semántico. La confianza nunca prueba acierto. Tier 1 conserva su contrato.
"""
from fractions import Fraction
import json
import math
import re

ESQUEMA_V = "hexelion.eleccion.tier2/1"
CLIFF = 20
EPSILON = 0
HUELLA = re.compile(r"sha256:[0-9a-f]{64}")
CAMPOS = {"schema_v", "content_v", "choice", "score", "noul", "probs",
          "judge", "arnes", "plan_hash", "no_data"}


def _huella(valor):
    return isinstance(valor, str) and HUELLA.fullmatch(valor) is not None


def _texto(valor):
    return isinstance(valor, str) and bool(valor.strip())


def _finito(valor):
    try:
        return type(valor) in (int, float) and math.isfinite(valor)
    except OverflowError:
        return False


def _calibracion(juez):
    rastro = juez.get("calibracion")
    if not isinstance(rastro, dict) or set(rastro) != {
            "estado", "sha256", "muestras", "aciertos", "causa"}:
        return False
    n, aciertos = rastro["muestras"], rastro["aciertos"]
    if rastro["estado"] == "NO_DATA":
        return (juez["veredicto"] == "NO_DATA" and rastro["sha256"] is None
                and type(n) is int and n == 0 and aciertos is None
                and _texto(rastro["causa"]))
    return (rastro["estado"] in ("MEDIDO", "SIMULATED")
            and _huella(rastro["sha256"]) and type(n) is int and n > 0
            and type(aciertos) is int and 0 <= aciertos <= n
            and (rastro["causa"] is None or _texto(rastro["causa"])))


def validar(e, opciones):
    """Devuelve causas de rechazo; función pura y cerrada, sin reparar la entrada."""
    if not isinstance(e, dict) or set(e) != CAMPOS:
        return ["campos fuera del contrato cerrado"]
    if (not isinstance(opciones, (list, tuple))
            or any(not _texto(o) or o == "NO_DATA" for o in opciones)
            or len(set(opciones)) != len(opciones)):
        return ["opciones: conjunto cerrado sin duplicados"]
    if not 1 <= len(opciones) <= CLIFF and not (
            e["choice"] == "NO_DATA" and e["noul"] is True
            and e["score"] is None and e["probs"] == []):
        return ["cliff: solo abstención sin probabilidades fuera de 1..20 opciones"]
    try:
        json.dumps(e, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        return ["salida no es JSON finito UTF-8"]
    fallos = []
    if e["schema_v"] != ESQUEMA_V:
        fallos.append("schema_v")
    for campo in ("content_v", "plan_hash"):
        if not _huella(e[campo]):
            fallos.append(campo + ": huella requerida")
    if not isinstance(e["choice"], str) or e["choice"] not in [*opciones, "NO_DATA"]:
        fallos.append("choice fuera del conjunto")
    if type(e["noul"]) is not bool or (e["choice"] == "NO_DATA") != e["noul"]:
        fallos.append("noul incoherente")
    if e["score"] is not None and not _finito(e["score"]):
        fallos.append("score no es finito o null")
    if e["noul"] is True and e["score"] is not None:
        fallos.append("abstención exige score=null")
    probs = e["probs"]
    if type(EPSILON) is not int or EPSILON != 0:
        fallos.append("epsilon exacto no declarado")
    if not isinstance(probs, list) or len(probs) > CLIFF:
        fallos.append("probs no es lista acotada")
    elif not probs:
        if e["choice"] != "NO_DATA":
            fallos.append("elección sin probabilidades medidas")
    elif any(not isinstance(p, dict) or set(p) != {"opcion", "p_bp"}
             or not isinstance(p["opcion"], str) or not _finito(p["p_bp"])
             or p["p_bp"] < 0 for p in probs):
        fallos.append("probs mal formadas")
    else:
        if len(probs) != len(opciones) or {p["opcion"] for p in probs} != set(opciones):
            fallos.append("probs duplicadas o incompletas")
        suma = sum((Fraction(str(p["p_bp"])) for p in probs), Fraction(0))
        if suma != 10000:
            fallos.append("probs normalizadas no suman 1 con epsilon=0")
    juez = e["judge"]
    if (not isinstance(juez, dict) or set(juez) != {"veredicto", "contra", "regla", "calibracion"}
            or juez["veredicto"] not in ("acuerdo", "desacuerdo", "NO_DATA")
            or not _texto(juez["contra"]) or not _texto(juez["regla"])
            or not _calibracion(juez)):
        fallos.append("judge: veredicto cerrado y rastro de calibración requeridos")
    arnes = e["arnes"]
    if (not isinstance(arnes, dict) or set(arnes) != {
            "tier", "donde", "modelo", "modo", "hash", "build", "configuracion"}
            or type(arnes["tier"]) is not int or arnes["tier"] != 2
            or arnes["donde"] not in ("local-forja", "local-rack", "EMULADO")
            or arnes["modo"] not in ("puntuar", "generar")
            or not _texto(arnes["modelo"]) or not _huella(arnes["hash"])
            or not _texto(arnes["build"]) or not isinstance(arnes["configuracion"], dict)
            or not arnes["configuracion"]):
        fallos.append("arnes: tier=2, digest, build y configuración requeridos")
    causas = e["no_data"]
    if not isinstance(causas, list) or any(
            not isinstance(c, dict) or set(c) != {"campo", "causa"}
            or not _texto(c["campo"]) or not _texto(c["causa"]) for c in causas):
        fallos.append("no_data: causas tipadas requeridas")
    elif e["choice"] == "NO_DATA" and not causas:
        fallos.append("NO_DATA sin causa")
    return fallos
