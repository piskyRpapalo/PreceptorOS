(function (root) {
  'use strict';
  var node = typeof module === 'object' && module.exports;
  var cycleMs = 1000;

  function eggView(e, now, incuba) {
    var left = Math.max(0, e.hasta - now), total = Math.max(1, e.hasta - e.desde);
    return { seq: e.seq, tc: e.tc, left: left, pct: Math.min(100, Math.floor((total - left) * 100 / total)), ready: left === 0, incuba: incuba };
  }
  function afford(E, coste) { return E.cobre >= coste.cobre && E.luz >= coste.luz; }

  var Eggs = { cycleMs: cycleMs, eggView: eggView, afford: afford };
  if (node) { module.exports = Eggs; return; }

  var doc = root.document, A = root.AtlasArmy, G = root.AtlasGacha, H = root.PreceptorFaceHooks;
  if (!A || !G || !H || !H.army) { return; }
  var $ = function (id) { return doc.getElementById(id); };
  var store = A.cajaWeb('preceptor-face', 'estado', 'v1');
  var E = { ciclo: 0, cobre: 0, luz: 0, tut: null }, chain = [], chainBox = null, timer = 0, listeners = [], busy = false, ready = false;

  function save() { return store.pon(JSON.parse(JSON.stringify(E))).catch(function () {}); }
  function emit() { listeners.forEach(function (f) { f(E); }); }
  function eggs() { return A.huevos(chain).map(function (e) { return eggView(e, E.ciclo, G.TCS[e.tc].incuba); }); }
  function sound(k) { var S = root.AtlasSintesis; if (S && H.sound()) { S.activa(true); S.suena(k); } }

  function tick() {
    if (doc.hidden) { return; }
    E.ciclo++;
    if (E.ciclo % 5 === 0) { save(); }
    paint();
  }
  function run() { if (!timer) { timer = root.setInterval(tick, cycleMs); } }

  function paint() {
    var box = $('eggs'), l = eggs();
    while (box.firstChild) { box.removeChild(box.firstChild); }
    box.hidden = !l.length;
    l.forEach(function (e) {
      var b = doc.createElement('button'), lv = e.tc.replace('tc', 'Level ');
      b.type = 'button'; b.className = 'egg' + (e.ready ? ' go' : ''); b.dataset.seq = e.seq;
      b.innerHTML = '<span class="bar"><i></i></span><span class="lbl"></span>';
      b.firstChild.firstChild.style.width = e.pct + '%';
      b.lastChild.textContent = e.ready ? 'Hatch' : e.left + ' cycles';
      b.setAttribute('aria-label', 'Egg ' + lv + ': ' + (e.ready ? 'ready. Tap to hatch and adopt.' : e.left + ' cycles left, ' + e.pct + ' percent.'));
      b.disabled = !e.ready || busy;
      b.addEventListener('click', function () { hatch(e.seq); });
      box.appendChild(b);
    });
    var r = l.filter(function (e) { return e.ready; }).length;
    if (r && !ready) { H.bubble(r === 1 ? 'An egg is ready. Tap it at the top to hatch and adopt it.' : r + ' eggs are ready at the top.'); }
    ready = r > 0;
    shop();
    emit();
  }

  function shop() {
    var key = H.army.key();
    Array.prototype.forEach.call(doc.querySelectorAll('[data-egg]'), function (b) {
      var tc = b.dataset.egg, c = G.TCS[tc].coste;
      b.disabled = busy || !key || !afford(E, c) || H.army.full();
      b.setAttribute('aria-label', 'Summon an egg, ' + tc.replace('tc', 'Level ') + ': ' + c.cobre + ' copper' + (c.luz ? ', ' + c.luz + ' light' : '') + ', hatches in ' + G.TCS[tc].incuba + ' cycles');
    });
    $('purse').textContent = 'Copper ' + E.cobre + ' · Light ' + E.luz + (key ? '' : ' · Summons need your key: create it below.');
  }

  function loadChain(pub) {
    chainBox = A.cadenaWeb(pub);
    return chainBox.lee().then(function (c) {
      return A.verificaCadena(c || [], pub, A.verificaWeb, A.semillaWeb).then(function (bad) { chain = bad ? [] : (c || []); if (bad) { H.bubble('Your egg record did not verify (' + bad + '): NO_DATA, it starts empty.'); } paint(); });
    }).catch(function () { chain = []; paint(); });
  }

  function summon(tc) {
    var I = root.Identity, TC = G.TCS[tc];
    if (busy || !H.army.key() || !afford(E, TC.coste)) { return Promise.resolve(null); }
    busy = true; shop();
    return I.publica().then(function (pub) {
      var o = A.eslabon(chain, tc, pub);
      return I.firmar(o).then(function (f) {
        return A.semillaWeb(f.firma).then(function (seed) {
          chain = A.anexa(chain, o, f.firma, seed, E.ciclo, E.ciclo + TC.incuba);
          E.cobre -= TC.coste.cobre; E.luz -= TC.coste.luz;
          return Promise.all([chainBox.pon(chain), save()]);
        });
      });
    }).then(function () {
      sound('huevo');
      H.bubble('An egg of ' + tc.replace('tc', 'Level ') + ' is incubating: ' + TC.incuba + ' cycles. Watch it at the top of the screen. Odds: ' + root.PreceptorArmyOdds(tc));
      return true;
    }).catch(function (e) { H.bubble('The egg was not summoned: ' + (e && e.message ? e.message : e) + '.'); return null; })
      .then(function (r) { busy = false; paint(); return r; });
  }

  function hatch(seq) {
    var e = chain.filter(function (x) { return x.obj.seq === seq && !x.abierto; })[0];
    if (!e || busy || E.ciclo < e.hasta) { return Promise.resolve(null); }
    var t = G.tirada(e.semilla, e.obj.tc);
    busy = true; sound('eclosion');
    if (root.AtlasRevela) { root.AtlasRevela.muestra(t, function () {}); }
    return H.army.adopt(t).then(function () {
      chain = A.abre(chain, seq);
      return chainBox.pon(chain);
    }).then(function () {
      H.bubble('Hatched: a ' + root.PreceptorArmyName(t) + ' joins your Army. The roll: ' + t.aristas + ' edges (' + root.PreceptorEdgeOdds(e.obj.tc, t.aristas) + ' at ' + e.obj.tc.replace('tc', 'Level ') + ').');
      return t;
    }).catch(function (err) { H.bubble('Not adopted: ' + (err && err.message ? err.message : err) + '.'); return null; })
      .then(function (r) { busy = false; paint(); return r; });
  }

  function grant(cobre, luz, why) { E.cobre += cobre; E.luz += luz; save(); H.bubble(why + ' +' + cobre + ' copper' + (luz ? ', +' + luz + ' light' : '') + '.'); shop(); emit(); }

  Array.prototype.forEach.call(doc.querySelectorAll('[data-egg]'), function (b) { b.addEventListener('click', function () { summon(b.dataset.egg); }); });
  var hud = doc.querySelector('.hudtop');
  if (hud && root.ResizeObserver) { new root.ResizeObserver(function () { doc.documentElement.style.setProperty('--hudh', (hud.offsetHeight + 6) + 'px'); }).observe(hud); }
  doc.addEventListener('preceptor:identity', function () { if (root.Identity && root.Identity.quien()) { root.Identity.publica().then(loadChain); } shop(); });
  store.lee().then(function (s) {
    if (s && typeof s === 'object' && Number.isSafeInteger(s.ciclo)) { E = Object.assign(E, s); }
    if (root.Identity && root.Identity.quien && root.Identity.quien()) { return root.Identity.publica().then(loadChain); }
    paint();
  }).then(function () { run(); emit(); });
  if (!root.AtlasJuego) { root.AtlasJuego = { instantanea: function () { return { ciclo: E.ciclo }; }, texto: function () { return null; } }; }
  H.economy = { state: function () { return E; }, eggs: eggs, summon: summon, hatch: hatch, grant: grant, save: save, on: function (f) { listeners.push(f); }, cycle: function () { return E.ciclo; } };
})(typeof module === 'object' && module.exports ? this : window);
