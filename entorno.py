#!/usr/bin/env python3
"""Lectura centralizada de las opciones locales del producto."""
from __future__ import annotations

import os

PREFIJO = "PRECEPTOROS_"


def leer(sufijo, defecto=""):
    """Lee una opción declarada por el entorno, o devuelve su valor por defecto."""
    return os.environ.get(PREFIJO + sufijo, defecto)


def puesta(sufijo):
    """Distingue una variable ausente de una variable presente y vacía."""
    return PREFIJO + sufijo in os.environ


def activa(sufijo):
    """Interpreta el valor afirmativo convencional de una bandera."""
    return leer(sufijo).strip() == "1"


def nombres(sufijo):
    """Devuelve el único nombre de entorno admitido para una opción."""
    return (PREFIJO + sufijo,)
