import hashlib, io, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import lora_signed_download as m

class Opener:
    def __init__(self, value): self.value, self.calls = value, 0
    def open(self, *args, **kwargs): self.calls += 1; return io.BytesIO(self.value)

class Tests(unittest.TestCase):
    def setUp(self):
        self.data = b'abcdefgh'
        h = lambda b: hashlib.sha256(b).hexdigest()
        self.items = [dict(name=f'preceptor-test-{i}.gguf', url=f'https://downloads.preceptoros.org/downloads/preceptor-test-{i}.gguf', size=8, sha256=h(self.data), chunks=[dict(size=4, sha256=h(self.data[:4])), dict(size=4, sha256=h(self.data[4:]))]) for i in range(5)]
        self.raw = json.dumps(dict(schema='preceptoros.lora-download/1', adapters=self.items)).encode()
    def test_explicit_consent_no_io(self):
        op = Opener(self.data)
        with self.assertRaises(m.Refused): m.download(self.raw, b's'*64, b'k'*32, self.items[0]['name'], '/missing', opener=op)
        self.assertEqual(op.calls, 0)
    @patch('lora_signed_download._verify_signature')
    def test_verified_and_corruption_keeps_old_file(self, verifier):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / self.items[0]['name']; path.write_bytes(b'old')
            with self.assertRaises(m.Refused): m.download(self.raw, b's'*64, b'k'*32, path.name, path, True, Opener(b'bad'))
            self.assertEqual(path.read_bytes(), b'old')
            m.download(self.raw, b's'*64, b'k'*32, path.name, path, True, Opener(self.data))
            self.assertEqual(path.read_bytes(), self.data)
    @patch('lora_signed_download._verify_signature', side_effect=ValueError('invalid'))
    def test_bad_signature(self, verifier):
        with self.assertRaises(m.Refused): m.verify_manifest(self.raw, b's'*64, b'k'*32)
    @patch('lora_signed_download._verify_signature')
    def test_foreign_url_rejected(self, verifier):
        self.items[0]['url'] = 'https://evil.invalid/a'
        raw = json.dumps(dict(schema='preceptoros.lora-download/1', adapters=self.items)).encode()
        with self.assertRaises(m.Refused): m.verify_manifest(raw, b's'*64, b'k'*32)
if __name__ == '__main__': unittest.main()
