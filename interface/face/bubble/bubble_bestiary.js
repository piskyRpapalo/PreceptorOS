(function (root) {
  'use strict';

  var PI = Math.PI, RAD = PI / 180;
  var PHASE_UNIT = PI / 32;
  var EMBLEM = [[1, 24, 24, 0], [-3, 13, 13, 44], [9, 3, 3, 40]];
  var EYE_STATES = ['up', 'open', 'shut'];

  function num(v, d) { return typeof v === 'number' && isFinite(v) ? v : d; }
  function pair(v, d) { return Array.isArray(v) && v.length === 2 ? v : d; }
  function clamp(v, lo, hi) { return Math.min(hi, Math.max(lo, v)); }
  function stateOf(v) { return EYE_STATES.indexOf(v) >= 0 ? v : 'open'; }
  function copyPts(pts) { return pts.map(function (q) { return [q[0], q[1]]; }); }

  function piece(o, props, f, s, lw, d) {
    var item = { o: o, f: f || null, s: s || null, d: d || 0 }, k;
    if (lw) { item.lw = lw; }
    for (k in props) { if (Object.prototype.hasOwnProperty.call(props, k)) { item[k] = props[k]; } }
    return item;
  }
  function disc(x, y, r, f, s, lw, d) { return piece('wave', { x: x, y: y, h: [[1, r, r, 0]] }, f, s, lw, d); }
  function strokeLine(pts, s, lw, d) { return piece('ribbon', { pts: pts, closed: false }, null, s, lw, d); }
  function closedShape(pts, f, s, lw, d) { return piece('ribbon', { pts: pts, closed: true }, f, s, lw, d); }

  function harmonicPoint(h, u) {
    var x = 0, y = 0, i, f;
    for (i = 0; i < h.length; i++) {
      f = h[i][0] * u + h[i][3] * PHASE_UNIT;
      x += h[i][1] * Math.cos(f);
      y += h[i][2] * Math.sin(f);
    }
    return [x, y];
  }

  function eyeItems(x, y, re, state, d) {
    if (state === 'shut') { return [strokeLine([[x - re, y], [x + re, y]], 'ink', 2.2, d)]; }
    var py = state === 'up' ? y - 0.5 * re : y;
    return [disc(x, y, re, 'paper', 'ink', 1.2, d), disc(x, py, 0.43 * re, 'ink', null, null, d)];
  }

  function crabWord(p) {
    var x = num(p.x, 0), y = num(p.y, 0), rr = num(p.rr, 40), dir = p.dir === -1 ? -1 : 1;
    var state = stateOf(p.eye), out = [], pts, s, j, k, up, arm, cu, cv, g, a, stalk, R = 0.27, lim = 0, scale, i, q;
    function X(u) { return x + dir * u * rr; }
    function Y(v) { return y + v * rr; }

    for (s = -1; s <= 1; s += 2) {
      for (j = 0; j <= 2; j++) {
        pts = [[X(s * (0.6 + 0.08 * j)), Y(0.08 * j)], [X(s * (1.02 + 0.1 * j)), Y(-0.3 + 0.1 * j)], [X(s * (1.14 + 0.12 * j)), Y(0.45)]];
        out.push(strokeLine(pts, 'ink', 4.6, 0), strokeLine(copyPts(pts), 'cyan', 2.2, 0));
      }
    }

    for (s = -1; s <= 1; s += 2) {
      up = s === 1 ? 0.12 : 0;
      arm = [[X(s * 0.62), Y(-0.22)], [X(s * 0.92), Y(-0.42 - up / 2)], [X(s * 1.0), Y(-0.62 - up)]];
      out.push(strokeLine(arm, 'ink', 7, 0), strokeLine(copyPts(arm), 'cyan', 3.8, 0));
      cu = s * 1.02;
      cv = -0.86 - up;
      g = s === 1 ? -110 : -70;
      pts = [];
      for (k = 0; k <= 18; k++) {
        a = (g + 28 + 304 * k / 18) * RAD;
        pts.push([X(cu + R * Math.cos(a)), Y(cv + R * Math.sin(a))]);
      }
      pts.push([X(cu + 0.18 * R * Math.cos(g * RAD)), Y(cv + 0.18 * R * Math.sin(g * RAD))]);
      out.push(closedShape(pts, 'cyan', 'ink', 3.2, 0));
    }

    out.push(piece('wave', { x: x, y: Y(0.02), h: [[1, 0.82 * rr, 0.46 * rr, 0]] }, 'cyan', 'ink', 3.2, 0));

    for (i = 0; i < EMBLEM.length; i++) { lim += Math.max(Math.abs(EMBLEM[i][1]), Math.abs(EMBLEM[i][2])); }
    scale = 0.2 * rr / lim;
    pts = [];
    for (i = 0; i < 48; i++) {
      q = harmonicPoint(EMBLEM, i / 48 * 2 * PI);
      pts.push([x + dir * q[0] * scale, y - 0.16 * rr + q[1] * scale]);
    }
    out.push(closedShape(pts, null, 'ink', 2, 0));

    out.push(strokeLine([[X(-0.12), Y(0.12)], [X(0), Y(0.2)], [X(0.12), Y(0.12)]], 'ink', 2.2, 0));

    for (s = -1; s <= 1; s += 2) {
      stalk = [[X(s * 0.2), Y(-0.38)], [X(s * 0.24), Y(-0.6)], [X(s * 0.28), Y(-0.74)]];
      out.push(strokeLine(stalk, 'ink', 4.2, 0), strokeLine(copyPts(stalk), 'cyan', 1.8, 0));
      out = out.concat(eyeItems(X(s * 0.28), Y(-0.84), 0.14 * rr, state, 0));
    }
    return out;
  }

  function starWord(p) {
    var x = num(p.x, 0), y = num(p.y, 0), r = num(p.r, 22), state = stateOf(p.eye);
    var body = piece('wave', { x: x, y: y, h: [[1, r, r, 0], [-4, 0.3 * r, 0.3 * r, 0]] }, 'cyan', 'ink', 3.2, 0);
    return [body].concat(eyeItems(x - 0.28 * r, y - 0.04 * r, 0.2 * r, state, 0),
      eyeItems(x + 0.28 * r, y - 0.04 * r, 0.2 * r, state, 0));
  }

  function snailWord(p) {
    var x = num(p.x, 0), y = num(p.y, 0), r = num(p.r, 16), state = stateOf(p.eye), out = [];
    var cx = x - 0.25 * r, cy = y - 0.35 * r, spiral = [], k, th, rho, stalks, i;
    for (k = 0; k <= 18; k++) {
      th = k / 18 * 5 * PI;
      rho = 0.08 * r + (0.5 * r - 0.08 * r) * k / 18;
      spiral.push([cx + rho * Math.cos(th), cy + rho * Math.sin(th)]);
    }
    out.push(piece('blob', { x: cx, y: cy, rx: 0.55 * r, ry: 0.55 * r, rot: 0, seed: 'concha', rough: 0.05 }, 'cyan', 'ink', 3.2, 0));
    out.push(strokeLine(spiral, 'ink', 2.5, 0));
    out.push(piece('blob', { x: x + 0.1 * r, y: y + 0.42 * r, rx: r, ry: 0.34 * r, rot: 0, seed: 'cuerpo', rough: 0.1 }, 'cyan', 'ink', 3.2, 0));
    stalks = [
      [[x + 0.5 * r, y + 0.2 * r], [x + 0.6 * r, y - 0.2 * r], [x + 0.56 * r, y - 0.55 * r]],
      [[x + 0.72 * r, y + 0.2 * r], [x + 0.82 * r, y - 0.1 * r], [x + 0.9 * r, y - 0.42 * r]]
    ];
    for (i = 0; i < stalks.length; i++) {
      out.push(strokeLine(stalks[i], 'ink', 2.2, 0));
      out = out.concat(eyeItems(stalks[i][2][0], stalks[i][2][1], 0.2 * r, state, 0));
    }
    return out;
  }

  function octoWord(p) {
    var x = num(p.x, 0), y = num(p.y, 0), r = num(p.r, 20), state = stateOf(p.eye), out = [];
    var i, k, dx, side, p0, p1, p2, c, th, rho, pts;
    for (i = 0; i < 6; i++) {
      dx = (i - 2.5) / 2.5 * 0.8 * r;
      side = dx < 0 ? -1 : 1;
      p0 = [x + dx * 0.5, y + 0.55 * r];
      p1 = [x + dx * 1.1, y + 0.9 * r];
      p2 = [x + dx * 1.2, y + 1.15 * r];
      c = [p2[0] + 0.12 * r * side, p2[1]];
      pts = [p0, p1, p2];
      for (k = 0; k <= 4; k++) {
        th = PI * (0.2 + 1.3 * k / 4);
        rho = 0.14 * r * (1 - 0.6 * k / 4);
        pts.push([c[0] + rho * Math.cos(th), c[1] + rho * Math.sin(th)]);
      }
      out.push(strokeLine(pts, 'ink', 3.2, 0));
    }
    out.push(piece('blob', { x: x, y: y - 0.15 * r, rx: r, ry: 0.9 * r, rot: 0, seed: 'cabeza', rough: 0.15 }, 'cyan', 'ink', 3.2, 0));
    return out.concat(eyeItems(x - 0.38 * r, y - 0.2 * r, 0.2 * r, state, 0),
      eyeItems(x + 0.38 * r, y - 0.2 * r, 0.2 * r, state, 0));
  }

  function fishWord(p) {
    return [piece('wave', { x: num(p.x, 0), y: num(p.y, 0), sc: num(p.sc, 1), h: [[1, 10, 5, 0], [2, 2, 2, 16]] }, null, 'cyan', 2.5, 2)];
  }

  function troopWord(p) {
    var x = num(p.x, 0), y = num(p.y, 0), r = num(p.r, 12), ph = num(p.ph, 0);
    return [
      piece('wave', { x: x, y: y, sc: r / 6, h: [[1, 6, 6, ph], [3, 2, 2, ph], [5, 1, 1, ph]] }, 'ocean', 'cyan', 2.5, 0),
      disc(x - 0.3 * r, y - 0.1 * r, 0.2 * r, 'paper', null, null, 0),
      disc(x + 0.3 * r, y - 0.1 * r, 0.2 * r, 'paper', null, null, 0)
    ];
  }

  function bustWord(p) {
    var x = num(p.x, 0), y = num(p.y, 0), r = num(p.r, 64), rot = num(p.rot, 0), sq = pair(p.sq, [1, 1]);
    var sx = clamp(num(sq[0], 1), 0.88, 1.12), sy = clamp(num(sq[1], 1), 0.88, 1.12);
    var cs = Math.cos(rot * RAD), sn = Math.sin(rot * RAD), out = [], i, k, a, u, ring, pts, circ, rizos, rizosBarba;
    var opened = p.eye === 'open';
    var cybState = p.cybEye === 'violet' || p.cybEye === 'shut' ? p.cybEye : (opened ? 'violet' : 'shut');
    var marbleState = p.mEye === 'open' || p.mEye === 'happy' || p.mEye === 'shut' ? p.mEye : (opened ? 'open' : 'shut');
    var mouth = p.mouth === 'o' || p.mouth === 'smile' ? p.mouth : 'closed';
    var TR = cybState === 'violet' ? 'FIRMADO.base' : 'cyan';
    function T(u0, v0) { var ua = u0 * sx, vb = v0 * sy; return [x + ua * cs - vb * sn, y + ua * sn + vb * cs]; }
    function P(q) { return T(q[0] * r, q[1] * r); }
    function shape(list, f, s, lw) { return piece('ribbon', { pts: list.map(P), closed: true }, f, s, lw, 0); }
    function path(list, s, lw) { return piece('ribbon', { pts: list.map(P), closed: false }, null, s, lw, 0); }
    function dot(du, dv, rad, f, s, lw) {
      var c = P([du, dv]);
      return piece('wave', { x: c[0], y: c[1], rot: rot, h: [[1, rad * r * sx, rad * r * sy, 0]] }, f, s, lw, 0);
    }
    function festoon(cu, cv, ru, rv, a0, a1, bumps, depth, taper) {
      var n = bumps * 3, list = [], j, tt, aa, fe, tp;
      for (j = 0; j <= n; j++) {
        tt = j / n; aa = (a0 + (a1 - a0) * tt) * RAD;
        fe = 1 - depth + 2 * depth * Math.abs(Math.sin(PI * bumps * tt));
        tp = 1 - taper * Math.max(0, Math.sin(aa));
        list.push([cu + ru * fe * tp * Math.cos(aa), cv + rv * fe * Math.sin(aa)]);
      }
      return list;
    }
    function spiral(cu, cv, a0) {
      var list = [], j, tt, aa, rh;
      for (j = 0; j < 8; j++) {
        tt = j / 7; aa = (a0 + 486 * tt) * RAD; rh = 0.08 * (1 - 0.8 * tt);
        list.push([cu + rh * Math.cos(aa), cv + rh * Math.sin(aa)]);
      }
      return list;
    }

    out.push(shape([[0, -0.92], [0.42, -0.86], [0.6, -0.6], [0.64, -0.3], [0.62, 0], [0.52, 0.32], [0.34, 0.6], [0, 0.72], [-0.34, 0.6], [-0.52, 0.32], [-0.62, 0], [-0.64, -0.3], [-0.6, -0.6], [-0.42, -0.86]], 'paper', 'ink', 3.5));
    out.push(shape([[0.06, -0.84], [0.4, -0.86], [0.6, -0.66], [0.66, -0.36], [0.63, -0.04], [0.5, 0.12], [0.3, 0.12], [0.18, -0.04], [0.13, -0.2], [0.07, -0.36], [0.05, -0.6]], 'ink', 'ink', 3));
    out.push(shape(festoon(0, 0.16, 0.68, 0.72, 213, -33, 15, 0.02, 0).concat([[0.52, -0.22], [0.48, 0.04], [0.32, 0.2], [0.14, 0.24], [0, 0.26], [-0.14, 0.24], [-0.32, 0.2], [-0.48, 0.04], [-0.52, -0.22]]), 'paper', 'ink', 3.5));
    out.push(shape([[0, 0.2], [0.12, 0.18], [0.24, 0.22], [0.31, 0.32], [0.22, 0.29], [0.11, 0.29], [0, 0.26], [-0.11, 0.29], [-0.22, 0.29], [-0.31, 0.32], [-0.24, 0.22], [-0.12, 0.18]], 'paper', 'ink', 2.8));
    if (mouth === 'o') { out.push(dot(0, 0.4, 0.065, 'ink', null, null)); }
    else if (mouth === 'smile') { out.push(path([[-0.12, 0.4], [0, 0.46], [0.12, 0.4]], 'ink', 2.5)); }
    else { out.push(path([[-0.08, 0.38], [0, 0.395], [0.08, 0.38]], 'ink', 2.5)); }

    pts = festoon(0, -0.64, 0.92, 0.88, 152, 388, 26, 0.022, 0.22).concat([[0.62, -0.3], [0.56, -0.5], [0.58, -0.68]]);
    for (k = 0; k <= 16; k++) { u = 0.5 - k / 16; pts.push([u, -0.8 + 0.08 * Math.abs(Math.sin(PI * (0.5 - u) / 0.25))]); }
    out.push(shape(pts.concat([[-0.58, -0.68], [-0.56, -0.5], [-0.62, -0.3]]), 'paper', 'ink', 3.5));

    out.push(path([[-0.54, -0.46], [-0.36, -0.55], [-0.14, -0.5]], 'ink', 3.2));
    out.push(path([[-0.03, -0.44], [-0.01, -0.15], [0.03, 0.07], [0, 0.14], [-0.1, 0.13]], 'ink', 2.5));
    out.push(path([[-0.56, -0.14], [-0.44, -0.08], [-0.32, -0.09]], 'ink', 2));

    if (marbleState === 'open') {
      out.push(shape([[-0.45, -0.33], [-0.32, -0.39], [-0.19, -0.33], [-0.32, -0.28]], 'paper', 'ink', 2), dot(-0.32, -0.335, 0.045, 'ink', null, null));
    } else if (marbleState === 'happy') {
      out.push(path([[-0.44, -0.3], [-0.32, -0.38], [-0.2, -0.3]], 'ink', 2.5));
    } else {
      out.push(path([[-0.44, -0.34], [-0.32, -0.29], [-0.2, -0.34]], 'ink', 2.5));
    }

    ring = [];
    for (k = 0; k < 16; k++) { a = 22.5 * k * RAD; ring.push([0.33 + 0.16 * Math.cos(a), -0.35 + 0.16 * Math.sin(a)]); }
    out.push(shape(ring, null, TR, 2.2));
    if (cybState === 'violet') {
      out.push(dot(0.33, -0.35, 0.12, 'FIRMADO.base', 'ink', 2), dot(0.29, -0.39, 0.04, 'paper', null, null));
    } else {
      out.push(shape([[0.2, -0.35], [0.33, -0.41], [0.46, -0.35], [0.33, -0.29]], 'paper', 'ink', 2), path([[0.21, -0.35], [0.33, -0.32], [0.45, -0.35]], 'ink', 1.8));
    }

    circ = [[[0.1, -0.7], [0.1, -0.5], [0.15, -0.32], [0.2, -0.12], [0.26, 0.02]], [[0.4, -0.21], [0.44, -0.1], [0.44, 0.02]], [[0.38, -0.5], [0.44, -0.58], [0.44, -0.7]]];
    for (i = 0; i < circ.length; i++) {
      pts = circ[i];
      out.push(path(pts, TR, 2), dot(pts[pts.length - 1][0], pts[pts.length - 1][1], 0.032, TR, null, null));
    }

    out.push(dot(0.2, -0.68, 0.028, 'paper', null, null), dot(0.5, -0.58, 0.028, 'paper', null, null));

    rizos = [[-0.27, -1.36], [0, -1.36], [0.27, -1.36], [-0.405, -1.16], [-0.135, -1.16], [0.135, -1.16], [0.405, -1.16], [-0.54, -0.96], [-0.27, -0.96], [0, -0.96], [0.27, -0.96], [0.54, -0.96], [-0.675, -0.76], [0.675, -0.76], [-0.76, -0.62], [0.76, -0.62], [-0.7, -0.38], [0.7, -0.38]];
    for (i = 0; i < rizos.length; i++) { out.push(path(spiral(rizos[i][0], rizos[i][1], (i * 97) % 360), 'ink', 1.8)); }

    rizosBarba = [[-0.56, 0.06], [0.58, 0.06], [-0.36, 0.52], [-0.12, 0.56], [0.12, 0.56], [0.36, 0.52], [-0.22, 0.72], [0.22, 0.72]];
    for (i = 0; i < rizosBarba.length; i++) {
      pts = [];
      for (k = 0; k <= 6; k++) { a = (200 + 220 * k / 6) * RAD; pts.push([rizosBarba[i][0] + 0.06 * Math.cos(a), rizosBarba[i][1] + 0.06 * Math.sin(a)]); }
      out.push(path(pts, 'ink', 1.8));
    }
    return out;
  }

  var WORDS = {
    bust: bustWord,
    crab: crabWord,
    star: starWord,
    snail: snailWord,
    octo: octoWord,
    fish: fishWord,
    troop: troopWord
  };

  var core = null;
  if (typeof module === 'object' && module.exports) {
    try { core = require('./bubble_language.js'); } catch (e) { core = null; }
  } else {
    core = root.AtlasBubble || null;
  }
  if (core && typeof core.define === 'function') {
    Object.keys(WORDS).forEach(function (name) { core.define(name, WORDS[name]); });
  }

  var API = { WORDS: WORDS };
  if (typeof module === 'object' && module.exports) { module.exports = API; }
  else { root.AtlasBubbleBestiary = API; }
})(typeof module === 'object' && module.exports ? this : (this || window));
