"""Federated view (commission 2026-11-13, Entrega C): the APP reads LAB's node receipts and re-checks them; it never
collects, pings or selects. Fixtures are synthetic and anonymous, built with LAB's own digest rule."""
import datetime as dt
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import federado as F
import hexelion_acciones as A

NOW = dt.datetime(2026, 11, 13, 10, 0, 0, tzinfo=dt.timezone.utc)


def receipts(node="node-b", backend=None, seen=NOW - dt.timedelta(seconds=30), models=2, resident=0, **header):
    """One LAB manifest + its model part, as federated_node_snapshot writes them."""
    rows = [{"model_ref": "%064x" % i, "model_version": "%064x" % (i+1), "state": "VERIFIED"} for i in range(models)]
    head = {"schema": F.SNAPSHOT_SCHEMA, "node": node, "observed_at": seen.isoformat(), "max_age_seconds": 120,
            "host": {"architecture": "x86_64", "cpu_count": 4, "memory_bytes": {"MemTotal": 8, "MemAvailable": 4}},
            "backend_version": {"state": "DECLARED", "value": "0.40.3"}, "catalog_state": "VERIFIED",
            "resident_count": resident, "admission": {"state": "NO_DATA", "cause": "task_resource_envelope_not_calibrated"},
            **header}
    stem = "20261113-federated-%s%s" % (node, "-" + backend if backend else "")
    part = json.dumps(rows).encode()
    manifest = {"schema": F.MANIFEST_SCHEMA, "header": head, "model_count": models,
                "parts": [{"file": stem + "-models-1.json", "count": models, "sha256": hashlib.sha256(part).hexdigest()}],
                "snapshot_ref": F.digest(dict(head, models=rows))}
    return {stem + ".json": json.dumps(manifest).encode(), stem + "-models-1.json": part}


def registry(base, devices):
    d = Path(base) / "federado"
    d.mkdir(exist_ok=True)
    (d / "dispositivos.json").write_text(json.dumps({"schema": F.REGISTRY_SCHEMA, "devices": devices}))


DEVICES = [
    {"id": "node-b", "kind": "rack_node", "node": "node-b", "label": "node-b", "roles": ["APP_CLIENT", "MODEL_SERVER"]},
    {"id": "node-a", "kind": "rack_node", "node": "node-a", "label": "node-a", "roles": ["MODEL_SERVER"]},
    {"id": "mobile-1", "kind": "mobile", "label": "mobile-1", "roles": ["APP_CLIENT", "LOCAL_AI"]},
    {"id": "mobile-3", "kind": "mobile", "label": "mobile-3", "roles": ["ACURAST_EXTERNAL"], "acurast": "core"},
    {"id": "mobile-4", "kind": "mobile", "label": "mobile-4", "roles": ["ACURAST_EXTERNAL"], "acurast": "lite",
     "parked": True},
]


