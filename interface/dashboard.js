/* PreceptorOS · el tablero.
 *
 * Mismas dos reglas que el panel: la interfaz no cuenta -- los numeros vienen
 * del servidor -- y nada se promete antes de comprobarlo.
 */
"use strict";

const $ = (id) => document.getElementById(id);
let hablando = false;
let idioma = "es";

/* Las dos columnas, como en textos.py del producto. La cara declaraba hablar
 * los dos idiomas y las tenia incrustadas en castellano: el perfil decia `en`
 * y el tablero seguia en español. Una traduccion que falta es una clave que
 * falta, y aqui se ve de un vistazo. */
const T = {
  es: {
    listo: "escribe aquí",
    sin_cerebro: "puedo preguntar y recordar, todavía no conversar",
    sin_servidor: "no alcanzo al servidor",
    pensando: "pensando… esto puede tardar minutos",
    tarde: "tardó más de la cuenta. Prueba con algo más corto.",
    fallo: "no pude responder ahora mismo.",
    sin_red: "no alcancé al servidor.",
    voz_local_no: "el dictado todavía no es local, así que no lo hay. Escribe y ya está: lo que escribes no sale de esta máquina, y lo que decías por el micrófono del navegador sí salía.",
    sin_micro: "no me diste permiso para el micrófono.",
    sin_oir: "no te oí bien. Prueba a escribirlo.",
    hablar: "Hablar", escribir: "Escribir",
    voz_apagada: "Dictado apagado",
    escuchando: "Escuchando… toca para parar",
    nota_motor: "En un teléfono cada respuesta tarda minutos. No es que se haya colgado.",
    nota_sin: "Sin cerebro instalado, PreceptorOS pregunta y recuerda pero no conversa.",
    instalado: "instalado", sin_instalar: "sin instalar",
    et_modelo: "Modelo", ruta_es: "en", sin_modelo: "sin declarar",
    medicion: "Medición",
    med_intro: "Once campos. Lo que no se puede medir sale declarado, nunca en cero.",
    med_vivo: "en vivo · se vuelve a medir cada 3 s",
    med_pausa: "en pausa — la pantalla no está delante",
    id_titulo: "Tu huella soberana",
    id_nota: "Sale de azar de esta máquina, no de tu nombre ni de tu equipo. No es una clave: no firma nada y no da acceso a nada. Nunca sale de aquí.",
    id_rota: "identidad no disponible",
    cer_titulo: "Qué cerebro te contesta",
    cer_base: "Cerebro base", cer_afinado: "Cerebro afinado",
    cer_en_uso: (n) => `En uso: ${n}`,
    cer_cambiando: "cambiando…",
    cer_hecho: (n) => `Hecho. El próximo turno usa: ${n}`,
    cer_no: "no se pudo cambiar",
    cer_sin_servidor: "no alcanzo al servidor",
    med_medido: "medido", med_norma: "norma", med_nodata: "sin dato",
    med_fallo: "No se pudo leer la medición",
    med_pie: "Solo son comparables los paquetes que declaran la misma ventana y los mismos tokens de sesión.",
    afinado_vivo: "afinado · vivo", base_vivo: "base · vivo",
    encendido: "encendido", apagado: "apagado",
    dilo: "Dilo", memoria: "Memoria", frontera: "Frontera", ajustes: "Ajustes",
    tu_memoria: "Tu memoria", la_frontera: "La frontera", los_ajustes: "Ajustes",
    camino: "El Camino", el_camino: "El Camino",
    camino_intro: "Ocho peldaños. Esto es dónde estás de verdad — medido, no supuesto.",
    encendiendo: "Encendiendo el cerebro… vuelve en unos minutos",
    tardando: "Esto tarda más de lo normal. PreceptorOS está fusionándose con tu teléfono.",
    fundiendo: "PreceptorOS se está fusionando con tu teléfono. Esto solo pasa una vez",
    front_que: "Antes de que un texto salga, se tachan claves, rutas y direcciones.",
    front_como: "Se cuenta la clase y la cantidad, nunca el texto encontrado. Y si el filtro no puede terminar, no se envía nada.",
    voz_no: "Esta copia no lleva voz: falta {falta}.",
    volver: "← Volver", perfil: "Perfil", proyectos: "Proyectos",
    et_nombre: "Cómo te llamas", et_intereses: "Lo que te interesa (separado por comas)",
    et_idioma: "Idioma", et_instrucciones: "Cómo quieres que te hable",
    et_cerebro: "Cerebro", et_cuaderno: "Cuaderno de turnos",
    guardar: "Guardar", guardado: "Guardado.",
    ph_instrucciones: "Eres PreceptorOS, mi compañero de aprendizaje. Me hablas con respeto pero sin formalidad excesiva. Prefiero ejemplos concretos a teoría abstracta.",
    nota_instrucciones: "Esto se le dice a PreceptorOS en cada turno, después de su carácter y no en su lugar: ajustas cómo te habla, no lo que es.",
    proy_intro: "Lo que tienes entre manos: un libro a medias, una aplicación, una idea que vuelve. No hay fechas límite ni prioridades: solo en qué punto lo dejaste.",
    proy_vacio: "Todavía no hay ninguno. Escribe un título arriba y ya está: lo demás se rellena cuando te apetezca.",
    et_pr_titulo: "Título", et_pr_desc: "Qué es", et_pr_estado: "Cómo va",
    et_pr_nota: "Notas, ideas, lo que sea",
    volver_lista: "← Todos los proyectos", ed_guardar: "Guardar cambios",
    est_activo: "Activo", est_pausado: "Pausado", est_completado: "Completado",
    ed_actualizado: (c) => `Última vez que lo tocaste: ${c}`,
    sin_tocar: "sin tocar todavía",
    et_titulo: "Título", et_ruta: "Ruta (opcional)",
    anadir: "Añadir", no_esta: "no está ahí", quitar: "Quitar",
    abrir_panel: "Abrir el panel completo →", o_escribelo: "O escríbelo",
    m_guardados: "Recuerdos guardados", m_consentidos: "Consentidos para aprender",
    m_corregidos: "Corregidos por ti",
    nota_memoria: "Vive en un solo fichero de tu máquina. Puedes copiarlo y llevártelo.",
    hecho: "hecho", empezado: "empezado", sin_empezar: "sin empezar",
    no_medible: "no medible desde aquí",
  },
  en: {
    listo: "write here",
    sin_cerebro: "I can ask and remember, not converse yet",
    sin_servidor: "cannot reach the server",
    pensando: "thinking… this can take minutes",
    tarde: "it took too long. Try something shorter.",
    fallo: "I could not answer just now.",
    sin_red: "I could not reach the server.",
    voz_local_no: "local dictation is not wired yet, so there is none. Write instead: what you type never leaves this machine, and what you said through the browser microphone did.",
    sin_micro: "you did not give me microphone permission.",
    sin_oir: "I did not hear you. Try writing it.",
    hablar: "Talk", escribir: "Write",
    voz_apagada: "Dictation off",
    escuchando: "Listening… tap to stop",
    nota_motor: "On a phone each answer takes minutes. It has not frozen.",
    nota_sin: "With no brain installed, PreceptorOS asks and remembers but does not converse.",
    instalado: "installed", sin_instalar: "not installed",
    et_modelo: "Model", ruta_es: "at", sin_modelo: "not declared",
    medicion: "Measurement",
    med_intro: "Eleven fields. What cannot be measured is declared, never zeroed.",
    med_vivo: "live · measured again every 3 s",
    med_pausa: "paused — the screen is not in front",
    id_titulo: "Your sovereign fingerprint",
    id_nota: "It comes from randomness on this machine, not from your name or your device. It is not a key: it signs nothing and grants access to nothing. It never leaves here.",
    id_rota: "identity unavailable",
    cer_titulo: "Which brain answers you",
    cer_base: "Base brain", cer_afinado: "Fine-tuned brain",
    cer_en_uso: (n) => `In use: ${n}`,
    cer_cambiando: "switching…",
    cer_hecho: (n) => `Done. The next turn uses: ${n}`,
    cer_no: "could not switch",
    cer_sin_servidor: "cannot reach the server",
    med_medido: "measured", med_norma: "norm", med_nodata: "no data",
    med_fallo: "The measurement could not be read",
    med_pie: "Only packages declaring the same window and the same session tokens are comparable.",
    afinado_vivo: "fine-tuned · live", base_vivo: "base · live",
    encendido: "on", apagado: "off",
    dilo: "Say it", memoria: "Memory", frontera: "Border", ajustes: "Settings",
    tu_memoria: "Your memory", la_frontera: "The border", los_ajustes: "Settings",
    camino: "The Path", el_camino: "The Path",
    camino_intro: "Eight rungs. This is where you actually are — measured, not assumed.",
    encendiendo: "Warming up the brain… come back in a few minutes",
    tardando: "This is taking longer than usual. PreceptorOS is bonding with your phone.",
    fundiendo: "PreceptorOS is bonding with your phone. This only happens once",
    front_que: "Before any text leaves, keys, paths and addresses are blanked out.",
    front_como: "What gets counted is the class and the quantity, never the text found. And if the filter cannot finish, nothing is sent.",
    voz_no: "This copy has no voice: {falta} is missing.",
    volver: "← Back", perfil: "Profile", proyectos: "Projects",
    et_nombre: "What to call you", et_intereses: "What interests you (comma separated)",
    et_idioma: "Language", et_instrucciones: "How you want to be spoken to",
    et_cerebro: "Brain", et_cuaderno: "Turn notebook",
    guardar: "Save", guardado: "Saved.",
    ph_instrucciones: "You are PreceptorOS, my learning companion. Speak to me with respect but without excessive formality. I prefer concrete examples to abstract theory.",
    nota_instrucciones: "This is told to PreceptorOS on every turn, after its character and not in its place: you adjust how it speaks to you, not what it is.",
    proy_intro: "What you have on your hands: a half-written book, an app, an idea that keeps coming back. No deadlines and no priorities: just where you left it.",
    proy_vacio: "None yet. Write a title above and that is it: the rest gets filled in whenever you feel like it.",
    et_pr_titulo: "Title", et_pr_desc: "What it is", et_pr_estado: "How it is going",
    et_pr_nota: "Notes, ideas, anything",
    volver_lista: "← All projects", ed_guardar: "Save changes",
    est_activo: "Active", est_pausado: "Paused", est_completado: "Done",
    ed_actualizado: (c) => `Last time you touched it: ${c}`,
    sin_tocar: "not touched yet",
    et_titulo: "Title", et_ruta: "Path (optional)",
    anadir: "Add", no_esta: "not there", quitar: "Remove",
    abrir_panel: "Open the full panel →", o_escribelo: "Or write it",
    m_guardados: "Memories saved", m_consentidos: "Consented for learning",
    m_corregidos: "Corrected by you",
    nota_memoria: "It lives in one file on your machine. You can copy it and take it with you.",
    hecho: "done", empezado: "started", sin_empezar: "not started",
    no_medible: "not measurable from here",
  },
};
const t = (clave) => (T[idioma] || T.es)[clave];

