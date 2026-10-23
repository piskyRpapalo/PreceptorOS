# PreceptorOS · first AI user journey · E8

This page is the operator's evidence sheet for the first real AI-authored
creation. It separates runnable judges from the physical journey. The fixture
is test-only data and does not stand in for the author's own creation.

## Journey to perform on the rack

1. Open the rack app and explicitly generate the voice catalog and WAV for the
   author's chosen statement. Listen to the statement through the rack output.
2. Open the web creation page, create or unlock the author's web identity, and
   draw the ribbon with keyboard guidance. Record the same frame from the
   visual and touch channels when those devices are available.
3. Load the generated voice files, listen again, sign the frame and statement,
   and download the package. Record the package ID and frame/audio SHA-256
   values; do not copy the private key or personal rack addresses here.
4. Import the package in the app with its explicit **Verify and import**
   action. Save the returned `/creaciones/<id>` URL.
5. Open that URL from a separate browser context on the rack. Record the
   service version and HTTP status, verify the same ID and hashes, render the
   ribbon, and play the WAV. Restart the app and repeat the read.
6. Keep the node charter flow separate. Its `encolado` receipt is not the
   creation URL and does not mean that the creation is LIVE.

## Evidence captured in this session

| Measurement | Result |
|---|---|
| OpenSSL and the JavaScript WebCrypto package verifier agree on the signed fixture | `VERDE` in Node; E8 judge compares manifest ID, frame hash, and audio hash |
| Rack HTTP upload/read/resource-pin/restart test | `NO_DATA`; sandbox denied loopback socket bind |
| Real browser opened the rack URL from a second context | `NO_DATA`; no rack browser control is available in this session |
| Physical keyboard-only drawing | `NO_DATA`; not measured on rack hardware |
| Physical touch | `NO_DATA`; no physical touch device measured |
| Audible guidance and statement through rack output | `NO_DATA`; no rack audio output measured; the Piper engine was absent in the inspected sandbox |
| User-created package, rendered on rack and reread after restart | `NO_DATA`; no real first-user journey was performed |
| LIVE seal | `PENDING`; only the Mesa can assign it after independent rack evidence |

The automated loopback case is executable on the rack and skips with the
concrete socket cause in this sandbox. Its package fixture proves the byte
contract only. Synthetic pointer, keyboard, and clip-sequence tests do not
prove physical accessibility or audible playback. No result here accredits
the rest of the house.

## Commands

```sh
python3 -m unittest test_creacion_recorrido test_creacion_publicacion
CREATION_JOURNEY_SABOTAGE=1 python3 -m unittest \
  test_creacion_recorrido.CreationJourney.test_sabotage_switch_rejects_changed_signed_bytes
```
