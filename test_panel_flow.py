"""Panel flow · one voice per reading, focus kept (PANEL-FLOW, 2026-11-13).

Measured in headless Chrome by tests/autonomia_a11y.browser.cjs step 15: before, reopening Notebook, Lab, Harness and
Settings spoke 3, 4, 2 and 4 lines (Lab said "Checking the local Lab…" from two regions at once); after, one each.
These tests pin the decisions where no browser runs.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HTML = (ROOT / "interface/app.html").read_text(encoding="utf-8")
APP = (ROOT / "interface/app.js").read_text(encoding="utf-8")
NOTEBOOK = (ROOT / "interface/notebook.js").read_text(encoding="utf-8")


class OneVoicePerReading(unittest.TestCase):
    def test_each_reading_panel_names_one_voice_that_is_its_own_live_line(self):
        voices = dict(re.findall(r'(\w+): "([\w-]+)"', APP[APP.index("const vozDelPanel"):APP.index("function cargarPanel")]))
        self.assertEqual(set(voices), {"cuaderno", "lab", "harness", "ajustes"})
        for panel, voice in voices.items():
            section = HTML[HTML.index('id="panel-%s"' % panel):]
            section = section[:section.index("</section>")]
            self.assertRegex(section, r'id="%s" role="status" aria-live="polite"' % voice, panel)

    def test_sections_are_quiet_while_loading_and_speak_again_after(self):
        body = APP[APP.index("function cargarPanel"):APP.index("window.PreceptorPanelFlow")]
        self.assertIn('callados.forEach((el) => el.setAttribute("aria-live", "off"));', body)
        self.assertIn('callados.forEach((el) => el.setAttribute("aria-live", "polite"));', body)
        self.assertIn(".finally(decir)", body)                                   # a failed reading still restores

    def test_the_notebook_refresh_goes_through_the_panel_flow(self):
        self.assertIn('root.PreceptorPanelFlow.load("cuaderno")', NOTEBOOK)


class FocusStays(unittest.TestCase):
    def test_a_busy_refresh_is_never_disabled(self):
        self.assertNotIn("button.disabled = true", NOTEBOOK)
        self.assertIn('button.setAttribute("aria-disabled", "true")', NOTEBOOK)
        self.assertIn('button.removeAttribute("aria-disabled")', NOTEBOOK)


class EnglishFirstPaint(unittest.TestCase):
    def test_reading_lines_start_in_english(self):
        for spanish in ("Consultando el Lab local", "Consultando los ciclos", "Bucles: "):
            self.assertNotIn(spanish, HTML + NOTEBOOK, spanish)


if __name__ == "__main__":
    unittest.main()
