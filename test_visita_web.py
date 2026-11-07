"""Web visit-record verifier, against a throwaway openssl Ed25519 pair."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import visita_web


def _openssl(*args):
    return subprocess.run(["openssl", *args], capture_output=True, timeout=20, check=True).stdout


def _pair(folder):
    private = str(Path(folder) / "k.pem")
    _openssl("genpkey", "-algorithm", "ed25519", "-out", private)
    der = _openssl("pkey", "-in", private, "-pubout", "-outform", "DER")
    return private, der[-32:].hex()


def _sign(folder, private, data):
    message, out = str(Path(folder) / "m"), str(Path(folder) / "s")
    Path(message).write_bytes(data)
    _openssl("pkeyutl", "-sign", "-rawin", "-inkey", private, "-in", message, "-out", out)
    return "ed25519:" + Path(out).read_bytes().hex()


@unittest.skipUnless(shutil.which("openssl"), "SKIP-DECLARED (not green): openssl is unavailable")
class TestVisitaWeb(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.private, self.public = _pair(self.tmp.name)
        record = {"esquema": "atlas.invocacion/2", "tc": "tc1", "seq": 1,
                  "prev": "genesis", "clave_publica": self.public}
        self.text = json.dumps(record, separators=(",", ":"))
        self.sig = _sign(self.tmp.name, self.private, self.text.encode())

    def test_valid_signature_verifies(self):
        self.assertEqual(visita_web.verificar(self.text, self.public, self.sig)["estado"], "VERIFICADA")

    def test_altered_byte_is_rejected(self):
        bad = self.text.replace('"seq":1', '"seq":2')
        self.assertEqual(visita_web.verificar(bad, self.public, self.sig)["estado"], "RECHAZADA")

    def test_foreign_signer_is_rejected_by_openssl(self):
        # The record names key 2 consistently, but key 1 signed it: only OpenSSL can catch this.
        with tempfile.TemporaryDirectory() as other:
            _, public2 = _pair(other)
        record = json.loads(self.text)
        record["clave_publica"] = public2
        text = json.dumps(record, separators=(",", ":"))
        forged = _sign(self.tmp.name, self.private, text.encode())
        r = visita_web.verificar(text, public2, forged)
        self.assertEqual(r["estado"], "RECHAZADA")
        self.assertIn("signature", r["causa"])

    def test_other_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as other:
            _, public2 = _pair(other)
        self.assertEqual(visita_web.verificar(self.text, public2, self.sig)["estado"], "RECHAZADA")

    def test_broken_formats_are_rejected(self):
        for record, key, sig in (
            (self.text, self.public[:-2], self.sig),
            (self.text, self.public, self.sig[8:]),
            (self.text, self.public, "ed25519:zz"),
            ("not json", self.public, self.sig),
            (None, self.public, self.sig),
            (self.text, None, self.sig),
        ):
            self.assertEqual(visita_web.verificar(record, key, sig)["estado"], "RECHAZADA")

    def test_oversized_payload_is_rejected(self):
        big = json.dumps({"clave_publica": self.public, "x": "a" * 1100})
        self.assertEqual(visita_web.verificar(big, self.public, self.sig)["estado"], "RECHAZADA")

    def test_missing_openssl_is_no_data(self):
        original = visita_web.shutil.which
        visita_web.shutil.which = lambda name: None
        self.addCleanup(setattr, visita_web.shutil, "which", original)
        self.assertEqual(visita_web.verificar(self.text, self.public, self.sig)["estado"], "NO_DATA")


if __name__ == "__main__":
    unittest.main()
