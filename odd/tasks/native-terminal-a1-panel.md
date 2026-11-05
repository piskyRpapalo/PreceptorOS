# Native terminal · piece A1 — the panel

The first piece of Carril A under `odd/tasks/native-terminal-visual-contract.md` (contract, merged as #173). One piece, one PR, in order A1→A4.

## Objective
Give the served terminal its panel: dark tokens re-derived from our own measured family, a glass header over the page, and `--acento` — the accent each node paints its terminal with, chosen by the carbon, persisted locally, no accounts (decreto LA TERMINAL).

## Measured (all values from this tree, app main `497c8e29`, 2026-11-05)
- Accents, from the skins of this house (`interface/face/skins.json` + the bubble palette):
  - basic → `ui.accent: "cyan"` → `#00d2ff` (`NEUTRAL.cyan`, `interface/face/bubble/comic_tokens.js`).
  - atlantis → `ui.accent: "comic yellow.base"` → `#ffb702` (`BASE_COMIC_YELLOW`, `interface/face/bubble/comic_accents.js`).
  - zombie → `ui.accent: "STALE.base"` → `hsl(60 70% 55%)` (HUE 60, SAT 70, LUZ 55, `interface/face/bubble/tabla_semantica.js`).
- Dark family re-derived (never pasted): `#1a1225` is the `<meta name="theme-color">`; the measured family in `interface/legacy/dashboard.css` is fondo `#17131f`, panel `#1e1929`, tinta `#ece9f5`, tinta suave `#a79fbe`, línea `#392f4d`. A1 declares them as tokens on the ACTIVE sheet (`interface/desnuda.css`, served as `/dashboard.css`).
- Geometry declared against the 420×640 reference (gentle-dot, MIT, cited as measure): our measured column is `48rem` wide with the chat at `60vh`, mobile first — declared, not moved. The reference values are never pasted as ours.
- Glass header: reference 0.82 / 12px blur re-derived to `color-mix(in srgb, Canvas 82%, transparent)` + `backdrop-filter: blur(12px)`, with a solid `Canvas` fallback under `@supports not` — readability never depends on the filter.

## Change
- `interface/desnuda.css`: accent tokens (`--acento-cian/sol/stale`, `--acento` driven by `data-acento`), dark tokens under `[data-tema="oscuro"]` with system fallbacks, sticky translucent `.cabezal`, accent paints focus rings (dark only — cyan fails contrast on light), the checked radio of the picker, and the send button. Laws of the minimal sheet intact: no `url()`, no image, no animation.
- `interface/dashboard.html`: `?v=58` → `?v=59` (SW cache is exact-URL, `test_pwa.py`); a new Profile field (`#et-acento` + `#p-acento` radiogroup) next to the skin switch.
- `interface/dashboard.html`: the picker lives in a small inline module at the end of the page, mirroring the theme switch (saved on click, `localStorage["acento"]`, `aria-checked` announced), with its own 9-language label table; it repaints on `lang` changes via `MutationObserver` (dashboard.js owns the language and does not know this exists). Default `cian` — basic is the door skin. No new served route and `bin/preceptoros-pwa` untouched: the route table lives in an executable file, and the contents API cannot rewrite executables without losing their mode bit (the yerba measured and cured in preceptoros-web#656). dashboard.js (140 KB) stays untouched.
- `interface/sw.js`, `test_pwa.py`: the cache URL and its assertions move to `?v=59`.

## Out of scope (A2+)
The anchor glyph and its states (A2), streaming chat (A3), composer (A4). Nothing is removed: the bust stays until A2 lands.

## Constraints
Propose-only; FIRMA over the exact head at merge. No build, no assets, no network. Screen-reader state is `aria-checked`, never color alone. `prefers-reduced-motion` needs nothing new: A1 adds zero motion.

## Checklist (stable IDs)
- [ ] A1-a: accent picker paints from `skins.json`-measured values only (checked above, with files).
- [ ] A1-b: choice persists in `localStorage` and survives reload; no accounts, no server write.
- [ ] A1-c: without JavaScript the sheet serves `cian` by default (`--acento` fallback chain).
- [ ] A1-d: `python3 -m unittest test_pwa` green, naming audit green (`bin/auditar_nombres_publicos.py`).
- [ ] A1-e: FPS / first-paint / TalkBack on the reference device: NO_DATA with cause (jail cannot measure a device; Sovereign's round pending).

## Log
- 2026-11-05: cooked by mesa-web under the vector claim (buzon#53 ·6648830330); FIRMA pending on the exact head of this PR.
