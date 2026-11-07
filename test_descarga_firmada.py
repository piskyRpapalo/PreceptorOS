import hashlib, io, json, os, shutil, subprocess, tempfile, unittest
from pathlib import Path
from urllib.request import Request
import descarga_firmada as m

SHA = 'a' * 40
H = lambda b: hashlib.sha256(b).hexdigest()


class Opener:
    def __init__(self, value): self.value, self.calls, self.urls = value, 0, []
    def open(self, req, timeout=None):
        self.calls += 1; self.urls.append(req.full_url); return io.BytesIO(self.value)


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('openssl'): raise RuntimeError('openssl required')
        cls.tmp = tempfile.TemporaryDirectory(); r = Path(cls.tmp.name)
        subprocess.run(['openssl', 'genpkey', '-algorithm', 'ED25519', '-out', str(r / 'k.pem')], check=True, capture_output=True)
        pub = subprocess.run(['openssl', 'pkey', '-in', str(r / 'k.pem'), '-pubout', '-outform', 'DER'], check=True, capture_output=True).stdout
        cls.key, cls.dir = pub[-32:], r
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def sign(self, raw):
        (self.dir / 'm').write_bytes(raw)
        subprocess.run(['openssl', 'pkeyutl', '-sign', '-inkey', str(self.dir / 'k.pem'), '-rawin', '-in', str(self.dir / 'm'), '-out', str(self.dir / 's')], check=True, capture_output=True)
        return (self.dir / 's').read_bytes()

    def setUp(self):
        self.data = b'abcdefgh'
        self.entry = dict(fichero='interface/app.css', bytes=8, sha256=H(self.data),
                          chunks=[dict(bytes=4, sha256=H(self.data[:4])), dict(bytes=4, sha256=H(self.data[4:]))])
        self.out = tempfile.TemporaryDirectory(); self.root = Path(self.out.name)
    def tearDown(self): self.out.cleanup()

    def man(self, **kw):
        d = dict(schema=m.SCHEMA, ref=SHA, via='raw', files=[self.entry]); d.update(kw)
        raw = json.dumps(d).encode(); return raw, self.sign(raw)
    def run_(self, raw=None, sig=None, data=None, name='interface/app.css', consent=True, op=None, **kw):
        if raw is None: raw, sig = self.man(**kw)
        op = op or Opener(self.data if data is None else data)
        return m.instalar(raw, sig, self.key, name, self.root, consent, op), op
    def refused(self, cause, **kw):
        with self.assertRaises(m.Refused) as c: self.run_(**kw)
        self.assertEqual(c.exception.args[0], cause)

    def test_install_and_receipt(self):
        rec, op = self.run_()
        dest = self.root / 'interface/app.css'
        self.assertEqual(rec['sha256'], H(dest.read_bytes()))
        self.assertEqual(rec['esquema'], m.RECEIPT)
        self.assertEqual([c['estado'] for c in rec['chunks']], ['OK', 'OK'])
        self.assertEqual(op.urls, [f'{m.RAW}{SHA}/interface/app.css'])
    def test_tampered_signature(self):
        raw, sig = self.man(); self.refused('signature or manifest invalid', raw=raw + b' ', sig=sig)
    def test_extra_and_duplicate_keys(self):
        raw = json.dumps(dict(schema=m.SCHEMA, ref=SHA, via='raw', files=[self.entry], x=1)).encode()
        self.refused('manifest schema', raw=raw, sig=self.sign(raw))
        raw = b'{"schema":"%s","schema":"%s","ref":"%s","via":"raw","files":[]}' % ((m.SCHEMA.encode(),) * 2 + (SHA.encode(),))
        self.refused('signature or manifest invalid', raw=raw, sig=self.sign(raw))
    def test_ref_not_exact(self):
        for ref in ('main', 'HEAD', 'abc1234', SHA.upper()): self.refused('ref_not_exact', ref=ref)
        self.refused('ref_not_exact', ref='main', via='release')
        self.refused('ref_not_exact', ref=SHA, via='release')
    def test_edge_not_published(self): self.refused('edge_route_not_published', via='edge')
    def test_model_data_never_leaves(self):
        for n in ('interface/m.gguf', 'interface/LoRA/a.css', 'interface/x.JSONL', 'interface/adapter.js', 'interface/dataset/a.css'):
            self.entry['fichero'] = n; self.refused('model_data_never_leaves', name=n)
    def test_bad_paths(self):
        for n in ('interface/../x', '/interface/a', 'interface\\a', 'other/a.css', 'interface/a b'):
            self.entry['fichero'] = n; self.refused('fichero_invalid', name=n)
    def test_corrupt_chunk_keeps_destination(self):
        dest = self.root / 'interface/app.css'; dest.parent.mkdir(); dest.write_bytes(b'old')
        self.refused('chunk_digest', data=b'abcdXXXX')
        self.assertEqual(dest.read_bytes(), b'old'); self.assertEqual(os.listdir(dest.parent), ['app.css'])
    def test_corrupt_chunk_fresh(self):
        self.refused('chunk_digest', data=b'Xbcdefgh')
        self.assertEqual(os.listdir(self.root / 'interface'), [])
    def test_truncated_and_oversize(self):
        self.refused('truncated', data=b'abcdef'); self.refused('size_mismatch', data=self.data + b'z')
    def test_no_consent_no_io(self):
        op = Opener(self.data)
        with self.assertRaises(m.Refused): self.run_(consent=False, op=op)
        self.assertEqual(op.calls, 0); self.assertEqual(os.listdir(self.root), [])
    def test_redirects(self):
        h = lambda via, code, url: m.Redirect(via).redirect_request(Request('https://x'), None, code, '', {}, url)
        with self.assertRaises(m.Refused): h('raw', 302, 'https://' + m.RELEASE_HOST + '/a')
        for bad in ('https://evil.invalid/a', 'http://' + m.RELEASE_HOST + '/a'):
            with self.assertRaises(m.Refused): h('release', 302, bad)
        with self.assertRaises(m.Refused): h('release', 301, 'https://' + m.RELEASE_HOST + '/a')
        r = m.Redirect('release'); r.redirect_request(Request('https://x'), None, 302, '', {}, 'https://' + m.RELEASE_HOST + '/a')
        with self.assertRaises(m.Refused): r.redirect_request(Request('https://x'), None, 302, '', {}, 'https://' + m.RELEASE_HOST + '/b')
    def test_url_for(self):
        e = dict(fichero='interface/app.css')
        self.assertEqual(m.url_for(dict(via='raw', ref=SHA), e), f'https://raw.githubusercontent.com/piskyRpapalo/PreceptorOS/{SHA}/interface/app.css')
        self.assertEqual(m.url_for(dict(via='release', ref='v1.3'), e), 'https://github.com/piskyRpapalo/PreceptorOS/releases/download/v1.3/app.css')

if __name__ == '__main__': unittest.main()
