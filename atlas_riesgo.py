import json


ESQUEMA_RIESGO = "atlas.riesgo/1"
MAX_BYTES_PAQUETE = 1024
CAMPOS_RIESGO = frozenset({"threat", "vector", "fence", "evidence", "status"})
SELLOS_RIESGO = frozenset({"LIVE", "STALE", "STATIC", "SIMULATED", "NO_DATA", "ERROR"})


class RiesgoRechazado(ValueError):
    pass


def _objeto_unico(pares):
    resultado = {}
    for clave, valor in pares:
        if clave in resultado:
            raise RiesgoRechazado("clave JSON duplicada")
        resultado[clave] = valor
    return resultado


def _constante_rechazada(_valor):
    raise RiesgoRechazado("valor JSON no finito")


def validar_riesgo(crudo):
    if type(crudo) is not bytes:
        raise RiesgoRechazado("el paquete debe ser bytes")
    if len(crudo) >= MAX_BYTES_PAQUETE:
        raise RiesgoRechazado("el paquete alcanza 1.024 B; rechazo íntegro")
    try:
        paquete = json.loads(
            crudo.decode("utf-8", errors="strict"),
            object_pairs_hook=_objeto_unico,
            parse_constant=_constante_rechazada,
        )
    except (UnicodeError, json.JSONDecodeError) as error:
        raise RiesgoRechazado("el paquete debe ser JSON UTF-8 válido") from error
    if type(paquete) is not dict or set(paquete) != CAMPOS_RIESGO:
        raise RiesgoRechazado("la forma no coincide con atlas.riesgo/1")
    for campo in CAMPOS_RIESGO:
        if type(paquete[campo]) is not str:
            raise RiesgoRechazado(f"{campo} debe ser texto")
        if not paquete[campo]:
            raise RiesgoRechazado(f"{campo} no puede estar vacío")
    if paquete["status"] not in SELLOS_RIESGO:
        raise RiesgoRechazado("sello desconocido")
    return paquete
