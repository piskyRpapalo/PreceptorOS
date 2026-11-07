# Retire the legacy face routes · 2026-11-07

Status: propose-only; ready for the Sovereign's exact-head FIRMO.

## Scope

- Make `/` serve the existing `interface/app.html` bytes without editing that file.
- Set the PWA `start_url` to `/app.html`.
- Move the service-worker cache to a fresh version and precache the app trunk; remove the legacy face, dashboard, Hexelion, and console resources from that cache.
- Return not-found for the legacy face pages, dashboard page, and Hexelion page. Their source files remain in Git history.
- Keep `/api/lab`, `/api/hexelion/chat`, `/api/camino`, and `/api/estado` unchanged.

## Evidence and gate

The route regression cases compare `/` and `/app.html` byte-for-byte and require the retired page routes to return 404. The manifest and cache tests assert the new start route and absence of legacy cache entries. `interface/app.html` is guarded at its measured 19,552-byte baseline.

No deployment or post-merge polling measurement is included. The `/api/camino` cadence is re-measured only after the Sovereign merges this exact head.