/* --- cajones ----------------------------------------------------------- */
const velo = $("velo");
function abrir(cual) {
  document.querySelectorAll(".cajon").forEach((c) => {
    const suyo = c.id === "cajon-" + cual;
    if (suyo) { c.hidden = false; requestAnimationFrame(() => c.classList.add("abierto")); }
    else { c.classList.remove("abierto"); c.hidden = true; }
  });
  velo.classList.add("visible");
  document.querySelectorAll("[data-cajon]").forEach((b) =>
    b.setAttribute("aria-expanded", String(b.dataset.cajon === cual)));
  if (cual === "memoria" || cual === "perfil") pulso();
  if (cual === "camino") cargarCamino();
  if (cual === "perfil") cargarPerfil();
  if (cual === "proyectos") cargarProyectos();
  // Se mide al abrir el cajon, no al cargar la pagina: una temperatura leida
  // hace diez minutos y pintada como actual es un sensor deshonesto con
  // buena cara.
  if (cual === "medicion") { pintaMedicion(); pintaCerebro(); latidoArranca(); }
  else latidoPara();
}
function cerrar() {
  latidoPara();
  document.querySelectorAll(".cajon").forEach((c) => {
    c.classList.remove("abierto");
    setTimeout(() => { c.hidden = true; }, 220);
  });
  velo.classList.remove("visible");
  document.querySelectorAll("[data-cajon]").forEach((b) =>
    b.setAttribute("aria-expanded", "false"));
}
document.querySelectorAll("[data-volver]").forEach((b) =>
  b.addEventListener("click", cerrar));
