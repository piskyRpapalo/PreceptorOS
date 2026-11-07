/* Keep this app on this device (joya 2, Mesa 2026-11-07): ask the browser for persistent storage, so it
   does not sweep the installed face. Only on a trusted click (nothing leaves or asks without a gesture);
   the verdict is the browser's own answer, shown as it came, or NO_DATA with its cause. */
"use strict";
(function (root) {
  async function keep(nav) {
    const storage = nav && nav.storage;
    if (!storage || typeof storage.persist !== "function" || typeof storage.persisted !== "function") {
      return Object.freeze({ estado: "NO_DATA", causa: "storage_persist_unsupported" });
    }
    try {
      if (await storage.persisted() === true) return Object.freeze({ estado: "kept", ya: true });
      const granted = await storage.persist();
      const now = await storage.persisted();
      if (granted === true && now === true) return Object.freeze({ estado: "kept", ya: false });
      return Object.freeze({ estado: "not_kept", causa: "browser_declined" });
    } catch (_) {
      return Object.freeze({ estado: "NO_DATA", causa: "storage_persist_failed" });
    }
  }
  const lines = Object.freeze({
    kept: "Kept: the browser will not clear this app's storage on its own.",
    not_kept: "Not kept: the browser declined. It may clear this app's storage under pressure.",
  });
  function line(result) {
    return result.estado === "NO_DATA" ? "NO_DATA: " + result.causa : lines[result.estado];
  }
  function mount(doc, nav) {
    const button = doc.getElementById("keep-device");
    const status = doc.getElementById("keep-device-status");
    if (!button || !status) return null;
    let running = false;
    button.addEventListener("click", async (event) => {
      if (running || (event && event.isTrusted === false)) return;
      running = true; button.disabled = true;
      status.textContent = line(await keep(nav));
      running = false; button.disabled = false;
    });
    return Object.freeze({ keep: () => keep(nav) });
  }
  const api = Object.freeze({ keep, line, mount });
  if (typeof module === "object" && module.exports) module.exports = api;
  else { root.PreceptorKeepDevice = api; mount(root.document, root.navigator); }
})(typeof window === "object" ? window : globalThis);
