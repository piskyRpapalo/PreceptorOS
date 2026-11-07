"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

class Element {
  constructor(id = "", owner = null) {
    this.id = id;
    this.owner = owner;
    this.children = [];
    this.attributes = new Map();
    this.handlers = new Map();
    this.dataset = {};
    this.hidden = false;
    this.textContent = "";
    this._src = "";
  }
  addEventListener(type, handler) {
    if (!this.handlers.has(type)) this.handlers.set(type, []);
    this.handlers.get(type).push(handler);
  }
  async dispatch(type, event = {}) {
    for (const handler of this.handlers.get(type) || []) await handler({
      target: this, preventDefault() {}, ...event,
    });
  }
  setAttribute(name, value) { this.attributes.set(name, String(value)); }
  getAttribute(name) { return this.attributes.get(name) ?? null; }
  removeAttribute(name) {
    this.attributes.delete(name);
    if (name === "src") this._src = "";
  }
  hasAttribute(name) { return this.attributes.has(name); }
  set src(value) { this._src = String(value); this.attributes.set("src", this._src); }
  get src() { return this._src; }
  appendChild(child) { this.children.push(child); return child; }
  replaceChildren(...children) { this.children = children; }
  focus() { if (this.owner) this.owner.activeElement = this; }
  contains(target) {
    return target === this || this.children.some((child) => child.contains(target));
  }
}

class Document {
  constructor() {
    this.elements = new Map();
    this.handlers = new Map();
    this.activeElement = null;
    for (const id of ["modelos-toggle", "modelos-menu", "modelos-estado", "modelos-lista",
      "modelo-activo", "openworld-frame", "openworld-status", "openworld-retry"]) {
      this.elements.set(id, new Element(id, this));
    }
    this.elements.get("modelos-menu").hidden = true;
    this.elements.get("openworld-frame").hidden = true;
    this.elements.get("openworld-retry").hidden = true;
  }
  getElementById(id) { return this.elements.get(id); }
  createElement() { return new Element("", this); }
  addEventListener(type, handler) {
    if (!this.handlers.has(type)) this.handlers.set(type, []);
    this.handlers.get(type).push(handler);
  }
  async dispatch(type, event = {}) {
    for (const handler of this.handlers.get(type) || []) await handler(event);
  }
}

function texts() {
  return {
    world_idle: "idle", world_checking: "checking", world_loading: "loading",
    world_loaded: "frame navigation ended; cross-origin HTTP status unreadable",
    world_frame_title: "OpenWorld frame", modelos_cargando: "checking models",
    lab_actualizado: "updated", lab_mini: "mini", lab_grande: "large",
    lab_soberano_coder: "coder", modelos_tier1: "tier one", modelos_tier2: "tier two",
    modelos_adaptador: "adapter", modelos_live: "live", modelos_stale: "stale",
    modelos_ausente: "unavailable", modelos_causa: "cause", modelos_causa_vacia: "none",
    model_last_reply: "last model that replied",
  };
}

function setup(fetcher) {
  global.window = {};
  delete require.cache[require.resolve("../interface/modelos_web.js")];
  require("../interface/modelos_web.js");
  const document = new Document();
  const timers = new Map();
  let timerId = 0;
  const window = {
    AbortController,
    setTimeout(callback) { const id = ++timerId; timers.set(id, callback); return id; },
    clearTimeout(id) { timers.delete(id); },
    runTimers() { for (const [id, callback] of [...timers]) { timers.delete(id); callback(); } },
  };
  const api = global.window.PreceptorModelosWeb.mount({
    document, window, getText: texts, fetcher,
  });
  return { document, window, api, timers };
}

const validModels = {
  mini: { tag: "qwen3:1.7b", estado: "MEDIDO", disponible: true },
  grande: { tag: "hexelion:latest", estado: "MEDIDO", disponible: true },
  soberano_coder: { tag: "coder-local", estado: "STALE", causa: "measurement_old" },
  eleccion: {
    tier1: { modelo: "rules:select", estado: "MEDIDO" },
    tier2: { estado: "NO_DATA", causa: "not_configured" },
    adaptador: { estado: "NO_DATA", causa: "adapter_absent" },
  },
};

