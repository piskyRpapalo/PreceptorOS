(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./core.js'));
  else root.ColonyLiveness = factory(root.ColonyCore);
})(globalThis, function (core) {
  'use strict';
  async function poll(nodes, observe) {
    const rows = core.state(nodes).rows;
    if (rows.some(row => row.kind !== 'node') || typeof observe !== 'function') throw new TypeError('poll input');
    const stamps = await Promise.all(rows.map(async row => {
      let result;
      try { result = await observe(row.id); } catch (_) { return { id: row.id, seal: 'STALE', cause: 'poll_failed' }; }
      if (!result || result.id !== row.id || typeof result.ok !== 'boolean' ||
          typeof result.cause !== 'string' || !/^[a-z0-9 _-]{1,80}$/i.test(result.cause) || !result.cause.trim()) {
        return { id: row.id, seal: 'STALE', cause: 'invalid_observation' };
      }
      return { id: row.id, seal: result.ok ? 'LIVE' : 'STALE', cause: result.cause };
    }));
    return { stamps, visible: rows.filter((_, index) => stamps[index].seal === 'LIVE') };
  }
  return { poll };
});
