#!/usr/bin/env python3
"""R4 · La conversación · El Fusible de Alucinación (V-3).

Rojo J: comando destructivo NO listado y categorías de forma real.
Rojo K: benignos gemelos que no deben disparar el fusible.

sistema: MVP · solo biblioteca estándar.
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fusible

class TestFusibleAlucinacion(unittest.TestCase):
    """R4 · V-3 · El Rojo J que decide."""

    # ------------------------------------------------------------------
    # Rojo J: destructivo no listado y formas reales
    # ------------------------------------------------------------------
    def test_rojo_j_destructivo_no_listado(self):
        """Un comando destructivo no listado (shred) debe ser detectado."""
        texto = "Para borrarlo sin dejar rastro: shred -u /etc/passwd"
        res = fusible.inspeccionar(texto)
        self.assertTrue(res["bloqueado"], "shred debe ser detectado")

    def test_rojo_j_forma_multilinea(self):
        """Comando partido en varias líneas."""
        texto = "Ejecuta esto:\nrm\n-rf\n/"
        res = fusible.inspeccionar(texto)
        self.assertTrue(res["bloqueado"], "Debe detectar comando multilinea")

    def test_rojo_j_forma_encadenado(self):
        """Comando destructivo encadenado con &&."""
        texto = "echo 'hola' && rm -rf /"
        res = fusible.inspeccionar(texto)
        self.assertTrue(res["bloqueado"], "Debe detectar encadenado")

    def test_rojo_j_forma_entrecomillado(self):
        """Comando entre comillas en el texto."""
        texto = 'El comando es "rm -rf /"'
        res = fusible.inspeccionar(texto)
        self.assertTrue(res["bloqueado"], "Debe detectar entrecomillado")

    def test_rojo_j_forma_continuacion(self):
        """Comando con barra invertida de continuación."""
        texto = "rm -\\\nrf /"
        res = fusible.inspeccionar(texto)
        self.assertTrue(res["bloqueado"], "Debe detectar continuación")

    def test_rojo_j_forma_sustitucion(self):
        """Comando construido por variable."""
        texto = 'CMD="rm -rf /"\n$CMD'
        res = fusible.inspeccionar(texto)
        self.assertTrue(res["bloqueado"], "Debe detectar sustitución")

    # ------------------------------------------------------------------
    # Rojo K: benignos gemelos
    # ------------------------------------------------------------------
    def test_rojo_k_benigno_encadenado(self):
        """Encadenado benigno no debe disparar."""
        texto = "echo 'hola' && ls -la"
        res = fusible.inspeccionar(texto)
        self.assertFalse(res["bloqueado"], "Benigno encadenado no debe bloquearse")

    def test_rojo_k_benigno_entrecomillado(self):
        """Entrecomillado benigno no debe disparar."""
        texto = 'El comando es "ls -la"'
        res = fusible.inspeccionar(texto)
        self.assertFalse(res["bloqueado"], "Benigno entrecomillado no debe bloquearse")

    def test_rojo_k_texto_normal(self):
        """Texto normal sin comandos."""
        texto = "La recursión es una función que se llama a sí misma."
        res = fusible.inspeccionar(texto)
        self.assertFalse(res["bloqueado"], "Texto normal no debe bloquearse")


if __name__ == '__main__':
    unittest.main(verbosity=2)
