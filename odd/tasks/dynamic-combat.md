# Dynamic combat · preservation and recovery plan

**Status: PROPOSAL · documentation only.** No served code, combat rule, seed, balance value, or route is changed by this task.

## Decision to preserve

The Sovereign's requirements recorded for 2026-10-28:

- Waves fight while **moving on screen**.
- A present human may choose a strategy or a different starting point without breaking determinism.
- Dynamic combat is a key part of gacha: a wave is not only a stat row or a static token; its generated form must be seen acting in the world.

These are requirements from the current commission, not measurements of browser behavior. The three defects below are also commission declarations, not measured findings: wave drawings are too large; invocations lag; Worlds have no distinct door and are reached through `/face`. No viewport, device, duration, or invocation timing was supplied, so all three remain **NO_DATA · no measurement run in this docs-only task**.

## Evidence boundary and important correction

Corpus pinned to WEB `origin/main` **`07df88e7e1195bc95a1f61dfd8bcc4b15359a695`**, measured 2026-10-28. Search expressions used:

- `git ls-tree -r --name-only origin/main | rg -i '(arena|onda|wave|combat|battle)'`
- `git show origin/main:public/game/wave_duel_scene.js | rg -n 'function (estado|escena|impacta|mueve|cuadro|reinicia)|op\.vivo|requestAnimationFrame'`
- `rg -n 'wave_duel_scene.js|face_fight_stage.js|ui-arena.js' public`
- `git ls-remote --heads origin 'mistral/w-o*'`

**The claim that the dynamic combat product is absent from refreshed WEB main is contradicted by this pinned source.** `public/game/wave_duel_scene.js` exports `AtlasWaveDuel`; `public/face/basic.html` loads it before `face_fight_stage.js`; `public/face/face_fight_stage.js` creates it with `{ vivo: true }`; `public/assets/thegame.js` loads it before `ui-arena.js`; and `ui-arena.js` calls `AtlasWaveDuel.escena`. This proves source and integration references exist in main. It does not prove the route is discoverable, visually sized correctly, or available from a dedicated Worlds door; those remain unmeasured.

The backup ref `origin/respaldo/visual-viejo-20261028` resolved to the same commit as `origin/main`; `git rev-list --left-right --count origin/main...origin/respaldo/visual-viejo-20261028` returned `0 0`. It supplies no distinct older source in this checkout. Contrary to the commission's branch note, `git ls-remote` found `mistral/w-o1a-wave-duel-20261027`, `mistral/w-o1b-switch-20261027`, `mistral/w-o2-audio-20261027`, and `mistral/w-o3-pulso-20261027` on origin on 2026-10-28; each queried head is an ancestor of pinned main. This task does not inspect their contents, alter them, or recover by cherry-pick. Main is the inventory source.

## Source inventory and anchors

All entries below are from the pinned WEB main above; the SHA is the Git blob ID. The canon files are documentary anchors; executable modules and their schemas define runtime behavior.

