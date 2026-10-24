(function (root) {
  'use strict';
  var node = typeof module === 'object' && module.exports;
  function lib(name, file) { return root[name] || (node ? require(file) : null); }
  var T = lib('AtlasCombateTicks', '../../../public/game/combate_ticks.js');
  var G = lib('AtlasGacha', '../../../public/game/gacha.js');
  var K = lib('AtlasCanon', '../../../public/game/canon.js');
  var E = lib('AtlasEscuadron', '../../../public/game/escuadron.js');
  var V = lib('AtlasValores', '../../../public/game/valores.js');
  var codex = {
    normal: 'f7b0f1c774f54b6f3efdfd51b2b6a9600380410f45449c38907e61846e4ef729',
    magico: 'a23d525508b2c6f0074aecea13737118b2729f9842c17a2d1161b3540a30e0e1',
    raro: '1d60dc3e11deee79b2c8836e7fdee51d9ac2a59767d852d5ee55b251ee0abb8c',
    unico: '9a342ec9292ec93c7a4de5450a402e2a2d74864e2d3aeb9d0747d9cbcf57ed1b'
  };
  var forms = ['agresiva', 'defensiva', 'flanqueo'];
  var formNames = { agresiva: 'Spear', defensiva: 'Shield', flanqueo: 'Wings' };
  var spots = [[[440, 300], [490, 326], [540, 300]], [[436, 104], [486, 82], [536, 104]]];

  function teams(squad) {
    return {
      def: squad && squad.length ? squad.slice(0, 3) : [{ semilla: codex.normal, tc: 'tc3' }, { semilla: codex.magico, tc: 'tc3' }, { semilla: codex.raro, tc: 'tc3' }],
      asa: [{ semilla: K.sha('preceptor.face/enemy:1'), tc: 'tc3' }, { semilla: K.sha('preceptor.face/enemy:2'), tc: 'tc3' }, { semilla: codex.unico, tc: 'tc2' }]
    };
  }
  var seed = K.sha('preceptor.face/battle:rift');

  function create() {
    var t, draws;
    function load() { t = teams(root.PreceptorArmySquad); draws = [t.def.map(function (x) { return G.tirada(x.semilla, x.tc); }), t.asa.map(function (x) { return G.tirada(x.semilla, x.tc); })]; }
    load();
    var b = { on: false, form: 'defensiva', orders: [], st: null, last: [], result: null, receipt: null, verified: null, reveal: 0 };

    function begin() {
      load();
      b.on = true; b.orders = []; b.result = null; b.receipt = null; b.verified = null; b.last = []; b.reveal = 0;
      b.st = T.inicia(t.def, t.asa, seed);
      return b;
    }
    function done() { return !!b.result; }
    function step() {
      if (!b.st || done()) { return false; }
      var st = b.st, n0 = st.registro.length, ok;
      b.orders.forEach(function (o) { if (o.tick === st.ronda + 1) { st.U[o.lado][o.i].vida = 0; } });
      ok = T.ronda(st);
      b.last = st.registro.slice(n0);
      if (!ok || !(st.ronda < st.P.rondas && alive(0).length && alive(1).length)) { finish(); }
      return true;
    }
    function alive(l) { return b.st.U[l].filter(function (u) { return u.vida > 0; }); }
    function finish() {
      b.result = T.cierra(b.st);
      var r = T.recibo(t.def, t.asa, seed, b.orders);
      b.receipt = r.ok ? r.texto : 'NO_DATA: ' + r.motivo;
      b.teams = t;
      b.verified = r.ok ? T.verifica(r.recibo, t.def, t.asa) : { ok: false, motivo: r.motivo };
    }
    function withdraw(i) {
      if (!b.st || done() || b.orders.length >= 1) { return false; }
      var u = b.st.U[0][i];
      if (!u || u.vida <= 0) { return false; }
      b.orders.push({ tick: b.st.ronda + 1, lado: 0, i: i, accion: 'retira' });
      return true;
    }
    function form(f) { if (forms.indexOf(f) >= 0) { b.form = f; } }

    function troops() {
      var out = [];
      [0, 1].forEach(function (l) {
        draws[l].forEach(function (d, i) {
          var u = b.st ? b.st.U[l][i] : { vida: d.stats.vida, max: d.stats.vida };
          out.push({ lado: l, i: i, d: d, vida: u.vida, max: u.max, at: spots[l][i], name: d.rareza });
        });
      });
      return out;
    }

    function frame(change) {
      var atoms = [0, 1].map(function (l) {
        var list = troops().filter(function (x) { return x.lado === l; });
        return { k: l ? 'theirs' : 'yours', r: (l ? 'enemy: ' : 'yours, ' + formNames[b.form] + ': ') + list.map(function (x) { return x.name + ' ' + x.vida + '/' + x.max; }).join(', '),
          i: list.filter(function (x) { return x.vida > 0; }).map(function (x) {
            var lim = 0;
            x.d.armonicos.forEach(function (h) { lim += Math.max(Math.abs(h[1]), Math.abs(h[2])); });
            return { o: 'wave', x: x.at[0], y: x.at[1], sc: Math.round(2200 / (lim || 1)) / 100, h: x.d.armonicos.map(function (h) { return [h[0], Math.round(h[1]), Math.round(h[2]), Math.round(h[3])]; }), f: l ? 'vermilion.base' : 'cyan' };
          }) };
      });
      return { v: 'preceptoros.bubble/1', id: 'battle', t: b.st ? b.st.ronda : 0, atoms: atoms, bands: ['cyan', 'vermilion.base', 'ink'],
        change: [change || (b.result ? 'verdict: ' + b.result.gana : 'tick ' + (b.st ? b.st.ronda : 0))], sound: 'NO_DATA', soundCause: 'sound off', motion: 'tick by tick' };
    }

    function paint(g, toScreen, z, quiet) {
      if (!b.on) { return; }
      var O = root.AtlasOnda, list = troops(), cap = V.army_tope || 30, per = Math.floor(cap / 3), k = Math.max(0.35, z);
      list.forEach(function (x) {
        var p = toScreen(x.at[0], x.at[1]), r = 26 * k, frac = x.max ? x.vida / x.max : 0, tone = O.tono(x.d), c = O.colorVida(frac, tone);
        if (x.vida <= 0) { return; }
        if (x.lado === 0) {
          var n = Math.min(per, E.cuantas(x.d.aristas)), s = E.sitios(n, x.d.semilla, b.form);
          for (var i = 1; i < E.vivas(n, x.vida, x.max); i++) { O.dibuja(g, x.d.armonicos, p[0] + s[i][0] * r * 0.9, p[1] + s[i][1] * r * 0.55, r * 0.22, { calidad: 0, color: c, alfa: 0.75 }); }
        }
        var grow = b.reveal && x.lado === 0 ? Math.min(x.d.armonicos.length, 1 + Math.floor(b.reveal / 6)) : x.d.armonicos.length;
        O.dibuja(g, x.d.armonicos.slice(0, grow), p[0], p[1] - r * 0.4, r, { calidad: quiet ? 1 : 2, color: c, face: true, estela: quiet ? 0 : 2, giro: (b.st ? b.st.ronda : 0) * 0.35 * (x.lado ? -1 : 1) });
      });
      g.save();
      b.last.forEach(function (e) {
        var a = list.filter(function (x) { return x.lado === e[1] && x.i === e[2]; })[0], d = list.filter(function (x) { return x.lado !== e[1] && x.i === e[3]; })[0];
        if (!a || !d) { return; }
        var p = toScreen(a.at[0], a.at[1]), q = toScreen(d.at[0], d.at[1]);
        g.setLineDash(e[4] < 0 ? [4, 6] : []);
        g.strokeStyle = e[1] ? 'rgba(230,57,70,.85)' : 'rgba(0,210,255,.85)'; g.lineWidth = Math.max(2, 3 * k);
        g.beginPath(); g.moveTo(p[0], p[1] - 10 * k); g.quadraticCurveTo((p[0] + q[0]) / 2, Math.min(p[1], q[1]) - 50 * k, q[0], q[1] - 10 * k); g.stroke();
      });
      g.restore();
    }

    function sonar(A) {
      if (!A) { return; }
      A.activa(true);
      A.suena({ tipo: 'sonar', portadora: 1320, moduladora: 660, indice: 90, dur: 0.5, gan: 0.08 });
    }

    function summary() {
      return { on: b.on, tick: b.st ? b.st.ronda : 0, form: b.form, orders: b.orders.slice(), result: b.result && { gana: b.result.gana, rondas: b.result.rondas, vida_por_mil: b.result.vida_por_mil },
        receipt: b.receipt, verified: b.verified, troops: troops().map(function (x) { return { side: x.lado ? 'enemy' : 'yours', name: x.name, life: x.vida, max: x.max }; }) };
    }

    return { begin: begin, step: step, done: done, withdraw: withdraw, form: form, frame: frame, paint: paint, sonar: sonar, summary: summary, troops: troops, b: b };
  }

  var Battle = { create: create, teams: teams, seed: seed, forms: forms, formNames: formNames };
  if (node) { module.exports = Battle; } else { root.PreceptorBattle = Battle; }
})(typeof module === 'object' && module.exports ? this : window);
