const assert = require('node:assert/strict');
const { project, version } = require('./shared_projection.js');
assert.equal(version, 'colony-projection/1');
const vectors = [[0, 0, 0, 0], [1, 0, 48, 0], [0, 1, 24, 12], [-2, 1, -72, 12], [2, -1, 72, -12]];
for (const [q, r, x, y] of vectors) assert.deepEqual(project(q, r), { x, y });
assert.throws(() => project(0.5, 0));
assert.throws(() => project(Number.MAX_SAFE_INTEGER, 0));
assert.throws(() => project(0, Infinity));
console.log(JSON.stringify(vectors.map(([q, r]) => project(q, r))));
