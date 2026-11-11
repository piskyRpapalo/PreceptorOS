/* Energy reader for the local app: one user click, one no-store sensor snapshot.
 * No polling, cloud request, relay control, or inferred battery charge.
 * The spoken and machine views use the same JSON response.
 */
(() => {
  "use strict";
  const button = document.getElementById("energy-read");
  const spoken = document.getElementById("energy-status");
  const machine = document.getElementById("energy-json");
  if (!button || !spoken || !machine) return;

  button.addEventListener("click", async () => {
    button.disabled = true;
    spoken.textContent = "Consultando el medidor local…";
    machine.textContent = "";
    const abort = new AbortController();
    const timeout = setTimeout(() => abort.abort(), 4000);
    try {
      const response = await fetch("/api/energia", {
        method: "GET", cache: "no-store", signal: abort.signal,
      });
      const data = await response.json();
      if (!response.ok || !data || data.esquema !== "preceptoros.energy-read/1" ||
          typeof data.texto !== "string" || data.solo_lectura !== true) {
        throw new Error("energy_snapshot_invalid");
      }
      spoken.textContent = data.texto;
      machine.textContent = JSON.stringify(data, null, 2);
    } catch {
      spoken.textContent = "Energía: NO_DATA (local_energy_endpoint_unavailable).";
    } finally {
      clearTimeout(timeout);
      button.disabled = false;
    }
  });
})();
