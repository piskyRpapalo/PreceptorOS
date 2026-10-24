
(function (root) {
  'use strict';
  function modelo(t, V, G) {
    if (!t || !Array.isArray(t.armonicos) || !G || !V) { return { causa: 'NO_DATA (wave or measured rules unavailable)' }; }
    return { tc: t.tc, aristas: Number.isSafeInteger(t.aristas) ? t.aristas : null,
      armonicos: t.armonicos.map(function (h) { return h.join(','); }).join(';'),
      lore: { base: t.base || null, prefijo: t.prefijo || null, sufijo: t.sufijo || null },
      stats: G.STATS.map(function (k) {
        var s = V.semantica[k];
        return { id: k, valor: Number.isFinite(t.stats[k]) ? t.stats[k] : null,
          formula: s && s[0] || 'NO_DATA (formula missing)', fuente: s && s[1] || 'NO_DATA (source missing)',
          clase: s && s[2] || 'NO_DATA (class missing)', lector: s && s[3] || 'NO_DATA (reader missing)' };
      }) };
  }
  function monta(t) {
    var V = root.AtlasValores, G = root.AtlasGacha, M = modelo(t, V, G), d = root.document;
    if (M.causa || !d) { return null; }
    function el(tag, cls, value) { var n = d.createElement(tag); if (cls) { n.className = cls; } if (value != null) { n.textContent = value; } return n; }
    function T(k, fallback) { var a = root.AtlasJuego && root.AtlasJuego.texto(k); return a && a !== k ? a : fallback; }
    var card = el('section', 'revela-ficha'), title = el('h2', null, T('summon_wave_title', 'Your new wave'));
    card.hidden = true; card.appendChild(title);
    var lore = [M.lore.base && T('base_' + M.lore.base, M.lore.base), M.lore.prefijo && T('af_' + M.lore.prefijo, M.lore.prefijo), M.lore.sufijo && T('af_' + M.lore.sufijo, M.lore.sufijo)].filter(Boolean);
    card.appendChild(el('p', 'revela-ficha-lore', lore.length ? lore.join(' · ') : 'NO_DATA (this wave declares no base or affix lore)'));
    var ecu = 'X(θ)=Σ ax·cos(kθ + phase·π/32); Y(θ)=Σ ay·sin(kθ + phase·π/32)';
    card.appendChild(el('p', 'revela-ficha-ecuacion', 'TC ' + M.tc + ' · ' + (M.aristas == null ? 'NO_DATA (edge count missing)' : M.aristas + ' edges') + ' · coefficient order [k, ax, ay, phase] · ' + ecu));
    card.appendChild(el('code', 'revela-ficha-vector', '[' + M.armonicos + ']'));
    card.appendChild(el('p', 'revela-ficha-stats', 'Stats: ' + M.stats.map(function (s) { return s.id + ' ' + (s.valor == null ? 'NO_DATA (stat missing)' : s.valor); }).join(' · ')));
    var more = el('details', 'revela-ficha-fuentes'); more.appendChild(el('summary', null, T('tecnico', 'Technical details')));
    M.stats.forEach(function (s) { more.appendChild(el('p', null, s.id + ': ' + s.formula + ' · ' + s.fuente + ' · ' + s.clase + ' · ' + s.lector)); });
    card.appendChild(more);
    var go = el('button', 'boton revela-personaliza', T('summon_personalize', 'Personalize'));
    go.type = 'button'; go.setAttribute('aria-label', 'Personalize this wave in Workshop'); card.appendChild(go);
    return { element: card, button: go, model: M };
  }
  function personaliza() {
    if (!root.TheGame || !root.TheGame.ve || !root.document) { return false; }
    root.TheGame.ve('ondas');
    root.requestAnimationFrame(function () {
      var section = root.document.querySelector('#thegame-ondas .taller-unido');
      if (section) { section.scrollIntoView({ block: 'start' }); section.setAttribute('tabindex', '-1'); section.focus(); }
    });
    return true;
  }
  var API = { modelo: modelo, monta: monta, personaliza: personaliza };
  if (typeof module === 'object' && module.exports) { module.exports = API; } else { root.AtlasRevelaFicha = API; }
})(typeof window === 'object' ? window : globalThis);
