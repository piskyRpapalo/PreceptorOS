"""Local, fail-closed app routes for the three bounded building verbs.

The route validates labels and delegates game state to an injected measured
adapter. It does not implement a building/game engine or write to the RAG.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import estado_compacto
import ficha_cartucho
import gramatica_acustica

ESQUEMA = "preceptoros.orquestador/1"
INTENTS = frozenset({"DEPLOY_BUILDING", "QUERY_STATE", "UPDATE_RAG"})
ESTADOS = frozenset({"PROPOSED", "MEASURED", "STALE", "NO_DATA"})
TOPE_B = 1024  # exclusivo: caben como máximo 1.023 bytes UTF-8
ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
TIPOS = frozenset({"boya", "observatorio", "lapidas", "cristal", "botella",
                   "monumento", "vivero", "baliza", "nombres"})
OBLIGATORIOS = {"esquema", "id", "tipo", "col", "fila", "huella",
                "nace_tic", "madura_tics", "desgaste_por_tic", "ficha"}
OPCIONALES = {"caduca_tic", "cuidado_tic", "carga", "escudo"}


class PeticionRechazada(ValueError):
    """Entrada no válida; nunca se procesa por partes."""


def _json_unico(pares):
    salida = {}
    for clave, valor in pares:
        if clave in salida:
            raise PeticionRechazada("clave JSON duplicada")
        salida[clave] = valor
    return salida


def decodificar(raw):
    """Decodifica una petición completa de hasta 1.023 bytes UTF-8."""
    if type(raw) not in (bytes, bytearray):
        raise PeticionRechazada("la petición debe llegar como bytes")
    if len(raw) >= TOPE_B:
        raise PeticionRechazada("paquete de 1.024 B o mayor; rechazo entero")
    try:
        peticion = json.loads(bytes(raw).decode("utf-8", errors="strict"),
                              object_pairs_hook=_json_unico,
                              parse_constant=lambda _: (_ for _ in ()).throw(
                                  PeticionRechazada("número JSON no finito")))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise PeticionRechazada("JSON UTF-8 inválido") from exc
    if (type(peticion) is not dict or set(peticion) !=
            {"esquema", "intent", "payload"}):
        raise PeticionRechazada("forma distinta del contrato cerrado")
    if peticion["esquema"] != ESQUEMA:
        raise PeticionRechazada("esquema de orquestador desconocido")
    if type(peticion["intent"]) is not str or peticion["intent"] not in INTENTS:
        raise PeticionRechazada("verbo fuera del vocabulario cerrado")
    if type(peticion["payload"]) is not dict:
        raise PeticionRechazada("payload debe ser un objeto")
    return peticion


def _manifiesto(m):
    if type(m) is not dict or not OBLIGATORIOS <= set(m) <= OBLIGATORIOS | OPCIONALES:
        return "manifest: fields do not match preceptoros.edificio/1"
    if m.get("esquema") != "preceptoros.edificio/1":
        return "manifest: schema"
    if type(m.get("id")) is not str or not ID.fullmatch(m["id"]):
        return "manifest: id"
    if type(m.get("tipo")) is not str or m.get("tipo") not in TIPOS:
        return "manifest: type"
    if "ficha" not in m:
        return "manifest: language/math card is missing"
    try:
        ficha_cartucho.validar(m["ficha"])
        estado_compacto.serializar_objeto(m)
    except (ficha_cartucho.FichaInvalida, TypeError, ValueError):
        return "manifest: label or language/math card is invalid or reaches 1.024 B"
    rangos = {"col": (-9999, 9999), "fila": (-9999, 9999), "huella": (1, 4),
              "nace_tic": (0, 10**9), "madura_tics": (0, 10**6),
              "desgaste_por_tic": (0, 1000), "carga": (0, 1000),
              "escudo": (0, 1000), "caduca_tic": (0, 10**9),
              "cuidado_tic": (0, 10**9)}
    for campo, (minimo, maximo) in rangos.items():
        if campo not in m or m[campo] is None:
            continue
        n = m[campo]
        if type(n) is not int or not minimo <= n <= maximo:
            return "manifest: " + campo
    for campo in ("caduca_tic", "cuidado_tic"):
        if campo in m and m[campo] is not None and m[campo] < m["nace_tic"]:
            return "manifest: " + campo
    return None


def _respuesta(intent, estado, causa=None, **campos):
    r = {"esquema": ESQUEMA, "intent": intent, "estado": estado,
         "causa": causa, **gramatica_acustica.frase(intent, estado), **campos}
    try:
        raw = estado_compacto.serializar_objeto(r)
    except (TypeError, ValueError, UnicodeError):
        raw = b""
    if len(raw) >= TOPE_B:
        return {"esquema": ESQUEMA, "intent": intent, "estado": "NO_DATA",
                "causa": "respuesta de 1.024 B o mayor; rechazo entero",
                **gramatica_acustica.frase(intent, "NO_DATA")}
    return r


def enrutar(raw, *, raiz=None, leer_estado=None, consultar_rag=None, desde_chat=True):
    """Route one bounded request without embedding game or arena logic."""
    p = decodificar(raw)
    intent, payload = p["intent"], p["payload"]
    if intent == "DEPLOY_BUILDING":
        if set(payload) != {"manifiesto"}:
            return _respuesta(intent, "NO_DATA", "forma DEPLOY_BUILDING inválida")
        manifest = payload.get("manifiesto")
        causa = _manifiesto(manifest)
        if causa:
            return _respuesta(intent, "NO_DATA", causa)
        return _respuesta(intent, "PROPOSED", None, requiere="FIRMO DESPLIEGUE",
                          efecto="none until signed", manifiesto=manifest)
    if intent == "UPDATE_RAG":
        causa = ("UPDATE_RAG is unavailable from chat; no RAG write is performed"
                 if desde_chat else
                 "signed frontera.py RAG adapter is not attached")
        return _respuesta(intent, "NO_DATA", causa)
    if "consulta" in payload:
        if (set(payload) != {"consulta"} or type(payload["consulta"]) is not str
                or not payload["consulta"].strip() or len(payload["consulta"]) > 600):
            return _respuesta(intent, "NO_DATA", "forma de consulta RAG inválida")
        if consultar_rag is None:
            return _respuesta(intent, "NO_DATA", "mini RAG local no está conectado",
                              origen="rag:unavailable")
        try:
            resultado = consultar_rag(payload["consulta"])
        except Exception as exc:
            return _respuesta(intent, "NO_DATA", "consulta RAG falló: " + type(exc).__name__,
                              origen="rag")
        if type(resultado) is not dict or type(resultado.get("estado")) is not str:
            return _respuesta(intent, "NO_DATA", "el adaptador RAG devolvió una forma inválida",
                              origen="rag")
        origen = resultado.get("origen")
        if type(origen) is not str or not origen:
            return _respuesta(intent, "NO_DATA", "la respuesta RAG no declara origen",
                              origen="rag")
        if resultado["estado"] != "MEASURED":
            causa = resultado.get("causa")
            return _respuesta(intent, "NO_DATA", causa if type(causa) is str and causa
                              else "RAG no medido", origen=origen)
        respuesta = resultado.get("respuesta")
        if type(respuesta) is not str or not respuesta.strip():
            return _respuesta(intent, "NO_DATA", "respuesta RAG vacía",
                              origen=origen)
        fuentes = resultado.get("fuentes")
        tokens = resultado.get("tokens_rag_aprox")
        completo = resultado.get("rag_completo")
        if (type(fuentes) is not int or not 1 <= fuentes <= 50
                or type(tokens) is not int or not 0 <= tokens <= 1200
                or type(completo) is not bool):
            return _respuesta(intent, "NO_DATA", "metadatos de recuperación RAG inválidos",
                              origen=origen)
        return _respuesta(intent, "MEASURED", None, origen=origen,
                          respuesta=respuesta.strip(),
                          fuentes=fuentes, tokens_rag_aprox=tokens,
                          rag_completo=completo)
    ident = payload.get("id")
    if set(payload) != {"id"}:
        return _respuesta(intent, "NO_DATA", "forma de consulta de estado inválida")
    if type(ident) is not str or not ID.fullmatch(ident):
        return _respuesta(intent, "NO_DATA", "cartucho id is invalid")
    base = Path(raiz) if raiz is not None else Path.home() / ".preceptoros" / "buildings"
    if base.is_symlink() or not base.is_dir():
        return _respuesta(intent, "NO_DATA", "local buildings directory is unavailable")
    ruta = base / (ident + ".json")
    if ruta.is_symlink() or not ruta.is_file():
        return _respuesta(intent, "NO_DATA", "cartucho manifest is unavailable")
    try:
        manifiesto = json.loads(ruta.read_text(encoding="utf-8"),
                                object_pairs_hook=_json_unico)
    except (OSError, UnicodeError, json.JSONDecodeError, PeticionRechazada):
        return _respuesta(intent, "NO_DATA", "cartucho manifest is invalid")
    causa = _manifiesto(manifiesto)
    if causa:
        return _respuesta(intent, "NO_DATA", causa)
    if leer_estado is None:
        return _respuesta(intent, "NO_DATA", "rack state adapter is not attached",
                          origen="rack:unavailable")
    try:
        lectura = leer_estado(manifiesto)
    except Exception as exc:  # an adapter failure becomes cause-only NO_DATA
        return _respuesta(intent, "NO_DATA", "rack state read failed: " + type(exc).__name__,
                          origen="rack")
    if (type(lectura) is not dict or set(lectura) not in
            ({"estado", "origen", "dato"}, {"estado", "origen", "causa"})
            or not isinstance(lectura.get("origen"), str) or not lectura["origen"]
            or type(lectura.get("estado")) is not str
            or lectura["estado"] not in {"MEASURED", "STALE", "NO_DATA"}):
        return _respuesta(intent, "NO_DATA", "rack adapter returned an invalid observation",
                          origen="rack")
    sello = lectura["estado"]
    if sello == "NO_DATA":
        causa = lectura.get("causa")
        if type(causa) is not str or not causa:
            return _respuesta(intent, "NO_DATA", "rack NO_DATA observation lacks cause",
                              origen=lectura["origen"])
        return _respuesta(intent, "NO_DATA", causa, origen=lectura["origen"])
    if "dato" not in lectura:
        return _respuesta(intent, "NO_DATA", "rack observation has no data",
                          origen=lectura["origen"])
    return _respuesta(intent, sello, None, dato=lectura["dato"], origen=lectura["origen"])
