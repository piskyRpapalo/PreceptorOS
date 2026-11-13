"""Autonomy parity S2 · Talk says what the Notebook says: one projected turn, one sentence, one cause."""
from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path
from unittest import mock

import canales
import turnos_hexelion as T
import test_hexelion_acciones as H
from test_hexelion_acciones import PWA
from test_hexelion_cli_thread import chat

ROOT = Path(__file__).resolve().parent
NOW = "2026-11-13T12:00:00Z"


def node(script):
    r = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True)
    if r.returncode == 127:
        raise unittest.SkipTest("NO_DATA: node not installed")
    if r.returncode:
        raise AssertionError(r.stderr)
    return json.loads(r.stdout)


class ReplyCarriesTheNotebooksTurn(unittest.TestCase):
    """The chat reply's `turno` is the very row GET /api/hexelion/turnos serves for that request."""

    # The door fixture (fake native MCP in a temp home), borrowed without re-running its own tests.
    setUp, tearDown, server, person = H.Door.setUp, H.Door.tearDown, H.Door.server, H.Door.person

    def notebook_row(self, thread, n):
        rows = T.project(canales.lee(thread, 0, base=self.base), NOW)["turns"]
        return next(t for t in rows if t["n"] == n)

    def check(self, out, state, thread="orquesta"):
        turno = out["body"]["turno"]
        self.assertEqual(turno["state"], state, out)
        row = self.notebook_row(thread, turno["n"])
        self.assertEqual(turno, {k: row[k] for k in T.TALK_FIELDS if k in row})
        return turno

    def test_every_door_outcome_reaches_talk_as_the_notebooks_turn(self):
        self.check(self.person("/estado"), "ACTED")
        refused = self.check(self.person("/ejecuta git merge x"), "ACTION_REFUSED")
        self.assertEqual(refused["cause"], "linea dura: git")
        # The fake server's write_file answers ok:true without bytes or SHA-256: the contract's proof is missing.
        unproved = self.check(self.person("/escribe @hexelion-x notas.txt :: hola"), "ACTION_UNVERIFIED")
        self.assertEqual(unproved["cause"], "proof_missing")
        self.env = mock.patch.dict(os.environ, {"PRECEPTOROS_MCP_NATIVO": str(Path(self.base) / "absent.py")})
        down = self.check(self.person("/estado"), "NO_ANSWER")
        self.assertEqual(down["cause"], "mcp_nativo_missing")

    def test_a_station_that_does_not_answer_is_the_same_turn_in_talk(self):
        with mock.patch.object(PWA.PWA, "_nodo_local_autorizado", return_value=True), \
                mock.patch.object(PWA._hexelion_proxy, "ask", return_value={"estado": "NO_DATA", "causa": "station_unavailable"}), \
                mock.patch.object(PWA._hexelion_book, "construir_prompt", return_value=({"estado": "MEASURED", "fuentes": []}, "p")), \
                mock.patch.object(PWA._hexelion_book, "formato_citas", return_value=None):
            out = chat(self.base, {"texto": "what is the Notebook?"}, {"Origin": "http://127.0.0.1:8742"})
        turno = self.check(out, "NO_ANSWER")
        self.assertEqual(turno["sentence"], "The local model did not respond, so nobody answered.")

    def test_an_agents_refused_action_is_projected_from_its_own_thread(self):
        with self.env:
            out = chat(self.base, {"texto": "/estado", "voz": "claude"}, {})
        self.assertEqual(out["body"]["causa"], "actions_person_only")
        self.check(out, "NO_ANSWER", thread="cli")

    def test_refused_before_the_thread_has_no_turn_and_none_is_invented(self):
        out = chat(self.base, {"texto": "/estado"}, {}, client="10.9.8.7")
        self.assertEqual((out["code"], out["body"]["causa"]), (403, "local_origin_required"))
        self.assertNotIn("turno", out["body"])
        self.assertEqual(canales.lee("orquesta", 0, base=self.base).get("mensajes") or [], [])

    def test_talk_and_the_notebook_card_read_the_same_words_in_node(self):
        self.person("/estado")
        self.person("/ejecuta git merge x")
        self.person("/escribe @hexelion-x a.txt :: b")
        raw = T.project(canales.lee("orquesta", 0, base=self.base), NOW)
        got = node("const N=require('./interface/notebook.js');const raw=%s;const p=N.projectTurns(raw);"
                   "console.log(JSON.stringify(raw.turns.map((t,i)=>{const l=N.turnLine(t),c=p.turns[i];"
                   "return [l.state===c.state,l.sentence===c.sentence,l.cause===c.cause,l.line,l.state]})))" % json.dumps(raw))
        self.assertEqual([g[:3] for g in got], [[True, True, True]] * 3)
        self.assertEqual([g[4] for g in got], ["ACTION_UNVERIFIED", "ACTION_REFUSED", "ACTED"])
        for g, t in zip(got, raw["turns"]):
            self.assertEqual(g[3], t["sentence"] + " " + t["next"])


