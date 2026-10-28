const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const { state } = require('./core.js');
const { project } = require('./projection.js');
const rows = [
  { kind: 'node', id: 'base', q: -1, r: 0, resource: { name: 'mana', seal: 'NO_DATA', cause: 'No measurement supplied' } },
  { kind: 'node', id: 'principal', q: 0, r: 0 },
  { kind: 'node', id: 'risen', q: 1, r: 0 },
  { kind: 'building', id: 'b', q: 0, r: 0 },
  { kind: 'unit', id: 'u', q: 0, r: 1 }
];
const first = state(rows);
assert.ok(Buffer.byteLength(JSON.stringify(first)) < 1024);
rows[0].q = 99;
assert.equal(first.rows[0].q, -1);
assert.deepEqual(project(1, 1), { x: 72, y: 12 });
assert.throws(() => state([{ kind: 'node', id: 'x', q: 0, r: 0 }, { kind: 'node', id: 'x', q: 1, r: 0 }]));
assert.throws(() => state([{ kind: 'node', id: 'x', q: 0, r: 0 }, { kind: 'node', id: 'y', q: 0, r: 0 }]));
assert.throws(() => state([{ kind: 'unit', id: 'x'.repeat(1024), q: 0, r: 0 }]));
assert.throws(() => project(0.5, 0));
function bitmap(value) {
  const pixels = Buffer.alloc(256 * 64);
  for (const row of value.rows.filter(r => r.kind === 'node')) {
    const p = project(row.q, row.r), x = 128 + p.x, y = 32 + p.y;
    if (x >= 0 && x < 256 && y >= 0 && y < 64) pixels[y * 256 + x] = 255;
  }
  return pixels;
}
const hash = b => createHash('sha256').update(b).digest('hex');
const a = bitmap(first), b = bitmap(state(first.rows));
assert.deepEqual(a, b);
const changed = Buffer.from(b); changed[0] ^= 1;
assert.notEqual(hash(a), hash(changed));
console.log('IC1/IC2 cases: 9 checks; bitmap sha256 ' + hash(a));
