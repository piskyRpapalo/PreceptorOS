(function (raiz) {
  'use strict';
      var SEM = (typeof module === 'object' && module.exports) ? require('./tabla_semantica.js') : raiz.AtlasSemantica;
  if (!SEM || !SEM.SELLOS) { throw new Error('NO_DATA · tabla_semantica.js no cargada: la tabla semantica manda, no se duplica'); }
  var SELLOS = SEM.SELLOS;
  var LUZ = { x: -0.6, y: -0.8 }, MORF_MS = 2000;
  var morfos = {}, narrado = {};

    function bandas(h, s, l) {
    function c(L) { return 'hsl(' + h + ' ' + s + '% ' + Math.max(4, Math.min(94, L)) + '%)'; }
    return { h: h, brillo: c(l + 16), base: c(l), sombra: c(l - 20), contorno: c(l - 44) };
  }
    function deSello(sello) { return SELLOS.hasOwnProperty(sello) ? bandas(SELLOS[sello], 70, 55) : null; }
    function morf(a, b, p) {
    var n = Math.max(a.length, b.length), r = [];
    for (var i = 0; i < n; i++) {
      var x = a[i] || [b[i][0], 0, 0, b[i][3]], y = b[i] || [a[i][0], 0, 0, a[i][3]];
      r.push([y[0], x[1] + (y[1] - x[1]) * p, x[2] + (y[2] - x[2]) * p, x[3] + (y[3] - x[3]) * p]);
    }
    return r;
  }
    function ondaVista(id, destino, t, quieto) {
    var m = morfos[id], j = JSON.stringify(destino);
    if (!m) { morfos[id] = { de: destino, a: destino, j: j, t0: t }; return destino; }
    if (m.j !== j) {
      var vista = ondaVista(id, m.a, t, quieto);
      morfos[id] = { de: vista, a: destino, j: j, t0: t };
      if (id === 'yo' && !quieto) { narra('shape changes (harmonic morph, 2 s)'); }
    }
    m = morfos[id];
    if (quieto || !t) { return m.a; }
    var p = Math.max(0, Math.min(1, (t - m.t0) / MORF_MS));
    return p >= 1 ? m.a : morf(m.de, m.a, p * p * (3 - 2 * p));
  }
  function narra(texto) {
    var R = raiz.AtlasRadioChat;
    if (R && R.dice && narrado.ultimo !== texto) { narrado.ultimo = texto; R.dice({ quien: 'Your crab', fuente: 'toon', texto: texto, sello: 'LIVE' }); }
  }
    function parpadea(ciclo, t, quieto) { return !quieto && ciclo != null && ciclo % 4 === 0 && (t % 1000) < 150; }

  function cangrejo(g, x, suelo, r, o) {
    var CJ = raiz.AtlasCangrejo, G = raiz.AtlasGacha;
    if (!CJ || !G || !G.punto) { return null; }
    var cu = o.cuerpo || {}, fo = o.forma, rr = Math.max(6, r * fo.escala), dpr = o.dpr || 1, q = !!o.quieto, t = o.t || 0;
    var arm = ondaVista(o.id || 'yo', CJ.onda(fo.escala, cu, o.estilo), t, q), n = 72, lim = 0, c = fo.tono, B = bandas(c[0], c[1], c[2] - 6);
    arm.forEach(function (h) { lim += Math.max(Math.abs(h[1]), Math.abs(h[2])); });
    var k = rr / lim, vaiven = q ? 0 : Math.sin(t * 0.012) * rr * 0.05, cy = suelo - rr * 0.55 + vaiven;
    function niebla(p) { g.globalAlpha = cu[p] === null ? 0.35 : 1; g.setLineDash(cu[p] === null ? [3 * dpr, 3 * dpr] : []); }
    function concha(dx, dy, e) {
      g.beginPath();
      for (var i = 0; i <= n; i++) { var p = G.punto(arm, i / n * Math.PI); g[i ? 'lineTo' : 'moveTo'](p[0] * k * e + dx, -Math.abs(p[1]) * k * 0.9 * e + dy); }
      g.closePath();
    }
    g.save(); g.translate(x, cy);
    if (o.dir < 0) { g.scale(-1, 1); }
    var lx = o.dir < 0 ? -LUZ.x : LUZ.x;   
        niebla('patas');
    var largo = rr * 0.5 * (0.6 + 0.8 * (cu.patas || 0));
    for (var l = 0; l < 6; l++) {
      var px = (l - 2.5) / 2.5 * rr * 0.85, ph = t * 0.02 + l * 1.7, alza = q ? 0 : Math.sin(ph) * rr * 0.08;
      var rod = [px * 1.05, largo * 0.45 - Math.abs(alza)], pie = [px * 1.15, largo + alza * 0.5];
      [[B.contorno, 3.4], [B.base, 1.6]].forEach(function (s) {
        g.strokeStyle = s[0]; g.lineWidth = s[1] * dpr; g.beginPath(); g.moveTo(px * 0.8, 0); g.lineTo(rod[0], rod[1]); g.lineTo(pie[0], pie[1]); g.stroke();
      });
    }
        niebla('caparazon');
    if (fo.brillo) { concha(0, 0, 1); g.strokeStyle = B.brillo; g.globalAlpha = 0.45; g.lineWidth = (4 + 8 * fo.brillo) * dpr; g.stroke(); niebla('caparazon'); }
        concha(0, 0, 1); g.save(); g.clip();
    g.fillStyle = B.sombra; g.fill();
    concha(lx * rr * 0.16, LUZ.y * rr * 0.16, 1); g.fillStyle = B.base; g.fill();
    concha(lx * rr * 0.32, LUZ.y * rr * 0.22, 0.42); g.fillStyle = B.brillo; g.fill();
    concha(lx * 1.5 * dpr, LUZ.y * 1.5 * dpr, 1); g.strokeStyle = B.brillo; g.lineWidth = 1.4 * dpr; g.stroke();   
    g.restore();
    concha(0, 0, 1); g.strokeStyle = B.contorno; g.lineWidth = 3.2 * dpr; g.stroke();   
        niebla('ojos');
    var alto = 0.75 + 0.45 * (cu.ojos || 0), cerrado = parpadea(o.ciclo, t, q);
    [[0.32, alto], [0.58, alto - 0.07]].forEach(function (e) {
      var ex = e[0] * rr, ey = -e[1] * rr;
      g.strokeStyle = B.contorno; g.lineWidth = 2.2 * dpr; g.beginPath(); g.moveTo(ex, -0.55 * rr); g.lineTo(ex, ey); g.stroke();
      if (cerrado) { g.lineWidth = 2 * dpr; g.beginPath(); g.moveTo(ex - 3 * dpr, ey); g.lineTo(ex + 3 * dpr, ey); g.stroke(); return; }
      g.fillStyle = '#f2f4f8'; g.beginPath(); g.arc(ex, ey, 3.2 * dpr, 0, 2 * Math.PI); g.fill();
      g.lineWidth = 1.2 * dpr; g.stroke();
      g.fillStyle = B.contorno; g.beginPath(); g.arc(ex + 1 * dpr, ey + 0.4 * dpr, 1.4 * dpr, 0, 2 * Math.PI); g.fill();
    });
    g.globalAlpha = 1; g.setLineDash([]);
    g.restore();
    var d = o.dir < 0 ? -1 : 1;
    return { radio: rr, caparazon: [x, cy - rr * 0.35], pinzas: [x + d * rr * 0.95, cy - rr * 0.1],
             patas: [x - d * rr * 0.5, suelo - rr * 0.55 + vaiven + largo], ojos: [x + d * rr * 0.45, cy - alto * rr] };
  }
    function ficha(clase) { var h = clase === 'coral' ? 12 : 196; return 'toon · light from upper-left · bands from class hue ' + h + ' · morph ' + MORF_MS / 1000 + ' s'; }

  var AtlasToon = { SELLOS: SELLOS, LUZ: LUZ, MORF_MS: MORF_MS, bandas: bandas, deSello: deSello, morf: morf, ondaVista: ondaVista, parpadea: parpadea, cangrejo: cangrejo, ficha: ficha };
  if (typeof module === 'object' && module.exports) { module.exports = AtlasToon; } else { raiz.AtlasToon = AtlasToon; }
})(this);
