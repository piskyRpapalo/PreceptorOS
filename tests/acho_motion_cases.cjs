// Cases for interface/acho_motion.js: one deterministic Acho math for every option.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const fuente = fs.readFileSync(path.join(__dirname, "..", "interface", "acho_motion.js"), "utf8");
function load(reduced) {
  const ctx = { document: null, matchMedia: () => ({ matches: !!reduced }) };
  ctx.window = ctx; vm.createContext(ctx); vm.runInContext(fuente, ctx); return ctx.AchoMotion;
}
const A = load(false);

test("same name, same curve and colour across fresh loads (n=2)", () => {
  const B = load(false);
  assert.equal(A.path(A.vector("lab|Retry")), B.path(B.vector("lab|Retry")));
  assert.equal(A.colourOf("lab|Retry"), B.colourOf("lab|Retry"));
});
test("different options draw different curves", () => {
  assert.notEqual(A.path(A.vector("a")), A.path(A.vector("b")));
});
test("an explicit form fixes the amplitudes; the name only moves the phase", () => {
  const a = A.vector("x", "easy"), b = A.vector("y", "easy");
  assert.equal(JSON.stringify(a.map((h) => [h.ax, h.ay])), JSON.stringify(b.map((h) => [h.ax, h.ay])));
  assert.notEqual(JSON.stringify(a.map((h) => h.phi)), JSON.stringify(b.map((h) => h.phi)));
});
test("vectors follow the house transition contract (k = 1, 2, 3, finite)", () => {
  const v = A.vector("tab|tab-lab");
  assert.equal(JSON.stringify(v.map((h) => h.k)), "[1,2,3]");
  for (const h of v) for (const n of [h.ax, h.ay, h.phi]) assert.ok(Number.isFinite(n));
});
test("every palette colour sounds inside 220-880 Hz", () => {
  for (const c of Object.keys(A.colours)) { const hz = A.tone(c); assert.ok(hz >= 220 && hz <= 880, c + " " + hz); }
});
test("reduced motion: the gesture never animates", () => {
  let called = 0; const node = { animate: () => { called++; } };
  load(true).gesture(node, A.vector("z"), "touch", 0);
  assert.equal(called, 0);
  A.gesture(node, A.vector("z"), "touch", 0);
  assert.equal(called, 1);
});
test("the gesture starts and ends at rest (no drift)", () => {
  let frames = null; A.gesture({ animate: (k) => { frames = k; } }, A.vector("z"), "touch", 0);
  assert.equal(frames[0].transform, "translate(0px, 0px)");
  assert.equal(frames[frames.length - 1].transform, "translate(0px, 0px)");
});
test("no randomness, no clock, no network", () => {
  assert.doesNotMatch(fuente, /Math\.random|Date\.now|new Date|performance\.now|fetch\(|XMLHttpRequest/);
});
