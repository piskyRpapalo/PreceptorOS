"""N4 parity: the app projects the model catalogue to the same Acho frames as the web, hash for hash.

The vector below was measured from preceptoros-web main (public/brains.json sha256 d0e7e237…, projected by
public/game/brain_frame.js, hashed by public/game/canon.js huella). If the web changes the frame, this
test goes red here until both sides move together.
"""
import json
import unittest

import cerebro_frame as CF

CATALOGO = {"esquema": 1, "cerebros": [
    {"id": "mini", "puerta": True, "firmado": False},
    {"id": "charla-web", "puerta": False, "firmado": False},
    {"id": "charla-multi", "puerta": False, "firmado": False},
    {"id": "v7", "puerta": False, "firmado": False},
    {"id": "qwen-coder", "puerta": False, "firmado": False},
    {"id": "mistral-base", "puerta": False, "firmado": False},
    {"id": "superviviente", "puerta": False, "firmado": False}]}

WEB_BRAINS_SHA256 = "d0e7e2376bfa5f63e570bd94aedac6a0158d9a3735f2d8af73166f4218705abd"
WEB_HUELLAS = {
    "brain-charla-multi": "503ac39359a24d5da422317b78c731d7c302d777edd91fbe4d86e854b376aa85",
    "brain-charla-web": "ff8a4387ac015c9a145786dbdc366c137ae222e89fb40081bc0c9a582c0de1f6",
    "brain-mini": "2856417c3dc766b83547f30b9ef4245307d48a40b14da8101b3dc542449568c7",
    "brain-mistral-base": "b0539e123549a263e7f4ac82ed43c0881a20dfd538474304426a892a3f6a6b03",
    "brain-qwen-coder": "c7c35452bd28bb73329a34742bd5eba87dbf02e95c99d55d3b45ce88b1e58a9e",
    "brain-superviviente": "5603c081574c244d839a4541e0c14190b1e108fb8ff10f0abcd3fffd773306cf",
    "brain-v7": "7df8de24dbb4f857c76eb8e801bb2743999369c3603d87160c7d0b5512266c03"}


class CerebroFrame(unittest.TestCase):
    def test_same_seven_hashes_as_the_web(self):
        r = CF.project(CATALOGO)
        self.assertTrue(r["ok"], r)
        self.assertEqual({f["id"]: CF.huella(f) for f in r["frames"]}, WEB_HUELLAS)

    def test_canon_matches_web_canon_on_hard_text(self):
        # measured with web canon.js: ñ, DEL, an astral emoji and a newline
        sample = {"a": "ñ\x7f😀\n", "b": [1, 2]}
        self.assertEqual(CF.canonical(sample), b'{"a":"\\u00f1\\u007f\\ud83d\\ude00\\n","b":[1,2]}')
        self.assertEqual(CF.huella(sample), "11783228ca156743b7bf1933c5dbd695bf78ca7dc05320e09a6edd0253d9f150")

    def test_every_frame_is_a_syllable_and_says_residency_no_data(self):
        for f in CF.project(CATALOGO)["frames"]:
            self.assertLess(len(json.dumps(f, ensure_ascii=False, separators=(",", ":")).encode()), CF.LIMITE_BYTES)
            self.assertEqual(f["seal"], "NO_DATA")
            self.assertIn("residency NO_DATA", f["atoms"][0]["r"])
            self.assertEqual(CF.valida(f), [])

    def test_sorted_and_door_comes_from_the_catalogue(self):
        frames = CF.project(CATALOGO)["frames"]
        self.assertEqual([f["id"] for f in frames], sorted(WEB_HUELLAS))
        mini = next(f for f in frames if f["id"] == "brain-mini")
        self.assertIn("door yes", mini["atoms"][0]["r"])

    def test_refuses_bad_catalogues(self):
        self.assertFalse(CF.project(None)["ok"])
        self.assertFalse(CF.project({"esquema": 2, "cerebros": []})["ok"])
        dup = {"esquema": 1, "cerebros": [{"id": "a"}, {"id": "a"}]}
        self.assertEqual(CF.project(dup)["cause"], "model id is missing, invalid or repeated")
        self.assertEqual(CF.project({"esquema": 1, "cerebros": [{"id": "Bad Id"}]})["ok"], False)

    def test_absent_field_is_no_data_not_a_guess(self):
        f = CF.project({"esquema": 1, "cerebros": [{"id": "x"}]})["frames"][0]
        self.assertIn("door NO_DATA (field absent)", f["atoms"][0]["r"])

    def test_pure(self):
        import ast
        tree = ast.parse(open(CF.__file__, encoding="utf-8").read())
        imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))
                    for a in getattr(n, "names", [])} | {(n.module or "").split(".")[0] for n in ast.walk(tree)
                                                         if isinstance(n, ast.ImportFrom)}
        self.assertEqual(imported - {""}, {"hashlib", "json", "re"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
