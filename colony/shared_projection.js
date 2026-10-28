(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./projection.js'));
  else root.ColonySharedProjection = factory(root.ColonyProjection);
})(globalThis, function (base) {
  'use strict';
  function project(q, r) {
    const point = base.project(q, r);
    if (!Number.isSafeInteger(point.x) || !Number.isSafeInteger(point.y)) throw new RangeError('projection');
    return point;
  }
  return Object.freeze({ version: 'colony-projection/1', project });
});
