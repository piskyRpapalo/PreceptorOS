(function (root) {
  "use strict";

  function rutear(texto, zonas, activa) {
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
