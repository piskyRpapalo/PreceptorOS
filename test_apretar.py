#!/usr/bin/env python3
"""test_apretar.py · que la compresion NO pueda alterar el contexto.

La suite entera existe para una afirmacion: `apretar` no puede cambiar el
sentido porque no puede escribir. Lo que se prueba, entonces, no es que
comprima bien --- eso es facil y poco interesante ---, sino que **el
verificador se entera cuando alguien rompe esa regla**. De ahi que la mitad de
las pruebas rompan el compresor a proposito.
"""
from __future__ import annotations

import unittest

import apretar


class SoloBorra(unittest.TestCase):
    def test_quita_duplicados_literales(self):
        t = "una cosa\n\notra cosa\n\nuna cosa"
        s, i = apretar.apretar(t)
        self.assertEqual(i["estado"], "OK")
        self.assertEqual(i["duplicadas"], 1)
        self.assertEqual(apretar.unidades(s), ["una cosa", "otra cosa"])

    def test_dos_unidades_iguales_salvo_espacios_son_una(self):
        s, i = apretar.apretar("El   nodo\nno tiene GPU\n\nEl nodo no tiene GPU")
        self.assertEqual(i["quitadas"], 1)

    def test_quita_la_contenida_en_otra(self):
        t = ("El nodo no tiene CUDA y la iGPU va por Vulkan.\n\n"
             "el nodo no tiene cuda")
        s, i = apretar.apretar(t)
        self.assertEqual(i["contenidas"], 1)
        self.assertIn("Vulkan", s)

    def test_toda_unidad_de_la_salida_esta_literal_en_la_entrada(self):
        t = "alfa 3 GB\n\nbeta ~/x/y\n\nalfa 3 GB\n\ngamma"
        s, _ = apretar.apretar(t)
        for u in apretar.unidades(s):
            self.assertIn(u, t)

    def test_una_negacion_no_se_reescribe_jamas(self):
        """Solo se borran unidades ENTERAS, asi que la que queda queda igual."""
        t = "El nodo NO tiene CUDA.\n\nEl nodo NO tiene CUDA."
        s, _ = apretar.apretar(t)
        self.assertIn("NO tiene CUDA", s)
        self.assertEqual(s.count("NO tiene CUDA"), 1)


class Verificador(unittest.TestCase):
    """`intacto` es la guarda. Si no se entera, `apretar` no garantiza nada."""

    ORIGINAL = ("La iGPU va a 4,63 tok/s con Vulkan.\n\n"
                "El modelo vive en ~/ia-models/qwen-uncensored/.\n\n"
                "OLLAMA_NUM_PARALLEL vale 1.")

    def test_una_reescritura_se_caza(self):
        falso = "La iGPU va rapida con Vulkan."
        ok, faltan = apretar.intacto(self.ORIGINAL, falso)
        self.assertFalse(ok)
        self.assertTrue(any("no estaba en el original" in f for f in faltan))

    def test_una_cifra_perdida_se_caza(self):
        sin = ("El modelo vive en ~/ia-models/qwen-uncensored/.\n\n"
               "OLLAMA_NUM_PARALLEL vale 1.")
        ok, faltan = apretar.intacto(self.ORIGINAL, sin)
        self.assertFalse(ok)
        self.assertTrue(any("cifra perdida" in f for f in faltan))

    def test_una_ruta_perdida_se_caza(self):
        sin = ("La iGPU va a 4,63 tok/s con Vulkan.\n\n"
               "OLLAMA_NUM_PARALLEL vale 1.")
        ok, faltan = apretar.intacto(self.ORIGINAL, sin)
        self.assertFalse(ok)
        self.assertTrue(any("ancla perdida" in f for f in faltan))

    def test_un_identificador_perdido_se_caza(self):
        sin = ("La iGPU va a 4,63 tok/s con Vulkan.\n\n"
               "El modelo vive en ~/ia-models/qwen-uncensored/.")
        ok, faltan = apretar.intacto(self.ORIGINAL, sin)
        self.assertFalse(ok)
        self.assertTrue(any("OLLAMA_NUM_PARALLEL" in f for f in faltan))

    def test_el_original_consigo_mismo_pasa(self):
        ok, faltan = apretar.intacto(self.ORIGINAL, self.ORIGINAL)
        self.assertTrue(ok, faltan)

    def test_reusa_el_sensor_de_cifras_de_la_casa(self):
        """El dia que cambie que es una cantidad, cambia en un solo sitio."""
        import cifras
        self.assertIs(apretar.cifras, cifras)


class RechazoConCausa(unittest.TestCase):
    def test_si_no_se_puede_garantizar_devuelve_el_ORIGINAL(self):
        """El valor devuelto ES la decision. Un aviso en otro campo se ignora."""
        original = "alfa 7 GB"
        roto = apretar.apretar

        def compresor_mentiroso(texto, tope_unidades=None):
            salida = "alfa"                       # se comio la cifra
            ok, faltan = apretar.intacto(texto, salida)
            return (texto, {"estado": "RECHAZADO", "causa": faltan}) if not ok \
                else (salida, {"estado": "OK"})

        salida, informe = compresor_mentiroso(original)
        self.assertEqual(salida, original)
        self.assertEqual(informe["estado"], "RECHAZADO")
        self.assertIs(apretar.apretar, roto)

    def test_texto_vacio_es_NO_DATA_con_causa(self):
        s, i = apretar.apretar("   ")
        self.assertEqual(i["estado"], "NO_DATA")
        self.assertIn("causa", i)


class Tope(unittest.TestCase):
    def test_recorta_por_unidades_enteras_nunca_a_media_frase(self):
        t = "uno 1 GB\n\ndos\n\ntres\n\ncuatro"
        s, i = apretar.apretar(t, tope_unidades=2)
        self.assertEqual(len(apretar.unidades(s)), 2)
        self.assertEqual(i["recortadas_por_tope"], 2)
        for u in apretar.unidades(s):
            self.assertIn(u, t)

    def test_recortar_una_cifra_se_declara_y_devuelve_el_original(self):
        """Si el tope tira la unidad que llevaba la cifra, el verificador lo
        ve y `apretar` se niega. El presupuesto no puede saltarse la guarda."""
        t = "texto sin numeros\n\notra linea\n\nel dato: 42 GB"
        s, i = apretar.apretar(t, tope_unidades=2)
        self.assertEqual(i["estado"], "RECHAZADO")
        self.assertEqual(s, t)


class Presupuesto(unittest.TestCase):
    def test_no_parte_ninguna_pieza(self):
        piezas = ["a" * 40, "b" * 40, "c" * 40]
        dentro, fuera = apretar.presupuesto(piezas, 90)
        self.assertEqual(len(dentro), 2)
        self.assertEqual(len(fuera), 1)
        for d in dentro:
            self.assertEqual(len(d), 40)

    def test_lo_que_no_cabe_se_devuelve_entero_para_contarlo(self):
        """Es `ctx_fuera`: no es un descarte silencioso, es una cuenta."""
        dentro, fuera = apretar.presupuesto(["x" * 100], 10)
        self.assertEqual(dentro, [])
        self.assertEqual(fuera, ["x" * 100])


if __name__ == "__main__":
    unittest.main(verbosity=2)
