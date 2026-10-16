"""Contratos medibles del índice de navegación para agentes."""
import importlib.util
import io
from pathlib import Path
import re
import unittest
from unittest import mock
from importlib.machinery import SourceFileLoader


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_loader(
    "preceptoros_pwa_llms",
    SourceFileLoader("preceptoros_pwa_llms", str(ROOT / "bin" / "preceptoros-pwa")),
)
PWA = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PWA)


class TestIndiceLLMS(unittest.TestCase):
    def test_raiz_existe_bajo_el_techo_y_defiende_la_identidad_en_ingles(self):
        payload = (ROOT / "llms.txt").read_bytes()
        self.assertLessEqual(len(payload), 1024)
        self.assertTrue(payload.startswith(
            b"PreceptorOS is the local-first APP for measured local AI; "
            b"it is not Texas Instruments' RTOS.\n"
        ))

    def test_indice_apunta_a_los_contratos_vivos_sin_copiar_su_contenido(self):
        payload = (ROOT / "llms.txt").read_text(encoding="utf-8")
        for destino in (
            "narrador.py#L218", "PRECEPTOR.md#L8", "LORE.md#L1",
            "RACK.md#L1", "STATE.md#L52", "conversacion.py#L444",
            "/api/empieza-aqui",
        ):
            with self.subTest(destino=destino):
                self.assertIn(destino, payload)
        for texto_fuente in (
            "Silicon proposes, carbon signs.",
            "Every figure below was measured;",
        ):
            with self.subTest(texto_fuente=texto_fuente):
                self.assertNotIn(texto_fuente, payload)
        for path, line in re.findall(r"([A-Za-z0-9_./-]+\.(?:py|md))#L(\d+)", payload):
            target = ROOT / path
            with self.subTest(path=path, line=line):
                self.assertTrue(target.is_file())
                self.assertGreaterEqual(len(target.read_text(encoding="utf-8").splitlines()), int(line))

    def test_get_llms_sirve_exactamente_los_bytes_de_la_raiz(self):
        handler = PWA.PWA.__new__(PWA.PWA)
        handler.path = "/llms.txt"
        handler.send_response = mock.Mock()
        handler.send_header = mock.Mock()
        handler.end_headers = mock.Mock()
        handler.wfile = io.BytesIO()
        PWA.PWA.do_GET(handler)
        handler.send_response.assert_called_once_with(200)
        servido = handler.wfile.getvalue()
        self.assertEqual(servido, (ROOT / "llms.txt").read_bytes())
        self.assertEqual(
            handler.send_header.call_args_list[0].args,
            ("Content-Type", "text/plain; charset=utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