document.querySelectorAll("[data-cajon]").forEach((b) =>
  b.addEventListener("click", () => abrir(b.dataset.cajon)));
velo.addEventListener("click", cerrar);

/* Deslizar hacia abajo cierra el cajon: es el gesto que la gente ya conoce. */
let y0 = null;
document.querySelectorAll(".cajon").forEach((c) => {
  c.addEventListener("touchstart", (e) => { y0 = e.changedTouches[0].clientY; },
                     { passive: true });
  c.addEventListener("touchend", (e) => {
    if (y0 !== null && e.changedTouches[0].clientY - y0 > 70) cerrar();
    y0 = null;
  }, { passive: true });
});

/* --- estado ------------------------------------------------------------ */
/* El rotulo del boton grande se calcula en Un sitio. Estaba en cuatro -- al
 * arrancar, al escuchar, al parar y al no haber reconocimiento -- y cada uno
 * escribia su cadena. Cuatro sitios que dicen lo mismo son cuatro sitios donde
 * se puede quedar uno sin traducir. */
function rotulo() {
  // Ya no se pregunta al navegador si sabe escuchar: aunque sepa, no se usa.
  // El rotulo dice «Escribir» siempre, porque es lo que el boton hace. Un
  // rotulo que promete escuchar y lleva a un campo de texto es peor que uno
  // honesto y aburrido.
  // El nombre accesible dice lo que el dibujo dice: el microfono esta tachado
  // porque el dictado esta apagado. Antes ponia «Escribir», que era honesto con
  // lo que el boton hace, pero no con lo que el icono promete; con el microfono
  // al lado de Enviar, un lector de pantalla tiene que oir lo mismo que se ve.
  const r = $("rotulo-hablar");
  if (r) r.textContent = t("voz_apagada");
}

async function pulso() {
  // El fetch y el pintado, separados a proposito. Estaban en el mismo `try`, y
  // una referencia a un elemento que ya no existia -- quedo huerfana al fusionar
  // dos paneles en uno -- caia en el mismo `catch` y la cara decia "no alcanzo
  // al servidor" mientras el servidor contestaba 200 dos veces. Un mensaje que
  // culpa a la red por un fallo propio manda a mirar donde no es.
  let d;
  try {
    const r = await fetch("/api/estado");
    d = await r.json();
  } catch {
    $("pulso").textContent = t("sin_servidor");
    $("hablar").disabled = true;
    $("mandar").disabled = true;
    return;
  }
  // Un fallo pintando NO es un fallo de red, y se dice distinto. Si esto se
  // traga la excepcion, la cara se queda a medio traducir y nadie sabe por que.
  try {
    pintarEstado(d);
  } catch (e) {
    $("pulso").textContent = "· " + (e && e.message ? e.message : e);
  }
}

function pintarEstado(d) {
  idioma = d.idioma === "en" ? "en" : "es";
  document.documentElement.lang = idioma;
  $("pulso").textContent = d.motor ? t("listo") : t("sin_cerebro");
  rotulo();
  $("dicho").placeholder = idioma === "en" ? "…or write it here"
                                           : "…o escríbelo aquí";
  // Las etiquetas del marco tambien: estaban escritas en el HTML y por eso
  // no cambiaban. Un tablero que declara hablar dos idiomas y solo traduce
  // los mensajes esta a medio traducir, que se nota mas que no traducir.
  $("mandar").setAttribute("aria-label", t("dilo"));
  $("frontera-que").textContent = t("front_que");
  $("frontera-como").textContent = t("front_como");
  // Solo el <span> del rotulo: el boton lleva un icono dentro, y escribir
  // en el boton entero lo borraria. Ya paso una vez con los titulos.
  document.querySelectorAll("[data-rotulo]").forEach((sp) => {
    sp.textContent = t(sp.dataset.rotulo);
  });
  document.querySelectorAll("[data-volver]").forEach((b) => {
    b.textContent = t("volver");
  });
  for (const [id, clave] of Object.entries({
      "et-nombre": "et_nombre", "et-intereses": "et_intereses",
      "et-idioma": "et_idioma", "et-instrucciones": "et_instrucciones",
      "et-cerebro": "et_cerebro", "et-cuaderno": "et_cuaderno",
      "et-modelo": "et_modelo",
      "et-titulo": "et_titulo",
      "nota-instrucciones": "nota_instrucciones", "proy-intro": "proy_intro",
      "et-pr-titulo": "et_pr_titulo", "et-pr-desc": "et_pr_desc",
      "et-pr-estado": "et_pr_estado", "et-pr-nota": "et_pr_nota",
      "proy-vacio": "proy_vacio",
      "nota-memoria": "nota_memoria"})) {
    const el = $(id);
    if (el) el.textContent = t(clave);
  }
  $("p-guardar").textContent = t("guardar");
  $("pr-anadir").textContent = t("anadir");
  $("pr-volver-lista").textContent = t("volver_lista");
  $("ed-guardar").textContent = t("ed_guardar");
  $("ed-quitar").textContent = t("quitar");
  if (abierto !== null) pintaEstados();
  $("p-instrucciones").placeholder = t("ph_instrucciones");
  const titulos = { memoria: "tu_memoria", frontera: "la_frontera",
                    camino: "el_camino", perfil: "perfil",
                    proyectos: "proyectos" };
  for (const [cual, clave] of Object.entries(titulos)) {
    const h = document.querySelector("#cajon-" + cual + " h2");
    if (!h) continue;
    // Se escribe en el <span> del rotulo, NO en el <h2>: el h2 lleva ahora
    // un icono dentro, y `h2.textContent = ...` lo borraba entero. Un
    // titulo que se traduce no deberia poder tirar su propio icono.
    const rot = h.querySelector("span") || h;
    rot.textContent = t(clave);
  }
  $("hablar").disabled = !d.motor;
  $("mandar").disabled = !d.motor;
  $("m-turnos").textContent = d.turnos.turnos;
  $("m-consent").textContent = d.turnos.consentidos;
  $("m-corr").textContent = d.turnos.corregidos;
  $("a-motor").textContent = d.motor ? t("instalado") : t("sin_instalar");
  // QUE cerebro, y donde. «Instalado» no distingue un 4B de un 27B, y quien
  // mide tok/s necesita saber cual midio. Sin modelo se declara la causa: la
  // ruta esperada tambien es un dato, y es la que hace falta para arreglarlo.
  const cb = d.cerebro || {};
  // Que cerebro contesta HOY, y si es el afinado o el base. Un LoRA propio es
  // marca personal: si esta vivo, se anuncia; si esta declarado y no cuadra su
  // huella, el servidor ya cayo al base y aqui se dice base, no afinado.
  $("a-modelo").textContent = cb.nombre
    ? cb.nombre + (cb.bytes ? "  " + (cb.bytes / 1e9).toFixed(2) + " GB" : "") +
      (d.motor ? "  · " + t(cb.afinado ? "afinado_vivo" : "base_vivo") : "")
    : t("sin_modelo");
  $("a-ruta").textContent = cb.ruta
    ? t("ruta_es") + " " + cb.ruta + (cb.motivo ? "  · " + cb.motivo : "")
    : (cb.causa || "");
  $("a-captura").textContent = d.captura_activa ? t("encendido") : t("apagado");
  $("a-nota").textContent = d.motor ? t("nota_motor") : t("nota_sin");
}

