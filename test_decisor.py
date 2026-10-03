#!/usr/bin/env python3
"""test_decisor.py · el tier 1 por reglas. Solo biblioteca estandar.

Lo que se defiende:
  1. `choice` es una opcion de la llamada o NO_DATA. Nunca otra cosa.
  2. Un empate es NO_DATA con causa. Jamas se desempata por orden de lista.
  3. Un conjunto de reglas sin sha256, o con uno que no cuadra, no se usa.
  4. El personaje narra la decision; no la cambia.
  5. Una regla nueva que empeora una decision pasada no pasa el replay.
  6. La salida tiene la forma de hexelion.eleccion.tier2/1 con tier=1, sin
     probabilidades inventadas.

`python3 test_decisor.py --sabotaje` rompe una copia de decisor.py de cada una
de esas formas y exige rojo.
"""
from __future__ import annotations

import ast
import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from unittest import mock

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

RUTA = os.environ.get("DECISOR_RUTA") or os.path.join(AQUI, "decisor.py")
_spec = importlib.util.spec_from_file_location("decisor_bajo_prueba", RUTA)
D = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(D)
FUENTE = open(RUTA, encoding="utf-8").read()

REGLAS = os.path.join(AQUI, "reglas", "companeros.json")
GOLDEN = os.path.join(AQUI, "reglas", "companeros.golden.jsonl")
CONJUNTO = D.cargar(REGLAS)
OPS = list(CONJUNTO["opciones"])
FICHAS = json.load(open(os.path.join(AQUI, "companeros.json"), encoding="utf-8"))["companeros"]


def conjunto(reglas, opciones=("a", "b", "c")):
    c = {"esquema": D.ESQUEMA_REGLAS, "tarea": "prueba", "version": 1,
         "opciones": list(opciones), "reglas": reglas}
    c["sha256"] = D.sellar(c)
    return c


def causa(d):
    return next((x["causa"] for x in d["no_data"] if x["campo"] == "choice"), "")


class TestTabla(unittest.TestCase):

    def test_las_reglas_del_producto_valen_y_cubren_los_ocho(self):
        self.assertEqual(sorted(OPS), sorted(f["id"] for f in FICHAS))
        self.assertEqual({r["opcion"] for r in CONJUNTO["reglas"]}, set(OPS),
                         "un compañero sin ninguna regla nunca seria sugerido")

    def test_la_opcion_fuera_de_la_llamada_no_gana(self):
        c = conjunto([{"id": "r1", "patron": "hola", "opcion": "c", "peso": 5}])
        d = D.decidir({"texto": "hola"}, ["a", "b"], conjunto=c)
        self.assertEqual(d["choice"], "NO_DATA")
        self.assertTrue(d["noul"])

    def test_regla_que_apunta_fuera_de_su_tabla_no_carga(self):
        c = conjunto([{"id": "r1", "patron": "hola", "opcion": "z", "peso": 1}])
        with self.assertRaises(D.ReglasInvalidas):
            D.validar(c)

    def test_choice_siempre_en_tabla_o_no_data(self):
        for c in D.leer_golden(GOLDEN):
            d = D.decidir({"texto": c["texto"]}, OPS)
            self.assertIn(d["choice"], OPS + ["NO_DATA"], c["texto"])
            self.assertEqual(D.valida_salida(d, OPS), [], c["texto"])

    def test_cliff_de_veinte(self):
        c = conjunto([{"id": "r1", "patron": "x", "opcion": "o0", "peso": 1}],
                     opciones=[f"o{i}" for i in range(21)])
        d = D.decidir({"texto": "x"}, [f"o{i}" for i in range(21)], conjunto=c)
        self.assertEqual(d["choice"], "NO_DATA")
        self.assertIn("cliff", causa(d))


