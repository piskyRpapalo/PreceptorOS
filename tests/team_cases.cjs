// Cases for interface/team.js: the team spectra are deterministic Acho curves.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const fuente = fs.readFileSync(path.join(__dirname, "..", "interface", "team.js"), "utf8");
const motor = fs.readFileSync(path.join(__dirname, "..", "interface", "acho_motion.js"), "utf8");
function cargarModulo() {
  const ctx = { document: { documentElement: { lang: "es" }, getElementById: () => null }, matchMedia: () => ({ matches: false }) };
  ctx.window = ctx; vm.createContext(ctx); vm.runInContext(motor, ctx); vm.runInContext(fuente, ctx); return ctx.PreceptorTeam;
}
const E = cargarModulo();
const tips = { id: "tips", form: "tips", ask: "", color: "sun" };

test("same agent, same curve (n=2, two fresh loads)", () => {
  assert.equal(E.path(E.vector(tips)), cargarModulo().path(cargarModulo().vector(tips)));
});
test("the form shapes the curve and the id moves its phase", () => {
  assert.notEqual(E.path(E.vector(tips)), E.path(E.vector({ ...tips, form: "easy" })));
  assert.notEqual(E.path(E.vector(tips)), E.path(E.vector({ ...tips, id: "otro" })));
});
test("the harmonic vector is the house transition contract (k = 1, 2, 3)", () => {
  assert.equal(JSON.stringify(E.vector(tips).map((h) => h.k)), "[1,2,3]");
  for (const h of E.vector(tips)) for (const v of [h.ax, h.ay, h.phi]) assert.ok(Number.isFinite(v));
});
test("tone by colour stays inside 220–880 Hz", () => {
  for (const c of ["sea", "blue", "grass", "sand", "clay", "sun", "sky", "moss"]) {
    const hz = E.tone(c); assert.ok(hz >= 220 && hz <= 880, c + " " + hz);
  }
});
test("no randomness, no wall clock, no network beyond the local team routes", () => {
  for (const src of [fuente, motor]) assert.doesNotMatch(src, /Math\.random|Date\.now|new Date|performance\.now/);
  const urls = fuente.match(/fetch\("([^"]+)"/g) || [];
  assert.ok(urls.length > 0 && urls.every((u) => u.includes('"/api/team')), urls.join(","));
});
test("every spectrum declares its sound and an Acho reading of NO_DATA with cause", () => {
  assert.match(motor, /dataset\.sonido/);
  assert.match(motor, /dataset\.achoLectura = nd/);
  assert.match(motor, /acho_reader_not_trained/);
});
test("reduced motion is honoured by morph and gesture", () => {
  assert.match(motor, /prefers-reduced-motion: reduce/);
  assert.ok((motor.match(/still\(\)/g) || []).length >= 2);
});
