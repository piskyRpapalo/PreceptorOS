// Cases for the 3DFabrika core inside interface/app.js: one state, three readers, nothing claimed that was not built.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const app = fs.readFileSync(path.join(__dirname, "..", "interface", "app.js"), "utf8");
const from = app.indexOf("/* <fabrika3d>"), to = app.indexOf("/* </fabrika3d> */");
assert.ok(from > 0 && to > from, "the core is marked in app.js");
function core() {
  const ctx = {}; vm.createContext(ctx);
  vm.runInContext(app.slice(from, to) + "\nthis.F = PreceptorFabrika;", ctx);
  return ctx.F;
}
const F = core();
const hook = { description: "  A wall hook for a\nbicycle helmet ", width: "40", depth: "", height: "60.04" };
const plain = (x) => JSON.parse(JSON.stringify(x));

test("the core touches no clock, network, storage or random numbers", () => {
  assert.equal(/Date\.|Math\.random|fetch\(|localStorage|XMLHttpRequest|document\.|window\./.test(app.slice(from, to)), false);
});
test("a valid request is cleaned, not changed: spaces folded, sizes to a tenth of a millimetre", () => {
  assert.deepEqual(plain(F.validate(hook)), { ok: true, description: "A wall hook for a bicycle helmet", size: { width: 40, depth: null, height: 60 } });
});
test("each mistake names the field to fix and how", () => {
  const cases = [
    [{ description: "   " }, "fab-desc", /Write what part you need/],
    [{ description: "x".repeat(401) }, "fab-desc", /too long/],
    [{ description: "a nut", width: "0" }, "fab-ancho", /Width must be a number between 1 and 300/],
    [{ description: "a nut", depth: "301" }, "fab-fondo", /Depth must be/],
    [{ description: "a nut", height: "tall" }, "fab-alto", /Height must be/],
    [{ description: "a nut", width: "Infinity" }, "fab-ancho", /Width must be/],
    [undefined, "fab-desc", /Write what part/],
  ];
  for (const [input, field, error] of cases) {
    const v = F.validate(input);
    assert.equal(v.ok, false); assert.equal(v.field, field); assert.match(v.error, error);
  }
});
test("creating a project selects it and gives it the next id; a mistake leaves the state untouched", () => {
  const a = F.create(F.empty(), hook);
  assert.equal(a.error, null);
  assert.deepEqual([a.state.projects.length, a.state.selected, a.state.next], [1, "p1", 2]);
  const b = F.create(a.state, { description: "" });
  assert.equal(b.state, a.state); assert.equal(b.error.field, "fab-desc");
  const c = F.create(a.state, { description: "a washer" });
  assert.deepEqual(plain(c.state.projects.map((p) => p.id)), ["p1", "p2"]);
});
test("the device keeps at most twelve projects and says how to make room", () => {
  let s = F.empty();
  for (let i = 0; i < F.MAX; i++) s = F.create(s, { description: "part " + i }).state;
  const full = F.create(s, { description: "one more" });
  assert.equal(full.state.projects.length, F.MAX); assert.match(full.error.error, /Remove one to make room/);
});
test("only the request is done; every later stage is NO_DATA with its cause", () => {
  const stages = plain(F.stages());
  assert.deepEqual(stages.map((e) => e.id), ["request", "shape", "file", "check", "verdict"]);
  assert.deepEqual(stages[0], { id: "request", name: "Request written", state: "DONE", cause: "" });
  for (const e of stages.slice(1)) { assert.equal(e.state, "NO_DATA"); assert.ok(e.cause.length > 0, e.id); }
  assert.equal(F.ENGINE.state, "NO_DATA");
});
test("the request is the exact line the existing engine takes, and cannot break out of its quotes", () => {
  const s = F.create(F.empty(), hook).state;
  assert.equal(F.request(F.chosen(s)), 'textcad "A wall hook for a bicycle helmet, 40 mm width, 60 mm height"');
  const sly = F.create(F.empty(), { description: 'a nut"; rm -rf ~ `id` $HOME \\' }).state;
  assert.equal(/["`$\\]/.test(F.request(F.chosen(sly)).slice(9, -1)), false);
});
test("eye, ear and machine get the same sentence, and it never says the part is built", () => {
  const none = F.empty();
  assert.equal(F.machine(none).line, F.line(none));
  assert.match(F.line(none), /no project selected/); assert.match(F.line(none), /not connected/);
  const s = F.create(F.create(F.empty(), hook).state, { description: "a washer" }).state;
  const m = plain(F.machine(s));
  assert.equal(m.line, F.line(s));
  assert.match(m.line, /^Project 2 of 2: a washer\. The request is written; the part is not built\./);
  assert.equal(m.selected, "p2"); assert.equal(m.schema, "preceptoros.fabrika3d/1");
  assert.deepEqual(m.print, { state: "NO_DATA", cause: "no_printable_file" });
  assert.deepEqual(m.engine, { state: "NO_DATA", cause: "engine_not_connected_to_this_app" });
  assert.equal(/\bLIVE\b|\bREADY\b|\bprinted\b|is ready to print/.test(JSON.stringify(m)), false);
  assert.match(F.printState(F.chosen(s)), /^NO_DATA: this project has no printable file yet/);
  assert.match(F.printState(null), /^NO_DATA: no project is selected/);
});
test("removing a project can be undone, and puts it back where it was", () => {
  let s = F.empty();
  for (const d of ["first", "second", "third"]) s = F.create(s, { description: d }).state;
  s = F.select(s, "p2");
  const gone = F.remove(s, "p2");
  assert.deepEqual(plain(gone.projects.map((p) => p.id)), ["p1", "p3"]); assert.equal(gone.selected, "p3");
  const back = F.undo(gone);
  assert.deepEqual(plain(back.projects.map((p) => p.id)), ["p1", "p2", "p3"]); assert.equal(back.selected, "p2"); assert.equal(back.removed, null);
  assert.equal(F.undo(back), back);
  assert.equal(F.remove(s, "nope"), s); assert.equal(F.select(s, "nope"), s);
});
test("what the browser kept is read back whole or not at all", () => {
  let s = F.create(F.create(F.empty(), hook).state, { description: "a washer" }).state;
  const again = F.load(F.dump(s));
  assert.deepEqual(plain(again.projects), plain(s.projects)); assert.equal(again.selected, "p2"); assert.equal(again.next, 3);
  assert.equal(F.dump(F.load(F.dump(s))), F.dump(s));
  const bad = ["", "not json", "{}", JSON.stringify({ schema: F.SCHEMA, next: 0, projects: [] }),
    JSON.stringify({ schema: "other/1", next: 1, projects: [] }),
    JSON.stringify({ schema: F.SCHEMA, next: 3, projects: [{ id: "p1", description: "", size: {} }] }),
    JSON.stringify({ schema: F.SCHEMA, next: 3, projects: [{ id: "x1", description: "a nut", size: {} }] }),
    JSON.stringify({ schema: F.SCHEMA, next: 3, projects: [{ id: "p1", description: "a nut", size: { width: 9000 } }] }),
    JSON.stringify({ schema: F.SCHEMA, next: 3, projects: [{ id: "p1", description: "a" }, { id: "p1", description: "b" }] })];
  for (const text of bad) assert.deepEqual(plain(F.load(text)), plain(F.empty()), text.slice(0, 40));
  const low = F.load(JSON.stringify({ schema: F.SCHEMA, next: 1, selected: "gone", projects: [{ id: "p7", description: "a nut", size: {} }] }));
  assert.equal(low.next, 8); assert.equal(low.selected, "p7");
});
test("two fresh loads of the core give the same answers", () => {
  const G = core(), a = F.create(F.empty(), hook).state, b = G.create(G.empty(), hook).state;
  assert.equal(JSON.stringify(F.machine(a)), JSON.stringify(G.machine(b)));
});
