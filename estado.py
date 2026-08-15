"""Qué hay instalado en esta máquina. No quién eres.

La frontera de este módulo importa: `estado.json` describe la MÁQUINA -- si el
cerebro está, si la voz está, si el ritual se firmó. Tu nombre, tu idioma y tu
ritmo describen a la PERSONA y ya viven en la tabla `profile` de tu memoria.
Guardarlos también aquí crearía dos verdades sobre el mismo hecho, y el día
que difieran no habría forma de saber cuál manda.

Y una regla que gobierna todo el fichero: **esto es una caché, no un canon.**
Dice lo que era cierto cuando se escribió. El disco dice lo que es cierto
ahora. Cuando discrepen, manda el disco.
"""

import json
import os

import casa as _casa

FICHERO = "estado.json"
BANDERAS = ("cerebro_descargado", "voz_descargada", "ritual_firmado")
VACIO = {b: False for b in BANDERAS}


def ruta(base=None):
    return (base or _casa.raiz()) / FICHERO


def leer(base=None):
    """Devuelve las banderas. Lo que falte, se asume False.

    Un fichero corrupto NO es un error fatal ni motivo para volver a descargar
    gigabytes: se trata como ausencia y se reconstruye mirando el disco. Un
    json a medias es exactamente lo que deja un corte de luz a mitad de
    escritura, y castigar a la persona por eso sería castigarla por el fallo
    de otro.
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
    return {b: bool(datos.get(b, False)) for b in BANDERAS}


def escribir(banderas, base=None):
    """Escribe entero o no escribe. Nunca deja medio fichero."""
    base = _casa.asegurar(base)
    destino = ruta(base)
    limpio = {b: bool(banderas.get(b, False)) for b in BANDERAS}
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


def reconciliar(comprobantes, base=None):
    """Corrige las banderas contra el disco y devuelve las que mentían.

    `comprobantes` es {bandera: función sin argumentos que mira el disco}. Se
    llama a cada una y se cree lo que dice, no lo que decía el fichero. Es la
    diferencia entre "recuerdo haberlo descargado" y "está ahí".

    `ritual_firmado` no lleva comprobante y se conserva: no deja huella en
    disco que mirar. Es el único dato de este fichero que solo existe aquí, y
    por eso es el único que se pierde si el fichero se pierde -- y perderlo
    solo cuesta repetir el ritual, no repetir una descarga.
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