class Integrity(unittest.TestCase):
    def test_fresh_metadata_is_observed_and_an_old_one_stale_by_our_ceiling_not_its_own(self):
        rows = F.backends(receipts(), NOW)
        b = next(r for r in rows if r["node"] == "node-b")
        self.assertEqual((b["state"], b["models_installed"], b["models_resident"]), ("OBSERVED", 2, 0))
        self.assertEqual(b['verification'],{'state':'VERIFIED','scope':'receipt_integrity_only'})
        self.assertEqual(b['inference']['state'],'NO_DATA')
        self.assertEqual(b['expires_at'],(NOW+dt.timedelta(seconds=90)).isoformat())
        old = receipts(seen=NOW - dt.timedelta(hours=1), max_age_seconds=10 ** 9)   # a receipt cannot extend its life
        self.assertEqual(next(r for r in F.backends(old, NOW) if r["node"] == "node-b")["state"], "STALE")

    def test_tampering_is_no_data_with_its_cause(self):
        files = receipts()
        part = "20261113-federated-node-b-models-1.json"
        bad = dict(files, **{part: files[part].replace(b'"VERIFIED"', b'"VERIFIEd"', 1)})
        self.assertEqual(next(r for r in F.backends(bad, NOW) if r["node"] == "node-b")["cause"], "part_hash_mismatch")
        man = json.loads(files["20261113-federated-node-b.json"])
        man["header"]["resident_count"] = 3                       # a header edit breaks the snapshot digest
        bad = dict(files, **{"20261113-federated-node-b.json": json.dumps(man).encode()})
        self.assertEqual(next(r for r in F.backends(bad, NOW) if r["node"] == "node-b")["cause"], "snapshot_integrity")
        bad = {"20261113-federated-node-b.json": files["20261113-federated-node-b.json"]}
        self.assertEqual(next(r for r in F.backends(bad, NOW) if r["node"] == "node-b")["cause"], "part_missing")

    def test_every_rack_node_appears_and_a_silent_one_is_no_data(self):
        rows = F.backends({**receipts(), **receipts("node-c", "primary"), **receipts("node-c", "secondary")}, NOW)
        self.assertEqual({r["node"] for r in rows}, set(F.NODES))
        self.assertEqual([r["backend"] for r in rows if r["node"] == "node-c"], ["primary", "secondary"])
        self.assertEqual(next(r for r in rows if r["node"] == "node-a")["cause"], "no_lab_receipt")

    def test_failed_catalog_does_not_become_a_verified_server(self):
        for value in ('NO_DATA', None, 'STALE'):
            row=next(r for r in F.backends(receipts(catalog_state=value),NOW) if r['node']=='node-b')
            self.assertEqual((row['state'],row['cause']),('NO_DATA','catalog_not_observed'))

    def test_resident_count_cannot_contradict_the_catalog(self):
        row=next(r for r in F.backends(receipts(models=1,resident=2),NOW) if r['node']=='node-b')
        self.assertEqual((row['state'],row['cause']),('NO_DATA','resident_catalog_contradiction'))

    def test_renamed_or_cross_node_receipts_never_change_attribution(self):
        files=receipts();manifest=files.pop('20261113-federated-node-b.json')
        files['20261113-federated-node-c.json']=manifest
        row=next(r for r in F.backends(files,NOW) if r['node']=='node-c')
        self.assertEqual((row['state'],row['cause']),('NO_DATA','part_identity_mismatch'))
        files=receipts(node='node-c');name='20261113-federated-node-c.json'
        doc=json.loads(files[name]);doc['header']['node']='node-b'
        models=json.loads(files[doc['parts'][0]['file']])
        doc['snapshot_ref']=F.digest(dict(doc['header'],models=models));files[name]=json.dumps(doc).encode()
        row=next(r for r in F.backends(files,NOW) if r['node']=='node-c')
        self.assertEqual(row['cause'],'node_identity_mismatch')

    def test_nonfinite_json_duplicate_parts_and_boolean_counts_are_refused(self):
        for raw in (b'{"x":NaN}',b'{"x":1e999}',b'{"x":1,"x":2}'):
            with self.assertRaises(ValueError):F._json(raw)
        files=receipts();name='20261113-federated-node-b.json';doc=json.loads(files[name])
        doc['parts']*=2;doc['model_count']=4
        files[name]=json.dumps(doc).encode()
        self.assertEqual(next(r for r in F.backends(files,NOW) if r['node']=='node-b')['cause'],'part_manifest_invalid')
        doc['model_count']=True;files[name]=json.dumps(doc).encode()
        self.assertEqual(next(r for r in F.backends(files,NOW) if r['node']=='node-b')['cause'],'manifest_schema')

    def test_metadata_claim_cannot_grant_inference_or_admission(self):
        files=receipts(admission={'state':'VERIFIED','allowed':True})
        row=next(r for r in F.backends(files,NOW) if r['node']=='node-b')
        self.assertEqual(row['admission']['state'],'NO_DATA')
        self.assertEqual(row['inference']['state'],'NO_DATA')
        self.assertEqual(row['state'],'OBSERVED')

    def test_invalid_time_or_oversized_manifest_cannot_crash_or_be_fresh(self):
        files=receipts(seen=NOW)
        name='20261113-federated-node-b.json';doc=json.loads(files[name]);doc['header']['observed_at']='invalid'
        models=json.loads(files[doc['parts'][0]['file']]);doc['snapshot_ref']=F.digest(dict(doc['header'],models=models))
        files[name]=json.dumps(doc).encode()
        self.assertEqual(next(r for r in F.backends(files,NOW) if r['node']=='node-b')['state'],'NO_DATA')
        files[name]=b' '*16384
        self.assertEqual(next(r for r in F.backends(files,NOW) if r['node']=='node-b')['cause'],'manifest_invalid_json')
        for stamp in (None, 123, '9999-12-31T23:59:59+00:00'):
            files=receipts(seen=NOW);doc=json.loads(files[name]);doc['header']['observed_at']=stamp
            models=json.loads(files[doc['parts'][0]['file']]);doc['snapshot_ref']=F.digest(dict(doc['header'],models=models))
            files[name]=json.dumps(doc).encode()
            self.assertEqual(next(r for r in F.backends(files,NOW) if r['node']=='node-b')['state'],'NO_DATA')


