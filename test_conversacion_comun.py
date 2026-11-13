"""APP-ROUTER-01 · one conversation, many preceptors: the projection, the addressed send, and the Talk wiring."""
from __future__ import annotations

import datetime as dt
import importlib.machinery
import importlib.util
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import canales  # noqa: E402
import conversacion_comun as C  # noqa: E402

NOW = dt.datetime(2026, 11, 12, 12, 0, tzinfo=dt.timezone.utc)


def _pwa():
    loader = importlib.machinery.SourceFileLoader("preceptoros_pwa_router", str(ROOT / "bin" / "preceptoros-pwa"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


PWA = _pwa()


def reading(*msgs):
    return {"estado": "MEDIDO", "mensajes": [dict({"maquina": {}, "sello": "DECLARADO", "rol": ""}, **m) for m in msgs]}


class Projection(unittest.TestCase):
    def test_every_voice_gets_an_explicit_identity_and_kind(self):
        r = reading({"n": 1, "t": "2026-11-12T11:00:00Z", "voz": "soberano", "texto": "hi", "maquina": {"via": "app", "para": "claude"}},
                    {"n": 2, "t": "2026-11-12T11:01:00Z", "voz": "claude", "texto": "read it"},
                    {"n": 3, "t": "2026-11-12T11:02:00Z", "voz": "hexelion", "texto": "quote",
                     "maquina": {"modelo": "hexelion:latest", "fuentes": [{"id": 9, "updated_at": "2026-11-06T00:00:00Z", "sha256": "a" * 64}]}},
                    {"n": 4, "t": "2026-11-12T11:03:00Z", "voz": "orquestador", "texto": "Energy: 3 W"},
                    {"n": 5, "t": "2026-11-12T11:04:00Z", "voz": "stranger", "texto": "who am I"})
        p = C.project(r, NOW)
        self.assertEqual(p["schema"], "preceptoros.multipreceptor/1")
        self.assertEqual(p["state"], "MEASURED")
        self.assertEqual([(m["from"], m["kind"]) for m in p["messages"]],
                         [("soberano", "person"), ("claude", "rack-cli"), ("hexelion", "private"),
                          ("orquestador", "sensor"), ("stranger", "unknown")])
        self.assertEqual(p["messages"][0]["to"], "claude")
        self.assertEqual(p["messages"][2]["sources"], ["#9 · 2026-11-06T00:00:00Z · aaaaaaaaaaaa"])
        self.assertEqual(p["messages"][2]["model"], "hexelion:latest")
        self.assertEqual(p["last"], 5)
        self.assertIn("not a signature", p["authority"])

    def test_since_limit_and_cut(self):
        r = reading(*[{"n": i, "t": "2026-11-12T11:00:00Z", "voz": "claude", "texto": "x" * (C.MAX_SHOWN + 5)} for i in range(1, 51)])
        p = C.project(r, NOW, since=5)
        self.assertEqual(len(p["messages"]), C.MAX_MESSAGES)
        self.assertEqual(p["hidden"], 45 - C.MAX_MESSAGES)
        self.assertEqual(p["messages"][-1]["n"], 50)
        self.assertTrue(all(m["cut"] and len(m["text"]) == C.MAX_SHOWN for m in p["messages"]))
        self.assertEqual(C.project(r, NOW, since=50)["messages"], [])

    def test_unreadable_thread_is_no_data_with_cause_and_no_last_spoke(self):
        p = C.project({"estado": "NO_DATA", "causa": "el canal aún no tiene mensajes", "mensajes": []}, NOW)
        self.assertEqual((p["state"], p["cause"], p["messages"], p["last"]), ("NO_DATA", "el canal aún no tiene mensajes", [], 0))
        self.assertTrue(all(d["last_spoke"].startswith("NO_DATA") for d in p["destinations"]))
        self.assertEqual(C.project(None, NOW)["cause"], "thread_unreadable")

    def test_a_recipient_outside_the_table_is_not_shown_as_someone(self):
        r = reading({"n": 1, "t": "2026-11-12T11:00:00Z", "voz": "soberano", "texto": "x", "maquina": {"para": "root"}})
        self.assertNotIn("to", C.project(r, NOW)["messages"][0])

    def test_destinations_say_transport_and_last_spoke(self):
        r = reading({"n": 1, "t": "2026-11-12T11:59:00Z", "voz": "claude", "texto": "x"})
        d = {x["id"]: x for x in C.destinations(r, NOW)}
        self.assertEqual((d["claude"]["last_spoke"], d["claude"]["age_s"]), ("2026-11-12T11:59:00Z", 60))
        self.assertEqual(d["codex"]["last_spoke"], "NO_DATA: never spoke in this thread")
        for ext in ("chatgpt", "mistral-web", "codex-web"):
            self.assertFalse(d[ext]["addressable"])
            self.assertTrue(d[ext]["transport"].startswith("NO_DATA: "))
        self.assertEqual(d["hexelion"]["route"], "station")

    def test_rack_cli_table_is_the_server_voice_allowlist(self):
        rack = {d["id"] for d in C.DESTINATIONS if d["kind"] == "rack-cli"}
        self.assertEqual(rack, set(PWA.AGENT_VOICES))
        self.assertEqual(len({d["id"] for d in C.DESTINATIONS}), len(C.DESTINATIONS))
        self.assertNotIn("soberano", C.BY_ID)

    def test_same_input_same_output(self):
        r = reading({"n": 1, "t": "2026-11-12T11:00:00Z", "voz": "claude", "texto": "x"})
        self.assertEqual(json.dumps(C.project(r, NOW), sort_keys=True), json.dumps(C.project(r, NOW), sort_keys=True))


class Send(unittest.TestCase):
    def test_check_send(self):
        self.assertEqual(C.check_send({"para": "claude", "texto": "  hi  "}), ("claude", "hi", None))
        cases = [({"para": "chatgpt", "texto": "hi"}, "no_transport"), ({"para": "hexelion", "texto": "hi"}, "use_station_door"),
                 ({"para": "soberano", "texto": "hi"}, "recipient_unknown"), ({"para": "lab", "texto": "hi"}, "recipient_unknown"),
                 ({"para": "claude", "texto": " "}, "text_invalid"), ({"para": "claude", "texto": "x" * 601}, "text_invalid"),
                 ({"para": "claude", "texto": "hi", "voz": "claude"}, "request_invalid"), ([], "request_invalid"),
                 ({"para": 1, "texto": "hi"}, "recipient_unknown")]
        for data, cause in cases:
            self.assertEqual(C.check_send(data)[2], cause, data)

    def test_di_soberano_stores_the_recipient_and_refuses_bad_ones(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(canales, "_registro", return_value=None):
            m = canales.di_soberano("orquesta", "hola", base=tmp, para="claude")
            self.assertEqual((m["voz"], m["maquina"]), ("soberano", {"via": "app", "para": "claude"}))
            self.assertEqual(canales.di_soberano("orquesta", "sin destino", base=tmp)["maquina"], {"via": "app"})
            for bad in ("Soberano", "s0berano", "x y", 3):
                with self.assertRaises(canales.CanalRechazado):
                    canales.di_soberano("orquesta", "hola", base=tmp, para=bad)


class Door(unittest.TestCase):
    def call(self, method, path, body=None, local=True, loopback=True, tmp=None):
        raw = json.dumps(body).encode() if body is not None else b""
        h = PWA.PWA.__new__(PWA.PWA)
        h.path, h.command = path, method
        h.headers = {"Content-Type": "application/json", "Content-Length": str(len(raw))}
        h.rfile, h.client_address, h.server = io.BytesIO(raw), ("127.0.0.1" if loopback else "192.0.2.9", 1), SimpleNamespace()
        out = {}
        h._json = lambda code, b: out.update(code=code, body=b)
        h._nodo_local_autorizado = lambda: local
        with mock.patch.object(PWA._casa, "raiz", return_value=pathlib.Path(tmp)), \
             mock.patch.object(canales, "_registro", return_value=None):
            (PWA.PWA._conversacion_enviar if method == "POST" else PWA.PWA._conversacion_leer)(h)
        return out

    def test_addressed_send_lands_in_the_thread_and_reads_back_with_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            sent = self.call("POST", "/api/conversacion", {"para": "codex", "texto": "check LAB #172"}, tmp=tmp)
            self.assertEqual((sent["code"], sent["body"]["state"], sent["body"]["to"]), (200, "DELIVERED_TO_THREAD", "codex"))
            self.assertTrue(sent["body"]["reply"].startswith("NO_DATA"))
            canales.di("orquesta", "codex", "LAB #172 read", base=tmp)
            got = self.call("GET", "/api/conversacion?desde=0", tmp=tmp)["body"]
            self.assertEqual([(m["name"], m["kind"], m.get("to")) for m in got["messages"]],
                             [("You", "person", "codex"), ("Codex", "rack-cli", None)])
            since = self.call("GET", "/api/conversacion?desde=%d" % got["messages"][0]["n"], tmp=tmp)["body"]
            self.assertEqual([m["from"] for m in since["messages"]], ["codex"])

    def test_refusals_write_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            for body, local, code, cause in [({"para": "chatgpt", "texto": "x"}, True, 409, "no_transport"),
                                             ({"para": "hexelion", "texto": "x"}, True, 409, "use_station_door"),
                                             ({"para": "claude", "texto": "x"}, False, 403, "local_origin_required"),
                                             ({"para": "claude", "texto": "x", "sello": "FIRMADO"}, True, 400, "request_invalid")]:
                out = self.call("POST", "/api/conversacion", body, local=local, tmp=tmp)
                self.assertEqual((out["code"], out["body"]["cause"]), (code, cause), body)
            self.assertFalse((pathlib.Path(tmp) / "registro" / "eventos.db").exists())
            self.assertEqual(self.call("GET", "/api/conversacion", tmp=tmp)["body"]["state"], "NO_DATA")
            self.assertEqual(self.call("GET", "/api/conversacion", loopback=False, tmp=tmp)["code"], 403)
            self.assertEqual(self.call("GET", "/api/conversacion?desde=x", tmp=tmp)["code"], 400)


class Shell(unittest.TestCase):
    def test_talk_reads_the_thread_and_marks_its_own_drafts(self):
        html = (ROOT / "interface/app.html").read_text(encoding="utf-8")
        sw = (ROOT / "interface/sw.js").read_text(encoding="utf-8")
        js = (ROOT / "interface/app.js").read_text(encoding="utf-8")
        conv = (ROOT / "interface/conversacion.js").read_text(encoding="utf-8")
        server = (ROOT / "bin/preceptoros-pwa").read_text(encoding="utf-8")
        self.assertIn('<script src="/conversacion.js?v=3"></script>', html)
        self.assertLess(html.index("/insertor.js?v=2"), html.index("/conversacion.js?v=3"))
        self.assertLess(html.index("/conversacion.js?v=3"), html.index("/app.js?v=30"))
        self.assertIn('"/conversacion.js?v=3"', sw)
        self.assertIn('"/conversacion.js": ("conversacion.js",', server)
        self.assertIn('"interface/conversacion.js"', (ROOT / "version.py").read_text(encoding="utf-8"))
        self.assertIn('id="conv-destinos"', html)
        self.assertIn('li.classList.add("local")', js)
        self.assertIn("sync({ replaceLocal: true })", js)
        self.assertIn("conversacion.routes()", js)
        self.assertNotRegex(conv, r"localStorage|sessionStorage|sendBeacon|innerHTML")
        self.assertLess(len(conv.encode()), 8192)

    def test_insertor_cases_pass(self):
        r = subprocess.run(["node", "--test", "tests/insertor_cases.cjs"], cwd=ROOT, capture_output=True, text=True)
        if r.returncode == 127:
            self.skipTest("NO_DATA: node not installed")
        self.assertEqual(r.returncode, 0, r.stdout[-800:])


if __name__ == "__main__":
    unittest.main()
