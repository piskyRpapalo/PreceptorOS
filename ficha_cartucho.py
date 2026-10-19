"""Compact, non-visual language/math card carried by a building label."""
from __future__ import annotations

import re

import estado_compacto

ESQUEMA = "preceptoros.ficha_cartucho/1"
VERBOS = frozenset({"DEPLOY_BUILDING", "QUERY_STATE", "UPDATE_RAG"})
ESTADOS = frozenset({"MEASURED", "STALE", "NO_DATA"})
CAUSAS = frozenset({"sin_sensor", "sin_medicion", "sin_fuente", "sin_firma"})
_ID = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
_UNIDAD = re.compile(r"^[a-zA-Z0-9/_-]{1,16}$")


class FichaInvalida(ValueError):
    pass


def validar(ficha):
    """Validate exact shape and encoded size; return canonical bytes."""
    if type(ficha) is not dict or set(ficha) != {
            "esquema", "verbos", "mesuras", "posturas", "cooldown_ticks", "ram_bytes"}:
        raise FichaInvalida("campos de ficha distintos del contrato")
    if ficha["esquema"] != ESQUEMA:
        raise FichaInvalida("esquema de ficha desconocido")
    verbos = ficha["verbos"]
    if (type(verbos) is not list or not verbos or
            any(type(v) is not str or v not in VERBOS for v in verbos) or
            len(set(verbos)) != len(verbos)):
        raise FichaInvalida("verbos fuera del vocabulario cerrado")
    mesuras = ficha["mesuras"]
    if type(mesuras) is not list or len(mesuras) > 8:
        raise FichaInvalida("mesuras debe ser una lista de hasta ocho datos")
    for m in mesuras:
        if type(m) is not dict or set(m) != {"id", "valor", "unidad", "estado", "causa"}:
            raise FichaInvalida("forma de mesura inválida")
        if type(m["id"]) is not str or not _ID.fullmatch(m["id"]):
            raise FichaInvalida("id de mesura inválido")
        if type(m["unidad"]) is not str or not _UNIDAD.fullmatch(m["unidad"]):
            raise FichaInvalida("unidad de mesura inválida")
        if type(m["estado"]) is not str or m["estado"] not in ESTADOS:
            raise FichaInvalida("estado de mesura inválido")
        if m["estado"] == "MEASURED":
            if type(m["valor"]) not in (int, float) or not isinstance(m["valor"], (int, float)):
                raise FichaInvalida("MEASURED requiere valor numérico")
            if m["causa"] is not None:
                raise FichaInvalida("MEASURED no admite causa")
        else:
            if m["valor"] is not None or type(m["causa"]) is not str or m["causa"] not in CAUSAS:
                raise FichaInvalida("STALE/NO_DATA requiere causa y valor ausente")
    posturas = ficha["posturas"]
    if (type(posturas) is not list or not posturas or len(posturas) > 8 or
            any(type(p) is not str or not _ID.fullmatch(p) for p in posturas) or
            len(set(posturas)) != len(posturas)):
        raise FichaInvalida("posturas inválidas")
    for clave in ("cooldown_ticks", "ram_bytes"):
        valor = ficha[clave]
        techo = 10**9 if clave == "cooldown_ticks" else 2**40
        if type(valor) is not int or not 0 <= valor <= techo:
            raise FichaInvalida(clave + " fuera de rango")
    try:
        return estado_compacto.serializar_objeto(ficha)
    except ValueError as exc:
        raise FichaInvalida(str(exc)) from exc
