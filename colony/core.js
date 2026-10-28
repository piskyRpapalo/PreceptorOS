(function (root, factory) {
  if (typeof module === 'object') module.exports = factory();
  else root.ColonyCore = factory();
})(globalThis, function () {
  'use strict';
  function state(rows) {
    const ids = new Set(), cells = new Set();
    const copy = rows.map(row => {
      if (!row || !['node', 'building', 'unit'].includes(row.kind) ||
          typeof row.id !== 'string' || !row.id || ids.has(row.id) ||
          !Number.isSafeInteger(row.q) || !Number.isSafeInteger(row.r)) throw new TypeError('row');
      ids.add(row.id);
      const cell = row.q + ',' + row.r;
      if (row.kind === 'node' && cells.has(cell)) throw new TypeError('cell');
      if (row.kind === 'node') cells.add(cell);
      return JSON.parse(JSON.stringify(row));
    });
    const value = { version: 'colony/1', rows: copy };
    if (new TextEncoder().encode(JSON.stringify(value)).length >= 1024) throw new RangeError('size');
    return value;
  }
  return { state };
});
