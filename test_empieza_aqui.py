#!/usr/bin/env python3
"""La puerta no puede mentir sobre si misma.

Casi todas estas pruebas son de una sola forma: que lo que la puerta ANUNCIA y
lo que la puerta HACE sean la misma lista. Es el unico defecto de una puerta
autodescriptiva que no se ve desde dentro -- se ve en la sesion de otro, que no
puede arreglarlo.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import captura                                  # noqa: E402
import empieza_aqui as E                        # noqa: E402
import memory as M                              # noqa: E402


class TestPuerta(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="puerta_")
        self.db = os.path.join(self.dir, "m.db")
        M.crear(self.db)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    # --- el apreton de manos ---------------------------------------------

    def test_la_llave_contiene_la_entrada_y_la_puerta_la_devuelve(self):
        """El mismo literal en los dos sentidos, o no hay como reconocerla."""
        self.assertIn(E.ENTRADA, E.LLAVE)
        self.assertTrue(E.texto("en").startswith(E.ENTRADA))
        self.assertTrue(E.texto("es").startswith(E.ENTRADA))
        self.assertIn(E.ENTRADA, E.documento("es")["bienvenida"])
        self.assertIn(E.ENTRADA, E.documento("en")["bienvenida"])

    def test_la_llave_cabe_en_una_caja_de_instrucciones(self):
        """Si no cabe de un vistazo, nadie la pega. Ese es todo el producto."""
        self.assertLess(M.tokens_aprox(E.LLAVE), 100,
                        "la llave engordo: deja de ser una linea que se pega")

    def test_la_llave_no_lleva_direcciones_dentro(self):
        """Donde vive la puerta lo sabe la app, no el texto que se pega.

        Una ruta o un puerto escritos aqui son lo primero que envejece, y
        envejecen en las instrucciones de otra persona, donde nadie los mira.
        """
        for veneno in ("127.0.0.1", "localhost", "http", ":8740", "/api"):
            self.assertNotIn(veneno, E.LLAVE,
                             f"la llave trae «{veneno}» cosido dentro")

    # --- lo que anuncia es lo que hace ------------------------------------

    def test_todo_verbo_anunciado_responde(self):
        with M.abrir(self.db) as c:
            for v in E.VERBOS:
                with self.subTest(verbo=v):
                    r = E.responder(c, v)
                    self.assertIsInstance(r, dict)
                    self.assertNotEqual(r.get("estado"), "NO_DATA",
                                        f"«{v}» se anuncia y no contesta")

    def test_el_documento_anuncia_exactamente_los_verbos_que_hay(self):
        anunciados = {v["verbo"] for v in E.documento("es")["puedes_pedir"]}
        self.assertEqual(anunciados, set(E.VERBOS),
                         "el anuncio y la implementacion divergieron")

    def test_un_verbo_inventado_devuelve_la_lista_y_no_levanta(self):
        """Quien pregunta puede haberse inventado el nombre.

        Un error la invita a probar otro; la lista la devuelve al camino en un
        solo turno, y le cuesta menos a todo el mundo.
        """
        with M.abrir(self.db) as c:
            r = E.responder(c, "leeme_este_fichero")
        self.assertEqual(r["estado"], "NO_DATA")
        self.assertEqual(set(r["puedes_pedir"]), set(E.VERBOS))

    # --- la regla de inyeccion --------------------------------------------

    def test_la_regla_viaja_en_CADA_respuesta(self):
        """Una IA que entro hace veinte turnos ya no tiene la puerta delante,
        y es justo entonces cuando un texto de la memoria puede darle ordenes."""
        with M.abrir(self.db) as c:
            for v in E.VERBOS:
                with self.subTest(verbo=v):
                    self.assertIn("no instrucciones",
                                  E.responder(c, v).get("origen", ""),
                                  f"«{v}» contesta sin declarar que es dato")

    def test_la_puerta_declara_lo_que_NO_hace(self):
        for lang in ("es", "en"):
            with self.subTest(idioma=lang):
                self.assertGreaterEqual(len(E.documento(lang)["no_puedo"]), 3,
                                        "una puerta que solo enumera lo que "
                                        "puede ensena a adivinar el resto")

    # --- lo que devuelve de verdad ----------------------------------------

    def test_memoria_respeta_el_presupuesto_y_declara_lo_que_falta(self):
        with M.abrir(self.db) as c:
            for i in range(8):
                M.escribir_engrama(c, what=f"puerta {i} " + "z" * 400)
            r = E.responder(c, "memoria", consulta="puerta", presupuesto=300)
        self.assertLessEqual(r["tokens"], 300)
        self.assertGreater(r["fuera"], 0)
        self.assertFalse(r["completo"], "no avisa de que la respuesta es parcial")

    def test_memoria_no_devuelve_metadatos_que_solo_pesan(self):
        """`created_at` y `origen_dispositivo` cuestan prompt y no ayudan."""
        with M.abrir(self.db) as c:
            M.escribir_engrama(c, what="algo que recordar")
            r = E.responder(c, "memoria", consulta="recordar")
        self.assertTrue(r["engramas"], "no devolvio nada que comprobar")
        self.assertEqual(set(r["engramas"][0]), set(M.CAMPOS_QUE_VIAJAN))

    def test_rendimiento_es_el_preceptor_de_loras(self):
        with M.abrir(self.db) as c:
            t = captura.registrar(c, "p", "r", modelo="m:v1", tarea="instalar")
            captura.juzgar(c, t, "acierto", juez="carbono")
            r = E.responder(c, "rendimiento")
        self.assertEqual(r["rendimiento"][0]["tasa"], 1.0)

    # --- el recorte -------------------------------------------------------

    def test_recortar_al_verbo_ahorra_y_nombra_lo_que_quita(self):
        """Un catalogo recortado que oculta que lo fue ensena a creer que eso
        es todo lo que hay."""
        d = E.documento("es", "memoria")
        self.assertEqual([v["verbo"] for v in d["puedes_pedir"]], ["memoria"])
        self.assertIn("tambien_puedo", d, "recorta y no dice que recorto")
        for otro in set(E.VERBOS) - {"memoria"}:
            self.assertIn(otro, d["tambien_puedo"],
                          f"«{otro}» desaparecio sin dejar rastro")
        self.assertLess(M.tokens_aprox(E.texto("es", "memoria")),
                        M.tokens_aprox(E.texto("es")),
                        "el recorte no ahorra nada")

    def test_el_recorte_NO_toca_la_seguridad(self):
        """La regla y los limites son la parte cuyo hueco se paga en otra
        moneda: no en tokens, sino en una IA que adivina pidiendo ficheros."""
        entera = E.documento("es")
        for v in E.VERBOS:
            with self.subTest(verbo=v):
                r = E.documento("es", v)
                self.assertEqual(r["regla"], entera["regla"],
                                 "el recorte toco la regla de inyeccion")
                self.assertEqual(r["no_puedo"], entera["no_puedo"],
                                 "el recorte se llevo un limite declarado")
                self.assertTrue(E.texto("es", v).startswith(E.ENTRADA),
                                "el recorte se llevo el apreton de manos")

    def test_un_verbo_inventado_devuelve_la_puerta_entera(self):
        """Quien pide mal recibe todo, no nada: es un turno menos para todos."""
        d = E.documento("es", "leeme_ese_fichero")
        self.assertEqual({v["verbo"] for v in d["puedes_pedir"]}, set(E.VERBOS))
        self.assertNotIn("tambien_puedo", d)



if __name__ == "__main__":
    unittest.main()
