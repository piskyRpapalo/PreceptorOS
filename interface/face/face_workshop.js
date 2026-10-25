(function (root) {
  'use strict';
  var doc = root.document, A = root.AtlasArmy, TL = root.AtlasTaller, V = root.AtlasValores, H = root.PreceptorFaceHooks;
  if (!A || !TL || !V || !H || !H.army) { return; }
  var $ = function (id) { return doc.getElementById(id); };
  var statNames = { velocidad: 'Speed', armadura: 'Armour', vida: 'Life', sigilo: 'Stealth' };
  var flagNames = { teal: 'Teal', ambar: 'Amber', hielo: 'Ice', violeta: 'Violet', coral: 'Coral', kelp: 'Kelp', oro: 'Gold', rosa: 'Rose' };
  var chain = [], box = null, est = TL.estado([]), sel = null, busy = false;

  function note(t) { $('ws-note').textContent = t; }
  function lija(semilla) { return est.lijas && est.lijas[semilla] ? Object.assign({}, est.lijas[semilla]) : null; }
  function tint(semilla) { var b = est.tintes ? est.tintes[semilla] : null; return b ? V.banderas[b] : null; }

  function load(pub) {
    box = A.cajaWeb('preceptor-face', 'taller', pub);
    return box.lee().then(function (c) {
      var e = TL.estado(c || []);
      if (e.error) { note('Workshop record did not verify (' + e.error + '): NO_DATA, it starts empty.'); chain = []; est = TL.estado([]); }
      else { chain = c || []; est = e; }
      paint(); H.army.paint();
    }).catch(function () { paint(); });
  }

  function op(o, done) {
    var I = root.Identity;
    if (busy || !H.army.key()) { return; }
    busy = true; paint();
    I.publica().then(function (pub) {
      var rec = TL.recibo(est, o, pub);
      return I.firmar(rec).then(function (f) {
        var next = chain.concat([{ recibo: rec, firma: f.firma }]), e = TL.estado(next);
        if (e.error) { throw new Error(e.error); }
        return Promise.resolve(done ? done(rec, f.firma) : null).then(function () { chain = next; est = e; return box.pon(chain); });
      });
    }).then(function () { H.army.paint(); }).catch(function (e) { note('Not done: ' + (e && e.message ? e.message : e) + '.'); })
      .then(function () { busy = false; paint(); });
  }

  function paint() {
    var list = H.army.list(), ul = $('ws-waves'), acts = $('ws-acts');
    if (!ul) { return; }
    while (ul.firstChild) { ul.removeChild(ul.firstChild); }
    while (acts.firstChild) { acts.removeChild(acts.firstChild); }
    $('ws-sand').textContent = 'Sand ' + (est.saldo || 0) + ' g';
    if (sel && !list.some(function (u) { return u.adopcion.tropa.semilla === sel; })) { sel = null; }
    list.forEach(function (u) {
      var t = u.adopcion.tropa, li = doc.createElement('li'), b = doc.createElement('button');
      b.type = 'button'; b.className = 'wave'; b.setAttribute('aria-pressed', String(sel === t.semilla));
      b.setAttribute('aria-label', 'Choose for the Workshop: ' + H.army.label(t));
      b.appendChild(H.army.thumb(t, 56));
      b.addEventListener('click', function () { sel = t.semilla; paint(); });
      li.appendChild(b); ul.appendChild(li);
    });
    if (!list.length) { note('The Workshop needs a wave: NO_DATA (Army empty).'); return; }
    if (!sel) { note('Tap a wave to improve, tint or dissolve it.'); return; }
    var u = list.filter(function (x) { return x.adopcion.tropa.semilla === sel; })[0], t = u.adopcion.tropa, lv = lija(sel) || {};
    V.taller.lija.stats.forEach(function (k) {
      var n = (lv[k] || 0) + 1, c = TL.coste(n), b = doc.createElement('button');
      b.type = 'button'; b.textContent = statNames[k] + ' +1 · ' + c + ' g';
      b.disabled = busy || n > V.taller.lija.max || est.saldo < c;
      b.addEventListener('click', function () { op({ op: 'lija', semilla: sel, stat: k }); });
      acts.appendChild(b);
    });
    Object.keys(V.banderas).forEach(function (f) {
      var b = doc.createElement('button');
      b.type = 'button'; b.className = 'chip'; b.style.background = 'hsl(' + V.banderas[f] + ' 70% 60%)';
      b.setAttribute('aria-label', 'Tint ' + flagNames[f] + ' · ' + V.taller.tinte.coste + ' g');
      b.disabled = busy || est.saldo < V.taller.tinte.coste || (est.tintes && est.tintes[sel] === f);
      b.addEventListener('click', function () { op({ op: 'tinte', semilla: sel, bandera: f }); });
      acts.appendChild(b);
    });
    var d = doc.createElement('button');
    d.type = 'button'; d.className = 'warn'; d.textContent = 'Dissolve · +' + TL.residuo(t) + ' g';
    d.disabled = busy;
    d.addEventListener('click', function () { op({ op: 'desintegra', tropa: t }, function (rec, f) { return H.army.retire(rec, f); }); });
    acts.appendChild(d);
    note('Improve raises a stat for battle; tint changes its colour; dissolving turns the wave into sand. Every change is signed by your key.');
  }

  doc.addEventListener('preceptor:identity', function () { if (root.Identity && root.Identity.quien()) { root.Identity.publica().then(load); } });
  H.army.on(paint);
  if (root.Identity && root.Identity.quien && root.Identity.quien()) { root.Identity.publica().then(load); } else { paint(); }
  H.workshop = { lija: lija, tint: tint, sand: function () { return est.saldo || 0; }, op: op, select: function (s) { sel = s; paint(); } };
})(window);
