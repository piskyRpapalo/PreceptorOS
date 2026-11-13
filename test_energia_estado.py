"""Energy observation tests; synthetic meter frames, no physical socket actions."""
import io
import json
import os
import sys
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, os.path.dirname(__file__))
import energia_estado as E
import metricas as M


def reading(power, voltage=230, current=0.5, factor=1.0):
    data = {"StatusSNS": {"ENERGY": {"Power": power, "Voltage": voltage,
                                     "Current": current, "Factor": factor}}}
    stream = mock.MagicMock()
    stream.read.return_value = json.dumps(data).encode("utf-8")
    stream.__enter__.return_value = stream
    return stream


class MeterContracts(unittest.TestCase):
    def read(self, stream):
        with mock.patch.object(M, "ENCHUFE", "http://127.0.0.1:9999"), \
             mock.patch.object(M.urllib.request, "urlopen", return_value=stream):
            return M._consumo_w()

    def test_unconfigured_meter_never_touches_network(self):
        with mock.patch.object(M, "ENCHUFE", M.ENCHUFE_NO_CONFIGURADO), \
             mock.patch.object(M.urllib.request, "urlopen") as fetch:
            found = M._consumo_w()
            fetch.assert_not_called()
        self.assertEqual(found["estado"], "NO_DATA")
        d = E.snapshot(reader=lambda: found)
        self.assertEqual(d["consumo"]["causa"], "meter_endpoint_not_configured")
        self.assertTrue(d["solo_lectura"])

    def test_consistent_power_keeps_source_and_measure(self):
        result = self.read(reading(115, voltage=230, current=0.5, factor=1))
        self.assertEqual(result["estado"], "MEDIDO")
        self.assertEqual(result["valor"], 115.0)
        d = E.snapshot(reader=lambda: result,
                       clock=lambda: datetime(2026, 11, 11, tzinfo=timezone.utc))
        self.assertEqual(d["estado"], "PARCIAL")
        self.assertEqual(d["consumo"]["estado"], "MEDIDO")
        self.assertEqual(d["consumo"]["valor"], 115.0)
        self.assertEqual(d["bateria"]["estado"], "NO_DATA")
        self.assertEqual(d["solar"]["estado"], "NO_DATA")
        self.assertEqual(d["reparto"]["estado"], "NO_DATA")
        self.assertIn("115.0 W", E.decir(d))

    def test_measured_incoherence_never_published_as_watts(self):
        result = self.read(reading(114.1, voltage=35, current=0.96, factor=1))
        self.assertEqual(result["estado"], "NO_DATA")
        d = E.respuesta(reader=lambda: result)
        self.assertEqual(d["estado"], "NO_DATA")
        self.assertEqual(d["consumo"]["causa"], "meter_electrical_incoherent")
        self.assertIsNone(d["consumo"]["valor"])
        self.assertIn("NO_DATA (meter_electrical_incoherent)", d["texto"])
        self.assertNotIn("114.1", d["texto"])

    def test_missing_reference_is_not_silent_success(self):
        frame = {"StatusSNS": {"ENERGY": {"Power": 115}}}
        stream = reading(115)
        stream.read.return_value = json.dumps(frame).encode()
        result = self.read(stream)
        self.assertEqual(result["estado"], "NO_DATA")
        self.assertEqual(E.snapshot(reader=lambda: result)["consumo"]["causa"],
                         "meter_reference_incomplete")

    def test_negative_and_non_finite_are_not_power_measurements(self):
        for watts in (-1, float("nan"), True):
            with self.subTest(watts=repr(watts)):
                self.assertEqual(self.read(reading(watts))["estado"], "NO_DATA")

    def test_measured_zero_is_not_the_no_data_placeholder(self):
        result = self.read(reading(0, voltage=230, current=0, factor=0))
        self.assertEqual(result["estado"], "MEDIDO")
        self.assertEqual(result["valor"], 0.0)

    def test_reader_exception_does_not_leak_private_url(self):
        def exploding():
            raise RuntimeError("meter at private-device.invalid secret")
        text = json.dumps(E.respuesta(reader=exploding), ensure_ascii=False)
        self.assertNotIn("private-device.invalid", text)
        self.assertEqual(E.respuesta(reader=exploding)["consumo"]["causa"],
                         "meter_reader_failed")

    def test_snapshot_is_finite_bounded_and_without_actuators(self):
        d = E.respuesta(reader=lambda: {"estado": "NO_DATA", "causa": "meter endpoint not configured"})
        self.assertEqual(d["esquema"], "preceptoros.energy-read/1")
        self.assertLess(len(json.dumps(d, ensure_ascii=False).encode()), 1024)
        self.assertFalse(any(k in d for k in ("switch", "set_power", "action", "relay")))
        self.assertTrue(d["solo_lectura"])


