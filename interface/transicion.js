/* Proyección determinista de la reorganización de una sola pestaña.
 * La zona la elige el controlador de la app; este módulo solo dibuja.
 */
(function (root) {
  "use strict";

  const vuelta = Math.PI * 2;
  const maxTau = 1_000_000;

  function faseDesenvuelta(desde, hacia) {
    if (!Number.isFinite(desde) || !Number.isFinite(hacia)) {
      throw new TypeError("fase no finita");
    }
    const delta = ((hacia - desde + Math.PI) % vuelta + vuelta) % vuelta - Math.PI;
    return desde + delta;
  }

  function validarVector(vector) {
    if (!Array.isArray(vector)) throw new TypeError("vector armónico inválido");
    let anterior = 0;
    for (const termino of vector) {
      if (!termino || !Number.isSafeInteger(termino.k) || termino.k <= anterior ||
          !Number.isFinite(termino.ax) || !Number.isFinite(termino.ay) ||
          !Number.isFinite(termino.phi)) {
        throw new TypeError("término armónico inválido");
      }
      anterior = termino.k;
    }
  }

  function interpolar(a, b, tau, opciones = {}) {
    validarVector(a);
    validarVector(b);
    if (!Number.isFinite(tau) || tau < 0 || tau > 1) throw new RangeError("tau fuera de [0,1]");
    if (a.length !== b.length || a.some((x, i) => x.k !== b[i].k)) {
      throw new TypeError("vectores armónicos incompatibles");
    }
    const signo = opciones.espejo === true ? -1 : 1;
    return a.map((x, i) => {
      const y = b[i];
      const phiB = faseDesenvuelta(x.phi, y.phi);
      return {
        k: x.k,
        ax: signo * (x.ax + (y.ax - x.ax) * tau),
        ay: x.ay + (y.ay - x.ay) * tau,
        phi: x.phi + (phiB - x.phi) * tau,
      };
    });
  }

  function bytes(vector) {
    validarVector(vector);
    return JSON.stringify(vector);
  }

  function vectorDesdePestana(elemento, ancho, alto) {
    const r = elemento.getBoundingClientRect();
    const x = ((r.left + r.width / 2) / ancho) - 0.5;
    const y = ((r.top + r.height / 2) / alto) - 0.5;
    const radio = Math.min(0.25, Math.hypot(x, y));
    return [{ k: 1, ax: radio, ay: y, phi: radio === 0 ? 0 : Math.atan2(y, x) }];
  }

  function angulo(vector, x, y, tau) {
    return vector.reduce((total, h) =>
      total + h.ax * Math.sin(h.k * x + h.ay * y + h.k * tau + h.phi), 0);
  }

  function pintar(origen, destino, opciones = {}) {
    if (!origen || !destino || origen === destino) return () => {};
    const doc = destino.ownerDocument;
    const win = doc.defaultView;
    const reducido = opciones.reducido === true ||
      !!(win.matchMedia && win.matchMedia("(prefers-reduced-motion: reduce)").matches);
    if (reducido) return () => {};

    const ancho = win.innerWidth || 1;
    const alto = win.innerHeight || 1;
    const a = origen.getBoundingClientRect();
    const b = destino.getBoundingClientRect();
    const A = [a.left + a.width / 2, a.top + a.height / 2];
    const B = [b.left + b.width / 2, b.top + b.height / 2];
    const inicio = vectorDesdePestana(origen, ancho, alto);
    const fin = vectorDesdePestana(destino, ancho, alto);
    const espejo = opciones.espejo === true;
    const canvas = doc.createElement("canvas");
    canvas.className = "gusano-transicion";
    canvas.setAttribute("aria-hidden", "true");
    canvas.setAttribute("role", "presentation");
    canvas.width = Math.round(ancho * Math.min(2, win.devicePixelRatio || 1));
    canvas.height = Math.round(alto * Math.min(2, win.devicePixelRatio || 1));
    doc.body.appendChild(canvas);
    const ctx = canvas.getContext("2d");
    if (!ctx) { canvas.remove(); return () => {}; }
    const dpr = Math.min(2, win.devicePixelRatio || 1);
    const distancia = Math.hypot(B[0] - A[0], B[1] - A[1]);
    const desvio = Math.min(56, distancia * 0.12);
    const dx = B[0] - A[0], dy = B[1] - A[1];
    const normal = Math.hypot(dx, dy) || 1;
    const duracion = opciones.duracion || 420;
    const segmentos = 7;
    let raf = null, t0 = null, cancelado = false;

    function cuadro(ts) {
      if (cancelado) return;
      if (t0 === null) t0 = ts;
      const tau = Math.max(0, Math.min(1, (ts - t0) / duracion));
      const estadoTau = Math.round(tau * maxTau);
      if (typeof opciones.onTau === "function") opciones.onTau(estadoTau);
      const terminos = interpolar(inicio, fin, tau, { espejo });
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (let s = 0; s < segmentos; s++) {
        const u = Math.max(0, tau - s * 0.045);
        const x = A[0] + dx * u, y = A[1] + dy * u;
        const ang = angulo(terminos, u * vuelta, y / alto, tau);
        const desplazamiento = Math.sin(ang) * desvio;
        const px = (x - (dy / normal) * desplazamiento) * dpr;
        const py = (y + (dx / normal) * desplazamiento) * dpr;
        ctx.beginPath();
        ctx.arc(px, py, (5.5 - s * 0.45) * dpr, 0, vuelta);
        ctx.fillStyle = win.getComputedStyle(destino).color;
        ctx.globalAlpha = 1 - s / (segmentos + 1);
        ctx.fill();
      }
      ctx.globalAlpha = 1;
      if (tau < 1) raf = win.requestAnimationFrame(cuadro);
      else { canvas.remove(); if (typeof opciones.onTau === "function") opciones.onTau(maxTau); }
    }
    raf = win.requestAnimationFrame(cuadro);
    return function cancelar() {
      cancelado = true;
      if (raf !== null) win.cancelAnimationFrame(raf);
      canvas.remove();
    };
  }

  const API = Object.freeze({ faseDesenvuelta, interpolar, bytes, pintar });
  if (typeof module === "object" && module.exports) module.exports = API;
  else root.PreceptorTransicion = API;
})(typeof window === "object" ? window : globalThis);
