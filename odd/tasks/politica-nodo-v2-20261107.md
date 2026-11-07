# Node law contract v2 · `preceptoros.politica-nodo/2` (mission H1, 2026-11-07)

> **Status: PROPOSAL.** This is the contract; there is no code yet. Code comes later as a Haiku slice reviewed by silver, after FIRMO on this text.
> **Base:** app `origin/main` b5d696f.
> **Today:** v1 is closed at six conditions. `mcp_thegame_server._read_policy` (`mcp_thegame_server.py:26`) rejects every extra key, and the Boundary read model (app PR from `haiku/boundary-read-model-20261107`) reports the posture and the signature as NO_DATA.

## Why a v2

The canon says «the node is a terrain with soldiers, buildings and trade caravans, each with laws chosen in the app; your node has laws and you sign them». The source is roadmap `PREGUNTAS.md:201`, and `odd/ADDENDUM-VECTORIALIDAD-COLONIA-20261101.md:19` names the five postures.

v1 carries the conditions. It has no posture, no validity window, no entry rules, no caravan terms and no owner signature. v2 adds those fields and changes nothing that v1 already measures.

## Shape (closed, ≤ 1,024 B as canonical JSON, the same ceiling as v1)

```
{
 "esquema": "preceptoros.politica-nodo/2",
 "version": "2.0.0",
 "nodo": null | "<cedula alias>",              // NO_DATA in no_data[] while unassigned
 "no_data": [{"campo": "...", "causa": "..."}],
 "postura": "pacifico|hostil|cooperativo|cerrado|abierto",
 "vigencia": {"desde_ciclo": int, "hasta_ciclo": int},  // game cycles, never the wall clock
 "entrada": ["esperar", ...],                  // subset of customs_agente.ACTIONS (customs_agente.py:14)
 "caravanas": {"acepta": bool, "peaje": [{"resource": "...", "amount": int}], "contrato": "preceptoros:caravana/1"},
 "condiciones": { the six v1 conditions, unchanged },
 "firma": {"clave": "<ed25519 public hex>", "sig": "ed25519:<hex>"}   // over the canonical JSON without "firma"
}
```

## What each posture means in engine terms

A posture is only a declaration until the engine reads it. Each posture maps onto mechanics that already exist or are already proposed, and invents none.

| Posture | Canon | Engine meaning | Allowed entry by default |
|---|---|---|---|
| pacifico | automatic defence | a `conquista_a2a` proposal is refused at PROPUESTA; buildings defend by design (bible law 9) | esperar, recoger |
| hostil | allows invasions | a `conquista_a2a` proposal may reach ACTIVA; finishing still needs the owner's signature (AI Act art. 14) | esperar, recoger, bajar_a |
| cooperativo | accepts outside help | `cooperacion_obligatoria.firmas_minimas` applies to outside help; `reparar` is open to declared agents with a cédula (bible law 6) | esperar, recoger, reparar |
| cerrado | does not expose its interior | the public frame carries the state only: no buildings, no cargo, no pressure | esperar |
| abierto | publishes its territorial pressure | the public frame adds the pressure counter; caravans may be proposed by anyone with a cédula | all five |

`entrada` may narrow the defaults but never widen them beyond `customs_agente.ACTIONS`.

## Laws that hold for every posture

These are carried from `aiact_art14_game_policy.json` and the game bible; no posture switches them off.

1. **Silicon proposes; the person signs.** A posture change, a caravan completion and a conquest completion all need `firma`. Without it they are EMULADO, never real (`aiact_art14_node_decide.propone`, `aiact_art14_node_decide.py:67`).
2. **Prohibited forever:**
   - credit for passive time, hover, scroll or reading without a signature;
   - psychological profiling from telemetry;
   - casino gacha;
   - device fingerprint as identity;
   - real money or crypto.
3. **A visible bot is a neighbour; a hidden bot is fraud** (bible law 6).
4. **Force does not transfer ownership.** Conquest is a signed offer that the owner accepts (bible law 3).

## Validation (deterministic; the order is fixed)

1. bytes < 1,024
2. valid JSON
3. closed key set for /2 (v1 files are still read; their posture and signature come out NO_DATA)
4. `postura` is in the enum
5. `vigencia.desde_ciclo ≤ hasta_ciclo`, both whole numbers ≥ 0
6. `entrada` ⊆ `customs_agente.ACTIONS`, and ⊆ the posture default
7. `caravanas.peaje` holds whole engine resources (the same list as `atlas.oferta/1`)
8. the six conditions are unchanged from v1
9. the signature verifies over the canonical JSON without `firma`. A missing signature gives `estado: PROPUESTA`; a signature that does not verify gives `RECHAZADA`.

The validator returns `{estado, causa}` and never raises.

## Red tests first (listed before any code)

- a v1 file reads as posture NO_DATA and signature NO_DATA, with no exception
- an unknown posture → rejected, with cause `posture_not_in_canon`
- `entrada` wider than the posture default → rejected
- `vigencia` with a clock timestamp (not a whole number) → rejected
- a valid shape without a signature → PROPUESTA, never active
- a signature over a different byte → RECHAZADA
- a document of 1,024 B or more → rejected before parsing
- `cerrado` → the public frame carries no building, no cargo and no pressure key
- a sabotage that accepts `hostil` with completion and no signature → the suite goes red

## Link to the bias arena (H2)

The posture is an experimental condition, not decoration. The same agent can be placed next to a `pacifico` neighbour and next to a `hostil` one, and its political-family behaviour compared under a hypothesis registered before the run. That comparison is H2's design; this contract only makes the condition signable and reproducible.

## NO_DATA

- The owner key ceremony: which key signs. The cédula (`preceptoros.cedula-nodo/1`) names the node but does not yet carry the owner's public key.
- An engine that reads `postura`: none yet. The first reader would be the Boundary read model, then customs.
