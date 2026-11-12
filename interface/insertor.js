(function (root) {
  "use strict";

  // `preceptores` (optional): { id: route } from /api/conversacion. A tag that names a preceptor addresses it;
  // route "none" means no transport on this node, so nothing is sent (NO_DATA with its cause).
  function rutear(texto, zonas, activa, preceptores) {
    if (typeof texto !== "string" || !Array.isArray(zonas) || !zonas.includes(activa)) {
      return { estado: "nodata", causa: "insertor_input_invalid" };
    }
    const limpio = texto.trim();
    if (!limpio.startsWith("@")) {
      return { estado: "medido", carril: "chat", panel: activa, texto: limpio };
    }
    const partes = /^@([a-z][a-z0-9_-]{0,31})(?:\s+([\s\S]*))?$/.exec(limpio);
    if (!partes) return { estado: "nodata", causa: "tag_invalid" };
    const tag = partes[1];
    const nota = (partes[2] || "").trim();
    if (tag === "ayuda") return { estado: "medido", carril: "ayuda", panel: activa, nota };
    const rutas = preceptores && typeof preceptores === "object" ? preceptores : {};
    if (!zonas.includes(tag) && Object.prototype.hasOwnProperty.call(rutas, tag)) {
      if (rutas[tag] === "none") return { estado: "nodata", causa: "no_transport", para: tag };
      if (!nota) return { estado: "nodata", causa: "text_missing", para: tag };
      return { estado: "medido", carril: "preceptor", panel: activa, para: tag, ruta: rutas[tag], texto: nota };
    }
    if (!zonas.includes(tag)) return { estado: "nodata", causa: "tag_not_declared" };
    return { estado: "medido", carril: "chat", panel: tag, texto: nota };
  }

  function base(panel) {
    if (!panel || typeof panel.querySelectorAll !== "function") return [];
    const headings = Array.from(panel.querySelectorAll("h2, h3"))
      .map((node) => typeof node.textContent === "string" ? node.textContent.trim() : "")
      .filter(Boolean).slice(0, 8);
    if (headings.length) return headings;
    const label = panel.getAttribute && panel.getAttribute("aria-label");
    return typeof label === "string" && label.trim() ? [label.trim()] : [];
  }

  const api = Object.freeze({ rutear, base });
  root.PreceptorInsertor = api;
  if (typeof module === "object" && module.exports) module.exports = api;
})(typeof window === "object" ? window : globalThis);
