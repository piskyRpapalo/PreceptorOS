#!/usr/bin/env python3
"""Tests for bin/instalar-pc-voz — A11Y plug&play: instalación guiada por voz.

Verifica que el instalador por voz: existe, es ejecutable, sintaxis bash
válida, anuncia cada paso (decir), nunca firma solo (confirmar), y cae a
texto cuando no hay voz (NO_DATA con causa, nunca bloquea).
"""
from __future__ import annotations
import os
import stat
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "bin" / "instalar-pc-voz"


class InstalarPcVozTests(unittest.TestCase):
    def test_existe_y_ejecutable(self):
        self.assertTrue(SCRIPT.is_file(), "falta bin/instalar-pc-voz")
        mode = SCRIPT.stat().st_mode
        self.assertTrue(mode & stat.S_IXUSR, "no es ejecutable")

    def test_sintaxis_bash_valida(self):
        r = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_tiene_decir_y_confirmar(self):
        src = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("decir()", src)
        self.assertIn("confirmar()", src)

    def test_delega_al_instalador_real(self):
        src = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("bin/instalar-pc", src)

    def test_no_firma_solo_confirmacion_hablada(self):
        src = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("¿Firmas la instalación?", src)
        self.assertIn("sí o no", src)

    def test_cae_a_texto_sin_voz(self):
        src = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("espeak-ng", src)
        self.assertIn("espeak", src)
        self.assertIn("NO_DATA", src)

    def test_voz_usa_modulo_local_piper(self):
        src = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("voz.hablar", src)
        self.assertNotIn("curl", src.split("decir()")[1].split("confirmar()")[0])

    def test_tamano_bajo_techo(self):
        size = SCRIPT.stat().st_size
        self.assertLess(size, 16384, f"instalar-pc-voz: {size} B >= 16.384 B")

    def test_sin_rutas_de_red(self):
        src = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("http://", src.replace("http://127.0.0.1", ""))
        self.assertNotIn("https://", src)

    def test_anuncia_cada_paso(self):
        src = SCRIPT.read_text(encoding="utf-8")
        pasos = src.count("az \"")
        self.assertGreaterEqual(pasos, 3, "faltan anuncios de pasos")


if __name__ == "__main__":
    unittest.main()
