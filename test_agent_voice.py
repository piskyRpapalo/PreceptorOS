"""The chat takes an agent voice only from a loopback CLI with no Origin, never the person's."""
import unittest
from pathlib import Path

SRC = (Path(__file__).resolve().parent / "bin" / "preceptoros-pwa").read_text(encoding="utf-8")
_PWA = None


def _load_pwa():
    """The server module, loaded once the same way test_pwa does it."""
    global _PWA
    if _PWA is None:
        import importlib.util, sys
        from importlib.machinery import SourceFileLoader
        aqui = Path(__file__).resolve().parent
        sys.path.insert(0, str(aqui))
        ruta = str(aqui / "bin" / "preceptoros-pwa")
        spec = importlib.util.spec_from_loader("preceptoros_pwa_voice", SourceFileLoader("preceptoros_pwa_voice", ruta))
        _PWA = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_PWA)
    return _PWA


class AgentVoice(unittest.TestCase):
    def test_allowlist_and_never_soberano(self):
        self.assertIn('AGENT_VOICES = frozenset({"claude", "codex", "gemini", "mistral"})', SRC)
        self.assertNotIn('"soberano"', SRC.split("AGENT_VOICES = ")[1].split("\n")[0])

    def test_agent_path_uses_di_and_needs_loopback_without_origin(self):
        bloque = SRC[SRC.index('voz = data.get("voz")'):SRC.index('return no_data("agent_voice_refused", 403)')]
        self.assertIn("_canales.di(\"cli\", voz", bloque)   # 2026-11-12: agents ask in their own thread
        self.assertIn("self._es_loopback(self.client_address[0])", bloque)
        self.assertIn('not self.headers.get("Origin")', bloque)

    def test_canales_refuses_soberano_voice(self):
        import canales
        with self.assertRaises(canales.CanalRechazado):
            canales.di("orquesta", "soberano", "x")


if __name__ == "__main__":
    unittest.main()


class TestAgentVoiceDoorLive(unittest.TestCase):
    """The door, walked through the real handler (not only read in the source): the CLI agent gets in."""

    def _walk(self, body, ip="127.0.0.1", origin=None, persona=False):
        import io, json
        from types import SimpleNamespace
        from unittest import mock
        PWA = _load_pwa()
        payload = json.dumps(body, ensure_ascii=False).encode()
        h = PWA.PWA.__new__(PWA.PWA)
        h.path = "/api/hexelion/chat"
        h.headers = {"Content-Type": "application/json", "Content-Length": str(len(payload))}
        if origin:
            h.headers["Origin"] = origin
        h.rfile = io.BytesIO(payload)
        h.client_address = (ip, 50000)
        h.server = SimpleNamespace(ruta_db="unused")
        got = {}
        h._json = lambda code, b: got.update(code=code, body=b)
        h._nodo_local_autorizado = lambda: persona
        empty = {"esquema": "preceptoros.memory-search/1", "estado": "NO_DATA", "causa": "no_match", "fuentes": []}
        with mock.patch.object(PWA._casa, "raiz", return_value="unused"), \
             mock.patch.object(PWA._canales, "di_soberano") as person, \
             mock.patch.object(PWA._canales, "di") as agent, \
             mock.patch.object(PWA._memory_lookup, "buscar", return_value=empty), \
             mock.patch.object(PWA._indice_rack, "buscar", return_value=empty), \
             mock.patch.object(PWA._hexelion_proxy, "ask") as ask:
            PWA.PWA._hexelion_chat(h)
        return got, person, agent, ask

    def test_cli_agent_with_voice_gets_in_and_speaks_as_itself(self):
        got, person, agent, _ = self._walk({"texto": "caravan states", "voz": "claude"})
        self.assertNotEqual(got.get("body", {}).get("causa"), "local_origin_required", got)
        person.assert_not_called()
        self.assertEqual(agent.call_args.args[:3], ("cli", "claude", "caravan states"))   # own thread since 2026-11-12

    def test_cli_without_voice_never_speaks_as_the_person(self):
        got, person, agent, _ = self._walk({"texto": "hola"})
        self.assertEqual((got["code"], got["body"]["causa"]), (403, "local_origin_required"))
        person.assert_not_called(); agent.assert_not_called()

    def test_remote_caller_is_refused_before_the_body(self):
        got, person, agent, _ = self._walk({"texto": "hola", "voz": "claude"}, ip="203.0.113.9")
        self.assertEqual((got["code"], got["body"]["causa"]), (403, "local_origin_required"))
        person.assert_not_called(); agent.assert_not_called()

    def test_the_window_still_speaks_as_the_person(self):
        got, person, agent, _ = self._walk({"texto": "hola"}, origin="http://127.0.0.1:8742", persona=True)
        person.assert_called_once()
        agent.assert_not_called()

    def test_a_window_cannot_borrow_an_agent_voice(self):
        got, person, agent, _ = self._walk({"texto": "hola", "voz": "claude"}, origin="http://127.0.0.1:8742", persona=True)
        self.assertEqual((got["code"], got["body"]["causa"]), (403, "agent_voice_refused"))
        person.assert_not_called(); agent.assert_not_called()
