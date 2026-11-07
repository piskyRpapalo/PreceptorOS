# App anatomy · chat and service panels

Date: 2026-11-07  
Status: local proposal · not published  
Source: PreceptorOS `origin/main` at `8f2bc8371b359f6e2e4398bd6a443a97cd459358`.  
Interaction reference: Gentle Dot `9732fb3`; copy its interaction anatomy only.  
Visual identity: retain PreceptorOS colors and its existing pixel-art preceptor asset.

## Explore

The app currently opens on Mando, uses text tabs across its header, and links to a
separate Hexelion page. The existing service zones and their local endpoints are
already present in `interface/app.html` and `interface/app.js`. The repo contains
the four-frame PreceptorOS pixel bust at `assets/preceptoros-up.png`.

## Proposed slice

1. Open on Hablar so the first screen is the existing local chat.
2. Put compact, labeled zone buttons above the conversation; each selects its
   existing panel and preserves its current service behavior.
3. Remove the separate Hexelion header link from this shell.
4. Use the app's pixel bust in a round control that collapses or restores the
   zone buttons and panel area. Keep the control's accessible name and expanded
   state synchronized.
5. Keep Bandeja under Ajustes so the chat and its navigation stay the primary
   surface.
6. Align the app stylesheet, script, pixel asset and service-worker cache.

No Gentle Dot colors, iconography, or product branding are copied. The web map,
node-connected state, and ephemeral visitor flow are outside this UI slice.

## Acceptance

- A fresh `/app` or `/app.html` opens the conversation panel.
- All nine existing zones remain reachable by touch and keyboard; their names
  remain available to assistive technology in the selected language.
- The round pixel-face control hides and restores navigation and the current
  panel, and reports its state through `aria-expanded`.
- Existing chat, panel, and API behavior remains intact.
- Service-worker cache versions and static URLs match the served app files.
- Browser/device appearance remains NO_DATA until a real browser/device pass.

## Record

Local changes are on `proposal/gentle-anatomy-acho-20261107`, based on the source
head above. No push or merge. Tests and browser/device rendering were not run.
