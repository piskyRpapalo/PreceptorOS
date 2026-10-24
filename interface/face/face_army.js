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
  function link(tc, n, pub) { return { esquema: 'preceptor.face.invoca/1', tc: tc, n: n, clave: pub }; }

  var Army = { names: names, oddsText: oddsText, edgeOdds: edgeOdds, link: link };
  if (node) { module.exports = Army; return; }

  var doc = root.document, A = root.AtlasArmy, G = root.AtlasGacha, O = root.AtlasOnda, H = root.PreceptorFaceHooks;
  if (!A || !G || !O || !H) { return; }
  var $ = function (id) { return doc.getElementById(id); };
  var skin = JSON.parse($('skin').textContent);
  var army = A.crea(A.verificaWeb, A.almacenWeb ? A.almacenWeb() : null), tc = 'tc1', pending = null, summons = 0;
  root.AtlasIncubadora = root.AtlasIncubadora || { army: function () { return army.lista(); } };

  function key() { return root.Identity && root.Identity.quien ? root.Identity.quien() : null; }
  function note(t) { $('g-note').textContent = t; }

  function thumb(t) {
    var c = doc.createElement('canvas'), d = Math.min(2, root.devicePixelRatio || 1), g = c.getContext('2d');
    c.width = 72 * d; c.height = 72 * d; c.setAttribute('aria-hidden', 'true');
    g.setTransform(d, 0, 0, d, 0, 0);
    O.dibuja(g, t.armonicos, 36, 38, 24, { calidad: 1, color: O.tono(t), face: true });
    return c;
  }

  function paint() {
    var ul = $('army'), list = army.lista();
    while (ul.firstChild) { ul.removeChild(ul.firstChild); }
    list.forEach(function (u) {
      var t = u.adopcion.tropa, li = doc.createElement('li'), b = doc.createElement('button');
      b.type = 'button'; b.className = 'wave';
      b.setAttribute('aria-label', names[t.rareza] + ' wave, ' + t.aristas + ' edges, life ' + t.stats.vida + '. Open its card.');
      b.appendChild(thumb(t));
      b.addEventListener('click', function () { if (root.AtlasArmyWavePanel) { root.AtlasArmyWavePanel.abre(t); } });
      li.appendChild(b); ul.appendChild(li);
    });
    $('army-note').textContent = list.length ? 'Your Army: ' + list.length + ' of ' + A.TOPE + ' waves. Tap one to open its card. The first three fight at the rift.'
      : 'Your Army is empty: NO_DATA (no waves adopted yet). Summon one below with your key, then adopt it.';
    H.panel.mark('battle', list.length ? 'LIVE' : 'NO_DATA');
    root.PreceptorArmySquad = list.slice(0, 3).map(function (u) { return { semilla: u.adopcion.tropa.semilla, tc: u.adopcion.tropa.tc }; });
    profile();
  }

  function odds() {
    $('odds').textContent = 'Odds at ' + tc.replace('tc', 'Level ') + ': ' + oddsText(G, tc);
    Array.prototype.forEach.call(doc.querySelectorAll('[data-tc]'), function (b) { b.setAttribute('aria-pressed', String(b.dataset.tc === tc)); });
  }

  function summon() {
    if (!key()) { note('Summoning needs your key: NO_DATA (no key on this device yet). Open Profile and create your key.'); H.bubble('A summon is signed by you. Open Profile to create your key first.'); return; }
    if (army.lista().length >= A.TOPE) { note('Your Army is full (' + A.TOPE + ' waves).'); return; }
    var I = root.Identity;
    note('Signing the summon with your key…');
    I.publica().then(function (pub) {
      return I.firmar(link(tc, army.lista().length + summons, pub));
    }).then(function (f) {
      summons++;
      return A.semillaWeb(f.firma);
    }).then(function (seed) {
      var t = G.tirada(seed, tc);
      pending = t;
      $('g-adopt').disabled = false;
      var said = 'The roll: a ' + names[t.rareza] + ' wave with ' + t.aristas + ' edges (that edge count had ' + edgeOdds(G, tc, t.aristas) + ' at ' + tc.replace('tc', 'Level ') + '). Seed ' + seed.slice(0, 12) + '… from your signature.';
      note(said);
      H.bubble(said + ' Sign again to adopt it into your Army.');
      if (root.AtlasRevela) { root.AtlasRevela.muestra(t, function () {}); }
    }).catch(function (e) { note('NO_DATA: the summon was not signed (' + (e && e.message ? e.message : e) + ').'); });
  }

  function adopt() {
    if (!pending || !key()) { return; }
    var I = root.Identity, t = pending;
    I.publica().then(function (pub) {
      var ad = A.adopcion(t, key(), pub);
      return I.firmar(ad).then(function (f) { return army.adopta(ad, f.firma); });
    }).then(function () {
      pending = null; $('g-adopt').disabled = true;
      note('Adopted: verified by your signature and kept on this device.');
      H.bubble('A ' + names[t.rareza] + ' wave joins your Army. It will fight at the rift.');
      paint();
    }).catch(function (e) { note('Not adopted: ' + (e && e.message ? e.message : e) + '.'); });
  }

  function profile() {
    var s = root.preceptorFace ? root.preceptorFace.state() : null, cv = $('me-art'), dl = $('me-stats');
    if (!s || !cv) { return; }
    var d = Math.min(2, root.devicePixelRatio || 1), g = cv.getContext('2d'), c = s.crab;
    cv.width = 120 * d; cv.height = 120 * d; g.setTransform(d, 0, 0, d, 0, 0); g.clearRect(0, 0, 120, 120);
    if (skin.hero && root.PreceptorHero) { root.AtlasComicAtoms.paint(g, root.AtlasBubble.compile(root.PreceptorHero.heroFrame(skin, c.clase, 1))); }
    else if (root.AtlasToon && root.AtlasCangrejo) { g.setTransform(1, 0, 0, 1, 0, 0); root.AtlasToon.cangrejo(g, 60 * d, 96 * d, 40 * d, { forma: root.AtlasCangrejo.forma(c.army, c.node, null), cuerpo: root.AtlasCangrejo.cuerpo({ army: c.army, nucleo: 3 * Math.min(s.done, 3) }), dir: 1, dpr: d, quieto: true, id: 'me' }); }
    cv.setAttribute('aria-label', 'You: a ' + c.clase + (skin.hero ? ' space soldier' : ' crab') + ', size ' + Math.round(c.escala * 100) / 100);
    var rows = [['Size', String(Math.round(c.escala * 100) / 100)], ['Colour', c.clase === 'coral' ? 'coral (holds a node, EMULADO)' : 'sea blue'], ['Places measured', String(s.done)],
      ['Waves adopted', army.lista().length + ' of ' + A.TOPE], ['Your key', key() || 'NO_DATA (not created yet)'], ['Growth rule', c.rule]];
    dl.innerHTML = '';
    rows.forEach(function (r) { var dt = doc.createElement('dt'), dd = doc.createElement('dd'); dt.textContent = r[0]; dd.textContent = r[1]; dl.appendChild(dt); dl.appendChild(dd); });
  }

  Array.prototype.forEach.call(doc.querySelectorAll('[data-tc]'), function (b) { b.addEventListener('click', function () { tc = b.dataset.tc; odds(); }); });
  $('g-summon').addEventListener('click', summon);
  $('g-adopt').addEventListener('click', adopt);
  doc.addEventListener('preceptor:identity', profile);
  new root.MutationObserver(function () { if (doc.body.dataset.view === 'profile') { profile(); } }).observe(doc.body, { attributes: true, attributeFilter: ['data-view'] });
  odds(); paint();
  army.restaura().then(paint);
  H.army = { list: function () { return army.lista(); }, summon: summon, adopt: adopt, tc: function (x) { if (x) { tc = x; odds(); } return tc; } };
})(typeof module === 'object' && module.exports ? this : window);
