/* Notebook operativo · one read-only projection of receipt-bearing agents, loops and reviews.
 * Existing agents in Harness are prompt styles, not processes; never call them live.
 * No arbitrary remote fetch, eval, signer, scheduler or local-store duplicate.
 */
(function (root) {
  "use strict";
  const translations = {
    es: {
      title: "Cuaderno operativo", subtitle: "Agentes, ciclos y revisiones con fuente. Un dato declarado no acredita un proceso vivo.",
      loading: "Leyendo los recibos locales…", refresh: "Actualizar lecturas",
      agents: "Agentes observados", loops: "Bucles del nodo", reports: "Revisiones",
      emptyAgents: "NO_DATA: censo de agentes ausente", emptyLoops: "NO_DATA: sensor de bucles sin lectura",
      error: "NO_DATA: servicio de Notebook no disponible", source: "Recibo", last: "Última observación",
      profile: "Observación declarada", lastLoop: "Última pasada", nextLoop: "Próxima pasada",
      timer: "Timer", wbr: "WBR · Semana", mbr: "MBR · Mes",
      declared: "Declarado; aún sin verificación independiente", unavailable: "NO_DATA",
      stale: "Dato antiguo", observed: "Observado; no se ha verificado el proceso",
      updated: "Lectura terminada. El estado pertenece a las fuentes, no a esta pantalla.",
      receipts: "Recibos de órdenes", receiptsNote: "Un recibo dice que una orden corrió y cómo terminó; no que su salida fuera correcta."
    },
    en: {
      title: "Operations Notebook", subtitle: "Sourced agents, cycles and reviews. A declaration does not prove a running process.",
      loading: "Reading local receipts…", refresh: "Refresh readings",
      agents: "Observed agents", loops: "Node loops", reports: "Reviews",
      emptyAgents: "NO_DATA: agent census missing", emptyLoops: "NO_DATA: loop sensor unavailable",
      error: "NO_DATA: Notebook service unavailable", source: "Receipt", last: "Last observation",
      profile: "Declared observation", lastLoop: "Last run", nextLoop: "Next run",
      timer: "Timer", wbr: "WBR · Week", mbr: "MBR · Month",
      declared: "Declared; independent verification pending", unavailable: "NO_DATA",
      stale: "Stale reading", observed: "Observed; running process unverified",
      updated: "Read complete. State belongs to sources, not this screen.",
      receipts: "Command receipts", receiptsNote: "A receipt says a command ran and how it ended; not that its output was right."
    }
  };
  function lang() {
    return /^es(?:-|$)/.test(typeof document !== "undefined" ? document.documentElement.lang : "es") ? translations.es : translations.en;
  }
  function clean(v, limit) { return typeof v === "string" && v.length <= limit ? v : ""; }
  function projectNotebook(raw) {
    if (!raw || raw.schema !== "preceptoros.notebook-readonly/0" ||
        !Array.isArray(raw.agents) || !Array.isArray(raw.reports)) return null;
    return {
      status: clean(raw.agents_status, 20),
      cause: clean(raw.agents_cause, 72),
      agents: raw.agents.filter(a => a && typeof a === "object").slice(0, 12).map(a => ({
        id: clean(a.id, 40), name: clean(a.name, 48), role: clean(a.role, 64),
        status: ["OBSERVADO", "STALE", "NO_DATA"].includes(a.status) ? a.status : "NO_DATA",
        cause: clean(a.cause, 72), last: clean(a.last_seen, 40), receipt: clean(a.receipt_sha256, 64)
      })),
      reports: raw.reports.filter(r => r && typeof r === "object" && ["WBR", "MBR"].includes(r.kind)).slice(0, 2).map(r => ({
        kind: r.kind === "WBR" ? "WBR" : "MBR",
        status: r.status === "DECLARADO" ? "DECLARADO" : "NO_DATA",
        cause: clean(r.cause, 100), period: clean(r.period, 16),
        summary: clean(r.summary, 420), stamp: clean(r.measured_at, 40),
        receipt: clean(r.receipt_sha256, 64)
      })),
      receiptsCause: clean(raw.receipts_cause, 72),
      receipts: (Array.isArray(raw.receipts) ? raw.receipts : []).filter(r => r && typeof r === "object").slice(-20).map(r => ({
        tool: clean(r.tool, 24), result: r.result === "ok" ? "ok" : "failed",
        status: ["DECLARED", "STALE"].includes(r.status) ? r.status : "NO_DATA", cause: clean(r.cause, 72),
        ms: Number.isSafeInteger(r.ms) ? r.ms : null, bytes: Number.isSafeInteger(r.out_bytes) ? r.out_bytes : null,
        stamp: clean(r.measured_at, 40), receipt: clean(r.receipt_sha256, 64)
      }))
    };
  }
  function projectHarness(raw, now) {
    if (!raw || !Array.isArray(raw.bucles)) return { rows: [], cause: "sensor_invalid" };
    const measured = typeof raw.medido === "string" ? Date.parse(raw.medido) : NaN;
    if (raw.estado === "NO_DATA" || !Number.isFinite(measured) || measured > now ||
        now - measured > 300000) return { rows: [], cause: clean(raw.causa, 72) || "sensor_stale_or_missing" };
    return { rows: raw.bucles.slice(0, 24).filter(b => b && typeof b === "object").map(b => ({
      name: clean(b.unidad, 88) || "NO_DATA", last: clean(b.ultima, 80),
      next: clean(b.proxima, 80), cause: clean(b.causa, 72),
      result: clean(b.resultado, 60)
    })), cause: null };
  }

  function elem(tag, cls, text) {
    const el = document.createElement(tag);
    if (cls) el.className = cls;
    if (text !== undefined) el.textContent = text;
    return el;
  }
  function field(box, label, value) {
    box.append(elem("p", "notebook-fact", label + ": " + (value || "NO_DATA")));
  }
  function card(title, badge, description) {
    const article = elem("article", "notebook-card");
    const top = elem("div", "notebook-top");
    top.append(elem("h4", "", title));
    const status = elem("span", "notebook-status", badge);
    status.dataset.status = badge;
    top.append(status); article.append(top);
    if (description) article.append(elem("p", "notebook-fact", description));
    return article;
  }
  async function request(path) {
    const r = await fetch(path, { cache: "no-store", credentials: "same-origin" });
    if (!r.ok) throw new Error("http_" + r.status);
    return r.json();
  }
  async function load() {
    const panel = document.getElementById("panel-cuaderno");
    if (!panel) return;
    const t = lang();
    [
      ["notebook-title", t.title], ["notebook-subtitle", t.subtitle],
      ["notebook-refresh", t.refresh], ["notebook-agents-title", t.agents],
      ["notebook-loops-title", t.loops], ["notebook-reports-title", t.reports]
    ].forEach(([id, value]) => { const target = document.getElementById(id); if (target) target.textContent = value; });
    const button = document.getElementById("notebook-refresh");
    const status = document.getElementById("notebook-status");
    button.disabled = true;
    status.textContent = t.loading;
    const [notesResult, harnessResult] = await Promise.allSettled([
      request("/api/notebook"), request("/api/harness")
    ]);
    const notes = notesResult.status === "fulfilled" ? projectNotebook(notesResult.value) : null;
    const loops = harnessResult.status === "fulfilled" ?
      projectHarness(harnessResult.value, Date.now()) : { rows: [], cause: "sensor_unreachable" };
    const aList = document.getElementById("notebook-agents");
    const lList = document.getElementById("notebook-loops");
    const rList = document.getElementById("notebook-reports");
    aList.replaceChildren(); lList.replaceChildren(); rList.replaceChildren();
    if (notes && notes.agents.length) {
      notes.agents.forEach(a => {
        const label = a.status === "OBSERVADO" ? t.observed : a.status === "STALE" ? t.stale : t.unavailable;
        const c = card(a.name, a.status, a.role + " · " + label);
        field(c, t.last, a.last);
        field(c, t.source, a.receipt && a.receipt.slice(0, 16) + "…");
        if (a.cause) field(c, "Causa", a.cause);
        aList.append(c);
      });
    } else aList.append(card(t.emptyAgents, "NO_DATA", notes ? notes.cause : "notebook_endpoint_unavailable"));
    if (loops.rows.length) {
      loops.rows.forEach(l => {
        const c = card(l.name, t.timer, l.result || t.profile);
        field(c, t.lastLoop, l.last);
        field(c, t.nextLoop, l.next);
        if (l.cause) field(c, "Causa", l.cause);
        lList.append(c);
      });
    } else lList.append(card(t.emptyLoops, "NO_DATA", loops.cause));
    const reports = notes ? notes.reports : [
      { kind: "WBR", status: "NO_DATA", cause: "notebook_endpoint_unavailable" },
      { kind: "MBR", status: "NO_DATA", cause: "notebook_endpoint_unavailable" }
    ];
    reports.forEach(r => {
      const c = card(r.kind === "WBR" ? t.wbr : t.mbr, r.status, r.summary || r.cause);
      if (r.status === "DECLARADO") {
        field(c, "Periodo", r.period);
        field(c, t.last, r.stamp);
        field(c, t.source, r.receipt && r.receipt.slice(0, 16) + "…");
        field(c, "Verificación", t.declared);
      }
      rList.append(c);
    });
    const xList = document.getElementById("notebook-receipts");
    if (xList) {
      xList.replaceChildren();
      const rows = notes ? notes.receipts : [];
      if (rows.length) {
        const last = rows[rows.length - 1];
        const c = card(t.receipts + " · " + rows.length, last.status, t.receiptsNote);
        rows.slice(-6).reverse().forEach(r => c.append(elem("p", "notebook-fact",
          [r.stamp.replace("T", " ").replace("Z", " UTC"), r.tool, r.result, r.ms === null ? "NO_DATA" : r.ms + " ms",
            r.bytes === null ? "NO_DATA" : r.bytes + " B", r.status, r.receipt.slice(0, 12)].join(" · "))));
        xList.append(c);
      } else xList.append(card(t.receipts, "NO_DATA", notes ? notes.receiptsCause || "no_valid_receipt" : "notebook_endpoint_unavailable"));
    }
    status.textContent = (notes ? t.updated : t.error) + (loops.cause ? " · Bucles: " + loops.cause : "");
    button.disabled = false;
  }
  function mount() {
    const refresh = document.getElementById("notebook-refresh");
    if (refresh) refresh.addEventListener("click", () => load().catch(() => {}));
  }
  const api = Object.freeze({ load, projectNotebook, projectHarness });
  root.PreceptorNotebook = api;
  if (typeof module === "object" && module.exports) module.exports = api;
  if (typeof document !== "undefined") mount();
})(typeof window === "object" ? window : globalThis);
