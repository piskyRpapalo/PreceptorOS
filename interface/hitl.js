/* HITL · PRs pendientes de la firma del Soberano (decision mia, sin firma).
 * Lista: GET /api/hitl (corre HITL sin args). Detalle: GET /api/hitl/<n> (solo lectura: se para en la pregunta).
 * «Sí, firmo y fusiono» = POST /api/hitl/<n> con el token de la página: corre HITL --si.
 * El «Sí» es el acto del Soberano; esta pagina no firma por si sola.
 */
(function (root) {
  "use strict";
  const doc = root.document;
  if (!doc || !doc.getElementById("hitl")) return;
  const $ = (id) => doc.getElementById(id);
  let token = ""; // llega con la lista (GET /api/hitl), nunca en la página
  const estado = $("hitl-estado"), lista = $("hitl-lista"), detalle = $("hitl-detalle");
  const resultado = $("hitl-resultado"), si = $("hitl-si"), no = $("hitl-no");
  const cabecera = $("hitl-cabecera"), cuerpo = $("hitl-cuerpo"), cuenta = $("hitl-n");
  let numero = null, ocupado = false;
  cabecera.addEventListener("click", () => {
    const abrir = cuerpo.hidden; cuerpo.hidden = !abrir; cabecera.setAttribute("aria-expanded", String(abrir));
  });
  const simbolo = (c) => c === "OK" ? "✓ checks ok" : c === "ROJO" ? "✗ checks en rojo" : "… checks en curso";
  // Vigía: texto (no solo color) y hora local HH:MM.
  function vigia(v) {
    if (!v) return "";
    const d = new Date(v.ts), hora = isNaN(d) ? "" : " · watch " + d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
    const t = v.estado === "listo" ? "✓ listo para firmar" : v.estado === "rojo" ? "✗ rojo: " + ((v.rojos || []).join(", ") || "sin detalle") : v.estado === "firmado" ? "✓ firmado" : "";
    return t ? t + hora : "";
  }
  function el(tag, cls, texto) {
    const e = doc.createElement(tag); if (cls) e.className = cls;
    if (texto != null) e.textContent = texto; return e;
  }
  async function leerJson(url) {
    const r = await fetch(url, { cache: "no-store" });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(d.motivo || d.causa || ("HTTP " + r.status));
    return d;
  }
  function cerrar() { numero = null; detalle.hidden = true; si.disabled = false; no.disabled = false;
    lista.querySelectorAll(".hitl-fila").forEach((b) => b.setAttribute("aria-expanded", "false")); }
  function pintarFilas(filas) {
    lista.after(detalle); lista.replaceChildren(); cuenta.textContent = String(filas.length);
    if (filas.length) { cuerpo.hidden = false; cabecera.setAttribute("aria-expanded", "true"); } // open by default when something waits
    if (!filas.length) { estado.textContent = "No PRs wait for your signature."; return; }
    estado.textContent = filas.length + (filas.length === 1 ? " PR espera tu firma." : " PRs esperan tu firma.");
    for (const f of filas) {
      const li = el("li"), b = el("button", "hitl-fila");
      b.type = "button"; b.setAttribute("aria-expanded", "false"); b.setAttribute("aria-controls", "hitl-detalle");
      b.append(el("strong", null, "#" + f.numero + " · " + (f.titulo || "(untitled)")),
        el("span", "pie", (f.cabeza || "") + " · " + (f.estado || "") + " · " + simbolo(f.checks)));
      const vt = vigia(f.vigia); if (vt) b.append(el("span", "hitl-vigia", vt));
      b.addEventListener("click", () => (numero === f.numero ? cerrar() : abrir(f, li, b)));
      li.appendChild(b); lista.appendChild(li);
    }
  }
  async function cargar() {
    estado.textContent = "Reading the PRs…";
    try { const d = await leerJson("/api/hitl"); token = d.token || ""; pintarFilas(d.filas || []);
      estado.textContent += " · read " + new Date().toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit" }); }
    catch (e) { lista.replaceChildren(); cuenta.textContent = "?"; estado.textContent = "NO_DATA: the list could not be read (" + e.message + ")."; }
  }
  async function abrir(f, li, b) {
    if (ocupado) return;
    cerrar(); // one panel open at a time: read it first, then choose
    if (li) { li.appendChild(detalle); b.setAttribute("aria-expanded", "true"); }
    numero = f.numero; resultado.textContent = "";
    $("hitl-detalle-titulo").textContent = "#" + f.numero + " · " + (f.titulo || "");
    $("hitl-resumen").textContent = "Reading the summary…";
    si.disabled = f.checks === "ROJO"; no.disabled = false; detalle.hidden = false;
    if (f.checks === "ROJO") resultado.textContent = "Checks are red: it cannot be signed until they are fixed.";
    try { $("hitl-resumen").textContent = (await leerJson("/api/hitl/" + f.numero)).texto || "(sin resumen)"; }
    catch (e) { $("hitl-resumen").textContent = "NO_DATA: the summary could not be read (" + e.message + ")."; }
    porque(f);
    detalle.scrollIntoView({ block: "nearest" });
  }
  async function firmar() {
    if (numero === null || ocupado) return;
    ocupado = true; si.disabled = true; no.disabled = true;
    resultado.textContent = "Firmando #" + numero + "… puede tardar varios minutos: espera a que los checks terminen.";
    try {
      const r = await fetch("/api/hitl/" + numero, { method: "POST", headers: { "X-Hitl-Token": token }, cache: "no-store" });
      const texto = await r.text();
      resultado.textContent = r.ok ? texto.trim() : "Not signed (" + r.status + "): " + texto.trim();
    } catch (e) { resultado.textContent = "NO_DATA: the app did not answer (" + e.message + ")."; }
    finally { ocupado = false; cerrar(); lista.after(detalle); cargar(); }
  }
  // Why is it not advancing? One fixed-order verdict from GET /api/hitl/<n>/why (read-only). The question for
  // Hexelion is built by the server from those facts; its answer is a suggestion and is labelled so.
  const why = el("p", "pie hitl-why"), ask = el("button", "hitl-ask", "Ask Hexelion what to do"), answer = el("p", "pie hitl-answer");
  why.id = "hitl-why"; why.setAttribute("role", "status"); ask.type = "button"; ask.id = "hitl-ask"; ask.hidden = true;
  answer.id = "hitl-answer"; answer.setAttribute("role", "status"); answer.setAttribute("aria-live", "polite");
  $("hitl-resumen").after(why, ask, answer);
  let pregunta = "";
  async function porque(f) {
    why.textContent = "Reading why it waits…"; ask.hidden = true; answer.textContent = ""; pregunta = "";
    try {
      const d = await leerJson("/api/hitl/" + f.numero + "/why");
      if (numero !== f.numero) return;
      why.textContent = (d.line || "") + (d.signing ? " · " + d.signing : "");
      pregunta = d.question || ""; ask.hidden = !pregunta;
    } catch (e) { why.textContent = "NO_DATA: the reason could not be read (" + e.message + ")"; }
  }
  ask.addEventListener("click", async () => {
    if (!pregunta || ask.disabled) return;
    ask.disabled = true; answer.textContent = "Asking Hexelion… on local hardware this can take a minute.";
    try {
      const r = await fetch("/api/hexelion/chat", { method: "POST", cache: "no-store",
        headers: { "Content-Type": "application/json" }, body: JSON.stringify({ texto: pregunta }) });
      const d = await r.json().catch(() => ({})), x = d.respuesta || {};
      const texto = typeof x === "string" ? x : (x.texto || x.respuesta || "");
      answer.textContent = texto ? "Hexelion suggests (not a decision): " + texto
        : "NO_DATA: Hexelion did not answer (" + (x.causa || d.causa || "HTTP " + r.status) + ")";
    } catch (e) { answer.textContent = "NO_DATA: the app could not be reached (" + e.message + ")"; }
    finally { ask.disabled = false; }
  });
  function rechazar() { cerrar(); resultado.textContent = "No firmado: nada hecho."; }
  $("hitl-recargar").addEventListener("click", cargar);
  si.addEventListener("click", firmar);
  no.addEventListener("click", rechazar);
  cargar();
  // Al abrir Boundary, la lista se relee en vivo (GET /api/hitl), sin datos guardados.
  const panel = $("panel-gobierno");
  if (panel) new root.MutationObserver(() => { if (!panel.hidden) cargar(); }).observe(panel, { attributes: true, attributeFilter: ["hidden"] });
  root.PreceptorHitl = Object.freeze({ load: cargar });
})(typeof window === "object" ? window : globalThis);
