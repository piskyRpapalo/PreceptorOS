"""E6: explicit import, exact local-origin gate, pinned view and read-back."""
import hashlib
import importlib.util
from importlib.machinery import SourceFileLoader
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

import creacion_publicacion as C
from creacion_store import CreationStore

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "tests" / "fixtures" / "creation" / "valid.json"
SERVER_PATH = ROOT / "bin" / "preceptoros-pwa"
SPEC = importlib.util.spec_from_loader(
    "creation_e6_pwa", SourceFileLoader("creation_e6_pwa", str(SERVER_PATH)))
PWA = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PWA)


class Handler:
    def __init__(self, body=b"", headers=None, path="/api/creaciones"):
        self.path = path
        self.headers = headers or {}
        self.rfile = io.BytesIO(body)
        self.wfile = io.BytesIO()
        self.server = SimpleNamespace(server_address=("127.0.0.1", 8740))
        self.code = None
        self.response_headers = {}

    def _json(self, code, value):
        self.code, self.body = code, value

    def send_response(self, code):
        self.code = code

    def send_header(self, name, value):
        self.response_headers[name] = value

    def end_headers(self):
        pass

    def _creacion_store(self):
        return self.store

    def _servir_creacion_asset(self, name):
        return PWA.PWA._servir_creacion_asset(self, name)

    def _leer(self):
        return self.body_data


