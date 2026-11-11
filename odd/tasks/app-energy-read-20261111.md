# APP-ENERGY-01 · Hexelion can read the local energy gap

**Agent:** Codex · GPT-6. **Authority:** Sovereign commissioned APP + local brain, 2026-11-11. **Mode:** BUILD on branch, HITL merge; no switch, battery control or systemd mutation. **Canonical source:** `AGENTS.md`, [energy assessment in buzon#61](https://github.com/piskyRpapalo/buzon/issues/61), `metricas.py:_consumo_w`, [LAB ENERGY_BUDGET](https://github.com/piskyRpapalo/lab/blob/main/ENERGY_BUDGET.md), `p0x/hexelion/laboratorio/colocacion.json`.

## Problem and anti-duplication

The app already contains a Tasmota/Nous A1T meter reader (`metricas._consumo_w`), but no local energy API or mini-HTML view. The model has no callable current-energy observation tool. Earlier direct rack samples exposed a physical inconsistency: the plug returned roughly 114 W while voltage was 35 V and current 0.96 A at declared power factor 1.0. Those fields cannot justify an energy budget. `solar-cadence` describes policy, not operational solar dispatch. CineK is independent and is not changed.

## This slice

1. Reuse `metricas._consumo_w`; require finite nonnegative Power, Voltage, Current, Factor and electrical consistency before reporting a measured watt value. A bad, incomplete, or unreachable reading remains `NO_DATA(cause)`, not a zero.
2. `energia_estado.py` projects the single reading into `preceptoros.energy-read/1`: meter, battery, solar input and allocation, with a timestamp, read-only flag, and one deterministic text sentence. Private endpoint identifiers and exception strings never enter the payload.
3. Local-only, no-store `GET /api/energia` and `GET /api/hexelion/energia` serve the same snapshot. Exact local Host plus loopback client, origin/fetch-site checks prevent unauthorized reads. CLI agents can read their endpoint without a browser; they cannot switch electricity.
4. Settings has a 44px button, status live region and opt-in JSON receipt; it fetches once per user action, with a 4-second abort, no polling. App shell and service-worker cache move together to v159.
5. Synthetic negative/control tests join the canonical `bin/pruebas` runner, including missing config, valid triangle, inconsistent Tasmota data, untrusted origins, browser resource parity and no private addresses.

## Criteria and limitations

- **Measure:** on the connected rack, identical local GET snapshots include their cause, and the 35 V / 0.96 A / ~114 W reading is rejected as electrically inconsistent. The exact physical location of the plug (battery input vs rack output) is NOT verified here.
- **NO_DATA:** solar battery state of charge, generated watts, UPS runtime, work distribution and joules/token; no upstream sensor, measured meter placement or policy authorization.
- **NO_DATA:** a model autonomously calling the tool and voice/screen-reader parity on a physical device; this slice exposes the tool and a browser live region, but does not yet wire a Talk intent or claim audio playback.
- **Security:** the existing meter endpoint remains trusted operator configuration; this slice does not introduce discovery, cloud telemetry, credentials, network writes, relay commands or automation.
- **Next piece:** APP-ENERGY-02 should route an explicit energy question from Talk through this same read-only snapshot, preserving model attribution and the exact-evidence contract; then physical calibration and an energy-policy FIRMO before any dispatch.

**Gate:** `python3 -m unittest test_energia_estado`, canonical `bin/pruebas` ×2, browser physical smoke and CI exact-head. Each skipped or unavailable measurement is reported as `NO_DATA`, never GREEN by implication.
