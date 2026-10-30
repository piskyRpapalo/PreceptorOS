const assert = require('node:assert/strict');
const fs = require('node:fs');
const B = require('./buildings.js');

// Snapshot fixture from web main: cabin is LIVE; the other declared rows are NO_DATA.
const rows = [
  { kind: 'node', id: 'cabin', q: -1, r: 0 },
  { kind: 'node', id: 'node-a', q: 0, r: 0 },
  { kind: 'node', id: 'node-b', q: 2, r: 0 },
  { kind: 'node', id: 'node-c', q: 2, r: -1 },
  { kind: 'building', id: 'b-cabin', node: 'cabin', q: -1, r: 0 },
  { kind: 'building', id: 'b-node-b', node: 'node-b', q: 2, r: 0 },
  { kind: 'building', id: 'b-node-c', node: 'node-c', q: 2, r: -1 }
];
const seals = { cabin: 'LIVE', 'node-a': 'NO_DATA', 'node-b': 'NO_DATA', 'node-c': 'NO_DATA' };
const scene = B.escena(rows, seals, 1 / 6, false);
assert.deepEqual(scene.tiles.map(x => x.id), ['cabin']);
assert.deepEqual(scene.buildings.map(x => x.id), ['b-cabin']);
assert.equal(scene.availability.seal, 'LIVE');
assert.equal(scene.buildings[0].forma, B.formaDe('b-cabin'));
assert.equal(scene.buildings[0].paso, 1);
assert.ok(B.bytes(scene.buildings[0].frame) < 1024);
assert.deepEqual(scene.buildings[0].frame.atoms[0].i[0].pts, B.marcoEdificio(rows[4], 1 / 6, 1, 'LIVE').atoms[0].i[0].pts);
assert.equal(JSON.stringify(B.escena(rows, seals, 1 / 6, false)), JSON.stringify(scene));

const sinVivos = B.escena(rows, {}, 1, false);
assert.equal(sinVivos.buildings.length, 0);
assert.equal(sinVivos.availability.seal, 'NO_DATA');
assert.match(sinVivos.availability.cause, /no LIVE node/);
const sinEdificio = B.escena(rows.filter(r => r.kind !== 'building'), seals, 1, false);
assert.equal(sinEdificio.buildings.length, 0);
assert.equal(sinEdificio.availability.cause, 'no building row is authored for a LIVE node');
assert.equal(B.escena(rows, seals, 0, true).buildings[0].paso, 6);
assert.throws(() => B.escena(rows.filter(r => r.id !== 'cabin'), seals, 1, false), /building_node_mismatch/);

const source = fs.readFileSync(__dirname + '/buildings.js', 'utf8');
assert.doesNotMatch(source, /Math\.random|Date\.now|new Date|performance\.now|fetch\(|XMLHttpRequest/);
console.log(JSON.stringify({ tiles: scene.tiles.length, buildings: scene.buildings.length,
  form: scene.buildings[0].forma, step: scene.step, cause: sinVivos.availability.cause }));
