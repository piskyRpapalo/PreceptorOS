import json
import tempfile
import unittest
from pathlib import Path
import bandeja_lectura


class BandejaLecturaTest(unittest.TestCase):
    def test_missing_and_valid_files_are_distinct(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(bandeja_lectura.leer(root)['huecos']['estado'], 'NO_DATA')
            folder = root / 'data' / 'bandeja'
            folder.mkdir(parents=True)
            (folder / 'huecos.jsonl').write_text(json.dumps({'id': 'B1'}) + '\n')
            got = bandeja_lectura.leer(root)
            self.assertEqual(got['huecos']['filas'], [{'id': 'B1'}])
            self.assertEqual(got['coberturas']['estado'], 'NO_DATA')

    def test_invalid_or_oversized_is_not_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / 'data' / 'bandeja'
            folder.mkdir(parents=True)
            (folder / 'huecos.jsonl').write_text('{}\nnot-json\n')
            (folder / 'coberturas.jsonl').write_text(' ' * 65537)
            self.assertTrue(all(x['estado'] == 'NO_DATA' for x in bandeja_lectura.leer(tmp).values()))

class BandejaRouteTest(unittest.TestCase):
    def test_cross_origin_and_remote_are_denied(self):
        import importlib.util
        import io
        from importlib.machinery import SourceFileLoader
        from unittest import mock
        path = Path(__file__).parent / 'bin' / 'preceptoros-pwa'
        spec = importlib.util.spec_from_loader('pwa_bandeja', SourceFileLoader('pwa_bandeja', str(path)))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for peer, headers in [('127.0.0.1', {'Host': '127.0.0.1:8740', 'Origin': 'https://outside.example'}),
                              ('192.0.2.10', {'Host': '127.0.0.1:8740', 'Sec-Fetch-Site': 'same-origin'})]:
            handler = module.PWA.__new__(module.PWA)
            handler.path = '/api/bandeja'
            handler.client_address = (peer, 1)
            handler.server = mock.Mock(server_port=8740)
            handler.headers = headers
            handler.send_response = mock.Mock()
            handler.send_header = mock.Mock()
            handler.end_headers = mock.Mock()
            handler.wfile = io.BytesIO()
            handler.do_GET()
            self.assertEqual(handler.send_response.call_args.args[0], 403)
