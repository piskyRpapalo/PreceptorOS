"""prueba_edificio: signed building-proof receipts; no verified signature, no datum."""
import datetime as dt
import pathlib
import shutil
import subprocess
import tempfile
import unittest

import cuenta_cangrejo as C
import prueba_edificio as P

HEX = "a" * 64


def recibo(**over):
    base = {"esquema": P.SCHEMA, "id": "proof-1", "edificio": "b-lab", "pregunta_sha256": HEX,
            "respuesta_sha256": "b" * 64, "bytes": 42, "fecha": "2026-11-07T12:00:00Z", "maquina": "edge-1"}
    base.update(over)
    return base


@unittest.skipUnless(shutil.which("ssh-keygen"), "NO_DATA: ssh-keygen is unavailable")
class Verificar(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.tmp.name)
        self.sov = root / "sov"
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(self.sov), "-C", "sov"], check=True)
        pub = (root / "sov.pub").read_text().split()
        self.signers = root / "allowed_signers"
        self.signers.write_text(f'soberano namespaces="{C.ACCOUNT_NAMESPACE}" {pub[0]} {pub[1]}\n')
        fp, self.private = C.generar_par(directorio=None)
        self.public = self.private + ".pub"
        self.cuenta = self.activa(C.crear_cuenta("errante", "nodo.1.edge", ["aportar_datos"], fp))

    def tearDown(self):
        self.tmp.cleanup()

    def activa(self, cuenta):
        src = pathlib.Path(tempfile.mkdtemp(dir=self.tmp.name)) / "account"
        src.write_bytes(C._account_payload(cuenta))
        subprocess.run(["ssh-keygen", "-q", "-Y", "sign", "-n", C.ACCOUNT_NAMESPACE, "-f", str(self.sov), str(src)], check=True)
        out = dict(cuenta)
        out["estado"] = "linkeado"
        out["firma_ssh"] = src.with_name("account.sig").read_text()
        return out

    def sobre(self, carga=None, cuenta=None):
        carga = carga or recibo()
        return {"recibo": carga, "cuenta": cuenta or self.cuenta,
                "firma": C.firmar(P.canonico(carga), self.private)}

    def check(self, sobre):
        return P.verificar(sobre, signers=str(self.signers), public_path=self.public)

    def test_valid_signature_is_verified(self):
        self.assertEqual(self.check(self.sobre()), {"estado": "VERIFICADA", "id": "proof-1"})

    def test_altered_byte_is_rejected(self):
        s = self.sobre()
        s["recibo"] = recibo(bytes=43)
        self.assertEqual(self.check(s)["estado"], "RECHAZADA")

    def test_missing_signature_is_rejected(self):
        s = self.sobre()
        s["firma"] = ""
        r = self.check(s)
        self.assertEqual(r["estado"], "RECHAZADA")
        self.assertTrue(r["causa"])

    def test_scope_without_contribution_is_rejected(self):
        fp = self.cuenta["clave_publica"]
        cuenta = self.activa(C.crear_cuenta("errante", "nodo.1.edge", ["conectar_ia"], fp))
        self.assertEqual(self.check(self.sobre(cuenta=cuenta))["causa"], "account_scope_missing_aportar_datos")

    def test_expired_account_is_rejected(self):
        old = dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc)
        cuenta = self.activa(C.crear_cuenta("puente", "nodo.1.edge", ["aportar_datos"],
                                            self.cuenta["clave_publica"], ahora=old))
        r = self.check(self.sobre(cuenta=cuenta))
        self.assertEqual(r["estado"], "RECHAZADA")
        self.assertIn("expired", r["causa"])

    def test_revoked_account_is_rejected(self):
        cuenta = dict(self.cuenta, estado="revocado")
        self.assertEqual(self.check(self.sobre(cuenta=cuenta))["estado"], "RECHAZADA")

    def test_no_signers_is_rejected_not_no_data(self):
        r = P.verificar(self.sobre(), signers=None, public_path=self.public)
        self.assertEqual(r["estado"], "RECHAZADA")

    def test_never_raises(self):
        for bad in (None, [], {"recibo": None}, {"recibo": recibo(), "cuenta": 1, "firma": 2}):
            self.assertEqual(P.verificar(bad)["estado"], "RECHAZADA")


class Forma(unittest.TestCase):
    def test_valid_shape(self):
        self.assertEqual(P.validar(recibo()), {"estado": "VALIDA"})

    def test_extra_or_missing_key(self):
        self.assertEqual(P.validar(dict(recibo(), extra=1))["estado"], "RECHAZADA")
        r = recibo()
        del r["maquina"]
        self.assertEqual(P.validar(r)["estado"], "RECHAZADA")

    def test_field_causes(self):
        cases = {"id": "Bad ID", "edificio": "", "pregunta_sha256": "XYZ", "bytes": 0,
                 "fecha": "2026-11-07 12:00", "maquina": "a" * 33, "esquema": "other/1"}
        for k, v in cases.items():
            r = P.validar(recibo(**{k: v}))
            self.assertEqual(r["estado"], "RECHAZADA", k)
            self.assertIn(k, r["causa"])
        self.assertEqual(P.validar(recibo(bytes=True))["estado"], "RECHAZADA")

    def test_ceiling(self):
        with self.assertRaises(ValueError):
            P.canonico(recibo(id="x" * 1100))
        self.assertLess(len(P.canonico(recibo())), 1024)

    def test_canonical_is_deterministic(self):
        a = recibo()
        b = dict(reversed(list(a.items())))
        self.assertEqual(P.canonico(a), P.canonico(b))


if __name__ == "__main__":
    unittest.main()
