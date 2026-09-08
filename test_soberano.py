#!/usr/bin/env python3
"""Quien manda en este aparato, y por que no es una contrasena."""
from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memory as M                              # noqa: E402
import soberano as S                            # noqa: E402


class TestSoberano(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="sob_")
        self.db = os.path.join(self.dir, "m.db")
        M.crear(self.db)
        self.pub = "3d4f" * 16

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_el_codigo_es_EL_MISMO_que_calcula_el_navegador(self):
        """Dos derivaciones distintas del mismo codigo no vinculan nada.

        Se rehace aqui la cuenta que hace `onboarding.js` --SHA-256 de la clave
        publica, un caracter por byte, doce, en tres grupos-- y se cruza. Si
        alguien cambia el alfabeto o la longitud en un lado y no en el otro,
        este caso cae, que es justo lo que hace falta.
        """
        h = hashlib.sha256(bytes.fromhex(self.pub)).digest()
        s = "".join(S.ALFABETO[b % 32] for b in h[:12])
        self.assertEqual(S.codigo_de(self.pub), f"{s[:4]}-{s[4:8]}-{s[8:12]}")

    def test_el_alfabeto_no_tiene_las_cuatro_que_se_confunden(self):
        """I, L, O y U se confunden al teclear mirando una pantalla."""
        self.assertEqual(len(S.ALFABETO), 32)
        for ch in "ILOU":
            self.assertNotIn(ch, S.ALFABETO)

    def test_determinista_y_sin_sal(self):
        """Con sal, el codigo de la web y el de la app no coincidirian."""
        self.assertEqual(S.codigo_de(self.pub), S.codigo_de(self.pub))

    def test_se_teclea_como_se_pueda(self):
        cod = S.codigo_de(self.pub)
        for variante in (cod.lower(), cod.replace("-", ""),
                         cod.lower().replace("-", " "), "  " + cod + "  "):
            with self.subTest(variante=variante):
                self.assertEqual(S.normalizar(variante), cod)

    def test_una_clave_que_no_es_hex_no_da_codigo(self):
        for basura in ("", None, "no-soy-hex", "zz"):
            with self.subTest(basura=basura):
                self.assertIsNone(S.codigo_de(basura))

    # --- la declaracion ---------------------------------------------------

    def test_sin_declarar_no_hay_soberano_y_NO_manda_cualquiera(self):
        """Un aparato sin dueno no es un aparato de todos."""
        with M.abrir(self.db) as c:
            self.assertIsNone(S.quien(c))
            self.assertFalse(S.es_soberano(c, S.codigo_de(self.pub)))

    def test_declarar_y_reconocer(self):
        cod = S.codigo_de(self.pub)
        with M.abrir(self.db) as c:
            self.assertEqual(S.declarar(c, cod), cod)
            self.assertEqual(S.quien(c), cod)
            self.assertTrue(S.es_soberano(c, cod))
            self.assertTrue(S.es_soberano(c, cod.lower().replace("-", "")))

    def test_otro_codigo_NO_reconoce(self):
        with M.abrir(self.db) as c:
            S.declarar(c, S.codigo_de(self.pub))
            self.assertFalse(S.es_soberano(c, S.codigo_de("ab12" * 16)))

    def test_el_ultimo_que_llega_NO_manda(self):
        """Sobrescribir en silencio seria lo contrario de lo que esto sirve."""
        primero = S.codigo_de(self.pub)
        otro = S.codigo_de("ab12" * 16)
        with M.abrir(self.db) as c:
            S.declarar(c, primero)
            self.assertIsNone(S.declarar(c, otro), "un segundo codigo se colo")
            self.assertEqual(S.quien(c), primero)

    def test_declarar_dos_veces_el_MISMO_no_es_un_error(self):
        cod = S.codigo_de(self.pub)
        with M.abrir(self.db) as c:
            S.declarar(c, cod)
            self.assertEqual(S.declarar(c, cod), cod)

    def test_retirar_deja_el_aparato_sin_dueno(self):
        cod = S.codigo_de(self.pub)
        with M.abrir(self.db) as c:
            S.declarar(c, cod)
            S.retirar(c)
            self.assertIsNone(S.quien(c))
            self.assertFalse(S.es_soberano(c, cod))
            # Y se puede volver a declarar otro: retirar es el gesto que lo
            # permite, y por eso existe separado.
            otro = S.codigo_de("ab12" * 16)
            self.assertEqual(S.declarar(c, otro), otro)

    def test_un_codigo_mal_escrito_no_declara_nada(self):
        with M.abrir(self.db) as c:
            self.assertIsNone(S.declarar(c, "ABC"))
            self.assertIsNone(S.quien(c))


if __name__ == "__main__":
    unittest.main()
