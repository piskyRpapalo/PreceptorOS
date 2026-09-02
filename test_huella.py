#!/usr/bin/env python3
"""La Huella Soberana · quien eres para esta maquina, y para nadie mas.

sistema: MVP · solo biblioteca estandar.

Se llama Huella Soberana (SHA256) y no Ed25519, que es como la nombraba el
plan. La correccion la firmo el Soberano el 2026-09-02: la biblioteca estandar
de Python no trae Ed25519, y meter `cryptography` rompe las dos reglas que
sostienen este producto -- stdlib unica y funciona en Termux. Llamar Ed25519 a
un sha256 seria mentir sobre la primitiva en la propia pantalla que promete
transparencia. La doctrina valora la correccion tecnica sobre la consistencia
con un error pasado.

Lo que la huella tiene que ser, y cada una de estas es una prueba de abajo:

  pseudonima  · no sale de tu nombre, ni de tu maquina, ni de nada que te
                identifique. Sale de azar. Si saliera del hostname, dos
                personas con el mismo portatil serian la misma persona, y una
                sola persona seria rastreable entre instalaciones.
  estable     · la misma en cada arranque, o no identifica nada.
  local       · vive en un fichero de tu casa, con permisos de solo tu.
  no fabricada· si la semilla esta y esta rota, se DECLARA rota. No se genera
                otra en silencio: una identidad que se regenera sola es una
                persona distinta cada vez que algo falla.
"""
from __future__ import annotations

import os
import stat
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import huella


class TestHuellaSoberana(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_1_es_estable_entre_llamadas(self):
        una = huella.leer(self.raiz)
        otra = huella.leer(self.raiz)
        self.assertEqual(una["huella"], otra["huella"])
        self.assertEqual(una["estado"], "ok")

    def test_2_dos_casas_son_dos_personas(self):
        with tempfile.TemporaryDirectory() as otra_casa:
            self.assertNotEqual(huella.leer(self.raiz)["huella"],
                                huella.leer(otra_casa)["huella"])

    def test_3_no_sale_de_nada_que_te_identifique(self):
        """La prueba de que es azar y no una derivacion del entorno.

        Si la huella saliera del usuario o del hostname, dos instalaciones del
        mismo equipo darian la misma -- y eso es exactamente lo que convierte
        un identificador pseudonimo en uno rastreable.
        """
        h = huella.leer(self.raiz)["huella"]
        for delator in (os.environ.get("USER", ""), os.environ.get("HOSTNAME", ""),
                        os.path.basename(os.path.expanduser("~"))):
            if delator:
                import hashlib
                self.assertNotEqual(
                    h, hashlib.sha256(delator.encode()).hexdigest(),
                    "la huella sale de un dato del entorno")

    def test_4_la_semilla_es_solo_tuya(self):
        huella.leer(self.raiz)
        modo = os.stat(os.path.join(self.raiz, huella.NOMBRE)).st_mode
        self.assertFalse(modo & (stat.S_IRGRP | stat.S_IROTH | stat.S_IWGRP | stat.S_IWOTH),
                         "la semilla la puede leer alguien que no eres tu")

    def test_5_una_semilla_rota_se_declara_no_se_sustituye(self):
        """La que de verdad importa.

        Regenerar en silencio ante un fichero corrupto convierte a la persona
        en otra sin avisarle. Se declara, con causa, y no se toca el fichero:
        una semilla ilegible todavia puede ser recuperable de una copia.
        """
        primera = huella.leer(self.raiz)["huella"]
        ruta = os.path.join(self.raiz, huella.NOMBRE)
        with open(ruta, "wb") as fh:
            fh.write(b"esto no es una semilla")
        roto = huella.leer(self.raiz)
        self.assertEqual(roto["estado"], "NO_DATA")
        self.assertIsNone(roto["huella"])
        self.assertTrue(roto["causa"])
        with open(ruta, "rb") as fh:
            self.assertEqual(fh.read(), b"esto no es una semilla",
                             "sobrescribio una semilla que podia recuperarse")
        self.assertTrue(primera)

    def test_6_la_semilla_nunca_viaja_en_el_paquete(self):
        """Se ensena la huella; el material del que sale, jamas."""
        paquete = huella.leer(self.raiz)
        with open(os.path.join(self.raiz, huella.NOMBRE), "rb") as fh:
            semilla = fh.read()
        crudo = repr(paquete).encode()
        self.assertNotIn(semilla, crudo)
        self.assertNotIn(semilla.hex().encode(), crudo)

    def test_7_la_forma_corta_es_para_leerla_en_voz_alta(self):
        p = huella.leer(self.raiz)
        self.assertEqual(len(p["huella"]), 64)
        # Grupos separados: un hexadecimal de 64 seguido no lo compara nadie a
        # ojo, y compararlo a ojo es justo para lo que sirve.
        self.assertIn(" ", p["corta"])
        self.assertTrue(p["huella"].startswith(p["corta"].split(" ")[0]))

    def test_8_sin_casa_no_se_inventa_una_huella(self):
        """Un directorio que no se puede crear no da identidad: da NO_DATA."""
        imposible = os.path.join(self.raiz, "fichero-no-carpeta")
        with open(imposible, "w") as fh:
            fh.write("x")
        p = huella.leer(os.path.join(imposible, "dentro"))
        self.assertEqual(p["estado"], "NO_DATA")
        self.assertIsNone(p["huella"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
