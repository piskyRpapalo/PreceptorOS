#!/usr/bin/env python3
"""La tabla de anclas legislativas.

Lo que se comprueba aqui no es que las citas sean CORRECTAS --eso lo dictamina
un jurista, no una prueba-- sino que la tabla no pueda mentir por descuido: que
no haya fuentes fantasma, que ningun concepto se quede colgando, y que lo que
no esta anclado se sepa que no lo esta.
"""
from __future__ import annotations

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import normas as N                               # noqa: E402


class TestNormas(unittest.TestCase):

    def test_toda_referencia_apunta_a_una_fuente_declarada(self):
        """Una cita a una fuente que no existe es una cita que nadie comprueba."""
        for concepto, (_, refs) in N.ANCLAS.items():
            for fuente, ref in refs:
                with self.subTest(concepto=concepto, fuente=fuente):
                    self.assertIn(fuente, N.FUENTES,
                                  f"«{concepto}» cita la fuente «{fuente}» y "
                                  "no esta declarada en FUENTES")

    def test_cada_fuente_dice_de_que_edicion_habla(self):
        """Una cita legal sin edicion es una cita que nadie puede comprobar.

        Los articulos del AI Act cambiaron de numero entre borradores y las ISO
        se revisan. Sin la edicion, dentro de dos anos nadie sabra si la cita
        envejecio o sigue valiendo.
        """
        for clave, texto in N.FUENTES.items():
            with self.subTest(fuente=clave):
                self.assertRegex(
                    texto, r"(19|20)\d{2}",
                    f"la fuente «{clave}» no dice de que ano es")

    def test_ningun_concepto_se_queda_sin_articulo(self):
        for concepto, (nombre, refs) in N.ANCLAS.items():
            with self.subTest(concepto=concepto):
                self.assertTrue(nombre.strip(), "sin nombre normativo")
                self.assertTrue(refs, "anclado a cero articulos")

    def test_lo_no_anclado_devuelve_None_y_no_una_invencion(self):
        """Que un concepto no tenga ancla es informacion, no un hueco a rellenar.

        Dice que nadie decidio todavia que articulo lo juzga. Inventarle uno
        para que la tabla quede completa seria la version legal de rellenar una
        celda con una estimacion.
        """
        self.assertIsNone(N.ancla("un concepto que no existe"))
        self.assertEqual(N.citas("un concepto que no existe"), [])

    def test_el_ancla_senala_al_juez_y_no_al_veredicto(self):
        """`sello_soberano` esta anclado Y declarado como hueco a la vez.

        Es la propiedad que hace util esta tabla: dice que articulo JUZGA cada
        pieza, no que la pieza cumpla. Si anclar significara cumplir, la tabla
        seria una declaracion de conformidad escrita por el propio interesado.
        """
        self.assertIsNotNone(N.ancla("sello_soberano"))
        doc = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "docs", "COMPLIANCE.md")
        if not os.path.isfile(doc):
            self.skipTest("sin COMPLIANCE.md")
        texto = open(doc, encoding="utf-8").read()
        self.assertIn("Ed25519", texto,
                      "el sello esta anclado y su hueco ya no se declara")

    def test_la_consulta_del_auditor_funciona(self):
        """Llega con «art. 12» en la mano y quiere saber que lo mira."""
        conceptos = dict(N.anclados_por("ai_act", "art. 12"))
        self.assertIn("linea", conceptos)
        self.assertIn("memoria", conceptos)
        # Y por fuente entera, sin articulo.
        self.assertGreater(len(N.anclados_por("27001")), 2)

    def test_las_citas_salen_legibles_para_pegar(self):
        c = N.citas("linea")
        self.assertIn("AI Act art. 12", c)
        self.assertIn("ISO 27001 A.5.33", c)
        for x in c:
            self.assertNotRegex(x, r"^(ai_act|27001|42001)",
                                "sale la clave interna en vez de la etiqueta")

    def test_los_conceptos_se_escriben_en_minusculas_sin_espacios(self):
        """Son identificadores, no prosa: lo mismo que los ocho atajos."""
        for concepto in N.ANCLAS:
            with self.subTest(concepto=concepto):
                self.assertRegex(concepto, r"^[a-z][a-z0-9_]*$")

    def test_la_tabla_no_importa_nada_del_arbol(self):
        """Es una tabla: si dependiera del producto, el producto no podria
        citarla sin arrastrar medio arbol, y un auditor no podria leerla sola.
        """
        aqui = os.path.dirname(os.path.abspath(__file__))
        fuente = open(os.path.join(aqui, "normas.py"), encoding="utf-8").read()
        cuerpo = re.sub(r'"""[\s\S]*?"""', "", fuente)
        importa = re.findall(r"(?m)^\s*(?:from|import)\s+([\w.]+)", cuerpo)
        for mod in importa:
            with self.subTest(modulo=mod):
                self.assertIn(mod, ("__future__",),
                              f"normas.py importa «{mod}» y no deberia "
                              "importar nada")


if __name__ == "__main__":
    unittest.main()
