#!/usr/bin/env python3
"""El filtro `lector`: elige una pieza de LORE.md y la entrega tal cual.

sistema: MVP · solo biblioteca estandar.

Este modulo existe por una medida, no por gusto. Se probo pedirle la historia
al modelo pequeno y se la invento; se probo darsela para que la resumiera y
aprendio a imitar la etiqueta e inventarse el bloque cuando faltaba. La
conclusion esta en ARQUETIPO.md §3b: la historia la pega el programa.

Por eso aqui no hay modelo. Hay un fichero revisado, una eleccion por palabras,
y la pieza entregada LITERAL. Si ninguna encaja, no se anade nada: un parrafo
forzado es peor que ninguno.
"""
from __future__ import annotations

import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
RUTA = os.path.join(AQUI, "LORE.md")

# Que palabras hacen pertinente cada pieza. Se busca en la pregunta Y en la
# respuesta: a veces el tema real solo aparece en lo que Preceptor contesto.
CLAVES = {
    "El libro que no era para nadie": (
        "diario", "cuaderno", "escribir", "escrib", "para mi", "privado",
        "journal", "notebook", "write", "private"),
    "Una cosa, bien hecha": (
        "programa", "comando", "terminal", "tuberia", "tubería", "unix",
        "pipe", "command", "process", "proceso"),
    "Un formato que promete durar": (
        "fichero", "archivo", "formato", "base de datos", "sqlite", "abrir",
        "file", "format", "database", "open"),
    "La copia que se guarda lejos": (
        "copia", "respaldo", "perder", "perdido", "backup", "lose", "lost",
        "otro sitio", "elsewhere", "usb", "disco", "disk"),
    "Reparar es un derecho que hubo que pelear": (
        "reparar", "arreglar", "abrir la maquina", "repair", "fix", "own",
        "alquil", "rent"),
    "Texto plano, que sobrevive a sus programas": (
        "texto plano", "plain text", "txt", "markdown", "editor", "word"),
    "El estorbo es el camino": (
        "error", "fallo", "roto", "no funciona", "bug", "broken", "fail",
        "depurar", "debug", "atasc", "stuck"),
    "Lo que no se midió, no se sabe": (
        "rapido", "rápido", "lento", "medir", "medida", "cuanto tarda",
        "fast", "slow", "measure", "benchmark", "latencia", "latency"),
}


def piezas(ruta=None):
    """{titulo: {"en": texto, "es": texto}} leido de LORE.md.

    Se lee el fichero, no una copia en codigo: si alguien corrige una pieza,
    la correccion vale desde la siguiente frase. Una segunda copia aqui se
    quedaria vieja sin que nadie se enterase.
    """
    doc = open(ruta or RUTA, encoding="utf-8").read()
    salida = {}
    bloques = re.split(r"\n\*\*(.+?)\*\*\n", doc)
    for i in range(1, len(bloques) - 1, 2):
        titulo, cuerpo = bloques[i], bloques[i + 1]
        citas = [l.strip("> ").strip() for l in cuerpo.splitlines()
                 if l.startswith(">")]
        # Las citas van en parrafos separados por una linea vacia: primero
        # ingles, despues espanol. Se agrupan por hueco, no por posicion fija.
        grupos, actual = [], []
        for linea in cuerpo.splitlines():
            if linea.startswith(">"):
                actual.append(linea.strip("> ").strip())
            elif actual:
                grupos.append(" ".join(actual))
                actual = []
        if actual:
            grupos.append(" ".join(actual))
        if len(grupos) >= 2 and citas:
            salida[titulo] = {"en": grupos[0], "es": grupos[1]}
    return salida


def _plano(texto):
    """Minusculas y sin acentos. 'cuánto' y 'cuanto' son la misma palabra para
    quien escribe con prisa, y la eleccion no puede depender de una tilde."""
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", (texto or "").lower())
                   if unicodedata.category(c) != "Mn")


def elegir(texto, idioma="es", ruta=None, usadas=()):
    """La pieza pertinente, o None. Nunca se fuerza una.

    Devuelve el texto LITERAL del fichero: ni resumido, ni reformulado, ni
    pasado por un modelo. Es lo unico que garantiza que lo que lee la persona
    es lo que alguien reviso.

    Gana la coincidencia mas ESPECIFICA, no la primera del diccionario. Con el
    orden a secas, 'fichero de texto plano' se llevaba la pieza del formato
    porque contenia 'fichero', y la pieza que hablaba justo de eso perdia.

    `usadas` son los titulos ya contados en esta conversacion. Se excluyen: la
    primera version repitio la pieza de Svalbard dos turnos seguidos, y una
    historia repetida deja de leerse a la segunda vez.
    """
    disponibles = piezas(ruta)
    bajo = _plano(texto)
    mejor, puntos = None, 0
    for titulo, claves in CLAVES.items():
        if titulo not in disponibles or titulo in usadas:
            continue
        for k in claves:
            if _plano(k) in bajo and len(k) > puntos:
                mejor, puntos = titulo, len(k)
    if not mejor:
        return None
    return mejor, disponibles[mejor].get(idioma)
