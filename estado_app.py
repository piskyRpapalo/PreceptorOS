"""Contrato compacto de la superficie de la app; no serializa el vector S_t."""
import json


ESQUEMA = "preceptoros.app.estado/1"
MAX_BYTES = 1024
FUENTE_SEMANTICA = {
    "manifiesto": "assets/herencia-web/indice.json",
    "pin": "config/herencia-web.sha256",
    "semilla": "tabla",
}
ZONAS = frozenset({
    "mando", "conversacion", "gobierno", "cuaderno", "lab",
    "harness", "puerta", "modelos", "ajustes",
})
ESTADOS_FRESCURA = frozenset({"LIVE", "STALE", "NO_DATA"})
ORDEN_GUION = frozenset({"titulo", "zona", "estado", "frescura", "contenido", "acciones"})
_U64_MAX = (1 << 64) - 1
_TAU_MAX = 1_000_000


def _claves(valor, esperadas, nombre):
    if type(valor) is not dict or set(valor) != esperadas:
        raise ValueError(f"{nombre}: conjunto de campos inválido")


def _entero(valor, minimo, maximo, nombre):
    if type(valor) is not int or not minimo <= valor <= maximo:
        raise ValueError(f"{nombre}: entero fuera de molde")


def _texto(valor, max_bytes, nombre):
    if type(valor) is not str or not valor or len(valor.encode("utf-8")) > max_bytes:
        raise ValueError(f"{nombre}: texto fuera de molde")


