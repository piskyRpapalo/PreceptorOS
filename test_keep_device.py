"""Joya 2: keep this app on this device (storage.persist), only on a click, verdict as the browser gave it."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).parent


class KeepDevice(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "SKIP-DECLARED (not green): node is unavailable")
    def test_cases(self):
        r = subprocess.run(["node", "--test", "--test-reporter=tap", "tests/keep_device_cases.cjs"], cwd=ROOT,
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr[-1000:])
        self.assertRegex(r.stdout, r"# pass [1-9]")

    def test_served_precached_and_mounted_in_ajustes(self):
        html = (ROOT / "interface/app.html").read_text(encoding="utf-8")
        sw = (ROOT / "interface/sw.js").read_text(encoding="utf-8")
        server = (ROOT / "bin/preceptoros-pwa").read_text(encoding="utf-8")
        self.assertIn('<script src="/keep_device.js?v=1"></script>', html)
        self.assertIn('"/keep_device.js?v=1"', sw)
        self.assertIn('"/keep_device.js": ("keep_device.js",', server)
        ajustes = html.split('id="panel-ajustes"', 1)[1]
        self.assertIn('id="keep-device"', ajustes)
        # nothing is asked at load: the module only listens for a click
        code = (ROOT / "interface/keep_device.js").read_text(encoding="utf-8")
        self.assertIn('addEventListener("click"', code)


if __name__ == "__main__":
    unittest.main()