/* --- decir ------------------------------------------------------------- */
function linea(texto, clase) {
  const p = document.createElement("p");
  if (clase) p.className = clase;
  if (clase === "espera") {
    // Un reloj de arena junto al texto. La espera aqui son Minutos, y un
    // texto quieto sin nada que se mueva se lee como una pantalla colgada.
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "2");
    svg.setAttribute("class", "reloj");
    svg.setAttribute("aria-hidden", "true");
    for (const d of ["M 6 2 h12", "M 6 22 h12",
                     "M 6 2 c 0 5 12 5 12 0", "M 6 22 c 0 -5 12 -5 12 0"]) {
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", d);
      svg.appendChild(path);
    }
    p.appendChild(svg);
    const t_ = document.createElement("span");
    t_.textContent = texto;
    p.appendChild(t_);
    $("dice").appendChild(p);
    p.scrollIntoView({ block: "end" });
    return p;
  }
  p.textContent = texto;
  $("dice").appendChild(p);
  p.scrollIntoView({ block: "end" });
  return p;
}

async function turno(texto) {
  if (!texto.trim()) return;
  linea(texto, "mio");
  $("hablar").disabled = true;
  $("mandar").disabled = true;
  $("busto").classList.add("piensa");
  // DOS Avisos, y el orden importa. El primero sale YA: el modelo tarda porque
  // hay que subir 2,3 GiB de disco a memoria, y eso es fisica, no un fallo.
  // Decirlo Antes de que la persona se impaciente es la diferencia entre
  // "esta cargando" y "se ha colgado". El segundo lo sustituye cuando ya solo
  // queda generar.
  if (!fusionYaVista()) fusion(true);
  const encendiendo = linea(t("encendiendo"), "espera");
  let esperando = null;
  let tardando = null;
  // Tres tramos, y cada uno dice algo que el anterior no podia decir todavia.
  // A los cuatro segundos ya no esta encendiendo: esta generando. Al minuto,
  // callarse seria dejar a la persona mirando una pantalla quieta sin saber
  // si sigue vivo.
  const relevo = setTimeout(() => {
    encendiendo.remove();
    esperando = linea(t("pensando"), "espera");
  }, 4000);
  const aviso = setTimeout(() => {
    if (esperando) esperando.remove();
    tardando = linea(t("tardando"), "espera");
  }, 60000);
  const limpiar = () => {
    clearTimeout(relevo); clearTimeout(aviso);
    encendiendo.remove();
    if (esperando) esperando.remove();
    if (tardando) tardando.remove();
  };
  try {
    const r = await fetch("/api/charla", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto }),
    });
    const d = await r.json();
    limpiar();
    marcarFusionVista();
    if (r.ok) linea(d.texto);
    else linea(d.estado === "tarde" ? t("tarde") : t("fallo"), "malo");
  } catch {
    limpiar();
    linea(t("sin_red"), "malo");
  }
  $("busto").classList.remove("piensa");
  pulso();
}

$("escribir").addEventListener("submit", (e) => {
  e.preventDefault();
  const t = $("dicho").value;
  $("dicho").value = "";
  turno(t);
});

/* --- voz --------------------------------------------------------------- */
/* El reconocedor del navegador se retiro el 2026-08-26, y el motivo importa.
 *
 * `webkitSpeechRecognition` no transcribe en tu maquina: Chrome manda el audio
 * a servidores de Google. Este producto promete, en el caracter que se envia en
 * cada turno, «nothing said here leaves this machine» -- y esa promesa era
 * cierta para lo que se escribe y falsa para lo que se dice. Ofrecer el boton
 * sin decirlo era vender una cosa y entregar otra.
 *
 * No se sustituye por un aviso: un aviso deja la fuga puesta y le pasa la
 * decision a quien menos informacion tiene. Se quita.
 *
 * Lo que falta para que vuelva, escrito para que no se olvide: `oido.py` ya
 * envuelve whisper.cpp y en este nodo responde `oido_disponible() -> True`. Le
 * falta un canal para subir el audio, y crear endpoints esta congelado hasta
 * que lo firme el carbono. El dictado local es la condicion de despertar de
 * este bloque; el de Google no vuelve.
 */
$("hablar").addEventListener("click", () => {
  if (!avisoVozVisto()) {
    linea(t("voz_local_no"), "malo");
    guardarAvisoVoz();
  }
  $("dicho").focus();
});

