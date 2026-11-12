/* One conversation, many preceptors (app router piece 01).
 * Talk shows the shared `orquesta` thread, the same one the rack CLI agents and Hexelion write to. Every message
 * says who wrote it and which kind of voice it is (you, private, rack CLI, sensor, external, unknown voice); a message
 * addressed to someone says to whom. Bubbles this window drew while waiting are marked `local` and are replaced by
 * the thread's own copy once the thread is read: the thread is the source, the bubble was only a draft of it.
 * Read-only except send(), which posts the person's addressed message; a message is never authority.
 */
(function (root) {
  "use strict";
  const doc = root.document;
  const kinds = { person: "person", private: "private", "rack-cli": "rack CLI", sensor: "sensor (not a model)",
    external: "external", unknown: "unknown voice" };
  let seen = 0, routes = {}, names = {}, busy = false, timer = null;

  function chip(m) {
    const span = doc.createElement("span");
    span.className = "quien quien-" + (kinds[m.kind] ? m.kind : "unknown");
    span.textContent = m.name + " · " + (kinds[m.kind] || kinds.unknown) + (m.to ? " → " + (names[m.to] || m.to) : "");
    return span;
  }

  function row(m) {
    const li = doc.createElement("li");
    li.dataset.n = String(m.n);
    li.className = "hilo-msg" + (m.kind === "person" ? " mio" : "");
    li.appendChild(chip(m));
    const words = doc.createElement("span");
    words.className = "hilo-texto";
    words.textContent = m.text + (m.cut ? " …" : "");
    li.appendChild(words);
    const foot = [m.t.replace("T", " ").replace("Z", " UTC"), m.seal];
    if (m.model) foot.push(m.model);
    const meta = doc.createElement("span");
    meta.className = "hilo-meta";
    meta.textContent = foot.join(" · ");
    li.appendChild(meta);
    (Array.isArray(m.sources) ? m.sources : []).forEach((s) => {
      const src = doc.createElement("span");
      src.className = "hilo-fuente";
      src.textContent = "source " + s;
      li.appendChild(src);
    });
    return li;
  }

  function paintDestinations(list) {
    const out = doc.getElementById("conv-destinos");
    if (!out || !Array.isArray(list)) return;
    const tags = (f) => list.filter(f).map((d) => "@" + d.id).join(" ");
    out.textContent = "Answers here: " + tags((d) => d.route === "station") +
      " · Reads the thread: " + tags((d) => d.route === "thread") +
      " · NO_DATA, no transport: " + tags((d) => !d.addressable);
    out.title = list.map((d) => "@" + d.id + ": " + d.transport).join("\n");
  }

  // sync({ replaceLocal }) -> the projection, or null. New messages after `seen` are appended in order.
  async function sync(opts) {
    if (busy) return null;
    busy = true;
    const list = doc.getElementById("hilo"), status = doc.getElementById("conv-destinos");
    try {
      const r = await fetch("/api/conversacion?desde=" + seen, { cache: "no-store" });
      const d = await r.json();
      if (!r.ok || !d || d.schema !== "preceptoros.multipreceptor/1") throw new Error("shape");
      routes = {}; names = {};
      (d.destinations || []).forEach((x) => { routes[x.id] = x.route; names[x.id] = x.name; });
      paintDestinations(d.destinations);
      if (d.state !== "MEASURED") {
        if (status) status.textContent = "NO_DATA: " + (d.cause || "the shared thread could not be read");
        return d;
      }
      if (opts && opts.replaceLocal) list.querySelectorAll("li.local").forEach((li) => li.remove());
      const fresh = (d.messages || []).filter((m) => Number.isSafeInteger(m.n) && m.n > seen &&
        !list.querySelector('li[data-n="' + m.n + '"]'));
      if (fresh.length) {
        list.setAttribute("aria-busy", "true");
        if (seen === 0 && d.hidden > 0) {
          const li = doc.createElement("li");
          li.className = "hilo-meta";
          li.textContent = d.hidden + " earlier messages are in the thread and not shown here.";
          list.appendChild(li);
        }
        fresh.forEach((m) => list.appendChild(row(m)));
        list.removeAttribute("aria-busy");
        list.lastElementChild.scrollIntoView({ block: "end" });
      }
      seen = Math.max(seen, d.last || 0);
      return d;
    } catch {
      if (status) status.textContent = "NO_DATA: the shared thread did not answer; your words stay in this window only.";
      return null;
    } finally {
      busy = false;
    }
  }

  // send(para, texto) -> { ok, cause, n }. The server stores it in the thread with `para`; no reply is promised.
  async function send(para, texto) {
    try {
      const r = await fetch("/api/conversacion", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ para, texto }) });
      const d = await r.json();
      return r.ok && d.state === "DELIVERED_TO_THREAD" ? { ok: true, n: d.n } : { ok: false, cause: d.cause || "NO_DATA" };
    } catch {
      return { ok: false, cause: "conversation_transport_unavailable" };
    }
  }

  function watch(panel) {
    if (timer) return;
    timer = root.setInterval(() => {
      if (!doc.hidden && panel && !panel.hidden) sync();
    }, 20000);
  }

  root.PreceptorConversacion = Object.freeze({ sync, send, watch, routes: () => Object.assign({}, routes),
    name: (id) => names[id] || id });
})(window);
