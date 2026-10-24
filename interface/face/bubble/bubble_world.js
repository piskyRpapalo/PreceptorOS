(function (root) {
  'use strict';

  var PI = Math.PI, RAD = PI / 180;

  function num(v, d) { return typeof v === 'number' && isFinite(v) ? v : d; }
  function pair(v, d) { return Array.isArray(v) && v.length === 2 ? v : d; }

  function piece(o, props, f, s, lw, d) {
    var item = { o: o, f: f || null, s: s || null, d: d || 0 }, k;
    if (lw) { item.lw = lw; }
    for (k in props) { if (Object.prototype.hasOwnProperty.call(props, k)) { item[k] = props[k]; } }
    return item;
  }
  function disc(x, y, r, f, s, lw, d) { return piece('wave', { x: x, y: y, h: [[1, r, r, 0]] }, f, s, lw, d); }
  function strokeLine(pts, s, lw, d) { return piece('ribbon', { pts: pts, closed: false }, null, s, lw, d); }
  function closedShape(pts, f, s, lw, d) { return piece('ribbon', { pts: pts, closed: true }, f, s, lw, d); }

  function cityWord(p) {
    var xs = pair(p.x, [300, 412]), ys = pair(p.y, [30, 80]);
    var domes = Math.max(1, Math.floor(num(p.dome, 3)));
    var span = (xs[1] - xs[0]) / domes, y1 = ys[1], out = [];
    var i, k, cx, rho, hd, wx, wy, wr, arch;
    for (i = 0; i < domes; i++) {
      cx = xs[0] + (i + 0.5) * span;
      rho = 0.46 * span;
      hd = Math.min(rho * (0.9 + 0.15 * (i % 3)), ys[1] - ys[0]);
      arch = [];
      for (k = 0; k <= 6; k++) {
        arch.push([cx + rho * Math.cos(PI + PI * k / 6), y1 + hd * Math.sin(PI + PI * k / 6)]);
      }
      out.push(strokeLine(arch, 'cyan', 2.5, 2));

      wx = cx + (i % 2 ? 0.1 : -0.1) * rho;
      wy = y1 - hd * (0.3 + 0.15 * i);
      wr = 0.14 * rho;
      arch = [];
      for (k = 0; k <= 4; k++) {
        arch.push([wx + wr * Math.cos(PI + PI * k / 4), wy + wr * Math.sin(PI + PI * k / 4)]);
      }
      out.push(strokeLine(arch, 'cyan', 2.5, 2));
    }
    return out;
  }

  function reefWord(p) {
    var xs = pair(p.x, [0, 96]), ys = pair(p.y, [0, 515]);
    var x0 = xs[0], x1 = xs[1], W = x1 - x0, y0 = ys[0], y1 = ys[1], H = y1 - y0;
    var out = [], edge = [], k, t, wob;

    for (k = 0; k <= 12; k++) {
      t = k / 12;
      wob = 6 * Math.sin(2 * PI * t);
      edge.push([x1 + wob, y0 + H * t]);
    }
    out.push(closedShape([[x0, y0]].concat(edge, [[x0, y1]]), 'ocean', 'cyan', 2.5, 1));

    function fan(bx, by, len, angles) {
      angles.forEach(function (deg) {
        var ca = Math.cos(deg * RAD), sa = Math.sin(deg * RAD);
        var tip = [bx + len * ca, by + len * sa];
        var mid = [bx + 0.5 * len * ca - 0.08 * len * sa, by + 0.5 * len * sa + 0.08 * len * ca];
        out.push(strokeLine([[bx, by], mid, tip], 'cyan', 2.5, 2));
        out.push(disc(tip[0], tip[1], 2.5, 'cyan', null, null, 2));
      });
    }
    fan(x0 + 0.3 * W, y1 - 0.05 * H, 0.55 * W, [-125, -90, -55]);
    fan(x0 + 0.72 * W, y1 - 0.06 * H, 0.42 * W, [-118, -84, -50]);

    out.push(piece('blob', { x: x0 + 0.18 * W, y: y1 - 0.2 * H, rx: 0.07 * W, ry: 0.22 * H, rot: -8, seed: 'tubo-1', rough: 0.12 }, null, 'cyan', 2.5, 2));
    out.push(piece('blob', { x: x0 + 0.82 * W, y: y1 - 0.3 * H, rx: 0.06 * W, ry: 0.2 * H, rot: 6, seed: 'tubo-2', rough: 0.12 }, null, 'cyan', 2.5, 2));

    out.push(piece('wave', { x: x0 + 0.5 * W, y: y1 - 0.12 * H, h: [[1, 0.14 * W, 0.14 * W, 0], [8, 0.03 * W, 0.03 * W, 0]] }, null, 'cyan', 2.5, 2));
    return out;
  }

  function pileWord(p) {
    var xs = pair(p.x, [140, 300]), ys = pair(p.y, [318, 420]);
    var n = Math.max(1, Math.floor(num(p.n, 7))), rr = pair(p.r, [18, 30]);
    var rMax = Math.max(rr[0], rr[1]), hasSeed = typeof p.seed === 'string' && p.seed.length > 0;
    var cx = (xs[0] + xs[1]) / 2, Rx = Math.max(0, (xs[1] - xs[0]) / 2 - rMax);
    var cy = ys[1] - rMax, Ry = Math.max(0, (ys[1] - ys[0]) - 2 * rMax);
    var out = [], i, t, th, rad;
    for (i = 0; i < n; i++) {
      t = n === 1 ? 0.5 : i / (n - 1);
      th = PI + PI * t;
      rad = rr[0] + (rr[1] - rr[0]) * (((i * 5 + 3) % 7) / 6);
      out.push(piece('blob', { x: cx + Rx * Math.cos(th), y: cy + Ry * Math.sin(th), rx: rad, ry: 0.85 * rad,
        rot: 0, seed: hasSeed ? p.seed + ':' + i : 'pila:' + i, rough: 0.15 }, 'paper', 'ink', 2.5, 0));
    }
    return out;
  }

  function riftWord(p) {
    var x = num(p.x, 0), y = num(p.y, 0), w = num(p.w, 150), h = num(p.h, 26), pts = [], k, t;
    for (k = 0; k <= 6; k++) { t = k / 6; pts.push([x + w * (t - 0.5), y + h * Math.sin(PI * t)]); }
    for (k = 5; k >= 1; k--) { t = k / 6; pts.push([x + w * (t - 0.5), y + 0.25 * h * Math.sin(PI * t)]); }
    return [closedShape(pts, 'ink', 'cyan', 3.5, 0)];
  }

  function seamWord(p) {
    var x = num(p.x, 0), ys = pair(p.y, [60, 515]), gap = num(p.gap, 0), N = 8;
    var left = [], right = [], k, t, yy, xx;
    for (k = 0; k <= N; k++) {
      t = k / N;
      yy = ys[0] + (ys[1] - ys[0]) * t;
      xx = x + 12 * Math.sin(2 * PI * t);
      left.push([xx - gap / 2, yy]);
      right.push([xx + gap / 2, yy]);
    }
    return [
      closedShape(left.concat(right.slice().reverse()), 'ocean', null, null, 0),
      strokeLine(left, 'ink', 3.5, 0),
      strokeLine(right, 'ink', 3.5, 0)
    ];
  }

  function boingWord(p) {
    var arc = num(p.arc, 50), n = Math.max(1, Math.floor(num(p.n, 2)));
    return [piece('arcs', { x: num(p.x, 0), y: num(p.y, 0), r: [10, 16], n: n, arc: arc, ph: num(p.ph, -arc / 2) }, null, 'paper', 2.5, 0)];
  }

  function wobWord(p) {
    return [piece('arcs', { x: num(p.x, 0), y: num(p.y, 0), r: pair(p.r, [120, 136]),
      n: Math.max(1, Math.floor(num(p.n, 4))), arc: num(p.arc, 40), ph: num(p.ph, 0) }, null, 'cyan', 2.5, 0)];
  }

  var WORDS = {
    city: cityWord,
    reef: reefWord,
    pile: pileWord,
    rift: riftWord,
    seam: seamWord,
    boing: boingWord,
    wob: wobWord
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
  else { root.AtlasBubbleWorld = API; }
})(typeof module === 'object' && module.exports ? this : (this || window));