class TheEnvelopeNeverBreaksTheAnswer(unittest.TestCase):
    """The chat reply keeps its 1,023 B envelope; the turn gives way, the answer does not."""

    def setUp(self):
        H.LocalReads.setUp(self)

    tearDown, person, thread, firmas = H.Door.tearDown, H.Door.person, H.Door.thread, H.LocalReads.firmas

    def test_a_long_answer_keeps_its_place_and_the_turn_is_cut_not_invented(self):
        import estado_compacto
        self.firmas("2026-11-13T09:25:00Z", [{"repo": "owner/repository-%d" % i, "n": 9000 + i, "title": "HITL · «é» " * 12,
                                              "checks": "green", "action": "sign"} for i in range(30)])
        with mock.patch.object(H.A, "_edad", side_effect=lambda s, now: 300.0):
            body = self.person("¿Qué espera mi firma?")["body"]
        estado_compacto.serializar_objeto(body)                     # raises if the reply would not fit
        self.assertEqual(body["estado"], "ACCION_LOCAL")
        turno = body["turno"]
        self.assertEqual((turno["state"], turno["cut"]), ("ACTED", "envelope"))
        self.assertNotIn("sentence", turno)
        got = node("const N=require('./interface/notebook.js');console.log(JSON.stringify(N.turnLine(%s)))" % json.dumps(turno))
        self.assertEqual(got["state"], "ACTED")
        self.assertIn("the Notebook shows it for request %d" % turno["n"], got["line"])

    def test_a_cut_turn_of_unknown_state_is_still_no_data(self):
        got = node("const N=require('./interface/notebook.js');console.log(JSON.stringify("
                   "N.turnLine({n:4,state:'RUNNING',cut:'envelope'})))")
        self.assertEqual(got["state"], "NO_DATA")


class TalkNeverWordsAResultItself(unittest.TestCase):
    def test_malformed_or_missing_turns_are_no_data_with_a_cause(self):
        got = node("const N=require('./interface/notebook.js');console.log(JSON.stringify(["
                   "N.turnLine(undefined),N.turnLine({state:'NO_DATA',cause:'turn_not_projected'}),"
                   "N.turnLine({n:'3',state:'ACTED',sentence:'s'}),N.turnLine({n:3,state:'RUNNING',sentence:'s'}),"
                   "N.turnLine({n:3,state:'ACTED',sentence:'x'.repeat(201)}),N.turnLine({n:3,state:'ACTED'}),"
                   "N.turnLine({n:3,state:'ACTED',sentence:'done',next:'n'})].map(l=>[l.state,l.cause,l.line])))")
        states = [g[0] for g in got]
        self.assertEqual(states, ["NO_DATA"] * 6 + ["ACTED"])
        self.assertEqual(got[0][1], "turn_missing")
        self.assertEqual(got[1][1], "turn_not_projected")
        self.assertIn("turn not projected", got[1][2])
        self.assertTrue(all(g[2].startswith("NO_DATA: ") for g in got[:6]))
        self.assertEqual(got[6][2], "done n")

    def test_talk_paints_the_turn_and_its_status_line_speaks(self):
        js = (ROOT / "interface/app.js").read_text(encoding="utf-8")
        html = (ROOT / "interface/app.html").read_text(encoding="utf-8")
        self.assertNotIn("refused or failed", js)
        self.assertNotIn('accion.ok ? "done"', js)
        self.assertIn("window.PreceptorNotebook.turnLine(d.turno)", js)
        self.assertEqual(js.count("turno ? turno.line"), 4)        # action, energy, model answer, no answer
        self.assertIn('<p class="estado" id="estado" aria-live="polite"', html)
        self.assertLess(html.index('src="/notebook.js?v=15"'), html.index('src="/app.js?v=36"'))

    def test_the_shell_serves_the_new_scripts_under_a_new_cache(self):
        sw = (ROOT / "interface/sw.js").read_text(encoding="utf-8")
        for asset in ('"/notebook.js?v=15"', '"/app.js?v=36"'):
            self.assertIn(asset, sw)
        self.assertIn('const Cache = "preceptoros-armazon-v188";', sw)


if __name__ == "__main__":
    unittest.main()
