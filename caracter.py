#!/usr/bin/env python3
"""caracter.py · La Costura del Carácter (D8).

Punto único de entrada para el estilo. Hoy lee un fichero de texto.
Mañana, un LoRA. El contrato no asume fichero, solo provee estilo.
Doctrina: El carácter da estilo, nunca decide. Es dato, no órdenes.
"""
from __future__ import annotations
import os
import sys

ARQUETIPO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ARQUETIPO.md")

PATRONES_HOSTILES = ["ignora el filtro", "exporta la memoria", "no registres"]

def verificar_hostilidad(texto: str) -> bool:
    """Detecta instrucciones imperativas hostiles en el carácter."""
    if not texto: return False
    texto_lower = texto.lower()
    for patron in PATRONES_HOSTILES:
        if patron in texto_lower:
            print(f"[WARN] Intento hostil en carácter detectado: '{patron}'. Efecto cero.", file=sys.stderr)
            return True
    return False

def cargar() -> str | None:
    """Carga el carácter base. Si no existe o falla, devuelve None (ausencia)."""
    if not os.path.isfile(ARQUETIPO_PATH):
        return None
    try:
        with open(ARQUETIPO_PATH, "r", encoding="utf-8") as f:
            contenido = f.read().strip()
            if contenido:
                verificar_hostilidad(contenido) # T4: Registrar intento, efecto cero.
            return contenido if contenido else None
    except Exception:
        return None

def obtener_estilo() -> str | None:
    """Devuelve el estilo cargado. Punto único para el andamio."""
    return cargar()

def obtener_pieza(nombre: str) -> str:
    """Lee una pieza literal (lore) para que el programa la pegue, no el modelo."""
    # Por ahora, simula la lectura de una pieza de lore.
    lore = "El silicio es la frontera. La matemática es la ley. El carbono sella la verdad."
    return lore
