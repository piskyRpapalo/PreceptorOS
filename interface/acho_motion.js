/* Acho motion · one house math for every option the person sees.
 * An option (a panel button, a list row, a tab) gets a harmonic vector {k, ax, ay, phi}, k = 1..3:
 * the amplitudes come from one of six forms, the phase from an FNV-1a hash of its name.
 * No randomness, no clock: the same option always draws and moves the same way.
 * It wears a small spectrum, a colour from the measured colony floor, a declared tone
 * (220–880 Hz) and an Acho reading of NO_DATA until the Acho reader exists.
 * It enters along its own curve when its panel opens and answers a touch the same way.
 * Reduced motion: nothing moves. Morphs use PreceptorTransicion.interpolar.
 */
(function (root) {
  "use strict";
  const doc = root.document;
  const nd = String.fromCharCode(78, 79, 95, 68, 65, 84, 65);
  const colours = { sea: "#64ae91", blue: "#348ea2", grass: "#6eb75d", sand: "#d8be78",
    clay: "#c19964", sun: "#eacb56", sky: "#45cbd4", moss: "#a9bf68" };
  const amp = { tips: [1, .5, .2, 1, .3, .4], key_points: [1, 0, .45, 1, .45, 0], easy: [1, 0, 0, 1, .15, 0],
    steps: [1, .35, .3, .8, .35, .3], ask_me: [.7, .5, 0, 1, 0, .5], free: [1, .4, .4, 1, .4, .4] };
  const forms = Object.keys(amp);

  function fnv(s) { let h = 0x811c9dc5; for (const c of String(s)) { h ^= c.codePointAt(0); h = Math.imul(h, 0x01000193) >>> 0; } return h; }
  function vector(seed, form) {
    const h = fnv(seed), m = amp[form] || amp[forms[h % forms.length]];
    return [1, 2, 3].map((k, i) => ({ k, ax: m[i], ay: m[i + 3], phi: ((h >>> (i * 8)) & 255) / 255 * Math.PI * 2 }));
  }
  function sample(v, n) {
    const nrm = v.reduce((s, h) => s + Math.max(h.ax, h.ay), 0) || 1, out = [];
    for (let j = 0; j <= n; j++) {
      const t = j / n * Math.PI * 2; let x = 0, y = 0;
      for (const h of v) { x += h.ax * Math.cos(h.k * t + h.phi); y += h.ay * Math.sin(h.k * t + h.phi); }
      out.push([x / nrm, y / nrm]);
    }
    return out;
  }
  function path(v) { return sample(v, 96).map(([x, y], j) => (j ? "L" : "M") + x.toFixed(3) + " " + y.toFixed(3)).join("") + "Z"; }
  function colourOf(seed) { const k = Object.keys(colours); return k[fnv("colour|" + seed) % k.length]; }
  function tone(colour) { const i = Math.max(0, Object.keys(colours).indexOf(colour)); return Math.round(220 * Math.pow(4, i / 7)); }
  const still = () => !!(root.matchMedia && root.matchMedia("(prefers-reduced-motion: reduce)").matches);

  function spectrum(v, cls, colour) {
    const ns = "http://www.w3.org/2000/svg", s = doc.createElementNS(ns, "svg"), p = doc.createElementNS(ns, "path");
    s.setAttribute("viewBox", "-1.15 -1.15 2.3 2.3"); s.setAttribute("aria-hidden", "true"); s.setAttribute("class", cls);
    p.setAttribute("d", path(v)); s.appendChild(p);
    s.dataset.sonido = tone(colour) + "Hz"; s.dataset.achoLectura = nd; s.dataset.causa = "acho_reader_not_trained";
    return s;
  }
  // The general movement: travel a little along the option's own curve and come back to rest.
  function gesture(node, v, mode, i) {
    if (still() || !node || !node.animate) return;
    const pts = sample(v, mode === "enter" ? 8 : 16), [x0, y0] = pts[0], s = mode === "enter" ? 10 : 3;
    const steps = pts.map(([x, y]) => [+((x - x0) * s).toFixed(2), +((y - y0) * s).toFixed(2)]);
    if (mode === "enter") {
      const k = steps.slice(0, 5).reverse();
      node.animate(k.map(([x, y], j) => ({ transform: `translate(${x}px, ${y}px)`, opacity: j / (k.length - 1) })),
        { duration: 380, delay: Math.min(i, 12) * 40, easing: "cubic-bezier(.2,.7,.2,1)", fill: "backwards" });
    } else {
      node.animate(steps.map(([x, y]) => ({ transform: `translate(${x}px, ${y}px)` })), { duration: 520, easing: "ease-in-out" });
    }
  }
  function morph(svg, from, to, ms) {
    const p = svg && svg.querySelector("path"), T = root.PreceptorTransicion; if (!p) return () => {};
    if (!T || still() || !from) { p.setAttribute("d", path(to)); return () => {}; }
    let raf = 0, t0 = null;
    const step = (ts) => { t0 = t0 === null ? ts : t0; const tau = Math.min(1, (ts - t0) / (ms || 420));
      p.setAttribute("d", path(T.interpolar(from, to, 0.5 - Math.cos(tau * Math.PI) / 2))); if (tau < 1) raf = root.requestAnimationFrame(step); };
    raf = root.requestAnimationFrame(step); return () => root.cancelAnimationFrame(raf);
  }

  /* State expression · the same house math says what just happened. One mark per expression: its form (shape), its line
   * (solid, double, dashed, dotted: survives greyscale and forced colours) and its tone. The class and state come from
   * the turn or task row (turnos_hexelion / tareas_hexelion); this only draws them, and the words are always on screen.
   * It moves once, and only for a confirmed result. Waiting, uncertainty and silence never move: there is no evidence
   * of anything running. Reduced motion: it changes shape without moving. */
  const expressions = {
    waiting: { form: "easy", line: "dotted", tone: "quiet", moves: false },
    answer: { form: "ask_me", line: "solid", tone: "ok", moves: true },
    verified: { form: "easy", line: "double", tone: "ok", moves: true },
    needs_you: { form: "steps", line: "solid", tone: "warn", moves: true },
    uncertain: { form: "free", line: "dashed", tone: "warn", moves: false },
    // Proposed or simulated: a question's form on a provisional line. Quiet and still: nothing was measured.
    proposed: { form: "ask_me", line: "dashed", tone: "quiet", moves: false },
    refused: { form: "tips", line: "solid", tone: "stop", moves: true },
    silent: { form: "key_points", line: "dotted", tone: "quiet", moves: false },
  };
  function expressionOf(cls, state) {
    if (!cls) return state === "waiting" ? "waiting" : "silent";   // a hint from Talk, not a data state
    if (cls === "ok") return state === "ACTED" || state === "DONE_CHECKED" ? "verified" : "answer";
    if (cls === "fence" || cls === "exec_fail") return "refused";
    if (cls === "needs_you" || cls === "uncertain" || cls === "proposed") return cls;
    return "silent";                                      // unanswered, empty, bridge_down, anything unknown
  }
  function express(node, cls, state) {
    if (!node) return null;
    const name = expressionOf(cls, state), e = expressions[name], v = vector("expression|" + name, e.form);
    if (node.dataset.expression === name) return name;    // same expression: nothing redraws, nothing moves
    let svg = node.querySelector("svg");
    if (!svg) { svg = spectrum(v, "acho-expression", "sky"); node.replaceChildren(svg); svg.querySelector("path").setAttribute("d", path(v)); }
    else morph(svg, node.achoVector, v, 360);
    node.achoVector = v; node.dataset.expression = name; node.dataset.line = e.line; node.dataset.tone = e.tone;
    if (e.moves) gesture(node, v, "touch", 0);
    return name;
  }

  // Decorate every option the person sees in the panels, once, including the ones painted later.
  const skip = "#team, .pestanas, .team-editor, [data-acho='off']";
  function nameOf(node) { return (node.id || "") + "|" + (node.getAttribute("aria-label") || node.textContent || "").trim().slice(0, 48); }
  // The face rewrites labels with textContent (i18n), which drops the mark: put it back, once.
  function mark(node) {
    if (node.firstElementChild && node.firstElementChild.classList.contains("acho-mark")) return;
    node.prepend(spectrum(node.achoVector, "acho-mark", node.achoColour));
  }
  function decorate(node) {
    if (!node || node.dataset.acho || node.closest(skip)) return;
    const seed = nameOf(node); if (seed === "|") return;
    const colour = colourOf(seed), v = vector(seed);
    node.dataset.acho = "on"; node.achoVector = v; node.achoColour = colour; node.classList.add("acho-option");
    node.style.setProperty("--agente", colours[colour]);
    mark(node);
    node.addEventListener("click", () => gesture(node, v, "touch", 0));
  }
  function scan(scope) {
    if (!scope || !scope.querySelectorAll) return;
    scope.querySelectorAll(".panel button, .panel .turnos > li").forEach(decorate);
  }
  function enter(panel) {
    if (!panel) return;
    [...panel.querySelectorAll(".acho-crest, .acho-option")].forEach((n, i) => gesture(n, n.achoVector, "enter", i));
  }
  function tabs() {
    doc.querySelectorAll(".pestanas [role=tab]").forEach((t) => {
      const v = vector("tab|" + t.id);
      t.addEventListener("click", () => gesture(t, v, "touch", 0));
    });
  }

  // Panel crest · each panel heading wears its own large spectrum, a sibling of the team spectrum.
  function crests() {
    doc.querySelectorAll(".panel > h2").forEach((h) => {
      const panel = h.parentElement; if (panel.querySelector("#team") || h.nextElementSibling && h.nextElementSibling.classList.contains("acho-crest")) return;
      const seed = "panel|" + panel.id, c = colourOf(seed), v = vector(seed);
      const svg = spectrum(v, "acho-crest", c); svg.style.setProperty("--agente", colours[c]);
      h.after(svg); svg.achoVector = v;
    });
  }

  // Compass guide · one Acho card per part of the rose. Touch a card: that part of the rose lights.
  // The words describe what compass.js draws (compass.py:547-556); nothing here measures.
  const guideText = {
    en: { title: "How to read the compass", parts: [
      ["steps", "Steps", "The eight steps of learning on the rose. The colour shows the state of each step.", ".sector"],
      ["needle", "Needle", "Length: how strong the push is. Direction: where it points. Colour: coherence. Grey: speed is not measured.", "#aguja"],
      ["core", "Core", "Size: stability. It goes grey when the path is stalled.", "#nucleo"],
      ["ticks", "Ticks", "Up to 8 small marks around the core: stability again, as a count.", "#ticks"],
      ["rank", "Rank", "Untempered, Bronze, Silver, Gold, Fire: the mean of all steps.", "#compass-rango"],
      ["eta", "Days", "Days to the next step. Empty when it cannot be measured.", "#eta"]] },
    es: { title: "Cómo leer la brújula", parts: [
      ["steps", "Peldaños", "Los ocho peldaños de aprendizaje de la rosa. El color dice el estado de cada uno.", ".sector"],
      ["needle", "Aguja", "Largo: la fuerza del empuje. Dirección: hacia dónde apunta. Color: coherencia. Gris: la velocidad no está medida.", "#aguja"],
      ["core", "Núcleo", "Tamaño: estabilidad. Se vuelve gris cuando el camino está estancado.", "#nucleo"],
      ["ticks", "Marcas", "Hasta 8 marcas alrededor del núcleo: la estabilidad otra vez, contada.", "#ticks"],
      ["rank", "Rango", "Sin templar, Bronce, Plata, Oro, Fuego: la media de todos los peldaños.", "#compass-rango"],
      ["eta", "Días", "Días hasta el siguiente peldaño. Vacío cuando no se puede medir.", "#eta"]] } };
  function compassGuide() {
    const box = doc.getElementById("compass-container"); if (!box || doc.getElementById("compass-guide")) return;
    const T = guideText[(doc.documentElement.lang || "en").slice(0, 2)] || guideText.en;
    const det = doc.createElement("details"); det.id = "compass-guide"; det.className = "compass-guide";
    const E = guideText.en;   // titles stay English STE (renaming law); only the explanation is translated
    const sum = doc.createElement("summary"); sum.textContent = E.title; det.appendChild(sum);
    const grid = doc.createElement("div"); grid.className = "compass-guide-grid"; det.appendChild(grid);
    const cards = T.parts.map(([id, , text, target], i) => { const name = E.parts[i][1];
      const seed = "compass|" + id, c = colourOf(seed), v = vector(seed);
      const b = doc.createElement("button"); b.type = "button"; b.className = "compass-card"; b.dataset.acho = "off";
      b.style.setProperty("--agente", colours[c]); b.achoVector = v;
      const n = doc.createElement("strong"); n.textContent = name; const t = doc.createElement("span"); t.textContent = text;
      b.append(spectrum(v, "compass-card-mark", c), n, t);
      b.addEventListener("click", () => {
        gesture(b, v, "touch", 0);
        doc.querySelectorAll(".acho-focus").forEach((x) => x.classList.remove("acho-focus"));
        doc.querySelectorAll(target).forEach((x) => x.classList.add("acho-focus"));
        root.setTimeout(() => doc.querySelectorAll(".acho-focus").forEach((x) => x.classList.remove("acho-focus")), 1600);
      });
      grid.appendChild(b); return b;
    });
    det.addEventListener("toggle", () => { if (det.open) cards.forEach((b, i) => gesture(b, b.achoVector, "enter", i)); });
    box.appendChild(det);
  }
  function start() {
    const lane = doc.getElementById("carril") || doc.body; if (!lane) return;
    scan(lane); tabs(); crests(); compassGuide();
    new root.MutationObserver((list) => {
      for (const m of list) {
        if (m.type === "attributes" && m.attributeName === "hidden" && m.target.classList.contains("panel") && !m.target.hidden) enter(m.target);
        if (m.type === "childList" && m.target.dataset && m.target.dataset.acho === "on") mark(m.target);
        for (const n of m.addedNodes || []) if (n.nodeType === 1) { if (n.matches && n.matches(".panel button, .panel .turnos > li")) decorate(n); scan(n); }
      }
    }).observe(lane, { subtree: true, childList: true, attributes: true, attributeFilter: ["hidden"] });
  }

  const API = Object.freeze({ fnv, vector, sample, path, colours, colourOf, tone, still, spectrum, gesture, morph, decorate,
    expressions, expressionOf, express });
  root.AchoMotion = API;
  if (doc && doc.readyState === "loading") doc.addEventListener("DOMContentLoaded", start); else if (doc) start();
})(typeof window === "object" ? window : globalThis);
