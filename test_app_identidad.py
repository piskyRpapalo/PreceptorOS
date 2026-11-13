"""Install identity (commission 2026-11-13, Entrega B): the installed app is PreceptorOS; Hexelion is the brain inside.

Android keeps an installed web app (WebAPK) by its manifest id and start URL. Changing those would make a SECOND
installation instead of renaming the first one, so they are pinned here. The name and icons change only through
the manifest, and the service worker serves the manifest cache-first: a new cache name is what lets an install read
the new manifest. Icon bytes = generator output is checked in test_icons_emblem.py; not repeated here.
"""
import json
import re
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = json.loads((ROOT / "interface/manifest.json").read_text(encoding="utf-8"))
SW = (ROOT / "interface/sw.js").read_text(encoding="utf-8")
APP = (ROOT / "interface/app.html").read_text(encoding="utf-8")


def png_size(path):
    raw = path.read_bytes()[:24]
    if raw[:8] != b"\x89PNG\r\n\x1a\n" or raw[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", raw[16:24])


class Name(unittest.TestCase):
    def test_the_installed_app_is_named_preceptoros_on_every_launcher_surface(self):
        self.assertEqual((MANIFEST["name"], MANIFEST["short_name"]), ("PreceptorOS", "PreceptorOS"))
        self.assertIn("<title>PreceptorOS</title>", APP)

    def test_hexelion_stays_the_brain_inside_talk_not_the_product(self):
        self.assertNotIn("Hexelion", MANIFEST["name"] + MANIFEST["short_name"])
        self.assertIn('aria-label="Hexelion commands"', APP)


class SameInstallation(unittest.TestCase):
    def test_id_start_url_and_scope_do_not_move(self):
        # Moving any of these makes Android mint a second app next to the old one.
        self.assertEqual((MANIFEST["id"], MANIFEST["start_url"], MANIFEST["scope"], MANIFEST["display"]),
                         ("/", "/app.html", "/", "standalone"))


class Icons(unittest.TestCase):
    def test_each_icon_exists_with_its_declared_size_and_purpose(self):
        purposes = set()
        for icon in MANIFEST["icons"]:
            path = ROOT / icon["src"].split("?", 1)[0].lstrip("/")
            side = int(icon["sizes"].split("x")[0])
            self.assertEqual(png_size(path), (side, side), icon["src"])
            purposes.add(icon["purpose"])
        self.assertEqual(purposes, {"any", "maskable"})

    def test_the_page_names_the_same_icon_addresses_as_the_manifest(self):
        page = set(re.findall(r'href="(/assets/icono-[^"]+)"', APP))
        self.assertTrue(page)
        self.assertLessEqual(page, {i["src"] for i in MANIFEST["icons"]})


class Update(unittest.TestCase):
    def test_the_shell_caches_the_manifest_and_the_exact_icon_addresses(self):
        shell = SW[SW.index("const Armazon"):SW.index("];", SW.index("const Armazon"))]
        self.assertIn('"/manifest.json"', shell)
        for icon in MANIFEST["icons"]:
            self.assertIn('"%s"' % icon["src"], shell)

    def test_the_cache_name_moved_with_the_identity(self):
        # The manifest is served cache-first; without a new cache an install keeps the old name forever.
        self.assertIn('const Cache = "preceptoros-armazon-v174";', SW)
        self.assertIn("(install identity)", SW)


if __name__ == "__main__":
    unittest.main()
