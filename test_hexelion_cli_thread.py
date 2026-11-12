"""Agents ask Hexelion in their own thread (cli): the person's thread and its 12-turn view stay the person's."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import canales
import turnos_hexelion
from test_pwa import PWA

ROOT = Path(__file__).resolve().parent


def chat(base, body, headers, client="127.0.0.1"):
    payload = json.dumps(body).encode()
    h = PWA.PWA.__new__(PWA.PWA)
    h.path = "/api/hexelion/chat"
    h.headers = dict(headers, **{"Content-Type": "application/json", "Content-Length": str(len(payload))})
    h.rfile = io.BytesIO(payload)
    h.client_address = (client, 1)
    h.server = SimpleNamespace(ruta_db=str(Path(base) / "absent.db"), server_port=8742)
    out = {}
    h._json = lambda code, b: out.update(code=code, body=b)
    with mock.patch.object(PWA._casa, "raiz", return_value=Path(base)):
        PWA.PWA._hexelion_chat(h)
    return out


class CliThread(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def read(self, thread):
        return canales.lee(thread, 0, base=self.base)

    def test_an_agent_question_and_its_door_receipt_land_in_cli_not_in_the_persons_thread(self):
        out = chat(self.base, {"texto": "what is the app cache version", "voz": "claude"}, {})
        self.assertEqual(out["body"]["estado"], "NO_DATA")                 # no memory db here: the door says why
        cli = self.read("cli")["mensajes"]
        self.assertEqual([m["voz"] for m in cli], ["claude", "hexelion-door"])
        self.assertEqual(cli[1]["maquina"]["pregunta_n"], cli[0]["n"])
        self.assertEqual(self.read("orquesta").get("mensajes") or [], [])

    def test_the_persons_question_stays_in_the_shared_thread(self):
        with mock.patch.object(PWA.PWA, "_nodo_local_autorizado", return_value=True):
            chat(self.base, {"texto": "what is the app cache version"}, {"Origin": "http://127.0.0.1:8742"})
        self.assertEqual([m["voz"] for m in self.read("orquesta")["mensajes"]], ["soberano", "hexelion-door"])
        self.assertEqual(self.read("cli").get("mensajes") or [], [])

    def test_the_cli_thread_reads_as_turns_with_the_same_projection(self):
        chat(self.base, {"texto": "how do I run the gate", "voz": "codex"}, {})
        p = turnos_hexelion.project(self.read("cli"), "2026-11-12T00:00:00Z")
        self.assertEqual((p["state"], p["turns"][0]["asked_by"], p["turns"][0]["state"]), ("MEASURED", "codex", "NO_ANSWER"))

    def test_turns_view_reads_cli_only_when_asked_and_harness_shows_it(self):
        src = (ROOT / "bin/preceptoros-pwa").read_text(encoding="utf-8")
        self.assertIn('.get("thread") == ["cli"]', src)
        self.assertIn('asked = _canales.di("cli", voz', src)
        html = (ROOT / "interface/app.html").read_text(encoding="utf-8")
        for ident in ("harness-cli", "harness-cli-status", "harness-cli-turns"):
            self.assertIn('id="%s"' % ident, html)
        app = (ROOT / "interface/app.js").read_text(encoding="utf-8")
        self.assertIn('loadTurns("harness-cli-turns", "harness-cli-status", 6, "cli")', app)
        self.assertIn("cli", canales.CANALES)


if __name__ == "__main__":
    unittest.main()
