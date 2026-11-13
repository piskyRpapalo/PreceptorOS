// Evidence chip cases (UI-COHERENCE-01 P3). Run: node tests/evidence_chip_cases.cjs
// The chip shows a state; it never decides one. Every visible word is English (the MVP freeze).
const assert = require("assert");
const E = require("../interface/evidence_chip.js");
const visibles = new Set();
for (const [entrada, esperado] of [
  ["VERIFIED", "VERIFIED"], ["OBSERVED", "OBSERVED"], ["MEDIDO", "OBSERVED"], ["DECLARADO", "DECLARED"],
  ["DECLARED", "DECLARED"], ["STALE", "STALE"], ["NO_DATA", "NO DATA"], ["no data", "NO DATA"],
  ["DENEGADO", "REFUSED"], ["REFUSED", "REFUSED"],
]) {
  assert.strictEqual(E.text(entrada), esperado, "estado " + entrada);
  visibles.add(esperado);
}
// Unknown or hostile input is NO_DATA, never a guess and never raw text on screen.
assert.strictEqual(E.normal("<script>"), "NO_DATA");
assert.strictEqual(E.normal(undefined), "NO_DATA");
assert.strictEqual(E.text("STALE", "lab_federated_not_on_ref"), "STALE · lab federated not on ref");
assert.ok(E.text("NO_DATA", "x".repeat(300)).length <= 9 + 3 + 80, "la causa se recorta");
// Every label reads in English: no Spanish state words leak into what a person hears.
for (const v of visibles) assert.ok(!/MEDIDO|DECLARADO|DENEGADO|SIN DATOS/.test(v), "palabra en espanol: " + v);
// Each state has a distinct shape, so colour is never the only signal.
const formas = new Set(Object.values(E.table).map((t) => t.glyph));
assert.ok(formas.size >= 5, "formas distintas: " + formas.size);
console.log(JSON.stringify({ schema: "preceptoros.evidence-chip-cases/1", casos: visibles.size, formas: formas.size, ok: true }));
