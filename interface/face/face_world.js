(function (root) {
  'use strict';
  var V = 'preceptoros.bubble/1', root2 = Math.SQRT2;
  var worldSize = 1000, tile = 12;
  var homeAt = [500, 690];
  var starH = [[1, 26, 26, 0], [-4, 8, 8, 0]];
  var places = [
    { id: 'beacon', name: 'the beacon', at: [306, 462], bend: 1,
      task: 'Your first task: sail to the beacon.',
      done: 'You reached the beacon. It is the door that picks your world and your tutorial. A node would show its signed card here; node: NO_DATA, cause: no node is paired with this preview.' },
    { id: 'reef', name: 'the Reef', at: [722, 430], bend: -1,
      task: 'Task two: sail to the Reef.',
      done: 'This is the Reef, where buildings grow. A phone can hold one building that nobody can take. Building it needs you: the machine proposes, you sign.' },
    { id: 'rift', name: 'the rift', at: [486, 196], bend: 1,
      task: 'Last task: sail to the rift.',
      done: 'This is the rift, the door of the map. It is quiet today: its life is not built yet, so it says NO_DATA.' }
  ];
  var isles = [
    { id: 'home', x: 500, y: 700, rx: 124, ry: 92, kind: 'sand' },
    { id: 'beacon', x: 300, y: 456, rx: 76, ry: 62, kind: 'sand' },
    { id: 'reef', x: 724, y: 428, rx: 92, ry: 74, kind: 'sand' },
    { id: 'rift', x: 486, y: 190, rx: 116, ry: 72, kind: 'rock' },
    { id: 'west', x: 196, y: 762, rx: 60, ry: 48, kind: 'forest' },
    { id: 'east', x: 824, y: 758, rx: 62, ry: 50, kind: 'rock' },
    { id: 'peak', x: 168, y: 230, rx: 84, ry: 64, kind: 'rock' },
    { id: 'wood', x: 820, y: 168, rx: 64, ry: 52, kind: 'forest' },
    { id: 'islet', x: 640, y: 588, rx: 40, ry: 30, kind: 'sand' }
  ];

  function hash32(s) {
    var h = 0x811c9dc5, i;
    for (i = 0; i < s.length; i++) { h = Math.imul(h ^ s.charCodeAt(i), 0x01000193); }
    return h >>> 0;
  }
  function uniq(list) { return list.filter(function (b, j, a) { return b && a.indexOf(b) === j; }); }
  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
  function iso(x, y) { return [Math.round((x - y) * root2 / 2), Math.round((x + y) * root2 / 4)]; }

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
    var s = sample(pts), acc = [0], i, total, steps, out = [], j = 0, d, f;
    for (i = 1; i < s.length; i++) { acc.push(acc[i - 1] + Math.hypot(s[i][0] - s[i - 1][0], s[i][1] - s[i - 1][1])); }
    total = acc[acc.length - 1];
    steps = Math.max(1, Math.round(total / tile));
    for (i = 0; i <= steps; i++) {
      d = total * i / steps;
      while (j < acc.length - 2 && acc[j + 1] < d) { j++; }
      f = acc[j + 1] > acc[j] ? (d - acc[j]) / (acc[j + 1] - acc[j]) : 0;
      out.push([Math.round(s[j][0] + (s[j + 1][0] - s[j][0]) * f), Math.round(s[j][1] + (s[j + 1][1] - s[j][1]) * f)]);
    }
    return { steps: steps, units: Math.round(total), at: out };
  }

  function counter(left, units) {
    return { tiles: left, steps: left, yardstick: '1 cell = ' + tile + ' map units; 1 step = 1 cell', mapUnits: units, realTime: 'NO_DATA: no clock is read' };
  }

  function islandItems(list, skin) {
    var out = [];
    list.forEach(function (s) {
      var top = s.kind === 'rock' ? skin.rock : s.kind === 'forest' ? skin.forest : skin.sand;
      out.push({ o: 'blob', x: s.x + 9, y: s.y + 9, rx: s.rx, ry: s.ry, seed: s.id, rough: 0.7, f: skin.cliff });
      out.push({ o: 'blob', x: s.x, y: s.y, rx: s.rx, ry: s.ry, seed: s.id, rough: 0.7, f: top });
    });
    return out;
  }

  function seaFrame(skin) {
    return { v: V, id: 'sea', t: 0, cv: [worldSize, worldSize], atoms: [
      { k: 'shelves', r: 'shelves on the shared seabed', i: isles.map(function (q) { return { o: 'blob', x: q.x + 4, y: q.y + 4, rx: Math.round(q.rx * 1.38), ry: Math.round(q.ry * 1.38), f: skin.shelf }; }) }],
      bands: [skin.shelf], change: ['rest'], sound: 'NO_DATA', soundCause: 'the sea is silent', motion: 'NO_DATA' };
  }

  var crabRule = 'EMULADO: army = 2 per place measured + 4 for a battle won; core = 3 per place; coral once the tutorial is done stands for a paired node; legs and eyes NO_DATA';
  function crabState(task, won) {
    var army = 2 * Math.min(task, places.length) + (won ? 4 : 0), node = task >= places.length;
    return { army: army, node: node, core: 3 * Math.min(task, places.length) };
  }

  var groups = [['home', 'beacon'], ['reef', 'rift'], ['west', 'east', 'peak'], ['wood', 'islet']];
  var groupNames = ['home and the beacon', 'the Reef and the rift', 'the west node, the east node and the peak', 'the wood and an islet'];

  function islesFrame(skin, part) {
    var list = isles.filter(function (s) { return groups[part].indexOf(s.id) >= 0; }), extra = [];
    var atoms = [{ k: 'isles', r: groupNames[part], i: islandItems(list, skin) }];
    if (part === 1) { atoms.push({ k: 'chasm', r: 'the rift opens', i: [{ o: 'ribbon', pts: [[420, 196], [486, 168], [552, 194], [486, 214]], closed: true, f: 'ink' }] }); extra = ['ink']; }
    if (part === 1) { atoms.push({ k: 'coral', r: 'coral of the Reef', i: [{ o: 'field', kind: 'phyllo', x: 724, y: 428, n: 30, c: 10, r: 8, f: skin.coral }] }); extra.push(skin.coral); }
    if (part === 3) { atoms.push({ k: 'woods', r: 'trees', i: [
      { o: 'field', kind: 'phyllo', x: 196, y: 760, n: 22, c: 9, r: 9, f: skin.leaf },
      { o: 'field', kind: 'phyllo', x: 820, y: 166, n: 26, c: 9, r: 9, f: skin.leaf }] }); extra = [skin.leaf]; }
    return { v: V, id: 'isles' + part, t: 0, cv: [worldSize, worldSize], atoms: atoms,
      bands: uniq([skin.cliff].concat(list.map(function (q) { return q.kind === 'rock' ? skin.rock : q.kind === 'forest' ? skin.forest : skin.sand; }), extra)), change: ['rest'], sound: 'NO_DATA', soundCause: 'the islands are silent', motion: 'NO_DATA' };
  }

  function standFrame(skin) {
    var p1 = iso(168, 224), p2 = iso(830, 752), p3 = iso(486, 176), h = iso(500, 690), w = iso(196, 756), e = iso(824, 750), small = [[1, 14, 14, 0], [-4, 4, 4, 0]];
    return { v: V, id: 'stand', t: 0, cv: [1420, 1420], atoms: [
      { k: 'peaks', r: 'mountains on the peak, the east node and the rift', i: [
        { o: 'blob', x: p1[0] - 22, y: p1[1] - 26, rx: 34, ry: 42, seed: 'm1', rough: 0.5, f: skin.mount },
        { o: 'blob', x: p1[0] + 20, y: p1[1] - 18, rx: 26, ry: 32, seed: 'm2', rough: 0.5, f: skin.mount },
        { o: 'blob', x: p2[0], y: p2[1] - 22, rx: 26, ry: 32, seed: 'm3', rough: 0.5, f: skin.mount },
        { o: 'blob', x: p3[0] - 70, y: p3[1] - 20, rx: 24, ry: 30, seed: 'm4', rough: 0.5, f: skin.mount }] },
      { k: 'town', r: 'the home town, domes', i: [{ o: 'city', x: [h[0] - 54, h[0] + 54], y: [h[1] - 58, h[1] - 8], dome: 3 }] },
      { k: 'nodes', r: 'two other nodes, each on its island', i: [{ o: 'wave', x: w[0], y: w[1] - 30, h: small, f: skin.star }, { o: 'wave', x: e[0] + 30, y: e[1] - 30, h: small, f: skin.star }] }],
      bands: uniq([skin.mount, skin.star, 'cyan']), change: ['rest'], sound: 'NO_DATA', soundCause: 'the map is silent', motion: 'NO_DATA' };
  }

  function namesFrame(skin) {
    var n = function (tx, x, y) { var p = iso(x, y); return { o: 'text', x: p[0], y: p[1], tx: tx, sz: 24, f: skin.label, sh: [2, 2, skin.halo] }; };
    return { v: V, id: 'names', t: 0, cv: [1420, 1420], atoms: [{ k: 'names', r: 'place names', i: [
      n('home', 560, 800), n('the beacon', 330, 540), n('the Reef', 760, 520), n('the rift', 540, 270)] }],
      bands: uniq([skin.label, skin.halo]), change: ['rest'], sound: 'NO_DATA', soundCause: 'the map is silent', motion: 'NO_DATA' };
  }

  function clears(st) {
    var c = [{ x: homeAt[0], y: homeAt[1], r: 190 }], i;
    for (i = 0; i < Math.min(st.task, places.length); i++) { c.push({ x: places[i].at[0], y: places[i].at[1], r: 150 }); }
    (st.trail || []).forEach(function (q) { c.push({ x: q[0], y: q[1], r: 80 }); });
    c.push({ x: st.at[0], y: st.at[1], r: 110 });
    return c;
  }

  function stateFrame(skin, st) {
    var c = iso(st.at[0], st.at[1]), x = c[0], y = c[1], done = st.task, atoms, b = iso(306, 462);
    atoms = [{ k: 'beacon', r: done ? 'beacon lit' : 'beacon', i: [{ o: 'wave', x: b[0], y: b[1] - 34, h: starH, f: done ? skin.lit : skin.star }] }];
    if (st.path) { atoms.push({ k: 'path', r: 'path', i: [{ o: 'ribbon', pts: st.path.map(function (q) { return iso(q[0], q[1]); }), s: skin.path, lw: 6 }] }); }
    if (done < places.length) {
      var p = iso(places[done].at[0], places[done].at[1]);
      atoms.push({ k: 'goal', r: 'task: ' + places[done].name, i: [{ o: 'arcs', x: p[0], y: p[1] - 8, r: [44, 44], n: 4, arc: 50, ph: -25, s: skin.path, lw: 6 }] });
    }
    atoms.push({ k: 'brume', r: 'mist clears: home, ' + Math.min(done, places.length) + ' places, ' + (st.trail || []).length + ' trail marks', i: [] });
    var cs = crabState(done, st.won), fo = st.forma || { escala: 1, clase: 'mar' };
    atoms.push({ k: 'crab', r: 'you, a ' + fo.clase + (skin.hero ? ' space soldier' : ' crab') + ', size ' + fo.escala + ' (army ' + cs.army + '), at ' + st.at[0] + ',' + st.at[1], i: [] });
    return { v: V, id: 'you', t: st.step || 0, cv: [1420, 1420], atoms: atoms,
      bands: uniq([done ? skin.lit : skin.star, skin.path, 'cyan', 'ink']),
      change: [st.change || 'rest'], sound: st.sound ? 'arrival voice' : 'NO_DATA', soundCause: st.sound ? 'vozDe star h' : 'sound off', motion: st.walking ? 'walking' : 'on input' };
  }

  var patrol = [[560, 560], [610, 610], [640, 680], [610, 750], [560, 790], [520, 600]];
  var codexScale = 1.6;
  var canon = [
    { o: 'octo', x: 800, y: 500, r: 29, eye: 'up', say: 'A little octopus looks up at you. Hello!' },
    { o: 'star', x: 360, y: 520, r: 32, eye: 'up', say: 'A starfish waves one of its five arms.' },
    { o: 'snail', x: 600, y: 760, r: 26, eye: 'up', say: 'A snail takes its time. So can you.' }
  ];

  function wanderAt(moves) {
    var k = 6, n = patrol.length * k, i = ((moves % n) + n) % n, a = patrol[Math.floor(i / k)], b = patrol[(Math.floor(i / k) + 1) % patrol.length], t = (i % k) / k;
    return [Math.round(a[0] + (b[0] - a[0]) * t), Math.round(a[1] + (b[1] - a[1]) * t), b[0] - b[1] >= a[0] - a[1] ? 1 : -1];
  }
  function near(st, x, y, r) { return Math.hypot(st.at[0] - x, st.at[1] - y) < r; }

  function castFrame(skin, st) {
    if (skin.cast === 'canon') {
      var items = [];
      canon.forEach(function (c) {
        var it = {}, k, p = iso(c.x, c.y);
        for (k in c) { if (k !== 'say') { it[k] = c[k]; } }
        it.x = p[0]; it.y = p[1];
        if (near(st, c.x, c.y, 110)) { it.eye = 'open'; }
        items.push(it);
      });
      return { v: V, id: 'cast', t: st.step || 0, cv: [1420, 1420], atoms: [{ k: 'creatures', r: 'the canon creatures: an octopus, a starfish and a snail', i: items }],
        bands: ['cyan', 'ink', 'ocean', 'paper'], change: [st.change || 'rest'], sound: 'NO_DATA', soundCause: 'the creatures are silent', motion: 'they look at you when you come near' };
    }
    if (skin.cast === 'wanderer') {
      var w = wanderAt(st.moves || 0), c0 = iso(w[0], w[1]), x = c0[0], y = c0[1], d = w[2], z = skin.zombie;
      var q = function (dx, dy) { return [Math.round(x + 1.5 * dx * d), Math.round(y - 1.5 * dy)]; };
      var o = function (kind, dx, dy, r, f) { var c = q(dx, dy); return { o: kind, x: c[0], y: c[1], rx: r, ry: r, f: f }; };
      return { v: V, id: 'cast', t: st.moves || 0, cv: [1420, 1420], atoms: [{ k: 'wanderer', r: 'friendly wanderer at ' + w[0] + ',' + w[1], i: [
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
    var i, w;
    if (skin.cast === 'canon') { for (i = 0; i < canon.length; i++) { if (near(st, canon[i].x, canon[i].y, 110)) { return canon[i].say; } } }
    if (skin.cast === 'wanderer') { w = wanderAt(st.moves || 0); if (near(st, w[0], w[1], 90)) { return 'Radio: a wanderer shuffles past, arms out. It only wants company, and it cannot hurt you.'; } }
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
      { k: 'base', r: 'joystick, four arrows', i: [{ o: 'blob', x: 84, y: 84, rx: 74, ry: 74, rough: 0, f: skin.sand },
        { o: 'arcs', x: 84, y: 84, r: [58, 58], n: 4, arc: 36, ph: -18, s: 'ink', lw: 5 }] },
      { k: 'knob', r: dx || dy ? 'knob pushed' : 'knob centered', i: [{ o: 'blob', x: 84 + dx, y: 84 + dy, rx: 30, ry: 30, rough: 0, f: skin.body }] }],
      bands: uniq([skin.sand, 'ink', skin.body]), change: ['joystick'], sound: 'NO_DATA', soundCause: 'joystick is silent', motion: 'follows the finger' };
  }

  function bytes(o) {
    var s = JSON.stringify(o);
    return typeof TextEncoder === 'function' ? new TextEncoder().encode(s).length : Buffer.byteLength(s, 'utf8');
  }

  var World = { worldSize: worldSize, tile: tile, homeAt: homeAt, places: places, isles: isles, starH: starH, iso: iso, route: route, walk: walk, counter: counter, clamp: clamp, clears: clears,
    seaFrame: seaFrame, crabState: crabState, crabRule: crabRule, islesFrame: islesFrame, groups: groups, standFrame: standFrame, namesFrame: namesFrame, stateFrame: stateFrame,
    castFrame: castFrame, castMeet: castMeet, wanderAt: wanderAt, canon: canon, codexScale: codexScale, headFrame: headFrame, joyFrame: joyFrame, bytes: bytes };
  if (typeof module === 'object' && module.exports) { module.exports = World; } else { root.PreceptorWorld = World; }
})(typeof module === 'object' && module.exports ? this : window);