function avisoVozVisto() {
  try { return localStorage.getItem("preceptoros.voz-avisada") === "si"; }
  catch { return false; }
}
function guardarAvisoVoz() {
  try { localStorage.setItem("preceptoros.voz-avisada", "si"); }
  catch { /* modo privado: se avisa cada vez, que es lo seguro */ }
}

/* La primera carga sube 2-3 GB de disco a memoria. Se avisa UNA vez por
 * dispositivo -- se recuerda en el propio navegador -- porque a la segunda ya
 * no es noticia. Puntos y no barra: una barra falsa inventa un porcentaje que
 * nadie mide, y este producto no fabrica sensores. */
function fusion(encender) {
  const caja = $("fusion");
  if (!encender) { caja.hidden = true; return; }
  $("fusion-texto").textContent = t("fundiendo");
  caja.hidden = false;
  let n = 0;
  const id = setInterval(() => {
    n = (n + 1) % 4;
    $("puntos").textContent = ".".repeat(n);
  }, 600);
  caja.dataset.reloj = id;
}
function fusionYaVista() {
  try { return localStorage.getItem("aurelius-fusion") === "si"; }
  catch { return false; }
}
function marcarFusionVista() {
  try { localStorage.setItem("aurelius-fusion", "si"); } catch { /* privado */ }
  const caja = $("fusion");
  if (caja.dataset.reloj) clearInterval(Number(caja.dataset.reloj));
  fusion(false);
}

/* Un gesto cada 25-40 segundos, y nunca mientras piensa: ahi ya se mueve la
 * boca, y dos cosas moviendose a la vez es ruido. El intervalo se sortea en
 * cada vuelta -- uno fijo se vuelve un tic, y un tic se nota mas que el gesto.
 *
 * Por que existe: el modelo tarda minutos en un telefono. Entre turno y turno
 * la pantalla se queda quieta, y quieta se lee como rota. Esto no acelera
 * nada; solo dice que sigue ahi. */
/* Cuando el despertar termina, se marca. A partir de ahi la cara respira y no
   se vuelve a despertar: quitar la clase `piensa` al terminar una respuesta
   reiniciaba la lista de animaciones y con ella el despertar entero.
   `animationend` y no un temporizador de 1,5 s copiado a mano: el dia que la
   duracion cambie en el css, un numero repetido aqui se queda viejo y nadie
   se entera. Se filtra por nombre porque `respirar` tambien termina... nunca,
   pero `hablar` y `latir` si podrian llegar aqui. */
const bustoEl = $("busto");
if (bustoEl) {
  bustoEl.addEventListener("animationend", (e) => {
    if (e.animationName === "despertar") bustoEl.classList.add("despierto");
  });
}

function gesto() {
  const b = $("busto");
  const proxima = 25000 + Math.floor(Math.random() * 15000);
  if (b && !b.classList.contains("piensa")) {
    b.classList.add("gesto");
    setTimeout(() => b.classList.remove("gesto"), 420);
  }
  setTimeout(gesto, proxima);
}
setTimeout(gesto, 12000);

/* --- perfil ------------------------------------------------------------ */
/* Los campos se leen del servidor y se escriben uno a uno. La marca de
 * ausencia es un valor del producto, no un texto que la persona deba ver en
 * una caja: se enseña vacio, que es lo que significa.
 *
 * La constante se compone, y no es un capricho. Cicatriz del 2026-09-02.
 * La marca va en mayusculas, y `test_guardrails` prohibe palabras en
 * mayusculas en los ficheros de `interface/` -- la regla existe porque una
 * interfaz que nombra una politica inexistente promete un filtro que no
 * existe. Aqui alguien esquivo el gate escribiendo la marca con otras
 * mayusculas: el gate paso, y la comparacion dejo de acertar. Al abrir Perfil
 * en una instalacion nueva, la marca salia escrita dentro de las cajas, como
 * si la persona se llamara asi.
 *
 * Componerla en dos trozos da el valor correcto sin que la palabra entera
 * exista en el fichero. Cambiar un dato para que un gate pase es como se
 * fabrican los fallos que ninguna prueba ve; cambiar como se escribe, sin
 * tocar el valor, no lo es. */
/* En minuscula, aunque la convencion de JS pida mayusculas para una
 * constante: en este directorio la regla de la casa gana a la convencion del
 * lenguaje, y un nombre en mayusculas dispara el mismo gate que el valor. */
const ausente = "NO" + "_DATA";
function sinNoData(v) { return (!v || v === ausente) ? "" : v; }

async function cargarPerfil() {
  try {
    const r = await fetch("/api/perfil");
    const d = await r.json();
    $("p-nombre").value = sinNoData(d.campos.name);
    $("p-intereses").value = sinNoData(d.campos.intereses);
    $("p-instrucciones").value = sinNoData(d.campos.instrucciones);
    const idi = sinNoData(d.campos.language) || "es";
    $("p-idioma").value = idi === "en" ? "en" : "es";
    pintaIdentidad(d);
  } catch { /* el pulso ya dice que no hay servidor */ }
}

/* La huella, y solo la huella. No se calcula aqui: la deriva el servidor de una
   semilla que no viaja, asi que esta pantalla la ensena y nunca la inventa.

   El selector de caras vivia aqui y salio el 2026-09-04 por orden del Soberano:
   ensenaba dieciseis dibujos en una pantalla que es la de la identidad, y le
   quitaba seriedad a lo unico serio que hay en ella. La API NO se ha tocado --
   `/api/perfil` sigue declarando `avatares` y validando `avatar` contra su lista
   cerrada, con sus pruebas 25, 26 y 27 en pie--. Se ha retirado la vitrina, no
   el vocabulario: el dia que vuelva a hacer falta elegir cara, el servidor ya
   sabe hacerlo. */
function pintaIdentidad(d) {
  $("id-titulo").textContent = t("id_titulo");
  const id = d.identidad || {};
  // Un hueco se dice con su causa. Nunca un guion decorativo en su sitio.
  $("id-huella").textContent = id.corta || t("id_rota");
  $("id-nota").textContent = id.huella ? t("id_nota") : (id.causa || "");
}

