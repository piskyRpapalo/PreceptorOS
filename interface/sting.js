(function (root) {
  "use strict";

  const semitonos = [0, 2, 4, 7, 9, 12, 14, 16];
  const contextos = new WeakMap();

  function noData(causa) {
    return { estado: "nodata", causa };
  }

  async function tocar(opciones = {}, host = root) {
    if (host.matchMedia && host.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return { estado: "inactivo", causa: "reduced motion" };
    }
    const Constructor = host.AudioContext || host.webkitAudioContext;
    if (typeof Constructor !== "function") return noData("Web Audio unavailable");

    try {
      let contexto = contextos.get(host);
      if (!contexto) {
        contexto = new Constructor();
        contextos.set(host, contexto);
      }
      if (contexto.state === "suspended") await contexto.resume();
      if (contexto.state !== "running") return noData("Web Audio context not running");

      const inicio = contexto.currentTime;
      const salida = contexto.createGain();
      salida.gain.setValueAtTime(0.0001, inicio);
      salida.gain.exponentialRampToValueAtTime(0.16, inicio + 0.035);
      salida.gain.exponentialRampToValueAtTime(0.0001, inicio + 0.57);
      salida.connect(contexto.destination);

      semitonos.forEach((semitono, indice) => {
        const t = inicio + indice * 0.07;
        const carrier = contexto.createOscillator();
        const modulador = contexto.createOscillator();
        const profundidad = contexto.createGain();
        const hz = 220 * (2 ** (semitono / 12));
        carrier.type = "sine";
        carrier.frequency.setValueAtTime(hz, t);
        modulador.type = "sine";
        modulador.frequency.setValueAtTime(hz * 2, t);
        profundidad.gain.setValueAtTime(hz * 0.32, t);
        modulador.connect(profundidad);
        profundidad.connect(carrier.frequency);
        carrier.connect(salida);
        carrier.start(t);
        modulador.start(t);
        carrier.stop(t + 0.068);
        modulador.stop(t + 0.068);
      });

      let suboctava = null;
      if (opciones.tension === true) {
        const grave = contexto.createOscillator();
        const volumen = contexto.createGain();
        grave.type = "sine";
        grave.frequency.setValueAtTime(110, inicio);
        volumen.gain.setValueAtTime(0.025, inicio);
        volumen.gain.exponentialRampToValueAtTime(0.0001, inicio + 0.57);
        grave.connect(volumen);
        volumen.connect(contexto.destination);
        grave.start(inicio);
        grave.stop(inicio + 0.56);
        suboctava = 110;
      }

      return {
        estado: "sonado",
        base_hz: 220,
        notas: semitonos.length,
        duracion_ms: 560,
        suboctava_hz: suboctava,
        causa_suboctava: suboctava === null ? "tension state not supplied" : null,
      };
    } catch (error) {
      return noData(`Web Audio failed: ${error && error.name ? error.name : "unknown cause"}`);
    }
  }

  root.PreceptorSting = { tocar };
  if (typeof module !== "undefined" && module.exports) module.exports = root.PreceptorSting;
})(typeof window !== "undefined" ? window : globalThis);
