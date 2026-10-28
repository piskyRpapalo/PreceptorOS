(function (root, factory) {
  if (typeof module === 'object') module.exports = factory();
  else root.ColonyInhabitant = factory();
})(globalThis, function () {
  'use strict';
  const ring = [[1, 0], [0, 1], [-1, 1], [-1, 0], [0, -1], [1, -1]];
  function position(unit, cycle) {
    if (!unit || unit.kind !== 'unit' || !Number.isSafeInteger(unit.q) ||
        !Number.isSafeInteger(unit.r) || !Number.isSafeInteger(unit.seed) ||
        !Number.isSafeInteger(cycle) || cycle < 0) throw new TypeError('unit or cycle');
    const phase = cycle % 7;
    if (!phase) return { q: unit.q, r: unit.r };
    const start = ((unit.seed % 6) + 6) % 6;
    const step = ring[(start + phase - 1) % 6];
    const q = unit.q + step[0], r = unit.r + step[1];
    if (!Number.isSafeInteger(q) || !Number.isSafeInteger(r)) throw new RangeError('cell');
    return { q, r };
  }
  return { position };
});
