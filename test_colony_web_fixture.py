"""Run the pinned comparison fixture without claiming browser parity."""
import pathlib
import shutil
import subprocess
import unittest


class WebFixture(unittest.TestCase):
    def test_pinned_scene(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('NO_DATA: node unavailable')
        root = pathlib.Path(__file__).resolve().parent
        outputs = [subprocess.run([node, 'colony/web_fixture_cases.cjs'], cwd=root,
                                  check=True, capture_output=True).stdout for _ in range(2)]
        self.assertEqual(*outputs)
