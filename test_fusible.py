#!/usr/bin/env python3
"""R4 · La conversación · El Fusible de Alucinación (Joya 3.3).

Rojo J: comando destructivo no en lista negra habitual ⇒ es atrapado por patrón.
Rojo K: comandos benignos no disparan el fusible.

sistema: MVP · solo biblioteca estándar.
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fusible

class TestFusibleAlucinacion(unittest.TestCase):
    """R4 · Los Rojos del inspector de patrones."""

    # ------------------------------------------------------------------
    # Rojo J: comando destructivo es atrapado
    # ------------------------------------------------------------------
    def test_rojo_j_comando_destructivo_bloqueado(self):
        """Un comando destructivo debe ser detectado y bloqueado."""
        texto_llm = "Para arreglarlo, ejecuta: rm -rf /"
        resultado = fusible.inspeccionar(texto_llm)
        self.assertTrue(resultado["bloqueado"], "El comando destructivo debe bloquearse")
        self.assertIn("rm -rf", resultado["hallazgos"][0], "Debe reportar el comando exacto")

    def test_rojo_j_patron_regex_bloqueado(self):
        """Un patrón peligroso (dd) debe ser detectado por regex, no solo por string."""
        texto_llm = "Puedes usar dd if=/dev/zero of=/dev/sda para limpiar el disco"
        resultado = fusible.inspeccionar(texto_llm)
        self.assertTrue(resultado["bloqueado"], "El patrón dd debe bloquearse")

    # ------------------------------------------------------------------
    # Rojo K: benignos no disparan
    # ------------------------------------------------------------------
    def test_rojo_k_benignos_pasan(self):
        """Un comando benigno no debe disparar el fusible."""
        texto_llm = "Puedes listar los archivos con: ls -la"
        resultado = fusible.inspeccionar(texto_llm)
        self.assertFalse(resultado["bloqueado"], "Los comandos benignos no deben bloquearse")
        self.assertEqual(len(resultado["hallazgos"]), 0, "No debe haber hallazgos")

    def test_rojo_k_texto_normal_pasa(self):
        """Texto sin comandos debe pasar limpio."""
        texto_llm = "La recursión es una función que se llama a sí misma."
        resultado = fusible.inspeccionar(texto_llm)
        self.assertFalse(resultado["bloqueado"], "El texto normal no debe bloquearse")


if __name__ == '__main__':
    unittest.main(verbosity=2)
