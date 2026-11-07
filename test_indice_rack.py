"""Tests for indice_rack: exact quotes, origin lines, secret scrub, the book's contract."""
import hashlib, tempfile, unittest
from pathlib import Path
import hexelion_book
import indice_rack as I

DOCS = [("rack: p0x/mente/buzon.md", "Ley", "La Ley del Buzón: el silicio no commitea.\n\napi_key = abc123\n\nOtra frase.", "2026-11-07"),
        ("github: o/r#7 (open)", "PR", "Caravan states: proposed, active, intercepted.", "2026-11-07"),
        ("rack: p0x/secretos/claves.md", "x", "nada", "2026-11-07")]


class Rack(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(); self.db = Path(self.d.name) / "rack.db"
        I.construir(self.db, DOCS)

    def tearDown(self):
        self.d.cleanup()

    def test_hit_keeps_origin_and_exact_hash(self):
        r = I.buscar("caravan states", self.db)
        self.assertEqual(r["estado"], "MEASURED")
        f = r["fuentes"][0]
        self.assertTrue(f["texto"].startswith("github: o/r#7 (open)\n"))
        self.assertEqual(f["sha256"], hashlib.sha256(f["texto"].encode()).hexdigest())
        self.assertGreater(f["id"], I.ID_BASE)

    def test_secret_lines_and_secret_paths_never_indexed(self):
        self.assertEqual(I.buscar("api_key abc123", self.db)["estado"], "NO_DATA")
        self.assertEqual(I.buscar("nada", self.db)["estado"], "NO_DATA")

    def test_chunks_fit_budget(self):
        for t in I.trozos("rack: x", "palabra " * 500):
            self.assertLessEqual(len(t.encode()), I.CHUNK_B)

    def test_missing_index_is_no_data(self):
        self.assertEqual(I.buscar("caravan states", Path(self.d.name) / "nope.db")["causa"], "rack_index_not_built")

    def test_union_passes_the_book(self):
        mem = I.no_data("memory_unavailable")
        ev = I.unir(mem, I.buscar("buzón silicio", self.db))
        prepared, prompt = hexelion_book.construir_prompt("¿qué dice la ley del buzón?", ev)
        self.assertEqual(prepared.get("estado"), "MEASURED")
        self.assertIn("rack: p0x/mente/buzon.md", prompt)

    def test_union_both_empty_keeps_cause(self):
        self.assertEqual(I.unir(I.no_data("a"), I.no_data("rack_no_match"))["estado"], "NO_DATA")

    def test_union_budget(self):
        big = {"estado": "MEASURED", "fuentes": [{"texto": "x" * 700, "id": 1}, {"texto": "y" * 300, "id": 2}]}
        out = I.unir(big, {"estado": "NO_DATA"})
        self.assertLessEqual(sum(len(f["texto"]) for f in out["fuentes"]), 768)

    def test_query_invalid(self):
        self.assertEqual(I.buscar("", self.db)["estado"], "NO_DATA")
        self.assertEqual(I.buscar("x" * 2000, self.db)["estado"], "NO_DATA")


if __name__ == "__main__":
    unittest.main()
