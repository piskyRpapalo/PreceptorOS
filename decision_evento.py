"""Valida decisiones de canal sin autoridad; recuperado del adaptador local."""
import hashlib
import json
import re
from datetime import datetime
SLUG=re.compile(r"^[a-z0-9][a-z0-9-]{0,60}$")
def _canonico(cuerpo):
    return json.dumps(cuerpo,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")
SELLOS_EVENTO = {"MEDIDO", "EMULADO", "NO_DATA", "PROPUESTA", "REQUIERE_FIRMA", "DECLARADO"}

ROLES_DECISION = {"agente", "carbono", "mesa", "navegante", "preceptor"}

CLAVES_DECISION = {"v", "rol", "alternativas", "eleccion", "encargo_ref", "firmo_ref",
                   "sello", "ancla", "utc"}

REF_ENCARGO = re.compile(r"^(?:issue:[1-9][0-9]*|sha256:[0-9a-f]{64})$")

REF_FIRMO = re.compile(r"^(?:issue:[1-9][0-9]*#comment-[1-9][0-9]*|sha256:[0-9a-f]{64})$")

REF_ANCLAJE = re.compile(
    r"^(?:(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+:[1-9][0-9]*|issue:[1-9][0-9]*#comment-[1-9][0-9]*)$")

def validar_evento_decision(cuerpo, no_data=None):
    """Valida el evento de canal L4a; no valida ni concede autoridad."""
    if not isinstance(cuerpo, dict) or set(cuerpo) != CLAVES_DECISION:
        return "decision: campos fuera del contrato cerrado"
    try:
        serializado = _canonico(cuerpo)
    except (TypeError, ValueError, UnicodeError, RecursionError):
        return "decision: cuerpo no serializable en UTF-8"
    if type(cuerpo["v"]) is not int or cuerpo["v"] != 1:
        return "decision.v: versión 1 requerida"
    utc = cuerpo["utc"]
    if not isinstance(utc, str) or not re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", utc):
        return "decision.utc: hora declarada UTC requerida"
    try:
        datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return "decision.utc: fecha inválida"
    if not isinstance(cuerpo["rol"], str) or cuerpo["rol"] not in ROLES_DECISION:
        return "decision.rol: rol fuera del vocabulario cerrado"
    opciones = cuerpo["alternativas"]
    if (not isinstance(opciones, list) or not 1 <= len(opciones) <= 20
            or any(not isinstance(x, str) or not x.strip() or len(x.encode("utf-8")) > 64 for x in opciones)
            or len(set(opciones)) != len(opciones)):
        return "decision.alternativas: 1..20 textos únicos de hasta 64 bytes"
    if cuerpo["eleccion"] not in opciones:
        return "decision.eleccion: fuera de alternativas"
    if not isinstance(cuerpo["encargo_ref"], str) or not REF_ENCARGO.fullmatch(cuerpo["encargo_ref"]):
        return "decision.encargo_ref: issue o sha256 requerido"
    if cuerpo["firmo_ref"] is not None and (
            not isinstance(cuerpo["firmo_ref"], str) or not REF_FIRMO.fullmatch(cuerpo["firmo_ref"])):
        return "decision.firmo_ref: referencia de comentario o sha256"
    causas = [] if no_data is None else no_data
    if not isinstance(causas, list) or any(
            not isinstance(x, dict) or set(x) != {"campo", "causa"}
            or not isinstance(x["campo"], str) or not isinstance(x["causa"], str) or not x["causa"].strip()
            for x in causas):
        return "decision.no_data: lista de causas tipadas"
    if cuerpo["firmo_ref"] is None and not any(x["campo"] == "firmo_ref" for x in causas):
        return "decision.firmo_ref: NO_DATA requiere causa"
    if not isinstance(cuerpo["sello"], str) or cuerpo["sello"] not in SELLOS_EVENTO:
        return "decision.sello: fuera del vocabulario del canal"
    if not isinstance(cuerpo["ancla"], str) or not REF_ANCLAJE.fullmatch(cuerpo["ancla"]):
        return "decision.ancla: fichero:linea o issue:comment requerido"
    if any(parte in (".", "..") for parte in cuerpo["ancla"].split(":", 1)[0].split("/")):
        return "decision.ancla: ruta relativa sin ascensos"
    if len(serializado) >= 1024:
        return "decision: cuerpo excede el techo de lectura de 1 KiB"
    return None

def ordenar_decisiones(eventos):
    """Lee el orden local de inserción; UTC no concede orden causal ni autoridad."""
    decisiones = [evento for evento in eventos if evento.get("tipo") == "decision"]
    if any(type(evento.get("n")) is not int or evento["n"] < 1 for evento in decisiones):
        raise ValueError("decision: número de inserción ausente")
    return sorted(decisiones, key=lambda evento: evento["n"])


def recibo_espejo(cuerpo):
    """Devuelve solo forma para una práctica aislada; no abre comunicación A2A."""
    causa = validar_evento_decision(cuerpo)
    if causa:
        raise ValueError(causa)
    return {"estado": "SIMULATED", "codigo": "decision_validada", "recuento": 1,
            "payload_sha256": hashlib.sha256(_canonico(cuerpo)).hexdigest()}


def cotejar_espejos(cuerpo, primero, segundo):
    """Recalcula la huella: dos recibos igualmente falsos no producen acuerdo."""
    try:
        esperado = recibo_espejo(cuerpo)
        return _canonico(primero) == _canonico(segundo) == _canonico(esperado)
    except (ValueError, TypeError, UnicodeError):
        return False
