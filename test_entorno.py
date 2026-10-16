"""Las opciones de entorno tienen un solo nombre y una sola lectura."""
from __future__ import annotations

import os
import unittest
from unittest import mock

import entorno as E


class TestOpcionesDeEntorno(unittest.TestCase):
    def test_lee_el_valor_declarado(self):
        with mock.patch.dict(os.environ, {"PRECEPTOROS_MOTOR": "/motor"}, clear=True):
            self.assertEqual(E.leer("MOTOR"), "/motor")

    def test_ausente_devuelve_el_defecto(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(E.leer("MOTOR", "local"), "local")

    def test_vacia_sigue_siendo_presente(self):
        with mock.patch.dict(os.environ, {"PRECEPTOROS_VOZ": ""}, clear=True):
            self.assertTrue(E.puesta("VOZ"))
            self.assertEqual(E.leer("VOZ", "defecto"), "")

    def test_ausente_no_se_confunde_con_vacia(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(E.puesta("VOZ"))

    def test_bandera_usa_el_valor_uno(self):
        for valor, esperado in (("1", True), (" 1 ", True), ("0", False),
                                ("si", False), ("", False)):
            with self.subTest(valor=valor), mock.patch.dict(
                    os.environ, {"PRECEPTOROS_SIN_CACHE": valor}, clear=True):
                self.assertIs(E.activa("SIN_CACHE"), esperado)

    def test_opcion_declara_un_solo_nombre(self):
        self.assertEqual(E.nombres("MOTOR"), ("PRECEPTOROS_MOTOR",))

    def test_lectura_no_escribe_en_stderr(self):
        with mock.patch.dict(os.environ, {"PRECEPTOROS_MOTOR": "/motor"}, clear=True):
            self.assertEqual(E.leer("MOTOR"), "/motor")


if __name__ == "__main__":
    unittest.main(verbosity=2)
