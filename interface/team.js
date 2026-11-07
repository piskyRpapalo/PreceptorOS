/* Team · the team the person shapes in the Harness tab.
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
  const glifos = ["✦", "◆", "☺", "⋮", "?", "⌁", "◇", "◉", "▲", "●"];
  const formas = ["tips", "key_points", "easy", "steps", "ask_me", "free"];
  // Titles are public names: English, ASD-STE100 (renaming law). Only the help sentences are translated.
  const titulos = { grupo: "Your team", tips: "Advice", key_points: "Key points", easy: "Simple words", steps: "Steps",
    ask_me: "Check questions", free: "Your words", editar: "Edit", lab: "Send to Lab", nuevo: "Add agent", nombre: "Name",
    glifo: "Glyph", color: "Colour", forma: "Answer type", guardar: "Save", cancelar: "Cancel", chapa: "Agent that answers" };
  const frases = {
    es: { intro: "Elige un agente. El agente responde en Talk.", pide: "Escribe cómo tiene que responder el agente.",
      guardado: "El team está guardado en este nodo.", enlab: (n) => `El agente está en el Lab como propuesta. Fichas: ${n}.`,
      error: "Error: ", casa: "Equipo de la casa. No está guardado en este nodo.", lleno: "El máximo es 6 agentes.",
      lectura: "Lectura Acho: " + nd + ". El lector Acho no existe.", sonido: (hz) => `tono ${hz} Hz` },
    en: { intro: "Select an agent. The agent answers in Talk.", pide: "Write how the agent must answer.",
      guardado: "The team is saved on this node.", enlab: (n) => `The agent is in the Lab as a proposal. Cards: ${n}.`,
      error: "Error: ", casa: "House team. It is not saved on this node.", lleno: "The maximum is 6 agents.",
      lectura: "Acho reading: " + nd + ". The Acho reader does not exist.", sonido: (hz) => `tone ${hz} Hz` },
  };
  const quien = (a, L) => (a.name === L[a.form] ? a.name : `${a.name} · ${L[a.form]}`);
  const tx = () => Object.assign({}, titulos, frases[(doc.documentElement.lang || "en").slice(0, 2)] || frases.en);

  const M = root.AchoMotion;   // one house math for every option (interface/acho_motion.js)
  const colores = M.colours;
  const vector = (a) => M.vector(a.id + "|" + (a.ask || ""), a.form);
  const camino = M.path, tono = M.tone;
  function espectro(a, clase) { return M.spectrum(vector(a), clase, a.color); }
  let team = null, origen = "casa", editando = null, cancelarMorph = null;
  const quieto = M.still;
  const activo = () => team && team.agents.find((a) => a.id === team.active) || null;

  function morph(svg, desde, hacia) { if (cancelarMorph) cancelarMorph(); cancelarMorph = M.morph(svg, desde, hacia, 420); }
  function gesto(nodo, v, modo, i) { M.gesture(nodo, v, modo === "entra" ? "enter" : "touch", i); }
  function el(tag, props, hijos) {
    const e = doc.createElement(tag);
    for (const [k, v] of Object.entries(props || {})) { if (k === "text") e.textContent = v; else if (k in e && k !== "list") e[k] = v; else e.setAttribute(k, v); }
    for (const h of hijos || []) if (h) e.appendChild(h);
    return e;
  }
  function estado(msg) { const s = doc.getElementById("team-status"); if (s) s.textContent = msg; }

  async function enviar(url, cuerpo) {
    const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error((d.fallos && d.fallos.join("; ")) || d.causa || String(r.status));
    return d;
  }

  async function elegir(id) {
    const antes = activo(); if (!team || (antes && antes.id === id)) return;
    team.active = id; pintar(antes ? vector(antes) : null);
    try { await enviar("/api/team", team); origen = "local"; estado(tx().guardado); } catch (e) { estado(tx().error + e.message); }
  }

  function chapa() {
    const form = doc.getElementById("form-chat"), a = activo(); if (!form) return;
    let b = doc.getElementById("agent-badge");
    if (!b) {
      b = el("button", { type: "button", id: "agent-badge", className: "agent-badge" });
      b.addEventListener("click", () => { const tab = doc.getElementById("tab-harness"); if (tab) tab.click(); });
      form.insertBefore(b, form.querySelector("textarea"));
    }
    b.hidden = !a; if (!a) return;
    b.style.setProperty("--agente", colores[a.color]);
    b.textContent = a.glyph; b.title = `${tx().chapa}: ${quien(a, tx())}`; b.setAttribute("aria-label", b.title);
  }

  function pintar(desde) {
    const caja = doc.getElementById("team"); if (!caja || !team) return;
    const L = tx(), a = activo();
    caja.replaceChildren();
    const grande = a ? espectro(a, "team-spectrum") : null;
    if (grande) { grande.style.setProperty("--agente", colores[a.color]); grande.setAttribute("aria-hidden", "false"); grande.setAttribute("role", "img");
      grande.setAttribute("aria-label", `${quien(a, L)} · ${L.sonido(tono(a.color))} · ${L.lectura}`); }
    const rej = el("div", { className: "team-grid", role: "radiogroup", "aria-label": L.grupo });
    team.agents.forEach((ag) => {
      const sel = ag.id === team.active;
      const b = el("button", { type: "button", className: "agent", role: "radio", "aria-checked": String(sel), tabIndex: sel ? 0 : -1 },
        [espectro(ag, "agent-spectrum"), el("span", { className: "agent-glyph", text: ag.glyph }),
          el("strong", { text: ag.name }), ag.name === L[ag.form] ? null : el("span", { className: "agent-form", text: L[ag.form] })]);
      b.style.setProperty("--agente", colores[ag.color]); b.dataset.id = ag.id;
      b.addEventListener("click", () => elegir(ag.id));
      rej.appendChild(b);
      if (!desde || sel) gesto(b, vector(ag), desde ? "toca" : "entra", rej.children.length - 1);
    });
    rej.addEventListener("keydown", (e) => {
      const ids = team.agents.map((x) => x.id), i = ids.indexOf(team.active);
      const d = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key]; if (!d) return;
      e.preventDefault(); elegir(ids[(i + d + ids.length) % ids.length]).then(() => { const f = rej.querySelector('[aria-checked="true"]'); if (f) f.focus(); });
    });
    const acciones = el("div", { className: "team-actions" }, [
      el("button", { type: "button", text: L.editar, onclick: () => abrir(a) }),
      el("button", { type: "button", text: L.lab, onclick: alLab }),
      el("button", { type: "button", text: "+ " + L.nuevo, onclick: () => abrir(null) })]);
    caja.append(el("p", { className: "pie", text: origen === "casa" ? L.casa : L.intro }), grande || el("span"), rej, acciones,
      el("p", { className: "pie", id: "team-status", role: "status", "aria-live": "polite" }));
    if (editando !== undefined && editando !== false && caja.dataset.abierto === "1") editor();
    if (grande && desde) morph(grande, desde, vector(a));
    chapa();
  }

  async function alLab() {
    const a = activo(); if (!a) return;
    try { const d = await enviar("/api/team/lab", { id: a.id }); estado(tx().enlab(d.en_el_lab)); } catch (e) { estado(tx().error + e.message); }
  }

  function abrir(a) {
    if (!a && team.agents.length >= 6) { estado(tx().lleno); return; }
    editando = a ? { ...a } : { id: "", name: "", glyph: "✦", color: "sun", form: "free", ask: "" };
    editor();
  }

  function editor() {
    const caja = doc.getElementById("team"), L = tx(), e = editando; if (!caja || !e) return;
    const viejo = caja.querySelector(".team-editor"); if (viejo) viejo.remove();
    const nombre = el("input", { value: e.name, maxLength: 24, required: true, id: "team-name" });
    const pide = el("textarea", { value: e.ask, rows: 2, id: "team-ask", placeholder: L.pide });
    const forma = el("select", { id: "team-form" }, formas.map((f) => el("option", { value: f, text: L[f], selected: f === e.form })));
    const radios = (lista, actual, campo, pinta) => el("div", { className: "team-options", role: "radiogroup", "aria-label": L[campo] },
      lista.map((v) => { const b = el("button", { type: "button", role: "radio", "aria-checked": String(v === actual), text: pinta(v), "aria-label": v });
        if (campo === "color") b.style.setProperty("--agente", colores[v]);
        b.addEventListener("click", () => { e[campo === "glifo" ? "glyph" : "color"] = v; editor(); }); return b; }));
    const form = el("form", { className: "team-editor" }, [
      el("label", { text: L.nombre }, [nombre]),
      el("p", { className: "pie", text: L.glifo }), radios(glifos, e.glyph, "glifo", (v) => v),
      el("p", { className: "pie", text: L.color }), radios(Object.keys(colores), e.color, "color", () => ""),
      el("label", { text: L.forma }, [forma]), el("label", { text: L.pide }, [pide]),
      el("div", { className: "team-actions" }, [el("button", { type: "submit", text: L.guardar }),
        el("button", { type: "button", text: L.cancelar, onclick: () => { editando = null; form.remove(); } })])]);
    pide.addEventListener("input", () => { if (pide.value.trim()) forma.value = "free"; });
    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      e.name = nombre.value.trim(); e.form = forma.value; e.ask = e.form === "free" ? pide.value.trim() : "";
      if (!e.id) e.id = ("a" + fnv(e.name + team.agents.length).toString(36)).slice(0, 24);
      const nuevo = { ...team, agents: team.agents.some((x) => x.id === e.id)
        ? team.agents.map((x) => (x.id === e.id ? e : x)) : [...team.agents, e], active: e.id };
      try { await enviar("/api/team", nuevo); const antes = activo(); team = nuevo; origen = "local"; editando = null; pintar(antes && vector(antes)); estado(L.guardado); }
      catch (err) { estado(L.error + err.message); }
    });
    caja.appendChild(form); nombre.focus();
  }

  // Read the team; a server that is restarting gets two quiet retries, then the cause and a Retry button.
  // The last good team is kept on screen: a failed read never erases what the person already sees.
  async function cargar(intento) {
    const n = intento || 0; let d = null;
    try {
      const r = await fetch("/api/team", { cache: "no-store" }); d = await r.json();
      if (!r.ok || !d.team || !Array.isArray(d.team.agents)) throw new Error("bad");
    } catch {
      if (n < 2) { root.setTimeout(() => cargar(n + 1), 900 * (n + 1)); return; }
      return fallo("team_server_unreachable");
    }
    try { team = d.team; origen = d.origen === "local" ? "local" : "casa"; pintar(null); }
    catch (e) { fallo("team_paint_failed"); if (root.console) root.console.error("[team]", e); }
  }
  function fallo(causa) {
    const c = doc.getElementById("team"); if (!c) return;
    const linea = el("p", { className: "pie", text: nd + ": " + causa });
    const otra = el("button", { type: "button", text: "Retry" }); otra.addEventListener("click", () => cargar(0));
    const viejo = c.querySelector(".team-grid");
    if (viejo) { estado(nd + ": " + causa); return; }
    c.replaceChildren(linea, el("div", { className: "team-actions" }, [otra]));
  }

  const API = Object.freeze({ load: cargar, active: activo, vector, path: camino, tone: tono, label: (a) => (a ? `${a.glyph} ${a.name}` : "") });
  root.PreceptorTeam = API;
  if (doc && doc.getElementById("team")) cargar();
})(typeof window === "object" ? window : globalThis);
