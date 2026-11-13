"""Tests for firmas_pendientes: the fence's own rules, read only, never raising."""
import unittest
import firmas_pendientes as F

SHA = "a" * 40
HOY = "2026-11-07"


def pr(n=1, sha=SHA, base="main", rama="claude/x-20261107", checks=None):
    return {"number": n, "title": "HITL · x", "url": "u", "headRefOid": sha, "headRefName": rama,
            "baseRefName": base, "isDraft": True,
            "statusCheckRollup": checks if checks is not None else [
                {"name": "test_web", "conclusion": "SUCCESS"}, {"name": "hitl", "conclusion": "FAILURE"}]}


def firma(sha=SHA, fecha=HOY, cabecera=True):
    return {"body": ("FIRMA SOBERANO\n" if cabecera else "") + "HITL: %s x %s" % (sha, fecha)}


class Firmas(unittest.TestCase):
    def accion(self, p, comentarios=(), prs=None):
        return F.documento({"o/r": prs or [p]}, list(comentarios), HOY, "t")["filas"][0]

    def test_green_unsigned_is_sign_with_exact_fence_text(self):
        f = self.accion(pr())
        self.assertEqual(f["action"], "sign")
        self.assertEqual(f["signature"], "FIRMA SOBERANO\nHITL: %s x %s" % (SHA, HOY))
        self.assertRegex(f["signature"].splitlines()[1], F.LINEA)

    def test_hitl_check_never_decides_green(self):
        self.assertEqual(F.estado_chequeos([{"name": "hitl", "conclusion": "FAILURE"}]), "no_data")

    def test_signed_exact_head_is_merge(self):
        self.assertEqual(self.accion(pr(), [firma()])["action"], "merge")

    def test_signature_without_header_does_not_count(self):
        self.assertEqual(self.accion(pr(), [firma(cabecera=False)])["action"], "sign")

    def test_signature_for_other_head_does_not_count(self):
        self.assertEqual(self.accion(pr(), [firma(sha="b" * 40)])["action"], "sign")

    def test_future_date_does_not_count(self):
        self.assertEqual(self.accion(pr(), [firma(fecha="2026-11-08")])["action"], "sign")

    def test_red_and_running(self):
        self.assertEqual(self.accion(pr(checks=[{"name": "t", "conclusion": "FAILURE"}]))["action"], "red")
        self.assertEqual(self.accion(pr(checks=[{"name": "t", "status": "IN_PROGRESS"}]))["action"], "running")

    def test_stacked_on_open_base_waits(self):
        prs = [pr(1, base="claude/a"), pr(2, rama="claude/a")]
        filas = F.documento({"o/r": prs}, [], HOY, "t")["filas"]
        self.assertEqual({f["n"]: f["action"] for f in filas}[1], "wait_base")

    def test_stacked_on_dead_base_is_retarget(self):
        f = self.accion(pr(base="codex/merged-20261107"))
        self.assertEqual((f["action"], f["retarget"]), ("retarget", "gh pr edit 1 -R o/r --base main"))

    def test_malformed_pr_is_no_data_never_raises(self):
        d = F.documento({"o/r": [{"bad": 1}, None]}, [None, 3], HOY, "t")
        self.assertTrue(all(f["action"] == "no_data" for f in d["filas"]))

    def test_order_and_determinism(self):
        prs = [pr(3, checks=[{"name": "t", "conclusion": "FAILURE"}]), pr(2), pr(1, base="dead")]
        a = F.documento({"o/r": prs}, [], HOY, "t")
        self.assertEqual([f["action"] for f in a["filas"]], ["retarget", "sign", "red"])
        self.assertEqual(a, F.documento({"o/r": list(prs)}, [], HOY, "t"))

    def test_slug_matches_fence(self):
        self.assertEqual(F.slug("claude/web-map-chrome-20261107"), "web-map-chrome")
        self.assertRegex("HITL: %s %s %s" % (SHA, F.slug("x/ñ é"), HOY), F.LINEA)

    def test_module_never_writes_or_calls_out(self):
        src = open(F.__file__, encoding="utf-8").read()
        for prohibido in ("subprocess", "urllib", "open(", "requests", ".now("):
            self.assertNotIn(prohibido, src)


class Cara(unittest.TestCase):
    """The face only reads and copies: it never posts a signature."""
    def test_wiring_and_no_write(self):
        from pathlib import Path
        raiz = Path(__file__).resolve().parent
        js = (raiz / "interface" / "firmas.js").read_text(encoding="utf-8")
        html = (raiz / "interface" / "app.html").read_text(encoding="utf-8")
        server = (raiz / "bin" / "preceptoros-pwa").read_text(encoding="utf-8")
        # [deprecated 2026-11-08] the scraped block left Command; HITL in Boundary replaces it.
        self.assertNotIn('id="firmas"', html)
        self.assertIn('id="hitl"', html)
        # Deprecated renderer remains in source for history, but it must not
        # execute or consume offline cache in the sole live app.
        self.assertNotIn('<script src="/firmas.js', html)
        self.assertIn('<script src="/hitl.js?v=7"></script>', html)
        sw = (raiz / "interface" / "sw.js").read_text(encoding="utf-8")
        self.assertNotIn('"/firmas.js?v=1"', sw)
        import re
        cache = re.search(r'const Cache = "preceptoros-armazon-v(\d+)"', sw)
        self.assertIsNotNone(cache)
        self.assertGreaterEqual(int(cache.group(1)), 156)
        self.assertIn('if ruta == "/api/firmas":', server)
        self.assertNotIn("POST", js); self.assertNotIn("buzon", js)
        self.assertIn("preceptoros-firmar", js)


if __name__ == "__main__":
    unittest.main()
