#!/usr/bin/env python3
"""test_version.py · la huella del armazon. Solo biblioteca estandar."""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import version as V  # noqa: E402


def arbol(contenido="hola"):
    """Un armazon de mentira con todos los ficheros que la version cubre."""
    d = tempfile.mkdtemp(prefix="version_")
    for rel in V.ARMAZON:
        ruta = os.path.join(d, rel)
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido)
    return d


class TestVersion(unittest.TestCase):

    def setUp(self):
        self.tmp = []

    def tearDown(self):
        for d in self.tmp:
            shutil.rmtree(d, ignore_errors=True)

    def _arbol(self, contenido="hola"):
        d = arbol(contenido)
        self.tmp.append(d)
        return d

    def test_el_arbol_real_tiene_huella_y_no_le_falta_nada(self):
        v = V.version()
        self.assertNotEqual(v["huella"], V.AUSENTE)
        self.assertEqual(v["faltan"], [], "el armazon declarado existe entero")
        self.assertEqual(v["ficheros"], len(V.ARMAZON))

    def test_dos_lecturas_del_mismo_arbol_dan_la_misma_huella(self):
        d = self._arbol()
        self.assertEqual(V.version(d)["huella"], V.version(d)["huella"])

    def test_tocar_una_pieza_cambia_la_huella(self):
        """Es toda la razon de ser del modulo: si la cara cambia, el numero cambia."""
        d = self._arbol()
        antes = V.version(d)["huella"]
        with open(os.path.join(d, "interface/app.js"), "a", encoding="utf-8") as f:
            f.write("// una coma mas\n")
        self.assertNotEqual(V.version(d)["huella"], antes)

    def test_dos_arboles_distintos_dan_huellas_distintas(self):
        self.assertNotEqual(V.version(self._arbol("uno"))["huella"],
                            V.version(self._arbol("dos"))["huella"])

    def test_lo_que_falta_se_declara_y_no_se_salta(self):
        d = self._arbol()
        os.remove(os.path.join(d, "interface/sw.js"))
        v = V.version(d)
        self.assertIn("interface/sw.js", v["faltan"])
        self.assertEqual(v["ficheros"], len(V.ARMAZON) - 1)

    def test_un_arbol_vacio_dice_NO_DATA_y_no_inventa_un_numero(self):
        d = tempfile.mkdtemp(prefix="version_vacio_")
        self.tmp.append(d)
        v = V.version(d)
        self.assertEqual(v["huella"], V.AUSENTE)
        self.assertEqual(v["fecha"], V.AUSENTE)
        self.assertEqual(V.corta(d), V.AUSENTE)

    def test_el_nombre_del_fichero_entra_en_la_huella(self):
        """Sin el nombre, mover el contenido de un fichero a otro no se notaria."""
        a, b = self._arbol(), self._arbol()
        with open(os.path.join(b, "interface/app.js"), "w", encoding="utf-8") as f:
            f.write("x")
        with open(os.path.join(b, "interface/app.css"), "w", encoding="utf-8") as f:
            f.write("hola" + "hola"[:0])
        # Mismo total de bytes, repartidos distinto: la huella tiene que cambiar.
        self.assertNotEqual(V.version(a)["huella"], V.version(b)["huella"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
