(function (root, factory) {
  if (typeof module === 'object') module.exports = factory();
  else root.ColonyAuthoring = factory();
})(globalThis, function () {
  'use strict';
  function draft(nodes, links) {
    if (!Array.isArray(nodes) || !Array.isArray(links)) throw new TypeError('draft');
    const ids = new Set(), cells = new Set();
    const rows = nodes.map(n => {
      if (!n || typeof n.id !== 'string' || !n.id || ids.has(n.id) ||
          !Number.isSafeInteger(n.q) || !Number.isSafeInteger(n.r)) throw new TypeError('node');
      const cell = n.q + ',' + n.r;
      if (cells.has(cell)) throw new TypeError('cell');
      ids.add(n.id); cells.add(cell);
      return { kind: 'node', id: n.id, q: n.q, r: n.r };
    });
    const seen = new Set();
    const edges = links.map(pair => {
      if (!Array.isArray(pair) || pair.length !== 2 || !ids.has(pair[0]) ||
          !ids.has(pair[1]) || pair[0] === pair[1]) throw new TypeError('link');
      const edge = pair.slice().sort(), key = JSON.stringify(edge);
      if (seen.has(key)) throw new TypeError('duplicate link');
      seen.add(key); return edge;
    });
    const result = { version: 'colony-draft/1', rows, links: edges };
    if (new TextEncoder().encode(JSON.stringify(result)).length >= 1024) throw new RangeError('size');
    return result;
  }
  function stamp(id, observation) {
    if (typeof id !== 'string' || !id || !observation ||
        typeof observation.ok !== 'boolean' || typeof observation.cause !== 'string' ||
        !observation.cause.trim()) throw new TypeError('observation');
    return { id, seal: observation.ok ? 'LIVE' : 'STALE', cause: observation.cause };
  }
  return { draft, stamp };
});
