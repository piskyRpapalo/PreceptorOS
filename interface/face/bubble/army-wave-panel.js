
(function (root) {
  'use strict';
  function modelo(t, niveles, V, G) {
    if (!t || !t.stats || !G || !V) { return { causa: 'NO_DATA (the shared Army wave or its measured rules are unavailable)' }; }
    var filas = G.STATS.map(function (k) {
      var d = niveles && niveles[k] || {}, sem = d.semantica || V.semantica[k], base = t.stats[k];
      var eligible = !!d.permitida, nivel = Number.isSafeInteger(d.nivel) ? d.nivel : null, max = Number.isSafeInteger(d.max) ? d.max : 0;
      return { id: k, base: Number.isFinite(base) ? base : null, valor: Number.isFinite(base) && (!eligible || nivel !== null) ? base + (eligible ? nivel * (d.paso || 0) : 0) : null,
        formula: sem && sem[0] || 'NO_DATA (semantic formula is missing)', fuente: sem && sem[1] || 'NO_DATA (semantic source is missing)',
        clase: sem && sem[2] || 'NO_DATA (semantic class is missing)', lector: sem && sem[3] || 'NO_DATA (semantic reader is missing)',
        nivel: nivel, max: max, coste: Number.isSafeInteger(d.coste) ? d.coste : null, disponible: !!d.disponible, causa: d.causa || null };
    });
    var odds = G.odds(t.tc).map(function (n, i) { return { rareza: G.RAREZAS[i], promil: n, porcentaje: (n / 10).toFixed(1) + '%' }; });
    return { matematicas: { tc: t.tc, aristas: Number.isSafeInteger(t.aristas) ? t.aristas : null,
        armonicos: Array.isArray(t.armonicos) ? t.armonicos.length : null,
        regla: 'TC edge table → edge-derived rarity → seeded base and affix formulas; equal seed and values give the same wave' },
      origen: { base: t.base || null, rareza: t.rareza || null, prefijo: t.prefijo || null, sufijo: t.sufijo || null },
      stats: filas, odds: odds, aristas: G.oddsAristas(t.tc) };
  }
  var dialogo = null, cuerpo = null, titulo = null, estado = null, anterior = null, semilla = null, renderOnda = null;
  function el(tag, clase, texto) { var n = root.document.createElement(tag); if (clase) { n.className = clase; } if (texto != null) { n.textContent = String(texto); } return n; }
  function texto(k, fallback) { var C = root.AtlasCasa, J = root.AtlasJuego, a = C && C.texto && C.texto(k), b = J && J.texto && J.texto(k); return a && a !== k ? a : b && b !== k ? b : fallback; }
  function waveActual() {
    var I = root.AtlasIncubadora, A = I && I.army ? I.army() : [];
    for (var i = 0; Array.isArray(A) && i < A.length; i++) { var t = A[i] && A[i].adopcion && A[i].adopcion.tropa; if (t && t.semilla === semilla) { return t; } }
    return null;
  }
  function cierra() { if (dialogo && dialogo.open) { dialogo.close(); if (anterior && anterior.isConnected) { anterior.focus(); } } }
  function monta() {
    if (dialogo) { return; }
    dialogo = el('dialog', 'army-wave-dialog'); dialogo.id = 'army-wave-dialog'; dialogo.setAttribute('aria-labelledby', 'army-wave-title');
    var top = el('header', 'army-wave-head'); titulo = el('h2'); titulo.id = 'army-wave-title'; top.appendChild(titulo);
    var close = el('button', 'boton-sec', 'Close'); close.type = 'button'; close.setAttribute('aria-label', 'Close wave details'); close.addEventListener('click', cierra); top.appendChild(close); dialogo.appendChild(top);
    cuerpo = el('div', 'army-wave-body'); dialogo.appendChild(cuerpo);
    estado = el('p', 'army-wave-status'); estado.setAttribute('role', 'status'); dialogo.appendChild(estado);
    dialogo.addEventListener('cancel', function () { cierra(); }); root.document.body.appendChild(dialogo);
  }
  function pinta() {
    var t = waveActual(), G = root.AtlasGacha, V = root.AtlasValores, T = root.AtlasTallerUI;
    cuerpo.textContent = '';
    if (!t) { cuerpo.appendChild(el('p', 'no-data', 'NO_DATA (this wave is no longer in the shared Army)')); return; }
    titulo.textContent = (renderOnda && renderOnda.nombre ? renderOnda.nombre(t) : 'Wave') + ' · ' + (t.rareza || 'NO_DATA');
    if (renderOnda) { cuerpo.appendChild(renderOnda(t, 168)); }
    var geo = el('section', 'army-wave-section'); geo.appendChild(el('h3', null, 'Mathematical description'));
    geo.appendChild(el('p', null, 'TC ' + t.tc + ' · ' + (t.aristas == null ? 'NO_DATA (edge count missing)' : t.aristas + ' measured edges') + ' · ' + (t.armonicos ? t.armonicos.length + ' harmonics' : 'NO_DATA (harmonics missing)')));
    geo.appendChild(el('p', null, 'The TC edge table sets rarity; the signed seed and values generate the same harmonics and stats on every device.')); cuerpo.appendChild(geo);
    var lore = el('section', 'army-wave-section'); lore.appendChild(el('h3', null, 'Origin'));
    var parts = [t.base && texto('base_' + t.base, t.base), t.prefijo && texto('af_' + t.prefijo, t.prefijo), t.sufijo && texto('af_' + t.sufijo, t.sufijo)].filter(Boolean);
    lore.appendChild(el('p', null, parts.length ? parts.join(' · ') : 'NO_DATA (the signed wave declares no base or affix lore)')); cuerpo.appendChild(lore);
    var statBox = el('section', 'army-wave-section'); statBox.appendChild(el('h3', null, 'Measured stats and Workshop levels'));
    var details = {};
    G.STATS.forEach(function (k) { details[k] = T && T.detalleStat ? T.detalleStat(semilla, k) : { causa: 'NO_DATA (Workshop detail reader is unavailable)' }; });
    var m = modelo(t, details, V, G);
    m.stats.forEach(function (s) {
      var row = el('article', 'army-wave-stat'); row.dataset.stat = s.id;
      var label = el('h4', null, texto('st_' + s.id, s.id)); row.appendChild(label);
      row.appendChild(el('p', 'army-wave-value', s.valor == null ? 'NO_DATA (stat is absent)' : String(s.valor)));
      row.appendChild(el('p', 'army-wave-source', 'Formula: ' + s.formula + ' · From: ' + s.fuente + ' · ' + s.clase + ' · Read by ' + s.lector));
      if (s.max > 0 && s.nivel !== null) {
        var bar = el('progress', 'army-wave-level'); bar.max = s.max; bar.value = Math.min(s.nivel, s.max); bar.setAttribute('aria-label', s.id + ' Workshop level ' + s.nivel + ' of ' + s.max); row.appendChild(bar);
        row.appendChild(el('span', null, 'Level ' + s.nivel + ' / ' + s.max));
      } else if (s.max > 0) { row.appendChild(el('p', 'no-data', 'NO_DATA (Workshop receipt chain has not been verified)')); }
      else { row.appendChild(el('p', 'no-data', 'NO_DATA (no Workshop level applies to this stat)')); }
      var plus = el('button', 'boton-sec army-wave-plus', '+'); plus.type = 'button'; plus.setAttribute('aria-label', 'Sand ' + s.id + (s.coste == null ? '' : ' for ' + s.coste + ' g')); plus.disabled = !s.disponible;
      plus.addEventListener('click', function () { var r = T && T.lijaSemilla ? T.lijaSemilla(semilla, s.id) : { causa: 'NO_DATA (Workshop action is unavailable)' }; estado.textContent = r.causa || 'Workshop action sent for signature.'; });
      row.appendChild(plus);
      if (s.coste != null) { row.appendChild(el('small', null, 'Next level cost: ' + s.coste + ' g')); }
      if (s.causa) { row.appendChild(el('p', 'no-data', 'NO_DATA (' + s.causa + ')')); }
      statBox.appendChild(row);
    });
    cuerpo.appendChild(statBox);
    var oddsBox = el('section', 'army-wave-section'); oddsBox.appendChild(el('h3', null, 'Honest summon odds'));
    oddsBox.appendChild(el('p', null, m.odds.map(function (o) { return o.rareza + ' ' + o.porcentaje; }).join(' · ')));
    oddsBox.appendChild(el('p', 'army-wave-source', 'Same TC edge table used by the roll: ' + m.aristas.map(function (x) { return x[0] + ' edges ' + (x[1] / 10).toFixed(1) + '%'; }).join(' · ')));
    oddsBox.appendChild(el('p', null, 'No hidden odds.')); cuerpo.appendChild(oddsBox);
  }
  function abre(t, ficha) {
    if (!t || !t.semilla) { return false; }
    monta(); semilla = t.semilla; renderOnda = ficha || null; anterior = root.document.activeElement; estado.textContent = ''; pinta();
    if (!dialogo.open) { dialogo.showModal(); }
    var b = cuerpo.querySelector('.army-wave-plus:not(:disabled)') || dialogo.querySelector('.army-wave-head button'); b.focus();
    return true;
  }
  function alToque(t, ficha) { return abre(t, ficha); }
  if (root.document) { root.document.addEventListener('atlas:onda-taller', function (e) { if (dialogo && dialogo.open && e.detail && e.detail.semilla === semilla) { pinta(); if (e.detail.causa) { estado.textContent = 'NO_DATA (' + e.detail.causa + ')'; } } }); }
  var API = { modelo: modelo, abre: abre, alToque: alToque, cierra: cierra };
  if (typeof module === 'object' && module.exports) { module.exports = API; } else { root.AtlasArmyWavePanel = API; }
})(typeof window === 'object' ? window : globalThis);
