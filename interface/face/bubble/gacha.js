(function (raiz) {
  'use strict';

    var V = (typeof module === 'object' && module.exports) ? require('./valores.js') : raiz.AtlasValores;
  var TCS = V.tcs, PREFIJOS = V.prefijos, SUFIJOS = V.sufijos;
  var RAREZAS = ['normal', 'magico', 'raro', 'unico'];
  var STATS = ['vida', 'armadura', 'velocidad', 'sigilo', 'inercia', 'profundidad', 'aura'];
  var TERMINOS = V.terminos, ARISTAS = V.aristas, RA = V.rareza_aristas, FORMA = V.forma;

    function generador(semilla) {
    if (!/^[0-9a-f]{64}$/.test(semilla || '')) { throw new Error('semilla'); }
    var s = [0, 8, 16, 24].map(function (i) { return parseInt(semilla.slice(i, i + 8), 16) >>> 0; });
    var a = s[0], b = s[1], c = s[2], d = s[3];
    function sig() {
      var t = (a + b >>> 0) + d >>> 0;
      d = d + 1 >>> 0; a = b ^ b >>> 9; b = c + (c << 3) >>> 0;
      c = (c << 21 | c >>> 11); c = c + t >>> 0;
      return t;
    }
    for (var i = 0; i < 12; i++) { sig(); }
    return {
      mil: function () { return sig() % 1000; },
      entre: function (r) { return r[0] + sig() % (r[1] - r[0] + 1); },
      uno: function (lista) { return lista[sig() % lista.length]; }
    };
  }

  function suma(stats, mods, g) {
    Object.keys(mods).forEach(function (k) { stats[k] += g.entre(mods[k]); });
  }

    function armonicos(n, rareza, g) {
    var a1 = g.entre(FORMA.a1), f1 = g.entre([0, 63]), out = [[1, 24, 24, 0], [1 - n, a1, a1, f1]];
    for (var j = 2; j < TERMINOS[rareza]; j++) {
      var s = j % 2 ? -1 : 1, amp = Math.floor(a1 / (FORMA.div * j * j));
      out.push([1 + s * n * j, amp, amp, ((-s * j * f1) % 64 + 64) % 64]);
    }
    return out;
  }
    function aristasDe(q, tc) {
    var t = ARISTAS[tc], acc = 0;
    for (var i = 0; i < t.length; i++) { acc += t[i][1]; if (q < acc) { return t[i][0]; } }
    return t[t.length - 1][0];
  }
  function rarezaDe(n) { return n <= RA.normal ? 'normal' : n <= RA.magico ? 'magico' : n <= RA.raro ? 'raro' : 'unico'; }
    function aristas(t) {
    var a = (t && t.armonicos) || t, N = 720, r = [], c = 0;
    for (var i = 0; i < N; i++) { var p = punto(a, i / N * 2 * Math.PI); r.push(Math.sqrt(p[0] * p[0] + p[1] * p[1])); }
    for (var k = 0; k < N; k++) { var b = r[k]; if (b > r[(k + N - 1) % N] && b >= r[(k + 1) % N]) { c++; } }
    return c;
  }

    function tirada(semilla, tc) {
    var T = TCS[tc];
    if (!T) { throw new Error('tc'); }
    var g = generador(semilla), n = aristasDe(g.mil(), tc), rareza = rarezaDe(n);
    var nivel = Number(tc.slice(2));
    var stats = {};
    STATS.forEach(function (k) { stats[k] = 0; });
    var B = V.base;
    stats.vida = B.vida[0] * nivel + g.entre([0, B.vida[1]]);
    stats.armadura = B.armadura[0] * nivel + g.entre([0, B.armadura[1]]);
    stats.velocidad = B.velocidad[0] + g.entre([0, B.velocidad[1]]);
    var pre = null, suf = null;
    if (rareza === 'unico') { pre = 'atlante'; suf = 'abismo'; }
    else if (rareza === 'raro') { pre = g.uno(Object.keys(PREFIJOS)); suf = g.uno(Object.keys(SUFIJOS)); }
    else if (rareza === 'magico') {
      var cual = g.entre([0, 2]);
      if (cual !== 1) { pre = g.uno(Object.keys(PREFIJOS)); }
      if (cual !== 0) { suf = g.uno(Object.keys(SUFIJOS)); }
    }
    if (pre) { suma(stats, PREFIJOS[pre], g); }
    if (suf) { suma(stats, SUFIJOS[suf], g); }
    if (rareza === 'raro' || rareza === 'unico') { suma(stats, PREFIJOS[g.uno(Object.keys(PREFIJOS))], g); }
    if (rareza === 'unico') { STATS.forEach(function (k) { stats[k] += nivel; }); }
    return {
      esquema: 'atlas.tropa/1', tc: tc, base: T.base, rareza: rareza,
      prefijo: pre, sufijo: suf, stats: stats, aristas: n, armonicos: armonicos(n, rareza, g), semilla: semilla, campo_origen: 'medido'
    };
  }

    var ORIGENES = ['medido', 'emulado'];
  function espectro(t) {
    var o = t.campo_origen || 'medido';
    if (ORIGENES.indexOf(o) < 0) { throw new Error('campo_origen'); }
    if (o === 'medido') { return t.armonicos; }
    return t.armonicos.map(function (h, i) {
      return i < 2 ? h : [h[0], h[1] >> (i - 1), h[2] >> (i - 1), h[3]];
    });
  }

    function lod(t, cara) { var e = espectro(t); return cara === 'taller' ? e : e.slice(0, 2); }

    var HUEVO = [[1, 16, 22, 0], [2, 0, 3, 16]];

    function mezcla(a, b, t) {
    var n = Math.max(a.length, b.length), out = [];
    for (var i = 0; i < n; i++) {
      var x = a[i] || [b[i][0], 0, 0, b[i][3]], y = b[i] || [a[i][0], 0, 0, a[i][3]];
      var k = t < 0.5 ? x[0] : y[0];
      out.push([k, x[1] + (y[1] - x[1]) * t, x[2] + (y[2] - x[2]) * t, x[3] + (y[3] - x[3]) * t]);
    }
    return out;
  }

    function punto(arm, u) {
    var x = 0, y = 0;
    arm.forEach(function (h) {
      var f = h[0] * u + h[3] * Math.PI / 32;
      x += h[1] * Math.cos(f); y += h[2] * Math.sin(f);
    });
    return [x, y];
  }

    function compacta(tropa) {
    return JSON.stringify([tropa.tc, tropa.rareza, tropa.prefijo, tropa.sufijo, tropa.armonicos]);
  }

    function caracter(t) {
    var a = (t && t.armonicos) || [], s = 0, amp = 0;
    a.forEach(function (h) { s += Math.abs(h[0]); amp += Math.abs(h[1]) + Math.abs(h[2]); });
    return { color: s % 4, pulso: a.length > 3 ? 1 : 0, tendencia: (s + amp) % 4 };
  }

    function odds(tc) {
    var o = [0, 0, 0, 0];
    ARISTAS[tc].forEach(function (x) { o[RAREZAS.indexOf(rarezaDe(x[0]))] += x[1]; });
    return o;
  }
  function oddsAristas(tc) { return ARISTAS[tc].map(function (x) { return x.slice(); }); }

  var AtlasGacha = {
    ESTADO: V.estado, VERSION_VALORES: V.version, TCS: TCS, RAREZAS: RAREZAS, PREFIJOS: PREFIJOS, SUFIJOS: SUFIJOS, STATS: STATS, HUEVO: HUEVO,
    ORIGENES: ORIGENES, generador: generador, tirada: tirada, espectro: espectro, lod: lod, aristas: aristas, rarezaDe: rarezaDe,
    mezcla: mezcla, punto: punto, compacta: compacta, caracter: caracter, odds: odds, oddsAristas: oddsAristas
  };
  if (typeof module === 'object' && module.exports) { module.exports = AtlasGacha; }
  else { raiz.AtlasGacha = AtlasGacha; }
})(this);
