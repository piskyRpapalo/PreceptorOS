(function (raiz) {
  'use strict';

  var K = [];
  (function () {
    var n = 2, k = 0;
    function frac32(x) { return ((x - Math.floor(x)) * 4294967296) >>> 0; }
    while (k < 64) {
      var primo = true;
      for (var d = 2; d * d <= n; d++) { if (n % d === 0) { primo = false; break; } }
      if (primo) { K[k++] = frac32(Math.pow(n, 1 / 3)); }
      n++;
    }
  })();
  function sha256(txt) {
    if (/[^\x20-\x7e]/.test(txt)) { throw new RangeError('solo ASCII'); }
    var b = [], i, H = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c,
      0x1f83d9ab, 0x5be0cd19], w = [], l = txt.length * 8;
    for (i = 0; i < txt.length; i++) { b.push(txt.charCodeAt(i)); }
    b.push(0x80);
    while (b.length % 64 !== 56) { b.push(0); }
    for (i = 7; i >= 0; i--) { b.push(i > 3 ? 0 : (l >>> (i * 8)) & 255); }
    function r(x, n) { return (x >>> n) | (x << (32 - n)); }
    for (var o = 0; o < b.length; o += 64) {
      for (i = 0; i < 64; i++) {
        w[i] = i < 16 ? (b[o + i * 4] << 24) | (b[o + i * 4 + 1] << 16) | (b[o + i * 4 + 2] << 8) | b[o + i * 4 + 3]
          : (w[i - 16] + (r(w[i - 15], 7) ^ r(w[i - 15], 18) ^ (w[i - 15] >>> 3)) + w[i - 7] +
             (r(w[i - 2], 17) ^ r(w[i - 2], 19) ^ (w[i - 2] >>> 10))) | 0;
      }
      var a = H.slice();
      for (i = 0; i < 64; i++) {
        var t1 = (a[7] + (r(a[4], 6) ^ r(a[4], 11) ^ r(a[4], 25)) + ((a[4] & a[5]) ^ (~a[4] & a[6])) + K[i] + w[i]) | 0;
        var t2 = ((r(a[0], 2) ^ r(a[0], 13) ^ r(a[0], 22)) + ((a[0] & a[1]) ^ (a[0] & a[2]) ^ (a[1] & a[2]))) | 0;
        a = [(t1 + t2) | 0, a[0], a[1], a[2], (a[3] + t1) | 0, a[4], a[5], a[6]];
      }
      for (i = 0; i < 8; i++) { H[i] = (H[i] + a[i]) | 0; }
    }
    return H.map(function (x) { return ('0000000' + (x >>> 0).toString(16)).slice(-8); }).join('');
  }

  function coord(pub, semilla, sector, x, y) {
    var h = sha256([pub, semilla, sector || 'abierto', Math.round(x) + ',' + Math.round(y)].join(':'));
    return { hex: h, corta: '#' + h.slice(0, 4) + '…' + h.slice(-2) };
  }

  var AtlasCoord = { sha256: sha256, coord: coord };
  if (typeof module === 'object' && module.exports) { module.exports = AtlasCoord; }
  else { raiz.AtlasCoord = AtlasCoord; }
})(this);
