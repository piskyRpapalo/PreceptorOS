
(function (raiz) {
  'use strict';
  var HUE = { LIVE: 120, PROPUESTA: 45, FIRMADO: 270, ERROR: 0, NO_DATA: 240, SIMULATED: 30, STALE: 60 };
  var SAT = 70, LUZ_BASE = 55;


  var DERIVADOS = {
    LIVE:      { flujo: 0.0006,  pulso_hz: 5.16, escala: 1.0,  feedback: 'flow' },
    PROPUESTA: { flujo: 0.0012,  pulso_hz: 2.00, escala: 0.96, feedback: 'pulse-sync' },
    FIRMADO:   { flujo: 0.0004,  pulso_hz: 1.00, escala: 1.08, feedback: 'bloom' },
    ERROR:     { flujo: 0.0030,  pulso_hz: 8.00, escala: 0.92, feedback: 'distort' },
    NO_DATA:   { flujo: 0,        pulso_hz: 0,    escala: 1.0,  feedback: 'silent-field' },
    SIMULATED: { flujo: 0.0008,  pulso_hz: 3.00, escala: 0.98, feedback: 'sim' },
    STALE:     { flujo: 0.0002,  pulso_hz: 0.50, escala: 0.90, feedback: 'fade' }
  };


  function congelada() {
    var t = {};
    Object.keys(HUE).forEach(function (k) { t[k] = HUE[k]; });
    return Object.freeze ? Object.freeze(t) : t;
  }
  var TABLA = congelada();


  function bandas(h, s, l) {
    function c(L) { return 'hsl(' + h + ' ' + s + '% ' + Math.max(4, Math.min(94, L)) + '%)'; }
    return { h: h, brillo: c(l + 16), base: c(l), sombra: c(l - 20), contorno: c(l - 44) };
  }

  function de(sello) {
    if (!HUE.hasOwnProperty(sello)) { return null; }
    var d = DERIVADOS[sello];
    return Object.freeze ? Object.freeze({
      sello: sello, hue: HUE[sello], bandas: bandas(HUE[sello], SAT, LUZ_BASE),
      flujo: d.flujo, pulso_hz: d.pulso_hz, escala: d.escala, feedback: d.feedback
    }) : { sello: sello, hue: HUE[sello], bandas: bandas(HUE[sello], SAT, LUZ_BASE),
      flujo: d.flujo, pulso_hz: d.pulso_hz, escala: d.escala, feedback: d.feedback };
  }

  function hueDe(sello) { return HUE.hasOwnProperty(sello) ? HUE[sello] : null; }

  var AtlasSemantica = { TABLA: TABLA, SELLOS: TABLA, de: de, hueDe: hueDe,
                          bandas: bandas, SAT: SAT, LUZ: LUZ_BASE };
  if (typeof module === 'object' && module.exports) { module.exports = AtlasSemantica; }
  else { raiz.AtlasSemantica = AtlasSemantica; }
})(typeof module === 'object' && module.exports ? this : (this || window));
