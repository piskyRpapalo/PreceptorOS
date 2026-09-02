#!/usr/bin/env python3
"""El cerebro afinado se elige, o no se elige, y siempre se dice por qué.

La que importa es la 4. `descarga.presente()` compara el sha256 del cerebro
contra el catálogo firmado; si un afinado con la huella cambiada pudiera
colarse, el producto estaría sirviendo un fichero que nadie firmó. Si alguna de
estas cinco se salta un día, que no sea esa.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import afinado


class TestCerebroAfinado(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = self.tmp.name
        self.base = os.path.join(self.raiz, "base.gguf")
        with open(self.base, "wb") as fh:
            fh.write(b"CEREBRO BASE")
        self.fino = os.path.join(self.raiz, "modelos", "afinado-v1.gguf")
        os.makedirs(os.path.dirname(self.fino), exist_ok=True)
        with open(self.fino, "wb") as fh:
            fh.write(b"CEREBRO AFINADO")

    def tearDown(self):
        self.tmp.cleanup()

    def test_1_sin_registro_elige_base(self):
        e = afinado.elegir(self.raiz, self.base)
        self.assertEqual(e.cual, "base")
        self.assertEqual(e.ruta, self.base)
        self.assertTrue(e.motivo, "una elección sin motivo no es auditable")

    def test_2_afinado_verificado_se_elige(self):
        afinado.promover(self.raiz, self.fino, "v1")
        e = afinado.elegir(self.raiz, self.base)
        self.assertEqual(e.cual, "afinado")
        self.assertEqual(os.path.realpath(e.ruta), os.path.realpath(self.fino))

    def test_3_declarado_pero_ausente_cae_al_base(self):
        afinado.promover(self.raiz, self.fino, "v1")
        os.remove(self.fino)
        e = afinado.elegir(self.raiz, self.base)
        self.assertEqual(e.cual, "base")

    def test_4_huella_que_no_cuadra_cae_al_base(self):
        """La que protege la promesa de integridad. El disco manda."""
        afinado.promover(self.raiz, self.fino, "v1")
        with open(self.fino, "wb") as fh:
            fh.write(b"OTRA COSA QUE NADIE FIRMO")
        e = afinado.elegir(self.raiz, self.base)
        self.assertEqual(e.cual, "base")
        self.assertIn("huella", e.motivo)

    def test_5_rollback_manda_sobre_un_afinado_valido(self):
        afinado.promover(self.raiz, self.fino, "v1")
        afinado.rollback(self.raiz, "el tester superó el umbral")
        e = afinado.elegir(self.raiz, self.base)
        self.assertEqual(e.cual, "base")
        self.assertTrue(os.path.isfile(self.fino),
                        "un rollback no destruye la prueba de lo que falló")

    def test_7_restaurar_deshace_el_rollback(self):
        """El rollback tenia ida y no vuelta.

        `rollback` escribe `preferencia: base` y solo `promover` la quitaba --
        pero `promover` exige una ruta de GGUF y mide su huella. O sea que para
        volver al afinado que ya estaba declarado y verificado habia que
        re-promoverlo, y eso es pedirle a la interfaz que maneje rutas de
        fichero. Una interfaz que manda rutas al servidor es una interfaz que
        puede mandar cualquier ruta.
        """
        afinado.promover(self.raiz, self.fino, "v1")
        afinado.rollback(self.raiz, "salio mal")
        self.assertEqual(afinado.elegir(self.raiz, self.base).cual, "base")

        afinado.restaurar(self.raiz, "ya se arreglo")
        eleccion = afinado.elegir(self.raiz, self.base)
        self.assertEqual(eleccion.cual, "afinado")
        self.assertEqual(eleccion.ruta, self.fino)

    def test_8_restaurar_no_inventa_un_afinado_que_no_existe(self):
        """Sin afinado declarado, restaurar no puede fabricar uno.

        Si `restaurar` se limitara a quitar la preferencia y devolver True, la
        interfaz enseñaria "ahora usas el afinado" con un registro vacio.
        """
        self.assertFalse(afinado.restaurar(self.raiz, "sin nada declarado"))
        self.assertEqual(afinado.elegir(self.raiz, self.base).cual, "base")

    def test_9_restaurar_no_borra_el_motivo_del_rollback(self):
        """El historial no se limpia al volver: un rollback ocurrio de verdad."""
        afinado.promover(self.raiz, self.fino, "v1")
        afinado.rollback(self.raiz, "se puso a repetir")
        afinado.restaurar(self.raiz, "reentrenado")
        import json
        reg = json.load(open(os.path.join(self.raiz, afinado.NOMBRE_REGISTRO),
                             encoding="utf-8"))
        self.assertNotIn("preferencia", reg)
        self.assertEqual(reg["rollback"]["motivo"], "se puso a repetir")

    def test_6_registro_roto_no_tumba_el_arranque(self):
        """Un JSON a medias es un fichero, no una excepción en la cara."""
        with open(os.path.join(self.raiz, afinado.NOMBRE_REGISTRO), "w") as fh:
            fh.write("{esto no es json")
        e = afinado.elegir(self.raiz, self.base)
        self.assertEqual(e.cual, "base")


if __name__ == "__main__":
    unittest.main(verbosity=2)
