"use strict";
const assert = require("node:assert/strict");
const N = require("../interface/notebook.js");

const receipt = "a".repeat(64);
const fixture = {
  schema: "preceptoros.notebook-readonly/0",
  agents_status: "DECLARADO",
  agents_cause: null,
  agents: [{ id: "claude-1", name: "Claude", role: "Builder",
             status: "OBSERVADO", cause: "recent_declared_heartbeat",
             last_seen: "2026-11-11T10:00:00Z", receipt_sha256: receipt }],
  reports: [{ kind: "WBR", status: "DECLARADO",
              summary: "1 tested PR", period: "2026-W46",
              measured_at: "2026-11-11T10:00:00Z", receipt_sha256: receipt,
              cause: "origin_receipt_not_independently_verified" }]
};
const state = N.projectNotebook(fixture);
assert.equal(state.agents[0].status, "OBSERVADO");
assert.equal(state.reports[0].status, "DECLARADO");
assert.equal(state.reports[0].summary, "1 tested PR");
assert.equal(N.projectNotebook({ agents: [], reports: [] }), null);
assert.equal(N.projectNotebook({ ...fixture, agents: [{ ...fixture.agents[0], status: "LIVE" }] }).agents[0].status, "NO_DATA");

const now = Date.parse("2026-11-11T10:00:00Z");
const fresh = N.projectHarness({
  estado: "MEDIDO", medido: "2026-11-11T09:59:50Z",
  bucles: [{ unidad: "weekly", ultima: "yesterday", proxima: "tomorrow" }]
}, now);
assert.equal(fresh.rows.length, 1);
const stale = N.projectHarness({
  estado: "MEDIDO", medido: "2026-11-11T08:30:00Z", bucles: [{ unidad: "weekly" }]
}, now);
assert.equal(stale.rows.length, 0);
assert.equal(stale.cause, "sensor_stale_or_missing");
assert.equal(N.projectHarness(null, now).cause, "sensor_invalid");
console.log("notebook_cases: OK (schema, status, loop freshness, fail-closed)");
