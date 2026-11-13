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

    def test_intermediate_ancestor_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as other:
            root = Path(other)
            actual = root / "real" / "inner" / "notebook"
            actual.mkdir(parents=True)
            (actual / "wbr.json").write_text(json.dumps({
                "schema": "preceptoros.wbr/1", "period": "2026-W46",
                "summary": "Synthetic receipt", "measured_at": "2026-11-11T09:59:00Z",
                "receipt_sha256": SHA
            }), encoding="utf-8")
            (root / "alias").symlink_to(root / "real", target_is_directory=True)
            state = N.read(root / "alias" / "inner", NOW)
            self.assertEqual(state["reports"][0]["status"], "NO_DATA")
            self.assertEqual(state["reports"][0]["cause"], "symlink_forbidden")
            self.assertEqual(state["agents_cause"], "symlink_forbidden")

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
        self.assertIn('<script src="/notebook.js?v=18"></script>', html)
        self.assertIn('"/notebook.js?v=18"', sw)
        self.assertIn('"/notebook.js": ("notebook.js", "application/javascript; charset=utf-8")', pwa)
        self.assertIn('ruta == "/api/notebook"', pwa)
        self.assertIn('ruta in ("/api/bandeja", "/api/energia", "/api/notebook")', pwa)
        self.assertIn("preceptoros-armazon-v192", sw)
        self.assertIn('<script src="/app.js?v=38"></script>', html)
        self.assertIn('"/app.js?v=38"', sw)
        self.assertIn('<link rel="stylesheet" href="/app.css?v=22">', html)
        self.assertIn('"/app.css?v=22"', sw)
        self.assertIn('window.PreceptorNotebook.load()', app)
        self.assertIn('Promise.allSettled([cargarCuaderno(), cargarPuerta()])', app)


if __name__ == "__main__":
    unittest.main()


class NotebookReceiptsReadTests(unittest.TestCase):
    """APP-NB-03: the Notebook reads receipts.json from its producer and re-checks every row."""
    def setUp(self):
        import notebook_receipts as P
        self.P = P
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        lines = [json.dumps({"ts": "2026-11-11T09:5%d:00Z" % i, "tool": "exec", "cmd_sha": "%016x" % i, "cmd": "secret text",
                             "rc": i % 2, "ms": 25 + i, "out_bytes": 100 * i}) for i in range(3)]
        P.write(self.root, P.project(lines, NOW))

    def tearDown(self):
        self.tmp.cleanup()

    def test_producer_to_reader_round_trip_recomputes_state_from_now(self):
        fresh = N.read(self.root, NOW)
        self.assertIsNone(fresh["receipts_cause"])
        self.assertEqual([(r["result"], r["status"]) for r in fresh["receipts"]],
                         [("ok", "DECLARED"), ("failed", "DECLARED"), ("ok", "DECLARED")])
        later = N.read(self.root, NOW + dt.timedelta(hours=1))
        self.assertEqual({r["status"] for r in later["receipts"]}, {"STALE"})
        self.assertNotIn("secret text", json.dumps(later))

    def test_a_tampered_row_drops_the_whole_list(self):
        path = self.root / "notebook" / "receipts.json"
        data = json.loads(path.read_text())
        data["receipts"][0]["ms"] = 1
        path.write_text(json.dumps(data))
        state = N.read(self.root, NOW)
        self.assertEqual((state["receipts"], state["receipts_cause"]), ([], "receipt_fingerprint_mismatch"))
        data["receipts"][0]["ms"] = "1"
        path.write_text(json.dumps(data))
        self.assertEqual(N.read(self.root, NOW)["receipts_cause"], "receipt_invalid")
        data["schema"] = "preceptoros.notebook-receipts/9"
        path.write_text(json.dumps(data))
        self.assertEqual(N.read(self.root, NOW)["receipts_cause"], "schema_invalid")

    def test_missing_and_future_are_no_data(self):
        (self.root / "notebook" / "receipts.json").unlink()
        self.assertEqual(N.read(self.root, NOW)["receipts_cause"], "file_missing")
        self.P.write(self.root, self.P.project([json.dumps({"ts": "2026-11-11T09:00:00Z", "tool": "exec",
                     "cmd_sha": "0" * 16, "rc": 0, "ms": 1, "out_bytes": 1})], NOW))
        past = N.read(self.root, NOW - dt.timedelta(days=1))
        self.assertEqual((past["receipts"][0]["status"], past["receipts"][0]["cause"]), ("NO_DATA", "future_timestamp"))

    def test_the_tab_has_a_place_for_them(self):
        html = Path(__file__).with_name("interface").joinpath("app.html").read_text(encoding="utf-8")
        js = Path(__file__).with_name("interface").joinpath("notebook.js").read_text(encoding="utf-8")
        self.assertIn('id="notebook-receipts"', html)
        self.assertIn('getElementById("notebook-receipts")', js)
        self.assertIn("not that its output was right", js)
