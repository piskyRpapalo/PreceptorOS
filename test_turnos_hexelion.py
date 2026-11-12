"""META-HARNESS-01 · what happened to each request: door receipts, pairing, attribution and one state for all readers."""
from __future__ import annotations

import hashlib
import importlib.machinery
import importlib.util
import io
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import canales  # noqa: E402
import hexelion_book  # noqa: E402
import turnos_hexelion as T  # noqa: E402

NOW = "2026-11-12T13:30:00Z"


def _pwa():
    loader = importlib.machinery.SourceFileLoader("preceptoros_pwa_turnos", str(ROOT / "bin" / "preceptoros-pwa"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


PWA = _pwa()


def msg(n, voz, texto="x", **machine):
    rol = machine.pop("rol", "")
    return {"n": n, "t": "2026-11-12T13:%02d:00Z" % (n % 60), "voz": voz, "texto": texto, "rol": rol,
            "sello": "DECLARADO", "maquina": machine}


def states(messages):
    return {t["n"]: t["state"] for t in T.turns(messages)}


class Pairing(unittest.TestCase):
    def test_attribution_of_every_kind_of_answer(self):
        rows = T.turns([
            msg(1, "soberano", "what is the Notebook?"),
            msg(2, "hexelion", "quote", pregunta_n=1, modelo="hexelion:latest", ms=20495.5, fuentes=[{"id": 1}]),
            msg(3, "soberano", "energy?"),
            msg(4, "orquestador", "Energy: 3 W", pregunta_n=3),
            msg(5, "soberano", "hello"),
            msg(6, "hexelion-door", "No answer · station_unavailable", pregunta_n=5, causa="station_unavailable"),
            msg(7, "soberano", "read LAB 173", via="app", para="claude"),
            msg(8, "claude", "LAB 173 read"),
        ])
        by = {t["n"]: t for t in rows}
        self.assertEqual([t["n"] for t in rows], [7, 5, 3, 1])
        self.assertEqual((by[1]["state"], by[1]["answered_by_name"], by[1]["evidence"]), ("ANSWERED", "Hexelion", "1 verified source"))
        self.assertEqual(by[1]["sentence"], "Hexelion answered in 20.5 s with 1 verified source (hexelion:latest).")
        self.assertEqual((by[3]["state"], by[3]["answered_by_name"]), ("LOCAL_SENSOR", "Local sensor"))
        self.assertEqual((by[5]["state"], by[5]["answered_by"], by[5]["cause"]), ("NO_ANSWER", None, "station_unavailable"))
        self.assertEqual((by[7]["state"], by[7]["to_name"], by[7]["answered_by_name"]), ("REPLIED", "Claude", "Claude"))

    def test_a_voice_that_was_not_addressed_closes_nothing(self):
        self.assertEqual(states([msg(1, "soberano"), msg(2, "claude", "unrelated note"), msg(3, "codex", "also")]),
                         {1: "NO_REPLY_RECORDED"})
        self.assertEqual(states([msg(1, "soberano", via="app", para="codex"), msg(2, "claude", "not codex")]),
                         {1: "NO_REPLY_RECORDED"})

    def test_a_rack_agent_asking_hexelion_is_a_turn_in_its_own_name(self):
        rows = T.turns([msg(1, "claude", "q", rol="rack CLI agent"),
                        msg(2, "hexelion", "a", pregunta_n=1, modelo="m", ms=5, fuentes=[])])
        self.assertEqual((rows[0]["asked_by_name"], rows[0]["state"]), ("Claude", "ANSWERED"))

    def test_malformed_events_do_not_invent_answers(self):
        self.assertEqual(states([msg(1, "soberano"), msg(2, "hexelion", "words")]), {1: "ANSWERED_UNVERIFIED"})
        self.assertEqual(states([msg(1, "soberano"), msg(2, "hexelion", "a", pregunta_n=99, modelo="m", ms=5)]),
                         {1: "NO_REPLY_RECORDED"})
        bad = [{"n": "1", "voz": "soberano"}, None, {"n": 2, "voz": "soberano", "maquina": "not a dict", "t": NOW},
               msg(3, "soberano", via="app", para="root"), msg(4, "hexelion", "a", pregunta_n=2, modelo="m", ms=-1)]
        self.assertEqual(states(bad), {2: "ANSWERED_UNVERIFIED"})

    def test_nothing_is_ever_reported_as_running(self):
        rows = T.turns([msg(1, "soberano"), msg(2, "soberano", via="app", para="codex")])
        text = json.dumps(rows).lower()
        for word in ("running", "working on it now", "in progress", "waiting"):
            self.assertNotIn(word, text.replace("nothing is recorded as working on it", ""))
        self.assertTrue(all(t["state"] == "NO_REPLY_RECORDED" for t in rows))

    def test_screen_reader_and_machine_say_the_same(self):
        for t in T.turns([msg(1, "soberano"), msg(2, "hexelion-door", pregunta_n=1, causa="station_timeout")]):
            self.assertEqual(t["next"], T.NEXT[t["state"]])
            self.assertIn(t["sentence"], t["reader"])
            self.assertIn(t["next"], t["reader"])
            self.assertEqual(t["sentence"], "The local model took too long and was stopped, so nobody answered.")
        odd = T.turns([msg(1, "soberano"), msg(2, "hexelion-door", pregunta_n=1, causa="a_new_cause")])[0]
        self.assertEqual(odd["sentence"], "Hexelion did not answer: a new cause.")   # unknown causes are read, not guessed

    def test_projection_and_its_no_data(self):
        p = T.project({"estado": "MEDIDO", "mensajes": [msg(1, "soberano")]}, NOW)
        self.assertEqual((p["schema"], p["state"], p["counts"]), ("preceptoros.hexelion-turns/1", "MEASURED", {"NO_REPLY_RECORDED": 1}))
        self.assertEqual(T.project({"estado": "NO_DATA", "causa": "el canal aún no tiene mensajes"}, NOW)["cause"],
                         "el canal aún no tiene mensajes")
        self.assertEqual(T.project({"estado": "MEDIDO", "mensajes": []}, NOW)["cause"], "no_request_in_thread")
        self.assertEqual(json.dumps(T.project({"estado": "MEDIDO", "mensajes": [msg(1, "soberano")]}, NOW)),
                         json.dumps(T.project({"estado": "MEDIDO", "mensajes": [msg(1, "soberano")]}, NOW)))


class Door(unittest.TestCase):
    """The real door with a real thread in a temporary home: a failed request leaves an attributed receipt."""
    def ask(self, tmp, proxy_result, memory=None):
        payload = json.dumps({"texto": "what is the Notebook?"}).encode()
        h = PWA.PWA.__new__(PWA.PWA)
        h.path, h.command = "/api/hexelion/chat", "POST"
        h.headers = {"Content-Type": "application/json", "Content-Length": str(len(payload))}
        h.rfile, h.client_address, h.server = io.BytesIO(payload), ("127.0.0.1", 1), SimpleNamespace(ruta_db="unused")
        out = {}
        h._json = lambda code, body: out.update(code=code, body=body)
        h._nodo_local_autorizado = lambda: True
        text = "The Notebook shows agents."
        evidence = memory or {"esquema": hexelion_book.SCHEMA, "estado": "MEASURED", "fuentes": [
            {"id": 3, "updated_at": "2026-11-06T00:00:00Z", "sha256": hashlib.sha256(text.encode()).hexdigest(), "texto": text}]}
        with mock.patch.object(PWA._casa, "raiz", return_value=pathlib.Path(tmp)), \
             mock.patch.object(canales, "_registro", return_value=None), \
             mock.patch.object(PWA._memory_lookup, "buscar", return_value=evidence), \
             mock.patch.object(PWA._indice_rack, "buscar", return_value={"estado": "NO_DATA", "fuentes": []}), \
             mock.patch.object(PWA._hexelion_proxy, "ask", return_value=proxy_result):
            PWA.PWA._hexelion_chat(h)
        return out, canales.lee("orquesta", base=tmp)

    def test_disconnected_station_leaves_a_door_receipt_never_in_hexelions_voice(self):
        with tempfile.TemporaryDirectory() as tmp:
            out, thread = self.ask(tmp, {"estado": "NO_DATA", "causa": "station_unavailable"})
            self.assertEqual((out["code"], out["body"]["causa"]), (503, "station_unavailable"))
            voices = [m["voz"] for m in thread["mensajes"]]
            self.assertEqual(voices, ["soberano", "hexelion-door"])
            door = thread["mensajes"][1]
            self.assertEqual((door["sello"], door["maquina"]["pregunta_n"], door["maquina"]["causa"]),
                             ("NO_DATA", thread["mensajes"][0]["n"], "station_unavailable"))
            turn = T.project(thread, NOW)["turns"][0]
            self.assertEqual((turn["state"], turn["answered_by"]), ("NO_ANSWER", None))

    def test_missing_evidence_is_also_a_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            out, thread = self.ask(tmp, {"estado": "MEASURED"}, memory={"estado": "NO_DATA", "causa": "no_matches", "fuentes": []})
            self.assertEqual(T.project(thread, NOW)["turns"][0]["state"], "NO_ANSWER")

    def test_an_answer_names_the_question_it_answers(self):
        with tempfile.TemporaryDirectory() as tmp:
            answer = json.dumps({"citas": [{"id": 3, "quote": "The Notebook shows agents."}]})
            out, thread = self.ask(tmp, {"estado": "MEASURED", "modelo": PWA._hexelion_proxy.MODEL, "ms": 12.0, "texto": answer})
            self.assertEqual(out["code"], 200, out)
            q, a = thread["mensajes"]
            self.assertEqual((a["voz"], a["maquina"]["pregunta_n"]), ("hexelion", q["n"]))
            self.assertEqual(T.project(thread, NOW)["turns"][0]["state"], "ANSWERED")

    def test_the_door_receipt_refuses_a_bad_question_number_and_cleans_the_cause(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(canales, "_registro", return_value=None):
            with self.assertRaises(canales.CanalRechazado):
                canales.di_recibo_puerta("orquesta", 0, "x", base=tmp)
            m = canales.di_recibo_puerta("orquesta", 4, "Station Down! <b>", base=tmp)
            self.assertEqual((m["voz"], m["maquina"]["causa"]), ("hexelion-door", "station_down_b"))

    def test_turns_route_is_loopback_only(self):
        h = PWA.PWA.__new__(PWA.PWA)
        h.path, h.client_address, out = "/api/hexelion/turnos", ("192.0.2.9", 1), {}
        h._json = lambda code, body: out.update(code=code)
        PWA.PWA._turnos_leer(h)
        self.assertEqual(out["code"], 403)


class Views(unittest.TestCase):
    def test_notebook_and_lab_render_the_same_turn_without_moving_focus_or_sound(self):
        html = (ROOT / "interface/app.html").read_text(encoding="utf-8")
        js = (ROOT / "interface/notebook.js").read_text(encoding="utf-8")
        app = (ROOT / "interface/app.js").read_text(encoding="utf-8")
        for ident in ("notebook-turns", "notebook-turns-status", "lab-turno", "lab-turno-status"):
            self.assertIn('id="%s"' % ident, html)
        self.assertIn('loadTurns("lab-turno", "lab-turno-status", 1)', app)
        self.assertIn('loadTurns("notebook-turns", "notebook-turns-status", 12)', js)
        block = js[js.index("const turnStates"):js.index("function mount()")]
        self.assertIn("card(x.by + \" asked \" + x.to", block)
        self.assertIn("x.sentence", block)
        self.assertIn("spoken[statusId] !== summary", block)          # speaks only when the summary changed
        self.assertNotRegex(block, r"\.focus\(|speechSynthesis|AudioContext|innerHTML|setInterval")

    def test_projectTurns_in_node_keeps_only_known_states(self):
        script = ("const N=require('./interface/notebook.js');const p=N.projectTurns({schema:'preceptoros.hexelion-turns/1',"
                  "state:'MEASURED',turns:[{n:1,state:'RUNNING',sentence:'s'},{n:'2'},{n:3,state:'ANSWERED',answer_n:4}]});"
                  "console.log(JSON.stringify(p.turns.map(t=>[t.n,t.state,t.answer])))")
        r = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True)
        if r.returncode == 127:
            self.skipTest("NO_DATA: node not installed")
        self.assertEqual(json.loads(r.stdout), [[1, "NO_DATA", None], [3, "ANSWERED", 4]])


if __name__ == "__main__":
    unittest.main()
