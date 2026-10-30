(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory(require('./core.js'), require('./projection.js'));
  } else root.ColonyBuildings = factory(root.ColonyCore, root.ColonyProjection);
})(globalThis, function (core, projection) {
  'use strict';
  const CAJA = [120, 110], BASE = [60, 84], PASOS = 6;
  const MODULOS = ['vermilion.base', 'comic yellow.base', 'ocean', 'cyan', 'paper', 'ink'];
  const FORMAS = ['dome', 'tower', 'block'];
  const fallo = causa => { throw new Error('colony_buildings: ' + causa); };
  function hash(texto) {
    let h = 0x811c9dc5;
    for (let i = 0; i < texto.length; i++) h = Math.imul(h ^ texto.charCodeAt(i), 0x01000193) >>> 0;
    return h >>> 0;
  }
  function colorDe(id) { return MODULOS[hash('module:' + id) % MODULOS.length]; }
  function formaDe(id) { return FORMAS[hash('building:' + id) % FORMAS.length]; }
  function hexagono() {
    const pts = [];
    for (let i = 0; i < 6; i++) {
      const p = [Math.round(BASE[0] + 50 * Math.cos(i * Math.PI / 3)), Math.round(BASE[1] + 24 * Math.sin(i * Math.PI / 3))];
      pts.push(p, p);
    }
    return pts;
  }
  function contorno(forma) {
    let pts = [];
    if (forma === 'dome') {
      for (let a = Math.PI; a >= 0; a -= Math.PI / 8) pts.push([Math.round(BASE[0] + 22 * Math.cos(a)), Math.round(BASE[1] - 6 - 22 * Math.sin(a))]);
      pts.push([BASE[0] + 22, BASE[1] - 6], [BASE[0] - 22, BASE[1] - 6]);
    } else if (forma === 'tower') {
      pts = [[BASE[0] - 12, BASE[1] - 6], [BASE[0] + 12, BASE[1] - 6], [BASE[0] + 12, BASE[1] - 46], [BASE[0] - 12, BASE[1] - 46]];
    } else {
      pts = [[BASE[0] - 20, BASE[1] - 26], [BASE[0], BASE[1] - 36], [BASE[0] + 20, BASE[1] - 26],
        [BASE[0] + 20, BASE[1] - 6], [BASE[0], BASE[1] + 4], [BASE[0] - 20, BASE[1] - 6]];
    }
    return pts.reduce((out, p) => (out.push(p, p), out), []);
  }
  function crece(pts, progreso) {
    return pts.map(p => [Math.round(BASE[0] + (p[0] - BASE[0]) * progreso), Math.round(BASE[1] + (p[1] - BASE[1]) * progreso)]);
  }
  function bytes(marco) { return new TextEncoder().encode(JSON.stringify(marco)).length; }
  function marcoModulo(nodo) {
    const color = colorDe(nodo.id), frase = 'module ' + nodo.id + ' · colour ' + color;
    return { v: 'preceptoros.bubble/1', id: nodo.id, t: 0, cv: CAJA,
      atoms: [{ k: 'module.' + nodo.id, r: frase, i: [{ o: 'ribbon', pts: hexagono(), closed: true, f: color, s: 'ink', lw: 2 }] }],
      bands: ['paper', 'ink', 'cyan'], change: [frase],
      sound: 'NO_DATA: modules declare no waves; nothing is invented', soundCause: 'a module has no measured value in this slice' };
  }
  function marcoEdificio(edificio, progreso, paso, sello) {
    const forma = formaDe(edificio.id), frase = 'building ' + edificio.id + ' on ' + edificio.node + ' · ' + forma + ' · growth ' + paso + '/' + PASOS + ' · seal ' + sello;
    return { v: 'preceptoros.bubble/1', id: edificio.id, t: paso, cv: CAJA, seal: sello,
      atoms: [{ k: 'building.' + forma, r: frase, i: [{ o: 'ribbon', pts: crece(contorno(forma), progreso), closed: true, f: 'paper', s: 'ink', lw: 2 }] }],
      bands: ['paper', 'ink', 'cyan'], change: [frase],
      sound: 'NO_DATA: buildings declare no waves; nothing is invented', soundCause: 'a building has no measured value in this slice' };
  }
  function escena(rows, sellos, progreso, movimientoReducido) {
    const state = core.state(rows), nodos = state.rows.filter(r => r.kind === 'node'), edificios = state.rows.filter(r => r.kind === 'building');
    const porId = new Map(nodos.map(n => [n.id, n]));
    edificios.forEach(b => { if (!porId.has(b.node)) fallo('building_node_mismatch: ' + b.id); });
    const vivos = nodos.filter(n => sellos && sellos[n.id] === 'LIVE');
    const visibles = new Set(vivos.map(n => n.id));
    const g = movimientoReducido === true ? 1 : Math.max(0, Math.min(1, Number.isFinite(progreso) ? progreso : 1));
    const paso = Math.max(1, Math.min(PASOS, Math.ceil(g * PASOS)));
    const tiles = vivos.map(n => {
      const p = projection.project(n.q, n.r), frame = marcoModulo(n);
      if (bytes(frame) >= 1024) fallo('module frame limit');
      return { id: n.id, q: n.q, r: n.r, x: p.x, y: p.y, color: colorDe(n.id), frame };
    });
    const construcciones = edificios.filter(b => visibles.has(b.node)).map(b => {
      const p = projection.project(b.q, b.r), frame = marcoEdificio(b, g, paso, 'LIVE');
      if (bytes(frame) >= 1024) fallo('building frame limit');
      return { id: b.id, node: b.node, q: b.q, r: b.r, forma: formaDe(b.id), x: p.x, y: p.y, paso, frame };
    }).sort((a, b) => a.y - b.y || a.x - b.x || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
    return { tiles, buildings: construcciones, progress: g, step: paso, steps: PASOS,
      availability: construcciones.length ? { seal: 'LIVE', cause: '' } :
        { seal: 'NO_DATA', cause: vivos.length ? 'no building row is authored for a LIVE node' : 'no LIVE node is supplied by the app poll' } };
  }
  return { PASOS, MODULOS, FORMAS, hash, colorDe, formaDe, escena, marcoModulo, marcoEdificio, bytes };
});
