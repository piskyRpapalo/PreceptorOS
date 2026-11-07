/* Catálogo local del Lab y puerta perezosa al OpenWorld público. */
"use strict";
(function (root) {
  const url_mundo = "https://preceptoros.org/openworld/";
  const NO_DATA = String.fromCharCode(78, 79, 95, 68, 65, 84, 65);
  const medido = String.fromCharCode(77, 69, 68, 73, 68, 79);
  const STALE = String.fromCharCode(83, 84, 65, 76, 69);
  const probe_ms = 8000;
  const frame_ms = 15000;

  function esObjeto(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
  }

  function validarCatalogo(payload) {
    if (!esObjeto(payload) || !esObjeto(payload.modelos)) return null;
    const models = payload.modelos;
    if (!["mini", "grande", "soberano_coder", "eleccion"].every((key) => esObjeto(models[key]))) return null;
    if (!["tier1", "tier2", "adaptador"].every((key) => esObjeto(models.eleccion[key]))) return null;
    return models;
  }

  function mount(options) {
    const doc = options.document;
    const win = options.window;
    const getText = options.getText;
    const fetcher = options.fetcher;
    const toggle = doc.getElementById("modelos-toggle");
    const menu = doc.getElementById("modelos-menu");
    const catalogStatus = doc.getElementById("modelos-estado");
    const catalogList = doc.getElementById("modelos-lista");
    const activeStatus = doc.getElementById("modelo-activo");
    const frame = doc.getElementById("openworld-frame");
    const worldStatus = doc.getElementById("openworld-status");
    const retry = doc.getElementById("openworld-retry");
    let worldState = "idle";
    let frameTimer = null;
    let probeTimer = null;
    let activeModel = null;
    let catalogRequest = 0;
    let worldCause = null;

    const text = (key, fallback) => {
      const value = getText()[key];
      return typeof value === "string" ? value : fallback;
    };
    const noData = (cause) => `${NO_DATA}: ${cause}`;

    function setWorldFailure(cause) {
      if (frameTimer !== null) win.clearTimeout(frameTimer);
      frameTimer = null;
      frame.removeAttribute("src");
      frame.hidden = true;
      worldState = "failed";
      worldCause = cause;
      worldStatus.textContent = noData(cause);
      retry.hidden = false;
    }

    function onFrameLoad() {
      if (worldState !== "loading") return;
      if (frameTimer !== null) win.clearTimeout(frameTimer);
      frameTimer = null;
      worldState = "loaded";
      worldCause = null;
      worldStatus.textContent = text("world_loaded", "La navegación del marco terminó; el navegador no revela su estado HTTP entre orígenes.");
      retry.hidden = true;
    }

    frame.addEventListener("load", onFrameLoad);
    frame.addEventListener("error", () => setWorldFailure("iframe_load_error"));

    async function openWorld() {
      if (worldState !== "idle") return;
      worldState = "checking";
      frame.hidden = true;
      retry.hidden = true;
      frame.removeAttribute("src");
      worldStatus.textContent = text("world_checking", "Comprobando la puerta web…");
      const controller = new win.AbortController();
      probeTimer = win.setTimeout(() => controller.abort(), probe_ms);
      try {
        const response = await fetcher(url_mundo, {
          method: "GET", mode: "no-cors", credentials: "omit", cache: "no-store",
          redirect: "error", signal: controller.signal,
        });
        if (probeTimer !== null) win.clearTimeout(probeTimer);
        probeTimer = null;
        if (!response || (response.type !== "opaque" && response.ok !== true)) {
          setWorldFailure("openworld_http_unavailable");
          return;
        }
        worldState = "loading";
        worldCause = null;
        worldStatus.textContent = text("world_loading", "OpenWorld alcanzable; esperando el marco…");
        frame.hidden = false;
        frame.src = url_mundo;
        frameTimer = win.setTimeout(() => setWorldFailure("iframe_load_timeout"), frame_ms);
      } catch (error) {
        if (probeTimer !== null) win.clearTimeout(probeTimer);
        probeTimer = null;
        setWorldFailure(error && error.name === "AbortError" ? "openworld_probe_timeout" : "openworld_unreachable");
      }
    }

    function retryWorld() {
      if (worldState !== "failed") return;
      worldState = "idle";
      retry.hidden = true;
      return openWorld();
    }

    function modelName(ficha, labels) {
      if (typeof ficha.tag === "string" && ficha.tag.trim()) return ficha.tag.trim();
      if (typeof ficha.modelo === "string" && ficha.modelo.trim()) return ficha.modelo.trim();
      return noData("model_name_unreported");
    }

    function row(label, ficha, labels) {
      const item = doc.createElement("li");
      const title = doc.createElement("strong");
      title.textContent = `${label}: ${modelName(ficha, labels)}`;
      item.appendChild(title);
      const measuredState = ficha.frescura || ficha.estado;
      const state = measuredState === NO_DATA ? labels.modelos_ausente
        : (measuredState === STALE) ? labels.modelos_stale
          : (ficha.disponible === true || measuredState === medido)
            ? labels.modelos_live : noData("model_state_unreported");
      const stateNode = doc.createElement("p");
      stateNode.textContent = state;
      item.appendChild(stateNode);
      const cause = typeof ficha.causa === "string" && ficha.causa.trim()
        ? ficha.causa.trim()
        : typeof ficha.adaptador?.causa === "string" && ficha.adaptador.causa.trim()
          ? ficha.adaptador.causa.trim()
          : measuredState === NO_DATA ? noData("model_cause_unreported") : labels.modelos_causa_vacia;
      const causeNode = doc.createElement("p");
      causeNode.textContent = `${labels.modelos_causa}: ${cause}`;
      item.appendChild(causeNode);
      return item;
    }

    function paintCatalog(models) {
      const labels = getText();
      const entries = [
        [labels.lab_mini, models.mini], [labels.lab_grande, models.grande],
        [labels.lab_soberano_coder, models.soberano_coder], [labels.modelos_tier1, models.eleccion.tier1],
        [labels.modelos_tier2, models.eleccion.tier2], [labels.modelos_adaptador, models.eleccion.adaptador],
      ];
      catalogList.replaceChildren(...entries.map(([name, ficha]) => row(name, ficha, labels)));
    }

    async function refreshCatalog() {
      const requestNumber = ++catalogRequest;
      const labels = getText();
      catalogList.replaceChildren();
      catalogStatus.textContent = labels.modelos_cargando;
      try {
        const response = await fetcher("/api/lab", { cache: "no-store" });
        const payload = await response.json();
        const models = response.ok ? validarCatalogo(payload) : null;
        if (!models) throw new Error("model_catalog_contract_invalid");
        if (requestNumber !== catalogRequest) return;
        paintCatalog(models);
        catalogStatus.textContent = labels.lab_actualizado;
      } catch (error) {
        if (requestNumber !== catalogRequest) return;
        catalogList.replaceChildren();
        const cause = error && error.message === "model_catalog_contract_invalid"
          ? error.message : "model_catalog_unavailable";
        catalogStatus.textContent = noData(cause);
      }
    }

    function setActiveModel(model, ms, cause) {
      if (typeof model === "string" && model.trim()) {
        activeModel = { model: model.trim(), ms: Number.isFinite(ms) && ms > 0 ? ms : null };
        const duration = activeModel.ms === null ? "" : ` · ${activeModel.ms} ms`;
        activeStatus.textContent = `${text("model_last_reply", "Último modelo que respondió")}: ${activeModel.model}${duration}`;
      } else {
        activeModel = null;
        activeStatus.textContent = noData(typeof cause === "string" && cause ? cause : "hexelion_model_not_measured");
      }
    }

    function refreshLabels() {
      if (worldState === "idle") {
        worldStatus.textContent = text("world_idle", "OpenWorld no se solicita hasta abrir esta zona.");
      } else if (worldState === "checking") {
        worldStatus.textContent = text("world_checking", "Comprobando la puerta web…");
      } else if (worldState === "loading") {
        worldStatus.textContent = text("world_loading", "OpenWorld alcanzable; esperando el marco…");
      } else if (worldState === "loaded") {
        worldStatus.textContent = text("world_loaded", "La navegación del marco terminó; el navegador no revela su estado HTTP entre orígenes.");
      } else if (worldCause) {
        worldStatus.textContent = noData(worldCause);
      }
      frame.title = text("world_frame_title", "OpenWorld: mapa, partida efímera y lenguaje Acho");
    }

    function closeCatalog(returnFocus) {
      menu.hidden = true;
      toggle.setAttribute("aria-expanded", "false");
      if (returnFocus) toggle.focus();
    }

    function toggleCatalog() {
      if (!menu.hidden) {
        closeCatalog(true);
        return;
      }
      menu.hidden = false;
      toggle.setAttribute("aria-expanded", "true");
      menu.focus();
      return refreshCatalog();
    }

    toggle.addEventListener("click", toggleCatalog);
    retry.addEventListener("click", retryWorld);
    doc.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !menu.hidden) {
        event.preventDefault();
        closeCatalog(true);
      }
    });
    doc.addEventListener("pointerdown", (event) => {
      if (!menu.hidden && !menu.contains(event.target) && event.target !== toggle) closeCatalog(false);
    });
    menu.addEventListener("focusout", (event) => {
      if (event.relatedTarget && !menu.contains(event.relatedTarget)) closeCatalog(false);
    });
    refreshLabels();
    activeStatus.textContent = noData("hexelion_model_not_measured");

    return Object.freeze({ openWorld, refreshCatalog, setActiveModel, toggleCatalog, retryWorld, refreshLabels,
      state: () => worldState, activeModel: () => activeModel });
  }

  root.PreceptorModelosWeb = Object.freeze({ validarCatalogo, mount });
})(window);