class Registry(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = self.tmp.name
        resolver=mock.patch('lab_bench.resolve_ref',return_value='a'*40)
        resolver.start();self.addCleanup(resolver.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def test_roles_have_evidence_only_where_a_producer_exists_and_acurast_is_never_a_worker(self):
        registry(self.base, DEVICES)
        view = F.project(receipts(), self.base, NOW)
        dev = {d["id"]: d for d in view["devices"]}
        ev = {e["role"]: e["state"] for e in dev["node-b"]["evidence"]}
        self.assertEqual(ev, {"APP_CLIENT": "DECLARED", "MODEL_SERVER": "OBSERVED"})
        self.assertEqual(dev["node-a"]["evidence"][0]["state"], "NO_DATA")
        self.assertEqual({e["state"] for e in dev["mobile-1"]["evidence"]}, {"DECLARED"})
        self.assertEqual(dev["mobile-3"]["evidence"][0]["cause"], "reserved_to_acurast_not_a_hexelion_worker")
        self.assertEqual(dev["mobile-3"]["coexistence"]["cause"], "acurast_core_operationally_incompatible_do_not_install")
        self.assertEqual(dev["mobile-4"]["coexistence"]["cause"], "needs_bounded_test_and_owner_consent")
        self.assertTrue(dev["mobile-4"]["parked"])

    def test_the_shipped_example_is_a_valid_anonymous_registry_of_ten(self):
        example = json.loads((Path(__file__).resolve().parent / "federado_dispositivos.example.json").read_text())
        registry(self.base, example["devices"])
        devices, cause = F.registry(self.base)
        self.assertIsNone(cause)
        self.assertEqual((len(devices), sum(d["kind"] == "rack_node" for d in devices)), (10, 5))
        self.assertTrue(all(d["label"] == d["id"] for d in devices))       # no real names in the repository

    def test_a_bad_registry_is_refused_whole(self):
        self.assertEqual(F.registry(self.base), ([], "registry_missing"))
        registry(self.base, DEVICES + [{"id": "x", "kind": "mobile", "label": "x", "roles": ["ROOT"]}])
        self.assertEqual(F.registry(self.base), ([], "registry_device_invalid"))
        registry(self.base, [{"id": "n", "kind": "rack_node", "node": "node-z", "label": "n", "roles": []}])
        self.assertEqual(F.registry(self.base), ([], "registry_node_invalid"))


class Talk(Registry):
    def lee(self, tool, files):
        with mock.patch("lab_bench.from_git", return_value=list(files.items())):
            return A.lee_local(tool, self.base, NOW)

    def test_phrases_name_the_two_reads_and_they_take_no_arguments(self):
        self.assertEqual(A.frase("¿Qué dispositivos están conectados?"), "/dispositivos")
        self.assertEqual(A.frase("What models do we have?"), "/modelos")
        self.assertEqual(A.interpreta("/devices x"), (None, "action_takes_no_arguments"))

    def test_devices_says_declared_is_not_connected_and_names_acurast_reserves(self):
        registry(self.base, DEVICES)
        acc = self.lee("devices", receipts())
        self.assertTrue(acc["ok"])
        self.assertIn("Model servers (LAB): node-b metadata observed; inference untested; node-a no evidence (no lab receipt).", acc["texto"])
        self.assertIn("Declared only, not pinged: mobile-1.", acc["texto"])
        self.assertIn("Reserved to Acurast, never Hexelion workers: mobile-3, mobile-4 (parked).", acc["texto"])

    def test_models_says_installed_is_not_available_and_no_lab_evidence_is_no_data(self):
        acc = self.lee("models", receipts(models=3, resident=1))
        self.assertIn("node-b 3/1, metadata observed now.", acc["texto"])
        self.assertIn("No evidence: node-a (no lab receipt);", acc["texto"])
        self.assertIn("Installed is not available; no inference was run.", acc["texto"])
        acc = self.lee("models", {"20261112-bench.json": b"{}"})
        self.assertEqual((acc["ok"], acc["causa"]), (False, "lab_federated_not_on_ref"))
        acc = self.lee("models", {})
        self.assertEqual(acc["causa"], "lab_clone_or_ref_missing")

    def test_ten_real_sized_devices_and_six_backends_fit_the_chat_envelope(self):
        import estado_compacto
        registry(self.base, [dict(d, id="dev-%d" % i, label="A long device name %d" % i)
                             for i, d in enumerate(DEVICES * 2)])
        files = {**receipts(), **receipts("node-c", "primary"), **receipts("node-c", "secondary"),
                 **receipts("node-d"), **receipts("node-e")}
        for tool in ("devices", "models"):
            acc = self.lee(tool, files)
            estado_compacto.serializar_objeto({"causa": "lectura_local;model_not_invoked", "estado": "ACCION_LOCAL",
                                               "respuesta": {"tipo": "accion_hexelion", "accion": acc}})

    def test_the_machine_form_is_a_read_only_route_not_the_chat(self):
        import io
        from types import SimpleNamespace
        from test_pwa import PWA
        registry(self.base, DEVICES)
        h = PWA.PWA.__new__(PWA.PWA)
        h.path, h.headers, h.client_address = "/api/federado", {}, ("127.0.0.1", 1)
        out = {}
        h._json = lambda code, body: out.update(code=code, body=body)
        h.server, h.wfile = SimpleNamespace(server_port=8742), io.BytesIO()
        with mock.patch.object(PWA._casa, "raiz", return_value=Path(self.base)), \
                mock.patch("lab_bench.from_git", return_value=list(receipts().items())):
            h.do_GET()
        self.assertEqual((out["code"], out["body"]["schema"]), (200, F.SCHEMA))
        self.assertEqual(len(out["body"]["devices"]), len(DEVICES))

    def test_without_a_registry_devices_is_no_data(self):
        acc = self.lee("devices", receipts())
        self.assertEqual((acc["ok"], acc["causa"]), (False, "registry_missing"))

    def test_the_app_never_fetches_lab_it_reads_a_local_ref(self):
        with mock.patch("lab_bench.from_git", return_value=[]) as g, \
                mock.patch.dict(os.environ, {"PRECEPTOROS_LAB_REPO": "/r", "PRECEPTOROS_LAB_REF": "origin/main"}):
            F.from_lab(self.base)
        g.assert_called_once_with("/r", "a"*40)


if __name__ == "__main__":
    unittest.main()
