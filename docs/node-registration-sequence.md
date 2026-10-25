# Node registration sequence: scaffold and bridge measurement

**Date:** 2026-10-25. **Status:** proposed; `REQUIRES_FIRMA` at merge. **Branch:** `mistral/r-nodo-secuencia-20261025`. No push, merge, deploy, key generation, signed credential creation, or database write was performed. The UI constructs only an unsigned pending cédula draft.

## What the scaffold does

- `interface/app.html` exposes a localized node-name preview in Settings, shows the canonical unsigned cédula and consequences, and requires explicit local consent before submission.
- `interface/node_registration.js` defines the state machine and signer slot. The phone never signs; the slot reports pending/signature-missing and submits the `firma: null` draft only after consent. The test-only signer labels every simulated result `test_stub_no_signature`.
- The production Door 1 adapter targets `POST https://api.preceptoros.org/api/v1/cedulas`, as selected by the Sovereign. `nodo_export.py` uses the same endpoint for its existing signed-cédula path. The old `/aduana/cedulas` path is retired by the ruling.
- `node_registration.py` and `/api/nodo/door1/preview` form a loopback-only preview receiver. It accepts only the explicit `test_stub_only` envelope, returns `persisted: false`, and reports `stub_not_published`. It does not call the public endpoint, mutate a catalogue, or implement the web receiver.
- `interface/sw.js`, the PWA static map, and `version.py` include the new script so the app can deliver the scaffold consistently.

The local dry-run test passes an unsigned canonical cédula through the state machine and an injected transport adapter, redirects only inside the test to the loopback stub receiver, and receives a synthetic count of one. That count belongs to the test stub; it is not a registry or web catalogue count. No live gateway request was made. Browser CORS behavior and the public receiver contract remain `NO_DATA` for the separate web piece.

## R-PUENTE measurement

Machine: Beelink host and USB-attached Android handset, 2026-10-25 18:00 UTC. Commands and measured results:

| Command / yardstick | Result |
|---|---|
| `tailscale serve status` | Existing tailnet-only Serve path proxies to `127.0.0.1:8740`; hostname omitted from this artifact. |
| `ss -ltnp \| grep ':8740'` | Service listens on `127.0.0.1:8740`. |
| `adb reverse --list` | `tcp:8740` reverse is present over USB. This is not a no-USB success. |
| `adb shell ip -brief addr` and `adb shell dumpsys connectivity` filtered for VPN | The attached handset showed Wi-Fi only and no active Tailscale VPN network. Address and SSID values omitted. |
| `adb shell toybox ping -c 1 -W 2 <node-tailnet-address>` | 1 packet sent, 0 received. The node tailnet address is omitted under the private-identifier rule. |
| `tailscale ping --c 1 <Android-peer>` | Host reached an Android tailnet peer, but the active peer did not match the USB-attached handset; its identifier is omitted. This does not prove the commissioned phone path. |

**Current phone-to-node path without USB: NO.** The attached handset has no active Tailscale VPN and the direct probe failed. **Persistence across disconnect/restart: NO_DATA**, because no active phone tunnel was available to disconnect or restart. No Tailscale login, settings, or node service configuration was changed. A successful host-to-peer ping is not substituted for a phone-originated test.

## End-to-end result and remaining boundary

The synthetic request → loopback node preview receiver → synthetic catalog count path is covered by the test suite, but it did not traverse the physical phone or Tailscale. Physical end-to-end over the bridge is **NO_DATA** with cause: the attached handset had no active tailnet route. The signed ruling now selects a rack ceremony with the Sovereign present and a trusted device holding the key; the exact device and backup/recovery method remain for the ceremony design and later anchor review. No real signer or trust anchor was added. The honest calendar date for the “1–2 clicks” claim remains **NO_DATA** until a physical phone-to-catalog run measures the complete path. A signed credential, public registry write, or real catalogue update remains outside this scaffold.

## Review surface

The app UI/state machine, loopback preview receiver, and PWA asset/version alignment are one proposed app piece. The private web receiver/catalogue projection and Sovereign signer/trust ceremonies remain separate reviewed pieces. No production behavior is claimed as measured from this proposal.