| Source | Blob | Relevant anchor / role |
|---|---|---|
| `public/game/arena.js` | `bfba0404baee4d5f4852c3e673103180d38e11fd` | `combate` at 63; `resuelve` at 65; `patrulla` and `lugares` at 116–123. Pure deterministic arena rules, seeded NPC defense, envelopes and result validation. |
| `public/game/combate_ticks.js` | `d3bf4d9afa520ebd3830d7fe53b781a4a6cc0b5e` | `inicia` 34; `ronda` 43; `combate` 68; `simula` 89; `recibo` 103; `verifica` 120. Tick engine is pure: no DOM, network, wall clock, or system randomness. The intervention currently encoded is `retira` at a chosen tick, not a general strategy API. |
| `public/game/wave_duel_scene.js` | `38020b21b1a5cf623a80aa7e51692b0c8f147bf0` | Seeded visual state `estado` 17; scene `escena` 38; impacts 67; movement 100–107; animation frame 207–221; restart/skip/stop 223–237. `op.vivo` consumes a growing combat log. |
| `public/face/face_fight_stage.js` | `12fc0697dee9beb9a9e84bbf0387fa5a144cb009` | Own battle canvas and `AtlasWaveDuel` invocation; live flag passed at scene creation. Canvas has a text label, but actual screen-reader narration was not measured here. |
| `public/game/combat_screen.js` | `a157a553533f7fc51995e107930e4ea254455cb5` | `#thegame/battle` route; screen lifecycle, browser Back/Escape/close, and one-time settle. |
| `public/game/ui-arena.js` | `2456bb7ddce617122c0b414dc21607838445091f` | Practice fallback and available squads 18–24; NPC/PvP invocation 89–101; scene and result lifecycle 120–160. NPC seed includes patrol id, squad fingerprint and attempt index. |
| `public/game/ui-arena-comun.js` | `a43e976d9b4c027d8cccd9b4c75b1399a7d79cb5` | Shared arena view: deterministic troop previews, place selection and fight controls. |
| `public/game/gacha.js` | `ee1694a8a6ecf16f0f5095bc98d085beb994f568` | Wave derivation from TC and seed; a generated wave's harmonics/stats are re-derived rather than trusted from a display payload. |
| `public/game/summon-wave-card.js` | `160b9ba09896ea9df698a45fcc358ce0aefb0748` | Summon reveal card; shows harmonics, origin and stats, then links to Workshop. It presents an already-generated wave; it is not the arena resolver. |
| `public/game/army-wave-panel.js` | `7289af89a62b6d037e7abf37b598c2a265b6eadb` | Selected Army wave detail, status and Workshop action; not a combat loop. |
| `public/assets/atlas-ondas.js` | `45ea14f4ac464ebe1ab847edb8f9816d4ee87aa1` | Seeded harmonic/sea drawing; presentation asset, not combat state. |
| `public/game/onda_profunda.js` | `c8ecc22a0f98c0a4b4663bcae141b32be42b9a56` | Pure floor depth/anchor planning and painter queue; z-order helper, not wave combat or combat animation. |
| `atlas/arena_ticks_casos.mjs` | `88d36556aac29d6c6e9933f11296b302965f9ca1` | Replay from tick 0, pre-fork prefix equality, invalid order rejection, altered-receipt rejection and 200 B ceiling. |
| `atlas/combat_screen_casos.mjs` | `8550b78790b0d0bd6171ce1c3710e37a4492d95c` | Battle route/lifecycle, one-time settlement, and script load order. |
| `atlas/wave_duel_casos.mjs` | `8459e491c9bd86dd84bfef793c763fd85b1ade3f` | Same fight+seed draw hash, sabotage twin, distinct fights, reduced-motion timing, and scene structure. |
| `atlas/wave_duel_browser.mjs` | `98606cadebbb6f84861713df9015d504b40cbfcb` | Browser evidence harness for round/damage labels and canvas text alternative. Not run in this documentation task. |
| `atlas/summon_wave_card_casos.mjs` | `eedd48737acb9466e2612187f2c13b2194b9e5e9` | Wave card render/model and Workshop path. |
| `atlas/army_wave_casos.mjs` | `3aab0b79bc0ad0ba61c4202f17e8848d2a06e582` | Army wave panel source contract. |
| `docs/canon-arena-and-duels.md` | `85a25529000bfaa92393523da34d4e8df820ba46` | Migrated arena/duel canon; signed defense, commit/reveal, whole rounds, replay verification, and declared-but-not-applied `en_juego`. |
| `docs/canon-vector-and-wave.md` | `b53d7e117224de4b73c8f1f57229e5d684aefe96` | Runtime stays in modules/schemas; shared semantic table is sole source for signal projection; display-time rendering is separate from game state. |

## How the loop works today

1. **Wave identity / gacha.** `gacha.js` maps a canonical type (TC) and seed to the same harmonics and stats. Summon reveal (`summon-wave-card.js`) displays that result; Army detail (`army-wave-panel.js`) reads the shared Army record. Neither display is allowed to invent a combatant.
2. **Choose a fight.** In `ui-arena.js`, owned Army entries are selected; if none exist, the practice squad uses fixed `atlas.practica/1` seed derivation. NPC PvE uses `atlas.pve/1`, NPC id, squad fingerprint, and local attempt index to derive a battle seed. PvP routes through `AtlasDueloUI` and the signed defense/assault/commit/reveal contract in the arena canon.
3. **Resolve.** `arena.js` calls the pure tick engine. Initiative, attacks, evasions and damage append an ordered round log. `combate_ticks.js` can replay the same seed from round zero and verify a compact result. Its current human intervention format only retires a named troop at a named tick; it does not yet express the requested range of strategy choices or starting-point choices.
4. **Animate and settle.** `ui-arena.js` routes the player to `#thegame/battle`, creates `AtlasWaveDuel`, and settles once on result/exit. The face battle stage consumes a live `d.combate` whose log grows tick by tick. The wave scene animates units toward opposing positions, shows rounds and hits, and stops/restarts/skips explicitly.
5. **Gacha connection.** The battle makes generated waves legible as moving actors, while identity and combat values remain the seeded gacha output. A future strategy or position choice must be explicit input to the pure resolver so the same complete input replays exactly.

## Determinism boundary

