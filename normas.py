#!/usr/bin/env python3
"""normas.py · el ancla legislativa de cada pieza, en un solo sitio.

**Solo biblioteca estandar. No importa nada del arbol: es una tabla.**

QUE ES ESTO Y POR QUE NO ES UN RENOMBRADO
------------------------------------------
El encargo era «adaptar los nombres a los articulos legislativos para
referencias futuras». Se hace como TABLA y no como renombrado, y la razon esta
en el propio acta de la Notaria: *«el alma de la casa se mantiene, pero se
traduce al idioma de los auditores»*.

Renombrar `frontera` a `perimetro_de_sanitizacion` costaria las dos cosas a la
vez: el vocabulario de la casa --que es marca y que la gente ya usa-- y la
trazabilidad de todo lo escrito hasta hoy, que quedaria hablando de una pieza
con otro nombre. Un renombrado masivo para complacer a un auditor es
exactamente la clase de cambio que rompe mas de lo que arregla.

Con una tabla se tienen las dos: `guardrails.py` sigue llamandose asi, y
`ancla("frontera")` devuelve los articulos que sirve. La cita queda a un grep
de distancia y ninguna sesion futura tiene que recordarla.

LO QUE ESTA TABLA NO AFIRMA
---------------------------
Que una pieza este ANCLADA a un articulo no dice que lo cumpla. Dice que ese
articulo es el que la juzga. La diferencia importa: `COMPLIANCE.md` declara
cinco huecos, y varios de ellos cuelgan de articulos que aparecen aqui. El
ancla senala al juez, no al veredicto.

Y LAS REFERENCIAS LLEVAN VERSION
--------------------------------
El Reglamento (UE) 2024/1689 tiene una numeracion de articulos que ya cambio
entre borradores, y las ISO se revisan. Esto no es un temor abstracto: el mismo
dia que nacio esta tabla, el cruce contra `COMPLIANCE.md` cazo un «art. 52»
--transparencia en el borrador de 2021-- que en el texto publicado es el
art. 50, mientras el 52 paso a ser otra cosa. Una cita heredada de un borrador
tiene el mismo aspecto que una correcta. Cada entrada dice de que texto habla,
para que dentro de dos anos se sepa si la cita envejecio o sigue valiendo. Una
cita legal sin edicion es una cita que nadie puede comprobar.
"""
from __future__ import annotations

import unicodedata

# Las fuentes, con su edicion. Se nombran una vez y se referencian por clave:
# repetir «Reglamento (UE) 2024/1689» en veinte sitios es garantizar que en
# alguno se escriba distinto.
FUENTES = {
    "ai_act": "Reglamento (UE) 2024/1689 (AI Act), texto publicado en el DOUE "
              "el 2024-07-12",
    "27001": "UNE-EN ISO/IEC 27001:2023 · Anexo A (controles de 2022)",
    "42001": "ISO/IEC 42001:2023 · sistema de gestion de IA",
}

# concepto de la casa -> (que es en idioma normativo, [(fuente, referencia)])
#
# El concepto es la CLAVE, no el nombre del fichero, a proposito: una pieza
# puede repartirse en varios ficheros --y `guardrails` ya lo hizo-- sin que la
# tabla tenga que enterarse.
ANCLAS = {
    "frontera": (
        "Perimetro de sanitizacion y gobernanza de datos",
        [("ai_act", "art. 10"), ("27001", "A.8.10"), ("27001", "A.8.12")],
    ),
    "santuario": (
        "Mecanismo de interrupcion de emergencia y supervision humana",
        [("ai_act", "art. 14")],
    ),
    "linea": (
        "Registro de eventos y trazabilidad · proteccion de registros",
        [("ai_act", "art. 12"), ("ai_act", "art. 19"),
         ("27001", "A.5.33"), ("27001", "A.8.15"), ("42001", "8.3")],
    ),
    "memoria": (
        "Registro de trazabilidad local (audit trail)",
        [("ai_act", "art. 12"), ("42001", "8.3")],
    ),
    "soberania": (
        "Autonomia del operador y control de la infraestructura",
        [("27001", "A.5.19"), ("27001", "A.5.21")],
    ),
    "afinado": (
        "Adaptacion de modelo y gestion de sesgos",
        [("ai_act", "art. 10"), ("42001", "6.1.2")],
    ),
    "no_data": (
        "Transparencia y comunicacion de la incertidumbre",
        [("ai_act", "art. 50"), ("ai_act", "art. 13")],
    ),
    "contrato_visual": (
        "Validacion humana en el bucle (HITL) y sellado de salida",
        [("ai_act", "art. 14"), ("42001", "9.2")],
    ),
    "sello_soberano": (
        "Evidencia de conformidad verificable por un tercero",
        [("ai_act", "art. 12"), ("27001", "A.5.33")],
    ),
    "fuga_del_museo": (
        "Concienciacion en ciberseguridad y privacidad",
        [("27001", "A.6.3")],
    ),
    "caracter": (
        "Perfil de comportamiento y limites de interaccion",
        [("ai_act", "art. 50")],
    ),
    "brujula": (
        "Evaluacion de impacto y madurez en el uso de IA",
        [("42001", "6.1.4")],
    ),
}


