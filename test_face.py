"""La cara nueva: chat + joystick, la misma que la web, servida en "/".

Encargo NORTE 5 (one-shot del pintor, 2026-10-24). La cara vive en
`interface/face/` y es la MISMA que la web: `face.js`, `face.css`,
`skins.json` y las tres paginas son bytes identicos a los de
preceptoros-web `docs/rebuild/examples/` (la paridad la mide
`APP_DIR=... node docs/rebuild/examples/validate.mjs` desde la web).

Las nueve piezas de la lengua de burbujas se copian tal cual desde la web
`public/game/` y quedan clavadas por sha256: si alguien edita una copia,
esta prueba se pone roja antes de que la app y la web digan cosas distintas.
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import os
import pathlib
import re
import unittest
from importlib.machinery import SourceFileLoader
from unittest import mock

AQUI = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_loader(
    "preceptoros_pwa_face", SourceFileLoader("preceptoros_pwa_face", os.path.join(AQUI, "bin", "preceptoros-pwa")))
PWA = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(PWA)

CARA = pathlib.Path(AQUI, "interface", "face")
PIELES = ("basic", "atlantis", "zombie")
# sha256 de preceptoros-web public/game/ en la base 63c8331 (rama del terreno NORTE 5).
CLAVADAS = {
    "tabla_semantica.js": "eaab078c53a15602bd6e0ed596c1b04c4320db19bd536d6813b5afc0100019ce",
    "comic_tokens.js": "41c49df095fb5e7e80bd11f790988d9371dcbe219cb91ce1fd6a644bfec52936",
    "comic_accents.js": "2d3483daa5d99fa28654aae211e487ad70100a12236f0aa86094f41d34dd0091",
    "valores.js": "0982f47281becb01f98f4db6d16b4df0d649e7fdbf01aacae34e5d455d254114",
    "gacha.js": "f98302cf4f59f281b1ee2bdd90715c576a4630ec42316231191d4fba266d403c",
    "comic_atoms.js": "4d73eed589017461d90aec51a244d4c3f4331e0eeee57764fca89308f0cbd101",
    "bubble_light.js": "ddec8332ed88e3482a2101bc93fe0d4dd0e0befd8889a9932f39d3490d00ceb1",
    "bubble_language.js": "21f1c84ac69575e6352de2a1ba350f1798908179fc28b8390c89c095234ab96f",
    "core.js": "f7f126fde151931830f772be35aecdd84fa97f7c5be4b257f80d9674a66f6a0d",
    "bubble_bestiary.js": "7288216a1bedb8f4ced75cf3c2930eaf40a917f15f52d8332881d182a10c69aa",
}


def _get(ruta):
    h = PWA.PWA.__new__(PWA.PWA)
    h.path = ruta
    h.send_response = mock.Mock()
    h.send_header = mock.Mock()
    h.end_headers = mock.Mock()
    h.wfile = io.BytesIO()
    h.headers = {}
    PWA.PWA.do_GET(h)
    return h.send_response.call_args[0][0], h.wfile.getvalue()


def _rutas_de(html):
    return re.findall(r'(?:src|href)="(/face/[^"]+)"', html)


class TestLaCaraEsLaPuerta(unittest.TestCase):

    def test_la_raiz_sirve_la_cara_basic(self):
        codigo, cuerpo = _get("/")
        self.assertEqual(codigo, 200)
        self.assertEqual(cuerpo, (CARA / "basic.html").read_bytes())

    def test_cada_piel_y_cada_pieza_que_enlaza_se_sirve(self):
        for piel in PIELES:
            codigo, cuerpo = _get(f"/face/{piel}.html")
            self.assertEqual(codigo, 200, piel)
            for ruta in _rutas_de(cuerpo.decode("utf-8")):
                with self.subTest(piel=piel, ruta=ruta):
                    c, b = _get(ruta)
                    self.assertEqual(c, 200, f"{ruta} no se sirve")
                    self.assertGreater(len(b), 0)

    def test_nada_de_red_ni_de_reloj_con_autoridad(self):
        for f in sorted(CARA.rglob("*")):
            if f.is_file() and f.suffix in (".html", ".js", ".css"):
                t = f.read_text(encoding="utf-8")
                with self.subTest(f=f.name):
                    self.assertNotRegex(t, r'(?:src|href)=["\']https?://', "peticion externa")
                    self.assertLessEqual(len(t.encode("utf-8")), 16384, "techo por pieza")
        cara = (CARA / "face.js").read_text(encoding="utf-8")
        self.assertNotRegex(cara, r"Math\.random|Date\.now|fetch\(|localStorage")

    def test_las_piezas_de_la_lengua_son_las_de_la_web(self):
        for nombre, sha in CLAVADAS.items():
            with self.subTest(pieza=nombre):
                self.assertEqual(hashlib.sha256((CARA / "bubble" / nombre).read_bytes()).hexdigest(), sha)

    def test_el_armazon_offline_lleva_toda_la_cara(self):
        sw = pathlib.Path(AQUI, "interface", "sw.js").read_text(encoding="utf-8")
        for piel in PIELES:
            html = (CARA / f"{piel}.html").read_text(encoding="utf-8")
            for ruta in [f"/face/{piel}.html"] + _rutas_de(html):
                with self.subTest(ruta=ruta):
                    self.assertIn(f'"{ruta}"', sw, "sin esto la cara no abre sin red")


if __name__ == "__main__":
    unittest.main()
