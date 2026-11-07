// Cases for interface/equipo.js: the team spectra are deterministic Acho curves.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const fuente = fs.readFileSync(path.join(__dirname, "..", "interface", "equipo.js"), "utf8");
function cargar() {
  const ctx = { document: { documentElement: { lang: "es" }, getElementById: () => null }, matchMedia: () => ({ matches: false }) };
  ctx.window = ctx; vm.createContext(ctx); vm.runInContext(fuente, ctx); return ctx.PreceptorEquipo;
}
const E = cargar();
const tips = { id: "tips", form: "tips", ask: "", color: "sun" };

test("same agent, same curve (n=2, two fresh loads)", () => {
  assert.equal(E.camino(E.vector(tips)), cargar().camino(cargar().vector(tips)));
});
test("the form shapes the curve and the id moves its phase", () => {
  assert.notEqual(E.camino(E.vector(tips)), E.camino(E.vector({ ...tips, form: "easy" })));
  assert.notEqual(E.camino(E.vector(tips)), E.camino(E.vector({ ...tips, id: "otro" })));
});
test("the harmonic vector is the house transition contract (k = 1, 2, 3)", () => {
  assert.equal(JSON.stringify(E.vector(tips).map((h) => h.k)), "[1,2,3]");
  for (const h of E.vector(tips)) for (const v of [h.ax, h.ay, h.phi]) assert.ok(Number.isFinite(v));
});
test("tone by colour stays inside 220–880 Hz", () => {
  for (const c of ["sea", "blue", "grass", "sand", "clay", "sun", "sky", "moss"]) {
    const hz = E.tono(c); assert.ok(hz >= 220 && hz <= 880, c + " " + hz);
  }
});
test("no randomness, no wall clock, no network beyond the local team routes", () => {
  assert.doesNotMatch(fuente, /Math\.random|Date\.now|new Date|performance\.now/);
  const urls = fuente.match(/fetch\("([^"]+)"/g) || [];
  assert.ok(urls.length > 0 && urls.every((u) => u.includes('"/api/equipo')), urls.join(","));
});
test("every spectrum declares its sound and an Acho reading of NO_DATA with cause", () => {
  assert.match(fuente, /dataset\.sonido/);
  assert.match(fuente, /dataset\.achoLectura = nd/);
  assert.match(fuente, /acho_reader_not_trained/);
});
test("reduced motion is honoured by morph and gesture", () => {
  assert.match(fuente, /prefers-reduced-motion: reduce/);
  assert.ok((fuente.match(/quieto\(\)/g) || []).length >= 2);
});
