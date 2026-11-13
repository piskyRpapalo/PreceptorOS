"""Accessibility proof · failures read as NO_DATA with a cause, never as fresh (ACCESSIBILITY-PROOF, 2026-11-13).

Measured in headless Chrome by tests/autonomia_a11y.browser.cjs steps 16-19 (forced colours, 768/1440/1920 widths,
every source failing with http 500, state words). Pinned here where no browser runs.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = (ROOT / "interface/app.js").read_text(encoding="utf-8")
HITL = (ROOT / "interface/hitl.js").read_text(encoding="utf-8")
HTML = (ROOT / "interface/app.html").read_text(encoding="utf-8")
EN = APP[APP.index("  en: {"):APP.index("  fr: {")] if "  fr: {" in APP else APP


class FailuresAreNoData(unittest.TestCase):
    def test_settings_never_says_read_when_a_reader_failed(self):
        self.assertIn('h.status === "rejected" || h.value === false', APP)
        for reader in ("async function cargarPuerta", "async function cargarCuaderno"):
            body = APP[APP.index(reader):APP.index("\n}\n", APP.index(reader))]
            self.assertIn("return false;", body, reader)

    def test_a_failed_answer_is_not_an_unreachable_server(self):
        self.assertIn('r ? "NO_DATA: the server answered http " + r.status', APP)

    def test_reading_errors_start_with_no_data_in_english(self):
        for key in ("lab_error", "harness_error", "puerta_error"):
            words = re.search(r"%s: [\"']([^\"']*)" % key, EN)
            self.assertIsNotNone(words, key)
            self.assertTrue(words.group(1).startswith("NO_DATA: "), key)

    def test_boundary_reading_messages_are_english_no_data(self):
        # Reading messages only. The signing flow's own words (Firmando, No firmado, listo para firmar) are the
        # Sovereign's wording and wait for the Mesa (odd/tasks/app-visual-coherence.md, open questions).
        for spanish in ("No se pudo", "Leyendo", "leído", "es-ES", "sin título", "No hay PRs", "No firmado ("):
            self.assertNotIn(spanish, HITL[HITL.index("function"):], spanish)
        self.assertIn('"NO_DATA: the list could not be read ("', HITL)

    def test_cause_codes_are_english(self):
        for spanish in ("conexion_local_no_disponible", "respuesta_invalida", "no se pudo ejecutar HITL"):
            self.assertNotIn(spanish, APP + (ROOT / "bin/preceptoros-pwa").read_text(encoding="utf-8"), spanish)
        self.assertIn('<pre id="tray-result" role="status" aria-live="polite">Not read yet.</pre>', HTML)


if __name__ == "__main__":
    unittest.main()
