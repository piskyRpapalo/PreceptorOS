"""Qué hay instalado en esta máquina. No quién eres.

La frontera de este módulo importa: `estado.json` describe la MÁQUINA -- si el
cerebro está, si la voz está, si el ritual se firmó, y en qué nivel de
soberanía corre esta instalación. Tu nombre, tu idioma y tu ritmo describen a
la PERSONA y ya viven en la tabla `profile` de tu memoria. Guardarlos también
aquí crearía dos verdades sobre el mismo hecho, y el día que difieran no habría
forma de saber cuál manda.

Y una regla que gobierna todo el fichero: **esto es una caché, no un canon.**
Dice lo que era cierto cuando se escribió. El disco dice lo que es cierto
ahora. Cuando discrepen, manda el disco.

El nivel entra aquí por esa misma frontera: un nivel de soberanía dice qué
puede hacer esta instalación, no quién la usa. Y entra como JSON plano y no en
la memoria de la persona a propósito -- la memoria es suya y viaja con ella; el
permiso es de la máquina y se queda donde está la máquina.
"""

import json
import os

import casa as _casa

FICHERO = "estado.json"
BANDERAS = ("cerebro_descargado", "voz_descargada", "ritual_firmado")

# El nivel de soberanía. No es una bandera: es un entero 0..3, y por eso vive
# separado de `BANDERAS` en vez de colarse en una tupla de booleanos donde
# `True` valdría 1 sin que nadie lo hubiera decidido.
NIVEL = "nivel_soberania"
SANTUARIO = 0
NIVEL_MAXIMO = 3

CLAVES = BANDERAS + (NIVEL,)
VACIO = {**{b: False for b in BANDERAS}, NIVEL: SANTUARIO}

# El botón de pánico que no pasa por la interfaz: un fichero vacío al lado del
# estado. Existe porque una interfaz puede fallar, puede no estar arrancada, o
# puede ser justamente lo que no responde -- y en ese momento tiene que haber
# una forma de cortar con `touch` y nada más. Manda sobre lo que declare el
# JSON, y NO lo reescribe: el interruptor corta la corriente, no cambia el
# cableado. Borrar el centinela devuelve la declaración intacta.
CENTINELA = "MODO_SANTUARIO"


def ruta(base=None):
    return (base or _casa.raiz()) / FICHERO


def ruta_centinela(base=None):
    return (base or _casa.raiz()) / CENTINELA


def _nivel_limpio(valor):
    """Un entero 0..3, y `SANTUARIO` ante cualquier otra cosa.

    Ante la duda se baja, nunca se sube: un nivel ilegible, negativo, fuera de
    rango, escrito como texto o colado como booleano no es un nivel -- es una
    ausencia de dato, y una ausencia de dato jamás concede un permiso.
    """
    if isinstance(valor, bool) or not isinstance(valor, int):
        return SANTUARIO
    if valor < SANTUARIO or valor > NIVEL_MAXIMO:
        return SANTUARIO
    return valor


def leer(base=None):
    """Devuelve lo que DECLARA el fichero. Lo que falte, se asume False o 0.

    Un fichero corrupto NO es un error fatal ni motivo para volver a descargar
    gigabytes: se trata como ausencia y se reconstruye mirando el disco. Un
    json a medias es exactamente lo que deja un corte de luz a mitad de
    escritura, y castigar a la persona por eso sería castigarla por el fallo
    de otro.

    Ojo con el nivel: esto es la DECLARACIÓN, no el nivel en vigor. El
    centinela no se mira aquí. Quien quiera saber qué puede hacerse ahora mismo
    llama a `nivel()`, no a `leer()[NIVEL]`.
    """
    try:
        crudo = ruta(base).read_text(encoding="utf-8")
    except OSError:
        return dict(VACIO)
    try:
        datos = json.loads(crudo)
    except ValueError:
        return dict(VACIO)
    if not isinstance(datos, dict):
        return dict(VACIO)
    leido = {b: bool(datos.get(b, False)) for b in BANDERAS}
    leido[NIVEL] = _nivel_limpio(datos.get(NIVEL, SANTUARIO))
    return leido


def escribir(banderas, base=None):
    """Escribe entero o no escribe. Nunca deja medio fichero.

    Lo que no venga en `banderas` se escribe en su valor seguro: False para las
    banderas, `SANTUARIO` para el nivel. Escribir a medias no puede acabar en
    un permiso que nadie concedió, así que la omisión baja y nunca sube.
    """
    base = _casa.asegurar(base)
    destino = ruta(base)
    limpio = {b: bool(banderas.get(b, False)) for b in BANDERAS}
    limpio[NIVEL] = _nivel_limpio(banderas.get(NIVEL, SANTUARIO))
    parcial = destino.with_suffix(".json.partial")
    texto = json.dumps(limpio, indent=2, sort_keys=True) + "\n"
    with open(parcial, "w", encoding="utf-8") as f:
        f.write(texto)
        f.flush()
        os.fsync(f.fileno())
    os.replace(parcial, destino)
    return limpio


def fijar(clave, valor, base=None):
    """Cambia una bandera y deja el resto como estaba."""
    if clave not in BANDERAS:
        raise KeyError(f"bandera desconocida: {clave}")
    actual = leer(base)
    actual[clave] = bool(valor)
    return escribir(actual, base)


def fijar_nivel(valor, base=None):
    """Declara el nivel de soberanía y deja las banderas como estaban.

    No comprueba el centinela ni lo borra: subir la declaración con el
    centinela puesto es legítimo y no tiene efecto, porque `nivel()` sigue
    devolviendo `SANTUARIO` hasta que el fichero se quite. Son dos gestos
    distintos y se hacen por separado a propósito -- que uno arrastre al otro
    es como se apagan los interruptores sin querer.
    """
    actual = leer(base)
    actual[NIVEL] = _nivel_limpio(valor)
    return escribir(actual, base)


def santuario_forzado(base=None):
    """¿Está puesto el centinela? Ante un disco que no responde, se asume que sí."""
    try:
        return ruta_centinela(base).exists()
    except OSError:
        return True


def nivel(base=None):
    """El nivel EN VIGOR: lo que declara el fichero, salvo que el centinela mande.

    Este es el número que decide qué puede hacerse. `leer()[NIVEL]` es lo que
    hay escrito; esto es lo que rige.
    """
    if santuario_forzado(base):
        return SANTUARIO
    return leer(base)[NIVEL]


def reconciliar(comprobantes, base=None):
    """Corrige las banderas contra el disco y devuelve las que mentían.

    `comprobantes` es {bandera: función sin argumentos que mira el disco}. Se
    llama a cada una y se cree lo que dice, no lo que decía el fichero. Es la
    diferencia entre "recuerdo haberlo descargado" y "está ahí".

    `ritual_firmado` no lleva comprobante y se conserva: no deja huella en
    disco que mirar. Es el único dato de este fichero que solo existe aquí, y
    por eso es el único que se pierde si el fichero se pierde -- y perderlo
    solo cuesta repetir el ritual, no repetir una descarga.

    El nivel tampoco se reconcilia, y por el mismo motivo: no hay nada en el
    disco que delate un permiso firmado. Pasa de largo, intacto.
    """
    antes = leer(base)
    despues = dict(antes)
    for bandera, mira_el_disco in comprobantes.items():
        if bandera not in BANDERAS:
            raise KeyError(f"bandera desconocida: {bandera}")
        despues[bandera] = bool(mira_el_disco())
    mentian = sorted(b for b in BANDERAS if antes[b] != despues[b])
    if mentian:
        escribir(despues, base)
    return despues, mentian
