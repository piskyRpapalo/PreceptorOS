import pathlib
import shutil
import subprocess
import unittest


class TerminalContract(unittest.TestCase):
    def test_cases_twice(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('NO_DATA: node unavailable')
        root = pathlib.Path(__file__).resolve().parent
        results = [subprocess.run([node, 'colony/terminal_cases.cjs'], cwd=root,
                                  capture_output=True, check=True).stdout for _ in range(2)]
        self.assertEqual(*results)
