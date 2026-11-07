"use strict";
const assert = require("node:assert/strict");
const test = require("node:test");
const K = require("../interface/keep_device.js");

const nav = (persisted, grant, opts = {}) => {
  let state = persisted, asked = 0;
  return { asked: () => asked, storage: {
    persisted: async () => { if (opts.throws) throw new Error("x"); return state; },
    persist: async () => { asked++; if (grant) state = true; return grant; },
  } };
};

test("unsupported browser is NO_DATA with cause, never a fake yes", async () => {
  for (const n of [undefined, {}, { storage: {} }, { storage: { persist: () => true } }]) {
    assert.deepEqual({ ...(await K.keep(n)) }, { estado: "NO_DATA", causa: "storage_persist_unsupported" });
  }
});
test("already persisted does not ask again", async () => {
  const n = nav(true, true);
  assert.equal((await K.keep(n)).estado, "kept");
  assert.equal(n.asked(), 0);
});
test("granted is KEPT only when persisted() agrees", async () => {
  const n = nav(false, true);
  assert.deepEqual({ ...(await K.keep(n)) }, { estado: "kept", ya: false });
  assert.equal(n.asked(), 1);
});
test("declined is NOT_KEPT with cause", async () => {
  assert.deepEqual({ ...(await K.keep(nav(false, false))) }, { estado: "not_kept", causa: "browser_declined" });
});
test("a throwing backend is NO_DATA, never a throw", async () => {
  assert.equal((await K.keep(nav(false, true, { throws: true }))).causa, "storage_persist_failed");
});
test("every verdict has a line; NO_DATA lines carry the cause", () => {
  assert.match(K.line({ estado: "NO_DATA", causa: "storage_persist_unsupported" }), /^NO_DATA: storage_persist_unsupported$/);
  assert.match(K.line({ estado: "kept" }), /^Kept/);
  assert.match(K.line({ estado: "not_kept" }), /^Not kept/);
});
test("a persist() yes that persisted() denies is not KEPT", async () => {
  const liar = { storage: { persisted: async () => false, persist: async () => true } };
  assert.equal((await K.keep(liar)).estado, "not_kept");
});
