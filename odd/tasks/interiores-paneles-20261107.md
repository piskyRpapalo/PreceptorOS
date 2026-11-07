# Panel interiors · the nine tabs of the mini window (2026-11-07)

> This plan extends the Mesa's tab roadmap. That roadmap lives on branch
> `mesa/tareas-abiertas-20261107`, in `odd/tasks/hoja-de-ruta-pestana-por-pestana-20261107.md`.
> Nothing here duplicates it.
> Base: app `origin/main` b5d696f. Every citation below is file:line on that head unless another repo is named.
> Target: the WebKitGTK mini window, content area 420×642. The panel area is 420×437, at 80% type, with 44 px targets.

## Lens (signed 2026-11-07)

- **App = the NODE.** It is a terrain with laws, soldiers, buildings and trade caravans, governed by its owner.
- **Ephemeral account = the VISITOR on the web.** It explores and can play. It never gains authority over the node and never gets a persistent identity.
- **SHARED:** game resources and wave combat. Sharing rules never mixes ownership, identity, memory or permissions.
- **The terrain is where AIs play.** It is the arena for behaviour and bias benchmarks across the seven families: sovereign, epistemic, thermodynamic, adversarial, creative, political and utilitarian.
  - Source: `study/14-bench-families.md` and roadmap `odd/ADDENDUM-VECTORIALIDAD-COLONIA-20261101.md:19-23`.
  - A green gate is not a safety score.
- **Every card shows exactly one state:** MEASURED, PROPOSED, EMULATED or NO_DATA. A NO_DATA card carries its cause.
- **Canon is not proof.** Caravans, invasions, trade and AI-vs-AI combat stay NO_DATA until they are measured.

## ⛨ Boundary · the node's A2A law (`gobierno`)

This tab works like the special harness of the ecosystem: the owner writes how other agents may reach the node.

1. **Posture.** One of `peaceful`, `hostile`, `cooperative`, `closed` or `open`.
   - Source: roadmap `PREGUNTAS.md:201` and the addendum, line 19.
   - Today: NO_DATA (`no posture field in preceptoros.politica-nodo/1`).
2. **Conditions (read only, MEASURED from the file).** The six conditions of `politica_nodo.json`: debt ledger, hydraulic brake, political fork, entry collateral, mandatory cooperation, and the wasmtime sandbox.
   - The sandbox condition already declares itself NO_DATA (`wasmtime_not_compiled`).
   - Reader: `mcp_thegame_server.py:26` (`consultar_politica`, :13). The PWA has no route for it yet.
3. **Who may enter.** Customs for agents, via `customs_agente.verificar_entrada` at `customs_agente.py:52`.
   - Signature check, 1,024 B payload.
   - Allowed actions: wait, gather, repair, defer, step down.
   - Shown as a whitelist, not as a form.
4. **Caravans.** Each route card has a state from the machine `PROPUESTA→ACTIVA→INTERCEPTADA→COMPLETADA/HUIDA/CADUCADA/NO_DATA`.
   - Source: `aiact_art14_game_policy.json` → `conquista_a2a` (REQUIERE_FIRMA; without a signature it is EMULADO).
   - Trade offers use the web contract `atlas.oferta/1` (whole engine resources only, expires per cycle, no settlement without a human signature).
   - The schemas `caravana.firma/1` and `pared.mensaje/1` are labels only: NO_DATA (`no schema file`).
5. **Laws of the game bible as toggles.** Source: p0x `mente/doctrina/BIBLIA_THEGAME.md`.
   - Embassy by mutual consent (2), bot with an ID card (6), visible legal state CLEAN/OFFENDER/FUGITIVE (5), treaty with clauses (15).
   - These are doc only, so NO_DATA until they get a contract.
6. **Sign.** The policy becomes versioned, carries a validity window, and is signed by the owner.
   - Silicon proposes; the person signs (AI Act art. 14, `aiact_art14_node_decide.py:67`).

**First slice:** a GET route serving `politica_nodo.json` through the existing validator, rendered as cards 2–3.
Writing the policy (posture plus signature) is the second slice and needs a FIRMO for its contract.

## ⌖ Mando · the node's controls (`mando`)

- **Keep:** the compass M0–M7 (`compass.py:159`, `/api/camino`).
- **Add a resource ledger of the node.**
  - `resource.mana` (web `public/game/global_map.js:17`) is SHARED.
  - The ledger design is p0x `propuestas/2026-10-22_diseno-economico-nodo/B1-libro-recursos.md`, PROPOSED.
- **Split actions into two lanes.** The node proposes (`aiact_art14_node_decide.propone`); the person signs. Irreversible actions always show the signature lane.
- **Soldiers and army of the node:** NO_DATA. The web says "node army not started" (`odd/tasks/ephemeral-user.md:4`).
- **Gap:** T11 (retarget the compass to node resources) has no code in any repo.