# --- EL LEXICO DE LA CASA · el negativo del molde ---------------------------
#
# Los nombres que YA existen. Se declaran aqui por una razon que costo dinero
# el 2026-09-08: en una sola jornada invente dos nombres para cosas que la casa
# ya nombraba --«Barra de Tiempo» donde se dice BARRA DEL CORTE, y «Acta de
# Revision» donde no habia nombre y por tanto no me tocaba ponerlo--. Ninguna
# prueba pudo verlo porque una prueba no sabe que palabras estaban ya cogidas.
#
# La regla del molde, con las palabras del Soberano: *«las paredes son el
# negativo; el cristal fundido llena el hueco sin tocarlas. Lo que no este aqui
# y haga falta se propone como DEUDA o como entrada nueva firmada, nunca como
# hecho. Un hueco declarado vale mas que una pared movida a escondidas.»*
#
# Consecuencia practica, y es la que evita la proxima invencion: si algo
# necesita nombre y no esta en esta lista, hay DOS salidas legitimas -- usar el
# termino del texto legal que lo juzga (por eso `ANCLAS` esta justo arriba), o
# dejarlo apuntado como deuda para que lo nombre el carbono. Inventarlo no es
# una de las dos.
LEXICO = (
    "hub", "loratelier", "forja", "rack", "nodo soberano",
    "la puerta", "la aduana", "el sello", "libro de pruebas",
    "barra del corte", "brujula", "atajo", "brida", "peldano",
    "hilo", "cicatriz", "santuario", "arnes", "expansion", "ecosistema",
    "modo_santuario", "huella soberana", "second-brain", "mecanico",
    "enjambre", "ventana", "pliegue", "linea", "cera", "cristal",
)

# Lo que cada nombre de la casa senala, cuando no es evidente. Solo se anota lo
# que se sabe: un glosario que adivina es peor que uno corto.
DONDE = {
    "la puerta": "empieza_aqui.py",
    "la aduana": "guardrails.py + output_guard.py",
    "el sello": "el manifiesto",
    "linea": "linea.py",
    "huella soberana": "huella.py",
    "modo_santuario": "soberania.py::modo_santuario",
    "peldano": "M0-M7, los peldanos del camino",
    "santuario": "nivel 0 de soberania",
    "arnes": "nivel 1 de soberania",
    "expansion": "nivel 2 de soberania",
    "ecosistema": "nivel 3 de soberania",
    "mecanico": "etapa 1 del Artesano",
}


def es_de_la_casa(nombre):
    """¿Esta palabra ya existe en el vocabulario? Comparacion sin tildes.

    Se normaliza sin acentos y sin articulo porque el lexico se escribe de dos
    maneras --«la Aduana» y «Aduana»-- y un guardian que distinga las dos deja
    pasar justo la variante que no se escribio.
    """
    def pelar(s):
        s = unicodedata.normalize("NFD", str(s or "").strip().lower())
        s = "".join(c for c in s if unicodedata.category(c) != "Mn")
        for art in ("el ", "la ", "los ", "las "):
            if s.startswith(art):
                s = s[len(art):]
        return s
    return pelar(nombre) in {pelar(x) for x in LEXICO}


def ancla(concepto):
    """(nombre normativo, [citas legibles]) de un concepto de la casa.

    Devuelve None si el concepto no esta anclado, y eso es informacion: dice
    que nadie decidio todavia que articulo lo juzga. Inventarle uno para que la
    tabla quede completa seria la version legal de rellenar un hueco con una
    estimacion.
    """
    e = ANCLAS.get(str(concepto or "").strip().lower())
    if not e:
        return None
    nombre, refs = e
    return nombre, [f"{FUENTES[f].split(' ·')[0].split(',')[0]} {r}"
                    for f, r in refs]


def citas(concepto):
    """Solo las citas cortas, para pegar en una tabla o en una respuesta."""
    e = ANCLAS.get(str(concepto or "").strip().lower())
    if not e:
        return []
    etiqueta = {"ai_act": "AI Act", "27001": "ISO 27001", "42001": "ISO 42001"}
    return [f"{etiqueta[f]} {r}" for f, r in e[1]]


def anclados_por(fuente, referencia=None):
    """Los conceptos que cuelgan de una fuente, o de un articulo concreto.

    Es la consulta que hace un auditor y no la que hace un programador: llega
    con «art. 12» en la mano y quiere saber que mira en este sistema.
    """
    salida = []
    for concepto, (nombre, refs) in sorted(ANCLAS.items()):
        for f, r in refs:
            if f == fuente and (referencia is None or r == referencia):
                salida.append((concepto, nombre))
                break
    return salida
