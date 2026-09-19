#!/usr/bin/env python3
"""apretar.py · comprimir contexto SIN poder alterarlo, y demostrarlo.

EL PROBLEMA
-----------
El contexto que viaja a un modelo local es caro dos veces: ocupa ventana --- y
la ventana medida de este nodo es 32768, no los 262K de la ficha --- y se paga
a 248 tok/s de prompt. `turnos.ctx_fuera` cuenta los engramas que NO cupieron:
cada uno es un dato que la recuperacion encontro y el presupuesto tiro.

Comprimir suena a la salida obvia. Y es la trampa obvia: casi toda compresion
de texto es una REESCRITURA, y una reescritura puede cambiar el sentido sin que
nada lo avise. Un resumen que dice «el nodo tiene GPU» donde el original decia
«el nodo NO tiene GPU» ocupa menos y miente.

LA REGLA QUE HACE ESTO SEGURO, y es una sola
---------------------------------------------
**Apretar solo puede BORRAR unidades enteras. Nunca reescribir una.**

De ahi sale la garantia fuerte, y es comprobable con una cuenta en vez de con
un juicio: si toda unidad de la salida esta LITERALMENTE en la entrada,
entonces ninguna frase se invento. No hace falta un modelo que juzgue si el
sentido cambio; hace falta un `in`.

Lo que la regla NO garantiza --- y se dice, porque callarlo seria el mismo
defecto ---: borrar una unidad entera SI puede cambiar el sentido del conjunto.
Por eso encima va el verificador.

EL VERIFICADOR · `intacto()`
-----------------------------
Tres comprobaciones, las tres deterministas:

  1 · nada NUEVO      toda unidad de la salida esta literal en la entrada
  2 · nada de CIFRAS  `cifras.cantidades()` de la entrada sobrevive entera.
                      Se reusa el sensor que ya existe en vez de escribir otro
                      regex: el dia que cambie la definicion de cantidad,
                      cambia en un sitio.
  3 · nada de ANCLAS  rutas, tags de modelo, mayusculas-identificador y urls
                      sobreviven. Son lo que hace util un engrama: si se va
                      `~/.preceptoros/memory.db`, se fue el dato.

Si falla cualquiera, `apretar()` NO devuelve texto apretado: devuelve el
original y una causa. Rechazo con causa, que es lo que hace esta casa con todo
lo que no puede garantizar.

Solo biblioteca estandar.
"""
from __future__ import annotations

import re

import cifras

# Una unidad es un parrafo, y si no hay parrafos, una linea. Se parte por lo
# mas grueso que exista porque borrar media idea es peor que no borrar nada.
_PARRAFOS = re.compile(r"\n\s*\n")

# LAS ANCLAS. No es un intento de lista completa de «cosas importantes» --- esa
# lista no existe ---, es la lista de lo que, si desaparece, convierte un
# engrama en una frase bonita: donde vive algo, como se llama exactamente, y a
# donde se va a buscarlo.
ANCLA = re.compile(
    r"(?:[~./][\w./\-]{3,})"              # rutas: ~/x, ./x, /etc/x
    r"|(?:\b[\w.\-]+:[\w.\-]{2,}\b)"      # tags de modelo: qwen3-coder:30b
    r"|(?:https?://\S+)"                  # urls
    r"|(?:\b[A-Z][A-Z0-9_]{3,}\b)")       # identificadores en mayusculas


def unidades(texto):
    """El texto partido por lo mas grueso que tenga. Nunca por palabras."""
    t = (texto or "").strip()
    if not t:
        return []
    trozos = [p.strip() for p in _PARRAFOS.split(t) if p.strip()]
    if len(trozos) > 1:
        return trozos
    return [l.strip() for l in t.splitlines() if l.strip()]


def _clave(u):
    """Dos unidades son la misma si solo se diferencian en espacios y caja."""
    return re.sub(r"\s+", " ", u).strip().lower()


def anclas(texto):
    return set(ANCLA.findall(texto or ""))


def intacto(original, apretado):
    """(ok, faltan). `faltan` es una lista de cadenas legibles, no pares."""
    faltan = []
    for u in unidades(apretado):
        if u not in original:
            faltan.append(f"unidad que no estaba en el original: {u[:60]!r}")
    perdidas = cifras.cantidades(original) - cifras.cantidades(apretado)
    faltan += [f"cifra perdida: {n} {u}" for n, u in sorted(perdidas)]
    faltan += [f"ancla perdida: {a}"
               for a in sorted(anclas(original) - anclas(apretado))]
    return not faltan, faltan


def apretar(texto, tope_unidades=None):
    """Devuelve (texto, informe). Si no se puede garantizar, devuelve el original.

    `tope_unidades` recorta por el FINAL y por unidades enteras. No hay recorte
    a media frase: una frase cortada por la mitad es una unidad nueva, y una
    unidad nueva rompe la comprobacion 1 --- que es justo lo que esa
    comprobacion existe para impedir.
    """
    us = unidades(texto)
    if not us:
        return texto or "", {"estado": "NO_DATA", "causa": "texto vacio",
                             "unidades": 0, "quitadas": 0, "bytes_antes": 0,
                             "bytes_despues": 0}
    vistas, quedan, motivos = set(), [], []
    for u in us:
        k = _clave(u)
        if k in vistas:
            motivos.append("duplicada")
            continue
        # Contenida en una que ya esta: el texto entero vuelve a aparecer mas
        # arriba, asi que borrarla no quita informacion.
        if any(k in _clave(v) for v in quedan):
            motivos.append("contenida")
            continue
        vistas.add(k)
        quedan.append(u)
    recortadas = 0
    if tope_unidades is not None and len(quedan) > tope_unidades:
        recortadas = len(quedan) - tope_unidades
        quedan = quedan[:tope_unidades]

    salida = "\n\n".join(quedan)
    ok, faltan = intacto(texto, salida)
    informe = {
        "estado": "OK" if ok else "RECHAZADO",
        "unidades": len(us), "quitadas": len(us) - len(quedan),
        "duplicadas": motivos.count("duplicada"),
        "contenidas": motivos.count("contenida"),
        "recortadas_por_tope": recortadas,
        "bytes_antes": len(texto or ""), "bytes_despues": len(salida),
    }
    if not ok:
        # RECHAZO CON CAUSA, y se devuelve el ORIGINAL. Devolver el apretado
        # «avisando» seria peor que no comprimir: quien llama ya tiene la
        # respuesta en la mano y el aviso viaja en otro campo que puede no
        # leerse. Aqui el valor que se devuelve ES la decision.
        informe["causa"] = faltan[:6]
        informe["bytes_despues"] = len(texto or "")
        return texto or "", informe
    informe["ahorro"] = (round(100 * (1 - len(salida) / len(texto)), 1)
                         if texto else 0.0)
    return salida, informe


def presupuesto(textos, tope_bytes):
    """Cuantas piezas caben enteras en el presupuesto, y cuantas se quedan fuera.

    ES LA CUENTA DE `ctx_fuera`, hecha explicita. Devuelve `(dentro, fuera)`.
    No parte ninguna pieza: media pieza no es contexto, es ruido con formato.
    """
    dentro, fuera, gastado = [], [], 0
    for t in textos:
        apretado, _ = apretar(t)
        coste = len(apretado) + 2
        if gastado + coste <= tope_bytes:
            dentro.append(apretado)
            gastado += coste
        else:
            fuera.append(t)
    return dentro, fuera
