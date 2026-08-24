#!/usr/bin/env python3
"""El puente de nombres de las variables (Mandato 1). Solo stdlib.

Las variables de entorno son la parte del renombrado que NO vive en este
repositorio: viven en el `.bashrc` de quien lo usa, en un `.service` escrito
hace un mes y en una nota de un cuaderno. Estas pruebas existen para que
cambiarles el nombre no apague en silencio una opción que llevaba meses
funcionando.
"""
from __future__ import annotations

import io
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import entorno as E  # noqa: E402


class TestPuente(unittest.TestCase):

    def setUp(self):
        E._ya_avisado.clear()

    def test_el_nombre_nuevo_se_lee(self):
        with mock.patch.dict(os.environ, {"PRECEPTOROS_MOTOR": "/x"}, clear=True):
            self.assertEqual(E.leer("MOTOR"), "/x")

    def test_el_nombre_viejo_SIGUE_funcionando(self):
        """Lo contrario rompe máquinas de otros, en silencio."""
        with mock.patch.dict(os.environ, {"AURELIUS_MOTOR": "/viejo"}, clear=True):
            self.assertEqual(E.leer("MOTOR"), "/viejo")

    def test_si_estan_las_dos_gana_la_nueva(self):
        """Que la vieja pisara a la nueva castigaría a quien ya migró."""
        with mock.patch.dict(os.environ, {"AURELIUS_MOTOR": "/viejo",
                                          "PRECEPTOROS_MOTOR": "/nuevo"}, clear=True):
            self.assertEqual(E.leer("MOTOR"), "/nuevo")

    def test_sin_ninguna_devuelve_el_defecto(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(E.leer("MOTOR", "por defecto"), "por defecto")
            self.assertEqual(E.leer("MOTOR"), "")

    def test_puesta_distingue_vacia_de_ausente(self):
        """Una variable puesta a cadena vacía ESTÁ puesta, y a veces significa algo."""
        with mock.patch.dict(os.environ, {"PRECEPTOROS_VOZ": ""}, clear=True):
            self.assertTrue(E.puesta("VOZ"))
            self.assertEqual(E.leer("VOZ"), "")
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(E.puesta("VOZ"))

    def test_puesta_tambien_ve_el_nombre_viejo(self):
        with mock.patch.dict(os.environ, {"AURELIUS_VOZ": ""}, clear=True):
            self.assertTrue(E.puesta("VOZ"))

    def test_activa_es_el_patron_igual_a_uno(self):
        for valor, esperado in (("1", True), (" 1 ", True), ("0", False),
                                ("si", False), ("", False)):
            with mock.patch.dict(os.environ,
                                 {"PRECEPTOROS_SIN_CACHE": valor}, clear=True):
                self.assertIs(E.activa("SIN_CACHE"), esperado, f"con {valor!r}")


class TestElAviso(unittest.TestCase):

    def setUp(self):
        E._ya_avisado.clear()

    def _leer_avisando(self, veces=1, sufijo="MOTOR"):
        err = io.StringIO()
        with mock.patch.dict(os.environ, {"AURELIUS_" + sufijo: "/x"}, clear=True), \
             mock.patch.object(sys, "stderr", err):
            for _ in range(veces):
                E.leer(sufijo)
        return err.getvalue()

    def test_usar_el_nombre_viejo_avisa(self):
        salida = self._leer_avisando()
        self.assertIn("AURELIUS_MOTOR", salida)
        self.assertIn("PRECEPTOROS_MOTOR", salida)
        self.assertIn(E.SOPORTE_NOMBRE_VIEJO_HASTA, salida,
                      "el aviso no dice hasta cuándo vale el nombre viejo")

    def test_avisa_UNA_vez_por_variable_y_proceso(self):
        """Repetirlo en cada turno lo convierte en ruido, y el ruido se apaga."""
        salida = self._leer_avisando(veces=20)
        self.assertEqual(salida.count("pasó a llamarse"), 1)

    def test_el_aviso_va_a_stderr_y_no_ensucia_la_respuesta(self):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, {"AURELIUS_MOTOR": "/x"}, clear=True), \
             mock.patch.object(sys, "stdout", out), \
             mock.patch.object(sys, "stderr", err):
            E.leer("MOTOR")
        self.assertEqual(out.getvalue(), "",
                         "el aviso salió por stdout: contamina lo que se lee")
        self.assertNotEqual(err.getvalue(), "")

    def test_el_nombre_nuevo_no_avisa_de_nada(self):
        err = io.StringIO()
        with mock.patch.dict(os.environ, {"PRECEPTOROS_MOTOR": "/x"}, clear=True), \
             mock.patch.object(sys, "stderr", err):
            E.leer("MOTOR")
        self.assertEqual(err.getvalue(), "")


