"""A1 de punta a punta por TUBERIA (plan de ronda 2026-10-11, P5; D68: ni un puerto).

Entra la instantanea `atlas.instantanea/1` (el vector compacto), sale UNA `atlas.accion/1` validada
o NO_DATA con su causa. El oraculo: en 20 estados de una partida determinista, la decision por la
puerta nueva es IDENTICA a la regla fija dentro del motor (orden `piloto`), y el motor declara su
huella (la del MANIFIESTO). El nodo PROPONE; firmar es de la persona (AI Act art. 14)."""
import json
import shutil
import unittest
from pathlib import Path

import aiact_art14_node_decide as D
import atlas_runner as R

AQUI = Path(__file__).resolve().parent


@unittest.skipUnless(shutil.which("node"), "NO_DATA · sin node en este aparato")
class DecidePorTuberia(unittest.TestCase):
    def test_veinte_estados_misma_decision_que_la_regla_del_motor(self):
        mo = R.Motor()
        try:
            r = mo.orden(op="inicial", ley=R.LEY)
            dif = []
            for paso in range(20):
                ins = mo.orden(op="ciclos", n=25)["ins"]
                dentro = mo.orden(op="piloto")["accion"]
                fuera = D.decide(ins)
                if fuera.get("estado") != "OK" or fuera["accion"] != dentro:
                    dif.append({"paso": paso, "motor": dentro, "puerta": fuera})
                if dentro["accion"] != "esperar":
                    mo.orden(op="aplica", accion=dentro)
        finally:
            mo.cierra()
        self.assertEqual(dif, [], "la puerta y la regla del motor no deciden igual")

    def test_declara_la_huella_del_motor_que_decidio(self):
        r = D.decide(self._una())
        man = json.loads((AQUI / "atlas" / "MANIFIESTO.json").read_text(encoding="utf-8"))
        self.assertEqual(r["motor"]["contenido_v"], man["contenido_v"])
        self.assertEqual(r["motor"]["piloto_sha256"], man["ficheros"]["atlas-piloto.js"])
        self.assertEqual(r["quien"], "regla fija (atlas-piloto.js)")
        self.assertIs(r["firma"], None, "el nodo propone; firmar es de la persona")

    def test_la_accion_siempre_es_del_enum(self):
        r = D.decide(self._una())
        self.assertIn(r["accion"]["accion"], ("esperar", "bajar_a", "recoger", "reparar", "aplazar", "invocar"))

    def test_instantanea_mal_formada_no_data_con_causa(self):
        for mala in (None, {}, {"esquema": "otra/1"}, dict(self._una(), contenido_v="1999-01-01.0")):
            with self.subTest(mala=str(mala)[:40]):
                r = D.decide(mala)
                self.assertEqual(r["estado"], "NO_DATA")
                self.assertTrue(r["causa"])

    def test_cli_por_tuberia_sin_puerto(self):
        """Por la CLI manda el guardian: en una instalacion de nivel 0 el nodo NO propone, y lo dice."""
        import subprocess, sys
        p = subprocess.run([sys.executable, str(AQUI / "aiact_art14_node_decide.py"), "--santuario"], input=json.dumps(self._una()),
                           capture_output=True, text=True, timeout=60)
        r = json.loads(p.stdout)
        self.assertEqual(r["estado"], "NO_DATA", p.stderr)
        self.assertIn("accion_de_juego", r["causa"])
        fuente = (AQUI / "aiact_art14_node_decide.py").read_text(encoding="utf-8")
        for puerto in ("socket", "http.server", "bind(", "listen("):
            self.assertNotIn(puerto, fuente, "D68: ni un puerto")

    def test_politica_y_guardian_delante_de_la_decision(self):
        """D6: con nivel 2 y politica valida, propone; nivel 1, politica rota o santuario: NO_DATA."""
        import tempfile
        import estado as E
        with tempfile.TemporaryDirectory() as d:
            E.fijar_nivel(2, Path(d))
            self.assertEqual(D.propone(self._una(), base=Path(d))["estado"], "OK")
            self.assertEqual(D.propone(self._una(), base=Path(d), argv=["--santuario"])["estado"], "NO_DATA")
            mala = Path(d) / "p.json"; mala.write_text(json.dumps({"esquema": "preceptoros.politica-juego/1", "capacidad": "accion_de_juego",
                                                                   "decide": {"reemplaza": True}, "st": {"max_bytes": 150}}))
            r = D.propone(self._una(), base=Path(d), ruta_politica=mala)
            self.assertEqual(r["estado"], "NO_DATA"); self.assertIn("politica", r["causa"])
            E.fijar_nivel(1, Path(d))
            self.assertEqual(D.propone(self._una(), base=Path(d))["estado"], "NO_DATA")

    def _una(self):
        mo = R.Motor()
        try:
            mo.orden(op="inicial", ley=R.LEY)
            return mo.orden(op="ciclos", n=40)["ins"]
        finally:
            mo.cierra()


if __name__ == "__main__":
    unittest.main()
