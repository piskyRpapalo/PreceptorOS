"""Run the building frame judge twice and require byte-identical receipts."""
import pathlib
import shutil
import subprocess
import unittest


class BuildingFrames(unittest.TestCase):
    def test_judge(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("NO_DATA: node is unavailable")
        root = pathlib.Path(__file__).resolve().parent
        first = subprocess.run([node, "colony/building_frames_cases.cjs"], cwd=root, capture_output=True, check=True)
        second = subprocess.run([node, "colony/building_frames_cases.cjs"], cwd=root, capture_output=True, check=True)
        self.assertEqual(first.stdout, second.stdout)


if __name__ == "__main__":
    unittest.main()
