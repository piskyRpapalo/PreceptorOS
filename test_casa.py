#!/usr/bin/env python3
"""La casa, y la red de seguridad del renombrado (Mandato 1). Solo stdlib.

El dia que `casa.NOMBRE` cambie, en el disco de la persona seguiran colgando
del nombre VIEJO su memoria, su perfil, su voz y 2,4 GB de modelos -- medido en
las dos maquinas el 2026-08-24. Estas pruebas existen para que ese dia no sea
el dia en que el producto arranca como si fuera nuevo.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import casa  # noqa: E402


class TestHerencia(unittest.TestCase):

    def _con_hogar(self, d):
        return mock.patch.object(casa.Path, "home", staticmethod(lambda: Path(d)))

    def test_sin_nombres_anteriores_no_hay_nada_que_heredar(self):
        """El caso normal de hoy: no se ha renombrado nada."""
        with tempfile.TemporaryDirectory() as d, self._con_hogar(d):
            self.assertIsNone(casa.heredada())
            self.assertEqual(casa.raiz(), Path(d) / casa.NOMBRE)

    def test_si_la_casa_vieja_existe_y_la_nueva_no_se_adopta_la_vieja(self):
        """Lo suyo no se queda huerfano por cambiar una constante."""
        with tempfile.TemporaryDirectory() as d, self._con_hogar(d):
            (Path(d) / ".vieja").mkdir()
            (Path(d) / ".vieja" / "memory.db").write_text("sus recuerdos")
            with mock.patch.object(casa, "NOMBRE", ".nueva"), \
                 mock.patch.object(casa, "NOMBRES_ANTERIORES", (".vieja",)):
                self.assertEqual(casa.raiz(), Path(d) / ".vieja")
                self.assertEqual(casa.heredada(), Path(d) / ".vieja")

    def test_la_casa_nueva_gana_en_cuanto_existe(self):
        with tempfile.TemporaryDirectory() as d, self._con_hogar(d):
            (Path(d) / ".vieja").mkdir()
            (Path(d) / ".nueva").mkdir()
            with mock.patch.object(casa, "NOMBRE", ".nueva"), \
                 mock.patch.object(casa, "NOMBRES_ANTERIORES", (".vieja",)):
                self.assertEqual(casa.raiz(), Path(d) / ".nueva")
                self.assertIsNone(casa.heredada(),
                                  "con la nueva puesta ya no hay herencia pendiente")

    def test_manda_la_mas_reciente_de_las_viejas(self):
        with tempfile.TemporaryDirectory() as d, self._con_hogar(d):
            (Path(d) / ".antigua").mkdir()
            (Path(d) / ".menos-antigua").mkdir()
            with mock.patch.object(casa, "NOMBRE", ".nueva"), \
                 mock.patch.object(casa, "NOMBRES_ANTERIORES",
                                   (".menos-antigua", ".antigua")):
                self.assertEqual(casa.raiz(), Path(d) / ".menos-antigua")

    def test_heredar_NO_mueve_nada(self):
        """Mover gigas es decision de la persona. A medio camino, en un telefono
        con la bateria al 12 %, es una forma nueva de perderlo todo."""
        with tempfile.TemporaryDirectory() as d, self._con_hogar(d):
            vieja = Path(d) / ".vieja"
            vieja.mkdir()
            (vieja / "memory.db").write_text("sus recuerdos")
            with mock.patch.object(casa, "NOMBRE", ".nueva"), \
                 mock.patch.object(casa, "NOMBRES_ANTERIORES", (".vieja",)):
                casa.asegurar(casa.raiz())
            self.assertTrue((vieja / "memory.db").exists(),
                            "la herencia movio o borro algo de la casa vieja")
            self.assertFalse((Path(d) / ".nueva").exists(),
                             "creo la casa nueva y dejo la memoria en la vieja: "
                             "eso es partir sus datos en dos")


class TestLoDeSiempre(unittest.TestCase):

    def test_asegurar_crea_y_no_toca_lo_que_hay(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d) / "casita"
            casa.asegurar(base)
            (base / "algo").write_text("mio")
            casa.asegurar(base)
            self.assertEqual((base / "algo").read_text(), "mio")

    def test_sin_hogar_se_para_en_vez_de_inventarse_uno(self):
        def sin_home():
            raise RuntimeError("no hay home")
        with mock.patch.object(casa.Path, "home", staticmethod(sin_home)):
            with self.assertRaises(casa.CasaInaccesible):
                casa.raiz()


if __name__ == "__main__":
    unittest.main(verbosity=2)
