"""Molde binario S_t v1, separado de la superficie JSON de hasta 1024 bytes.

Offsets inclusivos/exclusivos (enteros big-endian salvo bytes indicados):
  0:4 magic ``PST1``; 4 versión; 5 zona; 6 frescura; 7 flags;
  8:12 tau; 12:16 origen; 16:24 Proof of Tick; 24:40 ID de sesión;
  40:42 Hue; 42 Saturación; 43 Luminosidad; 44:48 carga;
  48:52 confianza; 52:56 escudo; 56:64 edad en tics; 64:72 TTL;
  72:80 nonce secuencial; 80:96 atestación térmica pública;
  96 causa NO_DATA; 97:128 cero reservado; 128:150 ENTROPÍA_TEMPORAL.

Flags: bit 0 niebla/NO_DATA, bit 1 borde ERROR, bit 2 halo STALE,
bit 3 propuesta pendiente de firma humana; bits 4..7 deben ser cero.
Hue/Saturación/Luminosidad y carga/confianza/escudo no son colores ni
autoridad: viajan como datos. Este molde no contiene hashes ni claves.
"""
from types import MappingProxyType

ZONAS = MappingProxyType({
    "mando": 1, "conversacion": 2, "gobierno": 3, "cuaderno": 4,
    "lab": 5, "harness": 6, "puerta": 7, "modelos": 8, "ajustes": 9,
})
FRESCURA = MappingProxyType({"NO_DATA": 0, "LIVE": 1, "STALE": 2})
CAUSAS = MappingProxyType({"sin_tick": 1, "expired": 2, "fuente_no_disponible": 3, "paquete_invalido": 4})
LONGITUD = 150
U32_MAX = (1 << 32) - 1
U64_MAX = (1 << 64) - 1
U176_MAX = (1 << 176) - 1
TAU_MAX = 1_000_000
_CAMPOS = {
    "zona", "frescura", "tau", "origen", "tick", "id_sesion", "hue",
    "saturacion", "luminosidad", "carga", "confianza", "escudo",
    "edad_tics", "ttl_tics", "nonce_secuencial",
    "atestacion_termica_publica", "causa_no_data", "entropia_temporal",
    "propuesta_pendiente_firma", "error",
}
_C_AUSENTE = {valor: clave for clave, valor in CAUSAS.items()}
_ZONA_NOMBRE = {valor: clave for clave, valor in ZONAS.items()}
_FRESCURA_NOMBRE = {valor: clave for clave, valor in FRESCURA.items()}


def _entero(valor, minimo, maximo, campo):
    if type(valor) is not int or not minimo <= valor <= maximo:
        raise ValueError(f"{campo}: fuera de rango")


def _bytes(valor, longitud, campo):
    if type(valor) is not bytes or len(valor) != longitud:
        raise ValueError(f"{campo}: longitud inválida")


