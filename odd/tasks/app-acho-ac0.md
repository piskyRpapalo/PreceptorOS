# app-acho-ac0

Date: 2026-11-02
Law: the Acho Mesa's addenda of 2-nov night (point 3: «AC-0 of the app, `interface/face/bubble/`, propose-only, D5 alias window; it closes D2 parity»). The web's own AC-0 is preceptoros-web #584 (seal `dq`, head `e4062185`), not merged yet. Decree: «bubble» removed as a name (buzon#30 ·6585675927). Status: **PLAN · REQUIRES_SIGNATURE**. Zero code in this piece.

## Why a plan and not the change, today

The app's copy of the web's language is **pinned by sha256** to the bytes of the web's `public/game/` (`test_face.py`, `CLAVADAS`, base `63c8331`). Copying the renamed files now would pin the app to an unmerged head of #584. That head has already changed once tonight (the cure of the signed creation fixtures). The change is built **after #584 merges**, against that merge's exact bytes.

## Scope measured (app main `0900d85`, 2026-11-02)

- `interface/face/bubble/`: 32 files. Five of them are the language (`bubble_language.js`, `bubble_bestiary.js`, `bubble_icons.js`, `bubble_light.js`, `bubble_world.js`), **byte-identical to web main `62dd2fd5`** (`cmp`). D2 parity holds today; #584 breaks it until this piece lands.
- «bubble» in **51** files of the app; the seal `preceptoros.bubble/1` in **18**. These include the app's own producers: `colony/buildings.js`, `colony/walking_frames.js`, `colony/web_global_map.js`, `creacion_import.py`, `assets/creation-view/game/creation_package.js`, and the three skins.
- The path `face/bubble/` appears in **10** files: the three skins, `interface/sw.js` (the app's cache list), `bin/preceptoros-pwa`, `colony/building_preview.html`, two docs, and `test_guardrails.py` and `test_herencia_web.py` (both exclude the vendored folder from their audits). `test_face.py` holds the pins.

## The change (when #584 merges)

1. **Directory:** `interface/face/bubble/` → `interface/face/acho/`; every loader path `/face/bubble/` → `/face/acho/`.
2. **Copies:** the five language files become `acho_*.js`, copied **byte for byte** from web main after #584. The 27 other vendored files are re-copied from the same sha. `CLAVADAS` is re-pinned to that sha, and the base comment cites it.
3. **Seal:** the app's producers write `preceptoros.acho/1`. Every reader of stored data accepts `preceptoros.bubble/1` during the D5 window, as the web does: `compile`, `creation_package.js` and `creacion_import.py`. Signed creations already on devices keep verifying, and signed fixtures are **not re-signed**: they are the proof of the window.
4. **Kept:** speech bubbles in `face.js` (`bubble(who, text)` is a dialogue balloon, not the language), water bubbles, the DOM flag, and dated records (`docs/receipts/`, acts under `odd/`).
5. **Lexicon:** the app's naming docs point to the web's coinage (web `docs/lexicon-implementation.md` §K «Acho»). The app does not coin twice.

## Gates

- `test_face.py` green with the new pins: every vendored file equals web main after #584, by sha256.
- `cmp` of the five `acho_*.js` against web main: identical (D2 closed).
- A case: a frame with `preceptoros.bubble/1` still compiles in the app, and a frame with any other `v` is refused.
- The app's full test run (`python3 -m pytest` and its node cases) green twice.
- SCRUB: no device names, no home paths.

## Checklist

- [x] APP-AC0-0 · this plan, measured.
- [ ] APP-AC0-1 · wait for #584 to merge; read its merge sha.
- [ ] APP-AC0-2 · rename + re-copy + re-pin (one PR).
- [ ] APP-AC0-3 · producers write Acho; readers keep the alias (same PR or the next, never bundled with unrelated work).

## Log

- 2026-11-02 · plan written on app main `0900d85`.
