# PRECEPTOR — Rack node (unsigned draft)

**Status:** DRAFT · REQUIRES_FIRMA · not authoritative

**Evidence measured:** 2026-10-25 23:08 UTC, read-only local checks under the Sovereign-signed device scope.

## Capability evidence for items 18–20

The exact item definitions and field mapping are `NO_DATA: not present in the repository source reviewed for this draft`. This section records only the observed capabilities below; it does not assign an infrastructure development level.

| Capability | Measured result | Method and limit |
|---|---|---|
| Local app API | `GET /api/estado` on loopback port `8740` returned HTTP `200`. | `curl -sS -o /dev/null -w '%{http_code}' --max-time 3` against loopback. Response body/version not recorded in this scope. |
| Service controller | `bin/preceptoros-servicio estado` exited `0` and reported running. | Output content, PID, and arguments were not recorded. |
| PWA process | Matching process-name boolean: present. | Read-only `/proc` command-line match; no arguments were emitted. |
| Service process | Matching process-name boolean: absent. | Same boolean-only check. This does not negate the controller's running status. |
| systemd units | `preceptoros-servicio` and `preceptoros-pwa` both reported inactive. | `systemctl is-active`; the PWA user unit is enabled. Unit state is distinct from the observed local HTTP response and process check. |
| TCP listener bindings | 24 listeners observed: 14 loopback, 7 non-loopback, 3 wildcard. | `ss -H -ltnp`; no IP literals or listener addresses are included in this draft. This is a snapshot, not an exposure assessment or authorization to change configuration. |
| Disk capacity | 30,027,440,128 bytes free; 982,240,026,624 bytes total. | `shutil.disk_usage` on the configured temporary filesystem. This is a point-in-time measurement after the reported cleanup; no earlier comparable byte-level baseline is available here. |

## Authority and limits

- These observations describe one measurement window only; they do not establish a durable guarantee or delegated infrastructure level.
- No listener, service, firewall, or system configuration was changed.
- No device action outside the signed read-only exposure scope was performed. Item 16 remains unexecuted.
- A separate Sovereign signature is required for this device before this draft becomes authoritative. Other devices require their own measurement and signature.

**Sovereign signature:** pending

**Effective date:** `NO_DATA` until signed

**Next review:** `NO_DATA` until signed