- **Combat outcome:** deterministic for the same canonical teams, TC, values pack, seed and ordered interventions. The resolver does not read display time or DOM. The NPC seed also includes the attempt index; a repeated attempt is deliberately a different input.
- **Current intervention:** `retira` is sorted by tick, side and unit index, then applied before that round. The existing tests require the log prefix before a fork point to match the baseline and require replay from tick zero.
- **Visual movement:** the duel scene derives its visual state from the fight seed and a seeded xorshift sequence, but motion advances in `requestAnimationFrame`; movement uses the supplied frame timestamp and `dt`. Therefore visual pixels are not claimed identical across different frame schedules, device pixel ratios, or canvas sizes. This display clock has no authority over the discrete fight result. Reduced-motion mode is a separate view behavior.
- **Human choices required by the Sovereign:** choices must be serialized as canonical values (strategy id, selected squad/order and initial positions), included in the challenge/receipt fingerprint, validated against a closed schema, and consumed by the deterministic resolver. Same canonical choice set + same seed + same value pack → same result. UI selection order must not change identity; canonical sorting/tie-breaks must be declared. This is a design constraint, **not an implemented feature or signed ruleset**.

## Known gaps and unresolved rules

| Topic | Current source-backed state | Open rule / evidence still needed |
|---|---|---|
| Moving waves | Implemented in `AtlasWaveDuel`; the face battle path passes `vivo:true`. Main contains the integration. | Measure actual public discoverability and animation on a fixed viewport; do not claim absence from main. |
| Strategies | Resolver accepts only `{tick, side, unit index, action:'retira'}`. | Sovereign chooses the allowed strategy vocabulary, choice points, legal range, tie-break, whether choices are simultaneous/secret, and whether strategy changes only rendering or also combat. No rules are invented here. |
| Starting positions | Scene computes columns/positions from canvas geometry and troop count; API has no signed initial-position input. | Sovereign chooses a bounded grid/anchors and whether position affects only presentation or attack reach/initiative. Canonical positions must be part of the replay input if they affect outcome. |
| Oversized waves | Declared defect only. | **NO_DATA** · no viewport/device measurements or pixel bounds supplied. Record width, height, DPR and worst-case troop count before sizing changes. |
| Slow invocation | Declared defect only. | **NO_DATA** · no cold/warm latency, stage timestamps, or browser/device pair supplied. Profile summon derivation, reveal render and fight startup separately. |
| Worlds entry | Declared requirement: a dedicated door is needed; current product is reached through `/face`. | **NO_DATA** · this task did not measure all public routes, deep links or user reachability. A future door is a separate proposal; preserve current deep links until measured. |
| Audio / accessibility | `face_fight_stage.js` gives the canvas a text alternative; wave-duel browser cases inspect canvas text. | No screen-reader run was made for this task. Require keyboard operation, reduced-motion path, and a readable event/result stream before calling the movement accessible. |
| Gacha link | Seeded wave generation and reveal/detail panels are present. | No measured invocation latency or evidence that every summon path reaches the same canonical Army state was produced in this docs-only task. |

## Recovery and preservation sequence

1. Keep the pinned main blobs above as the reference. Do not copy or cherry-pick the historical work branches: their measured remote heads are already ancestors of main. The named backup branch is byte-identical at the commit level to main.
2. Before any UI work, independently measure which Worlds routes are served and how a visitor reaches the live fight. Keep route loss/absence as NO_DATA with exact cause until that route audit exists.
3. Preserve the existing contracts in separate layers: seeded `gacha.js` identity; pure tick resolver and replay receipt; scene animation; accessible battle route/lifecycle; reveal and Army detail. A drawing fix must not alter a seed, combat input or result.
4. Resolve the human-choice contract before implementing it: closed strategy schema, starting-position domain, canonical order, seed/fingerprint inclusion, intervention timing, receipt size and replay behavior. The current `retira` action is not a substitute for the requested design.
5. Measure the declared large-wave and invocation-lag defects at a fixed viewport and device, including troop count, cold/warm invocation stages, frame schedule and reduced-motion behavior. Tune canvas geometry only after those baselines exist.
6. Make the dedicated Worlds door a separate, reversible route proposal after route inventory. Keep `/face` links working until a measured redirect/compatibility rule is accepted.
7. In a later implementation commission, preserve and extend the existing red-capable cases: replay/prefix/damaged-receipt (`arena_ticks_casos`), battle route/settle-once (`combat_screen_casos`), seeded draw determinism and reduced motion (`wave_duel_casos`), browser event/labels (`wave_duel_browser`), and summon reveal/Army contract cases. Run each relevant gate twice on the resulting implementation; this document has not run them.

## Search/copy guard

No code or asset was moved. `origin/respaldo/visual-viejo-20261028` and the four `mistral/w-o*` refs were queried read-only to test the commission's recovery premise. Their observed state is recorded above; no worktree, branch, or source on those refs was modified.
