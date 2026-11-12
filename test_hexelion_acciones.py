"""Hexelion acts from the chat (Sovereign 2026-11-12): «/…» is an action run by the native MCP as voice hexelion.
The model is never asked; only the person acts; a missing or read-only (S-1) server is NO_DATA with its cause;
the result is Hexelion's turn marked «not model»; Talk has a «?» list of the commands."""
import json
import os
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

import canales
import hexelion_acciones as A
import turnos_hexelion
from test_hexelion_cli_thread import chat
from test_pwa import PWA

ROOT = Path(__file__).resolve().parent

FAKE = textwrap.dedent('''
    import json, os, sys
    S3 = %r
    names = ["exec", "audit_last", "ping"] + (["write_file", "capabilities", "state"] if S3 else [])
    for line in sys.stdin:
        m = json.loads(line)
        if m["method"] == "initialize":
            r = {"serverInfo": {"name": "fake"}}
        elif m["method"] == "tools/list":
            r = {"tools": [{"name": n} for n in names]}
        else:
            name, args = m["params"]["name"], m["params"]["arguments"]
            voz = os.environ.get("PRECEPTOROS_MCP_VOZ")
            if name == "exec" and "merge" in args["command"]:
                out = {"ok": False, "denied": True, "causa": "linea dura: git"}
            elif name == "exec":
                out = {"ok": True, "rc": 0, "ms": 3, "out": "voz=%%s cwd=%%s" %% (voz, args.get("cwd")), "allowlist_version": "t"}
            elif name == "state":
                out = {"ok": True, "uptime": "up 1 day", "memoria": ["Mem: 8G 2G"], "disco_casa": ["40%% 100G"],
                       "servicios": [{"unidad": "a.service", "activo": "active"}, {"unidad": "b.service", "activo": "failed"}],
                       "modelos_cargados": []}
            else:
                out = {"ok": True, "voz": voz}
            r = {"content": [{"type": "text", "text": json.dumps(out)}]}
        print(json.dumps({"jsonrpc": "2.0", "id": m.get("id"), "result": r}), flush=True)
''')


class Grammar(unittest.TestCase):
    def test_exact_actions_parse_and_everything_else_is_refused_with_a_cause(self):
        with mock.patch.dict(os.environ, {"PRECEPTOROS_WT_RAIZ": "/w"}):
            self.assertEqual(A.interpreta("/estado"), ("state", {}))
            self.assertEqual(A.interpreta(" /Capabilities "), ("capabilities", {}))
            self.assertEqual(A.interpreta("/registro 7"), ("audit_last", {"n": 7}))
            self.assertEqual(A.interpreta("/run git status"), ("exec", {"command": "git status"}))
            self.assertEqual(A.interpreta("/ejecuta @hexelion-x bin/pruebas --rapido"),
                             ("exec", {"command": "bin/pruebas --rapido", "cwd": "/w/hexelion-x"}))
            self.assertEqual(A.interpreta("/escribe @hexelion-x docs/a.md :: hola"),
                             ("write_file", {"path": "/w/hexelion-x/docs/a.md", "content": "hola\n"}))
        for bad, cause in (("/borra todo", "action_unknown"), ("/estado ya", "action_takes_no_arguments"),
                           ("/registro 99", "audit_count_1_to_20"), ("/ejecuta", "command_missing"),
                           ("/ejecuta @../x ls", "worktree_name_invalid"), ("/escribe a.md :: x", "write_needs_worktree"),
                           ("/escribe @hexelion-x ../a.md :: x", "write_path_or_separator_invalid"),
                           ("/escribe @hexelion-x /etc/a :: x", "write_path_or_separator_invalid")):
            self.assertEqual(A.interpreta(bad), (None, cause), bad)
        self.assertFalse(A.es_accion("what is the rack state"))
        for cause in ("action_unknown", "mcp_s3_not_installed", "actions_person_only", "mcp_nativo_missing"):
            self.assertIn(cause, turnos_hexelion.CAUSES)


