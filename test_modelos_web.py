"""Sabotajes y contrato de la flecha de modelos y puerta Web."""
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).parent


class ModelosWebSabotajes(unittest.TestCase):
    def test_no_red_contrato_cierre_y_marco_sin_respuesta(self):
        result = subprocess.run(
            ["node", "--test", "tests/models_web_cases.cjs"],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_recurso_lazy_esta_servido_y_versionado(self):
        html = (ROOT / "interface/app.html").read_text(encoding="utf-8")
        css = (ROOT / "interface/app.css").read_text(encoding="utf-8")
        sw = (ROOT / "interface/sw.js").read_text(encoding="utf-8")
        server = (ROOT / "bin/preceptoros-pwa").read_text(encoding="utf-8")
        versions = (ROOT / "version.py").read_text(encoding="utf-8")
        frame = html.split('<iframe id="openworld-frame"', 1)[1].split(">", 1)[0]
        self.assertNotRegex(frame, r"\bsrc\s*=")
        self.assertIn('aria-haspopup="dialog"', html)
        self.assertIn('aria-expanded="false"', html)
        self.assertIn("min-width: 44px; min-height: 44px", css)
        self.assertIn('"/modelos_web.js": ("modelos_web.js",', server)
        self.assertIn('"/modelos_web.js?v=3"', sw)
        self.assertIn('<script src="/modelos_web.js?v=3"></script>', html)
        self.assertIn('"interface/modelos_web.js"', versions)
        self.assertRegex(sw, r"preceptoros-armazon-v\d+")  # [deprecated 2026-11-08] pinned v148: any bump was a red


if __name__ == "__main__":
    unittest.main(verbosity=2)
