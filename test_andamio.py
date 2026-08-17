#!/usr/bin/env python3
"""R3 · El andamio · tres Rojos.

Rojo G: intención elegida con preguntas sin contestar ⇒ huecos como NO_DATA.
Rojo H: sin modelo cargado, la intención produce texto copiable.
Rojo I: prompt ensamblado no puede salir sin haber sido mostrado (inspección).

sistema: MVP · solo biblioteca estándar.
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import andamio

class TestAndamio(unittest.TestCase):
    """R3 · Los tres Rojos del andamiaje."""

    # ------------------------------------------------------------------
    # Rojo G: huecos visibles como NO_DATA
    # ------------------------------------------------------------------
    def test_rojo_g_huecos_como_no_data(self):
        """Si falta contexto, el prompt ensamblado debe mostrar NO_DATA."""
        # Intención que requiere 'concepto' y 'nivel', pero pasamos vacío
        prompt = andamio.ensamblar(
            intencion="explicar_concepto",
            perfil={},
            contexto={}
        )
        self.assertIn("NO_DATA", prompt, "Los huecos deben ser visibles, no rellenos amables")

    # ------------------------------------------------------------------
    # Rojo H: texto copiable sin modelo
    # ------------------------------------------------------------------
    def test_rojo_h_sin_modelo_produce_texto(self):
        """El ensamblador debe devolver un string usable sin llamar al LLM."""
        prompt = andamio.ensamblar(
            intencion="explicar_concepto",
            perfil={"nombre": "Soberano"},
            contexto={"concepto": "Recursión", "nivel": "básico"}
        )
        self.assertIsInstance(prompt, str)
        self.assertIn("Recursión", prompt, "El contexto debe estar en el prompt")
        self.assertIn("Soberano", prompt, "El perfil debe estar en el prompt")
        self.assertIn("=== CARÁCTER ===", prompt, "El carácter base debe estar en el prompt")

    # ------------------------------------------------------------------
    # Rojo I: no salir sin mostrar
    # ------------------------------------------------------------------
    def test_rojo_i_salir_sin_mostrar_bloquea(self):
        """Intentar exportar el prompt sin inspección previa debe bloquear."""
        prompt = andamio.ensamblar(
            intencion="explicar_concepto",
            perfil={},
            contexto={}
        )
        # Sin haber llamado a andamio.marcar_inspeccionado()
        with self.assertRaises(andamio.SinInspeccion):
            andamio.preparar_salida_andamio(prompt)


if __name__ == '__main__':
    unittest.main(verbosity=2)
