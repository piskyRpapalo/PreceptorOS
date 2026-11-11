"""Notebook read-only fixtures: no live claims, symlink escapes or silent coercion."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import tempfile
import unittest

import notebook_read as N

NOW = dt.datetime(2026, 11, 11, 10, 0, tzinfo=dt.timezone.utc)
SHA = hashlib.sha256(b"receipt").hexdigest()


class NotebookReadTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "notebook").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, data):
        path = self.root / "notebook" / (name + ".json")
        path.write_text(json.dumps(data), encoding="utf-8")

    def test_missing_never_becomes_running_or_measured(self):
        state = N.read(self.root, NOW)
        self.assertEqual(state["agents_status"], "NO_DATA")
        self.assertEqual(state["agents_cause"], "file_missing")
        self.assertEqual([r["status"] for r in state["reports"]], ["NO_DATA", "NO_DATA"])

    def test_declared_recent_heartbeat_not_process_live(self):
        self.write("agents", {
            "schema": "preceptoros.notebook-agents/0",
            "agents": [{"id": "worker-1", "name": "Claude", "role": "builder",
                        "last_seen": "2026-11-11T09:59:20Z", "receipt_sha256": SHA}]
        })
        state = N.read(self.root, NOW)
        self.assertEqual(state["agents_status"], "DECLARADO")
        self.assertEqual(state["agents"][0]["status"], "OBSERVADO")
        self.assertNotIn("LIVE", json.dumps(state))
        self.assertEqual(state["agents"][0]["cause"], "recent_declared_heartbeat")

    def test_stale_and_future_heartbeat(self):
        for stamp, status in [("2026-11-11T09:20:00Z", "STALE"),
                              ("2026-11-12T09:20:00Z", "NO_DATA")]:
            with self.subTest(stamp=stamp):
                self.write("agents", {
                    "schema": "preceptoros.notebook-agents/0",
                    "agents": [{"id": "worker-1", "name": "Claude", "role": "builder",
                                "last_seen": stamp, "receipt_sha256": SHA}]
                })
                self.assertEqual(N.read(self.root, NOW)["agents"][0]["status"], status)

    def test_wbr_mbr_only_declared_until_independent_receipt_verification(self):
        for name in ("wbr", "mbr"):
            self.write(name, {
                "schema": "preceptoros." + name + "/1",
                "period": "2026-W46" if name == "wbr" else "2026-11",
                "summary": "3 PRs proposed, 1 independently tested",
                "measured_at": "2026-11-11T09:01:00Z",
                "receipt_sha256": SHA
            })
        state = N.read(self.root, NOW)
        self.assertEqual([r["status"] for r in state["reports"]], ["DECLARADO", "DECLARADO"])
        for row in state["reports"]:
            self.assertEqual(row["cause"], "origin_receipt_not_independently_verified")

    def test_duplicate_key_rejected(self):
        (self.root / "notebook" / "wbr.json").write_text(
            '{"schema":"preceptoros.wbr/1","schema":"preceptoros.wbr/1"}',
            encoding="utf-8")
        self.assertEqual(N.read(self.root, NOW)["reports"][0]["cause"], "invalid_json")

    def test_symlink_forbidden(self):
        with tempfile.TemporaryDirectory() as other:
            outside = Path(other) / "secret.json"
            outside.write_text('{"schema":"preceptoros.wbr/1"}')
            (self.root / "notebook" / "wbr.json").symlink_to(outside)
            self.assertEqual(N.read(self.root, NOW)["reports"][0]["cause"], "symlink_forbidden")

    def test_oversized_and_invalid_agent_census(self):
        (self.root / "notebook" / "agents.json").write_bytes(b"x" * 9000)
        self.assertEqual(N.read(self.root, NOW)["agents_cause"], "file_oversized")
        self.write("agents", {"schema": "preceptoros.notebook-agents/0",
                              "agents": [{"id": "../bad", "name": "X", "role": "Y",
                                          "last_seen": "2026-11-11T09:59:20Z",
                                          "receipt_sha256": SHA}]})
        self.assertEqual(N.read(self.root, NOW)["agents_cause"], "agent_invalid")


class NotebookShellTests(unittest.TestCase):
    ROOT = Path(__file__).parent

    def test_notebook_replaces_old_turns_without_deleting_consent(self):
        html = (self.ROOT / "interface/app.html").read_text(encoding="utf-8")
        notebook = html.split('id="panel-cuaderno"', 1)[1].split('id="panel-lab"', 1)[0]
        settings = html.split('id="panel-ajustes"', 1)[1]
        self.assertIn('id="notebook-agents"', notebook)
        self.assertIn('id="notebook-loops"', notebook)
        self.assertIn('id="notebook-reports"', notebook)
        self.assertNotIn('id="turnos"', notebook)
        self.assertIn('id="captura-consent"', settings)
        self.assertIn('id="turnos"', settings)
        self.assertIn('id="recuento"', settings)

    def test_route_and_cache_align(self):
        html = (self.ROOT / "interface/app.html").read_text(encoding="utf-8")
        sw = (self.ROOT / "interface/sw.js").read_text(encoding="utf-8")
        pwa = (self.ROOT / "bin/preceptoros-pwa").read_text(encoding="utf-8")
        app = (self.ROOT / "interface/app.js").read_text(encoding="utf-8")
        self.assertIn('<script src="/notebook.js?v=1"></script>', html)
        self.assertIn('"/notebook.js?v=1"', sw)
        self.assertIn('"/notebook.js": ("notebook.js", "application/javascript; charset=utf-8")', pwa)
        self.assertIn('ruta == "/api/notebook"', pwa)
        self.assertIn('ruta in ("/api/bandeja", "/api/notebook")', pwa)
        self.assertIn("preceptoros-armazon-v159", sw)  # v158 was taken by APP-LIVE-06; the Notebook lands as v159
        self.assertIn('<script src="/app.js?v=19"></script>', html)
        self.assertIn('"/app.js?v=19"', sw)
        self.assertIn('<link rel="stylesheet" href="/app.css?v=15">', html)
        self.assertIn('"/app.css?v=15"', sw)
        self.assertIn('window.PreceptorNotebook.load()', app)
        self.assertIn('if (paneles[panelActual].id === "ajustes") cargarCuaderno()', app)


if __name__ == "__main__":
    unittest.main()
