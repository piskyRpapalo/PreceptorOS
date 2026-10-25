(function (root) {
  'use strict';
  var node = typeof module === 'object' && module.exports;
  var names = { normal: 'Common', magico: 'Uncommon', raro: 'Rare', unico: 'Leviathan' };

  function oddsText(G, tc) {
    var o = G.odds(tc);
    return G.RAREZAS.map(function (r, i) { return names[r] + ' ' + (o[i] / 10).toFixed(1) + '%'; }).join(' · ') + '. No hidden odds.';
  }
  function edgeOdds(G, tc, edges) {
    var row = G.oddsAristas(tc).filter(function (x) { return x[0] === edges; })[0];
    return row ? (row[1] / 10).toFixed(1) + '%' : 'NO_DATA';
  }

  var Army = { names: names, oddsText: oddsText, edgeOdds: edgeOdds };
  if (node) { module.exports = Army; return; }

  var doc = root.document, A = root.AtlasArmy, O = root.AtlasOnda, H = root.PreceptorFaceHooks;
  if (!A || !O || !H) { return; }
  var $ = function (id) { return doc.getElementById(id); };
  var skin = JSON.parse($('skin').textContent);
  var army = A.crea(A.verificaWeb, A.almacenWeb ? A.almacenWeb() : null), listeners = [];
  root.AtlasIncubadora = root.AtlasIncubadora || { army: function () { return army.lista(); } };

  function key() { return root.Identity && root.Identity.quien ? root.Identity.quien() : null; }
  function tone(t) { var W = H.workshop, b = W ? W.tint(t.semilla) : null; return b != null ? [b, 70, 66] : O.tono(t); }

  function thumb(t, size) {
    var c = doc.createElement('canvas'), d = Math.min(2, root.devicePixelRatio || 1), g = c.getContext('2d'), s = size || 72;
    c.width = s * d; c.height = s * d; c.setAttribute('aria-hidden', 'true');
    g.setTransform(d, 0, 0, d, 0, 0);
    O.dibuja(g, t.armonicos, s / 2, s / 2 + 2, s / 3, { calidad: 1, color: tone(t), face: true });
    return c;
  }

  function label(t) { return names[t.rareza] + ' wave, ' + t.aristas + ' edges, life ' + t.stats.vida; }

  function list() { return army.lista(); }
  function squad() {
    var W = H.workshop;
    return list().slice(0, 10).map(function (u) { var t = u.adopcion.tropa, l = W ? W.lija(t.semilla) : null; return l ? { semilla: t.semilla, tc: t.tc, lija: l } : { semilla: t.semilla, tc: t.tc }; });
  }

  function paint() {
    var ul = $('army'), l = list();
    while (ul.firstChild) { ul.removeChild(ul.firstChild); }
    l.forEach(function (u) {
      var t = u.adopcion.tropa, li = doc.createElement('li'), b = doc.createElement('button');
      b.type = 'button'; b.className = 'wave';
      b.setAttribute('aria-label', label(t) + '. Open its card.');
      b.appendChild(thumb(t));
      b.addEventListener('click', function () { if (root.AtlasArmyWavePanel) { root.AtlasArmyWavePanel.abre(t); } });
      li.appendChild(b); ul.appendChild(li);
    });
    $('army-note').textContent = l.length ? l.length + ' of ' + A.TOPE + ' waves. Up to 10 fight together. Tap one for its card.'
      : 'Your Army is empty: NO_DATA (no waves adopted yet). Hatch an egg from your Profile to get one.';
    H.panel.mark('battle', l.length ? 'LIVE' : 'NO_DATA');
    root.PreceptorArmySquad = squad();
    profile();
    listeners.forEach(function (f) { f(l); });
  }

  function adopt(t) {
    var I = root.Identity;
    if (!key()) { return Promise.reject(new Error('NO_DATA: no key on this device yet')); }
    return I.publica().then(function (pub) {
      var ad = A.adopcion(t, key(), pub);
      return I.firmar(ad).then(function (f) { return army.adopta(ad, f.firma); });
    }).then(function (u) {
      if (root.AtlasSintesis && H.sound()) { root.AtlasSintesis.activa(true); root.AtlasSintesis.suena('adopcion'); }
      paint();
      return u;
    });
  }

  function profile() {
    var s = root.preceptorFace ? root.preceptorFace.state() : null, cv = $('me-art'), dl = $('me-stats');
    if (!s || !cv) { return; }
    var d = Math.min(2, root.devicePixelRatio || 1), g = cv.getContext('2d'), c = s.crab, E = H.economy ? H.economy.state() : null;
    cv.width = 120 * d; cv.height = 120 * d; g.setTransform(d, 0, 0, d, 0, 0); g.clearRect(0, 0, 120, 120);
    if (skin.hero && root.PreceptorHero) { root.AtlasComicAtoms.paint(g, root.AtlasBubble.compile(root.PreceptorHero.heroFrame(skin, c.clase, 1))); }
    else if (root.AtlasToon && root.AtlasCangrejo) { g.setTransform(1, 0, 0, 1, 0, 0); root.AtlasToon.cangrejo(g, 60 * d, 96 * d, 40 * d, { forma: root.AtlasCangrejo.forma(c.army, c.node, null), cuerpo: root.AtlasCangrejo.cuerpo({ army: c.army, nucleo: 3 * Math.min(s.done, 3) }), dir: 1, dpr: d, quieto: true, id: 'me' }); }
    cv.setAttribute('aria-label', 'You: a ' + c.clase + (skin.hero ? ' space soldier' : ' crab') + ', size ' + Math.round(c.escala * 100) / 100);
    var rows = [['Size', String(Math.round(c.escala * 100) / 100)], ['Colour', c.clase === 'coral' ? 'coral (holds a node, EMULADO)' : 'sea blue'],
      ['Copper', E ? String(E.cobre) : 'NO_DATA'], ['Light', E ? String(E.luz) : 'NO_DATA'], ['Waves', list().length + ' of ' + A.TOPE], ['Your key', key() || 'NO_DATA (not created yet)']];
    dl.innerHTML = '';
    rows.forEach(function (r) { var dt = doc.createElement('dt'), dd = doc.createElement('dd'); dt.textContent = r[0]; dd.textContent = r[1]; dl.appendChild(dt); dl.appendChild(dd); });
  }

  doc.addEventListener('preceptor:identity', function () { profile(); listeners.forEach(function (f) { f(list()); }); });
  new root.MutationObserver(function () { if (doc.body.dataset.view === 'profile') { profile(); } }).observe(doc.body, { attributes: true, attributeFilter: ['data-view'] });
  paint();
  army.restaura().then(paint);
  function retire(rec, f) { return army.retira(rec, f).then(function (u) { paint(); return u; }); }
  var G = root.AtlasGacha;
  root.PreceptorArmyOdds = function (tc) { return oddsText(G, tc); };
  root.PreceptorEdgeOdds = function (tc, n) { return edgeOdds(G, tc, n); };
  root.PreceptorArmyName = function (t) { return names[t.rareza] + ' wave'; };
  H.army = { retire: retire, list: list, squad: squad, adopt: adopt, paint: paint, profile: profile, thumb: thumb, label: label, key: key, tone: tone, full: function () { return list().length >= A.TOPE; }, on: function (f) { listeners.push(f); } };
})(typeof module === 'object' && module.exports ? this : window);