class CreationPublication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = FIXTURE.read_bytes()

    def test_origin_gate_is_exact_loopback_same_origin_only(self):
        self.assertTrue(C.origen_local_valido("http://127.0.0.1:8740", "127.0.0.1:8740", 8740))
        self.assertTrue(C.origen_local_valido("http://localhost:8740", "localhost:8740", 8740))
        for origin, host in (("https://127.0.0.1:8740", "127.0.0.1:8740"),
                             ("http://evil.example", "127.0.0.1:8740"),
                             ("http://127.0.0.1:8741", "127.0.0.1:8740"),
                             ("null", "127.0.0.1:8740"), (None, "127.0.0.1:8740")):
            self.assertFalse(C.origen_local_valido(origin, host, 8740))

    def test_authorized_post_persists_and_independent_get_returns_exact_package(self):
        with tempfile.TemporaryDirectory() as directory:
            store = CreationStore(Path(directory) / "creaciones")
            with mock.patch.object(PWA.PWA, "_creacion_store", lambda _self: store):
                headers = {"Origin": "http://127.0.0.1:8740", "Host": "127.0.0.1:8740",
                           "Content-Type": "application/json", "Content-Length": str(len(self.package))}
                post = Handler(self.package, headers)
                post.store = store
                PWA.PWA._creacion_publicar(post)
                self.assertEqual(post.code, 201)
                self.assertEqual(post.body["estado"], "publicado")
                identifier = hashlib.sha256(json.loads(self.package)["manifest"].encode()).hexdigest()
                self.assertEqual(post.body["id"], identifier)
                self.assertEqual(post.body["url"], "/creaciones/" + identifier)
                self.assertTrue((Path(directory) / "creaciones" / (identifier + ".json")).is_file())
                duplicate = Handler(self.package, headers)
                duplicate.store = store
                PWA.PWA._creacion_publicar(duplicate)
                self.assertEqual(duplicate.code, 200)
                restarted = CreationStore(Path(directory) / "creaciones")
                with mock.patch.object(PWA.PWA, "_creacion_store", lambda _self: restarted):
                    read = Handler(path="/api/creaciones/" + identifier)
                    read.store = restarted
                    PWA.PWA._creacion_leer(read, read.path)
                self.assertEqual(read.code, 200)
                self.assertEqual(read.wfile.getvalue(), self.package)
                self.assertEqual(read.response_headers["Cache-Control"], "no-store")

    def test_bad_origin_content_type_and_size_never_write(self):
        with tempfile.TemporaryDirectory() as directory:
            store = CreationStore(Path(directory) / "creaciones")
            with mock.patch.object(PWA.PWA, "_creacion_store", lambda _self: store):
                bad = Handler(self.package, {"Origin": "https://evil.example", "Host": "127.0.0.1:8740",
                    "Content-Type": "application/json", "Content-Length": str(len(self.package))})
                bad.store = store
                PWA.PWA._creacion_publicar(bad)
                self.assertEqual(bad.code, 403)
                wrong_type = Handler(self.package, {"Origin": "http://127.0.0.1:8740", "Host": "127.0.0.1:8740",
                    "Content-Type": "text/plain", "Content-Length": str(len(self.package))})
                wrong_type.store = store
                PWA.PWA._creacion_publicar(wrong_type)
                self.assertEqual(wrong_type.code, 415)
                too_big = Handler(headers={"Origin": "http://127.0.0.1:8740", "Host": "127.0.0.1:8740",
                    "Content-Type": "application/json", "Content-Length": str(C.MAX_PACKAGE + 1)})
                too_big.store = store
                PWA.PWA._creacion_publicar(too_big)
                self.assertEqual(too_big.code, 413)
                self.assertFalse((Path(directory) / "creaciones").exists())

    def test_preflight_is_local_and_legacy_charter_post_keeps_its_route(self):
        allowed = Handler(path="/api/creaciones", headers={
            "Origin": "http://127.0.0.1:8740", "Host": "127.0.0.1:8740",
            "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"})
        PWA.PWA.do_OPTIONS(allowed)
        self.assertEqual(allowed.code, 204)
        self.assertEqual(allowed.response_headers["Access-Control-Allow-Origin"], "http://127.0.0.1:8740")
        denied = Handler(path="/api/creaciones", headers={
            "Origin": "https://evil.example", "Host": "127.0.0.1:8740",
            "Access-Control-Request-Method": "POST"})
        PWA.PWA.do_OPTIONS(denied)
        self.assertEqual(denied.code, 403)
        charter = Handler(path="/api/nodo/export")
        charter.body_data = {"credential": "fixture"}
        with mock.patch.object(PWA._nodo_export, "enviar", return_value={"estado": "encolado", "http": 202}):
            PWA.PWA._despachar_post(charter)
        self.assertEqual(charter.code, 202)
        self.assertEqual(charter.body, {"estado": "encolado"})

    def test_stable_view_and_assets_are_confined_to_the_pinned_distribution(self):
        assets = ROOT / "assets" / "creation-view"
        manifest = C.asset_manifest(assets)
        self.assertEqual(len(manifest), 3)
        for name, descriptor in manifest.items():
            data, _media = C.read_asset(assets, name)
            self.assertEqual(len(data), descriptor["size"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), descriptor["sha256"])
        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "view"
            import shutil
            shutil.copytree(assets, copy)
            (copy / "creation_read.js").write_bytes(b"changed")
            with self.assertRaisesRegex(C.CreationError, "digest mismatch"):
                C.read_asset(copy, "creation_read.js")
        for name in ("../app.html", "/etc/passwd"):
            with self.assertRaises(C.CreationError):
                C.read_asset(assets, name)
        view = Handler(path="/creaciones/" + "a" * 64)
        view.store = None
        PWA.PWA._creacion_vista(view, view.path)
        self.assertEqual(view.code, 200)
        self.assertIn(b"Verified creation", view.wfile.getvalue())
        missing = Handler(path="/creaciones/not-an-id")
        PWA.PWA._creacion_vista(missing, missing.path)
        self.assertEqual(missing.code, 404)

    def test_file_selection_does_not_publish_and_only_submit_sends(self):
        source = (ROOT / "interface" / "creation_publish.js").read_text(encoding="utf-8")
        selection = source.split("input.addEventListener('change'", 1)[1].split(
            "form.addEventListener('submit'", 1)[0]
        self.assertNotIn("fetch(", selection)
        self.assertEqual(source.count("fetch('/api/creaciones'"), 1)
        self.assertIn("event.preventDefault()", source)

    def test_sabotage_switch_requires_tampered_package_to_pass(self):
        damaged = (ROOT / "tests" / "fixtures" / "creation" / "altered-audio.json").read_bytes()
        store = CreationStore(ROOT / ".creation-publication-sabotage")
        if os.environ.get("CREATION_PUBLICATION_SABOTAGE") == "1":
            store.put(damaged)
        with self.assertRaises(C.CreationError):
            store.put(damaged)


if __name__ == "__main__":
    unittest.main()
