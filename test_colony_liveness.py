"""Exercise the injected poll boundary in the standard gate."""
import pathlib
import shutil
import subprocess
import unittest


class Liveness(unittest.TestCase):
    def test_poll_cases_twice(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('NO_DATA: node unavailable')
        root = pathlib.Path(__file__).resolve().parent
        out = [subprocess.run([node, 'colony/liveness_cases.cjs'], cwd=root,
                              check=True, capture_output=True).stdout for _ in range(2)]
        self.assertEqual(*out)
