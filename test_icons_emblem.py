"""The install icons are generated from the emblem, never painted by hand."""
import importlib.util
import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent

try:
    from PIL import Image
except ImportError:  # the product itself never needs Pillow; only this generator does
    Image = None


def generator():
    spec = importlib.util.spec_from_file_location("icons_from_emblem", ROOT / "icons_from_emblem.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Source(unittest.TestCase):
    def test_the_source_uses_only_the_ten_ink_levels(self):
        g = generator()
        rows = g.rejilla()
        self.assertEqual((len(rows), len(rows[0])), (67, 82))
        self.assertTrue(all(0 <= v <= 1 for row in rows for v in row))

    def test_a_character_outside_the_ramp_is_an_error_not_a_guess(self):
        g = generator()
        real = g.FUENTE
        try:
            g.FUENTE = ROOT / "test_icons_emblem.py"
            with self.assertRaises(ValueError):
                g.rejilla()
        finally:
            g.FUENTE = real

    def test_the_manifest_names_exactly_the_generated_files(self):
        manifest = json.loads((ROOT / "interface" / "manifest.json").read_text(encoding="utf-8"))
        named = sorted(icon["src"].rsplit("/", 1)[1].split("?")[0] for icon in manifest["icons"])
        self.assertTrue(all(icon["src"].endswith("?v=2") for icon in manifest["icons"]), "a versioned address, so no device keeps the old picture")
        self.assertEqual(named, ["icono-192.png", "icono-512-maskable.png", "icono-512.png"])


@unittest.skipIf(Image is None, "NO_DATA: Pillow is not installed, so the icons cannot be regenerated here")
class Published(unittest.TestCase):
    def test_what_is_published_is_what_the_generator_makes(self):
        g = generator()
        for name, data in g.ficheros().items():
            with self.subTest(name=name):
                self.assertEqual((ROOT / "assets" / name).read_bytes(), data)

    def test_two_runs_give_the_same_bytes(self):
        g = generator()
        self.assertEqual(g.ficheros(), g.ficheros())

    def test_the_maskable_drawing_stays_inside_the_safe_circle(self):
        im = Image.open(ROOT / "assets" / "icono-512-maskable.png").convert("RGB")
        w, h = im.size
        self.assertEqual(w, h)
        ground, px, far = im.getpixel((2, 2)), im.load(), 0.0
        for y in range(h):
            for x in range(w):
                c = px[x, y]
                if sum(abs(c[i] - ground[i]) for i in range(3)) > 24:
                    far = max(far, math.hypot(x - w / 2, y - h / 2))
        self.assertLessEqual(far, 0.40 * w)

    def test_the_eye_is_violet_and_everything_else_is_ink_on_the_ground(self):
        g = generator()
        im = Image.open(ROOT / "assets" / "icono-512.png").convert("RGB")
        violet = sum(1 for c in im.getdata() if c[2] - c[1] > 60)
        self.assertGreater(violet, 40)
        self.assertLess(violet, 2000)
        self.assertEqual(im.getpixel((2, 2)), g.FONDO)


if __name__ == "__main__":
    unittest.main()
