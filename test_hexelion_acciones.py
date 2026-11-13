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
        self.assertEqual(tools, {"state", "capabilities", "audit_last",           # never exec or write_file
                                 "signatures", "lab", "preceptors", "devices", "models"})

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


class LocalReads(unittest.TestCase):
    """APP-TALK-E2E-01 (2026-11-13): «what awaits my signature?», «lab results», «which preceptors are working?»
    read the projections existing producers already write. No MCP, no model, no new daemon; gaps say their cause."""

    NOW = "2026-11-13T09:30:00Z"
    person, thread, tearDown = Door.person, Door.thread, Door.tearDown

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = self.tmp.name
        # Any MCP call here is a bug: these are local reads, so the server path points at nothing.
        self.env = mock.patch.dict(os.environ, {"PRECEPTOROS_MCP_NATIVO": str(Path(self.base) / "must_not_run.py")})

    def firmas(self, medido, filas):
        d = Path(self.base) / "firmas"
        d.mkdir(exist_ok=True)
        (d / "pendientes.json").write_text(json.dumps({"esquema": "preceptoros.firmas-pendientes/1", "medido": medido,
                                                       "filas": filas}))

    def test_grammar_and_phrases_name_the_three_reads_and_take_no_arguments(self):
        for said, order in (("¿Qué espera mi firma?", "/firmas"), ("What awaits my signature?", "/firmas"),
                            ("¿Qué resultados tenemos del laboratorio?", "/lab"), ("Lab results", "/lab"),
                            ("¿Qué preceptores están trabajando?", "/preceptores"), ("quem está a trabalhar", "/preceptores")):
            self.assertEqual(A.frase(said), order, said)
        self.assertEqual(A.interpreta("/signatures"), ("signatures", {}))
        self.assertEqual(A.interpreta("/preceptors"), ("preceptors", {}))
        self.assertEqual(A.interpreta("/lab rm -rf x"), (None, "action_takes_no_arguments"))
        self.assertIsNone(A.frase("firma el 176"))            # a command-shaped sentence never gains a write
        self.assertIn("/firmas", A.AYUDA)

    def test_signatures_list_what_waits_and_never_sign(self):
        self.firmas("2026-11-13T09:25:00Z", [
            {"repo": "o/lab", "n": 176, "title": "HITL · FORGE", "checks": "green", "action": "sign"},
            {"repo": "o/lab", "n": 175, "title": "HITL", "checks": "no_data", "action": "running"}])
        with mock.patch.object(A, "_edad", wraps=lambda s, now: 300.0):
            out = self.person("¿Qué espera mi firma?")
        self.assertEqual((out["code"], out["body"]["estado"], out["body"]["causa"]),
                         (200, "ACCION_LOCAL", "lectura_local;model_not_invoked"))
        acc = out["body"]["respuesta"]["accion"]
        self.assertEqual((acc["herramienta"], acc["ok"], acc["via"]), ("signatures", True, "lectura_local"))
        self.assertIn("Waiting for your signature: 1 — lab#176 «HITL · FORGE» (checks green)", acc["texto"])
        self.assertIn("1 with checks still running", acc["texto"])
        self.assertIn("I never sign for you.", acc["texto"])
        msgs = self.thread()
        self.assertEqual((msgs[1]["maquina"]["via"], msgs[1]["sello"]), ("lectura_local", "MEDIDO"))
        turn = turnos_hexelion.project(canales.lee("orquesta", 0, base=self.base), self.NOW)["turns"][0]
        self.assertEqual(turn["state"], "ACTED")
        self.assertIn("no model ran", turn["sentence"])

    def test_asking_twice_is_idempotent_reads_never_write_their_source(self):
        self.firmas("2026-11-13T09:25:00Z", [{"repo": "o/app", "n": 1, "title": "HITL", "checks": "green",
                                              "action": "sign"}])
        fuente = Path(self.base) / "firmas" / "pendientes.json"
        antes = (fuente.read_bytes(), fuente.stat().st_mtime_ns)
        with mock.patch.object(A, "_edad", side_effect=lambda s, now: 300.0):
            uno = self.person("What awaits my signature?")["body"]["respuesta"]["accion"]
            dos = self.person("What awaits my signature?")["body"]["respuesta"]["accion"]
        self.assertEqual((uno["texto"], uno["ok"], uno["causa"]), (dos["texto"], dos["ok"], dos["causa"]))
        self.assertEqual((fuente.read_bytes(), fuente.stat().st_mtime_ns), antes)
        msgs = self.thread()
        self.assertEqual([m["voz"] for m in msgs], ["soberano", "hexelion"] * 2)   # each question keeps its answer
        self.assertEqual([m["maquina"]["pregunta_n"] for m in msgs[1::2]], [msgs[0]["n"], msgs[2]["n"]])

    def test_the_longest_answers_still_fit_the_chat_envelope(self):
        # The test door replaces _json, so the server's 1,023 B envelope is applied here by hand.
        import estado_compacto
        self.firmas("2026-11-13T09:25:00Z", [{"repo": "owner/repository-%d" % i, "n": 9000 + i, "title": "HITL · «é» " * 12,
                                              "checks": "green", "action": a}
                                             for i, a in enumerate(["sign"] * 30 + ["running", "red", "wait_base"] * 3)])
        with mock.patch.object(A, "_edad", side_effect=lambda s, now: 300.0):
            out = self.person("¿Qué espera mi firma?")["body"]
        estado_compacto.serializar_objeto(out)                     # raises if the reply would not fit
        texto = out["respuesta"]["accion"]["texto"]
        self.assertIn("(+27 more)", texto)
        self.assertLessEqual(len(texto.encode("utf-8")), A.TOPE_LOCAL_B)
        self.assertEqual(A.cabe("x" * 900)[-24:], " … (cut to fit the chat)")
        import notebook_read
        run = {"date": "2026-11-12", "experiment": "e" * 80, "fingerprint": "RECHECKED", "sentence": "s" * 900}
        with mock.patch.object(notebook_read, "read", return_value={"bench": [run] * 6, "bench_cause": None,
                                                                    "bench_observed_at": "2026-11-13T09:20:00Z"}):
            out = self.person("lab results")["body"]
        estado_compacto.serializar_objeto(out)

    def test_an_old_or_missing_signature_list_is_said_not_hidden(self):
        self.firmas("2026-11-12T09:00:00Z", [])
        acc = self.person("/firmas")["body"]["respuesta"]["accion"]
        self.assertEqual((acc["ok"], acc["causa"]), (False, "signatures_stale"))
        self.assertTrue(acc["texto"].startswith("STALE: Nothing waits for your signature now."))
        (Path(self.base) / "firmas" / "pendientes.json").unlink()
        acc = self.person("/firmas")["body"]["respuesta"]["accion"]
        self.assertEqual((acc["ok"], acc["causa"]), (False, "scraper_not_run"))
        self.assertEqual(self.thread()[-1]["sello"], "NO_DATA")

    def test_lab_without_a_bench_projection_says_its_cause(self):
        acc = self.person("lab results")["body"]["respuesta"]["accion"]
        self.assertEqual((acc["herramienta"], acc["ok"], acc["causa"]), ("lab", False, "file_missing"))
        self.assertIn("No Lab result I can show: file missing.", acc["texto"])

    def test_lab_reads_the_same_runs_the_notebook_shows(self):
        import notebook_read
        run = {"date": "2026-11-12T12:20:21+00:00", "experiment": "public-throughput-v1", "fingerprint": "RECHECKED",
               "sentence": "qwen3:1.7b generated 30.1 tokens/s over 1 sample."}
        with mock.patch.object(notebook_read, "read", return_value={
                "bench": [run], "bench_cause": None, "bench_observed_at": "2026-11-13T09:20:00Z"}):
            acc = A.lee_local("lab", self.base)
        self.assertTrue(acc["ok"])
        self.assertIn("latest: 2026-11-12 public-throughput-v1: qwen3:1.7b generated 30.1 tokens/s", acc["texto"])
        self.assertIn("(fingerprint rechecked)", acc["texto"])

    def test_preceptors_without_heartbeats_never_guess_and_say_who_acted(self):
        import notebook_read
        vista = {"agents": [], "agents_status": "NO_DATA", "agents_cause": "file_missing",
                 "receipts": [{"voice": "hexelion", "status": "DECLARED"}, {"voice": "claude", "status": "STALE"}]}
        with mock.patch.object(notebook_read, "read", return_value=vista):
            acc = A.lee_local("preceptors", self.base)
        self.assertEqual((acc["ok"], acc["causa"]), (False, "agents_file_missing"))
        self.assertIn("I cannot say which preceptors are working", acc["texto"])
        self.assertIn("Actions with a receipt in the last 10 min: hexelion 1.", acc["texto"])
        self.assertNotIn("claude", acc["texto"])                              # a stale receipt is not «working»
        vista.update(agents=[{"name": "Codex CLI", "role": "LAB", "status": "OBSERVADO", "cause": "x"}],
                     agents_status="DECLARADO", agents_cause=None)
        with mock.patch.object(notebook_read, "read", return_value=vista):
            acc = A.lee_local("preceptors", self.base)
        self.assertIn("Codex CLI (LAB): heartbeat in the last 10 min", acc["texto"])

    def test_a_reader_failure_is_a_cause_not_a_crash(self):
        with mock.patch.dict(A._LECTORES, {"lab": (mock.Mock(side_effect=RuntimeError("x")), "notebook/bench.json")}):
            acc = A.lee_local("lab", self.base)
        self.assertEqual((acc["estado"], acc["ok"], acc["causa"]), ("MEASURED", False, "local_read_failed"))

    def test_a_cli_agent_cannot_use_the_reads_through_hexelion(self):
        with self.env:
            out = chat(self.base, {"texto": "/firmas", "voz": "claude"}, {})
        self.assertEqual((out["code"], out["body"]["causa"]), (403, "actions_person_only"))


