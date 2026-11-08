"""The chat takes an agent voice only from a loopback CLI with no Origin, never the person's."""
import unittest
from pathlib import Path

SRC = (Path(__file__).resolve().parent / "bin" / "preceptoros-pwa").read_text(encoding="utf-8")


class AgentVoice(unittest.TestCase):
    def test_allowlist_and_never_soberano(self):
        self.assertIn('AGENT_VOICES = frozenset({"claude", "codex", "gemini", "mistral"})', SRC)
        self.assertNotIn('"soberano"', SRC.split("AGENT_VOICES = ")[1].split("\n")[0])

    def test_agent_path_uses_di_and_needs_loopback_without_origin(self):
        bloque = SRC[SRC.index('voz = data.get("voz")'):SRC.index('return no_data("agent_voice_refused", 403)')]
        self.assertIn("_canales.di(\"orquesta\", voz", bloque)
        self.assertIn("self._es_loopback(self.client_address[0])", bloque)
        self.assertIn('not self.headers.get("Origin")', bloque)

    def test_canales_refuses_soberano_voice(self):
        import canales
        with self.assertRaises(canales.CanalRechazado):
            canales.di("orquesta", "soberano", "x")


if __name__ == "__main__":
    unittest.main()
