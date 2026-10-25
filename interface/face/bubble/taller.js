(function (raiz) {
  'use strict';
  var EN_NODE = typeof module === 'object' && module.exports;
  var V = EN_NODE ? require('./valores.js') : raiz.AtlasValores;
  var G = EN_NODE ? require('./gacha.js') : raiz.AtlasGacha;
  var K = EN_NODE ? require('./canon.js') : raiz.AtlasCanon;
  var TA = V.taller, LI = TA.lija, BA = V.banderas, CERO = new Array(65).join('0');

    function aristasDe(t) { return t.aristas || G.aristas(t); }
    function residuo(t) { var n = aristasDe(t); return n * TA.gramos_por_arista * (n > 12 ? TA.leviatan_x : 1); }
    function coste(nivel) { return LI.base * nivel; }

    function aplica(t, lija) {
    var c = JSON.parse(JSON.stringify(t));
    Object.keys(lija || {}).forEach(function (k) { if (LI.stats.indexOf(k) >= 0) { c.stats[k] += lija[k] * LI.paso; } });
    return c;
  }

    function recibo(estado, op, clave) {
    var r = { esquema: 'atlas.taller/1', op: op.op, prev: estado.ultimo, clave_publica: clave };
    if (op.op === 'desintegra') {
      var t = op.tropa;
      if (estado.disueltas[t.semilla]) { throw new Error('ya desintegrada'); }
      r.semilla = t.semilla; r.tc = t.tc; r.aristas = aristasDe(t); r.gramos = residuo(t);
    } else if (op.op === 'lija') {
      if (LI.stats.indexOf(op.stat) < 0) { throw new Error('stat'); }
      if (estado.disueltas[op.semilla]) { throw new Error('desintegrada'); }
      var nv = ((estado.lijas[op.semilla] || {})[op.stat] || 0) + 1;
      if (nv > LI.max) { throw new Error('tope'); }
      if (estado.saldo < coste(nv)) { throw new Error('sin residuo'); }
      r.semilla = op.semilla; r.stat = op.stat; r.nivel = nv; r.gramos = -coste(nv);
    } else if (op.op === 'tinte') {
            if (!(op.bandera in BA)) { throw new Error('bandera'); }
      if (estado.disueltas[op.semilla]) { throw new Error('desintegrada'); }
      if (estado.tintes[op.semilla] === op.bandera) { throw new Error('ya tenida'); }
      if (estado.saldo < TA.tinte.coste) { throw new Error('sin residuo'); }
      r.semilla = op.semilla; r.bandera = op.bandera; r.gramos = -TA.tinte.coste;
    } else { throw new Error('op'); }
    r.saldo = estado.saldo + r.gramos;
    return r;
  }

    function estado(cadena) {
    var e = { saldo: 0, lijas: {}, disueltas: {}, tintes: {}, ultimo: CERO, clave: null, n: 0 };
    for (var i = 0; i < (cadena || []).length; i++) {
      var r = cadena[i] && cadena[i].recibo, esperado;
      if (!r || r.esquema !== 'atlas.taller/1' || r.prev !== e.ultimo) { return { error: 'eslabon ' + i + ': enlace' }; }
      if (e.clave && r.clave_publica !== e.clave) { return { error: 'eslabon ' + i + ': otra clave' }; }
      try {
        esperado = recibo(e, r.op === 'desintegra' ? { op: r.op, tropa: { semilla: r.semilla, tc: r.tc, aristas: r.aristas, armonicos: [] } }
          : { op: r.op, semilla: r.semilla, stat: r.stat, bandera: r.bandera }, r.clave_publica);
      } catch (x) { return { error: 'eslabon ' + i + ': ' + x.message }; }
      if (JSON.stringify(esperado) !== JSON.stringify(r)) { return { error: 'eslabon ' + i + ': cuentas' }; }
      if (r.op === 'desintegra') { e.disueltas[r.semilla] = true; }
      else if (r.op === 'tinte') { e.tintes[r.semilla] = r.bandera; }
      else { e.lijas[r.semilla] = e.lijas[r.semilla] || {}; e.lijas[r.semilla][r.stat] = r.nivel; }
      e.saldo = r.saldo; e.clave = r.clave_publica; e.ultimo = K.sha(JSON.stringify(r)); e.n++;
    }
    return e;
  }
    function verificaFirmas(cadena, verifica) {
    return Promise.all((cadena || []).map(function (x) {
      var m = /^ed25519:([0-9a-f]{128})$/.exec(x.firma || '');
      return m ? Promise.resolve(verifica(JSON.stringify(x.recibo), m[1], x.recibo.clave_publica)) : false;
    })).then(function (l) { return l.every(Boolean); });
  }

  var AtlasTaller = { residuo: residuo, coste: coste, aplica: aplica, recibo: recibo, estado: estado, verificaFirmas: verificaFirmas, CERO: CERO };
  if (EN_NODE) { module.exports = AtlasTaller; } else { raiz.AtlasTaller = AtlasTaller; }
})(this);