class Shell(unittest.TestCase):
    def test_talk_has_a_question_mark_with_the_commands_and_the_chat_paints_actions(self):
        html = (ROOT / "interface/app.html").read_text(encoding="utf-8")
        head = html[html.index('id="panel-conversacion"'):html.index('id="hilo"')]
        self.assertIn('<details class="comandos" id="comandos-hexelion">', head)
        self.assertIn('aria-label="Hexelion commands"', head)
        for cmd in ("/estado", "/capacidades", "/registro 5", "/firmas", "/lab", "/preceptores", "/ejecuta", "/escribe"):
            self.assertIn('data-comando="%s' % cmd, head)
        app = (ROOT / "interface/app.js").read_text(encoding="utf-8")
        self.assertIn('d.estado === "ACCION_LOCAL"', app)
        self.assertIn('#comandos-hexelion [data-comando]', app)
        self.assertIn('"ACTED", "ACTION_REFUSED"', (ROOT / "interface/notebook.js").read_text(encoding="utf-8"))
        sw = (ROOT / "interface/sw.js").read_text(encoding="utf-8")
        self.assertIn("preceptoros-armazon-v181", sw)
        for asset in ('"/app.js?v=31"', '"/app.css?v=20"', '"/notebook.js?v=11"'):
            self.assertIn(asset, sw)


if __name__ == "__main__":
    unittest.main()