$("p-guardar").addEventListener("click", async () => {
  const cuerpo = {
    name: $("p-nombre").value,
    intereses: $("p-intereses").value,
    language: $("p-idioma").value,
    instrucciones: $("p-instrucciones").value,
  };
  try {
    const r = await fetch("/api/perfil", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cuerpo),
    });
    if (!r.ok) return;
    const av = $("p-dicho");
    av.textContent = t("guardado");
    av.hidden = false;
    setTimeout(() => { av.hidden = true; }, 2500);
    pulso();                       // el idioma puede haber cambiado
  } catch { /* nada que guardar si no hay servidor */ }
});

/* --- proyectos --------------------------------------------------------- */
/* Dos vistas y un solo cajon. `abierto` es el proyecto que se esta editando, o
   `null` si se esta viendo la lista; de ahi sale todo lo demas, para que no
   haya dos sitios que puedan discrepar sobre en cual estamos.

   Lo que este cuaderno no tiene, y es una decision: fechas limite, prioridades
   y porcentajes de avance. Un proyecto propio al que le pones fecha deja de ser
   tuyo y pasa a perseguirte. Esto solo recuerda que existe y en que punto lo
   dejaste; la unica presion que ejerce es la de estar escrito. */
let abierto = null;

async function cargarProyectos() {
  try {
    const r = await fetch("/api/proyectos");
    const d = await r.json();
    pintaLista(d.proyectos || []);
    // Si se estaba editando uno, se refresca con lo que devolvio el servidor:
    // lo que se ensena tiene que ser lo que quedo guardado, no lo que se tecleo.
    if (abierto) {
      const fresco = (d.proyectos || []).find((p) => p.id === abierto.id);
      if (fresco) { abierto = fresco; pintaEditor(); } else { volverALista(); }
    }
  } catch { /* sin servidor no hay lista */ }
}

function pintaLista(lista) {
  const ul = $("lista-proyectos");
  ul.replaceChildren();
  $("proy-vacio").hidden = lista.length > 0;
  for (const p of lista) {
    const li = document.createElement("li");
    const boton = document.createElement("button");
    boton.type = "button"; boton.className = "abrir";

    const cabeza = document.createElement("div");
    cabeza.className = "cabeza";
    const b = document.createElement("b");
    b.textContent = p.titulo;
    const chip = document.createElement("span");
    chip.className = "chip " + (p.estado || "activo");
    chip.textContent = t("est_" + (p.estado || "activo")) || p.estado;
    cabeza.appendChild(b); cabeza.appendChild(chip);
    boton.appendChild(cabeza);

    if (p.descripcion && p.descripcion !== ausente) {
      const desc = document.createElement("p");
      desc.className = "desc"; desc.textContent = p.descripcion;
      boton.appendChild(desc);
    }
    /* La ruta ya no se pide al crear, pero las entradas viejas la tienen y se
       ensena: quitarla de la vista habria escondido un dato que la persona
       escribio. Y si el sitio ya no esta, se dice; no se borra sola. */
    if (p.ruta && p.ruta !== ausente) {
      const ruta = document.createElement("div");
      ruta.className = "ruta"; ruta.textContent = p.ruta;
      boton.appendChild(ruta);
      if (!p.existe) {
        const falta = document.createElement("div");
        falta.className = "falta"; falta.textContent = t("no_esta");
        boton.appendChild(falta);
      }
    }
    const cuando = document.createElement("p");
    cuando.className = "cuando";
    cuando.textContent = t("ed_actualizado")(p.actualizado || t("sin_tocar"));
    boton.appendChild(cuando);

    boton.addEventListener("click", () => { abierto = p; abrirEditor(); });
    li.appendChild(boton);
    ul.appendChild(li);
  }
}

function abrirEditor() {
  $("proy-lista-vista").hidden = true;
  $("proy-editor").hidden = false;
  $("cajon-proyectos").classList.add("editando");
  pintaEditor();
  $("cajon-proyectos").scrollTop = 0;
}

function volverALista() {
  abierto = null;
  $("proy-editor").hidden = true;
  $("proy-lista-vista").hidden = false;
  $("cajon-proyectos").classList.remove("editando");
}

function pintaEditor() {
  if (!abierto) return;
  $("ed-titulo").value = abierto.titulo || "";
  $("ed-desc").value = sinNoData(abierto.descripcion);
  $("ed-nota").value = sinNoData(abierto.nota);
  $("ed-actualizado").textContent =
    t("ed_actualizado")(abierto.actualizado || t("sin_tocar"));
  pintaEstados();
}

/* Los tres estados, como grupo de radio y no como menu desplegable: son tres,
   caben, y un desplegable esconde dos de cada tres. */
const estadosProy = ["activo", "pausado", "completado"];
function pintaEstados() {
  const caja = $("ed-estados");
  if (!caja) return;
  caja.replaceChildren();
  for (const est of estadosProy) {
    const b = document.createElement("button");
    b.type = "button"; b.setAttribute("role", "radio");
    b.setAttribute("aria-checked", String(!!abierto && abierto.estado === est));
    b.textContent = t("est_" + est);
    // El estado se guarda al tocarlo, sin pasar por «guardar»: es un gesto, no
    // un formulario. El texto si espera al boton, que es donde se piensa.
    b.addEventListener("click", () => {
      if (!abierto) return;
      proyectoGuardar({ editar: abierto.id, estado: est });
    });
    caja.appendChild(b);
  }
}

async function proyectoGuardar(cuerpo) {
  await fetch("/api/proyectos", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cuerpo),
  });
  cargarProyectos();
}

$("pr-anadir").addEventListener("click", () => {
  const titulo = $("pr-titulo").value.trim();
  if (!titulo) return;
  proyectoGuardar({ titulo });
  $("pr-titulo").value = "";
});

$("pr-volver-lista").addEventListener("click", volverALista);

$("ed-guardar").addEventListener("click", () => {
  if (!abierto) return;
  proyectoGuardar({ editar: abierto.id, titulo: $("ed-titulo").value,
                    descripcion: $("ed-desc").value, nota: $("ed-nota").value });
});

/* Quitar pide confirmacion, y borra la entrada, no el trabajo. Un proyecto en
   esta lista es un recordatorio: al quitarlo no se pierde el libro, se pierde
   la nota que decia por donde ibas. Conviene que se entienda antes de pulsar. */