test("mount makes no requests and leaves the external frame without src", () => {
  let calls = 0;
  const { document, api } = setup(async () => { calls++; throw new Error("unexpected"); });
  assert.equal(calls, 0);
  assert.equal(document.getElementById("openworld-frame").hasAttribute("src"), false);
  assert.equal(api.state(), "idle");
});

test("catalog contract failure is NO_DATA and clears all rows", async () => {
  const { document, api } = setup(async () => ({ ok: true, json: async () => ({ modelos: { mini: "lie" } }) }));
  await api.toggleCatalog();
  assert.equal(document.getElementById("modelos-lista").children.length, 0);
  assert.match(document.getElementById("modelos-estado").textContent, /NO_DATA: model_catalog_contract_invalid/);
});

test("measured model catalogue displays causes and Escape restores focus", async () => {
  const { document, api } = setup(async (url) => {
    assert.equal(url, "/api/lab");
    return { ok: true, json: async () => ({ modelos: validModels }) };
  });
  await api.toggleCatalog();
  const list = document.getElementById("modelos-lista");
  assert.equal(list.children.length, 6);
  assert.match(list.children[2].textContent + list.children[2].children.map((x) => x.textContent).join(" "), /measurement_old/);
  assert.match(list.children[3].children[1].textContent, /live/);
  api.setActiveModel("hexelion:latest", 2300);
  assert.match(document.getElementById("modelo-activo").textContent, /hexelion:latest.*2300 ms/);
  await document.dispatch("keydown", { key: "Escape", preventDefault() {} });
  assert.equal(document.getElementById("modelos-menu").hidden, true);
  assert.equal(document.getElementById("modelos-toggle").getAttribute("aria-expanded"), "false");
  assert.equal(document.activeElement, document.getElementById("modelos-toggle"));
});

test("offline probe reports a cause and never assigns the frame URL", async () => {
  const { document, api } = setup(async () => { throw new TypeError("offline"); });
  await api.openWorld();
  assert.equal(api.state(), "failed");
  assert.equal(document.getElementById("openworld-frame").hasAttribute("src"), false);
  assert.equal(document.getElementById("openworld-retry").hidden, false);
  assert.match(document.getElementById("openworld-status").textContent, /NO_DATA: openworld_unreachable/);
});

test("a frame that never completes fails closed and removes its URL", async () => {
  const { document, window, api } = setup(async () => ({ type: "opaque", ok: false }));
  await api.openWorld();
  const frame = document.getElementById("openworld-frame");
  assert.equal(frame.src, "https://preceptoros.org/openworld/");
  window.runTimers();
  assert.equal(api.state(), "failed");
  assert.equal(frame.hasAttribute("src"), false);
  assert.match(document.getElementById("openworld-status").textContent, /NO_DATA: iframe_load_timeout/);
});

test("frame load only reports navigation completion, not cross-origin HTTP status", async () => {
  const { document, api } = setup(async () => ({ type: "opaque", ok: false }));
  await api.openWorld();
  await document.getElementById("openworld-frame").dispatch("load");
  assert.equal(api.state(), "loaded");
  assert.match(document.getElementById("openworld-status").textContent, /HTTP status unreadable/);
});

// Measured 2026-11-07 in Chromium (420x680 window): fetch(url, {mode: "no-cors", redirect: "error"})
// throws before any network ("Request mode is \"no-cors\" but the redirect mode is not \"follow\""),
// so the World tab was NO_DATA: openworld_unreachable even with the site answering 200. The fake
// fetcher now enforces that Fetch-standard rule, so the probe can never pass a test it fails live.
test("probe init is legal under the Fetch standard and an opaque answer loads the frame", async () => {
  const seen = [];
  const { document, api } = setup(async (url, init) => {
    seen.push(init);
    if (init.mode === "no-cors" && init.redirect !== "follow") {
      throw new TypeError('Request mode is "no-cors" but the redirect mode is not "follow"');
    }
    return { type: "opaque", ok: false };
  });
  await api.openWorld();
  assert.equal(seen.length, 1);
  assert.equal(seen[0].credentials, "omit");
  assert.equal(api.state(), "loading");
  assert.equal(document.getElementById("openworld-frame").getAttribute("src"), "https://preceptoros.org/openworld/");
});
