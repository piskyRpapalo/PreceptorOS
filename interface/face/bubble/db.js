
(function (raiz) {
  'use strict';

  var V = (typeof module === 'object' && module.exports) ? require('./valores.js') : raiz.AtlasValores;
  var TOPE = V.army_tope;

  function hex(buf) {
    return Array.prototype.map.call(new Uint8Array(buf), function (b) {
      return ('0' + b.toString(16)).slice(-2);
    }).join('');
  }


  function adopcion(tropa, pseudonimo, clave) {
    return { esquema: 'atlas.adopcion/1', tropa: tropa, pseudonimo: pseudonimo, clave_publica: clave };
  }


  function crea(verifica, almacen) {
    var army = [];
    function guarda() {
      if (almacen) { almacen.pon(army.map(function (u) { return { adopcion: u.adopcion, firma: u.firma }; })); }
    }
    var yo = {
      lista: function () { return army.slice(); },

      adopta: function (ad, firma) {
        if (!ad || ad.esquema !== 'atlas.adopcion/1' || !ad.tropa || ad.tropa.esquema !== 'atlas.tropa/1') {
          return Promise.reject(new Error('forma: adopcion'));
        }
        var m = /^ed25519:([0-9a-f]{128})$/.exec(firma || '');
        if (!m) { return Promise.reject(new Error('sin firma')); }
        if (!/^[0-9a-f]{64}$/.test(ad.clave_publica || '')) { return Promise.reject(new Error('forma: clave')); }
        if (army.length >= TOPE) { return Promise.reject(new Error('army lleno (' + TOPE + ')')); }
        if (army.some(function (a) { return a.adopcion.tropa.semilla === ad.tropa.semilla; })) {
          return Promise.reject(new Error('ya adoptada'));
        }
        return Promise.resolve(verifica(JSON.stringify(ad), m[1], ad.clave_publica)).then(function (ok) {
          if (!ok) { throw new Error('firma: no verifica'); }
          var u = { adopcion: ad, firma: firma };
          army.push(u);
          guarda();
          return u;
        });
      },

      retira: function (rec, firma) {
        var m = /^ed25519:([0-9a-f]{128})$/.exec(firma || '');
        if (!rec || rec.esquema !== 'atlas.taller/1' || rec.op !== 'desintegra' || !m) { return Promise.reject(new Error('forma: recibo')); }
        var i = army.map(function (u) { return u.adopcion.tropa.semilla; }).indexOf(rec.semilla);
        if (i < 0) { return Promise.reject(new Error('no esta en el army')); }
        if (army[i].adopcion.clave_publica !== rec.clave_publica) { return Promise.reject(new Error('otra clave')); }
        return Promise.resolve(verifica(JSON.stringify(rec), m[1], rec.clave_publica)).then(function (ok) {
          if (!ok) { throw new Error('firma: no verifica'); }
          var u = army.splice(i, 1)[0];
          guarda();
          return u;
        });
      },

      restaura: function () {
        if (!almacen) { return Promise.resolve({ entran: 0, fuera: [] }); }
        return Promise.resolve(almacen.lee()).then(function (l) {
          var fuera = [], cadena = Promise.resolve();
          (Array.isArray(l) ? l : []).forEach(function (u) {
            cadena = cadena.then(function () {
              return yo.adopta(u && u.adopcion, u && u.firma).catch(function (e) { fuera.push(e.message); });
            });
          });
          return cadena.then(function () { if (fuera.length) { guarda(); } return { entran: army.length, fuera: fuera }; });
        });
      }
    };
    return yo;
  }


  function almacenWeb() {
    function db() {
      return new Promise(function (ok, mal) {
        var r = raiz.indexedDB.open('atlas-army', 1);
        r.onupgradeneeded = function () { r.result.createObjectStore('army'); };
        r.onsuccess = function () { ok(r.result); }; r.onerror = function () { mal(r.error); };
      });
    }
    return {
      lee: function () {
        return db().then(function (d) {
          return new Promise(function (ok) {
            var q = d.transaction('army').objectStore('army').get('mia');
            q.onsuccess = function () { d.close(); ok(q.result || []); }; q.onerror = function () { d.close(); ok([]); };
          });
        }).catch(function () { return []; });
      },
      pon: function (l) {
        db().then(function (d) {
          var tx = d.transaction('army', 'readwrite'); tx.objectStore('army').put(l, 'mia');
          tx.oncomplete = function () { d.close(); };
        }).catch(function () {});
      }
    };
  }


  function caja(base, almacen, clave, strict) {
    function db() {
      return new Promise(function (ok, mal) {
        var r = raiz.indexedDB.open(base, 1);
        r.onupgradeneeded = function () { r.result.createObjectStore(almacen); };
        r.onsuccess = function () { ok(r.result); }; r.onerror = function () { mal(r.error); };
      });
    }
    return {
      lee: function () {
        return db().then(function (d) {
          return new Promise(function (ok, mal) {
            var q = d.transaction(almacen).objectStore(almacen).get(clave);
            q.onsuccess = function () { d.close(); ok(q.result || null); }; q.onerror = function () { d.close(); if (strict) { mal(q.error); } else { ok(null); } };
          });
        }).catch(function (error) { if (strict) { throw error; } return null; });
      },
      pon: function (v) {
        return db().then(function (d) {
          return new Promise(function (ok, mal) {
            var tx = d.transaction(almacen, 'readwrite'); tx.objectStore(almacen).put(v, clave);
            tx.oncomplete = function () { d.close(); ok(true); };
            tx.onerror = tx.onabort = function () { d.close(); mal(tx.error || new Error('NO_DATA · device transaction aborted')); };
          });
        });
      }
    };
  }

  function calidadWeb() { return caja('atlas-calidad', 'calidad', 'modo'); }

  function conquistasWeb(record, lugares, pinta) {
    var c = caja('atlas-conquista', 'conquista', 'record');
    c.lee().then(function (r) {
      var l = limpiaRecord(r, lugares.map(function (x) { return x.clave; }));
      Object.keys(l).forEach(function (k) { if (!record[k]) { record[k] = l[k]; } });
      pinta();
    });
    return c;
  }

  function limpiaRecord(r, claves) {
    var o = {};
    function ok(n) { return Number.isInteger(n) && n >= 0; }
    if (!r || typeof r !== 'object' || Array.isArray(r)) { return o; }
    claves.forEach(function (k) {
      var x = r[k];
      if (x && typeof x === 'object' && ok(x.g) && ok(x.p)) { o[k] = { g: x.g, p: x.p }; }
    });
    return o;
  }


  function verificaWeb(texto, firmaHex, claveHex) {
    function bytes(h) { return new Uint8Array(h.match(/../g).map(function (x) { return parseInt(x, 16); })); }
    var s = raiz.crypto && raiz.crypto.subtle;
    if (!s) { return Promise.reject(new Error('NO_DATA · sin WebCrypto')); }
    return s.importKey('raw', bytes(claveHex), { name: 'Ed25519' }, false, ['verify'])
      .then(function (k) {
        return s.verify({ name: 'Ed25519' }, k, bytes(firmaHex), new TextEncoder().encode(texto));
      });
  }


  function semillaWeb(firma) {
    return raiz.crypto.subtle.digest('SHA-256', new TextEncoder().encode(firma)).then(hex);
  }


  function eslabon(cadena, tc, clave) {
    var u = cadena[cadena.length - 1];
    return { esquema: 'atlas.invocacion/2', tc: tc, seq: u ? u.obj.seq + 1 : 1, prev: u ? u.semilla : 'genesis', clave_publica: clave };
  }
  function compruebaCadena(cadena) {
    for (var i = 0; i < cadena.length; i++) {
      var e = cadena[i], o = e && e.obj;
      if (!o || o.esquema !== 'atlas.invocacion/2') { return 'eslabon ' + (i + 1) + ': esquema'; }
      if (o.seq !== i + 1) { return 'hueco: se esperaba seq ' + (i + 1) + ' y llega ' + o.seq; }
      if (o.prev !== (i ? cadena[i - 1].semilla : 'genesis')) { return 'eslabon ' + o.seq + ': prev no enlaza'; }
      if (i && o.clave_publica !== cadena[0].obj.clave_publica) { return 'eslabon ' + o.seq + ': otra clave'; }
    }
    return '';
  }
  function anexa(cadena, obj, firma, semilla, desde, hasta) {
    var c = cadena.concat([{ obj: obj, firma: firma, semilla: semilla, desde: desde, hasta: hasta, abierto: false }]), causa = compruebaCadena(c);
    if (causa) { throw new Error('cadena: ' + causa); }
    return c;
  }
  function huevos(cadena) {
    return cadena.filter(function (e) { return !e.abierto; }).map(function (e) { return { tc: e.obj.tc, semilla: e.semilla, desde: e.desde, hasta: e.hasta, seq: e.obj.seq }; });
  }
  function abre(cadena, seq) { return cadena.map(function (e) { return e.obj.seq === seq ? Object.assign({}, e, { abierto: true }) : e; }); }

  function verificaCadena(cadena, clave, verifica, sha) {
    var causa = compruebaCadena(cadena);
    if (causa) { return Promise.resolve(causa); }
    return cadena.reduce(function (p, e) {
      return p.then(function (c) {
        if (c) { return c; }
        var m = /^ed25519:([0-9a-f]{128})$/.exec(e.firma || '');
        if (!m || e.obj.clave_publica !== clave) { return 'eslabon ' + e.obj.seq + ': firma'; }
        return Promise.resolve(verifica(JSON.stringify(e.obj), m[1], clave)).then(function (ok) {
          if (!ok) { return 'eslabon ' + e.obj.seq + ': firma'; }
          return Promise.resolve(sha(e.firma)).then(function (s) { return s === e.semilla ? '' : 'eslabon ' + e.obj.seq + ': semilla'; });
        });
      });
    }, Promise.resolve(''));
  }
  function cadenaWeb(clave) { return caja('atlas-invocaciones', 'cadena', clave, true); }

  function piedad(cadena, rareza) {
    var causa = cadena ? compruebaCadena(cadena) : 'sin cadena';
    if (causa) { return { nd: causa }; }
    var abiertos = cadena.filter(function (e) { return e.abierto; }), n = 0;
    for (var i = abiertos.length - 1; i >= 0; i--) { var r = rareza(abiertos[i]); if (r === 'raro' || r === 'unico') { break; } n++; }
    return { desde_raro: n, abiertos: abiertos.length, incubando: cadena.length - abiertos.length };
  }

  function cronica(cadena, tirada) {
    return (cadena || []).filter(function (e) { return e.abierto; }).map(function (e) {
      var t = tirada(e.semilla, e.obj.tc);
      return { seq: e.obj.seq, tc: e.obj.tc, ciclo: e.desde, sello: e.semilla.slice(0, 8), aristas: t.aristas, rareza: t.rareza };
    });
  }

  var AtlasArmy = { TOPE: TOPE, adopcion: adopcion, crea: crea, almacenWeb: almacenWeb, cajaWeb: caja, calidadWeb: calidadWeb, conquistasWeb: conquistasWeb, limpiaRecord: limpiaRecord, verificaWeb: verificaWeb, semillaWeb: semillaWeb,
    eslabon: eslabon, compruebaCadena: compruebaCadena, anexa: anexa, huevos: huevos, abre: abre, verificaCadena: verificaCadena, cadenaWeb: cadenaWeb,
    piedad: piedad, cronica: cronica };
  if (typeof module === 'object' && module.exports) { module.exports = AtlasArmy; }
  else { raiz.AtlasArmy = AtlasArmy; }
})(this);
