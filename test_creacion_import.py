"""E5: consume the shared browser package and fail closed on damaged bytes."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import creacion_import as I
from creacion_store import CreationStore

FIXTURES = Path(__file__).parent / "tests" / "fixtures" / "creation"


class CreationImport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid = (FIXTURES / "valid.json").read_bytes()

    def test_cross_language_fixture_and_exact_manifest_bytes(self):
        result = I.validate(self.valid)
        self.assertEqual(result["manifest"]["author"], "Fixture author")
        self.assertTrue(result["manifest_bytes"].startswith(b"\n"))
        self.assertEqual(result["id"], I.hashlib.sha256(result["manifest_bytes"]).hexdigest())
        self.assertEqual(result["frame"]["atoms"][0]["i"][0]["o"], "ribbon")
        self.assertEqual(result["audio"][:4], b"RIFF")

    def test_shared_corruption_fixtures_fail_closed(self):
        for name in ("altered-frame", "altered-audio", "altered-manifest", "altered-signature"):
            with self.subTest(name=name), self.assertRaises(I.CreationError):
                I.validate((FIXTURES / (name + ".json")).read_bytes())

    def test_closed_names_fields_and_route_traversal(self):
        original = json.loads(self.valid)
        for mutate in (
            lambda value: value.update(extra=True),
            lambda value: value["files"].update({"../frame.json": value["files"]["frame.json"]}),
            lambda value: value["files"].pop("frame.json"),
            lambda value: value.update(public_key="F" * 64),
        ):
            broken = json.loads(json.dumps(original))
            mutate(broken)
            with self.subTest(broken=broken.keys()), self.assertRaises(I.CreationError):
                I.validate(json.dumps(broken).encode())

    def test_limits_and_bad_coordinates(self):
        with self.assertRaisesRegex(I.CreationError, "package byte limit"):
            I.validate(b" " * (I.MAX_PACKAGE + 1))
        with self.assertRaisesRegex(I.CreationError, "frame byte limit"):
            I._frame(b" " * I.MAX_FRAME)
        value = I.validate(self.valid)
        frame = value["files"]["frame.json"]
        obj = json.loads(frame)
        obj["atoms"][0]["i"][0]["pts"][0][0] = True
        with self.assertRaisesRegex(I.CreationError, "coordinates"):
            I._frame(json.dumps(obj).encode())

    def test_unbounded_json_integers_fail_closed(self):
        huge = 10 ** 250
        frame = I.validate(self.valid)["files"]["frame.json"]
        obj = json.loads(frame)
        obj["atoms"][0]["i"][0]["pts"][0][0] = huge
        with self.assertRaisesRegex(I.CreationError, "coordinates"):
            I._frame(json.dumps(obj).encode())
        manifest = json.loads(I.validate(self.valid)["manifest_bytes"])
        manifest["files"][0]["size"] = huge
        with self.assertRaisesRegex(I.CreationError, "file descriptor"):
            I._manifest(json.dumps(manifest))

    def test_openssl_absence_is_nodata(self):
        with self.assertRaisesRegex(I.CreationError, "OpenSSL unavailable"):
            I.validate(self.valid, "missing-creation-openssl")

    def test_atomic_store_idempotence_and_restart_read(self):
        with tempfile.TemporaryDirectory() as directory:
            first = CreationStore(directory)
            identifier, created = first.put(self.valid)
            self.assertTrue(created)
            self.assertEqual(list(Path(directory).glob("*.json")), [Path(directory) / (identifier + ".json")])
            self.assertEqual(first.put(self.valid), (identifier, False))
            restarted = CreationStore(directory)
            self.assertEqual(restarted.get(identifier)["package_bytes"], self.valid)
            with self.assertRaises(I.CreationError):
                restarted.get("../" + identifier)

    def test_interrupted_write_leaves_no_publishable_package(self):
        with tempfile.TemporaryDirectory() as directory:
            store = CreationStore(directory)
            with patch("creacion_store.os.link", side_effect=OSError("interrupted")):
                with self.assertRaises(OSError):
                    store.put(self.valid)
            self.assertEqual(list(Path(directory).glob("*.json")), [])
            self.assertEqual(list(Path(directory).glob(".pending-*")), [])
            self.assertIsNone(store.get(I.validate(self.valid)["id"]))

    def test_sabotage_switch_requires_tampered_package_to_pass(self):
        if __import__("os").environ.get("CREATION_IMPORT_SABOTAGE") == "1":
            I.validate((FIXTURES / "altered-audio.json").read_bytes())
        else:
            with self.assertRaises(I.CreationError):
                I.validate((FIXTURES / "altered-audio.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
