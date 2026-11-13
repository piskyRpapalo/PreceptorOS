"""Regenerate tests/fixtures/p2_mirror_packets.json with LAB's own P2 mirror producer (read-only, synthetic only).

Run from a LAB checkout at the pinned commit, never against a host journal:
    python3 tests/fixtures/gen_p2_mirror_packets.py <lab checkout> tests/fixtures/p2_mirror_packets.json
It builds temporary synthetic journals with LAB's test fixture and a synthetic local-source witness; the packets carry
no paths. The provenance block records the LAB commit and the sha256 of each producer file it ran.
"""
import hashlib, json, os, sys, tempfile
from pathlib import Path
LAB = Path(sys.argv[1]).resolve(); OUT = Path(sys.argv[2])
sys.path.insert(0, str(LAB)); os.chdir(LAB)
from meta_harness.readonly_mirror import ReadOnlyMirror
from meta_harness.delegation import sha
from tests.test_meta_delegation import STAMP, task
import tests.test_human_uncertainty as synthetic

cases = {}
def fixture():
    f = synthetic.HumanUncertainty(); f.setUp(); return f
f = fixture(); good = {'owned': {'journal': str(f.path), 'task': task()}}
yes = lambda _: True
cases['unknown_hitl_required'] = ReadOnlyMirror(good, local_source_witness=yes).read('owned', observed_at=STAMP)
cases['local_source_not_attested'] = ReadOnlyMirror(good).read('owned', observed_at=STAMP)
cases['source_not_allowlisted'] = ReadOnlyMirror(good, local_source_witness=yes).read('other', observed_at=STAMP)
cases['host_clock_invalid'] = ReadOnlyMirror(good, local_source_witness=yes).read('owned', observed_at='invalid')
p = f.proposal(); f.accepted.add(p['resolution_ref']); f.acknowledge(p)
cases['synthetic_ack_not_verified'] = ReadOnlyMirror(good, local_source_witness=yes).read('owned', observed_at=STAMP)
Path(str(f.path) + '-wal').write_bytes(b'fixture')
cases['source_busy_wal'] = ReadOnlyMirror(good, local_source_witness=yes).read('owned', observed_at=STAMP)
f.doCleanups()
d = Path(tempfile.mkdtemp())
missing = {'owned': {'journal': str(d / 'absent.sqlite3'), 'task': task()}}
cases['journal_absent'] = ReadOnlyMirror(missing, local_source_witness=yes).read('owned', observed_at=STAMP)
(d / 'corrupt.sqlite3').write_bytes(b'not a sqlite database' * 8)
corrupt = {'owned': {'journal': str(d / 'corrupt.sqlite3'), 'task': task()}}
cases['journal_corrupt'] = ReadOnlyMirror(corrupt, local_source_witness=yes).read('owned', observed_at=STAMP)

src = {n: hashlib.sha256((LAB / 'meta_harness' / n).read_bytes()).hexdigest()
       for n in ('readonly_mirror.py', 'uncertainty_views.py', 'execution_journal.py', 'host_witness.py', 'delegation.py')}
t = task()
OUT.write_text(json.dumps({'provenance': {'lab_commit': os.popen('git rev-parse HEAD').read().strip(),
    'producer': 'meta_harness.readonly_mirror.ReadOnlyMirror.read', 'witness': 'SYNTHETIC (tests fixture)',
    'source_sha256': src, 'stamp': STAMP},
    'task': {'run_id': t['run_id'], 'task_sha256': sha(t)}, 'packets': cases},
    ensure_ascii=False, sort_keys=True, indent=1) + '\n')
for n, c in cases.items():
    r = c['machine']['record']; print(n, r['state'], r['acknowledgement'], r['cause'], r['task_ref'] and r['task_ref'][:8], len(json.dumps(r, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()))
