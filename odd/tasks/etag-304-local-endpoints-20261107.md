# Conditional cache for two local snapshots

Status: implementation proposal for PreceptorOS. This is the small ETag/304 slice from the 2026-11-07 Joyas round 2 list. It does not add polling, a service-worker route, a download manifest, or remote transport.

## Contract

- `GET /api/estado` and `GET /api/manifiesto` may return a strong ETag derived from the exact UTF-8 JSON response bytes.
- A matching `If-None-Match` (including a weak match, a comma-separated list, or `*`) returns `304` with the same ETag, `Cache-Control: private, max-age=60, must-revalidate`, no body, and no `Content-Length`.
- A changed representation returns `200`, a new ETag, the same cache policy, and the full body. The 60-second freshness window bounds reuse; after that the browser must revalidate.
- The allowlist is deliberately narrow. Node identity, Hexelion, inbox, captured user content, writes, errors, and non-GET responses do not receive ETags. Existing `no-store` behavior remains authoritative.
- The local server API is distinct from the PWA service-worker cache list and world-state. This slice does not add or imply a map poll loop or download flow.

## Checks

The directed tests exercise first response, same-body 304, changed-body 200, weak/list matching, manifest revalidation, no-store identity responses, and method gating. The repository gate remains the acceptance yardstick before the draft PR is published. Browser and physical-device cache behavior remain NO_DATA until exercised.
