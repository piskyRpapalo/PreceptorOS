/* Equipo · the team the person shapes in the Harness tab.
 * Each agent answers in its own way (tips, key points, easy, steps, ask me, free) and wears
 * its own Acho spectrum: a harmonic vector {k, ax, ay, phi} drawn as one closed curve.
 * Amplitudes come from the form, phases from an FNV-1a hash of the id: no randomness, no clock.
 * Switching agents morphs the curve with PreceptorTransicion.interpolar (the house math);
 * reduced motion makes it instant. Every spectrum declares its tone (220–880 Hz by colour)
 * and its Acho reading, which stays NO_DATA until the Acho reader exists.
 * The agent shapes presentation only: Hablar still cites exact quotes or says NO_DATA.
 */
(function (root) {
  "use strict";
  const doc = root.document;
  const nd = String.fromCharCode(78, 79, 95, 68, 65, 84, 65);
  const colores = { sea: "#64ae91", blue: "#348ea2", grass: "#6eb75d", sand: "#d8be78",
    clay: "#c19964", sun: "#eacb56", sky: "#45cbd4", moss: "#a9bf68" };
  const glifos = ["✦", "◆", "☺", "⋮", "?", "⌁", "◇", "◉", "▲", "●"];
  const formas = ["tips", "key_points", "easy", "steps", "ask_me", "free"];
  // amplitudes per form for k = 1, 2, 3 (x then y): the shape is the form, not decoration
  const amp = { tips: [1, .5, .2, 1, .3, .4], key_points: [1, 0, .45, 1, .45, 0], easy: [1, 0, 0, 1, .15, 0],
    steps: [1, .35, .3, .8, .35, .3], ask_me: [.7, .5, 0, 1, 0, .5], free: [1, .4, .4, 1, .4, .4] };
  // Titles are public names: English, ASD-STE100 (renaming law). Only the help sentences are translated.
  const titulos = { grupo: "Your team", tips: "Advice", key_points: "Key points", easy: "Simple words", steps: "Steps",
    ask_me: "Questions", free: "Your words", editar: "Edit", lab: "Send to Lab", nuevo: "Add agent", nombre: "Name",
    glifo: "Glyph", color: "Colour", forma: "Answer type", guardar: "Save", cancelar: "Cancel", chapa: "Agent that answers" };
  const frases = {
    es: { intro: "Elige un agente. El agente responde en Hablar.", pide: "Escribe cómo tiene que responder el agente.",
      guardado: "El equipo está guardado en este nodo.", enlab: (n) => `El agente está en el Lab como propuesta. Fichas: ${n}.`,
      error: "Error: ", casa: "Equipo de la casa. No está guardado en este nodo.", lleno: "El máximo es 6 agentes.",
      lectura: "Lectura Acho: " + nd + ". El lector Acho no existe.", sonido: (hz) => `tono ${hz} Hz` },
    en: { intro: "Select an agent. The agent answers in Hablar.", pide: "Write how the agent must answer.",
      guardado: "The team is saved on this node.", enlab: (n) => `The agent is in the Lab as a proposal. Cards: ${n}.`,
      error: "Error: ", casa: "House team. It is not saved on this node.", lleno: "The maximum is 6 agents.",
      lectura: "Acho reading: " + nd + ". The Acho reader does not exist.", sonido: (hz) => `tone ${hz} Hz` },
  };
  const quien = (a, L) => (a.name === L[a.form] ? a.name : `${a.name} · ${L[a.form]}`);
  const tx = () => Object.assign({}, titulos, frases[(doc.documentElement.lang || "en").slice(0, 2)] || frases.en);

  function fnv(s) { let h = 0x811c9dc5; for (const c of String(s)) { h ^= c.codePointAt(0); h = Math.imul(h, 0x01000193) >>> 0; } return h; }
  function vector(a) {
    const m = amp[a.form] || amp.free, h = fnv(a.id + "|" + (a.ask || ""));
    return [1, 2, 3].map((k, i) => ({ k, ax: m[i], ay: m[i + 3], phi: ((h >>> (i * 8)) & 255) / 255 * Math.PI * 2 }));
  }
  function camino(v) {
    let d = "";
    for (let j = 0; j <= 96; j++) {
      const t = j / 96 * Math.PI * 2;
      let x = 0, y = 0;
      for (const h of v) { x += h.ax * Math.cos(h.k * t + h.phi); y += h.ay * Math.sin(h.k * t + h.phi); }
      const n = v.reduce((s, h) => s + Math.max(h.ax, h.ay), 0) || 1;
      d += (j ? "L" : "M") + (x / n).toFixed(3) + " " + (y / n).toFixed(3);
    }
    return d + "Z";
  }
  function tono(color) { const i = Math.max(0, Object.keys(colores).indexOf(color)); return Math.round(220 * Math.pow(4, i / 7)); }
  function espectro(a, clase) {
    const ns = "http://www.w3.org/2000/svg", s = doc.createElementNS(ns, "svg"), p = doc.createElementNS(ns, "path");
    s.setAttribute("viewBox", "-1.15 -1.15 2.3 2.3"); s.setAttribute("aria-hidden", "true"); s.setAttribute("class", clase);
    p.setAttribute("d", camino(vector(a))); s.appendChild(p);
    s.dataset.sonido = tono(a.color) + "Hz"; s.dataset.achoLectura = nd; s.dataset.causa = "acho_reader_not_trained";
    return s;
  }

  let equipo = null, origen = "casa", editando = null, cancelarMorph = null;
  const quieto = () => root.matchMedia && root.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const activo = () => equipo && equipo.agents.find((a) => a.id === equipo.active) || null;

  function morph(svg, desde, hacia) {
    const p = svg.querySelector("path"), T = root.PreceptorTransicion;
    if (cancelarMorph) cancelarMorph();
    if (!T || quieto() || !desde) { p.setAttribute("d", camino(hacia)); return; }
    let raf = 0, t0 = null; const ms = 420;
    const paso = (ts) => {
      t0 = t0 === null ? ts : t0; const tau = Math.min(1, (ts - t0) / ms);
      p.setAttribute("d", camino(T.interpolar(desde, hacia, 0.5 - Math.cos(tau * Math.PI) / 2)));
      if (tau < 1) raf = root.requestAnimationFrame(paso); else cancelarMorph = null;
    };
    raf = root.requestAnimationFrame(paso); cancelarMorph = () => root.cancelAnimationFrame(raf);
  }

  // The general movement of every team button: each one travels a little along its own curve.
  function puntos(v, n, escala) {
    const nrm = v.reduce((s, h) => s + Math.max(h.ax, h.ay), 0) || 1, out = [];
    for (let j = 0; j <= n; j++) {
      const t = j / n * Math.PI * 2; let x = 0, y = 0;
      for (const h of v) { x += h.ax * Math.cos(h.k * t + h.phi); y += h.ay * Math.sin(h.k * t + h.phi); }
      out.push([x / nrm * escala, y / nrm * escala]);
    }
    const [x0, y0] = out[0];
    return out.map(([x, y]) => [+(x - x0).toFixed(2), +(y - y0).toFixed(2)]);  // starts and ends at rest
  }
  function gesto(nodo, v, modo, i) {
    if (quieto() || !nodo.animate) return;
    if (modo === "entra") {
      const pt = puntos(v, 8, 10).slice(0, 5).reverse();
      nodo.animate(pt.map(([x, y], j) => ({ transform: `translate(${x}px, ${y}px)`, opacity: j / (pt.length - 1) })),
        { duration: 380, delay: i * 45, easing: "cubic-bezier(.2,.7,.2,1)", fill: "backwards" });
    } else {
      nodo.animate(puntos(v, 16, 3).map(([x, y]) => ({ transform: `translate(${x}px, ${y}px)` })),
        { duration: 520, easing: "ease-in-out" });
    }
  }

  function el(tag, props, hijos) {
    const e = doc.createElement(tag);
    for (const [k, v] of Object.entries(props || {})) { if (k === "text") e.textContent = v; else if (k in e && k !== "list") e[k] = v; else e.setAttribute(k, v); }
    for (const h of hijos || []) if (h) e.appendChild(h);
    return e;
  }
  function estado(msg) { const s = doc.getElementById("equipo-estado"); if (s) s.textContent = msg; }

  async function enviar(url, cuerpo) {
    const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error((d.fallos && d.fallos.join("; ")) || d.causa || String(r.status));
    return d;
  }

  async function elegir(id) {
    const antes = activo(); if (!equipo || (antes && antes.id === id)) return;
    equipo.active = id; pintar(antes ? vector(antes) : null);
    try { await enviar("/api/equipo", equipo); origen = "local"; estado(tx().guardado); } catch (e) { estado(tx().error + e.message); }
  }

  function chapa() {
    const form = doc.getElementById("form-chat"), a = activo(); if (!form) return;
    let b = doc.getElementById("chapa-agente");
    if (!b) {
      b = el("button", { type: "button", id: "chapa-agente", className: "chapa-agente" });
      b.addEventListener("click", () => { const tab = doc.getElementById("tab-harness"); if (tab) tab.click(); });
      form.insertBefore(b, form.querySelector("textarea"));
    }
    b.hidden = !a; if (!a) return;
    b.style.setProperty("--agente", colores[a.color]);
    b.textContent = a.glyph; b.title = `${tx().chapa}: ${quien(a, tx())}`; b.setAttribute("aria-label", b.title);
  }

  function pintar(desde) {
    const caja = doc.getElementById("equipo"); if (!caja || !equipo) return;
    const L = tx(), a = activo();
    caja.replaceChildren();
    const grande = a ? espectro(a, "equipo-espectro") : null;
    if (grande) { grande.style.setProperty("--agente", colores[a.color]); grande.setAttribute("aria-hidden", "false"); grande.setAttribute("role", "img");
      grande.setAttribute("aria-label", `${quien(a, L)} · ${L.sonido(tono(a.color))} · ${L.lectura}`); }
    const rej = el("div", { className: "equipo-rejilla", role: "radiogroup", "aria-label": L.grupo });
    equipo.agents.forEach((ag) => {
      const sel = ag.id === equipo.active;
      const b = el("button", { type: "button", className: "agente", role: "radio", "aria-checked": String(sel), tabIndex: sel ? 0 : -1 },
        [espectro(ag, "agente-espectro"), el("span", { className: "agente-glifo", text: ag.glyph }),
          el("strong", { text: ag.name }), ag.name === L[ag.form] ? null : el("span", { className: "agente-forma", text: L[ag.form] })]);
      b.style.setProperty("--agente", colores[ag.color]); b.dataset.id = ag.id;
      b.addEventListener("click", () => elegir(ag.id));
      rej.appendChild(b);
      if (!desde || sel) gesto(b, vector(ag), desde ? "toca" : "entra", rej.children.length - 1);
    });
    rej.addEventListener("keydown", (e) => {
      const ids = equipo.agents.map((x) => x.id), i = ids.indexOf(equipo.active);
      const d = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key]; if (!d) return;
      e.preventDefault(); elegir(ids[(i + d + ids.length) % ids.length]).then(() => { const f = rej.querySelector('[aria-checked="true"]'); if (f) f.focus(); });
    });
    const acciones = el("div", { className: "equipo-acciones" }, [
      el("button", { type: "button", text: L.editar, onclick: () => abrir(a) }),
      el("button", { type: "button", text: L.lab, onclick: alLab }),
      el("button", { type: "button", text: "+ " + L.nuevo, onclick: () => abrir(null) })]);
    caja.append(el("p", { className: "pie", text: origen === "casa" ? L.casa : L.intro }), grande || el("span"), rej, acciones,
      el("p", { className: "pie", id: "equipo-estado", role: "status", "aria-live": "polite" }));
    if (editando !== undefined && editando !== false && caja.dataset.abierto === "1") editor();
    if (grande && desde) morph(grande, desde, vector(a));
    chapa();
  }

  async function alLab() {
    const a = activo(); if (!a) return;
    try { const d = await enviar("/api/equipo/lab", { id: a.id }); estado(tx().enlab(d.en_el_lab)); } catch (e) { estado(tx().error + e.message); }
  }

  function abrir(a) {
    if (!a && equipo.agents.length >= 6) { estado(tx().lleno); return; }
    editando = a ? { ...a } : { id: "", name: "", glyph: "✦", color: "sun", form: "free", ask: "" };
    editor();
  }

  function editor() {
    const caja = doc.getElementById("equipo"), L = tx(), e = editando; if (!caja || !e) return;
    const viejo = caja.querySelector(".equipo-editor"); if (viejo) viejo.remove();
    const nombre = el("input", { value: e.name, maxLength: 24, required: true, id: "equipo-nombre" });
    const pide = el("textarea", { value: e.ask, rows: 2, id: "equipo-pide", placeholder: L.pide });
    const forma = el("select", { id: "equipo-forma" }, formas.map((f) => el("option", { value: f, text: L[f], selected: f === e.form })));
    const radios = (lista, actual, campo, pinta) => el("div", { className: "equipo-opciones", role: "radiogroup", "aria-label": L[campo] },
      lista.map((v) => { const b = el("button", { type: "button", role: "radio", "aria-checked": String(v === actual), text: pinta(v), "aria-label": v });
        if (campo === "color") b.style.setProperty("--agente", colores[v]);
        b.addEventListener("click", () => { e[campo === "glifo" ? "glyph" : "color"] = v; editor(); }); return b; }));
    const form = el("form", { className: "equipo-editor" }, [
      el("label", { text: L.nombre }, [nombre]),
      el("p", { className: "pie", text: L.glifo }), radios(glifos, e.glyph, "glifo", (v) => v),
      el("p", { className: "pie", text: L.color }), radios(Object.keys(colores), e.color, "color", () => ""),
      el("label", { text: L.forma }, [forma]), el("label", { text: L.pide }, [pide]),
      el("div", { className: "equipo-acciones" }, [el("button", { type: "submit", text: L.guardar }),
        el("button", { type: "button", text: L.cancelar, onclick: () => { editando = null; form.remove(); } })])]);
    pide.addEventListener("input", () => { if (pide.value.trim()) forma.value = "free"; });
    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      e.name = nombre.value.trim(); e.form = forma.value; e.ask = e.form === "free" ? pide.value.trim() : "";
      if (!e.id) e.id = ("a" + fnv(e.name + equipo.agents.length).toString(36)).slice(0, 24);
      const nuevo = { ...equipo, agents: equipo.agents.some((x) => x.id === e.id)
        ? equipo.agents.map((x) => (x.id === e.id ? e : x)) : [...equipo.agents, e], active: e.id };
      try { await enviar("/api/equipo", nuevo); const antes = activo(); equipo = nuevo; origen = "local"; editando = null; pintar(antes && vector(antes)); estado(L.guardado); }
      catch (err) { estado(L.error + err.message); }
    });
    caja.appendChild(form); nombre.focus();
  }

  async function cargar() {
    try {
      const r = await fetch("/api/equipo", { cache: "no-store" }); const d = await r.json();
      if (!r.ok || !d.equipo || !Array.isArray(d.equipo.agents)) throw new Error("team_unreadable");
      equipo = d.equipo; origen = d.origen === "local" ? "local" : "casa"; pintar(null);
    } catch { const c = doc.getElementById("equipo"); if (c) c.replaceChildren(el("p", { className: "pie", text: nd + ": team_unreadable" })); }
  }

  const API = Object.freeze({ cargar, activo, vector, camino, tono, etiqueta: (a) => (a ? `${a.glyph} ${a.name}` : "") });
  root.PreceptorEquipo = API;
  if (doc && doc.getElementById("equipo")) cargar();
})(typeof window === "object" ? window : globalThis);
