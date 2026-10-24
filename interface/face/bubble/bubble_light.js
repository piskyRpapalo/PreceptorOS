(function (root) {
  'use strict';
  var IS_NODE = typeof module === 'object' && !!module.exports;
  var STYLES = ['volume', 'etch', 'clear'];
  var HALF = 0.62, DOT_R = 2.4, DOT_EXP = 0.8, DOT_STEP = 6, EDGE_MIN = 3;
  var CAST = 5.6, HATCH_MID = 5, HATCH_DEEP = 3.5, HATCH_LW = 1.4;

  function rd(x) { return Math.round(x * 100) / 100; }
  function unit(x, y) { var n = Math.sqrt(x * x + y * y) || 1; return [x / n, y / n]; }

  function light3(l) { var n = Math.sqrt(l[0] * l[0] + l[1] * l[1] + 0.81); return [l[0] / n, l[1] / n, 0.9 / n]; }

  function ellipse(p) {
    var x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity, i;
    for (i = 0; i < p.length; i++) {
      x0 = Math.min(x0, p[i][0]); x1 = Math.max(x1, p[i][0]);
      y0 = Math.min(y0, p[i][1]); y1 = Math.max(y1, p[i][1]);
    }
    return { cx: (x0 + x1) / 2, cy: (y0 + y1) / 2, Rx: Math.max(1e-6, (x1 - x0) / 2), Ry: Math.max(1e-6, (y1 - y0) / 2) };
  }

  function inside(x, y, p) {
    var c = false, i, j;
    for (i = 0, j = p.length - 1; i < p.length; j = i++) {
      if ((p[i][1] > y) !== (p[j][1] > y) && x < (p[j][0] - p[i][0]) * (y - p[i][1]) / (p[j][1] - p[i][1]) + p[i][0]) { c = !c; }
    }
    return c;
  }
  function dist(x, y, p) {
    var best = Infinity, i, j;
    for (i = 0, j = p.length - 1; i < p.length; j = i++) {
      var ax = p[j][0], ay = p[j][1], dx = p[i][0] - ax, dy = p[i][1] - ay, l = dx * dx + dy * dy;
      var t = l > 0 ? Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / l)) : 0;
      best = Math.min(best, Math.hypot(ax + t * dx - x, ay + t * dy - y));
    }
    return best;
  }
  function bloqueado(x, y, cajas) {
    for (var i = 0; i < cajas.length; i++) { if (inside(x, y, cajas[i])) { return true; } }
    return false;
  }

  function lum(x, y, g, L3) {
    var nx = (x - g.cx) / g.Rx, ny = (y - g.cy) / g.Ry, nz = Math.sqrt(Math.max(0, 1 - nx * nx - ny * ny));
    return Math.max(0, nx * L3[0] + ny * L3[1] + nz * L3[2]);
  }

  function normals(p, g) {
    var n = p.length, out = [], i;
    for (i = 0; i < n; i++) {
      var a = p[(i + n - 1) % n], b = p[(i + 1) % n];
      var tx = b[0] - a[0], ty = b[1] - a[1], l = Math.sqrt(tx * tx + ty * ty) || 1;
      var nx = ty / l, ny = -tx / l;
      if (nx * (p[i][0] - g.cx) + ny * (p[i][1] - g.cy) < 0) { nx = -nx; ny = -ny; }
      out.push([nx, ny]);
    }
    return out;
  }

  function tramos(p, nr, L, cond, dentro) {
    var n = p.length, on = [], res = [], cur = [], i, s = -1, k;
    for (i = 0; i < n; i++) { on.push(cond(nr[i][0] * L[0] + nr[i][1] * L[1])); }
    var hacia = function (q) { return [p[q][0] - nr[q][0] * dentro, p[q][1] - nr[q][1] * dentro]; };
    if (on.every(Boolean)) {
      var todo = [];
      for (k = 0; k < n; k++) { todo.push(hacia(k)); }
      return [{ pts: todo, closed: true }];
    }
    for (i = 0; i < n; i++) { if (on[i] && !on[(i + n - 1) % n]) { s = i; break; } }
    if (s < 0) { return res; }
    for (i = 0; i < n; i++) {
      k = (s + i) % n;
      if (on[k]) { cur.push(hacia(k)); } else { if (cur.length > 1) { res.push({ pts: cur, closed: false }); } cur = []; }
    }
    if (cur.length > 1) { res.push({ pts: cur, closed: false }); }
    return res;
  }

  function bloqueadoDot(x, y, p, cajas) { return !inside(x, y, p) || dist(x, y, p) < EDGE_MIN || bloqueado(x, y, cajas); }

  function puntos(out, p, g, L3, o, cajas) {
    var c = DOT_STEP * Math.SQRT1_2, K = Math.ceil((g.Rx + g.Ry) / c) + 1, i, j;
    for (i = -K; i <= K; i++) {
      for (j = -K; j <= K; j++) {
        var x = g.cx + c * (i - j), y = g.cy + c * (i + j), l = lum(x, y, g, L3);
        if (!(l < HALF) || bloqueadoDot(x, y, p, cajas)) { continue; }
        out.push({ op: 'circle', x: rd(x), y: rd(y), r: rd(DOT_R * Math.pow((HALF - l) / HALF, DOT_EXP)), fill: o.ink, stroke: null, lw: 0, shadow: null, tag: 'dot' });
      }
    }
  }

  function vuelca(out, cur, ink) {
    if (cur.length > 1) { out.push({ op: 'path', d: 'M' + cur.join('L'), fill: null, stroke: ink, lw: HATCH_LW, shadow: null, tag: 'hatch' }); }
  }

  function rayas(out, p, g, L3, o, cajas) {
    var fams = [[HATCH_MID, HALF], [HATCH_DEEP, 0.35]], sq = Math.SQRT1_2;
    var diag = Math.sqrt(g.Rx * g.Rx + g.Ry * g.Ry) + 2;
    fams.forEach(function (f) {
      var K = Math.ceil(diag / f[0]), k, t;
      for (k = -K; k <= K; k++) {
        var cur = [];
        for (t = -diag; t <= diag; t += 2) {
          var x = g.cx + sq * (k * f[0] + t), y = g.cy + sq * (t - k * f[0]);
          if (lum(x, y, g, L3) < f[1] && !bloqueadoDot(x, y, p, cajas)) { cur.push(rd(x) + ' ' + rd(y)); }
          else { vuelca(out, cur, o.ink); cur = []; }
        }
        vuelca(out, cur, o.ink);
      }
    });
  }

  function apply(salida, contorno, opciones) {
    var o = opciones || {}, p = contorno || [];
    var style = o.style || 'volume';
    if (STYLES.indexOf(style) < 0) { throw new Error('bubble light: unknown style ' + style); }
    if (p.length < 3) { return salida; }
    if (typeof o.toPath !== 'function' || !Array.isArray(o.light)) { throw new Error('bubble light: faltan toPath o light'); }
    var L = unit(o.light[0], o.light[1]), L3 = light3(o.light), g = ellipse(p), nr = normals(p, g);
    var cajas = o.textBoxes || [], d = o.toPath(p, true);
    var lw = o.lw !== undefined ? o.lw : (o.depth === 0 ? 3.5 : 3.0);
    var off = [Math.round(-o.light[0] * CAST), Math.round(-o.light[1] * CAST)];
    salida.push({ op: 'path', d: o.toPath(p.map(function (q) { return [q[0] + off[0], q[1] + off[1]]; }), true), fill: o.shadow, stroke: null, lw: 0, shadow: null, tag: 'cast' });
    if (style !== 'clear') {
      salida.push({ op: 'path', d: d, fill: o.fill, stroke: null, lw: 0, shadow: null, tag: 'body' });
      if (style === 'volume') { puntos(salida, p, g, L3, o, cajas); } else { rayas(salida, p, g, L3, o, cajas); }
      tramos(p, nr, L, function (v) { return v < -0.35; }, 2.5).forEach(function (t) {
        salida.push({ op: 'path', d: o.toPath(t.pts, t.closed), fill: null, stroke: o.rim, lw: 2, shadow: null, tag: 'rim' });
      });
      if (o.highlight) {
        tramos(p, nr, L, function (v) { return v > 0.55; }, 4).forEach(function (t) {
          salida.push({ op: 'path', d: o.toPath(t.pts, t.closed), fill: null, stroke: o.highlight, lw: 3, shadow: null, tag: 'highlight' });
        });
      }
    }
    salida.push({ op: 'path', d: d, fill: null, stroke: o.stroke, lw: lw, shadow: null, tag: 'outline' });
    return salida;
  }

  var AtlasBubbleLight = Object.freeze({ apply: apply });
  if (IS_NODE) { module.exports = AtlasBubbleLight; } else { root.AtlasBubbleLight = AtlasBubbleLight; }
})(typeof module === 'object' && module.exports ? this : (this || window));