def _validar(estado):
    if type(estado) is not dict or set(estado) != _CAMPOS:
        raise ValueError("S_t: campos distintos del molde")
    if type(estado["zona"]) is not str or estado["zona"] not in ZONAS:
        raise ValueError("zona desconocida")
    if type(estado["frescura"]) is not str or estado["frescura"] not in FRESCURA:
        raise ValueError("frescura desconocida")
    _entero(estado["tau"], 0, TAU_MAX, "tau")
    origen = estado["origen"]
    if origen is not None and (type(origen) is not str or origen not in ZONAS):
        raise ValueError("origen desconocido")
    if origen is None and estado["tau"] != 0:
        raise ValueError("sin origen, tau debe ser cero")
    if origen == estado["zona"] and estado["tau"] != TAU_MAX:
        raise ValueError("zona estable requiere tau completo")
    if origen is not None and origen != estado["zona"] and estado["tau"] == TAU_MAX:
        raise ValueError("zona distinta no puede declarar transición terminada")

    tick = estado["tick"]
    if tick is not None:
        _entero(tick, 0, U64_MAX - 1, "tick lógico")
    _bytes(estado["id_sesion"], 16, "id de sesión")
    _bytes(estado["atestacion_termica_publica"], 16, "atestación térmica pública")
    _entero(estado["nonce_secuencial"], 0, U64_MAX, "nonce secuencial")
    _entero(estado["entropia_temporal"], 0, U176_MAX, "entropía temporal")
    if type(estado["propuesta_pendiente_firma"]) is not bool or type(estado["error"]) is not bool:
        raise ValueError("flags de estado deben ser booleanos")

    nivel = estado["frescura"]
    edad, ttl, causa = estado["edad_tics"], estado["ttl_tics"], estado["causa_no_data"]
    if nivel == "LIVE":
        if tick is None or edad != 0 or type(edad) is not int or causa is not None:
            raise ValueError("LIVE requiere Proof of Tick, edad cero y sin causa")
        _entero(ttl, 1, U64_MAX - 1, "TTL en tics")
    elif nivel == "STALE":
        _entero(edad, 1, U64_MAX - 1, "edad en tics")
        _entero(ttl, 1, U64_MAX - 1, "TTL en tics")
        if tick is None or edad >= ttl or causa is not None:
            raise ValueError("STALE requiere edad positiva menor que TTL")
    else:
        if type(causa) is not str or causa not in CAUSAS:
            raise ValueError("NO_DATA requiere causa tipada")
        if causa == "expired":
            _entero(edad, 1, U64_MAX - 1, "edad caducada en tics")
            _entero(ttl, 1, U64_MAX - 1, "TTL en tics")
            if tick is None or edad < ttl:
                raise ValueError("caducidad requiere edad >= TTL y Proof of Tick")
        else:
            if edad is not None or ttl is not None:
                raise ValueError("sin edad válida, edad y TTL deben ser NO_DATA")
            if causa == "sin_tick" and tick is not None:
                raise ValueError("sin_tick no admite tick")

    hsl_metricas = ("hue", "saturacion", "luminosidad", "carga", "confianza", "escudo")
    if nivel == "NO_DATA":
        if any(estado[campo] is not None for campo in hsl_metricas):
            raise ValueError("NO_DATA no admite valores semánticos")
    else:
        _entero(estado["hue"], 0, 359, "Hue")
        _entero(estado["saturacion"], 0, 100, "Saturación")
        _entero(estado["luminosidad"], 0, 100, "Luminosidad")
        for campo in ("carga", "confianza", "escudo"):
            _entero(estado[campo], 0, 1_000_000, campo)


def _u(valor, ancho):
    return valor.to_bytes(ancho, "big")


def codificar(estado):
    """Codifica S_t con offsets fijos, big-endian y rechazo ante cualquier exceso."""
    _validar(estado)
    nivel = estado["frescura"]
    edad = estado["edad_tics"]
    ttl = estado["ttl_tics"]
    causa = estado["causa_no_data"]
    flags = ((nivel == "NO_DATA") | (estado["error"] << 1) |
             ((nivel == "STALE") << 2) | (estado["propuesta_pendiente_firma"] << 3))
    hue = 0xFFFF if nivel == "NO_DATA" else estado["hue"]
    sat = 0xFF if nivel == "NO_DATA" else estado["saturacion"]
    luz = 0xFF if nivel == "NO_DATA" else estado["luminosidad"]
    carga = U32_MAX if nivel == "NO_DATA" else estado["carga"]
    confianza = U32_MAX if nivel == "NO_DATA" else estado["confianza"]
    escudo = U32_MAX if nivel == "NO_DATA" else estado["escudo"]
    edad_wire = U64_MAX if edad is None else edad
    ttl_wire = U64_MAX if ttl is None else ttl
    tick_wire = U64_MAX if estado["tick"] is None else estado["tick"]
    causa_wire = 0 if causa is None else CAUSAS[causa]
    datos = b"".join((
        b"PST1", b"\x01", bytes((ZONAS[estado["zona"]], FRESCURA[nivel], flags)),
        _u(estado["tau"], 4), _u(0 if estado["origen"] is None else ZONAS[estado["origen"]], 4),
        _u(tick_wire, 8), estado["id_sesion"], _u(hue, 2), bytes((sat, luz)),
        _u(carga, 4), _u(confianza, 4), _u(escudo, 4), _u(edad_wire, 8),
        _u(ttl_wire, 8), _u(estado["nonce_secuencial"], 8),
        estado["atestacion_termica_publica"], bytes((causa_wire,)),
        bytes(31), _u(estado["entropia_temporal"], 22),
    ))
    if len(datos) != LONGITUD:
        raise ValueError("S_t no cabe exactamente en 150 bytes")
    return datos


