/* Firmas · Pending signatures, at the top of the Command tab.
 * Reads /api/firmas, the card the internal scraper (bin/firmas-scraper, every 10 min) writes.
 * One Acho card per open front. The page never signs: «Copy» gives the one command the
 * Sovereign runs (preceptoros-firmar), which signs, waits for CI, merges and deploys.
 */
(function (root) {
  "use strict";
  const doc = root.document, M = root.AchoMotion;
  const nd = String.fromCharCode(78, 79, 95, 68, 65, 84, 65);
  const acciones = { retarget: "Retarget", sign: "Ready to sign", merge: "Signed · merge", running: "Checks running",
    red: "Checks red", wait_base: "Wait for base", no_data: nd };
  const corto = (repo) => repo === "piskyRpapalo/preceptoros-web" ? "web" : repo === "piskyRpapalo/PreceptorOS" ? "app" : repo;
  function el(tag, props, hijos) {
    const e = doc.createElement(tag);
    for (const [k, v] of Object.entries(props || {})) { if (k === "text") e.textContent = v; else e.setAttribute(k, v); }
    for (const h of hijos || []) if (h) e.appendChild(h);
    return e;
  }
  function edad(iso) {
    const t = Date.parse(iso || ""); if (!t) return nd;
    const m = Math.max(0, Math.round((Date.now() - t) / 60000));
    return m < 60 ? m + " min ago" : Math.round(m / 60) + " h ago";
  }
  async function copiar(texto, boton) {
    try { await root.navigator.clipboard.writeText(texto); }
    catch { const a = el("textarea"); a.value = texto; doc.body.appendChild(a); a.select(); try { doc.execCommand("copy"); } finally { a.remove(); } }
    const antes = boton.textContent; boton.textContent = "Copied"; root.setTimeout(() => { boton.textContent = antes; }, 1400);
  }
  function tarjeta(f, i) {
    const seed = "firma|" + f.repo + "#" + f.n, colour = M ? M.colourOf(seed) : "sun";
    const card = el("article", { class: "firma firma-" + f.action });
    if (M) { card.style.setProperty("--agente", M.colours[colour]); card.achoVector = M.vector(seed); card.prepend(M.spectrum(card.achoVector, "firma-mark", colour)); }
    card.append(el("p", { class: "firma-estado", text: acciones[f.action] || nd }),
      el("strong", { text: corto(f.repo) + " #" + f.n }), el("span", { class: "firma-titulo", text: f.title || "" }),
      el("span", { class: "pie", text: "head " + (f.head || nd) + " · checks " + f.checks }));
    const fila = el("div", { class: "firma-acciones" });
    const cmd = f.action === "retarget" ? f.retarget : (f.action === "sign" || f.action === "merge") ? "preceptoros-firmar " + corto(f.repo) + " " + f.n : null;
    if (cmd) { const b = el("button", { type: "button", text: f.action === "retarget" ? "Copy retarget" : "Copy sign" }); b.addEventListener("click", () => copiar(cmd, b)); fila.appendChild(b); }
    if (f.url) fila.appendChild(el("a", { href: f.url, target: "_blank", rel: "noopener", text: "Open" }));
    card.appendChild(fila);
    if (M) root.setTimeout(() => M.gesture(card, card.achoVector, "enter", i), 0);
    return card;
  }
  async function cargar() {
    const caja = doc.getElementById("firmas"); if (!caja) return;
    let d;
    try { const r = await fetch("/api/firmas", { cache: "no-store" }); d = await r.json(); }
    catch { caja.replaceChildren(el("p", { class: "pie", text: nd + ": signatures_unreadable" })); return; }
    const filas = Array.isArray(d.filas) ? d.filas : [];
    const listos = filas.filter((f) => f.action === "sign" || f.action === "retarget" || f.action === "merge").length;
    const det = el("details", { class: "firmas-caja" }); if (listos) det.open = true;
    det.appendChild(el("summary", { text: "Pending signatures · " + listos + " ready · " + filas.length + " open" }));
    det.appendChild(el("p", { class: "pie", text: d.estado === nd ? nd + ": " + (d.causa || "") : "Scraped " + edad(d.medido) + ". Copy sign gives one command: it signs, waits for CI, merges and deploys." }));
    const grid = el("div", { class: "firmas-grid" }); filas.forEach((f, i) => grid.appendChild(tarjeta(f, i))); det.appendChild(grid);
    caja.replaceChildren(det);
  }
  root.PreceptorFirmas = Object.freeze({ load: cargar });
  if (doc && doc.getElementById("firmas")) { cargar(); root.setInterval(cargar, 120000); }
})(typeof window === "object" ? window : globalThis);
