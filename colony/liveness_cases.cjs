const assert = require('node:assert/strict');
const { poll } = require('./liveness.js');
(async () => {
  const nodes = [{ kind: 'node', id: 'a', q: 0, r: 0 }, { kind: 'node', id: 'b', q: 1, r: 0 }];
  const measured = await poll(nodes, async id => id === 'a' ? { id, ok: true, cause: 'poll succeeded' } : { id, ok: false, cause: 'poll failed' });
  assert.deepEqual(measured.visible, [nodes[0]]);
  assert.deepEqual(measured.stamps, [{ id: 'a', seal: 'LIVE', cause: 'poll succeeded' }, { id: 'b', seal: 'STALE', cause: 'poll failed' }]);
  assert.equal((await poll(nodes, async () => { throw new Error('secret'); })).visible.length, 0);
  assert.equal((await poll(nodes, async () => ({ id: 'other', ok: true, cause: 'wrong identity' }))).stamps[0].cause, 'invalid_observation');
  assert.equal((await poll(nodes, async id => ({ id, ok: true, cause: '' }))).visible.length, 0);
  assert.deepEqual(await poll(nodes, async id => ({ id, ok: true, cause: 'ok' })), await poll(nodes, async id => ({ id, ok: true, cause: 'ok' })));
  await assert.rejects(() => poll([nodes[0], nodes[0]], async () => ({})));
  console.log(JSON.stringify(measured));
})().catch(e => { console.error(e); process.exitCode = 1; });