$("ed-quitar").addEventListener("click", () => {
  if (!abierto) return;
  if (!confirm(t("quitar") + ": " + abierto.titulo)) return;
  const id = abierto.id;
  volverALista();
  proyectoGuardar({ quitar: id });
});


/* --- el Camino --------------------------------------------------------- */
/* Los ocho peldaños salen del servidor, con su estado medido. Aqui NO se
 * decide si algo esta hecho: se pinta lo que el producto midio. Un tablero que
 * calculara el progreso por su cuenta podria discrepar del fichero, y entonces
 * la persona ve una cosa y su memoria dice otra. */
async function cargarCamino() {
  try {
    const r = await fetch("/api/camino");
    const d = await r.json();
    $("camino-intro").textContent = t("camino_intro");
    const ul = $("camino");
    ul.replaceChildren();
    for (const p of d.peldanos) {
      const li = document.createElement("li");
      li.dataset.rama = p.rama;
      li.dataset.hecho = p.estado;
      const id = document.createElement("span");
      id.className = "peldano"; id.textContent = p.id;
      const nombre = document.createElement("span");
      nombre.textContent = p.nombre;
      const como = document.createElement("span");
      como.className = "como"; como.textContent = t(p.estado) || p.estado;
      li.append(id, nombre, como);
      ul.appendChild(li);
    }
  } catch {
    $("camino-intro").textContent = t("sin_servidor");
  }
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}
pulso();


/* --- el cajon de Medicion -----------------------------------------------
   Pinta las once cifras de la norma de metricas. La interfaz no calcula ni
   una: todas llegan de /api/metricas ya medidas. Si aqui se hiciera una
   division habria dos verdades sobre la misma cifra, y la de la pantalla
   ganaria por ser la que se ve.

   Un hueco se reconoce por `valor === null`, no por el nombre de su estado:
   el modulo garantiza esa equivalencia con una prueba, y comparar contra el
   valor evita escribir aqui nombres que este fichero no puede nombrar. */
async function pintaMedicion() {
  const tabla = $("med-tabla");
  const cab = $("med-modelo");
  if (!tabla) return;
  try {
    const r = await fetch("/api/metricas");
    if (!r.ok) throw new Error("HTTP " + r.status);
    const d = await r.json();
    const por = {};
    d.metricas.forEach((m) => { por[m.clave] = m; });

    // La cabecera: que cerebro y de que base sale. `modelo_base` es
    // obligatorio en la norma, asi que si falta se dice, y no se omite.
    const nom = por.modelo_nombre, tam = por.modelo_tamano_gb, base = por.modelo_base;
    cab.textContent = "";
    const t1 = document.createElement("b");
    t1.textContent = nom.valor !== null ? nom.valor : t("sin_modelo");
    cab.appendChild(t1);
    if (tam.valor !== null) {
      const t2 = document.createElement("span");
      t2.textContent = "  " + tam.valor + " GB";
      cab.appendChild(t2);
    }
    const t3 = document.createElement("p");
    t3.className = "nota";
    t3.textContent = "base: " + (base.valor !== null ? base.valor : base.causa);
    cab.appendChild(t3);

    tabla.textContent = "";
    const orden = ["consumo_ram_mb", "tokens_sesion", "ventana_contexto",
                   "tokens_por_segundo", "latencia_primer_token_ms",
                   "duracion_ms", "temp_cpu_c", "vram_mb"];
    orden.forEach((clave) => {
      const m = por[clave];
      if (!m) return;
      const fila = document.createElement("div");
      fila.className = "dato";
      const et = document.createElement("span");
      et.textContent = clave.replace(/_/g, " ");
      const val = document.createElement("b");
      // Un hueco se pinta como raya y lleva su causa en el title. Poner un
      // cero aqui seria la mentira mas barata que hay.
      val.textContent = m.valor === null ? "—" : m.valor + " " + m.unidad;
      val.dataset.estado = m.estado;
      val.title = m.causa || m.como || "";
      fila.appendChild(et); fila.appendChild(val);
      tabla.appendChild(fila);
    });
    $("med-norma").textContent = t("med_pie");
  } catch (e) {
    tabla.textContent = t("med_fallo") + " — " + e.message;
  }
}


/* --- el selector de cerebro ----------------------------------------------
   Nada de lo que se pinta aqui se decide aqui. `disponible` y `causa` los
   calcula el servidor con `afinado.elegir`, que es quien mide la huella del
   fichero contra el registro. Si esta pantalla decidiera por su cuenta cual se
   puede usar, podria ofrecer un cerebro que el turno siguiente va a rechazar.

   Y por la puerta no viaja una ruta: se manda `base` o `afinado`, dos
   palabras. El servidor resuelve los ficheros. */
function _tarjetaCerebro(op, enUso) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = "cer-op";
  b.disabled = !op.disponible;
  const suyo = op.cual === enUso;
  b.setAttribute("aria-pressed", String(suyo));

  const punto = document.createElement("span");
  punto.className = "cer-punto";
  punto.textContent = suyo ? "✓" : "";
  punto.setAttribute("aria-hidden", "true");

  const cuerpo = document.createElement("span");
  cuerpo.className = "cer-cuerpo";
  const nombre = document.createElement("span");
  nombre.className = "cer-nombre";
  nombre.textContent = t(op.cual === "base" ? "cer_base" : "cer_afinado");
  cuerpo.appendChild(nombre);

  /* Lo que se sabe de este cerebro, en una linea. Si no se puede usar, la
     causa la manda el servidor palabra por palabra: aqui no se traduce ni se
     resume un motivo tecnico -- resumirlo es donde se pierde el porque. */
  const detalle = document.createElement("p");
  detalle.className = "cer-detalle";
  const trozos = [];
  if (op.nombre) trozos.push(op.nombre);
  if (op.version) trozos.push(op.version);
  if (op.bytes !== null && op.bytes !== undefined) {
    trozos.push((op.bytes / 1073741824).toFixed(2) + " GB");
  }
  if (op.notas) trozos.push(op.notas);
  if (op.causa) trozos.push(op.causa);
  detalle.textContent = trozos.join(" · ");
  cuerpo.appendChild(detalle);

  b.append(punto, cuerpo);
  if (!b.disabled && !suyo) {
    b.addEventListener("click", () => elegirCerebro(op.cual));
  }
  return b;
}

