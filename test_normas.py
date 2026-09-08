#!/usr/bin/env python3
"""La tabla de anclas legislativas.

Lo que se comprueba aqui no es que las citas sean CORRECTAS --eso lo dictamina
un jurista, no una prueba-- sino que la tabla no pueda mentir por descuido: que
no haya fuentes fantasma, que ningun concepto se quede colgando, y que lo que
no esta anclado se sepa que no lo esta.
"""
from __future__ import annotations

import os
import pathlib
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

    # --- el molde · que no entren nombres inventados ------------------------

    def test_el_lexico_reconoce_sus_propias_palabras(self):
        for palabra in N.LEXICO:
            with self.subTest(palabra=palabra):
                self.assertTrue(N.es_de_la_casa(palabra))
        # Con articulo y con tildes, que es como se escriben de verdad.
        self.assertTrue(N.es_de_la_casa("La Barra del Corte"))
        self.assertTrue(N.es_de_la_casa("el Sello"))
        self.assertTrue(N.es_de_la_casa("Brújula"))

    def test_un_nombre_inventado_NO_pasa_por_de_la_casa(self):
        """Los dos que invente el 2026-09-08, guardados como caso.

        «Barra de Tiempo» donde se dice BARRA DEL CORTE, y «Acta de Revision»
        donde no habia nombre y por tanto no me tocaba ponerlo. Ninguna prueba
        pudo verlo entonces porque ninguna sabia que palabras estaban cogidas.
        """
        for inventado in ("Barra de Tiempo", "Acta de Revision",
                          "Perimetro de Sanitizacion"):
            with self.subTest(inventado=inventado):
                self.assertFalse(N.es_de_la_casa(inventado))

    def test_donde_solo_apunta_a_palabras_del_lexico(self):
        """Un glosario que explica una palabra que no existe explica un fantasma."""
        for clave in N.DONDE:
            with self.subTest(clave=clave):
                self.assertTrue(N.es_de_la_casa(clave),
                                f"DONDE explica «{clave}» y no esta en LEXICO")

    def test_los_bloques_de_la_web_usan_lexico_o_termino_legal(self):
        """El cruce que habria cazado la invencion el mismo dia.

        Cada linea de investigacion del LoRAtelier lleva un nombre visible. Ese
        nombre tiene que salir de UNA de dos fuentes: el vocabulario de la casa,
        o el termino del texto legal que juzga la pieza. Lo que no vale es una
        tercera: una palabra bonita que se le ocurrio a quien lo escribio.

        Se mira el castellano, que es donde se decide el nombre; las otras siete
        son su traduccion y ya tienen su propio guardian en la web.
        """
        ruta = os.path.expanduser("~/p0x/preceptoros-web/public/taller-es.json")
        if not os.path.isfile(ruta):
            self.skipTest("el repo de la web no esta a mano")
        import json
        bloques = json.load(open(ruta, encoding="utf-8"))["bloques"]
        # Terminos que salen de un texto legal, con su articulo. No son nombres
        # de la casa y por eso se declaran: cada uno es una cita, no un invento.
        LEGALES = {"supervision humana": "AI Act art. 14",
                   "business": "marca del producto"}
        # Y los que YA ESTABAN cuando llego el glosario, el 2026-09-08. Se
        # enumeran en vez de ensancharle el lexico a la casa por mi cuenta:
        # decidir que estas cuatro son canon no me toca, y ampliar la lista de
        # arriba para que el gate calle es exactamente la pared movida a
        # escondidas que el molde prohibe. Son el negativo: existian antes, y
        # esta lista solo puede ENCOGER, por decision del carbono.
        HEREDADOS = {"bienvenida", "medidor", "memoria de aprendizaje",
                     "atencion al publico"}
        for bid, campos in bloques.items():
            nombre = campos["nombre"]
            with self.subTest(bloque=bid, nombre=nombre):
                if N.es_de_la_casa(nombre):
                    continue
                import unicodedata
                pelado = unicodedata.normalize("NFD", nombre.lower())
                pelado = "".join(c for c in pelado
                                 if unicodedata.category(c) != "Mn")
                for art in ("el ", "la ", "los ", "las "):
                    if pelado.startswith(art):
                        pelado = pelado[len(art):]
                if pelado in HEREDADOS:
                    continue
                self.assertIn(
                    pelado, LEGALES,
                    f"el bloque «{bid}» se llama «{nombre}», que no esta en el "
                    "lexico de la casa ni declarado como termino legal. Si "
                    "hace falta un nombre nuevo, se propone como deuda y lo "
                    "firma el carbono -- no se inventa aqui")

    def test_la_tabla_no_importa_nada_del_arbol(self):
        """Es una tabla: si dependiera del producto, el producto no podria
        citarla sin arrastrar medio arbol, y un auditor no podria leerla sola.
        """
        aqui = os.path.dirname(os.path.abspath(__file__))
        fuente = open(os.path.join(aqui, "normas.py"), encoding="utf-8").read()
        cuerpo = re.sub(r'"""[\s\S]*?"""', "", fuente)
        # Lo que se prohibe es importar del ARBOL, que es lo que dice el nombre
        # de esta prueba. La primera version exigia «ni un import», y salio
        # roja sobre `unicodedata` -- biblioteca estandar, que no ata la tabla
        # a nada. Una prueba mas estricta que su propio motivo obliga a
        # retorcer el codigo para complacerla.
        locales = {f.stem for f in pathlib.Path(aqui).glob("*.py")}
        importa = re.findall(r"(?m)^\s*(?:from|import)\s+([\w.]+)", cuerpo)
        for mod in importa:
            with self.subTest(modulo=mod):
                self.assertNotIn(mod.split(".")[0], locales,
                                 f"normas.py importa «{mod}» del arbol. Es una "
                                 "tabla: si dependiera del producto, un auditor "
                                 "no podria leerla sola")


if __name__ == "__main__":
    unittest.main()
