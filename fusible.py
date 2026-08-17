#!/usr/bin/env python3
"""fusible.py · El Fusible de Alucinación (Joya 3.3).

Inspecciona la salida del LLM en busca de comandos Bash destructivos.
Es determinista (regex), cero LLM. Si detecta peligro, bloquea.
"""
from __future__ import annotations
import re

# Patrones peligrosos: si el LLM sugiere esto, se bloquea.
PATRONES_PELIGROSOS = [
    r'rm\s+-rf\s+/',            # Borrado recursivo de raíz
    r'dd\s+if=',                # Sobrescritura de disco
    r'mkfs\.',                  # Formateo de disco
    r':\(\)\{\s*:\|\:&\s*\};:', # Fork bomb
    r'>\s*/dev/sd[a-z]',        # Escritura directa a dispositivo de bloque
    r'chmod\s+-R\s+777\s+/'     # Permisos universales en raíz
]

def inspeccionar(texto: str) -> dict:
    """Inspecciona el texto y devuelve si está bloqueado y los hallazgos."""
    hallazgos = []
    for patron in PATRONES_PELIGROSOS:
        match = re.search(patron, texto)
        if match:
            hallazgos.append(match.group(0).strip())
    
    return {
        "bloqueado": len(hallazgos) > 0,
        "hallazgos": hallazgos
    }
