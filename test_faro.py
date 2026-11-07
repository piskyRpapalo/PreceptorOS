"""Observatory beacon: two proofs kept apart, each with cause and time. No network: a fake opener."""
import io
import json
import unittest
import urllib.error

import faro

STATION = "http://127.0.0.1:9"
APP = "http://127.0.0.1:8"


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        self.t += 0.5
        return self.t


def opener_for(*, voice=True, app_reply=None, app_error=None, seen=None):
    def open_url(req, timeout=None):
        url = req.full_url
        if seen is not None:
            seen.append((url, dict(req.header_items())))
        if url.endswith("/api/tags"):
            if not voice:
                raise urllib.error.URLError("down")
            return io.BytesIO(json.dumps({"models": [{"name": "hexelion:latest"}]}).encode())
        if url.endswith("/api/generate"):
            return io.BytesIO(json.dumps({"model": "hexelion:latest", "response": "Yes.",
                                          "total_duration": 7_900_000_000}).encode())
        if url.endswith("/api/hexelion/chat"):
            if app_error:
                raise app_error
            return io.BytesIO(json.dumps(app_reply).encode())
        raise AssertionError("undeclared request: " + url)
    return open_url


CITED = {"respuesta": {"estado": "MEASURED", "voz": "hexelion", "texto": "x",
                       "fuentes": [{"id": 4, "updated_at": "t", "sha256": "a" * 64}],
                       "maquina": {"modelo": "hexelion:latest", "ms": 22897.9}}}
UNCITED = {"respuesta": {"estado": "NO_DATA", "causa": "no_matches", "fuentes": []}}


class Beacon(unittest.TestCase):
    def run_faro(self, **kw):
        return faro.faro("LoRA v7 servido en Ollama", endpoint=STATION, app=APP,
                         opener=opener_for(**kw), clock=Clock(), fecha="2026-11-07")

    def test_both_measured_stay_two_proofs(self):
        f = self.run_faro(app_reply=CITED)
        self.assertEqual(f["voz_directa"]["estado"], "MEASURED")
        self.assertEqual(f["voz_directa"]["ms_generacion"], 7900.0)
        self.assertEqual(f["app_con_fuente"]["estado"], "MEASURED")
        self.assertEqual(f["app_con_fuente"]["fuentes"], 1)
        self.assertNotIn("estado", f)  # no combined verdict, on purpose
        self.assertLess(len(json.dumps(f, ensure_ascii=False, separators=(",", ":")).encode()), 1024)

    def test_voice_up_app_without_source_is_not_measured(self):
        f = self.run_faro(app_reply=UNCITED)
        self.assertEqual(f["voz_directa"]["estado"], "MEASURED")
        self.assertEqual(f["app_con_fuente"], {"prueba": "app_con_fuente", "estado": "NO_DATA",
                                               "causa": "no_matches", "ms_total": 500.0})

    def test_measured_answer_without_sources_is_not_a_cited_answer(self):
        reply = {"respuesta": dict(CITED["respuesta"], fuentes=[])}
        self.assertEqual(self.run_faro(app_reply=reply)["app_con_fuente"]["causa"], "app_answer_without_source")

    def test_station_down_app_up_is_still_two_answers(self):
        f = self.run_faro(voice=False, app_reply=CITED)
        self.assertEqual(f["voz_directa"]["estado"], "NO_DATA")
        self.assertEqual(f["voz_directa"]["causa"], "station_unavailable")
        self.assertEqual(f["app_con_fuente"]["estado"], "MEASURED")

    def test_app_unreachable_and_rejected_have_causes(self):
        self.assertEqual(self.run_faro(app_error=urllib.error.URLError("x"))["app_con_fuente"]["causa"], "app_unavailable")
        err = urllib.error.HTTPError(APP, 403, "no", {}, None)
        self.assertEqual(self.run_faro(app_error=err)["app_con_fuente"]["causa"], "app_rejected_request")

    def test_honest_no_data_on_a_503_keeps_its_cause(self):
        body = io.BytesIO(json.dumps({"respuesta": {"estado": "NO_DATA", "causa": "no_matches"}}).encode())
        err = urllib.error.HTTPError(APP, 503, "x", {}, body)
        self.assertEqual(self.run_faro(app_error=err)["app_con_fuente"]["causa"], "no_matches")

    def test_app_must_be_loopback(self):
        for app in ("http://10.0.0.1:8", "https://127.0.0.1:8", "http://127.0.0.1", None, "http://127.0.0.1:8/x"):
            r = faro.app_con_fuente("q", app=app, opener=opener_for(app_reply=CITED), clock=Clock())
            self.assertEqual(r["causa"], "app_loopback_required", app)

    def test_app_request_carries_local_origin_and_nothing_else_is_called(self):
        seen = []
        faro.faro("q", endpoint=STATION, app=APP, opener=opener_for(app_reply=CITED, seen=seen), clock=Clock())
        urls = [u for u, _ in seen]
        self.assertEqual(urls, [STATION + "/api/tags", STATION + "/api/generate", APP + "/api/hexelion/chat"])
        self.assertEqual(seen[-1][1].get("Origin"), APP)


if __name__ == "__main__":
    unittest.main()
