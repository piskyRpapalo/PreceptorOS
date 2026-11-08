"""N4 parity: the app projects the model catalogue to the same Acho frames as the web, hash for hash.

The vector below was measured from preceptoros-web main (public/brains.json sha256 d0e7e237…, projected by
public/game/brain_frame.js, hashed by public/game/canon.js huella; N4 P2: the frame carries it as `huella`). If the web changes the frame, this
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
    "brain-charla-multi": "cce2b5961c8f5eb7672e79ad9efecc394e662376e39122aecf314dff0c25469f",
    "brain-charla-web": "9a1b0edf4d2f9d4f35164ac87ea3d9ad0703a957118a6d5447832cdf7cfb7d31",
    "brain-mini": "a68342de8ca6d670fe1ce494708713b4c61bc6387dd9dddf459bcdc1d3d92aa4",
    "brain-mistral-base": "bd4d78eda6266c8b13b00c4779baf2b588a995cfe16e420aea02a015a53500b6",
    "brain-qwen-coder": "0958e33e080519aa9f5889b9d38ddb460b81c8e3d979e6b4420078aaa6296f51",
    "brain-superviviente": "d6b50b1b8d0921c9f038aac7a1ec73a65dee8ba9746a29a6202ad374d32119cd",
    "brain-v7": "bb5ef043d2d07c1142490664a275b0f8f2b0c3b6e69b764817ae5b4de5a7304d"}


class CerebroFrame(unittest.TestCase):
    def test_same_seven_hashes_as_the_web(self):
        r = CF.project(CATALOGO)
        self.assertTrue(r["ok"], r)
        self.assertEqual({f["id"]: f["huella"] for f in r["frames"]}, WEB_HUELLAS)
        for f in r["frames"]:
            rest = {k: v for k, v in f.items() if k != "huella"}
            self.assertEqual(CF.huella(rest), f["huella"])

    def test_canon_matches_web_canon_on_hard_text(self):
        # measured with web canon.js: ñ, DEL, an astral emoji and a newline
        sample = {"a": "ñ\x7f😀\n", "b": [1, 2]}
        self.assertEqual(CF.canonical(sample), b'{"a":"\\u00f1\\u007f\\ud83d\\ude00\\n","b":[1,2]}')
        self.assertEqual(CF.huella(sample), "11783228ca156743b7bf1933c5dbd695bf78ca7dc05320e09a6edd0253d9f150")

    def test_every_frame_is_a_syllable_and_says_residency_no_data(self):
        for f in CF.project(CATALOGO)["frames"]:
            self.assertLess(len(json.dumps(f, ensure_ascii=False, separators=(",", ":")).encode()), CF.LIMITE_BYTES)
            self.assertEqual(f["seal"], "NO_DATA")
            self.assertIn("residency NO_DATA (CAUSA_RESIDENTE)", f["atoms"][0]["r"])
            self.assertEqual((f["residencia"], f["causa"]["CAUSA_RESIDENTE"]), ("NO_DATA", CF.CAUSA_RESIDENTE))
            self.assertLess(len(CF.canonical(f)), CF.LIMITE_BYTES)
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
