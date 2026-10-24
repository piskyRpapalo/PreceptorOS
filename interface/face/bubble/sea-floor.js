(function (raiz) {
  'use strict';

    var TIERRA = [[12, 51, 57], [14, 76, 82], [14, 96, 104], [32, 112, 108], [32, 124, 116], [48, 151, 128], [70, 178, 166]];
  var NIEBLA = [null, [64, 72, 96]], TESELA = 240, RES = 4;


    function deriva(t) { return [Math.sin(t * 0.00011) * 10, Math.cos(t * 0.00009) * 10]; }

    function lecho(x, y, E) {
    var cx = Math.floor(x / 320), cy = Math.floor(y / 280), px = x / 320 - cx, py = y / 280 - cy;
    var hx = E.hash(cx, cy, 71), hy = E.hash(cx, cy, 97), rx = 0.22 + E.hash(cx, cy, 131) * 0.13;
    var ry = 0.2 + E.hash(cx, cy, 173) * 0.12, dx = (px - 0.25 - hx * 0.5) / rx, dy = (py - 0.25 - hy * 0.5) / ry;
    var d = dx * dx + dy * dy, r = Math.max(0, Math.min(1, (1.18 - d) * 1.35));
    return r * r * (3 - 2 * r);
  }
    function texturaLecho(E, i, j, n) {
    var c = raiz.document.createElement('canvas'); c.width = c.height = n;
    var g = c.getContext('2d'), im = g.createImageData(n, n), k = 0;
    for (var y = 0; y < n; y++) { for (var x = 0; x < n; x++) {
      var wx = i * TESELA + x * RES, wy = j * TESELA + y * RES;
      var bed = lecho(wx, wy, E), shade = lecho(wx - 38, wy - 44, E);
      var v = Math.max(0, Math.min(1, 0.2 + E.fbm(wx / 350, wy / 350, 11) * 0.08 + bed * 0.22 + E.fbm(wx / 88, wy / 88, 4) * 0.08 - shade * 0.035));
      var p = TIERRA[Math.round(v * (TIERRA.length - 1))];
      im.data[k++] = p[0]; im.data[k++] = p[1]; im.data[k++] = p[2]; im.data[k++] = 255;
    } }
    g.putImageData(im, 0, 0); return c;
  }

    var TOPE = 220;
  function suelta(c) { for (var k in c) { delete c[k]; return; } }
  function pintor() {
    var E = raiz.AtlasEscena, N = raiz.AtlasNiebla, C = raiz.AtlasCamara, R = raiz.AtlasMarRift;
    var estilo = R && typeof R.textura === 'function' ? R : null, paletaNiebla = estilo && estilo.niebla ? [null, estilo.niebla] : NIEBLA;
    var tierra = {}, nt = 0, nieblas = {}, nn = 0, huella = '', circ = [];
    function tesela(i, j) {
      var k = i + ',' + j;
      if (tierra[k]) { return tierra[k]; }
      if (nt >= TOPE) { suelta(tierra); nt--; }
      var n = TESELA / RES;
      tierra[k] = estilo ? estilo.textura(E, i, j, n, raiz.document) : texturaLecho(E, i, j, n);
      nt++;
      return tierra[k];
    }
    function bruma(i, j) {
      var k = i + ',' + j;
      if (nieblas[k] !== undefined) { return nieblas[k]; }
      if (nn >= TOPE) { suelta(nieblas); nn--; }
      var n = TESELA / RES, algo = false;
      var t = E.textura(n, n, function (x, y) {
        var v = N.niebla(i * TESELA + x * RES, j * TESELA + y * RES, circ) * 0.78;
        if (v > 0.05) { algo = true; }
        return v;
      }, paletaNiebla);
      nieblas[k] = algo ? t : null; nn++;
      return nieblas[k];
    }
        function capas(g, cam, W, H, z, que, dx, dy) {
      var v = C.vista(cam, W, H, z), m = C.matriz(z), n = TESELA / RES;
      g.save();
      for (var i = Math.floor((v.x0 - dx) / TESELA); i <= Math.floor((v.x1 - dx) / TESELA); i++) {
        for (var j = Math.floor((v.y0 - dy) / TESELA); j <= Math.floor((v.y1 - dy) / TESELA); j++) {
          var p = C.aPantalla(cam, W, H, z, i * TESELA + dx, j * TESELA + dy), lado = TESELA * m[0], alto = TESELA * m[1];
                    if (p[0] + lado < 0 || p[0] - lado > W || p[1] > H || p[1] + 2 * alto < 0) { continue; }
          var t = que(i, j);
          if (t) { g.imageSmoothingEnabled = true; g.setTransform(m[0] * RES, m[1] * RES, m[2] * RES, m[3] * RES, p[0], p[1]); g.drawImage(t, 0, 0, n + 0.6, n + 0.6); }
        }
      }
      g.restore();
    }
    return {
            despejado: function (c) { var h = N.huella(c); if (h !== huella) { huella = h; nieblas = {}; nn = 0; } circ = c; },
      tierra: function (g, cam, W, H, z, d) { capas(g, cam, W, H, z, tesela, d ? d[0] : 0, d ? d[1] : 0); },
      niebla: function (g, cam, W, H, z) { capas(g, cam, W, H, z, bruma, 0, 0); }
    };
  }

  var AtlasMarFondo = { TESELA: TESELA, RES: RES, deriva: deriva, lecho: lecho, pintor: pintor };
  if (typeof module === 'object' && module.exports) { module.exports = AtlasMarFondo; }
  else { raiz.AtlasMarFondo = AtlasMarFondo; }
})(this);