## ▱ Hablar · conversation bound to context (`conversacion`)

- **Keep:** cited chat. `_hexelion_chat` at `bin/preceptoros-pwa:817` chains `memory_lookup` → `hexelion_book` → `verificar_citas`.
- **Add a context chip:** the tab or building the question is about. This uses `hexelion_book.PANELES` (`hexelion_book.py:11`).
- **Add read aloud:** `HexelionNativeVoice.read` from `native_voice.js`. The face does not load it yet.
- **Rule:** a reply without a verified source is labelled so. A model answering does not mean the answer has sources.

## ▤ Cuaderno · the node's records (`cuaderno`)

- **Keep:** turns, consent, and per-item receipts (`captura.py`, `/api/captura`).
- **Add a receipt shelf.** Two kinds of receipt, kept separate:
  - nesting receipts from Boundary (Mesa pending);
  - building-proof receipts.
  - Visit data never lands here.
- **Add T9: paste large text.**
  - The nearest door is `/api/anidar` (512 KiB limit).
  - No route writes a large text into `turnos` yet: NO_DATA.
- **LoRA dataset row count:** `lora_dataset.py` lives on a branch; training stays NO_DATA (`CAUSA_SIN_LORA`).

## ⚗ Lab · experiments and bias benchmarks (`lab`)

- **Keep:** channels and local models (`lab.py`).
- **Add the Lab V2 factory card.** Contract `fabrica/1 {id,titulo,estado,novedades≤100,agentes,edad}`, on the Mesa branch.
- **Add a benchmark shelf with one row per family.** Each row carries condition, source, age and receipt.
  - Existing:
    - self-preference (lab `benchmarks/self-preference-20261025`);
    - red-team (lab `benchmarks/redteam-20261020`);
    - signed opinions on the judge (web `atlas/verify_opinion.mjs`);
    - the Hexelion benchmark (web `public/openworld/hexelion-benchmark.json`).
  - On the terrain:
    - BM-1 is MEASURED (web `atlas/puros/bench_move.js`);
    - BM-2 to BM-4 (AI wave duel, record, send to Lab) are open;
    - a bias benchmark run on the map is NO_DATA.
- **Agents on the terrain:** web `atlas/harness_agents.mjs:67` reports SIMULATED ("no A2A transport is configured"). Show it as EMULATED.

## ⌁ Harness · measured cycles (`harness`)

- **Keep:** freshness and the loop list (`/api/harness` → Nexo `/api/timers`).
- **Fix first:** the route is duplicated (`bin/preceptoros-pwa:418` and `:420`), and so is `_harness_leer` (`:1176` and `:1197`).
- **Add per-loop age** in place of one freshness for the whole panel.
- **Add hit rate per model and task:** `captura.rendimiento` at `captura.py:438`.

## ⌂ Puerta · what an outside agent reads (`puerta`)

- **Keep:** the key and the pasteable document (`/api/empieza-aqui`, `empieza_aqui.py:169` VERBOS).
- **Add a verifiable node ID card:** `preceptoros.cedula-nodo/1`.
- **Declare the decree "zero undeclared requests"** in `llms.txt` (`odd/tasks/cola-paralela-20261107.md:9,17`).
- **Public agent card / `.well-known`:** NO_DATA (zero files in any repo).

## ▦ Mundo · the shared map (`modelos`)

- **Keep:** the fixed-piece iframe.
- **Add an entry line:** "you govern this node" or "you are visiting", read from the cédula and the visitor account (web `public/game/visitor_account.js`).
- **Combat outcomes come only from the engine:**
  - `wave_rules.js` W1 is deterministic;
  - victory, abandonment and missing data are all shown;
  - nothing is invented.
- **Mana and wave combat are SHARED.**
- **VISITOR only:** visitor copper (`visitor_eggs.js:3`) and visitor battle.

## ⚙ Ajustes · local preferences of this device (`ajustes`)

- **Keep:**
  - redaction;
  - keep this app on this device (#207: explicit click, verified result);
  - node identity / building cards.
- **Add the brain route:** base or tuned model (`afinado.py:110-124`). Today the selector exists only in the old dashboard.
- **Add an own endpoint + own key**, stored on the device only (Mesa MVP).
- **Day energy (solar cadence):** NO_DATA in the app.
- **Review the "creation voice" and "publish creation" cards:** they are creation flows, not settings. They are PROPOSED to move, not deleted.

## Order (smallest measurable first)

1. Harness duplicate cure.
2. Boundary policy GET plus cards 2–3.
3. Mundo entry line.
4. Lab benchmark shelf, read only.
5. Hablar context chip and read aloud.
6. Boundary posture and signature (FIRMO on the contract).
7. Caravan schema (FIRMO).

One piece = one branch = one draft PR "HITL · …", measured in the mini window.
