(function (root) {
  'use strict';
  var node = typeof module === 'object' && module.exports;
  function lib(name, file) { return root[name] || (node ? require(file) : null); }
  var T = lib('AtlasCombateTicks', '../../../public/game/combate_ticks.js');
  var G = lib('AtlasGacha', '../../../public/game/gacha.js');
  var K = lib('AtlasCanon', '../../../public/game/canon.js');
  var E = lib('AtlasEscuadron', '../../../public/game/escuadron.js');
  var V = lib('AtlasValores', '../../../public/game/valores.js');
  var forms = ['agresiva', 'defensiva', 'flanqueo'];
  var formNames = { agresiva: 'Spear', defensiva: 'Shield', flanqueo: 'Wings' };
  var patrolNames = { arrecife: 'Reef patrol', algas: 'Kelp patrol', ruinas: 'Ruins patrol', limo: 'Silt patrol', abismo: 'Abyss patrol', nucleo: 'Core patrol' };
  var field = [486, 200];

  function patrols() {
    return V.patrullas.map(function (p) {
      var s = K.sha('atlas.patrulla/1:' + p.id), ts = [];
      for (var i = 0; i < p.n; i++) { ts.push({ tc: p.tc, semilla: K.sha(s + ':patrulla:' + i) }); }
      return { id: p.id, name: patrolNames[p.id] || p.id, tc: p.tc, n: p.n, semilla: s, tropas: ts };
    });
  }
  function seedFor(p, squad) { return K.sha('preceptor.face/batalla:' + p.id + ':' + squad.map(function (x) { return x.semilla; }).join(',')); }
  function spot(side, i, n) { var k = i - (n - 1) / 2; return [Math.round(field[0] + k * 38 + (i % 2) * 6), Math.round(field[1] + (side ? 96 : -96) + (i % 2) * 18)]; }

  function create() {
    var p = null, squad = [], seed = null, draws = [[], []];
    var b = { on: false, form: 'defensiva', orders: [], st: null, last: [], result: null, receipt: null, verified: null, reveal: 0, patrol: null };

    function begin(patrol, army) {
      p = patrol; squad = (army || []).slice(0, V.combate.tropas_max);
      if (!p || !squad.length) { return null; }
      seed = seedFor(p, squad);
      draws = [p.tropas.map(function (x) { return G.tirada(x.semilla, x.tc); }), squad.map(function (x) { return G.tirada(x.semilla, x.tc); })];
      b.on = true; b.patrol = p.id; b.orders = []; b.result = null; b.receipt = null; b.verified = null; b.last = []; b.reveal = 0;
      b.st = T.inicia(p.tropas, squad, seed);
      return b;
    }
    function done() { return !!b.result; }
    function alive(l) { return b.st.U[l].filter(function (u) { return u.vida > 0; }); }
    function step() {
      if (!b.st || done()) { return false; }
      var st = b.st, n0 = st.registro.length, ok;
      b.orders.forEach(function (o) { if (o.tick === st.ronda + 1) { st.U[o.lado][o.i].vida = 0; } });
      ok = T.ronda(st);
      b.last = st.registro.slice(n0);
      if (!ok || !(st.ronda < st.P.rondas && alive(0).length && alive(1).length)) { finish(); }
      return true;
    }
    function finish() {
      b.result = T.cierra(b.st);
      var r = T.recibo(p.tropas, squad, seed, b.orders);
      b.receipt = r.ok ? r.texto : 'NO_DATA: ' + r.motivo;
      b.verified = r.ok ? T.verifica(r.recibo, p.tropas, squad) : { ok: false, motivo: r.motivo };
    }
    function withdraw(i) {
      if (!b.st || done() || b.orders.length >= 1) { return false; }
      var u = b.st.U[1][i];
      if (!u || u.vida <= 0) { return false; }
      b.orders.push({ tick: b.st.ronda + 1, lado: 1, i: i, accion: 'retira' });
      return true;
    }
    function form(f) { if (forms.indexOf(f) >= 0) { b.form = f; } }

    function troops() {
      var out = [];
      [0, 1].forEach(function (l) {
        draws[l].forEach(function (d, i) {
          var u = b.st ? b.st.U[l][i] : { vida: d.stats.vida, max: d.stats.vida };
          out.push({ lado: l, i: i, d: d, vida: u.vida, max: u.max, at: spot(l, i, draws[l].length), name: d.rareza });
        });
      });
      return out;
    }
    function life(l) { var v = 0, m = 0; troops().forEach(function (x) { if (x.lado === l) { v += x.vida; m += x.max; } }); return [v, m]; }

    function frame(change) {
      var atoms = [0, 1].map(function (l) {
        var list = troops().filter(function (x) { return x.lado === l && x.vida > 0; }), lf = life(l);
        return { k: l ? 'yours' : 'patrol', r: (l ? 'your squad, ' + formNames[b.form] : (patrolNames[b.patrol] || 'patrol')) + ': ' + list.length + ' alive, life ' + lf[0] + ' of ' + lf[1],
          i: list.map(function (x) { return { o: 'wave', x: x.at[0], y: x.at[1], h: [[1, 9, 9, 0]], f: l ? 'cyan' : 'vermilion.base' }; }) };
      });
      return { v: 'preceptoros.bubble/1', id: 'battle', t: b.st ? b.st.ronda : 0, atoms: atoms, bands: ['cyan', 'vermilion.base', 'ink'],
        change: [change || (b.result ? 'verdict: ' + b.result.gana : 'tick ' + (b.st ? b.st.ronda : 0))], sound: 'NO_DATA', soundCause: 'sound off', motion: 'tick by tick' };
    }

    function paint(g, toScreen, z, quiet) {
      if (!b.on) { return; }
      var O = root.AtlasOnda, list = troops(), per = Math.max(1, Math.floor((V.army_tope || 30) / Math.max(1, draws[1].length))), k = Math.max(0.35, z);
      list.forEach(function (x) {
        var p2 = toScreen(x.at[0], x.at[1]), r = 18 * k, frac = x.max ? x.vida / x.max : 0, c = O.colorVida(frac, O.tono(x.d));
        if (x.vida <= 0) { return; }
        if (x.lado === 1) {
          var n = Math.min(per, E.cuantas(x.d.aristas)), s = E.sitios(n, x.d.semilla, b.form);
          for (var i = 1; i < E.vivas(n, x.vida, x.max); i++) { O.dibuja(g, x.d.armonicos, p2[0] + s[i][0] * r * 0.9, p2[1] + s[i][1] * r * 0.55, r * 0.22, { calidad: 0, color: c, alfa: 0.75 }); }
        }
        var grow = b.reveal && x.lado === 1 ? Math.min(x.d.armonicos.length, 1 + Math.floor(b.reveal / 6)) : x.d.armonicos.length;
        O.dibuja(g, x.d.armonicos.slice(0, grow), p2[0], p2[1] - r * 0.4, r, { calidad: quiet ? 1 : 2, color: c, face: true, estela: quiet ? 0 : 2, giro: (b.st ? b.st.ronda : 0) * 0.35 * (x.lado ? -1 : 1) });
      });
      g.save();
      b.last.forEach(function (e) {
        var a = list.filter(function (x) { return x.lado === e[1] && x.i === e[2]; })[0], d = list.filter(function (x) { return x.lado !== e[1] && x.i === e[3]; })[0];
        if (!a || !d) { return; }
        var p1 = toScreen(a.at[0], a.at[1]), q = toScreen(d.at[0], d.at[1]);
        g.setLineDash(e[4] < 0 ? [4, 6] : []);
        g.strokeStyle = e[1] ? 'rgba(0,210,255,.85)' : 'rgba(230,57,70,.85)'; g.lineWidth = Math.max(2, 3 * k);
        g.beginPath(); g.moveTo(p1[0], p1[1] - 10 * k); g.quadraticCurveTo((p1[0] + q[0]) / 2, Math.min(p1[1], q[1]) - 50 * k, q[0], q[1] - 10 * k); g.stroke();
      });
      g.restore();
    }

    function sonar(A) { if (A) { A.activa(true); A.suena({ tipo: 'sonar', portadora: 1320, moduladora: 660, indice: 90, dur: 0.5, gan: 0.08 }); } }

    function summary() {
      return { on: b.on, patrol: b.patrol, tick: b.st ? b.st.ronda : 0, form: b.form, orders: b.orders.slice(), result: b.result && { gana: b.result.gana, rondas: b.result.rondas, vida_por_mil: b.result.vida_por_mil },
        receipt: b.receipt, verified: b.verified, won: !!(b.result && b.result.gana === 'asalto'),
        troops: troops().map(function (x) { return { side: x.lado ? 'yours' : 'patrol', i: x.i, name: x.name, life: x.vida, max: x.max }; }) };
    }

    return { begin: begin, step: step, done: done, withdraw: withdraw, form: form, frame: frame, paint: paint, sonar: sonar, summary: summary, troops: troops, b: b };
  }

  var Battle = { create: create, patrols: patrols, seedFor: seedFor, forms: forms, formNames: formNames, field: field };
  if (node) { module.exports = Battle; } else { root.PreceptorBattle = Battle; }
})(typeof module === 'object' && module.exports ? this : window);
