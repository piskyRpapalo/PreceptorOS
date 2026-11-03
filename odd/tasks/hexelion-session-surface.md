# Hexelion session surface

## Explore · plan before code

Authority: Sovereign FIRMA in buzon#30 comment 6592198560, 2026-11-03;
firmas book and DECISIONES_MAIN consulted. Reading scope: PWA static routes,
HTML, conversation handler, SW/version, native voice and install entry points.
Baseline app main c32e88f9; live checkout is older 0900d858. This is a proposal,
not a deployment. No service, credential, aula setting or phone installation.

Measured on the local app host: :8740 serves the basic map at /, the older
dashboard at /dashboard.html and the tabbed app at /app.html. /api/estado
returns 200, version 4ad608eb4254; /api/voz says no Piper binary. The aula
HTML at :8080 returns 200; terminal :8831 refuses connection. The existing
POST /api/lab calls the local pipe orchestrator and records attributed channel
messages. It does not call the tower or authenticated aula. Source existence
does not establish an operational identity→aula join.

## Implement

Add /hexelion.html inside the existing server/PWA, not another service. Make
it a quiet session room: Hexelion title, clear status, attributed conversation,
one explicit send action, readable receipt and links back to the existing
map, tabbed app and dashboard. Refresh uses GET /api/lab only after a gesture;
no startup request to external origins, no private endpoint from web code.
Use the existing POST /api/lab and its actual speaker/channel/sequence; never
relabel the local orchestrator as a tower answer. Render text with textContent.
No response means NO_DATA; no placeholder model answer and no automatic retry.

Read aloud will invoke a separately reviewed local-only reader on demand;
until it exists, failure is visible NO_DATA. Read exactly the visible attributed
turn, never hidden instructions. Each focus has its actual viewport coordinate
and an equivalent text label. Controls are >=44 CSS px, keyboard usable, with
visible focus, reduced-motion support and a 390 px layout. Existing terminal
skins share one session link; their pinned language files are untouched.

Expose local aula only on a browser whose own origin is loopback; a remote
phone's localhost is not the app host. Other contexts declare NO_DATA rather
than guessing a private address. The actual aula identity/ACL bridge stays
separate. No public remote-control API or new principal.

Wire static routes, SW shell and version.ARMAZON together; change the cache
namespace. Preserve /, history, signatures and existing app functions.

## Check

Directed browser tests: real served candidate HTML at desktop/mobile sizes,
keyboard/focus/44px targets, DOM-safe malicious text fixture, actual failed
backend path and no duplicate send. Fixtures remain explicitly synthetic.
Measure a real local-model request separately, with actual speaker, channel n,
response digest and cause; model availability may be NO_DATA. Headless mobile
screenshots do not prove physical Android behavior or audible speech.
Run the repository gate; report skips and sabotage separately. Capture the
before/after UI privately, publish only scrubbed screenshots. J1 is the named
design requirement; other J-* mapping remains NO_DATA.

Return: remove this surface/static assets and links; existing services remain.
The Desk controls FIRMA+FIRMO and seal letters. No web edit: coordination sent
in buzon#30 comment 6592221232; Claude retains the formal web/AC-0 rail.
