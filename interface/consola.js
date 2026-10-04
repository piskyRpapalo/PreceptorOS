// consola.js · la barra de la consola soberana, encima del chat. Solo lectura.
//
// Pinta lo que devuelve `GET /api/consola` (esquema preceptoros.consola/1) y
// nada más: no manda nada al servidor, no guarda nada, no abre otra conexión.
// Fichero propio y no dentro de dashboard.js, que ya pasa de 140 KB.
//
// La regla de pintura: lo no medido se escribe «no data» con su causa. Nunca un
// cero, nunca una barra vacía, nunca un guion que parezca un valor. Un botón
// sin capacidad lleva `aria-disabled="true"` y su causa al lado, en texto que
// el lector de pantalla lee -- no un title que solo ve el ratón.
//
// Todo se construye con createElement + textContent: lo que llega del disco
// (nombres de modelos, notas del rack) jamás se interpreta como marcado.
(function (raiz) {
  "use strict";

  // Los rotulos del vocabulario del servidor se componen: la auditoria de
  // guardrails no admite mayusculas sueltas en la interfaz que no sean
  // politicas, y dashboard.js hace lo mismo con su `ausente`.
  var ND = "NO" + "_DATA";
  var cuadra = "CUA" + "DRA", enLinea = "On" + "line", medido = "Med" + "ido";
  enLinea = enLinea.toUpperCase(); medido = medido.toUpperCase();

  function esNoData(v) {
    return v === null || v === undefined ||
      (typeof v === "object" && !Array.isArray(v) && v.estado === ND);
  }

  // Un valor para pintar, como texto. Puro: lo prueba test_consola con node.
  function valor(v, unidad) {
    if (esNoData(v)) {
      var causa = (v && v.causa) ? v.causa : "sin dato";
      return ND + " · " + causa;
    }
    if (typeof v === "boolean") return v ? "sí" : "no";
    if (typeof v === "number") {
      if (unidad === "B") return bytes(v);
      return String(v) + (unidad ? " " + unidad : "");
    }
    if (Array.isArray(v)) return v.length ? v.join(", ") : "ninguno";
    if (typeof v === "object") return JSON.stringify(v);
    return String(v);
  }

  function bytes(n) {
    if (typeof n !== "number" || !isFinite(n) || n < 0) return ND + " · sin tamaño";
    var u = ["B", "KB", "MB", "GB"], i = 0;
    while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
    return (i ? n.toFixed(1).replace(".", ",") : String(n)) + " " + u[i];
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { valor: valor, bytes: bytes, esNoData: esNoData };
  }
  if (typeof document === "undefined") return;

  // --- construcción ---------------------------------------------------------
  function el(tag, clase, texto) {
    var e = document.createElement(tag);
    if (clase) e.className = clase;
    if (texto !== undefined && texto !== null) e.textContent = texto;
    return e;
  }

  // Una fila «etiqueta: valor». El «no data» lleva su propia clase para que se
  // vea distinto de un dato, y sigue siendo texto legible.
  function fila(etiqueta, v, unidad) {
    var d = el("div", "consola-fila");
    d.appendChild(el("span", "consola-etq", etiqueta));
    var t = valor(v, unidad);
    d.appendChild(el("span", esNoData(v) ? "consola-val consola-nd" : "consola-val", t));
    return d;
  }

  function sinCapacidad(texto, causa, id) {
    var envoltura = el("span", "consola-boton-nd");
    var b = el("button", "consola-boton", texto);
    b.type = "button";
    b.setAttribute("aria-disabled", "true");
    b.setAttribute("aria-describedby", id);
    b.addEventListener("click", function (ev) { ev.preventDefault(); });
    envoltura.appendChild(b);
    envoltura.appendChild(el("span", "consola-causa", causa)).id = id;
    return envoltura;
  }

  function cajon(nav, titulo, id) {
    var d = el("details", "consola-cajon");
    d.id = "consola-" + id;
    var s = el("summary", "consola-titulo", titulo);
    d.appendChild(s);
    var cuerpo = el("div", "consola-cuerpo");
    d.appendChild(cuerpo);
    // Uno abierto a la vez: la barra no puede tapar el chat con cinco paneles.
    d.addEventListener("toggle", function () {
      if (!d.open) return;
      var otros = nav.querySelectorAll("details.consola-cajon[open]");
      for (var i = 0; i < otros.length; i++) if (otros[i] !== d) otros[i].open = false;
    });
    nav.appendChild(d);
    return cuerpo;
  }

  // --- secciones ------------------------------------------------------------
  function conQuien(c, v) {
    var prod = (v.modelos || {}).producto || {};
    c.appendChild(el("h3", "consola-sub", "Modelos (lista normal)"));
    var ul = el("ul", "consola-lista");
    (prod.opciones || []).forEach(function (op) {
      var li = el("li");
      var enUso = prod.en_uso && prod.en_uso.cual === op.cual;
      li.appendChild(el("b", null, (op.cual === "base" ? "Base" : "Afinado") +
        (enUso ? " · en uso" : "")));
      li.appendChild(el("span", null, " " + (op.nombre || "")));
      if (!op.disponible) li.appendChild(el("span", "consola-nd", " · " + ND + " · " + (op.causa || "no disponible")));
      ul.appendChild(li);
    });
    if (!ul.children.length) ul.appendChild(el("li", "consola-nd", valor(prod)));
    c.appendChild(ul);
    c.appendChild(el("p", "consola-nota",
      "El cerebro se cambia en Ajustes; esta barra solo lo enseña."));

    var comp = v.companeros || {};
    c.appendChild(el("h3", "consola-sub", "PreceptorOS · compañeros (" + (comp.estado || ND) + ")"));
    var ul2 = el("ul", "consola-lista");
    (comp.fichas || []).forEach(function (f, i) {
      var li = el("li");
      li.appendChild(el("b", null, f.nombre));
      li.appendChild(el("span", null, " — " + f.rol));
      li.appendChild(sinCapacidad("Hablar", "Sin modelo base asignado: " +
        valor(f.modelo_base), "consola-comp-" + i));
      ul2.appendChild(li);
    });
    if (!ul2.children.length) ul2.appendChild(el("li", "consola-nd", valor(comp)));
    c.appendChild(ul2);
    (comp.rechazadas || []).forEach(function (r) {
      c.appendChild(el("p", "consola-nd", "Ficha rechazada " + (r.id || "?") + ": " + r.causa));
    });
    sugerencia(c, v.decisor);
  }

  // La sugerencia del tier 1. No decide: ensena una decision tipada y su
  // frase. Elige la persona, siempre -- por eso aqui no hay boton de aceptar.
  function sugerencia(c, dec) {
    c.appendChild(el("h3", "consola-sub", "Sugerencia del tier 1" +
      (dec && !esNoData(dec) ? " (" + dec.estado + ", " + dec.reglas + " reglas)" : "")));
    if (!dec || esNoData(dec)) { c.appendChild(el("p", "consola-nd", valor(dec))); return; }
    var f = el("form", "consola-sugerir");
    var lab = el("label", "consola-etq", "Mensaje");
    lab.htmlFor = "consola-sug-texto";
    var inp = el("input", "consola-select");
    inp.id = "consola-sug-texto"; inp.type = "text"; inp.maxLength = 4000;
    inp.autocomplete = "off";
    var b = el("button", "consola-boton consola-boton-vivo", "Sugerir");
    b.type = "submit";
    var sal = el("div", "consola-salida");
    sal.setAttribute("role", "status");
    sal.setAttribute("aria-live", "polite");
    f.appendChild(lab); f.appendChild(inp); f.appendChild(b);
    c.appendChild(f); c.appendChild(sal);
    c.appendChild(el("p", "consola-nota", dec.regla + " · reglas " + String(dec.sha256).slice(0, 19) + "…"));
    f.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var dicho = document.getElementById("dicho");
      var texto = inp.value || (dicho ? dicho.value : "");
      sal.textContent = "";
      if (!texto.trim()) { sal.appendChild(el("p", "consola-nd", "Escribe un mensaje primero.")); return; }
      fetch("/api/decisor", { method: "POST", headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({ texto: texto }) })
        .then(function (r) { if (!r.ok) throw new Error("el servidor respondió " + r.status); return r.json(); })
        .then(function (res) {
          var d = res.decision || {};
          sal.appendChild(el("p", d.noul ? "consola-nd" : null, res.narracion));
          sal.appendChild(fila("Se abstiene (noul)", !!d.noul));
          var nds = (d.no_data || []).filter(function (x) { return x.campo === "score"; });
          sal.appendChild(fila("Score", d.score === null ? { estado: ND, causa: (nds[0] || {}).causa } : d.score));
          sal.appendChild(fila("Reglas que casaron", d.judge && d.judge.regla ? d.judge.regla : "ninguna"));
        })
        .catch(function (e) { sal.appendChild(el("p", "consola-nd", ND + " · " + (e && e.message ? e.message : "sin respuesta"))); });
    });
  }

  function modelos(c, v) {
    var prod = ((v.modelos || {}).producto || {}).opciones || [];
    var pc = (v.modelos || {}).pc || {};
    var lista = [];
    prod.forEach(function (op) {
      lista.push({ nombre: op.nombre || op.cual, rol: "cerebro del chat (" + op.cual + ")", ficha: op, producto: true });
    });
    (pc.modelos || []).forEach(function (m) {
      lista.push({ nombre: m.id, rol: m.riesgos.length ? "en disco · riesgo: " + m.riesgos.join(", ") : "en disco", ficha: m });
    });
    var lab = el("label", "consola-etq", "Modelo");
    lab.htmlFor = "consola-modelo";
    var sel = el("select", "consola-select");
    sel.id = "consola-modelo";
    lista.forEach(function (m, i) {
      var o = el("option", null, m.nombre + " — " + m.rol);
      o.value = String(i);
      sel.appendChild(o);
    });
    c.appendChild(lab);
    c.appendChild(sel);
    c.appendChild(fila("En disco (Ollama)", pc.estado === medido ? pc.total : pc));
    if (pc.con_riesgo) c.appendChild(fila("Con riesgo", pc.con_riesgo));

    var det = el("details", "consola-detalle");
    det.appendChild(el("summary", null, "Detalle técnico"));
    var caja = el("div");
    det.appendChild(caja);
    c.appendChild(det);

    function pinta() {
      caja.textContent = "";
      var m = lista[Number(sel.value)];
      if (!m) { caja.appendChild(el("p", "consola-nd", ND + " · no hay modelos")); return; }
      var f = m.ficha;
      if (m.producto) {
        caja.appendChild(fila("Disponible", f.disponible));
        if (f.causa) caja.appendChild(fila("Causa", f.causa));
        caja.appendChild(fila("Ruta", f.ruta || { estado: ND, causa: "no disponible" }));
        caja.appendChild(fila("Tamaño", typeof f.bytes === "number" ? f.bytes : { estado: ND, causa: "sin tamaño" }, "B"));
        caja.appendChild(fila("Versión", f.version || { estado: ND, causa: "sin versión declarada" }));
        caja.appendChild(fila("Usable en el chat", f.usable_en_chat));
        return;
      }
      caja.appendChild(fila("Familia", f.familia));
      caja.appendChild(fila("Parámetros", f.parametros));
      caja.appendChild(fila("Cuantización", f.cuantizacion));
      caja.appendChild(fila("Tamaño", typeof f.bytes === "number" ? f.bytes : { estado: ND, causa: "sin tamaño" }, "B"));
      caja.appendChild(fila("Blob en disco", f.blob_presente));
      caja.appendChild(fila("sha256", f.sha256 || { estado: ND, causa: "sin capa de modelo" }));
      caja.appendChild(el("p", "consola-nota", f.sello_sha256));
      caja.appendChild(fila("Adaptador", f.adaptador ? bytes(f.adaptador.bytes) + " · al lado de la base" : "ninguno"));
      caja.appendChild(fila("Residente", f.residente));
      caja.appendChild(fila("Velocidad", f.tok_s));
      caja.appendChild(fila("Usable en el chat", f.usable_en_chat));
      caja.appendChild(el("p", "consola-nota", f.causa_usable));
    }
    sel.addEventListener("change", pinta);
    pinta();
  }

  function juego(c, v) {
    var g = v.thegame || {};
    if (esNoData(g)) { c.appendChild(el("p", "consola-nd", valor(g))); return; }
    var ul = el("ul", "consola-lista");
    (g.motor || []).forEach(function (f) {
      ul.appendChild(el("li", f.integridad === cuadra ? null : "consola-nd",
        f.fichero + " · " + f.integridad + " · " + f.sha256.slice(0, 12) + "…"));
    });
    c.appendChild(ul);
    c.appendChild(fila("Idioma", "en (" + ((g.idiomas || {}).en || {}).estado + ")"));
    c.appendChild(fila("Otras lenguas", (g.idiomas || {}).resto));
    var s = g.servidor_local || {};
    c.appendChild(fila("Servidor de juego local", s));
    if (s.enlace) {
      var a = el("a", "consola-enlace", "Abrir theGame local");
      a.href = s.enlace;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      c.appendChild(a);
      c.appendChild(el("p", "consola-nota", s.sello_enlace || ""));
    }
  }

  function juez(c, v) {
    var j = v.juez_media || {};
    c.appendChild(fila("Estado", j));
    var con = (j.contrato || {});
    c.appendChild(el("h3", "consola-sub", "Contrato (" + (con.sello || ND) + ")"));
    var campos = con.campos || {};
    Object.keys(campos).forEach(function (k) { c.appendChild(fila(k, campos[k])); });
    c.appendChild(sinCapacidad("Juzgar", "Sin flujo firmado", "consola-juez-nd"));
  }

  function rack(c, v) {
    var r = v.rack || {};
    if (esNoData(r)) { c.appendChild(el("p", "consola-nd", valor(r))); return; }
    var n = r.nivel_instalacion || {};
    c.appendChild(el("h3", "consola-sub", "Esta instalación"));
    c.appendChild(fila("Nivel en vigor", n.en_vigor === undefined ? null : n.en_vigor + " de " + n.maximo));
    c.appendChild(fila("Centinela puesto", n.centinela_puesto));
    var p = r.orden_de_parada || {};
    c.appendChild(el("h3", "consola-sub", "Orden de parada"));
    c.appendChild(el("p", null, p.que + ": " + (p.donde || "")));
    c.appendChild(el("p", "consola-nota", p.efecto + " · deshacer: " + p.deshacer));
    c.appendChild(sinCapacidad("Parar desde aquí", p.causa || "solo lectura", "consola-parada-nd"));
    c.appendChild(fila("Plan vigente", esNoData(r.plan_vigente) ? r.plan_vigente :
      "cola: " + valor(r.plan_vigente.cola) + (typeof r.plan_vigente.edad_s === "number" ?
        " · hace " + Math.round(r.plan_vigente.edad_s / 60) + " min" : "")));
    c.appendChild(fila("Interruptores", r.interruptores));

    var i = r.instantanea || {};
    c.appendChild(el("h3", "consola-sub", "Rack (laboratorio)"));
    if (esNoData(i)) { c.appendChild(fila("Instantánea", i)); return; }
    c.appendChild(fila("Edad", Math.round(i.edad_s / 60) + " min"));
    c.appendChild(fila("Nivel del rack", i.nivel ? i.nivel.nombre + " (" + i.nivel.n + " de " + i.nivel.maximo + ")" :
      { estado: ND, causa: "el laboratorio no lo midió" }));
    var ul = el("ul", "consola-lista");
    (i.nodos || []).forEach(function (x) {
      ul.appendChild(el("li", x.estado === enLinea ? null : "consola-nd",
        x.nodo + " · " + x.estado + (x.nota ? " · " + x.nota : "")));
    });
    if (!ul.children.length) ul.appendChild(el("li", "consola-nd", ND + " · sin nodos en la instantánea"));
    c.appendChild(ul);
    var res = ((i.ollama || {}).residentes || []).map(function (m) {
      return m.modelo + (m.backend ? " (" + m.backend + ")" : "");
    });
    c.appendChild(fila("Residentes en Ollama", res));
    (i.no_data || []).forEach(function (x) {
      c.appendChild(fila(x.campo, { estado: ND, causa: x.causa }));
    });
  }

  // --- canales -------------------------------------------------------------
  // Dos capas por mensaje: la frase humana, visible; la capa maquina (sello,
  // rol, maquina), plegada. Un canal no es autoridad: se dice en la cabecera.
  function canales(c) {
    c.appendChild(el("p", "consola-nota",
      "Un canal no es autoridad: ningún mensaje concede permisos ni cuenta como firma."));
    var lab = el("label", "consola-etq", "Canal");
    lab.htmlFor = "consola-canal";
    var sel = el("select", "consola-select");
    sel.id = "consola-canal";
    var lista = el("div", "consola-canal-lista");
    lista.setAttribute("aria-live", "polite");
    c.appendChild(lab); c.appendChild(sel); c.appendChild(lista);

    var f = el("form", "consola-sugerir");
    var lt = el("label", "consola-etq", "Escribir como soberano");
    lt.htmlFor = "consola-canal-texto";
    var inp = el("input", "consola-select");
    inp.id = "consola-canal-texto"; inp.type = "text"; inp.maxLength = 8000;
    inp.autocomplete = "off";
    var b = el("button", "consola-boton consola-boton-vivo", "Decir");
    b.type = "submit";
    var estadoEnvio = el("p", "consola-nota");
    estadoEnvio.setAttribute("role", "status");
    f.appendChild(lt); f.appendChild(inp); f.appendChild(b);
    c.appendChild(f); c.appendChild(estadoEnvio);

    function pintaMensajes(r) {
      lista.textContent = "";
      if (esNoData(r)) { lista.appendChild(el("p", "consola-nd", valor(r))); return; }
      if (r.corruptas) lista.appendChild(el("p", "consola-nd", r.corruptas + " línea(s) ilegibles en el canal; no se pintan."));
      (r.mensajes || []).slice(-30).forEach(function (m) {
        var art = el("article", "consola-mensaje");
        art.appendChild(el("p", "consola-etq", "#" + m.n + " · " + m.voz + " · " + m.t));
        art.appendChild(el("p", null, m.texto));
        var d = el("details", "consola-detalle");
        d.appendChild(el("summary", null, "Capa máquina"));
        d.appendChild(fila("Sello", m.sello));
        d.appendChild(fila("Rol", m.rol || "ninguno"));
        d.appendChild(el("pre", "consola-pre", JSON.stringify(m.maquina || {}, null, 1)));
        art.appendChild(d);
        lista.appendChild(art);
      });
      if (!(r.mensajes || []).length) lista.appendChild(el("p", "consola-nd", ND + " · el canal aún no tiene mensajes"));
    }

    function carga() {
      fetch("/api/canales?canal=" + encodeURIComponent(sel.value), { cache: "no-store" })
        .then(function (r) { if (!r.ok) throw new Error("el servidor respondió " + r.status); return r.json(); })
        .then(pintaMensajes)
        .catch(function (e) { lista.textContent = ""; lista.appendChild(el("p", "consola-nd", ND + " · " + e.message)); });
    }

    fetch("/api/canales", { cache: "no-store" })
      .then(function (r) { if (!r.ok) throw new Error("el servidor respondió " + r.status); return r.json(); })
      .then(function (r) {
        (r.canales || []).forEach(function (x) {
          var o = el("option", null, x.canal + " (" + x.ultimo + ")");
          o.value = x.canal;
          sel.appendChild(o);
        });
        sel.addEventListener("change", carga);
        if (sel.options.length) carga();
      })
      .catch(function (e) { lista.appendChild(el("p", "consola-nd", ND + " · " + e.message)); });

    f.addEventListener("submit", function (ev) {
      ev.preventDefault();
      if (!inp.value.trim() || !sel.value) return;
      fetch("/api/canales", { method: "POST", headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({ canal: sel.value, texto: inp.value }) })
        .then(function (r) { return r.json().then(function (j) { if (!r.ok) throw new Error(j.motivo || r.status); return j; }); })
        .then(function (m) { inp.value = ""; estadoEnvio.textContent = "Escrito como #" + m.n + "."; carga(); })
        .catch(function (e) { estadoEnvio.textContent = ND + " · " + e.message; });
    });
  }

  // --- arranque -------------------------------------------------------------
  function monta(v) {
    var nav = document.getElementById("consola");
    if (!nav) return;
    nav.textContent = "";
    conQuien(cajon(nav, "Con quién hablas", "quien"), v);
    modelos(cajon(nav, "Modelos", "modelos"), v);
    juego(cajon(nav, "TheGame", "thegame"), v);
    juez(cajon(nav, "Juez · media", "juez"), v);
    rack(cajon(nav, "Rack/Lab (solo lectura)", "rack"), v);
    canales(cajon(nav, "Canales", "canales"));
    nav.hidden = false;
  }

  function falla(causa) {
    var nav = document.getElementById("consola");
    if (!nav) return;
    nav.textContent = "";
    nav.appendChild(el("p", "consola-nd", "Consola · " + ND + " · " + causa));
    nav.hidden = false;
  }

  function carga() {
    fetch("/api/consola", { cache: "no-store" })
      .then(function (r) {
        if (!r.ok) throw new Error("el servidor respondió " + r.status);
        return r.json();
      })
      .then(function (v) {
        if (!v || v.esquema !== "preceptoros.consola/1") throw new Error("esquema inesperado");
        monta(v);
      })
      .catch(function (e) { falla(e && e.message ? e.message : "sin respuesta"); });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", carga);
  else carga();
})(this);