def decodificar(datos):
    """Lee solo el molde v1 completo; ningún byte extra o reservado se tolera."""
    if type(datos) is not bytes or len(datos) != LONGITUD:
        raise ValueError("S_t debe medir exactamente 150 bytes")
    if datos[0:4] != b"PST1" or datos[4] != 1:
        raise ValueError("magic o versión de S_t no reconocidos")
    if datos[7] & 0xF0 or any(datos[97:128]):
        raise ValueError("bits reservados de S_t deben ser cero")
    zona = _ZONA_NOMBRE.get(datos[5])
    frescura = _FRESCURA_NOMBRE.get(datos[6])
    if zona is None or frescura is None:
        raise ValueError("código de zona o frescura inválido")
    origen_code = int.from_bytes(datos[12:16], "big")
    origen = None if origen_code == 0 else _ZONA_NOMBRE.get(origen_code)
    if origen_code and origen is None:
        raise ValueError("código de origen inválido")
    flags = datos[7]
    causa = _C_AUSENTE.get(datos[96]) if datos[96] else None
    if datos[96] and causa is None:
        raise ValueError("código NO_DATA inválido")
    no_data = frescura == "NO_DATA"
    hsl_metricas = (
        int.from_bytes(datos[40:42], "big"), datos[42], datos[43],
        int.from_bytes(datos[44:48], "big"), int.from_bytes(datos[48:52], "big"),
        int.from_bytes(datos[52:56], "big"),
    )
    ausentes = (0xFFFF, 0xFF, 0xFF, U32_MAX, U32_MAX, U32_MAX)
    if no_data != (hsl_metricas == ausentes):
        raise ValueError("sentinelas semánticos no coinciden con frescura")
    if bool(flags & 0b0001) != no_data or bool(flags & 0b0100) != (frescura == "STALE"):
        raise ValueError("niebla o halo no coinciden con frescura")
    tick_wire = int.from_bytes(datos[16:24], "big")
    edad_wire = int.from_bytes(datos[56:64], "big")
    ttl_wire = int.from_bytes(datos[64:72], "big")
    estado = {
        "zona": zona, "frescura": frescura,
        "tau": int.from_bytes(datos[8:12], "big"), "origen": origen,
        "tick": None if tick_wire == U64_MAX else tick_wire,
        "id_sesion": datos[24:40],
        "hue": None if no_data else hsl_metricas[0],
        "saturacion": None if no_data else hsl_metricas[1],
        "luminosidad": None if no_data else hsl_metricas[2],
        "carga": None if no_data else hsl_metricas[3],
        "confianza": None if no_data else hsl_metricas[4],
        "escudo": None if no_data else hsl_metricas[5],
        "edad_tics": None if edad_wire == U64_MAX else edad_wire,
        "ttl_tics": None if ttl_wire == U64_MAX else ttl_wire,
        "nonce_secuencial": int.from_bytes(datos[72:80], "big"),
        "atestacion_termica_publica": datos[80:96],
        "causa_no_data": causa,
        "entropia_temporal": int.from_bytes(datos[128:150], "big"),
        "propuesta_pendiente_firma": bool(flags & 0b1000),
        "error": bool(flags & 0b0010),
    }
    _validar(estado)
    return estado
