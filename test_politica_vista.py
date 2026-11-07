"""politica_vista: the read model of the node's A2A boundary panel. No network."""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import politica_vista

HERE = Path(__file__).resolve().parent
LIMITE = 1024
FICHEROS = ("mcp_thegame_server.py", "politica_nodo.json", "aiact_art14_game_policy.json")


def _texto(valor):
    return json.dumps(valor, ensure_ascii=False, separators=(",", ":"))


class PoliticaVistaTest(unittest.TestCase):
    def setUp(self):
        self.raiz = Path(tempfile.mkdtemp(prefix="pv-"))
        for nombre in FICHEROS:
            shutil.copy(HERE / nombre, self.raiz / nombre)

    def tearDown(self):
        shutil.rmtree(self.raiz, ignore_errors=True)

    def test_vista_real_compacta_y_con_esquema(self):
        v = politica_vista.vista()
        self.assertLess(len(_texto(v).encode("utf-8")), LIMITE)
        self.assertEqual(v["esquema"], "preceptoros.politica-vista/1")

    def test_posture_no_data_con_causa(self):
        p = politica_vista.vista()["posture"]
        self.assertEqual(p["state"], "NO_DATA")
        self.assertTrue(p["cause"])
        self.assertEqual(p["canon"], ["peaceful", "hostile", "cooperative", "closed", "open"])

    def test_condiciones_medidas_y_sandbox_con_causa_del_fichero(self):
        c = {x["id"]: x for x in politica_vista.vista()["conditions"]}
        self.assertEqual(set(c), {"registro_deudas", "freno_hidraulico", "fork_politico",
                                  "colateral_entrada", "cooperacion_obligatoria", "sandbox_wasmtime"})
        self.assertEqual(c["registro_deudas"]["state"], "DECLARED")
        self.assertEqual(c["cooperacion_obligatoria"]["state"], "DECLARED")  # firmas_minimas: 2, no activo flag
        self.assertNotIn("MEASURED", {x["state"] for x in c.values()})  # a file declares, never measures
        self.assertEqual(c["sandbox_wasmtime"], {"id": "sandbox_wasmtime", "state": "NO_DATA",
                                                 "cause": "wasmtime_not_compiled"})

    def test_caravanas_y_firma(self):
        v = politica_vista.vista()
        self.assertEqual(v["caravans"]["state"], "NO_DATA")
        self.assertEqual(v["caravans"]["machine"][0], "PROPUESTA")
        self.assertEqual(v["caravans"]["unsigned"], "EMULADO")
        self.assertEqual(v["signature"]["state"], "NO_DATA")
        self.assertTrue(v["signature"]["cause"])

    def test_fichero_ausente_da_no_data(self):
        os.remove(self.raiz / "politica_nodo.json")
        self.assertEqual(politica_vista.vista(self.raiz).get("state"), "NO_DATA")
        self.assertTrue(politica_vista.vista(self.raiz)["cause"])

    def test_aiact_ausente_da_no_data(self):
        os.remove(self.raiz / "aiact_art14_game_policy.json")
        self.assertEqual(politica_vista.vista(self.raiz)["state"], "NO_DATA")

    def test_json_roto_da_no_data(self):
        (self.raiz / "politica_nodo.json").write_text("{no json", encoding="utf-8")
        self.assertEqual(politica_vista.vista(self.raiz)["state"], "NO_DATA")
        (self.raiz / "politica_nodo.json").write_bytes(
            (HERE / "politica_nodo.json").read_bytes())
        (self.raiz / "aiact_art14_game_policy.json").write_text("[1,", encoding="utf-8")
        self.assertEqual(politica_vista.vista(self.raiz)["state"], "NO_DATA")

    def test_sin_rutas_de_casa_ni_de_tmp(self):
        for raiz in (None, self.raiz):
            texto = _texto(politica_vista.vista(raiz))
            self.assertNotIn("home/", texto)
            self.assertNotIn("/tmp", texto)


if __name__ == "__main__":
    unittest.main()
