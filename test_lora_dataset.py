"""lora_dataset: rows only from verified receipts; data never leaves the building."""
import hashlib
import json
import os
import pathlib
import tempfile
import unittest

import lora_dataset as D


def sha(t):
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def item(ident="p-1", pregunta="¿qué mide el lab?", respuesta="mide modelos locales", **over):
    recibo = {"esquema": "preceptoros.building-proof/1", "id": ident, "edificio": "b-lab",
              "pregunta_sha256": sha(pregunta), "respuesta_sha256": sha(respuesta),
              "bytes": len(pregunta.encode()) + len(respuesta.encode()),
              "fecha": "2026-11-07T12:00:00Z", "maquina": "edge-1"}
    recibo.update(over)
    return {"sobre": {"recibo": recibo, "cuenta": {}, "firma": "sig"}, "pregunta": pregunta, "respuesta": respuesta}


def ok(_sobre):
    return {"estado": "VERIFICADA"}


def no(_sobre):
    return {"estado": "RECHAZADA", "causa": "signature_verification_failed"}


class Filas(unittest.TestCase):
    def test_verified_receipt_becomes_row(self):
        filas, rechazos = D.filas([item()], ok)
        self.assertEqual(rechazos, [])
        self.assertEqual(filas, [{"recibo_id": "p-1", "edificio": "b-lab", "fecha": "2026-11-07T12:00:00Z",
                                  "pregunta": "¿qué mide el lab?", "respuesta": "mide modelos locales"}])

    def test_rejected_receipt_keeps_cause(self):
        filas, rechazos = D.filas([item()], no)
        self.assertEqual(filas, [])
        self.assertEqual(rechazos, [{"indice": 0, "causa": "signature_verification_failed"}])

    def test_rejected_without_cause(self):
        self.assertEqual(D.filas([item()], lambda s: {"estado": "RECHAZADA"})[1][0]["causa"], "not_verified")

    def test_altered_text_is_rejected(self):
        it = item()
        it["respuesta"] = "otra respuesta"
        self.assertEqual(D.filas([it], ok)[1][0]["causa"], "hash_mismatch")

    def test_bytes_mismatch(self):
        self.assertEqual(D.filas([item(bytes=1)], ok)[1][0]["causa"], "bytes_mismatch")

    def test_duplicate_receipt(self):
        filas, rechazos = D.filas([item(), item()], ok)
        self.assertEqual(len(filas), 1)
        self.assertEqual(rechazos, [{"indice": 1, "causa": "duplicate_receipt"}])

    def test_malformed_items(self):
        for bad in (None, {}, {"sobre": {}, "pregunta": "a", "respuesta": "b"}, {"sobre": {"recibo": {}}, "pregunta": 1}):
            self.assertEqual(D.filas([bad], ok)[1][0]["causa"], "malformed_item")

    def test_verifier_exception_is_rejection(self):
        def boom(_):
            raise RuntimeError("x")
        self.assertEqual(D.filas([item()], boom)[1][0]["causa"], "verifier_error")


class Escribir(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dest = pathlib.Path(self.tmp.name) / "dataset.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def test_zero_rows_is_no_data_and_no_file(self):
        self.assertEqual(D.escribir([], self.dest), {"estado": "NO_DATA", "causa": "no_verified_receipts"})
        self.assertFalse(self.dest.exists())
        self.assertEqual(os.listdir(self.tmp.name), [])

    def test_receipt_matches_written_file(self):
        filas, _ = D.filas([item("p-1"), item("p-2", "ñandú", "sí")], ok)
        r = D.escribir(filas, self.dest)
        raw = self.dest.read_bytes()
        self.assertEqual(r, {"esquema": "preceptoros.lora-dataset/1", "filas": 2, "bytes": len(raw),
                             "sha256": hashlib.sha256(raw).hexdigest()})
        lines = raw.decode("utf-8").splitlines()
        self.assertEqual(json.loads(lines[1])["pregunta"], "ñandú")
        self.assertIn("ñandú", lines[1])
        self.assertEqual(sorted(os.listdir(self.tmp.name)), ["dataset.jsonl"])

    def test_module_has_no_network_or_training(self):
        src = pathlib.Path(D.__file__).read_text(encoding="utf-8")
        for bad in ("socket", "urllib", "http.client", "subprocess", "/home/"):
            self.assertNotIn(bad, src)


if __name__ == "__main__":
    unittest.main()
