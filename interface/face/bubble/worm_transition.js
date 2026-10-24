(function (raiz) {
  'use strict';
  var TOPE_SEG = 9, intentos = {}, visible = null, textoDe = {}, ultimo = null, lienzo = null, scrollTarget = null, scrollDraw = null;

  function hueDe(sello) { var T = raiz.AtlasSemantica || raiz.AtlasToon; return T && T.SELLOS && T.SELLOS.hasOwnProperty(sello) ? T.SELLOS[sello] : null; }
  function cicloValido(c) { return Number.isSafeInteger(c) && c >= 0 && c <= 1000000000; }
  function cicloActual() {
    try {
      var J = raiz.AtlasJuego, i = J && J.instantanea ? J.instantanea() : null, c = i && i.ciclo;
      return cicloValido(c) ? c : null;
    } catch (_) { return null; }
  }

  function bubble() { return raiz.AtlasBubble || (typeof module === 'object' && module.exports ? require('../game/bubble_language.js') : null); }
  function gusano(S, A, B, p) {
    var segs = Math.max(1, Math.min(TOPE_SEG, S.intentos || 1)), curva = Math.min(140, 16 + Math.abs(S.delta || 0) / 12);
    var BUBBLE = bubble(), lado = cicloValido(S.ciclo) ? (S.ciclo % 2 === 0 ? -1 : 1) : 0;
    p = Number.isFinite(p) ? Math.max(0, Math.min(1, p)) : 0;
    return { puntos: BUBBLE.neck(A, B, lado ? curva : 0, p, lado || 1), segmentos: segs, progreso: p, hue: hueDe(S.sello) };
  }
  function centro(el) { if (!el) { return null; } var q = el.getBoundingClientRect(); return [Math.round(q.left + q.width / 2), Math.round(q.top + q.height / 2)]; }
  function quieto() { return raiz.matchMedia && raiz.matchMedia('(prefers-reduced-motion: reduce)').matches; }
  function progreso(el) {
    var maximo = el.scrollHeight - el.clientHeight;
    return maximo > 0 ? Math.max(0, Math.min(1, el.scrollTop / maximo)) : 0;
  }
  function anima(S, A, B, el) {
    var D = raiz.document;
    if (!lienzo) { lienzo = D.createElement('canvas'); lienzo.className = 'gusano-lienzo'; lienzo.setAttribute('aria-hidden', 'true'); D.body.appendChild(lienzo); }
    var dpr = Math.min(2, raiz.devicePixelRatio || 1), g = lienzo.getContext('2d'), gu = gusano(S, A, B, progreso(el));
    lienzo.width = Math.round(raiz.innerWidth * dpr); lienzo.height = Math.round(raiz.innerHeight * dpr);
    var color = gu.hue === null ? 'rgba(150,160,180,.8)' : 'hsl(' + gu.hue + ' 70% 60%)';
    var scale = 4 * gu.progreso * (1 - gu.progreso), cab = Math.round(gu.progreso * 24);
    g.clearRect(0, 0, lienzo.width, lienzo.height);
    for (var s = 0; s < gu.segmentos; s++) {
      var q = gu.puntos[Math.max(0, cab - s * 2)];
      g.beginPath(); g.arc(q[0] * dpr, q[1] * dpr, (6 - s * 0.4) * dpr * scale, 0, 2 * Math.PI);
      g.fillStyle = color; g.globalAlpha = 1 - s / (gu.segmentos + 1); g.fill();
    }
    g.globalAlpha = 1;
  }

  function vistoAhora() {
    var D = raiz.document, caja = D.getElementById('thegame-terminal'), v = null;
    D.querySelectorAll('.thegame-hoja').forEach(function (h) { if (!h.hidden) { v = { id: h.id.replace('thegame-', ''), el: h }; } });
    if (!v && caja && !caja.hidden) { Array.prototype.forEach.call(caja.children, function (d) { if (d.tagName === 'DETAILS' && !d.hidden) { v = { id: d.id, el: d }; } }); }
    return v;
  }
  function transita() {
    var v = vistoAhora(), id = v ? v.id : null;
    if (id === visible) { return; }
    var de = visible, D = raiz.document;
    visible = id;
    if (!id) {
      if (scrollTarget && scrollDraw) { scrollTarget.removeEventListener('scroll', scrollDraw); }
      scrollTarget = scrollDraw = null;
      if (lienzo) { lienzo.getContext('2d').clearRect(0, 0, lienzo.width, lienzo.height); }
      return;
    }
    intentos[id] = (intentos[id] || 0) + 1;
    var largo = (v.el.innerText || '').length, delta = largo - (de && textoDe[de] !== undefined ? textoDe[de] : 0);
    textoDe[id] = largo;
    var W = raiz.AtlasVentana;
    if (W && W.pinta) { W.pinta(); }
    var f = W && W.ficha ? W.ficha() : null;
    var S = { ciclo: cicloActual(), de: de, a: id, delta: delta, intentos: intentos[id], sello: f && f.id === id ? f.sello : 'NO_DATA' };
    var A = centro(D.getElementById('menu-' + (de || id))) || [0, 0], B = centro(D.getElementById('menu-' + id)) || A;
    if (scrollTarget && scrollDraw) { scrollTarget.removeEventListener('scroll', scrollDraw); }
    scrollTarget = v.el.closest('.thegame-hoja') || D.getElementById('thegame-terminal');
    ultimo = { S: S, segmentos: S.intentos, progreso: scrollTarget ? progreso(scrollTarget) : 0, hue: hueDe(S.sello) };
    if (scrollTarget && !quieto()) {
      scrollDraw = function () { ultimo.progreso = progreso(scrollTarget); anima(S, A, B, scrollTarget); };
      scrollTarget.addEventListener('scroll', scrollDraw, { passive: true }); scrollDraw();
    } else if (lienzo) { lienzo.getContext('2d').clearRect(0, 0, lienzo.width, lienzo.height); }
    var R = raiz.AtlasRadioChat;
    if (R && R.dice) { R.dice({ quien: 'Terminal', fuente: 'gusano', sello: S.sello, texto: (de || 'map') + ' → ' + id + ' · Δ text ' + (delta >= 0 ? '+' : '') + delta + ' · opened ×' + S.intentos }); }
  }
  function monta() {
    var D = raiz.document, caja = D && D.getElementById('thegame-terminal');
    if (!caja || monta.hecho) { return; }
    monta.hecho = true;
    var piso = caja.parentNode || D.body;
    new MutationObserver(transita).observe(piso, { subtree: true, attributes: true, attributeFilter: ['hidden'] });
  }
  if (raiz.setInterval && raiz.document) { raiz.setInterval(monta, 1000); }

  function ficha() { return ultimo ? JSON.parse(JSON.stringify(ultimo)) : null; }

  var AtlasWorm = { gusano: gusano, ficha: ficha, TOPE_SEG: TOPE_SEG };
  if (typeof module === 'object' && module.exports) { module.exports = AtlasWorm; } else { raiz.AtlasWorm = AtlasWorm; }
})(this);
