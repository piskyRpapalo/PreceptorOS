"""E3: synthesis doubles prove contracts, never physical sound."""
import base64
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave

import voz_creacion as V


def wav():
    out = io.BytesIO()
    with wave.open(out, 'wb') as w:
        w.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
        w.writeframes(b'\x01\x00' * 160)
    return out.getvalue()


class CreationVoice(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.model = Path(self.tmp.name) / 'model.onnx'
        self.model.write_bytes(b'public synthetic model fixture')
        Path(str(self.model) + '.json').write_text('{"fixture":true}')
        self.engine = Path(self.tmp.name) / 'engine'
        self.engine.write_bytes(b'public synthetic engine fixture')
        self.calls = []
        for name, value in [('MODELO_DEFECTO', str(self.model)),
                            ('piper_binario', lambda: str(self.engine)),
                            ('piper_disponible', lambda: True),
                            ('hablar', self.speak)]:
            p = patch.object(V.voz, name, value)
            p.start()
            self.addCleanup(p.stop)

    def speak(self, text, path, **kwargs):
        self.calls.append((text, kwargs))
        Path(path).write_bytes(wav())
        return path

    def test_complete_inventory_and_one_profile(self):
        result = V.generar('I made this drawing.')
        self.assertEqual(result['estado'], 'ok', result)
        c, d = result['catalog'], result['declaration']
        self.assertEqual(c['schema'], 'preceptoros.creation-voice/1')
        self.assertEqual(d['schema'], 'preceptoros.creation-declaration/1')
        self.assertEqual(c['profile_id'], hashlib.sha256(c['profile'].encode()).hexdigest())
        self.assertEqual(d['profile_id'], c['profile_id'])
        self.assertEqual(set(c['clips']), set(V.INVENTARIO))
        self.assertEqual(len(self.calls), len(V.INVENTARIO) + 1)
        self.assertTrue(all(params == V.PARAMETROS for _, params in self.calls))
        self.assertNotIn(self.tmp.name, json.dumps(result))
        for clip in [*c['clips'].values(), d]:
            data = base64.b64decode(clip['data'], validate=True)
            self.assertEqual(clip['size'], len(data))
            self.assertEqual(clip['sha256'], hashlib.sha256(data).hexdigest())
            V.validar_wav(data)

    def test_repeatable_profile_and_bytes(self):
        self.assertEqual(V.generar('A line.'), V.generar('A line.'))

    def test_model_change_aborts_without_download(self):
        def change(text, path, **kw):
            self.model.write_bytes(b'changed')
            return self.speak(text, path, **kw)
        with patch.object(V.voz, 'hablar', change):
            r = V.generar('A line.')
        self.assertEqual(r['estado'], 'NO_DATA')
        self.assertIn('profile changed', r['causa'])
        self.assertNotIn('catalog', r)

    def test_missing_engine_and_generation_failure(self):
        with patch.object(V.voz, 'piper_disponible', return_value=False):
            self.assertEqual(V.generar('A line.')['estado'], 'NO_DATA')
        with patch.object(V.voz, 'hablar', return_value=None):
            self.assertIn('generation failed', V.generar('A line.')['causa'])

    def test_engine_exception_is_sanitized(self):
        for error in [RuntimeError(self.tmp.name), ValueError(self.tmp.name)]:
            with patch.object(V.voz, 'hablar', side_effect=error):
                result = V.generar('A line.')
            self.assertEqual(result['estado'], 'NO_DATA')
            self.assertNotIn(self.tmp.name, json.dumps(result))

    def test_invalid_wav_and_whole_package_limit(self):
        def bad(text, path, **kw):
            Path(path).write_bytes(b'not a WAV')
            return path
        with patch.object(V.voz, 'hablar', bad):
            self.assertEqual(V.generar('A line.')['estado'], 'NO_DATA')
        with patch.object(V, 'LIMITE', 1500):
            r = V.generar('A line.')
            self.assertEqual(r['estado'], 'NO_DATA')
            self.assertIn('limit', r['causa'])

    def test_wav_rejects_truncation_extra_chunks_and_stereo(self):
        good = wav()
        for data in [good[:-1], good + b'extra', good[:22] + b'\x02\x00' + good[24:]]:
            with self.assertRaises(ValueError):
                V.validar_wav(data)

    def test_empty_or_long_author_statement(self):
        for text in ['', '   ', 'x' * 1025, None, '\ud800']:
            self.assertEqual(V.generar(text)['estado'], 'NO_DATA')
        self.assertEqual(self.calls, [])


if __name__ == '__main__':
    unittest.main()
