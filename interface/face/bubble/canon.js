(function (raiz) {
  'use strict';

  var C = (typeof module === 'object' && module.exports) ? require('../assets/atlas-coord.js') : raiz.AtlasCoord;

  function ascii(s) {
    return s.replace(/[^\x20-\x7e]/g, function (c) { return '\\u' + ('000' + c.charCodeAt(0).toString(16)).slice(-4); });
  }

  function canon(x) {
    if (x === null) { return 'null'; }
    if (typeof x === 'boolean') { return x ? 'true' : 'false'; }
    if (typeof x === 'number') {
      if (!Number.isSafeInteger(x)) { throw new RangeError('canon: solo enteros seguros (' + x + ')'); }
      return String(x);
    }
    if (typeof x === 'string') { return ascii(JSON.stringify(x)); }
    if (Array.isArray(x)) { return '[' + x.map(canon).join(',') + ']'; }
    if (typeof x === 'object') {
      return '{' + Object.keys(x).sort().map(function (k) { return ascii(JSON.stringify(k)) + ':' + canon(x[k]); }).join(',') + '}';
    }
    throw new TypeError('canon: tipo ' + typeof x);
  }

  function sha(texto) { return C.sha256(texto); }
  function huella(x) { return sha(canon(x)); }

    function ordena(x) {
    if (Array.isArray(x)) { return x.map(ordena); }
    if (x && typeof x === 'object') {
      var o = {};
      Object.keys(x).sort().forEach(function (k) { o[k] = ordena(x[k]); });
      return o;
    }
    return x;
  }

  var HEX64 = /^[0-9a-f]{64}$/;

  function generador(semilla) {
    if (!HEX64.test(semilla || '')) { throw new Error('semilla: 64 hex'); }
    var a = parseInt(semilla.slice(0, 8), 16) | 0;
    function u32() {
      a = a + 0x6D2B79F5 | 0;
      var t = Math.imul(a ^ a >>> 15, 1 | a);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return (t ^ t >>> 14) >>> 0;
    }
        function uniforme(n) {
      if (!Number.isSafeInteger(n) || n < 1 || n > 4294967296) { throw new RangeError('uniforme: n ' + n); }
      var tope = 4294967296 - (4294967296 % n), x;
      do { x = u32(); } while (x >= tope);
      return x % n;
    }
    return { u32: u32, uniforme: uniforme };
  }

    function loteria(pesos, g) {
    var total = 0;
    pesos.forEach(function (p) {
      if (!Number.isSafeInteger(p) || p < 0) { throw new RangeError('loteria: peso ' + p); }
      total += p;
    });
    if (total < 1) { throw new RangeError('loteria: sin peso'); }
    var r = g.uniforme(total), acum = 0;
    for (var i = 0; i < pesos.length; i++) { acum += pesos[i]; if (r < acum) { return i; } }
    throw new Error('loteria: inalcanzable');
  }

    function puntosBasicos(pesos) {
    var total = pesos.reduce(function (s, p) { return s + p; }, 0);
    var pb = pesos.map(function (p) { return Math.floor(p * 10000 / total); });
    return { pb: pb, resto: 10000 - pb.reduce(function (s, p) { return s + p; }, 0) };
  }

    function satura(x, min, max) { return x < min ? min : x > max ? max : x; }

  var AtlasCanon = { canon: canon, huella: huella, sha: sha, ordena: ordena, generador: generador,
                     loteria: loteria, puntosBasicos: puntosBasicos, satura: satura, HEX64: HEX64 };
  if (typeof module === 'object' && module.exports) { module.exports = AtlasCanon; }
  else { raiz.AtlasCanon = AtlasCanon; }
})(this);
