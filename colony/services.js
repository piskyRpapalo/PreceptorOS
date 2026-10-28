(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory(require('./core.js'), require('./projection.js'));
  } else root.ColonyServices = factory(root.ColonyCore, root.ColonyProjection);
})(globalThis, function (core, projection) {
  'use strict';
  const key = value => typeof value === 'string' && /^[a-z0-9][a-z0-9._-]{0,63}$/.test(value);
  const no = cause => ({ seal: 'NO_DATA', cause });
  const size = value => new TextEncoder().encode(JSON.stringify(value)).length;
  function resolve(rows, services, query) {
    if (!query || !key(query.node) || !key(query.building) || !key(query.service)) return no('query_invalid');
    try { rows = core.state(rows).rows; } catch (_) { return no('state_invalid'); }
    if (!rows.some(row => row.kind === 'node' && row.id === query.node)) return no('node_missing');
    const building = rows.find(row => row.kind === 'building' && row.id === query.building);
    if (!building) return no('building_missing');
    if (building.node !== query.node) return no('building_node_mismatch');
    if (!Array.isArray(services)) return no('catalog_invalid');
    const matches = services.filter(s => s && s.node === query.node && s.building === query.building && s.id === query.service);
    if (!matches.length) return no('service_missing');
    if (matches.length !== 1) return no('service_ambiguous');
    const s = matches[0];
    let sourceSize;
    try { sourceSize = size(s); } catch (_) { return no('source_invalid'); }
    if (!key(s.source) || typeof s.cause !== 'string' || !s.cause.trim() || sourceSize >= 1024 ||
        !['DECLARADO', 'NO_DATA'].includes(s.seal) ||
        (s.seal === 'DECLARADO' && !/^[0-9a-f]{64}$/.test(s.digest)) ||
        (s.seal === 'NO_DATA' && s.digest !== null)) return no('source_invalid');
    if (s.seal === 'NO_DATA') return no(s.cause);
    const screen = projection.project(building.q, building.r);
    if (!Number.isSafeInteger(screen.x) || !Number.isSafeInteger(screen.y)) return no('projection_invalid');
    const result = { seal: s.seal, cause: s.cause, node: query.node, building: query.building,
      service: query.service, source: s.source, digest: s.digest,
      cell: { q: building.q, r: building.r }, screen };
    return size(result) < 1024 ? result : no('route_too_large');
  }
  return { resolve };
});
