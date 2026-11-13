# Install identity · the installed app is PreceptorOS (APP-IDENTITY-01)

Commission 2026-11-13 «Corrección arquitectónica multidispositivo», Entrega B. Owner: Claude Code (APP).
Stacked after APP #266 (cache v173 → v174).

## Explore (2026-11-13, read only)

- The Sovereign saw the main phone's app named «Hexelion» with an old icon. `interface/manifest.json` published
  `name: "Hexelion · PreceptorOS"`, `short_name: "Hexelion"` (since 2026-11-03).
- Served icons = repo = generator (`icons_from_emblem.py --comprobar`: IGUAL ×3): the #248 emblem is what the
  app serves.
- Three different things, not one installation:
  1. the local app's WebAPK on the main phone (origin `http://127.0.0.1`, minted 2026-11-11 21:52 UTC,
     12 min before the emblem icons merged): name «Hexelion · PreceptorOS» / «Hexelion», the old bust icon;
  2. the local app's WebAPK on the S110 (minted 2026-11-12 02:22 UTC): same names, the emblem icon;
  3. the public TWA APK (web repo, android-v1.0.0): not installed on either phone (user 0). Not touched.
- Chrome's own update state (`chrome://webapks`): NO_DATA, DevTools refuses chrome:// pages.

## Implement

- Manifest `name` and `short_name` = PreceptorOS. Hexelion keeps its name inside Talk.
- `id`, `start_url`, `scope`, `display` unchanged and pinned by test: moving them would mint a second app.
- Icons unchanged (already the emblem). The service worker serves the manifest cache-first, so the cache name
  moves (v174); that is what lets an install read the new manifest.

## Check

`test_app_identidad.py` (name, same installation, icon sizes/purposes, page = manifest addresses, shell caches the
manifest and exact icon addresses, cache moved). Sabotage 5/5 red. Gate figures in the PR receipt.

## Log

- 2026-11-13 · A new manifest does not rename an existing WebAPK by itself: Chrome checks on launch after its own
  update interval and may ask the person to confirm a name/icon change. Measure after merge: package
  `lastUpdateTime`, launcher label and icon on both phones. No reinstall, no data clear, no shortcut removal.
