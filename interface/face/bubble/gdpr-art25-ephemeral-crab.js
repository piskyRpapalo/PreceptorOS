(function (raiz) {
  'use strict';
  var K = (typeof module === 'object' && module.exports) ? require('./canon.js') : raiz.AtlasCanon;
  var TRAMO = 12;                       
  var BORDE = [0.06, 0.94];             
  var CLASES = { mar: [196, 62, 64], coral: [12, 82, 66] };

    function punto(semilla, k) {
    var g = K.generador(K.sha('atlas.cangrejo/1:' + semilla + ':' + k));
    return BORDE[0] + (BORDE[1] - BORDE[0]) * g.uniforme(10000) / 10000;
  }
    function paseo(semilla, ciclo, f) {
    var c = Math.max(0, Math.floor(ciclo || 0)), k = Math.floor(c / TRAMO);
    var a = punto(semilla, k), b = punto(semilla, k + 1);
    var u = ((c % TRAMO) + Math.max(0, Math.min(1, f || 0))) / TRAMO, s = u * u * (3 - 2 * u);
    return { x: a + (b - a) * s, dir: b >= a ? 1 : -1, tramo: k };
  }
    function forma(army, nodo, latido) {
    var n = Math.max(0, Math.floor(army || 0));
    return { escala: 1 + Math.min(1.2, n * 0.12), clase: nodo ? 'coral' : 'mar', tono: CLASES[nodo ? 'coral' : 'mar'],
             brillo: nodo && latido != null ? Math.max(0, Math.min(1, latido)) : null };
  }
    var PARTES = ['caparazon', 'pinzas', 'patas', 'ojos'], TOPES = { caparazon: 10, pinzas: 12, patas: 6, ojos: 3 };
  var DE = { caparazon: 'nucleo', pinzas: 'army', patas: 'bosque', ojos: 'faro' };
  function cuerpo(m) {
    var c = {};
    PARTES.forEach(function (p) {
      var v = m ? m[DE[p]] : null;
      c[p] = v == null || !isFinite(v) ? null : Math.max(0, Math.min(1, v / TOPES[p]));
    });
    return c;
  }
    var FESTON = { cupula: [6, 7], concha: [6, 11], aguja: [10, 6] };
  function onda(escala, cu, estilo) {
    var e = Math.round(10 * escala), p = cu && cu.pinzas != null ? cu.pinzas : 0, f = FESTON[estilo] || FESTON.cupula;
    return [[1, 40 + e, 26 + e, 0], [f[0], f[1], f[1], 0], [2, Math.round(9 + 9 * p), Math.round(4 + 4 * p), 1]];
  }
    function huellaPaseo(semilla, ciclos) {
    var xs = [];
    for (var c = 0; c < ciclos; c++) { xs.push(Math.round(paseo(semilla, c, 0).x * 1e6)); }
    return K.sha(JSON.stringify(xs));
  }

    function pinta(g, x, suelo, r, o) {
    var G = raiz.AtlasGacha;
    if (!G || !G.punto) { return null; }
    var cu = o.cuerpo || {}, fo = o.forma, rr = Math.max(6, r * fo.escala), dpr = o.dpr || 1, arm = onda(fo.escala, cu, o.estilo), n = 72, lim = 0;
    function niebla(p) { g.globalAlpha = cu[p] === null ? 0.35 : 1; g.setLineDash(cu[p] === null ? [3 * dpr, 3 * dpr] : []); }
    arm.forEach(function (h) { lim += Math.max(Math.abs(h[1]), Math.abs(h[2])); });
    var k = rr / lim, paso = o.quieto ? 0 : Math.sin((o.t || 0) * 0.012) * rr * 0.05, c = fo.tono, cy = suelo - rr * 0.55 + paso;
    g.save();
    g.translate(x, cy);
    if (o.dir < 0) { g.scale(-1, 1); }   
    if (fo.brillo) { g.shadowColor = 'hsla(' + c[0] + ' 90% 70% / ' + fo.brillo + ')'; g.shadowBlur = 16 * dpr * fo.brillo; }
    niebla('caparazon'); g.beginPath();
        for (var i = 0; i <= n; i++) { var p = G.punto(arm, i / n * Math.PI); g[i ? 'lineTo' : 'moveTo'](p[0] * k, -Math.abs(p[1]) * k * 0.9); }
    g.closePath();
    g.fillStyle = 'hsl(' + c[0] + ' ' + c[1] + '% ' + (c[2] - 8) + '%)'; g.fill();
    g.shadowBlur = 0;
    g.lineWidth = 2 * dpr; g.strokeStyle = 'hsl(' + c[0] + ' ' + c[1] + '% ' + Math.min(92, c[2] + 18) + '%)'; g.stroke();
        g.lineWidth = 1.6 * dpr; niebla('patas');
    var largo = rr * 0.5 * (0.6 + 0.8 * (cu.patas || 0));
    for (var l = 0; l < 6; l++) {
      var lx = (l - 2.5) / 2.5 * rr * 0.85, alt = o.quieto ? 0 : Math.sin((o.t || 0) * 0.02 + l * 1.7) * rr * 0.08;
      g.beginPath(); g.moveTo(lx * 0.8, 0); g.lineTo(lx, largo + alt); g.stroke();
    }
        g.fillStyle = '#f2f4f8'; niebla('ojos');
    var alto = 0.75 + 0.45 * (cu.ojos || 0);
    [[0.32, alto], [0.58, alto - 0.07]].forEach(function (e) {
      g.beginPath(); g.moveTo(e[0] * rr, -0.55 * rr); g.lineTo(e[0] * rr, -e[1] * rr); g.stroke();
      g.beginPath(); g.arc(e[0] * rr, -e[1] * rr, 2.6 * dpr, 0, 2 * Math.PI); g.fill();
    });
    g.globalAlpha = 1; g.setLineDash([]);
    g.restore();
    var d = o.dir < 0 ? -1 : 1;
    return { radio: rr, caparazon: [x, cy - rr * 0.35], pinzas: [x + d * rr * 0.95, cy - rr * 0.1],
             patas: [x - d * rr * 0.5, suelo - rr * 0.55 + paso + largo], ojos: [x + d * rr * 0.45, cy - alto * rr] };
  }

  var AtlasCangrejo = { TRAMO: TRAMO, PARTES: PARTES, paseo: paseo, forma: forma, cuerpo: cuerpo, onda: onda, huellaPaseo: huellaPaseo, pinta: pinta };
  if (typeof module === 'object' && module.exports) { module.exports = AtlasCangrejo; }
  else { raiz.AtlasCangrejo = AtlasCangrejo; }
})(this);
