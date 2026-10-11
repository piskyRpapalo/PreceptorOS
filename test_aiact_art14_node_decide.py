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
        import subprocess, sys
        p = subprocess.run([sys.executable, str(AQUI / "aiact_art14_node_decide.py")], input=json.dumps(self._una()),
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(json.loads(p.stdout)["estado"], "OK", p.stderr)
        fuente = (AQUI / "aiact_art14_node_decide.py").read_text(encoding="utf-8")
        for puerto in ("socket", "http.server", "bind(", "listen("):
            self.assertNotIn(puerto, fuente, "D68: ni un puerto")

    def _una(self):
        mo = R.Motor()
        try:
            mo.orden(op="inicial", ley=R.LEY)
            return mo.orden(op="ciclos", n=40)["ins"]
        finally:
            mo.cierra()


if __name__ == "__main__":
    unittest.main()