class Door(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = self.tmp.name
        self.server(True)

    def tearDown(self):
        self.tmp.cleanup()

    def server(self, s3):
        p = Path(self.base) / ("fake_s3.py" if s3 else "fake_s1.py")
        p.write_text(FAKE % s3)
        self.env = mock.patch.dict(os.environ, {"PRECEPTOROS_MCP_NATIVO": str(p)})

    def person(self, text):
        with self.env, mock.patch.object(PWA.PWA, "_nodo_local_autorizado", return_value=True), \
                mock.patch.object(PWA._hexelion_proxy, "ask", side_effect=AssertionError("model asked")):
            return chat(self.base, {"texto": text}, {"Origin": "http://127.0.0.1:8742"})

    def thread(self):
        return canales.lee("orquesta", 0, base=self.base)["mensajes"]

    def test_an_action_runs_as_hexelion_without_the_model_and_lands_as_its_turn(self):
        out = self.person("/estado")
        self.assertEqual((out["code"], out["body"]["estado"]), (200, "ACCION_LOCAL"))
        acc = out["body"]["respuesta"]["accion"]
        self.assertEqual((acc["herramienta"], acc["ok"]), ("state", True))
        self.assertIn("1/2 house services active; failed: b.service", acc["texto"])
        msgs = self.thread()
        self.assertEqual([m["voz"] for m in msgs], ["soberano", "hexelion"])
        self.assertEqual((msgs[1]["maquina"]["via"], msgs[1]["maquina"]["pregunta_n"]), ("mcp_nativo", msgs[0]["n"]))
        turn = turnos_hexelion.project(canales.lee("orquesta", 0, base=self.base), "2026-11-12T00:00:00Z")["turns"][0]
        self.assertEqual(turn["state"], "ACTED")

    def test_the_server_runs_with_hexelions_voice_and_its_fence_refusals_are_reported(self):
        acc = self.person("/ejecuta @hexelion-x git status")["body"]["respuesta"]["accion"]
        self.assertIn("voz=hexelion", acc["texto"])
        refused = self.person("/ejecuta git merge x")["body"]["respuesta"]["accion"]
        self.assertEqual((refused["ok"], refused["denegada"]), (False, True))
        self.assertIn("Refused by the fence: linea dura: git", refused["texto"])
        turn = turnos_hexelion.project(canales.lee("orquesta", 0, base=self.base), "2026-11-12T00:00:00Z")["turns"][0]
        self.assertEqual((turn["state"], turn["cause"]), ("ACTION_REFUSED", "linea dura: git"))

    def test_read_only_or_missing_server_is_no_data_with_its_cause(self):
        self.server(False)
        out = self.person("/estado")
        self.assertEqual((out["code"], out["body"]["causa"]), (503, "mcp_s3_not_installed"))
        self.env = mock.patch.dict(os.environ, {"PRECEPTOROS_MCP_NATIVO": str(Path(self.base) / "absent.py")})
        self.assertEqual(self.person("/estado")["body"]["causa"], "mcp_nativo_missing")
        self.assertEqual(self.person("/nope")["body"]["causa"], "action_unknown")
        self.assertEqual([m["voz"] for m in self.thread()][-1], "hexelion-door")

    def test_a_cli_agent_never_acts_through_hexelion(self):
        with self.env:
            out = chat(self.base, {"texto": "/estado", "voz": "claude"}, {})
        self.assertEqual((out["code"], out["body"]["causa"]), (403, "actions_person_only"))


class Phrases(Door):
    """One sentence, no typing (NORTE §4): exact phrases name READ actions only; nothing else changes path."""

    def test_exact_phrases_in_three_languages_name_only_read_actions(self):
        for said, order in (("¿Cómo está el rack?", "/estado"), ("How is the rack?", "/estado"),
                            ("o que podes fazer", "/capacidades"), ("Qué has hecho", "/registro 5")):
            self.assertEqual(A.frase(said), order, said)
        for other in ("como esta el rack ahora", "borra el rack", "/estado", "what is the cache version", "x" * 200):
            self.assertIsNone(A.frase(other), other)
        tools = {A.interpreta(order)[0] for order in A.FRASES}
        self.assertEqual(tools, {"state", "capabilities", "audit_last"})          # never exec or write_file

    def test_the_person_says_a_phrase_and_hexelion_acts_and_the_thread_keeps_the_words(self):
        out = self.person("¿Cómo está el rack?")
        self.assertEqual(out["body"]["estado"], "ACCION_LOCAL")
        acc = out["body"]["respuesta"]["accion"]
        self.assertEqual((acc["herramienta"], acc["frase"]), ("state", "/estado"))
        msgs = self.thread()
        self.assertEqual(msgs[0]["texto"], "¿Cómo está el rack?")
        self.assertEqual(msgs[1]["maquina"]["frase"], "/estado")

    def test_a_cli_agent_saying_a_phrase_still_asks_a_question(self):
        with self.env, mock.patch.object(PWA._hexelion_proxy, "ask", side_effect=AssertionError("model asked")):
            out = chat(self.base, {"texto": "what can you do", "voz": "codex"}, {})
        self.assertNotEqual(out["body"].get("causa"), "actions_person_only")
        self.assertNotEqual(out["body"].get("estado"), "ACCION_LOCAL")

    def test_the_question_mark_list_says_the_phrases(self):
        html = (ROOT / "interface/app.html").read_text(encoding="utf-8")
        self.assertIn('id="comandos-hexelion-frases"', html)
        self.assertIn("«how is the rack?»", html)


class Shell(unittest.TestCase):
    def test_talk_has_a_question_mark_with_the_commands_and_the_chat_paints_actions(self):
        html = (ROOT / "interface/app.html").read_text(encoding="utf-8")
        head = html[html.index('id="panel-conversacion"'):html.index('id="hilo"')]
        self.assertIn('<details class="comandos" id="comandos-hexelion">', head)
        self.assertIn('aria-label="Hexelion commands"', head)
        for cmd in ("/estado", "/capacidades", "/registro 5", "/ejecuta", "/escribe"):
            self.assertIn('data-comando="%s' % cmd, head)
        app = (ROOT / "interface/app.js").read_text(encoding="utf-8")
        self.assertIn('d.estado === "ACCION_LOCAL"', app)
        self.assertIn('#comandos-hexelion [data-comando]', app)
        self.assertIn('"ACTED", "ACTION_REFUSED"', (ROOT / "interface/notebook.js").read_text(encoding="utf-8"))
        sw = (ROOT / "interface/sw.js").read_text(encoding="utf-8")
        self.assertIn("preceptoros-armazon-v171", sw)
        for asset in ('"/app.js?v=28"', '"/app.css?v=19"', '"/notebook.js?v=6"'):
            self.assertIn(asset, sw)


if __name__ == "__main__":
    unittest.main()
