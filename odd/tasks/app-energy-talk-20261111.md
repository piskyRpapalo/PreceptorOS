# APP-ENERGY-02 · Local sensor query in the one Talk panel

**Agent:** Codex · GPT-6. **Scope:** APP + local Hexelion tool boundary. **Mode:** BUILD / PROPOSE-ONLY, no production change. **Dependency:** [APP-ENERGY-01 PR #244](https://github.com/piskyRpapalo/preceptoros-app/pull/244) must be merged/revalidated before this stacked draft can target main. No second app, electricity controller, new model or daemon.

## Problem and sources

The existing Talk path (`bin/preceptoros-pwa:_hexelion_chat`) correctly requires model answers to contain SHA-256 verified exact memory citations; absent evidence => NO_DATA. That is **not** an appropriate ground truth source for present-tense device energy. APP-ENERGY-01 already defines a read-only, timestamped `preceptoros.energy-read/1` snapshot from the existing meter, with invalid electric readings rejected. Independent current, SOC, generation, watt-hours and energy allocation remain NO_DATA, cause: no valid sensor or controller connected.

The user wants Hexelion to answer "How much power does the rack use?" without pretending that model memory is a live sensor. Policy: one app/device; A11Y sight/voice/machine parity; model output never grants action; English app/web interfaces.

## Adaptation, not duplication

- Reuse `energia_estado.respuesta()` as the **single source**. No independent meter read, guessed power, new polling loop or duplicated dashboard.
- Reuse the earlier unmerged `energia_intencion.es_consulta` exact-phrase prototype, with explicit English/Spanish/Portuguese query allowlist and no fuzzy matching. Mixed instructions deliberately do **not** match.
- Enforce the existing request authentication, JSON bounds, team/voice rules and append-only user turn **before** recognizing sensor intent. It then creates a separate response type `LECTURA_LOCAL/energia_local`. No call to the model or memory selector, no fabricated citations, no claimed GPU/CPU backend.
- In the **existing Talk** bubble, distinguish "local sensor (model not invoked)" from the model answer, with the same response text in screen-reader live output and structured API receipt. Cached scripts and SW advanced together to v161. The energy UI remains English.
- Sensor failure fails closed, not back to an LLM guess. Does not modify the physical socket or authorize solar allocation.

## Measurable benefit and verification

Target: exact energy question -> one local sensor snapshot, zero `_hexelion_proxy.ask` calls and zero memory-search calls; result visible in Talk and parsable by a machine. Negative tests cover malicious trailing commands, remote origin, model non-invocation, no memory citation forgery, CLI actor attribution, 1,024 B receipt, sensor faults.

**Measured in isolated Beelink checkout 2026-11-11:** `python3 -m unittest test_energia_intencion test_energia_estado test_metricas -q` 32/32 ×2, `python3 test_idioma.py` 17/17 ×2, public-name inventory 80 routes ×2, JS syntax and `git diff --check` passed. All were test fixtures; physical electricity and real screen reader are not exercised.

**NO_DATA:** complete canonical APP `./bin/pruebas` ×2 on this exact head, GitHub Actions exact-head, a person testing a real Talk UI, speaker/audio output, reliable voltage, solar charge and actual energy/token — these require separate receipts. CI and physical browser tests must not be inferred from Python fixtures.

## Risks / next piece

English-only interface is a separate standing policy; foreign-language **queries** are input, not a localized UI. A new question outside the exact allowlist stays in the model's existing source-verified path; it is not an autonomous planner. Check browser keyboard and ARIA announcement using a real device before calling accessibility E2E. Only add solar-cadence actions after validated battery topology and a fresh Sovereign signature.

**Collision fence:** Notebook [#236](https://github.com/piskyRpapalo/preceptoros-app/pull/236) belongs to its existing APP lane; WEB and Vercel/3DFabrika are not this PR; the old unmerged `codex/app-energy-talk-20261111` prototype is superseded by this tested stack.