def validar(estado):
    """Valida superficie y guion; no decide zona ni interpreta sellos.

    ``tick`` es lógico y solo puede venir de Proof of Tick verificado por el
    productor. Este módulo valida su rango; no convierte reloj de pared en
    prueba. H/S/L son datos para lectura de máquina: Hue=vida/recurso/pertenencia,
    Saturación=carga/confianza, Luminosidad=escudo/frescura. La tabla compartida
    interpreta esos datos; este contrato no crea una paleta local. El campo
    ``fuente_semantica`` apunta a la semilla de tabla del manifiesto fijado por
    ``config/herencia-web.sha256``; revisión y bytes se leen desde esa fuente.
    """
    campos = {"esquema", "zona", "transicion", "tick", "frescura", "guion",
              "semantica", "fuente_semantica"}
    _claves(estado, campos, "estado")
    if estado["esquema"] != ESQUEMA:
        raise ValueError("esquema desconocido")
    if type(estado["zona"]) is not str or estado["zona"] not in ZONAS:
        raise ValueError("zona desconocida")
    _claves(estado["fuente_semantica"], set(FUENTE_SEMANTICA), "fuente semántica")
    if estado["fuente_semantica"] != FUENTE_SEMANTICA:
        raise ValueError("la tabla semántica debe venir de la revisión fijada por manifiesto")

    transicion = estado["transicion"]
    _claves(transicion, {"origen", "destino", "tau"}, "transicion")
    if (transicion["origen"] is not None and
            (type(transicion["origen"]) is not str or transicion["origen"] not in ZONAS)):
        raise ValueError("origen desconocido")
    if (type(transicion["destino"]) is not str or transicion["destino"] not in ZONAS or
            transicion["destino"] != estado["zona"]):
        raise ValueError("destino no coincide con la zona declarada")
    _entero(transicion["tau"], 0, _TAU_MAX, "tau")
    if transicion["origen"] == transicion["destino"] and transicion["tau"] != _TAU_MAX:
        raise ValueError("zona en reposo requiere tau completo")

    tick = estado["tick"]
    if tick is not None:
        _entero(tick, 0, _U64_MAX, "tick lógico")

    frescura = estado["frescura"]
    _claves(frescura, {"estado", "edad_tics", "causa"}, "frescura")
    nivel = frescura["estado"]
    edad = frescura["edad_tics"]
    causa = frescura["causa"]
    if type(nivel) is not str or nivel not in ESTADOS_FRESCURA:
        raise ValueError("estado de frescura desconocido")
    if nivel == "LIVE":
        _entero(edad, 0, 0, "edad en tics")
        if tick is None or causa is not None:
            raise ValueError("LIVE requiere tick y edad cero")
    elif nivel == "STALE":
        _entero(edad, 1, _U64_MAX, "edad en tics")
        if tick is None or causa is not None:
            raise ValueError("STALE requiere tick vigente y causa vacía")
    else:
        if edad is not None:
            raise ValueError("NO_DATA no conserva una edad que sugiera frescura")
        _texto(causa, 120, "causa NO_DATA")

    guion = estado["guion"]
    _claves(guion, {"titulo", "orden", "edad_tics"}, "guion")
    _texto(guion["titulo"], 120, "título del guion")
    orden = guion["orden"]
    if type(orden) is not list or not 1 <= len(orden) <= len(ORDEN_GUION):
        raise ValueError("orden de lectura fuera de molde")
    if any(type(item) is not str or item not in ORDEN_GUION for item in orden):
        raise ValueError("elemento de lectura desconocido")
    if len(orden) != len(set(orden)):
        raise ValueError("orden de lectura duplicado")
    if edad is None:
        if guion["edad_tics"] is not None:
            raise ValueError("guion no puede añadir edad sin dato")
    else:
        _entero(guion["edad_tics"], 0, _U64_MAX, "edad del guion en tics")
    if guion["edad_tics"] != edad:
        raise ValueError("la edad en tics del guion debe coincidir con frescura")

    semantica = estado["semantica"]
    _claves(semantica, {"hue", "saturacion", "luminosidad", "niebla", "borde", "halo"}, "semántica")
    niebla = semantica["niebla"]
    if type(niebla) is not bool:
        raise ValueError("niebla debe ser booleana")
    if nivel == "NO_DATA":
        if not niebla or any(semantica[k] is not None for k in ("hue", "saturacion", "luminosidad")):
            raise ValueError("NO_DATA requiere niebla y ausencia de HSL")
        if semantica["halo"] != "normal":
            raise ValueError("NO_DATA no se representa como STALE")
    else:
        if niebla:
            raise ValueError("niebla representa exclusivamente NO_DATA")
        _entero(semantica["hue"], 0, 359, "Hue")
        _entero(semantica["saturacion"], 0, 100, "Saturación")
        _entero(semantica["luminosidad"], 0, 100, "Luminosidad")
        esperado = "STALE" if nivel == "STALE" else "normal"
        if semantica["halo"] != esperado:
            raise ValueError("halo no coincide con la frescura")
    if type(semantica["borde"]) is not str or semantica["borde"] not in {"normal", "ERROR"}:
        raise ValueError("borde semántico desconocido")
    return True


def serializar(estado):
    """Serializa JSON UTF-8 canónico con límite duro de 1024 bytes."""
    validar(estado)
    datos = json.dumps(estado, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False).encode("utf-8")
    if len(datos) > MAX_BYTES:
        raise ValueError("superficie supera 1024 bytes")
    return datos


def _objeto_sin_duplicados(pares):
    salida = {}
    for clave, valor in pares:
        if clave in salida:
            raise ValueError("clave JSON duplicada")
        salida[clave] = valor
    return salida


def deserializar(datos):
    """Acepta solo bytes canónicos del contrato y devuelve su objeto validado."""
    if type(datos) is not bytes or len(datos) > MAX_BYTES:
        raise ValueError("paquete de superficie fuera de tamaño o tipo")
    try:
        texto = datos.decode("utf-8", errors="strict")
        estado = json.loads(texto, object_pairs_hook=_objeto_sin_duplicados,
                            parse_constant=lambda _: (_ for _ in ()).throw(ValueError("constante no JSON")))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("JSON de superficie inválido") from exc
    validar(estado)
    if serializar(estado) != datos:
        raise ValueError("JSON de superficie no canónico")
    return estado
