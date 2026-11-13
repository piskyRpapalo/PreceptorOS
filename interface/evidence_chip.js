/* Evidence chip (visual-coherence commission). One visual word for how much a figure can be trusted.
 * Presentation only: the state comes from the data (Codex CLI owns it); this file never decides a state.
 * Shape + word + colour, never colour alone: the shape survives forced-colors and greyscale, and the word
 * is what a screen reader hears (aria-label is the same text the eye reads). English labels: the MVP is English.
 */
(function (root) {
  "use strict";
  // Input words from the data (MEDIDO/DECLARADO come from the records) and the Mesa's vocabulary.
  var tabla = {
    VERIFIED: { word: "VERIFIED", glyph: "■", tone: "ok", says: "checked again by this app" },
    OBSERVED: { word: "OBSERVED", glyph: "●", tone: "ok", says: "measured on this device or rack" },
    MEDIDO: { word: "OBSERVED", glyph: "●", tone: "ok", says: "measured on this device or rack" },
    DECLARED: { word: "DECLARED", glyph: "◇", tone: "warn", says: "declared by a person, not measured" },
    DECLARADO: { word: "DECLARED", glyph: "◇", tone: "warn", says: "declared by a person, not measured" },
    STALE: { word: "STALE", glyph: "▲", tone: "warn", says: "was true, but too old to count now" },
    NO_DATA: { word: "NO DATA", glyph: "□", tone: "quiet", says: "not measured; the cause is shown" },
    REFUSED: { word: "REFUSED", glyph: "✕", tone: "stop", says: "asked for, and the rule said no" },
    DENEGADO: { word: "REFUSED", glyph: "✕", tone: "stop", says: "asked for, and the rule said no" }
  };

  function normal(state) {
    var key = String(state || "").trim().toUpperCase().replace(/[\s-]+/g, "_");
    return tabla[key] ? key : "NO_DATA";
  }

  // Returns the text the person reads and hears, e.g. "NO DATA · lab federated not on ref".
  function text(state, cause) {
    var t = tabla[normal(state)];
    var c = cause ? String(cause).replace(/_/g, " ").slice(0, 80) : "";
    return t.word + (c ? " · " + c : "");
  }

  function make(doc, state, cause) {
    var key = normal(state), t = tabla[key];
    var span = doc.createElement("span");
    span.className = "evidence-chip evidence-" + t.tone;
    span.dataset.state = key;
    span.setAttribute("aria-label", text(state, cause));
    var glyph = doc.createElement("span");
    glyph.className = "evidence-glyph";
    glyph.setAttribute("aria-hidden", "true");
    glyph.textContent = t.glyph;
    span.appendChild(glyph);
    span.appendChild(doc.createTextNode(" " + text(state, cause)));
    span.title = t.says;
    return span;
  }

  var api = { text: text, normal: normal, make: make, table: tabla };
  if (typeof module !== "undefined" && module.exports) { module.exports = api; }
  root.PreceptorEvidence = api;
})(typeof window !== "undefined" ? window : globalThis);
