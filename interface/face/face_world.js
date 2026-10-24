(function (root) {
  'use strict';
  var V = 'preceptoros.bubble/1';
  var W = 720, H = 960, tile = 12;
  var homeAt = [360, 836];
  var starH = [[1, 26, 26, 0], [-4, 8, 8, 0]];
  var crabH = [[1, 30, 18, 0], [5, 5, 5, 32], [-3, 5, 5, -32]];
  var places = [
    { id: 'beacon', name: 'the beacon', at: [168, 548], bend: 1,
      task: 'Your first task: walk to the beacon.',
      done: 'You reached the beacon. It is the door that picks your world and your tutorial. A node would show its signed card here; node: NO_DATA, cause: no node is paired with this preview.' },
    { id: 'reef', name: 'the Reef', at: [566, 470], bend: -1,
      task: 'Task two: walk to the Reef.',
      done: 'This is the Reef, where buildings grow. A phone can hold one building that nobody can take. Building it needs you: the machine proposes, you sign.' },
    { id: 'rift', name: 'the rift', at: [330, 214], bend: 1,
      task: 'Last task: walk to the rift.',
      done: 'This is the rift, the door of the map. It is quiet today: its life is not built yet, so it says NO_DATA.' }
  ];
  var fogZones = [[400, 720, 330, 640], [160, 500, 70, 330]];

  function hash32(s) {
    var h = 0x811c9dc5, i;
    for (i = 0; i < s.length; i++) { h = Math.imul(h ^ s.charCodeAt(i), 0x01000193); }
    return h >>> 0;
  }
  function uniq(list) { return list.filter(function (b, j, a) { return a.indexOf(b) === j; }); }
  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

  function route(from, place) {
    var a = from, b = place.at, dx = b[0] - a[0], dy = b[1] - a[1], len = Math.hypot(dx, dy) || 1;
    var nx = -dy / len, ny = dx / len, h = hash32(place.id), pts = [], i, t, w, bow;
    for (i = 0; i <= 4; i++) {
      t = i / 4;
      bow = place.bend * 0.22 * len * Math.sin(Math.PI * t);
      w = i === 0 || i === 4 ? 0 : (((h >>> (i * 4)) & 15) - 7.5);
      pts.push([Math.round(a[0] + dx * t + nx * (bow + w)), Math.round(a[1] + dy * t + ny * (bow + w))]);
    }
    return pts;
  }

  function sample(pts) {
    var out = [pts[0]], n = pts.length, i, k, p0, p1, p2, p3, c1, c2, t, u;
    for (i = 0; i < n - 1; i++) {
      p0 = pts[Math.max(0, i - 1)]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[Math.min(n - 1, i + 2)];
      c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
      c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
      for (k = 1; k <= 24; k++) {
        t = k / 24; u = 1 - t;
        out.push([u * u * u * p1[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t * t * t * p2[0],
          u * u * u * p1[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t * t * t * p2[1]]);
      }
    }
    return out;
  }

  function walk(pts) {
    var s = sample(pts), acc = [0], i, total, steps, out = [], j = 0, d;
    for (i = 1; i < s.length; i++) { acc.push(acc[i - 1] + Math.hypot(s[i][0] - s[i - 1][0], s[i][1] - s[i - 1][1])); }
    total = acc[acc.length - 1];
    steps = Math.max(1, Math.round(total / tile));
    for (i = 0; i <= steps; i++) {
      d = total * i / steps;
      while (j < acc.length - 2 && acc[j + 1] < d) { j++; }
      var f = acc[j + 1] > acc[j] ? (d - acc[j]) / (acc[j + 1] - acc[j]) : 0;
      out.push([Math.round(s[j][0] + (s[j + 1][0] - s[j][0]) * f), Math.round(s[j][1] + (s[j + 1][1] - s[j][1]) * f)]);
    }
    return { steps: steps, units: Math.round(total), at: out };
  }

  function counter(left, units) {
    return { tiles: left, steps: left, yardstick: '1 tile = ' + tile + ' map units; 1 step = 1 tile', mapUnits: units, realTime: 'NO_DATA: no clock is read' };
  }

  function mapFrame(skin) {
    return { v: V, id: 'map', t: 0, cv: [W, H], atoms: [
            { k: 'land', r: 'home, west, east, north', i: [
        { o: 'blob', x: 360, y: 846, rx: 230, ry: 96, f: skin.land },
        { o: 'blob', x: 186, y: 560, rx: 150, ry: 186, f: skin.land },
        { o: 'blob', x: 570, y: 470, rx: 136, ry: 214, f: skin.land },
        { o: 'blob', x: 330, y: 206, rx: 226, ry: 118, f: skin.land }] },
      { k: 'rift', r: 'the rift', i: [{ o: 'ribbon', pts: [[176, 214], [330, 176], [486, 214], [330, 250]], closed: true, f: skin.deep }] },
      { k: 'reef', r: 'the Reef', i: [{ o: 'field', kind: 'phyllo', x: 566, y: 470, n: 34, c: 9, r: 7, f: skin.coral }] }],
      bands: uniq([skin.land, skin.deep, skin.coral]), change: ['rest'], sound: 'NO_DATA', soundCause: 'the map is silent', motion: 'NO_DATA' };
  }

  function nodesFrame(skin) {
    var small = [[1, 14, 14, 0], [-4, 4, 4, 0]];
    return { v: V, id: 'nodes', t: 0, cv: [W, H], atoms: [
      { k: 'islet', r: 'an islet', i: [{ o: 'blob', x: 626, y: 790, rx: 62, ry: 36, f: skin.land }] },
      { k: 'nodes', r: 'two other nodes', i: [{ o: 'wave', x: 626, y: 784, h: small, f: skin.star }, { o: 'wave', x: 96, y: 300, h: small, f: skin.star }] }],
      bands: uniq([skin.land, skin.star]), change: ['rest'], sound: 'NO_DATA', soundCause: 'the map is silent', motion: 'NO_DATA' };
  }

  function gridFrame(skin) {
    var i = [], k;
    for (k = 1; k < 3; k++) { i.push({ o: 'ribbon', pts: [[k * 240, 24], [k * 240 + (2 * k - 3) * 40, 480], [k * 240, 936]], s: skin.grid, lw: 2 }); }
    for (k = 1; k < 3; k++) { i.push({ o: 'ribbon', pts: [[24, k * 320], [360, k * 320 + 24], [696, k * 320]], s: skin.grid, lw: 2 }); }
    return { v: V, id: 'grid', t: 0, cv: [W, H], atoms: [
      { k: 'grid', r: 'globe lines', i: i },
      { k: 'names', r: 'place names', i: [
        { o: 'text', x: 300, y: 900, tx: 'home', sz: 28, f: skin.label, sh: [2, 2, skin.halo] },
        { o: 'text', x: 96, y: 620, tx: 'the beacon', sz: 28, f: skin.label, sh: [2, 2, skin.halo] },
        { o: 'text', x: 500, y: 600, tx: 'the Reef', sz: 28, f: skin.label, sh: [2, 2, skin.halo] },
        { o: 'text', x: 280, y: 300, tx: 'the rift', sz: 28, f: skin.label, sh: [2, 2, skin.halo] }] }],
      bands: uniq([skin.grid, skin.label, skin.halo]), change: ['rest'], sound: 'NO_DATA', soundCause: 'the map is silent', motion: 'NO_DATA' };
  }

  function stateFrame(skin, st) {
    var c = st.at, x = c[0], y = c[1], ph = (st.step || 0) % 2 ? 4 : 0, done = st.task, fog = [], atoms;
    fogZones.forEach(function (z, i) { if (done < i + 2) { fog.push({ o: 'field', kind: 'halftone', x: [z[0], z[1]], y: [z[2], z[3]], f: skin.fog }); } });
    atoms = [{ k: 'beacon', r: done ? 'beacon lit' : 'beacon', i: [{ o: 'wave', x: 168, y: 548, h: starH, f: done ? skin.lit : skin.star }] }];
    if (fog.length) { atoms.push({ k: 'fog', r: 'fog', i: fog }); }
    if (st.path) { atoms.push({ k: 'path', r: 'path', i: [{ o: 'ribbon', pts: st.path, s: skin.path, lw: 6 }] }); }
    if (done < places.length) {
      var p = places[done].at;
      atoms.push({ k: 'goal', r: 'task: ' + places[done].name, i: [{ o: 'arcs', x: p[0], y: p[1], r: [40, 40], n: 4, arc: 50, ph: -25, s: skin.path, lw: 6 }] });
    }
    atoms.push({ k: 'crab', r: 'you at ' + x + ',' + y, i: skin.crab === 'canon'
      ? [{ o: 'crab', x: x, y: y, rr: 54, dir: st.dir === 1 ? 1 : -1, eye: (st.step || 0) % 2 ? 'up' : 'open' }]
      : [{ o: 'wave', x: x, y: y, h: [crabH[0], [5, 5, 5, 32 + ph], [-3, 5, 5, -32 + ph]], f: skin.body },
        { o: 'arcs', x: x, y: y - 6, r: [9, 9], n: 2, arc: 24, ph: 168, s: 'ink', lw: 7 }] });
    return { v: V, id: 'you', t: st.step || 0, cv: [W, H], atoms: atoms,
      bands: uniq([done ? skin.lit : skin.star].concat(fog.length ? [skin.fog] : [], [skin.path, skin.crab === 'canon' ? 'cyan' : skin.body, 'ink'])),
      change: [st.change || 'rest'], sound: st.sound ? 'arrival voice' : 'NO_DATA', soundCause: st.sound ? 'vozDe star h' : 'sound off', motion: st.walking ? 'walking' : 'on input' };
  }

  var patrol = [[486, 642], [566, 700], [626, 768], [566, 830], [476, 772], [430, 700]];
  var codexScale = 1.6;
  var canon = [
    { o: 'octo', x: 650, y: 610, r: 29, eye: 'up', say: 'A little octopus looks up at you. Hello!' },
    { o: 'star', x: 262, y: 716, r: 32, eye: 'up', say: 'A starfish waves one of its five arms.' },
    { o: 'snail', x: 480, y: 872, r: 26, eye: 'up', say: 'A snail takes its time. So can you.' },
    { o: 'bust', x: 452, y: 132, r: 74, eye: 'open', cybEye: 'violet', mEye: 'happy', mouth: 'o', say: 'The Preceptor has landed upright by the rift. Its violet eye means signed.' }
  ];

  function wanderAt(moves) {
    var k = 6, n = patrol.length * k, i = ((moves % n) + n) % n, a = patrol[Math.floor(i / k)], b = patrol[(Math.floor(i / k) + 1) % patrol.length], t = (i % k) / k;
    return [Math.round(a[0] + (b[0] - a[0]) * t), Math.round(a[1] + (b[1] - a[1]) * t), b[0] >= a[0] ? 1 : -1];
  }

  function near(st, x, y, r) { return Math.hypot(st.at[0] - x, st.at[1] - y) < r; }

  function castFrame(skin, st) {
    if (skin.cast === 'canon') {
      var items = [{ o: 'field', kind: 'halftone', y: [70, 300], r: '2.2|1.2|.6|0', step: 16, f: 'cyan' }];
      canon.forEach(function (c) {
        var it = {}, k;
        for (k in c) { if (k !== 'say') { it[k] = c[k]; } }
        if (c.o !== 'bust' && near(st, c.x, c.y, 110)) { it.eye = 'open'; }
        items.push(it);
      });
      return { v: V, id: 'cast', t: st.step || 0, cv: [W, H], atoms: [{ k: 'creatures', r: 'the canon creatures: an octopus, a starfish, a snail, and the Preceptor by the rift', i: items }],
        bands: ['cyan', 'ink', 'ocean', 'paper', 'FIRMADO.base'], change: [st.change || 'rest'], sound: 'NO_DATA', soundCause: 'the creatures are silent', motion: 'they look at you when you come near' };
    }
    if (skin.cast === 'wanderer') {
      var w = wanderAt(st.moves || 0), x = w[0], y = w[1], d = w[2], z = skin.zombie;
      var q = function (dx, dy) { return [Math.round(x + 1.5 * dx * d), Math.round(y - 1.5 * dy)]; };
      var o = function (kind, dx, dy, r, f) { var c = q(dx, dy); return { o: kind, x: c[0], y: c[1], rx: r, ry: r, f: f }; };
      return { v: V, id: 'cast', t: st.moves || 0, cv: [W, H], atoms: [{ k: 'wanderer', r: 'friendly wanderer at ' + x + ',' + y, i: [
        { o: 'ribbon', pts: [q(-7, 0), q(-5, 22), q(5, 22), q(8, 1)], s: z.pants, lw: 13 },
        { o: 'wave', x: x, y: Math.round(y - 52), h: [[1, 24, 26, 0], [6, 0, 3, 0]], f: z.shirt },
        o('blob', 5, 34, 6, z.patch),
        { o: 'ribbon', pts: [q(4, 44), q(18, 46), q(31, 42)], s: z.skin, lw: 11 },
        o('blob', 3, 63, 34, z.skin),
        o('blob', 10, 66, 8, 'paper'), o('blob', -3, 66, 7, 'paper'),
        { o: 'arcs', x: q(4, 65)[0], y: q(4, 65)[1], r: [10, 10], n: 2, arc: 30, ph: -15, s: 'ink', lw: 5 },
        o('blob', 7, 54, 7, z.patch)] }],
        bands: uniq([z.pants, z.shirt, z.patch, z.skin, 'paper', 'ink']), change: [st.change || 'rest'], sound: 'NO_DATA', soundCause: 'silent', motion: 'steps when you move' };
    }
    return null;
  }

  function castMeet(skin, st) {
    if (skin.cast === 'canon') { for (var i = 0; i < canon.length; i++) { if (near(st, canon[i].x, canon[i].y, 110)) { return canon[i].say; } } }
    if (skin.cast === 'wanderer') { var w = wanderAt(st.moves || 0); if (near(st, w[0], w[1] - 40, 90)) { return 'Radio: a wanderer shuffles past, arms out. It only wants company, and it cannot hurt you.'; } }
    return null;
  }

  function headFrame(skin) {
    return { v: V, id: 'head', t: 0, cv: [120, 120], atoms: [{ k: 'head', r: 'the Preceptor smiles', i: [
      { o: 'arcs', x: 60, y: 60, r: [50, 50], n: 3, arc: 70, ph: 195, s: skin.path, lw: 5 },
      { o: 'blob', x: 60, y: 62, rx: 38, ry: 40, f: skin.face },
      { o: 'blob', x: 47, y: 56, rx: 5, ry: 7, f: 'ink' }, { o: 'blob', x: 73, y: 56, rx: 5, ry: 7, f: 'ink' },
      { o: 'ribbon', pts: [[47, 76], [60, 85], [73, 76]], s: 'ink', lw: 4 }] }],
      bands: uniq([skin.path, skin.face, 'ink']), change: ['rest'], sound: 'NO_DATA', soundCause: 'avatar is silent', motion: 'NO_DATA' };
  }

  function joyFrame(skin, dx, dy) {
    return { v: V, id: 'joy', t: 0, cv: [168, 168], atoms: [
      { k: 'base', r: 'joystick, four arrows', i: [{ o: 'blob', x: 84, y: 84, rx: 74, ry: 74, rough: 0, f: skin.land },
        { o: 'arcs', x: 84, y: 84, r: [58, 58], n: 4, arc: 36, ph: -18, s: 'ink', lw: 5 }] },
      { k: 'knob', r: dx || dy ? 'knob pushed' : 'knob centered', i: [{ o: 'blob', x: 84 + dx, y: 84 + dy, rx: 30, ry: 30, rough: 0, f: skin.body }] }],
      bands: uniq([skin.land, 'ink', skin.body]), change: ['joystick'], sound: 'NO_DATA', soundCause: 'joystick is silent', motion: 'follows the finger' };
  }

  function bytes(o) {
    var s = JSON.stringify(o);
    return typeof TextEncoder === 'function' ? new TextEncoder().encode(s).length : Buffer.byteLength(s, 'utf8');
  }

  var World = { W: W, H: H, tile: tile, homeAt: homeAt, places: places, starH: starH, route: route, walk: walk, counter: counter, clamp: clamp,
    mapFrame: mapFrame, gridFrame: gridFrame, nodesFrame: nodesFrame, stateFrame: stateFrame, headFrame: headFrame, castFrame: castFrame, castMeet: castMeet, wanderAt: wanderAt, canon: canon, codexScale: codexScale, joyFrame: joyFrame, bytes: bytes };
  if (typeof module === 'object' && module.exports) { module.exports = World; } else { root.PreceptorWorld = World; }
})(typeof module === 'object' && module.exports ? this : window);
