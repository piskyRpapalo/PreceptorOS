(function (raiz) {
  'use strict';
  var EN_NODE = typeof module === 'object' && module.exports;
  var V = EN_NODE ? require('./valores.js') : raiz.AtlasValores;
  var G = EN_NODE ? require('./gacha.js') : raiz.AtlasGacha;
  var K = EN_NODE ? require('./canon.js') : raiz.AtlasCanon;
  var ES = V.escuadron, AUREO = Math.PI * (3 - Math.sqrt(5)), CAMINOS = {}, nc = 0;

    function cuantas(n) { return n > 12 ? ES.coloso : Math.max(1, Math.min(ES.tope, Math.round(ES.por_aristas / n))); }
    function vivas(n, vida, max) { return vida <= 0 || !max ? 0 : Math.max(1, Math.ceil(n * vida / max)); }

    function sitios(n, semilla, forma) {
    var g = G.generador(K.sha('atlas.escuadron/1:' + semilla)), out = [[0, 0]];
    for (var i = 1; i < n; i++) {
      var r = Math.sqrt(i / n) * ES.radio, a = i * AUREO + (g.mil() - 500) / 4000, x = Math.cos(a) * r, y = Math.sin(a) * r;
      if (forma === 'agresiva') { x = x * 0.7 + Math.abs(y) * 0.35; }
      else if (forma === 'defensiva') { var k = ES.radio * 0.8 / Math.max(0.3, Math.sqrt(x * x + y * y)); x *= k; y *= k; }
      else if (forma === 'flanqueo') { y = y * 1.35 + (y < 0 ? -0.5 : 0.5); x *= 0.6; }
      out.push([Math.round(x * 1000) / 1000, Math.round(y * 1000) / 1000]);
    }
    return out;
  }

    function camino(t) {
    var k = t.semilla;
    if (CAMINOS[k]) { return CAMINOS[k]; }
    if (nc > 64) { CAMINOS = {}; nc = 0; }
    var arm = G.lod(t), lim = 0, p = new raiz.Path2D();
    arm.forEach(function (h) { lim += Math.max(Math.abs(h[1]), Math.abs(h[2])); });
    for (var i = 0; i <= 48; i++) { var q = G.punto(arm, i / 48 * 2 * Math.PI); p[i ? 'lineTo' : 'moveTo'](q[0] / lim, -q[1] / lim); }
    nc++; CAMINOS[k] = p;
    return p;
  }

    function pinta(g, u, o) {
    if (!raiz.Path2D || !raiz.DOMMatrix || !u.t) { return 0; }
    var n = cuantas(u.t.aristas || G.aristas(u.t)), v = vivas(n, u.vida, u.max);
    if (v < 2 || o.alfa <= 0) { return v; }
    var C = raiz.AtlasCasa, forma = C && C.casa ? C.casa().formacion : null, S = sitios(n, u.t.semilla, forma), p = camino(u.t);
    var lote = new raiz.Path2D(), s = o.r * ES.unidad, c = Math.cos(o.giro || 0) * s, sn = Math.sin(o.giro || 0) * s, lado = u.lado ? -1 : 1;
    for (var i = 1; i < v; i++) {
      var bx = o.quieto ? 0 : Math.sin((o.t || 0) * 0.003 + i) * o.r * 0.06;
      lote.addPath(p, new raiz.DOMMatrix([c, sn, -sn, c, u.x + S[i][0] * o.r * lado + bx, u.y + S[i][1] * o.r]));
    }
    g.save(); g.globalAlpha = o.alfa * 0.8; g.strokeStyle = u.color; g.lineWidth = 1.2 * (o.dpr || 1); g.stroke(lote); g.restore();
    return v;
  }

  var AtlasEscuadron = { cuantas: cuantas, vivas: vivas, sitios: sitios, pinta: pinta };
  if (EN_NODE) { module.exports = AtlasEscuadron; } else { raiz.AtlasEscuadron = AtlasEscuadron; }
})(this);
