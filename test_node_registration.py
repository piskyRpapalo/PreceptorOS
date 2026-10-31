import importlib.util
from importlib.machinery import SourceFileLoader
import json
import os
from pathlib import Path
import subprocess
from http.server import ThreadingHTTPServer
import threading
import unittest
from types import SimpleNamespace

import node_registration as NR
import version

ROOT = Path(__file__).resolve().parent
PWA_PATH = ROOT / "bin" / "preceptoros-pwa"
SPEC = importlib.util.spec_from_loader(
    "node_registration_pwa", SourceFileLoader("node_registration_pwa", str(PWA_PATH)))
PWA = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PWA)


def envelope(node="nodo.7.demo"):
    return {"mode": "test_stub_only", "request": {
        "schema": NR.SCHEMA, "node": node,
        "cedula_sha256": "a" * 64,
        "signer": {"state": "stub", "label": "test_only_no_signature"}}}


class Handler:
    def __init__(self, data, client="127.0.0.1"):
        body = json.dumps(data).encode()
        self.path = "/api/nodo/door1/preview"
        self.headers = {"Content-Length": str(len(body))}
        self.rfile = __import__("io").BytesIO(body)
        self.client_address = (client, 12345)
        self.server = SimpleNamespace(server_address=("127.0.0.1", 8740))
        self.code = None

    def _json(self, code, body):
        self.code, self.body = code, body

    _leer = PWA.PWA._leer
    _es_loopback = staticmethod(PWA.PWA._es_loopback)
    _despachar_post = PWA.PWA._despachar_post
    _nodo_door1_preview = PWA.PWA._nodo_door1_preview


