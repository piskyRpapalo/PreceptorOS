(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./inhabitant.js'), require('./shared_projection.js'));
  else root.ColonyWalkingFrames = factory(root.ColonyInhabitant, root.ColonySharedProjection);
})(globalThis, function (routes, projection) {
  'use strict';
  function frame(unit, cycle, style) {
    if (!['tutorial', 'atlantis', 'risen'].includes(style) || typeof unit.id !== 'string' || !/^[a-z0-9-]{1,32}$/.test(unit.id)) throw new TypeError('fixture');
    const cell = routes.position(unit, cycle), point = projection.project(cell.q, cell.r);
    const phrase = unit.id + ' at ' + cell.q + ',' + cell.r;
    const result = { v: 'preceptoros.bubble/1', id: unit.id, t: cycle, style,
      atoms: [{ k: 'unit', r: phrase, i: [{ o: 'wave', x: point.x, y: point.y, h: [[1, 8, 8, 0]] }] }],
      bands: ['paper', 'ink'], change: [phrase], sound: 'NO_DATA: fixture has no sound synthesis' };
    if (new TextEncoder().encode(JSON.stringify(result)).length >= 1024) throw new RangeError('frame');
    return result;
  }
  return { frame };
});
