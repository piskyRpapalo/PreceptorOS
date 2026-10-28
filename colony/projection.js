(function (root, factory) {
  if (typeof module === 'object') module.exports = factory();
  else root.ColonyProjection = factory();
})(globalThis, function () {
  'use strict';
  function project(q, r) {
    if (!Number.isSafeInteger(q) || !Number.isSafeInteger(r)) throw new TypeError('cell');
    return { x: 48 * q + 24 * r, y: 12 * r };
  }
  return { project };
});
