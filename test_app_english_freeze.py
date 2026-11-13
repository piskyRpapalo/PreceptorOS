"""APP-only language freeze; CLI and stored profile choices are not changed.

These tests are intentionally independent of a live /api/perfil service.
The browser BEACON exercises both the normal and blocked-profile cases.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent


class EnglishOnlyApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "interface/app.html").read_text(encoding="utf-8")
        cls.js = (ROOT / "interface/app.js").read_text(encoding="utf-8")
        cls.sw = (ROOT / "interface/sw.js").read_text(encoding="utf-8")

    def test_initial_document_language_is_english(self):
        self.assertRegex(self.html, r'(?m)^<html lang="en">')
        self.assertNotRegex(self.html, r'(?m)^<html lang="es">')

    def test_active_dictionary_is_english_even_if_profile_is_unreachable(self):
        self.assertTrue("let t = textos.en;" in self.js, "active default must be English")
        self.assertFalse("let t = textos.es;" in self.js, "Spanish must not be the active default")
        start = self.js.index("async function fijarIdioma()")
        end = self.js.index("let panelActual", start)
        renderer = self.js[start:end]
        self.assertIn("t = textos.en;", renderer)
        self.assertIn("pintarEstaticos();", renderer)
        self.assertNotIn('fetch("/api/perfil")', renderer)
        self.assertNotIn("textos[l]", renderer)

    def test_translation_history_is_retained_not_ripped_out(self):
        for code in ("es", "en", "fr", "pt", "it", "de", "ru", "el", "ar"):
            with self.subTest(code=code):
                self.assertRegex(self.js, rf"(?m)^  {code}: \{{")
        self.assertIn("document.documentElement.lang = lengua;", self.js)
        self.assertIn('lengua === "ar" ? "rtl" : "ltr"', self.js)

    def test_fresh_shell_asset_versions_match_pinned_service_worker(self):
        self.assertIn('src="/app.js?v=32"', self.html)
        self.assertIn('"/app.js?v=32"', self.sw)
        self.assertIn('preceptoros-armazon-v183', self.sw)
        self.assertIn('src="/energia_ui.js?v=2"', self.html)
        self.assertIn('"/energia_ui.js?v=2"', self.sw)

    def test_page_still_has_one_talk_and_nine_tabs(self):
        self.assertEqual(len(re.findall(r'role="tab"', self.html)), 9)
        self.assertIn('id="form-chat"', self.html)
        self.assertIn('id="energy-status" role="status" aria-live="polite"', self.html)


if __name__ == "__main__":
    unittest.main()
