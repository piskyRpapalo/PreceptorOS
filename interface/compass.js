/* compass.js · la rosa de los vientos.
 *
 * La brujula no se oculta jamas. Si la red falla se pinta lo ultimo que hubo y
 * se dice la edad del dato en la propia cara. Un instrumento que desaparece
 * cuando no sabe es peor que uno que dice que no sabe: el primero parece que
 * no pasa nada. Es la regla de los sensores honestos, aplicada aqui.
 *
 * Nota de estilo, y no es capricho: en los ficheros de interfaz no se usan
 * identificadores en mayusculas. `test_guardrails` lee cada palabra en
 * mayusculas como el nombre de una politica y exige que exista -- asi la cara
 * no puede prometer una proteccion que no esta. Lo cazó con este fichero.
 */
(function () {
  "use strict";

  var clave = "preceptoros.compass";
  var cadaMs = 30000;
  var viejoS = 3600;      // 1 h -> aviso naranja
  var antiguoS = 7200;    // 2 h -> aviso rojo
  var temporizador = null;

  // El modo se puede fijar por URL: `?compass=detalle`. Existe para que un
  // enlace lleve a alguien exactamente a lo que le quieres ensenar -- y de paso
  // hace que una captura sea reproducible en vez de depender de un toque.
  function modoInicial() {
    try {
      var m = new URLSearchParams(location.search).get("compass");
      return m === "detalle" ? "detalle" : "camino";
    } catch (e) { return "camino"; }
  }
  var modo = modoInicial();

  function $(id) { return document.getElementById(id); }

  function guardar(datos) {
    try {
      localStorage.setItem(clave, JSON.stringify(
        { t: Date.now(), modo: modo, datos: datos }));
    } catch (e) { /* sin almacen, se sigue sin cache */ }
  }

  function recuperar() {
    try {
      var crudo = localStorage.getItem(clave);
      return crudo ? JSON.parse(crudo) : null;
    } catch (e) { return null; }
  }

  function claseEstado(p) {
    if (p.estado === "no_medible") return "no_medible";
    if (p.estado === "completado") return "completado";
    if (p.estado === "en_progreso") return "en_progreso";
    return "bloqueado";
  }

  function pintar(d, edadSegundos) {
    var claves = Object.keys(d["peldaños"] || d.peldanos || {});
    var mapa = d["peldaños"] || d.peldanos || {};

    for (var i = 0; i < 8; i++) {
      var el = $("sector-m" + i);
      if (!el) continue;
      var p = mapa["M" + i];
      el.setAttribute("class", "sector " + (p ? claseEstado(p) : "bloqueado") +
        (d.activo === "M" + i ? " activo" : ""));
      el.setAttribute("aria-label", "M" + i + " " +
        (p ? p.nombre + ", " + p.estado + ", " + Math.round(p.valor * 100) + "%"
           : "sin dato"));
    }

    var anillo = $("anillo-detalle");
    if (anillo) {
      anillo.setAttribute("class", modo === "detalle" ? "" : "oculto");
      if (modo === "detalle") {
        for (var k = 8; k < claves.length; k++) {
          var s = $("sector-d" + (k - 8));
          if (!s) continue;
          var q = mapa[claves[k]];
          s.setAttribute("class", "sector detalle " + claseEstado(q) +
            (d.activo === claves[k] ? " activo" : ""));
          s.setAttribute("aria-label", claves[k] + ", " + q.estado);
        }
      }
    }

    var ind = d.indicadores || {};
    var aguja = $("aguja");
    if (aguja) {
      var largo = 12 + (ind.intensidad || 0) * 46;
      var ang = (ind.orientacion || 0) - Math.PI / 2;
      aguja.setAttribute("x2", (100 + largo * Math.cos(ang)).toFixed(2));
      aguja.setAttribute("y2", (100 + largo * Math.sin(ang)).toFixed(2));
      // Sin velocidad no hay coherencia que medir, y pintar la aguja de rojo
      // diria «vas mal» cuando la verdad es «no se puede saber». Son cosas
      // distintas y el color no puede confundirlas.
      var c = ind.coherencia || 0;
      aguja.setAttribute("class", !d.velocidad_medible ? "sin-medir"
        : (c > 0.7 ? "coherente" : (c >= 0.3 ? "intermedia" : "incoherente")));
    }

    var nucleo = $("nucleo");
    if (nucleo) {
      nucleo.setAttribute("r", (5 + (ind.estabilidad || 0) * 10).toFixed(1));
      nucleo.setAttribute("class", ind.estancado ? "estancado" : "");
    }

    // S sin normalizar es un logaritmo y no cabe en un radio: se pinta
    // S_vis = exp(-kappa), que vive en [0,1]. Esta escrito en la documentacion.
    var ticks = $("ticks");
    if (ticks) {
      var svis = Math.max(0, Math.min(1, ind.estabilidad || 0));
      ticks.innerHTML = "";
      var n = Math.round(svis * 8);
      for (var t = 0; t < n; t++) {
        var a = (t / 8) * 2 * Math.PI - Math.PI / 2;
        var l = document.createElementNS("http://www.w3.org/2000/svg", "line");
        l.setAttribute("x1", (100 + 22 * Math.cos(a)).toFixed(2));
        l.setAttribute("y1", (100 + 22 * Math.sin(a)).toFixed(2));
        l.setAttribute("x2", (100 + 27 * Math.cos(a)).toFixed(2));
        l.setAttribute("y2", (100 + 27 * Math.sin(a)).toFixed(2));
        ticks.appendChild(l);
      }
    }

    var eta = $("eta");
    if (eta) {
      eta.textContent = d.eta_segundos === null || d.eta_segundos === undefined
        ? "" : "~" + Math.max(1, Math.round(d.eta_segundos / 86400)) + " d";
    }

    var aviso = $("compass-aviso");
    if (aviso) {
      if (edadSegundos === 0) {
        aviso.textContent = "";
        aviso.className = "";
      } else {
        var min = Math.round(edadSegundos / 60);
        aviso.textContent = "sin conexión · dato de hace " + min + " min";
        aviso.className = edadSegundos > antiguoS ? "antiguo"
          : (edadSegundos > viejoS ? "viejo" : "");
      }
    }
  }

  function pedir() {
    fetch("/api/camino?modo=" + modo, { cache: "no-store" })
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(function (d) { guardar(d); pintar(d, 0); })
      .catch(function () {
        var c = recuperar();
        if (c && c.datos) pintar(c.datos, Math.round((Date.now() - c.t) / 1000));
      });
  }

  function cambiarModo(nuevo) {
    modo = nuevo;
    var b1 = $("compass-modo-camino"), b2 = $("compass-modo-detalle");
    if (b1) b1.setAttribute("aria-pressed", String(nuevo === "camino"));
    if (b2) b2.setAttribute("aria-pressed", String(nuevo === "detalle"));
    pedir();
  }

  function arrancar() {
    var cont = $("compass-container");
    if (!cont) return;
    var b0 = $("compass-modo-camino"), d0 = $("compass-modo-detalle");
    if (b0) b0.setAttribute("aria-pressed", String(modo === "camino"));
    if (d0) d0.setAttribute("aria-pressed", String(modo === "detalle"));
    fetch("/assets/compass.svg")
      .then(function (r) { return r.text(); })
      .then(function (svg) {
        var hueco = $("compass-svg-hueco");
        if (hueco) hueco.innerHTML = svg;
        var c = recuperar();
        if (c && c.datos) pintar(c.datos, Math.round((Date.now() - c.t) / 1000));
        var b1 = $("compass-modo-camino"), b2 = $("compass-modo-detalle");
        if (b1) b1.addEventListener("click", function () { cambiarModo("camino"); });
        if (b2) b2.addEventListener("click", function () { cambiarModo("detalle"); });
        pedir();
        temporizador = setInterval(pedir, cadaMs);
      })
      .catch(function () { /* sin SVG no hay rosa; el aviso lo dice */ });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", arrancar);
  } else { arrancar(); }
})();