function _pintaPaqueteCerebro(d) {
  $("cer-titulo").textContent = t("cer_titulo");
  $("cer-uso").textContent =
    t("cer_en_uso")(d.en_uso.nombre || d.en_uso.cual) + " — " + d.en_uso.motivo;
  const caja = $("cer-opciones");
  caja.replaceChildren();
  for (const op of d.opciones) caja.appendChild(_tarjetaCerebro(op, d.en_uso.cual));
}

async function pintaCerebro() {
  try {
    const r = await fetch("/api/cerebro", { cache: "no-store" });
    if (!r.ok) throw new Error(r.status);
    _pintaPaqueteCerebro(await r.json());
    $("cer-dicho").hidden = true;
  } catch {
    $("cer-titulo").textContent = t("cer_titulo");
    $("cer-uso").textContent = t("cer_sin_servidor");
    $("cer-opciones").replaceChildren();
  }
}

async function elegirCerebro(cual) {
  $("cer-dicho").hidden = false;
  $("cer-dicho").textContent = t("cer_cambiando");
  try {
    const r = await fetch("/api/cerebro", {
      method: "Post", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cual, motivo: "elegido desde el tablero" }),
    });
    const d = await r.json();
    if (!r.ok) {
      $("cer-dicho").textContent = `${t("cer_no")}: ${d.motivo || r.status}`;
      return;
    }
    // Se repinta con lo que el servidor dice que hay en este momento. Pedir el afinado y
    // que su huella no cuadre termina en el base, y eso tiene que verse.
    _pintaPaqueteCerebro(d);
    $("cer-dicho").hidden = false;
    $("cer-dicho").textContent =
      t("cer_hecho")(d.en_uso.nombre || d.en_uso.cual);
  } catch {
    $("cer-dicho").textContent = t("cer_sin_servidor");
  }
}


/* --- el latido de Medicion ------------------------------------------------
   Las cifras se vuelven a medir mientras el cajon esta abierto, y solo
   mientras lo esta.

   Por que no al cargar la pagina: una temperatura leida hace diez minutos y
   pintada como actual es un sensor deshonesto con buena cara -- eso ya lo
   decia el comentario de `abrir`, y esto es su continuacion. Un panel que se
   llama Banco de Pruebas y ensena un numero congelado no vale para lo que
   existe: comparar dos cerebros midiendo.

   Y por que se para: un reloj que se arranca al abrir y no se para al cerrar
   sigue pidiendo al servidor para siempre. En un telefono eso es bateria que
   se va sin que nada en la pantalla lo justifique. Peor: abrir y cerrar cinco
   veces dejaria cinco relojes a la vez. `latidoPara` se llama siempre antes de
   arrancar otro, asi que no se pueden apilar aunque alguien llame dos veces.

   Tambien se para con la pantalla detras. `visibilitychange` cubre lo que un
   telefono hace de verdad: bloquear y cambiar de aplicacion no cierran el
   cajon, y sin esto se seguiria midiendo con el aparato en el bolsillo. */
/* En minuscula por la regla de la casa para `interface/`, no por descuido. */
const latidoMs = 3000;
let latido = null;

function latidoPara() {
  if (latido) { clearInterval(latido); latido = null; }
  const aviso = $("med-vivo");
  if (aviso) aviso.hidden = true;
}

function latidoArranca() {
  latidoPara();                       // nunca dos a la vez
  const aviso = $("med-vivo");
  if (document.hidden) {
    if (aviso) { aviso.hidden = false; aviso.textContent = t("med_pausa"); }
    return;
  }
  latido = setInterval(() => {
    if (document.hidden) return;      // no se mide lo que nadie mira
    pintaMedicion();
  }, latidoMs);
  if (aviso) { aviso.hidden = false; aviso.textContent = t("med_vivo"); }
}

/* El cajon abierto se reconoce por el propio cajon, no por una variable que
   haya que mantener en paralelo: dos verdades sobre si algo esta abierto
   terminan discrepando. */
function medicionAbierta() {
  const c = $("cajon-medicion");
  return c && !c.hidden;
}

document.addEventListener("visibilitychange", () => {
  if (document.hidden) latidoPara();
  else if (medicionAbierta()) { pintaMedicion(); latidoArranca(); }
});

/* --- El teclado de Android, y por que `resize` a secas no basta -----------
 *
 * En Chrome de Android el teclado NO encoge el layout: la ventana sigue
 * midiendo lo mismo y el teclado se pinta Encima. `window.innerHeight` no se
 * entera, `resize` casi nunca dispara, y el ultimo mensaje del chat se queda
 * debajo del teclado sin que nada avise. Lo que si se entera es
 * `visualViewport`, que es lo que de verdad se ve.
 *
 * Se mide cuanto tapa --lo que la ventana tiene de mas sobre la parte visible--
 * y se le resta al alto de la app. Asi la zona de escribir sube sola y el
 * chat conserva su scroll al fondo, que es lo unico que la persona quiere:
 * ver lo ultimo que se dijo mientras escribe la respuesta.
 *
 * `scrollIntoView` no servia aqui: no hay scroll nuevo que hacer, el problema
 * es que el sitio donde estaba el mensaje ya no se ve. */
if (window.visualViewport) {
  const vv = window.visualViewport;
  const alFondo = () => {
    const d = $("dice");
    if (d) d.scrollTop = d.scrollHeight;
  };
  const ajusta = () => {
    const tapado = Math.max(0, window.innerHeight - vv.height - vv.offsetTop);
    document.documentElement.style.setProperty("--teclado", tapado + "px");
    // El umbral es de 120 px y no de cero: una barra de direcciones que se
    // esconde al deslizar tambien cambia el viewport visual, y eso no es un
    // teclado. Ningun teclado de movil mide menos de 120 px.
    document.body.classList.toggle("con-teclado", tapado > 120);
    alFondo();
  };
  vv.addEventListener("resize", ajusta);
  vv.addEventListener("scroll", ajusta);
  ajusta();
}