class NodeRegistration(unittest.TestCase):
    def test_receiver_counts_only_in_a_nonpersistent_test_catalog(self):
        code, result = NR.receive_preview(envelope())
        self.assertEqual(code, 200)
        self.assertEqual(result["state"], "received")
        self.assertEqual(result["catalog"], {"state": "stub_not_published", "count": 1})
        self.assertFalse(result["persisted"])

    def test_no_real_signer_publication_or_malformed_request_is_accepted(self):
        for data, expected in (
            ({"mode": "production", "request": envelope()["request"]}, "dry_run_only"),
            ({"mode": "test_stub_only", "request": {
                "schema": NR.SCHEMA, "node": "nodo.7.demo", "cedula_sha256": "a" * 64,
                "signer": {"state": "signed"}}},
             "real_signer_not_implemented"),
            (envelope("bad"), "invalid_request"),
        ):
            with self.subTest(expected=expected):
                _code, result = NR.receive_preview(data)
                self.assertEqual(result["cause"], expected)

    def test_request_size_is_bounded(self):
        data = envelope()
        data["request"]["node"] = "nodo.7." + "a" * 1024
        self.assertEqual(NR.receive_preview(data)[0], 413)

    def test_server_route_is_loopback_only_and_does_not_persist(self):
        local = Handler(envelope())
        PWA.PWA._despachar_post(local)
        self.assertEqual(local.code, 200)
        self.assertFalse(local.body["persisted"])
        remote = Handler(envelope(), "192.0.2.1")
        PWA.PWA._despachar_post(remote)
        self.assertEqual(remote.code, 403)

    def test_http_body_size_limit_is_applied_before_the_stub_receiver(self):
        large = Handler(envelope())
        large.headers["Content-Length"] = str(NR.MAX_BYTES + 1)
        PWA.PWA._despachar_post(large)
        self.assertEqual(large.code, 413)
        self.assertEqual(large.body["cause"], "request_too_large")

    def test_phone_state_machine_and_door_one_adapter_with_explicit_stubs(self):
        script = r"""
const assert = require('node:assert/strict');
const flow = require('./interface/node_registration.js');
let received = 0;
const adapter = flow.doorOneAdapter((url, options) => {
  assert.equal(url, 'https://api.preceptoros.org/api/v1/cedulas');
  const outgoing = JSON.parse(options.body);
  const cedula = outgoing.cedula;
  assert.equal(cedula.esquema, 'preceptoros.cedula-nodo/1');
  assert.equal(cedula.firma, null);
  assert.equal(cedula.firma_ssh, null);
  assert.match(cedula.sha256, /^[0-9a-f]{64}$/);
  assert.ok(Buffer.byteLength(JSON.stringify(cedula), 'utf8') < 1024);
  received++;
  const stub = { mode: 'test_stub_only', request: { schema: 'preceptoros.node-registration-request/1',
    node: cedula.nodo, cedula_sha256: cedula.sha256,
    signer: { state: 'stub', label: 'test_only_no_signature' } } };
  return fetch(new URL('/api/nodo/door1/preview', process.env.PRECEPTOROS_NODE_TEST_URL), {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(stub)
  });
});
(async () => {
  const pendingSlot = await flow.pendingSigner();
  assert.equal(pendingSlot.state, 'pending');
  assert.equal(pendingSlot.cause, 'signature_missing');
  const draft = await flow.createRequest('nodo.7.demo');
  await assert.rejects(() => adapter.submitPending(draft, false), /explicit_consent_required/);
  assert.equal(received, 0);
  const pendingAdapter = flow.doorOneAdapter(async (url, options) => {
    assert.equal(url, flow.doorOneUrl);
    assert.equal(JSON.parse(options.body).cedula.firma, null);
    return { ok: true, status: 202, json: async () => ({ state: 'pending', trust: 'untrusted',
      cause: 'signature_missing', receipt_id: 'receipt-stub', cedula_sha256: draft.sha256 }) };
  });
  const pendingReceipt = await pendingAdapter.submitPending(draft, true);
  assert.equal(pendingReceipt.state, 'pending');
  assert.equal(pendingReceipt.trust, 'untrusted');
  assert.equal(pendingReceipt.cause, 'signature_missing');
  const brokenReceiptAdapter = flow.doorOneAdapter(async () => ({ ok: true, status: 200,
    json: async () => ({ state: 'pending', trust: 'untrusted', cause: 'signature_missing',
      receipt_id: 'receipt-stub', cedula_sha256: '0'.repeat(64) }) }));
  await assert.rejects(() => brokenReceiptAdapter.submitPending(draft, true), /receipt_unverified/);
  const tampered = Object.assign({}, draft, { nodo: 'nodo.8.demo' });
  await assert.rejects(() => adapter.submitPending(tampered, true), /cedula_hash_mismatch/);
  const dry = await flow.runDryRun('nodo.7.demo', flow.testStubSigner, adapter);
  assert.equal(dry.state, flow.states.catalogStub);
  assert.deepEqual(dry.transitions, ['draft', 'preview', 'consented', 'submitting', 'catalog_stub']);
  assert.equal(dry.receipt.catalog.state, 'stub_not_published');
  assert.equal(dry.receipt.catalog.count, 1);
  assert.equal(dry.receipt.persisted, false);
  assert.equal(dry.cedula.firma, null);
  assert.equal(dry.cedula.firma_ssh, null);
  assert.equal(dry.signer.label, 'test_stub_no_signature');
  assert.equal(received, 1);
})().catch(e => { console.error(e); process.exit(1); });
"""
        class QuietPWA(PWA.PWA):
            def log_message(self, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), QuietPWA)
        server.daemon_threads = True
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        env = os.environ.copy()
        env["PRECEPTOROS_NODE_TEST_URL"] = "http://127.0.0.1:%d" % server.server_address[1]
        try:
            subprocess.run(["node", "-e", script], cwd=ROOT, check=True,
                           capture_output=True, text=True, env=env)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_ui_and_transport_are_explicitly_stubbed(self):
        html = (ROOT / "interface" / "app.html").read_text(encoding="utf-8")
        js = (ROOT / "interface" / "node_registration.js").read_text(encoding="utf-8")
        self.assertIn('id="node-registration-form"', html)
        self.assertIn('id="node-registration-consent"', html)
        self.assertIn('id="node-registration-submit"', html)
        self.assertIn("test_stub_no_signature", js)
        self.assertIn("https://api.preceptoros.org/api/v1/cedulas", js)
        self.assertNotIn("/aduana/cedulas", js)
        self.assertNotIn("/api/v1/paquetes", js)

    def test_browser_cedula_hash_matches_the_existing_app_validator(self):
        script = "const f=require('./interface/node_registration.js'); f.createRequest('nodo.7.demo').then(c=>console.log(JSON.stringify(c))).catch(e=>{console.error(e);process.exit(1)})"
        result = subprocess.run(["node", "-e", script], cwd=ROOT, check=True,
                                capture_output=True, text=True)
        cedula = json.loads(result.stdout)
        import nodo_app
        self.assertIsNone(nodo_app._forma(cedula))
        self.assertIsNone(cedula["firma"])
        self.assertIsNone(cedula["firma_ssh"])
        self.assertEqual(cedula["autenticidad"], "NO_DATA")

    def test_pwa_route_service_worker_and_version_cover_the_new_asset(self):
        sw = (ROOT / "interface" / "sw.js").read_text(encoding="utf-8")
        html = (ROOT / "interface" / "app.html").read_text(encoding="utf-8")
        self.assertIn('"/node_registration.js": ("node_registration.js"', PWA_PATH.read_text())
        self.assertIn('/node_registration.js?v=1', html)
        self.assertIn('"/node_registration.js?v=1"', sw)
        self.assertIn('preceptoros-armazon-v120', sw)
        self.assertIn("interface/node_registration.js", version.ARMAZON)
        self.assertIn('"/node_building.js": ("node_building.js"', PWA_PATH.read_text())
        self.assertIn('/node_building.js?v=1', html)
        self.assertIn('"/node_building.js?v=1"', sw)
        self.assertIn("interface/node_building.js", version.ARMAZON)


if __name__ == "__main__":
    unittest.main()
