"""The PWA must stay on loopback unless its operator opts in."""
import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROBE = (
    "import runpy; "
    "print(runpy.run_path('bin/preceptoros-pwa', "
    "run_name='pwa_bind_probe')['BIND'])"
)


class PwaBindTests(unittest.TestCase):
    def test_default_bind_is_loopback(self):
        env = os.environ.copy()
        env.pop("PRECEPTOROS_PWA_BIND", None)
        result = subprocess.run(
            [sys.executable, "-c", PROBE], cwd=ROOT, env=env,
            check=True, capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.stdout.strip(), "127.0.0.1")


if __name__ == "__main__":
    unittest.main()
