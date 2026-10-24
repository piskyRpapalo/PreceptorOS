(function (raiz) {
  'use strict';

  // Combate por rondas (un tick = una ronda), paso a paso. PURO: ni DOM, ni red, ni reloj, ni azar del sistema.
  // inicia / ronda / cierra reproducen combate() de arena.js con el MISMO orden de sorteos.
  // simula añade ordenes en un tick K (fork desde 0 con la misma semilla) y el recibo de la partida.

  var enNode = typeof module === 'object' && module.exports;
  var V = enNode ? require('./valores.js') : raiz.AtlasValores;
  var G = enNode ? require('./gacha.js') : raiz.AtlasGacha;
  var K = enNode ? require('./canon.js') : raiz.AtlasCanon;
  var TL = enNode ? require('./taller.js') : raiz.AtlasTaller;

  var RECIBO_TOPE = 200;
  var HEX64 = /^[0-9a-f]{64}$/;

  function unidades(ts, lado, v) {
    var A = v.combate.ataque;
    return ts.map(function (t, i) {
      var b = G.tirada(t.semilla, t.tc), s = t.lija && TL ? TL.aplica(b, t.lija).stats : b.stats;
      return { lado: lado, i: i, vida: s.vida, max: s.vida, arm: s.armadura, vel: s.velocidad, sig: s.sigilo,
               atk: A.base + A.aura * s.aura + A.inercia * s.inercia + A.profundidad * s.profundidad };
    });
  }

  function porMil(us) {
    var v = 0, m = 0;
    us.forEach(function (u) { v += u.vida; m += u.max; });
    return m ? Math.floor(v * 1000 / m) : 0;
  }

  function vivos(st, l) { return st.U[l].filter(function (u) { return u.vida > 0; }); }

  function inicia(def, asa, semilla, v) {
    v = v || V;
    var U = [unidades(def, 0, v), unidades(asa, 1, v)];
    return { v: v, P: v.combate, g: K.generador(semilla), U: U, todos: U[0].concat(U[1]), registro: [], ronda: 0 };
  }

  // Ejecuta una ronda. Devuelve false si el combate ya termino (sin tocar nada).
  function activo(st) { return st.ronda < st.P.rondas && vivos(st, 0).length > 0 && vivos(st, 1).length > 0; }

  function ronda(st) {
    if (!activo(st)) { return false; }
    st.ronda++;
    var P = st.P, g = st.g, registro = st.registro, n = st.ronda;
    var turno = st.todos.filter(function (u) { return u.vida > 0; })
      .map(function (u) { return { u: u, k: g.uniforme(1000000) }; })
      .sort(function (a, b) { return b.u.vel - a.u.vel || a.k - b.k || a.u.lado - b.u.lado || a.u.i - b.u.i; });
    turno.forEach(function (x) {
      var u = x.u, enemigos = vivos(st, 1 - u.lado);
      if (u.vida <= 0 || !enemigos.length) { return; }
      var t = enemigos[0], esquiva = Math.min(P.esquiva.tope, t.sig * P.esquiva.por_sigilo);
      if (g.uniforme(1000) < esquiva) { registro.push([n, u.lado, u.i, t.i, -1]); return; }
      var d = Math.max(1, u.atk - Math.floor(t.arm / P.armadura_div));
      t.vida = Math.max(0, t.vida - d);
      registro.push([n, u.lado, u.i, t.i, d]);
    });
    return true;
  }

  function cierra(st) {
    var vd = vivos(st, 0).length, va = vivos(st, 1).length, pd = porMil(st.U[0]), pa = porMil(st.U[1]);
    var gana = vd && !va ? 'defensa' : va && !vd ? 'asalto' : pd > pa ? 'defensa' : pa > pd ? 'asalto' : 'empate';
    return { esquema: 'atlas.combate/1', rondas: st.ronda, gana: gana, vida_por_mil: [pd, pa], registro: st.registro };
  }

  function combate(def, asa, semilla, v) {
    var st = inicia(def, asa, semilla, v);
    while (ronda(st)) { /* una ronda por vuelta */ }
    return cierra(st);
  }

  // Ordenes de intervencion: { tick: K, lado: 0|1, i: indice, accion: 'retira' }.
  // 'retira' deja la unidad fuera del combate (vida 0) antes de la ronda K; las rondas K..N se recalculan.
  function valida(ordenes, P, nUnidades) {
    if (!Array.isArray(ordenes)) { return 'ordenes no es una lista'; }
    for (var j = 0; j < ordenes.length; j++) {
      var o = ordenes[j];
      if (!o || typeof o !== 'object') { return 'orden ' + j + ' no es un registro'; }
      if (!Number.isSafeInteger(o.tick) || o.tick < 1 || o.tick > P.rondas) { return 'orden ' + j + ': tick ' + o.tick + ' fuera de 1..' + P.rondas; }
      if (o.lado !== 0 && o.lado !== 1) { return 'orden ' + j + ': lado invalido'; }
      if (!Number.isSafeInteger(o.i) || o.i < 0 || o.i >= nUnidades[o.lado]) { return 'orden ' + j + ': unidad ' + o.i + ' no existe'; }
      if (o.accion !== 'retira') { return 'orden ' + j + ': accion desconocida'; }
    }
    return null;
  }

  function simula(def, asa, semilla, ordenes, v) {
    v = v || V;
    var motivo = valida(ordenes || [], v.combate, [def.length, asa.length]);
    if (motivo) { return { ok: false, motivo: motivo }; }
    var st = inicia(def, asa, semilla, v), ord = (ordenes || []).slice().sort(function (a, b) { return a.tick - b.tick || a.lado - b.lado || a.i - b.i; });
    while (activo(st)) {
      ord.forEach(function (o) {
        if (o.tick === st.ronda + 1) { st.U[o.lado][o.i].vida = 0; }
      });
      ronda(st);
    }
    return { ok: true, combate: cierra(st) };
  }

  function recibo(def, asa, semilla, ordenes, v) {
    var s = simula(def, asa, semilla, ordenes, v);
    if (!s.ok) { return s; }
    var c = s.combate;
    // Claves compactas: con los nombres completos (seed, initial_teams_hash, orders_array, final_verdict,
    // signature) el recibo pasa de 200 B. Desviacion declarada en la PR; el mapeo vive aqui.
    //   s = semilla · e = huella de equipos (16 hex) · o = ordenes · v = veredicto {g, r, m} · f = firma (NO_DATA)
    var r = {
      s: semilla, e: K.huella({ def: def, asa: asa }).slice(0, 16), o: (ordenes || []).slice(),
      v: { g: c.gana, r: c.rondas, m: c.vida_por_mil }, f: 'NO_DATA'
    };
    var texto = JSON.stringify(r);
    if (texto.length > RECIBO_TOPE) { return { ok: false, motivo: 'recibo de ' + texto.length + ' B supera ' + RECIBO_TOPE }; }
    return { ok: true, recibo: r, texto: texto };
  }

  // Reproduce desde tick 0 con la semilla y las ordenes del recibo y compara el veredicto.
  function verifica(rec, def, asa, v) {
    if (!rec || !HEX64.test(rec.s || '')) { return { ok: false, motivo: 'semilla mal formada' }; }
    if (!rec.v) { return { ok: false, motivo: 'sin veredicto' }; }
    if (rec.e !== K.huella({ def: def, asa: asa }).slice(0, 16)) { return { ok: false, motivo: 'equipos distintos del recibo' }; }
    var r = recibo(def, asa, rec.s, rec.o, v);
    if (!r.ok) { return r; }
    var same = JSON.stringify(r.recibo.v) === JSON.stringify(rec.v);
    return same ? { ok: true } : { ok: false, motivo: 'veredicto distinto al recalcular desde tick 0' };
  }

  var AtlasCombateTicks = {
    RECIBO_TOPE: RECIBO_TOPE, unidades: unidades, porMil: porMil,
    inicia: inicia, ronda: ronda, cierra: cierra, combate: combate,
    simula: simula, recibo: recibo, verifica: verifica
  };
  if (enNode) { module.exports = AtlasCombateTicks; }
  else { raiz.AtlasCombateTicks = AtlasCombateTicks; }
})(this);
