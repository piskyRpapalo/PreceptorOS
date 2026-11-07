/* Zonas de la pestaña única: datos de presentación, sin navegación ni autoridad. */
"use strict";
(function (root) {
  const zonas = Object.freeze([
    Object.freeze({ id: "mando", panel: "mando", titulo: "Mando" }),
    Object.freeze({ id: "conversacion", panel: "conversacion", titulo: "Conversación" }),
    Object.freeze({ id: "gobierno", panel: "gobierno", titulo: "Gobierno" }),
    Object.freeze({ id: "cuaderno", panel: "cuaderno", titulo: "Cuaderno" }),
    Object.freeze({ id: "lab", panel: "lab", titulo: "Lab" }),
    Object.freeze({ id: "harness", panel: "harness", titulo: "Harness" }),
    Object.freeze({ id: "puerta", panel: "puerta", titulo: "Puerta pública" }),
    Object.freeze({ id: "modelos", panel: "modelos", titulo: "Modelos" }),
    Object.freeze({ id: "ajustes", panel: "ajustes", titulo: "Ajustes" }),
  ]);
  root.PreceptorZonas = Object.freeze({ zonas });
})(window);
