/* Acho sound · the short tone a Hexelion turn may carry (autonomy parity).
 * Off until the person turns it on in Settings; the choice stays in this browser only. The tone never replaces the
 * words: Talk calls it only for a turn that has its sentence, which the status line has already said (aria-live).
 * The class and motif come from the server (turnos_hexelion + audio_feedback); this file only checks and plays them.
 * Anything malformed is NO_DATA with its cause and stays silent. No network, no clock of its own, no telemetry.
 */
(function (root) {
  "use strict";
  const KEY = "preceptoros.acho.sound";
  const classes = ["ok", "needs_you", "unanswered", "fence", "exec_fail", "empty", "bridge_down"];
  const contexts = new WeakMap();

  function store(host) { try { return host.localStorage || null; } catch (e) { return null; } }
  function enabled(host = root) {
    const s = store(host);
    try { return !!s && s.getItem(KEY) === "on"; } catch (e) { return false; }
  }
  function set(on, host = root) {
    const s = store(host);
    try { if (!s) return false; if (on) s.setItem(KEY, "on"); else s.removeItem(KEY); return true; } catch (e) { return false; }
  }
  function describe(host = root) {
    return enabled(host)
      ? "Turn sounds are on in this browser. Every tone follows words that are already on screen and read aloud by your screen reader."
      : "Turn sounds are off. The words are always on screen and for screen readers.";
  }
  const num = (v, lo, hi) => typeof v === "number" && Number.isFinite(v) && v >= lo && v <= hi;
  // check(acho) -> { ok: true, cls, motif } or { ok: false, cause }: the only shapes the player accepts.
  function check(acho) {
    if (!acho || typeof acho !== "object") return { ok: false, cause: "acho_missing" };
    if (!classes.includes(acho.class)) return { ok: false, cause: "acho_class_unknown" };
    const m = acho.motif;
    if (!m || typeof m !== "object" || !num(m.portadora, 100, 1000) || !num(m.moduladora, 50, 2000) ||
        !num(m.indice, 0, 400) || !num(m.dur, 0.05, 1) || typeof m.vibrato !== "boolean") {
      return { ok: false, cause: "acho_motif_invalid" };
    }
    return { ok: true, cls: acho.class, motif: m };
  }
  async function play(acho, host = root) {
    if (!enabled(host)) return { state: "off", cause: "sound is off until you turn it on" };
    const c = check(acho);
    if (!c.ok) return { state: "NO_DATA", cause: c.cause };
    const Ctor = host.AudioContext || host.webkitAudioContext;
    if (typeof Ctor !== "function") return { state: "NO_DATA", cause: "web_audio_unavailable" };
    try {
      let ctx = contexts.get(host);
      if (!ctx) { ctx = new Ctor(); contexts.set(host, ctx); }
      if (ctx.state === "suspended") await ctx.resume();
      if (ctx.state !== "running") return { state: "NO_DATA", cause: "web_audio_not_running" };
      const t = ctx.currentTime, m = c.motif;
      const out = ctx.createGain(), car = ctx.createOscillator(), mod = ctx.createOscillator(), depth = ctx.createGain();
      out.gain.setValueAtTime(0.0001, t);
      out.gain.exponentialRampToValueAtTime(0.12, t + 0.03);
      out.gain.exponentialRampToValueAtTime(0.0001, t + m.dur);
      car.type = "sine"; car.frequency.setValueAtTime(m.portadora, t);
      mod.type = "sine"; mod.frequency.setValueAtTime(m.moduladora, t);
      depth.gain.setValueAtTime(m.indice, t);
      mod.connect(depth); depth.connect(car.frequency); car.connect(out); out.connect(ctx.destination);
      let lfo = null;
      if (m.vibrato) {
        lfo = ctx.createOscillator(); const lfoDepth = ctx.createGain();
        lfo.frequency.setValueAtTime(5, t); lfoDepth.gain.setValueAtTime(m.portadora * 0.01, t);
        lfo.connect(lfoDepth); lfoDepth.connect(car.frequency); lfo.start(t); lfo.stop(t + m.dur);
      }
      car.start(t); mod.start(t); car.stop(t + m.dur); mod.stop(t + m.dur);
      return { state: "played", cls: c.cls };
    } catch (e) {
      return { state: "NO_DATA", cause: "web_audio_refused" };
    }
  }
  // Settings: one switch, its words, and a line that says what changed.
  function mount(host = root) {
    const doc = host.document;
    const box = doc && doc.getElementById("acho-sonido");
    const line = doc && doc.getElementById("acho-sonido-estado");
    if (!box || !line) return;
    box.checked = enabled(host);
    line.textContent = describe(host);
    box.addEventListener("change", () => {
      const kept = set(box.checked, host);
      box.checked = enabled(host);
      line.textContent = kept ? describe(host) : "NO_DATA: this browser does not keep settings, so turn sounds stay off.";
    });
  }
  const api = Object.freeze({ KEY, classes, enabled, set, describe, check, play, mount });
  root.PreceptorAchoSonido = api;
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root.document) mount(root);
})(typeof window === "object" ? window : globalThis);
