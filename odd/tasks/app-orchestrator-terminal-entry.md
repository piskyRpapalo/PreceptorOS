# Local orchestrator terminal

Expose the existing local chat directly from each map skin.

Measured on app main `3a96d50`: `/dashboard.html` renders the console; submit POSTs to `/api/lab`; `lab.responder` calls `di_soberano("orquesta")`. `bin/preceptoros-pwa` binds to loopback by default (`test_pwa_bind.py`). This is local chat, not a shell or remote service.

Change: visible keyboard-focusable link in all three map headers; renew service-worker cache and served-version fingerprint.

Boundary: physical installation, availability and model response are NO_DATA until exercised on the node. No inference, bind, network or data behavior changes.

Log: 2026-10-30 — proposed; CI and human review pending.