class TestEmpate(unittest.TestCase):

    def test_empate_es_no_data_en_cualquier_orden(self):
        c = conjunto([{"id": "ra", "patron": "x", "opcion": "a", "peso": 2},
                      {"id": "rb", "patron": "x", "opcion": "b", "peso": 2}])
        for orden in (["a", "b", "c"], ["b", "a", "c"], ["c", "b", "a"]):
            d = D.decidir({"texto": "x"}, orden, conjunto=c)
            self.assertEqual(d["choice"], "NO_DATA", orden)
            self.assertIn("empate", causa(d))

    def test_el_orden_no_cambia_la_decision(self):
        c = conjunto([{"id": "ra", "patron": "x", "opcion": "a", "peso": 3},
                      {"id": "rb", "patron": "x", "opcion": "b", "peso": 2}])
        elegidas = {D.decidir({"texto": "x"}, o, conjunto=c)["choice"]
                    for o in (["a", "b", "c"], ["b", "a", "c"], ["c", "b", "a"])}
        self.assertEqual(elegidas, {"a"})

    def test_sin_regla_es_no_data_y_escala(self):
        d = D.decidir({"texto": "hola qué tal"}, OPS)
        self.assertEqual(d["choice"], "NO_DATA")
        self.assertIn("escala", causa(d))


class TestSello(unittest.TestCase):

    def test_sin_sha256_no_carga(self):
        c = conjunto([{"id": "r1", "patron": "x", "opcion": "a", "peso": 1}])
        del c["sha256"]
        with self.assertRaises(D.ReglasInvalidas):
            D.validar(c)
        d = D.decidir({"texto": "x"}, ["a", "b"], conjunto=c)
        self.assertEqual(d["choice"], "NO_DATA")
        self.assertIn("sha256", causa(d))

    def test_regla_tocada_sin_resellar_no_carga(self):
        c = copy.deepcopy(CONJUNTO)
        c["reglas"][0]["peso"] += 1
        with self.assertRaises(D.ReglasInvalidas):
            D.validar(c)

    def test_el_fichero_del_producto_esta_sellado(self):
        self.assertEqual(CONJUNTO["sha256"], D.sellar(CONJUNTO))


class TestPersonaje(unittest.TestCase):

    def test_narrar_no_toca_la_decision(self):
        for texto in ("traduce esto al inglés", "hola", "ordena mis apuntes"):
            d = D.decidir({"texto": texto}, OPS)
            antes = copy.deepcopy(d)
            frase = D.narrar(d, FICHAS)
            self.assertEqual(d, antes, texto)
            self.assertIsInstance(frase, str)

    def test_la_frase_dice_quien_elige(self):
        d = D.decidir({"texto": "traduce esto al inglés"}, OPS)
        self.assertIn("El Traductor", D.narrar(d, FICHAS))
        self.assertIn("Eliges tú", D.narrar(d, FICHAS))
        nd = D.decidir({"texto": "hola"}, OPS)
        self.assertIn("no sabe: escala", D.narrar(nd, FICHAS))


class TestForma(unittest.TestCase):

    def test_tier_1_sin_probabilidad_inventada(self):
        d = D.decidir({"texto": "traduce esto"}, OPS)
        self.assertEqual(d["choice"], "traductor")
        self.assertIsNone(d["score"])
        self.assertEqual(d["probs"], [])
        self.assertEqual(d["arnes"], {"tier": 1, "donde": "local-rack",
                                      "modelo": f"reglas:enrutado-companeros@{CONJUNTO['sha256']}",
                                      "modo": "reglas"})
        self.assertEqual({x["campo"] for x in d["no_data"]}, {"score", "probs"})

    def test_misma_entrada_mismo_plan_misma_salida(self):
        a = D.decidir({"texto": "escribe un test"}, OPS)
        b = D.decidir({"texto": "escribe un test"}, OPS)
        self.assertEqual(a, b)
        c = D.decidir({"texto": "escribe un test"}, list(reversed(OPS)))
        self.assertNotEqual(a["plan_hash"], c["plan_hash"])
        self.assertEqual(a["choice"], c["choice"])

    def test_no_abre_red_ni_escribe(self):
        arbol = ast.parse(FUENTE)
        for n in ast.walk(arbol):
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                nombres = [a.name for a in n.names] if isinstance(n, ast.Import) else [n.module]
                for m in nombres:
                    self.assertNotIn(m.split(".")[0], {"socket", "urllib", "http", "subprocess"})
            if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "open" and len(n.args) > 1:
                self.assertIn(ast.literal_eval(n.args[1]), ("r", "rb"))


