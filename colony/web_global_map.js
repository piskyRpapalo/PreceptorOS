// Global map · the first three nodes (ODD isometric-colony, mandate 2026-10-28 evening).
// One state, many renders (D4/D5): this pure core turns the liveness rows into bubble-language frames.
// A node appears only while it is alive; the tutorial cabin is always here. Every visible change is a frame of
// under 1,024 UTF-8 bytes whose sound comes from the frame's own waves. The day/night palette is a function of the
// cycle tick `t` alone: never a wall clock. No random numbers, no clock reads, no network.
(function (root) {
  'use strict';
  var common = typeof module === 'object' && module.exports;
  var Iso = common ? require('./isometric_floor_projection.js') : root.IsometricFloor;

  var LIMITE_BYTES = 1024;     // a frame is a syllable (docs/bubble-language.md §1)
  var ANCHO = 320, ALTO = 96;  // the box one node's bubble is drawn in
  var CELDA = 56;              // fixed axonometric cell width: the angle never changes
  var CYCLE = 240;             // ticks in one full day and night
  var ESCALA = 1.5;            // the scene's spacing, in reference units (480 x 240)
  var BURBUJA = 0.6;           // one bubble's scale in the reference units: the same in the door and in the check page
  var RECURSO = 'resource.mana';

  // Lexicon keys: a visible node without one is an orphan_visual_node, and it is refused.
  // The three nodes are the first three named in the mandate; their names are English, never an iron brand.
  var NODES = [
    { id: 'cabin',    clave: 'node.cabin',    nombre: 'Tutorial cabin',          reco: [0, 0],  siempre: true },
    { id: 'atlantis', clave: 'node.atlantis', nombre: 'Atlantis · Node Hexelion', reco: [-2, 1], siempre: false },
    { id: 'risen',    clave: 'node.risen',    nombre: 'the Risen',                reco: [2, -1], siempre: false }
  ];
  var FRASE = {
    appears: 'appears: the node is alive',
    leaves: 'leaves: the node is no longer alive, so it is not drawn'
  };
  var HEX = [];
  for (var i = 0; i < 6; i++) {
    HEX.push([Math.round(160 + 60 * Math.cos(i * Math.PI / 3)), Math.round(48 + 40 * Math.sin(i * Math.PI / 3))]);
  }

  function claveHuerfana(node) { return node.clave === undefined || node.clave === '' || node.clave === null; }

  // A visible node: the cabin always, the others only when listed as alive. Unknown ids are not drawn.
  // The mana of each node is MEDIDO only when the entry carries a whole number; otherwise NO_DATA with its cause.
  function mana(entrada, node) {
    var m = entrada && entrada.mana;
    if (m && typeof m.valor === 'number' && Number.isInteger(m.valor) && m.valor >= 0 && m.valor <= 100) {
      return { estado: 'MEDIDO', valor: m.valor };
    }
    return { estado: 'NO_DATA', causa: node.id === 'cabin' ? 'no mana measurement reported for the tutorial cabin yet' : 'no mana measurement reported for this node' };
  }

  // estado(entrada) → the visible rows, in fixed order. entrada = { t, cabin?, nodes: [{ id, mana? }] }.
  function estado(entrada) {
    var e = entrada || {};
    var vivos = Array.isArray(e.nodes) ? e.nodes : [];
    var rows = [];
    NODES.forEach(function (node) {
      var vivo = node.siempre || vivos.some(function (n) { return n && n.id === node.id; });
      if (!vivo) { return; }
      if (claveHuerfana(node)) { throw new Error('orphan_visual_node: ' + node.id + ' has no lexicon key'); }
      var nodeEntry = node.id === 'cabin' ? (e.cabin || {}) : (vivos.find(function (n) { return n && n.id === node.id; }) || {});
      rows.push({ id: node.id, clave: node.clave, nombre: node.nombre, reco: node.reco, mana: mana(nodeEntry, node) });
    });
    return Object.freeze(rows.map(Object.freeze));
  }

  // paleta(t) → day/night colours. Integer lerp between night and day; the triangle wave depends on t only.
  var NOCHE = { cielo: [23, 19, 31], tinta: [236, 228, 210] };
  var DIA = { cielo: [244, 235, 208], tinta: [23, 19, 31] };
  function hex(c) { return '#' + c.map(function (v) { return ('0' + v.toString(16)).slice(-2); }).join(''); }
  function mezcla(a, b, k) { return a.map(function (v, j) { return Math.round(v + (b[j] - v) * k / 256); }); }
  function paleta(t) {
    var n = Number.isInteger(t) ? t : 0;
    var f = ((n % CYCLE) + CYCLE) % CYCLE;
    var tri = f < CYCLE / 2 ? f : CYCLE - f;          // 0 at midnight, CYCLE/2 at noon
    var k = Math.round(tri * 256 / (CYCLE / 2));      // 0..256
    return { t: n, dia: k, cielo: hex(mezcla(NOCHE.cielo, DIA.cielo, k)), tinta: hex(mezcla(NOCHE.tinta, DIA.tinta, k)) };
  }

  // The base sound of every bubble is the tutorial sea's own wave (the frame's design data, as the door drew it before).
  // A measured mana adds a second wave, from its value; NO_DATA adds nothing and says so in the sentence.
  var SEA = [[1, 40, 10, 0], [3, 20, 5, 4]];
  function ondas(m) {
    if (m.estado !== 'MEDIDO') { return []; }
    return [[1, m.valor, 10, 0], [3, Math.floor(m.valor / 2), 5, 4]];
  }

  // marco(row, t, evento) → one state frame, under 1,024 bytes.
  function marco(row, t, evento) {
    var items = [
      { o: 'ribbon', pts: HEX, closed: true, f: 'paper', s: 'ink', lw: 3 },
      { o: 'letters', x: 160, y: 28, tx: row.nombre, sz: 16, f: 'paper', s: 'ink', sh: [1.5, 1.5, 'cyan'] },
      { o: 'wave', x: 250, y: 72, sc: 0.35, h: SEA, f: 'paper', s: 'ink' }
    ];
    var h = ondas(row.mana);
    if (h.length) { items.push({ o: 'wave', x: 160, y: 70, sc: 0.4, h: h, f: 'paper', s: 'ink' }); }
    var medida = row.mana.estado === 'MEDIDO' ? 'mana ' + row.mana.valor : 'mana NO_DATA (' + row.mana.causa + ')';
    var frase = row.nombre + ' · ' + medida + ' · ' + (evento ? FRASE[evento] : 'drawn at tick ' + t);
    var fotograma = {
      v: 'preceptoros.bubble/1', id: row.id, t: t, cv: [ANCHO, ALTO],
      atoms: [{ k: row.clave, r: frase, i: items }],
      bands: ['paper', 'ink', 'cyan'],
      change: [frase],
      sound: 'ok'
    };
    return fotograma;
  }

  // The sky is a visible change too: its own frame, one sentence, no waves (so its sound is NO_DATA with its cause).
  function cielo(pal) {
    return {
      v: 'preceptoros.bubble/1', id: 'sky', t: pal.t, cv: [ANCHO, ALTO],
      atoms: [{ k: 'sky', r: 'the sky at tick ' + pal.t + ': day ' + pal.dia + ' of 256', i: [] }],
      bands: ['paper', 'ink', 'cyan'],
      change: ['the sky at tick ' + pal.t],
      sound: 'NO_DATA: the sky declares no waves; nothing is invented'
    };
  }

  // mapa(entrada) → the scene: palette and its sky frame, and each visible node placed by the fixed iso angle and its frame.
  function mapa(entrada) {
    var rows = estado(entrada);
    var t = entrada && Number.isInteger(entrada.t) ? entrada.t : 0;
    var base = Iso.proyecta(NODES[0].reco[0], NODES[0].reco[1], CELDA);
    return Object.freeze({
      paleta: paleta(t),
      cielo: cielo(paleta(t)),
      nodes: rows.map(function (row) {
        var p = Iso.proyecta(row.reco[0], row.reco[1], CELDA);
        return Object.freeze({ id: row.id, x: (p.x - base.x) * ESCALA, y: (p.y - base.y) * ESCALA, frame: marco(row, t) });
      })
    });
  }

  // cambios(anterior, siguiente) → the frames of what changed: a node that appears, leaves, or gets its mana.
  function cambios(anterior, siguiente, t) {
    var antes = estado(anterior), despues = estado(siguiente), out = [];
    var ids = function (rs) { return rs.map(function (r) { return r.id; }); };
    despues.forEach(function (r) {
      if (ids(antes).indexOf(r.id) < 0) { out.push(marco(r, t, 'appears')); }
    });
    antes.forEach(function (r) {
      if (ids(despues).indexOf(r.id) < 0) { out.push(marco(r, t, 'leaves')); }
    });
    return out;
  }

  // Frame size law and the byte count of a frame, measured by its serialised form.
  function bytes(fotograma) {
    var texto = JSON.stringify(fotograma);
    return typeof TextEncoder !== 'undefined' ? new TextEncoder().encode(texto).length : texto.length;
  }
  function valida(fotograma) {
    var problemas = [];
    if (bytes(fotograma) >= LIMITE_BYTES) { problemas.push('frame of ' + bytes(fotograma) + ' bytes, limit ' + LIMITE_BYTES); }
    if (typeof fotograma.sound !== 'string' || !fotograma.sound) { problemas.push('sound not declared'); }
    return problemas;
  }

  // FNV-1a over a string: the same bytes give the same hash in every run (the gate's n=2 receipt).
  function hash32(texto) {
    var h = 0x811c9dc5;
    for (var i = 0; i < texto.length; i++) { h ^= texto.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; }
    return ('00000000' + (h >>> 0).toString(16)).slice(-8);
  }

  var AtlasMapaGlobal = Object.freeze({
    NODES: NODES, CYCLE: CYCLE, ANCHO: ANCHO, ALTO: ALTO, LIMITE_BYTES: LIMITE_BYTES, RECURSO: RECURSO,
    ESCALA: ESCALA, BURBUJA: BURBUJA,
    estado: estado, paleta: paleta, marco: marco, mapa: mapa, cambios: cambios,
    bytes: bytes, valida: valida, hash32: hash32
  });
  if (common) { module.exports = AtlasMapaGlobal; } else { root.AtlasMapaGlobal = AtlasMapaGlobal; }
})(typeof globalThis !== 'undefined' ? globalThis : this);
