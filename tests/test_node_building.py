import hashlib
import json
import os
import pathlib
import stat
import tempfile
import unittest

import node_building as subject


KEY = "a5" * 32


class NodeBuildingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="pwa-node-building-")
        self.base = pathlib.Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def provision(self, node="primer-ancla"):
        result = subject.provisionar_identidad(self.base, node)
        self.assertEqual(result["estado"], "provisionada")
        return result

    def key_file(self, mode=0o600):
        path = self.base / "heartbeat-key"
        path.write_text(KEY + "\n", encoding="ascii")
        path.chmod(mode)
        return path

    def receipt(self, node="primer-ancla", body=None):
        body = body or {"esquema": subject.DECLARATION_SCHEMA, "edificio": subject.BUILDING_ID}
        receipt = {
            "esquema": subject.RECEIPT_SCHEMA,
            "estado": "recibido",
            "causa": None,
            "nodo": node,
            "edificio": subject.BUILDING_ID,
            "payload_sha256": hashlib.sha256(subject._canonical(body)).hexdigest(),
            "recibido_en": "2026-11-01T12:00:00.000Z",
            "procedencia": "preceptoros-141-candidate+142-census+central-allocation",
        }
        receipt["recibo_sha256"] = hashlib.sha256(subject._canonical(receipt)).hexdigest()
        return receipt

    def transport_for(self, response, status=202, *, final_url=None, capture=None):
        def send(endpoint, body, headers, timeout):
            if capture is not None:
                capture.update(endpoint=endpoint, body=body, headers=headers, timeout=timeout)
            return status, json.dumps(response, separators=(",", ":")).encode(), final_url or endpoint
        return send

    def test_identity_provision_is_canonical_atomic_private_and_idempotent(self):
        result = self.provision()
        path = self.base / "node-identity.json"
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(json.loads(path.read_text()), {
            "esquema": subject.IDENTITY_SCHEMA, "node_id": "primer-ancla"})
        self.assertEqual(subject.provisionar_identidad(self.base, "primer-ancla")["repetida"], True)
        self.assertEqual(subject.provisionar_identidad(self.base, "other-node")["causa"],
                         "identidad_ya_provisionada")

    def test_identity_rejects_invalid_and_malformed_config(self):
        self.assertEqual(subject.provisionar_identidad(self.base, "../node")["estado"], "NO_DATA")
        (self.base / "node-identity.json").write_text("{}", encoding="utf-8")
        self.assertEqual(subject.leer_identidad(self.base)["causa"], "identidad_local_invalida")

    def test_duplicate_identity_keys_are_rejected(self):
        path = self.base / "node-identity.json"
        path.write_text('{"esquema":"preceptoros.pwa-node-identity/1",'
                        '"node_id":"primer-ancla","node_id":"onexstation"}', encoding="utf-8")
        path.chmod(0o600)
        self.assertEqual(subject.leer_identidad(self.base)["causa"], "identidad_local_invalida")

    def test_credential_requires_private_regular_file_and_never_leaves_reader(self):
        self.assertEqual(subject._read_key(self.base)[1], "credencial_no_provisionada")
        path = self.key_file(0o644)
        self.assertEqual(subject._read_key(self.base)[1], "credencial_local_invalida")
        path.chmod(0o600)
        self.assertEqual(subject._read_key(self.base)[0], KEY)

    def test_symlink_credential_is_rejected(self):
        target = self.base / "outside"
        target.write_text(KEY)
        target.chmod(0o600)
        (self.base / "heartbeat-key").symlink_to(target)
        self.assertEqual(subject._read_key(self.base)[1], "credencial_local_invalida")

    def test_no_identity_or_unassigned_node_never_calls_transport(self):
        calls = []
        result = subject.declarar_edificio(self.base, transport=lambda *args: calls.append(args))
        self.assertEqual(result["causa"], "identidad_no_provisionada")
        self.provision("onexstation")
        self.key_file()
        result = subject.declarar_edificio(self.base, transport=lambda *args: calls.append(args))
        self.assertEqual(result["causa"], "nodo_sin_edificio_asignado")
        self.assertEqual(calls, [])

    def test_exact_fixed_https_request_and_valid_receipt(self):
        self.provision()
        self.key_file()
        captured = {}
        result = subject.declarar_edificio(self.base,
            transport=self.transport_for(self.receipt(), capture=captured))
        self.assertEqual(result["estado"], "recibido")
        self.assertEqual(captured["endpoint"], subject.ENDPOINT)
        self.assertEqual(json.loads(captured["body"]), {
            "esquema": "preceptoros.edificio-declaracion/1",
            "edificio": "observatorio-primer-ancla"})
        self.assertEqual(captured["headers"][subject.KEY_HEADER], KEY)
        self.assertEqual(captured["timeout"], 8)
        self.assertNotIn(KEY, json.dumps(result))

    def test_wrong_node_payload_hash_or_receipt_digest_fail_closed(self):
        self.provision()
        self.key_file()
        wrong_node = self.receipt(node="onexstation")
        self.assertEqual(subject.declarar_edificio(self.base,
            transport=self.transport_for(wrong_node))["causa"], "recibo_no_coincide")
        wrong_hash = self.receipt()
        wrong_hash["payload_sha256"] = "00" * 32
        wrong_hash["recibo_sha256"] = hashlib.sha256(subject._canonical(
            {k: v for k, v in wrong_hash.items() if k != "recibo_sha256"})).hexdigest()
        self.assertEqual(subject.declarar_edificio(self.base,
            transport=self.transport_for(wrong_hash))["causa"], "recibo_no_coincide")
        invalid_digest = self.receipt()
        invalid_digest["recibo_sha256"] = "00" * 32
        self.assertEqual(subject.declarar_edificio(self.base,
            transport=self.transport_for(invalid_digest))["causa"], "recibo_no_coincide")

    def test_http_errors_redirects_oversize_and_bad_json_do_not_claim_success(self):
        self.provision()
        self.key_file()
        rejected = {"esquema": subject.RECEIPT_SCHEMA, "estado": "NO_DATA", "causa": "emisor_no_autorizado"}
        self.assertEqual(subject.declarar_edificio(self.base,
            transport=self.transport_for(rejected, status=401))["causa"], "emisor_no_autorizado")
        self.assertEqual(subject.declarar_edificio(self.base,
            transport=lambda *args: (302, b"{}", "https://elsewhere.example/"))["causa"], "destino_no_coincide")
        self.assertEqual(subject.declarar_edificio(self.base,
            transport=lambda *args: (200, b"x" * (subject.MAX_RESPONSE + 1), subject.ENDPOINT))["causa"],
            "respuesta_fuera_de_rango")
        self.assertEqual(subject.declarar_edificio(self.base,
            transport=lambda *args: (200, b"not-json", subject.ENDPOINT))["causa"], "respuesta_mal_formada")

    def test_network_failure_returns_typed_no_data_without_exception_text(self):
        self.provision()
        self.key_file()
        result = subject.declarar_edificio(self.base,
            transport=lambda *args: (_ for _ in ()).throw(OSError("secret path")))
        self.assertEqual(result, {"estado": "NO_DATA", "causa": "aduana_no_disponible"})


if __name__ == "__main__":
    unittest.main()
