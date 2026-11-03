# Install the app from its origin · plan before code

Authority: Sovereign FIRMA buzon#30 6592198560. App is access to the open-source
web, per the prior decree cited in 6589938394. Coordination with TF was sent
before any web edit in 6592221232. Claude retains preceptoros-web and APP#151.
This dependent slice is stacked over the native reader/surface for isolated
review and cache alignment. The Desk retargets after predecessors land.

## Explore and decision

Choose the existing PWA: the app already has manifest, icons, SW and a local
HTTP shell. It avoids a new Android binary, installer/service or identity.
Installing a PWA installs the client shell, not Python, private node services,
an aula credential or a signing mandate. A public-world PWA remains a window;
access to local hardware still requires the existing authenticated APP door.

Two-click path, on browsers that actually offer beforeinstallprompt:
1. On the app's own secure origin, choose Install Hexelion.
2. Confirm Install in the browser's native dialog.

A link from the public web to a different private origin, followed by the
button and native confirmation, is at least three actions, not two. To offer
two clicks FROM the public web, Claude must integrate this controller into
the existing public PWA on that same origin, preserving its own manifest ID
and entry. This PR changes no public web route or HTTPS hosting. Do not expose
a private backend or proxy to meet a click count. MANOS owns any hosting work.

HTTPS or browser-trusted loopback is required. A plain private-network URL on
a phone is not trusted loopback. Safari/manual-menu installation may take more
steps; unsupported prompt, absent eligibility, insecure context, dismissal and
already installed must be explicit states, never simulated installation.

## Implement

Use one install button in the session header; no startup install, remote load
or telemetry. Retain the native event, show eligibility, invoke prompt only
on a trusted click. Do not equate userChoice=accepted with appinstalled.
Handle late/repeated events and prevent double prompt. Keep the current
manifest identity with explicit id=/ and scope=/; enter at /hexelion.html.
Existing map/dashboard stay linked. Add standalone/mobile icons to precache,
and align static route, SW and version with this feature.

The web handoff is a proposal to the Mesas: use the existing public manifest
and one same-origin button; do not transplant private start URLs or create a
second PWA identity. The same event/state behavior should be used in all
terminal skins; one link leads to this shared install surface.

## Check

Test synthetic event lifecycle separately from real browser manifest parsing,
SW activation, cache contents and Chromium installability diagnostics. No
fixture counts as an OS installation. Physical phone install remains MANOS
and NO_DATA until observed. Read-only current phone screenshot shows the
public world, not this candidate; no new phone control or install was used.

References: [installability](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable),
[native prompt](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/How_to/Trigger_install_prompt).
J1: focus, coordinates, native text equivalent and >=44px. Other J-* mapping
NO_DATA. Return: remove install controller/restore prior manifest entry;
no runtime data, keys, model or server state is changed.
