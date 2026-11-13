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
        tool: clean(r.tool, 24), result: ["ok", "refused"].includes(r.result) ? r.result : "failed",
        voice: clean(r.voice, 24),
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
          [r.stamp.replace("T", " ").replace("Z", " UTC"), (r.voice ? r.voice + " · " : "") + r.tool,
            r.result === "refused" ? "refused by the fence" : r.result, r.ms === null ? "NO_DATA" : r.ms + " ms",
            r.bytes === null ? "NO_DATA" : r.bytes + " B", r.status, r.receipt.slice(0, 12)].join(" · "))));
        xList.append(c);
      } else xList.append(card(t.receipts, "NO_DATA", notes ? notes.receiptsCause || "no_valid_receipt" : "notebook_endpoint_unavailable"));
    }
    await loadTurns("notebook-turns", "notebook-turns-status", 12);
    await loadTasks("notebook-tasks", "notebook-tasks-status");
    await loadBench("notebook-bench", "notebook-bench-status", notesResult.status === "fulfilled" ? notesResult.value : null);
    status.textContent = (notes ? t.updated : t.error) + (loops.cause ? " · Bucles: " + loops.cause : "");
    button.disabled = false;
  }
  /* What happened to each request (meta-harness 01). One projection from /api/hexelion/turnos feeds the screen, the
   * screen reader and the machine: the card's words are the turn's `sentence` and `next`, its data-state is the
   * machine state, and the status line speaks only when the summary changed (no announcement on every refresh). */
  // Acho classes (autonomy parity): how a turn sounds, decided by turnos_hexelion with its sentence. Unknown -> empty.
  const achoClasses = ["ok", "needs_you", "unanswered", "fence", "exec_fail", "empty", "bridge_down"];
  function acho(x) { const c = x && x.acho && x.acho.class; return achoClasses.includes(c) ? c : "empty"; }
  const turnStates = ["ANSWERED", "ANSWERED_UNVERIFIED", "LOCAL_SENSOR", "ACTED", "ACTION_REFUSED", "ACTION_UNVERIFIED", "NO_ANSWER", "REPLIED", "NO_REPLY_RECORDED"];
  function projectTurns(raw) {
    if (!raw || raw.schema !== "preceptoros.hexelion-turns/1" || !Array.isArray(raw.turns)) return null;
    return {
      state: raw.state === "MEASURED" ? "MEASURED" : "NO_DATA", cause: clean(raw.cause, 80),
      turns: raw.turns.filter(x => x && typeof x === "object" && Number.isSafeInteger(x.n)).slice(0, 12).map(x => ({
        n: x.n, state: turnStates.includes(x.state) ? x.state : "NO_DATA", asked: clean(x.asked_at, 24),
        by: clean(x.asked_by_name, 24), to: clean(x.to_name, 24), question: clean(x.question, 160),
        sentence: clean(x.sentence, 200), next: clean(x.next, 160), who: clean(x.answered_by_name, 24),
        evidence: clean(x.evidence, 60), cause: clean(x.cause, 80), answer: Number.isSafeInteger(x.answer_n) ? x.answer_n : null,
        acho: turnStates.includes(x.state) ? acho(x) : "empty"
      }))
    };
  }
  /* Talk says what this card says (autonomy parity): the chat reply carries the turn turnos_hexelion projected from the
   * thread, and this one function turns it into Talk's status line. Same state, same sentence, same cause as the card.
   * Missing, malformed or unknown: NO_DATA with its cause. Talk never words a result of its own. */
  function turnLine(raw) {
    const x = raw && typeof raw === "object" ? raw : null;
    if (!x || !Number.isSafeInteger(x.n)) {
      const cause = clean(x && x.cause, 80) || "turn_missing";
      return { state: "NO_DATA", n: null, cause, sentence: "", next: "", acho: "empty",
        line: "NO_DATA: this request has no projected turn (" + cause.replace(/_/g, " ") + "); the Notebook keeps the thread." };
    }
    const state = turnStates.includes(x.state) ? x.state : "NO_DATA";
    if (x.cut === "envelope" && state !== "NO_DATA") {
      return { state, n: x.n, cause: clean(x.cause, 80), sentence: "", next: "", acho: "empty",
        line: state + ": the full sentence did not fit this reply; the Notebook shows it for request " + x.n + "." };
    }
    const sentence = clean(x.sentence, 200), next = clean(x.next, 160);
    if (state === "NO_DATA" || !sentence) {
      return { state: "NO_DATA", n: x.n, cause: "turn_unreadable", sentence: "", next: "", acho: "empty",
        line: "NO_DATA: the turn for this request could not be read; the Notebook keeps the thread." };
    }
    return { state, n: x.n, cause: clean(x.cause, 80), sentence, next, acho: acho(x), line: next ? sentence + " " + next : sentence };
  }
  /* Delegated tasks (autonomy parity, task slice): the delegation journal's receipts told by tareas_hexelion. The Notebook only paints
   * them; it never claims, retries or authorises. Unknown states are NO_DATA; unknown Acho classes are empty. */
  const taskStates = ["DONE_CHECKED", "DONE_UNCHECKED", "NEEDS_YOUR_AUTHORIZATION", "FAILED", "CANCELLED", "OUTCOME_UNKNOWN", "NO_RESULT_RECORDED", "NO_DATA"];
  function projectTasks(raw) {
    if (!raw || raw.schema !== "preceptoros.hexelion-tasks/1" || !Array.isArray(raw.tasks)) return null;
    const tasks = raw.tasks.slice(0, 12).filter(x => x && typeof x === "object").map(x => {
      const state = taskStates.includes(x.state) ? x.state : "NO_DATA";
      const sentence = clean(x.sentence, 240), next = clean(x.next, 160);
      return { run: clean(x.run_id, 32) || "unnamed", state: sentence ? state : "NO_DATA", cause: clean(x.cause, 80),
        sentence: sentence || "NO_DATA: this task could not be read.", next, acho: state === x.state ? acho(x) : "empty" };
    });
    const needs = tasks.filter(x => x.state === "NEEDS_YOUR_AUTHORIZATION").length;
    return { state: raw.state === "MEASURED" ? "MEASURED" : "NO_DATA", cause: clean(raw.cause, 80), tasks, needs };
  }
  function taskSummary(p) {
    if (!p) return "NO_DATA: the tasks could not be read (the app server did not answer).";
    if (!p.tasks.length) return "NO_DATA: " + (p.cause || "no task recorded").replace(/_/g, " ") + ".";
    const head = p.needs ? p.needs + (p.needs === 1 ? " task needs" : " tasks need") + " your authorization. " : "";
    return head + "Last task: " + p.tasks[0].sentence;
  }
  async function loadTasks(listId, statusId) {
    const list = document.getElementById(listId), status = document.getElementById(statusId);
    if (!list) return null;
    let p = null;
    try { p = projectTasks(await request("/api/hexelion/tareas")); } catch { p = null; }
    list.replaceChildren();
    (p ? p.tasks : []).forEach(x => {
      const c = card("Task " + x.run, x.state, x.sentence);
      c.dataset.state = x.state; c.dataset.acho = x.acho;
      if (x.next) field(c, "Next", x.next);
      list.append(c);
    });
    const summary = taskSummary(p);
    if (!p || !p.tasks.length) list.append(card("Delegated tasks", "NO_DATA", summary));
    if (status && spoken[statusId] !== summary) { status.textContent = summary; spoken[statusId] = summary; }
    return p;
  }
  function turnCard(x) {
    const when = x.asked.replace("T", " ").replace("Z", " UTC");
    const c = card(x.by + " asked " + x.to + " · " + when, x.state, x.sentence);
    c.dataset.n = String(x.n); c.dataset.state = x.state; c.dataset.acho = x.acho;
    c.append(elem("p", "notebook-fact", "«" + x.question + "»"));
    field(c, "Answered by", x.who || "nobody recorded");
    field(c, "Evidence", x.evidence || "none");
    if (x.cause) field(c, "Cause", x.cause);
    field(c, "Thread", "message " + x.n + (x.answer ? " → " + x.answer : ""));
    c.append(elem("p", "notebook-fact notebook-next", x.next));
    return c;
  }
  const spoken = {};
  /* Lab benchmark runs (LAB bench-repro-01-v1, via lab_bench.py). Each card is one execution: the runner's
   * sentence, then the checks the app re-did and the fields nobody measured, each with its cause. */
  function benchCard(r) {
    const c = card((clean(r.model, 40) || "NO_DATA") + " · " + clean(r.date, 25).replace("T", " ").slice(0, 16) + " UTC",
      clean(r.state, 12) || "NO_DATA", clean(r.sentence, 420));
    c.dataset.receipt = clean(r.receipt, 16);
    field(c, "Receipt fingerprint", clean(r.fingerprint, 12) + " · " + clean(r.receipt, 16));
    field(c, "Comparison key (controls only)", clean(r.comparison_key, 12));
    field(c, "Source", "commit " + (clean(r.commit, 12) || "NO_DATA") + " · runner " + (clean(r.runner, 12) || "NO_DATA"));
    field(c, "Model", (clean(r.model_digest, 12) || "NO_DATA") + (r.model_stable === true ? " · stable across samples" : " · stability NO_DATA"));
    (Array.isArray(r.samples) ? r.samples : []).slice(0, 4).forEach((x) => field(c, "Sample " + (x.attempt || "?"),
      (x.tokens_per_s == null ? "NO_DATA" : Number(x.tokens_per_s).toFixed(1) + " tokens/s") + " · wall " +
      (x.wall_ms == null ? "NO_DATA" : x.wall_ms + " ms") + " · load " + (x.load_ms == null ? "NO_DATA" : x.load_ms + " ms")));
    const missing = (Array.isArray(r.not_measured) ? r.not_measured : []).map((m) => clean(m.field, 24) + " (" + clean(m.cause, 60) + ")");
    if (missing.length) field(c, "Not measured", missing.join(", "));
    return c;
  }
  async function loadBench(listId, statusId, raw) {
    const list = document.getElementById(listId), status = document.getElementById(statusId);
    if (!list) return null;
    let d = raw;
    if (!d) { try { d = await request("/api/notebook"); } catch { d = null; } }
    const runs = d && Array.isArray(d.bench) ? d.bench.filter((r) => r && typeof r === "object") : [];
    list.replaceChildren();
    let summary;
    if (!d) summary = "NO_DATA: the benchmark reading did not answer (app server).";
    else if (!runs.length) summary = "NO_DATA: " + (clean(d.bench_cause, 72) || "no benchmark receipt read yet");
    else {
      runs.slice().reverse().forEach((r) => list.append(benchCard(r)));
      summary = runs.length + " run" + (runs.length === 1 ? "" : "s") + " from the Lab, fingerprints re-checked here. Read " +
        clean(d.bench_observed_at, 24).replace("T", " ").replace("Z", " UTC") + ". Each card says what was not measured.";
    }
    if (!runs.length) list.append(card("Benchmarks", "NO_DATA", summary));
    if (status && spoken[statusId] !== summary) { status.textContent = summary; spoken[statusId] = summary; }
    return runs;
  }
  async function loadTurns(listId, statusId, limit, thread) {
    const list = document.getElementById(listId), status = document.getElementById(statusId);
    if (!list) return null;
    let p = null;
    try { p = projectTurns(await request("/api/hexelion/turnos" + (thread === "cli" ? "?thread=cli" : ""))); } catch { p = null; }
    list.replaceChildren();
    let summary;
    if (!p) summary = "NO_DATA: the requests could not be read (the app server did not answer).";
    else if (!p.turns.length) summary = "NO_DATA: " + (p.cause || (thread === "cli" ? "no agent has asked Hexelion yet" : "no request in the shared thread yet"));
    else {
      p.turns.slice(0, limit).forEach(x => list.append(turnCard(x)));
      const last = p.turns[0];
      summary = "Last request: " + last.by + " asked " + last.to + ". " + last.sentence;
    }
    if (!p || !p.turns.length) list.append(card("Requests", "NO_DATA", summary));
    if (status && spoken[statusId] !== summary) { status.textContent = summary; spoken[statusId] = summary; }
    return p;
  }
  function mount() {
    const refresh = document.getElementById("notebook-refresh");
    if (refresh) refresh.addEventListener("click", () => load().catch(() => {}));
  }
  const api = Object.freeze({ load, projectNotebook, projectHarness, projectTurns, turnLine, achoClasses, projectTasks, taskSummary, loadTasks, loadTurns, loadBench });
  root.PreceptorNotebook = api;
  if (typeof module === "object" && module.exports) module.exports = api;
  if (typeof document !== "undefined") mount();
})(typeof window === "object" ? window : globalThis);