class TestReplay(unittest.TestCase):

    def test_el_golden_no_empeora(self):
        self.assertEqual(D.replay(CONJUNTO, D.leer_golden(GOLDEN)), [])

    def test_una_regla_que_empeora_no_pasa(self):
        c = copy.deepcopy(CONJUNTO)
        c["reglas"].append({"id": "mala", "patron": r"\btradu", "opcion": "coder", "peso": 9})
        c["sha256"] = D.sellar(c)
        peor = D.replay(c, D.leer_golden(GOLDEN))
        self.assertTrue(peor)
        self.assertTrue(all(p["ahora"] == "coder" for p in peor))

    def test_el_golden_tiene_aciertos_y_abstenciones(self):
        g = D.leer_golden(GOLDEN)
        self.assertGreater(sum(c["acierta"] for c in g), 0)
        self.assertGreater(sum(c["tier1"] == "NO_DATA" for c in g), 0)


class TestPuerta(unittest.TestCase):

    def setUp(self):
        sp = importlib.util.spec_from_loader(
            "preceptoros_pwa_decisor",
            SourceFileLoader("preceptoros_pwa_decisor", os.path.join(AQUI, "bin", "preceptoros-pwa")))
        self.PWA = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(self.PWA)

    def _post(self, datos):
        h = mock.Mock()
        h.server = mock.Mock()
        r = {}
        h._json = lambda c, b: r.update(codigo=c, cuerpo=b)
        self.PWA.PWA._decisor(h, datos)
        return r["codigo"], r["cuerpo"]

    def test_post_decisor(self):
        codigo, cuerpo = self._post({"texto": "tradúceme esto al francés"})
        self.assertEqual(codigo, 200)
        self.assertEqual(cuerpo["decision"]["choice"], "traductor")
        self.assertTrue(cuerpo["forma_valida"])
        self.assertEqual(cuerpo["elige"], "la persona")

    def test_post_sin_texto_es_400(self):
        for malo in ({}, {"texto": ""}, {"texto": 3}, {"texto": "x" * 4001}):
            self.assertEqual(self._post(malo)[0], 400, malo)


SABOTAJES = (
    ("opcion fuera de la tabla gana", '        if r["opcion"] not in opciones:\n            continue',
     '        pass'),
    ("empate resuelto por orden", "    if len(ganadoras) > 1:", "    if False:"),
    ("regla sin sha256 se usa", '''    sello = conjunto.get("sha256")
    if not isinstance(sello, str) or not _CONTENT_V.match(sello):
        raise ReglasInvalidas("el conjunto no lleva sha256")
    if sello != sellar(conjunto):''', '''    sello = conjunto.get("sha256") or sellar(conjunto)
    if False:'''),
    ("el personaje cambia la decision", "    d = copy.deepcopy(decision)",
     '    d = decision\n    d["choice"] = fichas[0]["id"] if fichas else d["choice"]'),
    ("replay ciego", "    return peor\n", "    return []\n"),
    ("probabilidad inventada", '"score": None, "noul": noul,', '"score": 10000, "noul": noul,'),
)


def sabotaje():
    fuente = open(os.path.join(AQUI, "decisor.py"), encoding="utf-8").read()
    tmp = tempfile.mkdtemp(prefix="decisor-sabotaje-")
    # La copia busca su tabla junto a si misma, como el original.
    shutil.copytree(os.path.join(AQUI, "reglas"), os.path.join(tmp, "reglas"))
    detectadas = 0

    def corre(texto):
        ruta = os.path.join(tmp, "decisor.py")
        with open(ruta, "w", encoding="utf-8") as fh:
            fh.write(texto)
        env = dict(os.environ, DECISOR_RUTA=ruta)
        return subprocess.run([sys.executable, "-m", "unittest", "test_decisor"], cwd=AQUI,
                              env=env, capture_output=True, text=True, timeout=600).returncode

    try:
        if corre(fuente) != 0:
            print("AVISO · la copia SIN sabotear ya sale roja")
            print(f"RESULTADO SABOTAJE: 0/{len(SABOTAJES)}")
            return 1
        print("VERDE · copia intacta")
        for nombre, antes, despues in SABOTAJES:
            if antes not in fuente:
                print(f"  CRITICO · {nombre}: el ancla ya no existe en decisor.py")
                continue
            if corre(fuente.replace(antes, despues, 1)) != 0:
                detectadas += 1
                print(f"  ROJO  · {nombre} · detectado")
            else:
                print(f"  VERDE · {nombre} · NO detectado")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"RESULTADO SABOTAJE: {detectadas}/{len(SABOTAJES)}")
    return 0 if detectadas == len(SABOTAJES) else 1


if __name__ == "__main__":
    if "--sabotaje" in sys.argv:
        sys.exit(sabotaje())
    unittest.main()
