#!/usr/bin/env python3
"""fusible.py · El Fusible de Alucinación (Joya 3.3 · V-3).

Normaliza el texto del LLM y lo inspecciona por forma estructural.
Determinista, cero LLM. No es completo: frena, no sustituye a la persona.
"""
from __future__ import annotations
import re

# Patrones por forma estructural, no por nombre exacto.
PATRONES_PELIGROSOS = [
    r'rm\s+(-\S*\s+)*[\/\*]',      # rm con flags sobre raíz o comodín
    r'shred\s+(-\S*\s+)*',         # shred (sobrescritura segura)
    r'dd\s+if=',                   # dd (sobrescritura de disco)
    r'mkfs\.\w+\s+/dev/',          # mkfs (formateo)
    r':\(\)\{\s*:\|\:&\s*\};:',    # fork bomb
    r'>\s*/dev/sd[a-z]',           # escritura directa a bloque
    r'chmod\s+(-\S*\s+)*0+\s+/',   # permisos 000 sobre raíz
    r'killall\s+(-\S*\s+)*-9',     # kill -9 a todo
    r'(wget|curl)\s+.*\|\s*(ba)?sh', # pipe a shell (remote exec)
]

def _normalizar(texto: str) -> str:
    """Normaliza continuaciones de línea y espacios para cazar la forma."""
    # Quitar backslash y espacios/newlines que le siguen (unión de líneas)
    t = re.sub(r'\\\s*', '', texto)
    # Colapsar multiples whitespace (incluido newlines) a un solo espacio
    t = re.sub(r'\s+', ' ', t)
    return t.strip()

def inspeccionar(texto: str) -> dict:
    """Inspecciona el texto y devuelve si está bloqueado y los hallazgos."""
    normalizado = _normalizar(texto)
    hallazgos = []
    for patron in PATRONES_PELIGROSOS:
        match = re.search(patron, normalizado, re.IGNORECASE)
        if match:
            hallazgos.append(match.group(0).strip())
    
    return {
        "bloqueado": len(hallazgos) > 0,
        "hallazgos": hallazgos
    }
