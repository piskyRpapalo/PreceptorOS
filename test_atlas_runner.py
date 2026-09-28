"""El runner de theGame (2026-09-28): tuberia fiel, fallos medidos, escudo termico y huella del motor.

Solo biblioteca estandar. Hace falta `node` (el motor es JS); sin node, NO_DATA (skip), nunca verde.
"""
import json
import os
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import atlas_runner as R

AQUI = Path(__file__).resolve().parent


@unittest.skipUnless(shutil.which("node"), "NO_DATA · sin node no hay motor de theGame")
class Runner(unittest.TestCase):
    def frio(self):
        return R.Escudo(sensor=lambda: ("cpu", 50.0), dormir=lambda s: None)

    def test_la_tuberia_es_fiel_la_regla_empata_exacto_con_la_base(self):
        r = R.correr(R._pensar_regla(25), 12, 25, escudo=self.frio(), nombre="regla")
        self.assertEqual(r["estado"], "OK")
        self.assertEqual(r["final"], r["base"], "la corrida y la base no juegan la misma ley al mismo ritmo")
        self.assertEqual(r["veredicto"], "empate")
        self.assertEqual(r["medidas"]["invalidas"], 0)
        self.assertFalse(r["reemplaza"])

    def test_lo_que_no_es_una_accion_legal_es_un_fallo_medido(self):
        respuestas = iter(["hello there", '{"accion":"invocar"}', '{"accion":"bajar_a","banda":"luna"}',
                           None, '{"accion":"esperar"} and more text'])

        def pensar(prompt):
            v = next(respuestas)
            if v is None:
                raise RuntimeError("boom")
            return v
        r = R.correr(pensar, 5, 10, escudo=self.frio())
        causas = [p["causa"] for p in r["pasos"]]
        self.assertEqual(r["medidas"]["validas"], 1, causas)
        self.assertEqual(causas[0], "sin JSON en la respuesta")
        self.assertTrue(causas[1].startswith("no es legal ahora"))
        self.assertEqual(causas[3], "RuntimeError", "un modelo que revienta no es un fallo medido")
        self.assertTrue(r["pasos"][4]["valida"])

    def test_el_prompt_solo_lleva_estado_y_legales(self):
        p = R.pregunta({"esquema": "atlas.instantanea/1", "ciclo": 3}, [{"accion": "esperar"}])
        self.assertIn("STATE: ", p)
        self.assertIn('LEGAL: [{"accion":"esperar"}]', p)

    def test_escudo_espera_con_calor_y_para_si_no_baja(self):
        lecturas, dormido = iter([("cpu", 90.0), ("cpu", 86.0), ("cpu", 60.0)]), []
        e = R.Escudo(sensor=lambda: next(lecturas), dormir=dormido.append)
        self.assertTrue(e.antes(0.0))
        self.assertEqual(dormido, [30, 30])
        self.assertEqual([l.get("espera") for l in e.lecturas], [True, True, None])
        t = iter(range(0, 10000, 400))
        viejo = R.ESPERA_MAX_S
        R.ESPERA_MAX_S = 1000
        try:
            e2 = R.Escudo(sensor=lambda: ("bateria", 45.0), dormir=lambda s: None, reloj=lambda: next(t))
            self.assertFalse(e2.antes(0.0))
            self.assertIn("bateria a 45.0 C", e2.parado)
        finally:
            R.ESPERA_MAX_S = viejo
        r = R.correr(R._pensar_regla(25), 3, 25, escudo=e2)
        self.assertEqual(r["estado"], "PARADO_POR_CALOR")
        self.assertEqual(r["plan"]["jugadas"], 0)

    def test_sin_sensor_no_data_y_descansa_lo_que_tardo(self):
        dormido = []
        e = R.Escudo(sensor=lambda: (None, "sin sensor"), dormir=dormido.append)
        self.assertTrue(e.antes(1.5))
        self.assertEqual(dormido, [1.5])
        self.assertEqual(e.lecturas[0]["estado"], "NO_DATA")

    def test_un_motor_tocado_no_juega(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            shutil.copytree(AQUI / "atlas", tmp / "atlas")
            f = tmp / "atlas" / "atlas-motor.js"
            f.write_text(f.read_text() + "\n// tocado\n")
            r = R.correr(R._pensar_regla(25), 2, 25, escudo=self.frio(), corre=tmp / "atlas" / "corre.mjs")
            self.assertEqual(r["estado"], "NO_DATA")
            self.assertIn("FALLO_INTEGRIDAD", r["causa"])
            self.assertIn("atlas-motor.js", r["causa"])
        finally:
            shutil.rmtree(tmp)

    def test_sin_socket_ni_red(self):
        py = (AQUI / "atlas_runner.py").read_text(encoding="utf-8")
        js = (AQUI / "atlas" / "corre.mjs").read_text(encoding="utf-8")
        for prohibido in ("import socket", "urllib", "http.client"):
            self.assertNotIn(prohibido, py)
        for prohibido in ("node:net", "node:http", "node:https", "fetch(", "WebSocket", "Math.random"):
            self.assertNotIn(prohibido, js)

    def test_guardar_en_la_casa_0600(self):
        tmp = tempfile.mkdtemp()
        viejo = os.environ.get("HOME")
        os.environ["HOME"] = tmp
        try:
            r = R.correr(R._pensar_regla(25), 2, 25, escudo=self.frio())
            ruta = R.guardar(r)
            self.assertTrue(str(ruta).startswith(tmp))
            self.assertEqual(oct(ruta.stat().st_mode)[-3:], "600")
            self.assertEqual(json.loads(ruta.read_text())["esquema"], "atlas.corrida/1")
        finally:
            os.environ["HOME"] = viejo
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
