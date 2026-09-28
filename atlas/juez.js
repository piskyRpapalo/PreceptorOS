/* preceptoros.org · theGame · el JUEZ: cuando corriges o ignoras al piloto, ¿quién tenía razón?

   QUÉ HACE. Desde el estado EXACTO del momento de la sugerencia juega dos ramas con el mismo
   motor puro: lo que sugirió el piloto y lo que hiciste tú (o esperar, si no hiciste nada).
   Después, HORIZONTE ciclos con el piloto al mando en las dos, y compara Núcleo, fase,
   integridad mínima y XP, en ese orden. Como el motor es puro, el veredicto no es una opinión:
   cualquiera lo vuelve a jugar y sale igual. Eso enseña determinismo con la propia partida.

   UNA FUENTE, DOS USOS. `juzga` es puro y se exporta por `module.exports`: la Aduana del rack
   lo carga desde aquí para decidir qué correcciones entrenan al piloto. La pestaña y el rack no
   pueden discrepar porque no hay dos jueces, hay uno.

   SIN RED Y SIN ENSUCIAR LA PARTIDA. En la pestaña simula con `AtlasPartida.puro`, el motor
   SIN la grabadora: el envuelto anota cada llamada, y su `inicial` vaciaría la partida en
   curso. Nada sale de la pestaña. */
