# Modelos → Mundo: catalogue and lazy OpenWorld door

Status: proposal on branch proposal/modelos-web-panel-20261107; no merge.
Base measured: 81a99089390cf4da5464d92a348844b09581aa41 (main, 2026-11-07).

## Measured contract before the change

- interface/app.html supplies the #panel-modelos shell, #tab-modelos, and #estado in the header.
- interface/app.js previously filled the model panel from GET /api/lab. It rendered modelos.mini, modelos.grande, modelos.eleccion, and the election's tier 1, tier 2, and adapter. bin/preceptoros-pwa routes that request to lab.py::modelos_lab; there is no /api/modelos route.
- Hexelion chat returns the measured model in respuesta.maquina.modelo and elapsed time in respuesta.maquina.ms. The header renders these only after a measured response. The arrow's last-response label uses those same fields; before one exists it says NO_DATA with a cause.
- The public door is https://preceptoros.org/openworld/. On 2026-11-07 it answered HTTP 200. The page contains the ephemeral visitor and Acho language surfaces. The response did not declare frame-ancestors or X-Frame-Options; this is only a measured header result for that response.

## UI and data contract

The visible tab label is **Mundo**. Its stable internal id remains tab-modelos / panel-modelos; this avoids changing zone history and routing. The header arrow opens the local model catalogue. It has aria-haspopup, aria-expanded, Escape-to-close, focus restoration, and a 44 px target.

The catalogue is read on demand from /api/lab, not from an invented endpoint. It accepts only the measured object structure. Missing or malformed fields clear the list and produce NO_DATA with a cause. Names, availability, stale state, and causes are rendered with textContent, never inferred by counting or interpolating HTML.

The OpenWorld iframe has no src at startup. Opening Mundo first probes the fixed public URL with an anonymous, no-cors request and an eight-second limit; only a resolved opaque response permits the iframe navigation. A failed probe shows NO_DATA and leaves src absent. A frame that does not complete within 15 seconds is cleared and reports a cause. A browser load event measures navigation completion only: same-origin policy prevents this app from claiming the frame's HTTP status or interpreting its document. The user can also open the public door directly with the visible link.

## Reuse in the app MVP

This is a shell-and-door mechanism, not a second game implementation. An app embeds the canonical OpenWorld page, where the browser's ephemeral visitor can play and try Acho. The shell supplies a lazy, user-opened frame, honest offline state, and an external fallback link. It does not create an account, mirror the world, or send app state to the public site.

## Verification and delivery

- interface/modelos_web.js owns the dropdown and lazy frame behavior.
- bin/preceptoros-pwa, interface/sw.js, and version.py register/version the new asset; app CSS/JS query versions and the service-worker seal move together.
- Node sabotage cases cover no startup request, malformed catalogue, Escape focus return, offline probe, iframe timeout, and the limit of a cross-origin load event.
- The running local service was measured separately and uses a runtime tree outside this checkout. A draft GitHub PR alone cannot update that running tree. A preview from this proposal must use a separate port; deployment to the existing service remains a separate, explicit operation after review.

## Log

- 2026-11-07: proposal implemented on a branch from measured main. Repository gate: 1,242/1,242 across 106 suites; all 47 sabotage cases detected. The proposed visible name is **Mundo**.