class LocalEnergyRoutes(unittest.TestCase):
    def handler(self, path="/api/energia", *, host="127.0.0.1:8742", site=None,
                origin=None, remote="127.0.0.1"):
        from test_pwa import PWA
        h = PWA.PWA.__new__(PWA.PWA)
        h.path = path
        h.headers = {"Host": host}
        if site is not None:
            h.headers["Sec-Fetch-Site"] = site
        if origin is not None:
            h.headers["Origin"] = origin
        h.client_address = (remote, 12345)
        h.server = SimpleNamespace(server_port=8742)
        h._es_loopback = lambda addr: addr == "127.0.0.1"
        h._nodo_local_autorizado = lambda: origin == "http://127.0.0.1:8742"
        captured = {}
        h._json = lambda code, body: captured.update(code=code, body=body)
        return h, captured, PWA

    def test_machine_and_app_get_same_source_contract(self):
        for path in ("/api/energia", "/api/hexelion/energia"):
            with self.subTest(path=path):
                h, got, PWA = self.handler(path, site="same-origin")
                with mock.patch.object(PWA._energia_estado, "respuesta",
                                       return_value={"esquema": E.SCHEMA, "solo_lectura": True}) as reader:
                    PWA.PWA.do_GET(h)
                    reader.assert_called_once_with()
                self.assertEqual(got["code"], 200)
                self.assertTrue(got["body"]["solo_lectura"])

    def test_external_origin_and_dns_rebinding_fail_before_sensor(self):
        for bad in ({"host": "example.org:8742"},
                    {"site": "cross-site"},
                    {"origin": "https://example.org"},
                    {"remote": "203.0.113.10"}):
            with self.subTest(bad=bad):
                h, got, PWA = self.handler(**bad)
                with mock.patch.object(PWA._energia_estado, "respuesta") as reader:
                    PWA.PWA.do_GET(h)
                    reader.assert_not_called()
                self.assertEqual(got["code"], 403)

    def test_local_cli_without_origin_is_read_only(self):
        h, got, PWA = self.handler(path="/api/hexelion/energia", host="localhost:8742")
        with mock.patch.object(PWA._energia_estado, "respuesta",
                               return_value={"esquema": E.SCHEMA, "solo_lectura": True}):
            PWA.PWA.do_GET(h)
        self.assertEqual(got["code"], 200)


class MiniHtmlEnergyContract(unittest.TestCase):
    def test_card_script_and_cache_are_the_same_app(self):
        from pathlib import Path
        from test_pwa import PWA
        root = Path(__file__).resolve().parent
        html = (root / "interface/app.html").read_text(encoding="utf-8")
        js = (root / "interface/energia_ui.js").read_text(encoding="utf-8")
        sw = (root / "interface/sw.js").read_text(encoding="utf-8")
        self.assertIn('id="energy-read"', html)
        self.assertIn('id="energy-status" role="status" aria-live="polite"', html)
        self.assertIn('id="energy-json"', html)
        self.assertIn('src="/energia_ui.js?v=2"', html)
        self.assertIn('"/energia_ui.js?v=2"', sw)
        self.assertIn('preceptoros-armazon-v174', sw)
        self.assertIn("/energia_ui.js", PWA.ESTATICOS)
        self.assertIn('cache: "no-store"', js)
        self.assertIn('spoken.textContent = data.texto', js)
        self.assertNotIn('setInterval(', js)
        self.assertNotIn('cmnd=Power', js)
        self.assertNotIn('fetch("http', js)


if __name__ == "__main__":
    unittest.main()