(function (raiz) {
  'use strict';

  var HORIZONTE = 300, SIN_DIA = 'sin-dia';

  function aplicar(M, e, a) {
    if (a.accion === 'esperar') { return e; }
    if (a.accion === 'bajar_a') { return M.bajarA(e, a.banda, SIN_DIA); }
    if (a.accion === 'invocar') { return M.invocar(e, a.coste, SIN_DIA); }
    if (a.accion === 'recoger' || a.accion === 'reparar' || a.accion === 'aplazar') {
      return M[a.accion](e, SIN_DIA);
    }
    throw new Error('accion desconocida: ' + a.accion);
  }

  /* Una rama: la acción, y después `h` ciclos con el piloto decidiendo tras cada uno. */
  function rama(M, Pa, Pi, e0, a, ley, h) {
    var e = aplicar(M, e0, a), min = e.integridad;
    for (var i = 0; i < h; i++) {
      e = M.ciclo(e, ley);
      var p = Pi.decide(Pa.instantanea(e, M), M);
      if (Pi.valida(p) && p.accion !== 'esperar') { e = aplicar(M, e, p); }
      if (e.integridad < min) { min = e.integridad; }
    }
    var xp = 0;
    e.xp.forEach(function (x) { xp += x; });
    return { fase: M.fase(e), nucleo: M.nivelNucleo(e), integridad_min: min,
             integridad_fin: e.integridad, xp: xp };
  }

  /* Lo que importa, en orden: el Núcleo, la fase, no romperse por el camino y la XP. */
  function gana(p, h) {
    if (!h) { return 'NO_DATA'; }
    var k = ['nucleo', 'fase', 'integridad_min', 'xp'];
    for (var i = 0; i < k.length; i++) {
      if (h[k[i]] > p[k[i]]) { return 'humano'; }
      if (h[k[i]] < p[k[i]]) { return 'piloto'; }
    }
    return 'empate';
  }

  /* Una sugerencia que no cambia nada del estado es una alucinación: no hay rama que jugar. */
  function sinEfecto(M, Pa, e, a) {
    try {
      return JSON.stringify(Pa.final(aplicar(M, e, a), M)) === JSON.stringify(Pa.final(e, M));
    } catch (x) { return true; }
  }

  function juzga(M, Pa, Pi, e, sug, hum, ley, h) {
    h = h || HORIZONTE;
    var nula = sinEfecto(M, Pa, e, sug);
    var rp = nula ? null : rama(M, Pa, Pi, e, sug, ley, h);
    var rh = hum ? rama(M, Pa, Pi, e, hum, ley, h) : null;
    return { horizonte: h, piloto: rp, humano: rh, gana: rp ? gana(rp, rh) : 'NO_DATA', alucinacion: nula };
  }

  var AtlasJuez = { HORIZONTE: HORIZONTE, aplicar: aplicar, rama: rama, gana: gana, juzga: juzga,
                    sinEfecto: sinEfecto };
  if (typeof module === 'object' && module.exports) { module.exports = AtlasJuez; return; }
  raiz.AtlasJuez = AtlasJuez;

  /* --- la pestaña ---------------------------------------------------------------------- */
  var M = raiz.AtlasMotor, Pa = raiz.AtlasPartida, Pi = raiz.AtlasPiloto, J = raiz.AtlasJuego;
  if (!M || !Pa || !Pa.puro || !Pi || !J) { return; }
  var puro = Pa.puro, pendiente = null, latido = 0;
  /* La voz del Preceptor (atlas-dialogo.js) se alimenta de lo que el juez YA escucha. */
  function D(f, a, b) { var d = raiz.AtlasDialogo; if (d && d[f]) { d[f](a, b); } }

  function texto(k, v) {
    return String(J.texto(k) || '').replace(/\{(\w+)\}/g, function (_, n) { return n in v ? v[n] : ''; });
  }
  function pinta(v) {
    var sug = document.querySelector('.thegame-sugerencia');
    if (!sug) { return; }
    var p = sug.parentNode.querySelector('.thegame-juez');
    if (!p) {
      p = document.createElement('p');
      p.className = 'thegame-sugerencia thegame-juez';
      p.setAttribute('role', 'status');
      sug.parentNode.insertBefore(p, sug.nextSibling);
    }
    var r = v.piloto, h = v.humano;
    p.textContent = v.alucinacion ? texto('juez_nulo', {})
      : texto('juez_' + v.gana, { h: v.horizonte, np: r.nucleo, ip: r.integridad_min,
                                  nh: h ? h.nucleo : '', ih: h ? h.integridad_min : '' });
    p.hidden = false;
    D('voz', 'voz_juez_' + (v.alucinacion ? 'nulo' : v.gana));
  }
  /* Se juzga fuera del clic, para que el botón responda al instante. */
  function juzgaLuego(hum) {
    var x = pendiente;
    pendiente = null;
    setTimeout(function () { pinta(juzga(puro, Pa, Pi, x.e, x.sug, hum, x.ley)); }, 0);
  }

  /* La primera sugerencia que ve la persona, una sola vez. */
  var visto = false;
  new MutationObserver(function () {
    var s = document.querySelector('.thegame-sugerencia:not(.thegame-juez)');
    if (!visto && s && !s.hidden) { visto = true; D('voz', 'voz_sugiere'); }
  }).observe(document.body, { subtree: true, attributes: true, attributeFilter: ['hidden'], childList: true });

  var anota = Pa.anota;
  Pa.anota = function (a, respuesta) {
    anota(a, respuesta);
    pendiente = null;
    D('voz', respuesta === 'hecha' ? 'voz_hecha' : 'voz_ignorada');
    if (respuesta !== 'ignorada') { return; }
    var p = J.partida();
    if (!p) { return; }
    try {
      var sug = { accion: a.accion };
      if (a.banda) { sug.banda = a.banda; }
      pendiente = { e: Pa.reproduce(p, puro), ley: p.ley, sug: sug };
    } catch (x) { pendiente = null; }
  };
  /* La corrección es lo PRIMERO que haces tras ignorar; si pasa un ciclo sin hacer nada,
     tu jugada fue esperar. Se envuelve la versión que graba: el juez solo escucha. */
  ['recoger', 'reparar', 'aplazar', 'bajarA', 'invocar', 'ciclo', 'dormir'].forEach(function (k) {
    var f = M[k];
    M[k] = function (e, x) {
      var r = f.apply(this, arguments);
      if (k === 'ciclo') {
        if (++latido % 5 === 0) { D('observa', J.instantanea()); }
      } else if (k !== 'dormir') {
        D('accion', k === 'bajarA' ? { accion: 'bajar_a', banda: x } : { accion: k }, r && r.t);
      }
      if (pendiente) {
        juzgaLuego(k === 'ciclo' || k === 'dormir' ? { accion: 'esperar' }
          : k === 'bajarA' ? { accion: 'bajar_a', banda: x }
          : k === 'invocar' ? { accion: 'invocar', coste: x } : { accion: k });
      }
      return r;
    };
  });
})(this);
