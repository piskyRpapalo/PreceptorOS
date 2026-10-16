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



# --- P1 + P2 (plan de ronda 2026-10-11, firmas D4/D5) ------------------------------------------------
import subprocess
from datetime import datetime, timedelta, timezone

AGENTE = "e5" * 32
AHORA = datetime(2026, 10, 11, 3, 0, tzinfo=timezone.utc)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def con_agente(estado="linkeado", ambito=("herramientas",), caduca=AHORA + timedelta(hours=2)):
    c = cedula([(MIA, "linkeado")])
    c.pop("sha256")
    c["dispositivos"].append({"clave": AGENTE, "estado": estado, "tipo": "agente", "ambito": list(ambito),
                              "caduca": iso(caduca), "solicitud_testigo": "x", "aceptacion_testigo": "y"})
    c["sha256"] = hashlib.sha256(json.dumps(c, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return c


class AgenteDelegado(unittest.TestCase):
    """P1 · la clave del agente entra en la cedula con AMBITO, CADUCIDAD y revocacion (patron Artemis:
    herramienta efimera, 30 min-8 h). La delegacion nunca sube niveles: dice que puede tocar, y cuando."""

    def test_agente_vigente_dentro_de_su_ambito(self):
        r = NA.agente(con_agente(), AGENTE, "herramientas", AHORA)
        self.assertEqual(r["estado"], "OK", r)

    def test_fuera_de_su_ambito_rechazado(self):
        r = NA.agente(con_agente(), AGENTE, "aportar_datos", AHORA)
        self.assertEqual(r["estado"], "RECHAZADA"); self.assertIn("ambito", r["causa"])

    def test_clave_vencida_rechazada_con_causa(self):
        r = NA.agente(con_agente(caduca=AHORA - timedelta(seconds=1)), AGENTE, "herramientas", AHORA)
        self.assertEqual(r["estado"], "RECHAZADA"); self.assertIn("caduc", r["causa"])

    def test_revocado_rechazado_al_instante(self):
        r = NA.agente(con_agente(estado="revocado"), AGENTE, "herramientas", AHORA)
        self.assertEqual(r["estado"], "RECHAZADA"); self.assertIn("revocad", r["causa"])

    def test_ttl_fuera_de_la_ventana_artemis_no_se_acepta(self):
        for mal in (AHORA + timedelta(hours=9), AHORA + timedelta(days=30)):
            with self.subTest(caduca=iso(mal)):
                self.assertEqual(NA.agente(con_agente(caduca=mal), AGENTE, "herramientas", AHORA)["estado"], "RECHAZADA")

    def test_capacidad_inventada_no_cuela(self):
        r = NA.agente(con_agente(ambito=("herramientas", "firmar_valor")), AGENTE, "herramientas", AHORA)
        self.assertEqual(r["estado"], "RECHAZADA")

    def test_el_agente_no_es_cuenta_nodo_del_humano(self):
        """La delegacion nunca sube niveles: el agente no hereda el nivel 3 del Soberano."""
        r = NA.lee(con_agente(), soberano.codigo_de(AGENTE))
        self.assertNotEqual(r.get("nivel"), 3)

    def test_agente_auto_anadido_sin_rehacer_el_hash(self):
        c = cedula([(MIA, "linkeado")])
        c["dispositivos"].append({"clave": AGENTE, "estado": "linkeado", "tipo": "agente", "ambito": ["herramientas"],
                                  "caduca": iso(AHORA + timedelta(hours=1))})
        self.assertEqual(NA.agente(c, AGENTE, "herramientas", AHORA)["estado"], "FALLO_INTEGRIDAD")


@unittest.skipUnless(shutil.which("ssh-keygen"), "NO_DATA · sin ssh-keygen en este aparato")
class CedulaFirmada(unittest.TestCase):
    """P2 · la cedula la firma el SOBERANO (no el rack: IronClaw) con ssh-keygen -Y y namespace
    preceptoros-cedula; la app la verifica por subproceso, sin dependencia nueva (D5)."""

    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(self.d / "k"), "-C", "prueba"], check=True)
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(self.d / "otra"), "-C", "otra"], check=True)
        t, k = (self.d / "k.pub").read_text().split()[:2]
        (self.d / "signers").write_text(f'soberano namespaces="preceptoros-cedula" {t} {k}\n')

    def tearDown(self):
        shutil.rmtree(self.d)

    def firmada(self, c, clave="k"):
        f = self.d / "cuerpo"
        f.write_bytes(NA.cuerpo_firmado(c))
        subprocess.run(["ssh-keygen", "-q", "-Y", "sign", "-n", "preceptoros-cedula", "-f", str(self.d / clave), str(f)], check=True)
        c = dict(c); c.pop("sha256", None)
        c["firma_ssh"] = (self.d / "cuerpo.sig").read_text()
        c["sha256"] = hashlib.sha256(json.dumps(c, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return c

    def test_firmada_por_el_soberano_autenticidad_ok(self):
        r = NA.lee(self.firmada(cedula([(MIA, "linkeado")])), soberano.codigo_de(MIA), signers=self.d / "signers")
        self.assertTrue(r["autenticidad"].startswith("OK"), r["autenticidad"])

    def test_firmada_por_otra_clave_rechazada(self):
        r = NA.lee(self.firmada(cedula([(MIA, "linkeado")]), "otra"), soberano.codigo_de(MIA), signers=self.d / "signers")
        self.assertEqual(r["estado"], "RECHAZADA"); self.assertIn("firma", r["causa"])

    def test_agente_anadido_despues_de_firmar_rompe_la_firma(self):
        c = self.firmada(cedula([(MIA, "linkeado")]))
        c.pop("sha256")
        c["dispositivos"].append({"clave": AGENTE, "estado": "linkeado", "tipo": "agente", "ambito": ["herramientas"],
                                  "caduca": iso(AHORA + timedelta(hours=1))})
        c["sha256"] = hashlib.sha256(json.dumps(c, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(NA.lee(c, soberano.codigo_de(MIA), signers=self.d / "signers")["estado"], "RECHAZADA")

    def test_sin_firma_sigue_no_data_sin_fingir(self):
        r = NA.lee(cedula([(MIA, "linkeado")]), soberano.codigo_de(MIA), signers=self.d / "signers")
        self.assertTrue(r["autenticidad"].startswith("NO_DATA"))

    def test_sin_signers_no_data_con_causa(self):
        r = NA.lee(self.firmada(cedula([(MIA, "linkeado")])), soberano.codigo_de(MIA), signers=self.d / "no-existe")
        self.assertTrue(r["autenticidad"].startswith("NO_DATA")); self.assertIn("allowed_signers", r["autenticidad"])


if __name__ == "__main__":
    unittest.main()
