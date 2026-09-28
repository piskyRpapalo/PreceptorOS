"""¿Es este aparato cuenta nodo? (2026-09-28) La cedula del rack, leida sin inventar nada."""
import hashlib
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import nodo_app as NA
import soberano

MIA, OTRA, TERCERA = "a1" * 32, "b2" * 32, "c3" * 32


def cedula(dispositivos, nodo="nodo.0.hexelion"):
    c = {"esquema": "preceptoros.cedula-nodo/1", "nodo": nodo, "admin": "d4" * 32,
         "dispositivos": [{"clave": k, "estado": e, "solicitud_testigo": "x", "aceptacion_testigo": None}
                          for k, e in dispositivos],
         "firma": None, "autenticidad": "NO_DATA · declaracion del rack, sin firma"}
    c["sha256"] = hashlib.sha256(json.dumps(c, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return c


class Cedula(unittest.TestCase):
    def test_linkeado_es_cuenta_nodo(self):
        r = NA.lee(cedula([(MIA, "linkeado"), (OTRA, "solicitado")]), soberano.codigo_de(MIA))
        self.assertEqual((r["estado"], r["nivel"]), ("OK", 3))
        self.assertTrue(r["autenticidad"].startswith("NO_DATA"), "finge una firma que no hay")

    def test_solicitado_o_revocado_no_es_cuenta_nodo(self):
        for e in ("solicitado", "revocado"):
            with self.subTest(estado=e):
                self.assertEqual(NA.lee(cedula([(MIA, e)]), soberano.codigo_de(MIA))["nivel"], 2)

    def test_otro_aparato_no_esta(self):
        r = NA.lee(cedula([(OTRA, "linkeado")]), soberano.codigo_de(MIA))
        self.assertEqual(r["nivel"], 2)
        self.assertIn("no esta en la cedula", r["causa"])

    def test_sin_soberano_declarado_no_data(self):
        r = NA.lee(cedula([(MIA, "linkeado")]), None)
        self.assertEqual((r["estado"], r["nivel"]), ("NO_DATA", None))

    def test_el_codigo_escrito_a_mano_tambien_vale(self):
        cod = soberano.codigo_de(MIA).replace("-", "").lower()
        self.assertEqual(NA.lee(cedula([(MIA, "linkeado")]), cod)["nivel"], 3)

    def test_una_cedula_tocada_no_pasa(self):
        c = cedula([(OTRA, "linkeado")])
        c["dispositivos"][0]["clave"] = MIA          # alguien se pone en la lista a mano
        r = NA.lee(c, soberano.codigo_de(MIA))
        self.assertEqual(r["estado"], "FALLO_INTEGRIDAD")

    def test_mal_formada_se_rechaza(self):
        for mala in ({}, dict(cedula([]), nodo="x"), dict(cedula([]), dispositivos=[{"clave": "zz", "estado": "linkeado"}])):
            with self.subTest(mala=str(mala)[:40]):
                self.assertEqual(NA.lee(mala, None)["estado"], "RECHAZADA")

    def test_importar_guarda_0600_y_estado_la_relee(self):
        d = tempfile.mkdtemp()
        try:
            f = Path(d) / "c.json"
            f.write_text(json.dumps(cedula([(MIA, "linkeado")])))
            r = NA.importar(f, soberano.codigo_de(MIA), destino=Path(d) / "nodo.json")
            self.assertEqual(r["nivel"], 3)
            self.assertEqual(oct((Path(d) / "nodo.json").stat().st_mode)[-3:], "600")
            self.assertEqual(NA.estado(soberano.codigo_de(MIA), origen=Path(d) / "nodo.json")["nivel"], 3)
            self.assertEqual(NA.estado(None, origen=Path(d) / "nada.json")["estado"], "NO_DATA")
        finally:
            shutil.rmtree(d)

    def test_la_cedula_del_rack_de_verdad_se_lee_aqui(self):
        """Cruce entre repos: la cedula que escribe `nodos.py` la lee esta app (mismo hash, mismo codigo)."""
        nexo = Path(__file__).resolve().parent.parent / "hexelion-nexo"
        if not (nexo / "nodos.py").exists():
            self.skipTest("NO_DATA · no hay hexelion-nexo al lado de la app")
        import subprocess
        d = tempfile.mkdtemp()
        try:
            db = os.path.join(d, "n.db")
            subprocess.run(["python3", str(nexo / "nodos.py"), "--db", db, "crear", "nodo.3.cruce"], check=True, capture_output=True)
            r = subprocess.run(["python3", str(nexo / "nodos.py"), "--db", db, "cedula", "nodo.3.cruce"], capture_output=True, text=True)
            ced = json.loads(r.stdout)
            self.assertEqual(NA.lee(ced, soberano.codigo_de(MIA))["estado"], "OK", "la app no entiende la cedula del rack")
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()