class TestLaFechaDeMuerte(unittest.TestCase):

    def test_la_compatibilidad_tiene_fecha_escrita(self):
        """Una compatibilidad sin fecha se queda para siempre, y dentro de tres
        años nadie sabrá si se puede quitar."""
        import datetime
        fecha = datetime.date.fromisoformat(E.SOPORTE_NOMBRE_VIEJO_HASTA)
        self.assertGreater(fecha, datetime.date(2026, 8, 25),
                           "la fecha de muerte ya pasó cuando se escribió")


class TestElProductoUsaElPuente(unittest.TestCase):
    """El invariante real no es *cómo* se lee, sino que nadie lea SOLO el nombre
    viejo: quien lo haga funcionará hoy y dejará de funcionar el día que el
    puente se retire, sin que nada falle mientras tanto.
    """

    FICHEROS_PRODUCTO = ("conversacion.py", "voz.py", "tono.py", "fuga.py",
                         "silencio.py", "cara.py", "aurelius.py",
                         "empaquetado/lanzador.py")

    # Módulos que leen las dos variables a mano en vez de importar `entorno`,
    # con su motivo. Sin motivo escrito, dentro de un año nadie sabrá si fue
    # decisión u olvido -- misma regla que las CONOCIDAS del Guardián.
    A_MANO = {
        "tono.py": "es un módulo HOJA: no importa nada de este árbol, y "
                   "`test_tono` caso 8 lo vigila desde antes del renombrado. "
                   "Acoplarlo al puente por ahorrar dos líneas cambiaría una "
                   "propiedad del diseño por comodidad.",
    }

    def _fuente(self, nombre):
        ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), nombre)
        if not os.path.exists(ruta):
            return None
        with open(ruta, encoding="utf-8") as f:
            return f.read()

    def test_nadie_lee_solo_el_nombre_viejo(self):
        import re
        viejo = re.compile(r'os\.environ(?:\.get)?\(\s*"AURELIUS_([A-Z_]+)"')
        for nombre in self.FICHEROS_PRODUCTO:
            cuerpo = self._fuente(nombre)
            if cuerpo is None:
                continue
            for sufijo in set(viejo.findall(cuerpo)):
                self.assertIn(f'"PRECEPTOROS_{sufijo}"', cuerpo,
                              f"{nombre} lee AURELIUS_{sufijo} y NO "
                              f"PRECEPTOROS_{sufijo}: dejará de funcionar en "
                              f"silencio cuando el puente se retire")

    def test_leer_a_mano_exige_motivo_escrito(self):
        import re
        viejo = re.compile(r'os\.environ(?:\.get)?\(\s*"AURELIUS_')
        for nombre in self.FICHEROS_PRODUCTO:
            cuerpo = self._fuente(nombre)
            if cuerpo is None:
                continue
            if viejo.search(cuerpo):
                self.assertIn(nombre, self.A_MANO,
                              f"{nombre} lee las variables a mano sin motivo "
                              f"declarado en A_MANO")

    def test_cada_excepcion_trae_su_porque(self):
        for nombre, motivo in self.A_MANO.items():
            self.assertGreater(len(motivo), 40,
                               f"el motivo de `{nombre}` no explica nada")


if __name__ == "__main__":
    unittest.main(verbosity=2)
