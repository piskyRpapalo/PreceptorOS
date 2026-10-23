# F3 · Rack creation and LIVE evidence runbook

This is an operator procedure for the first signed creation. Run it on the
rack, from the PreceptorOS checkout, with the existing PWA bound to loopback.
It does not deploy the public site, open a listener on another interface, or
create a tunnel. Keep the package and generated voice files outside the Git
worktree; never attach them to a PR.

## 0. Preconditions and stop rules

1. Confirm the installed app is the reviewed build. Record the app commit from
   the operator's checkout and the sanitized `/api/estado` version below.
2. Confirm the process bind is loopback. If the bind is anything else, stop
   with `NO_DATA · configured app bind is not loopback`; do not change network
   exposure for this run.
3. Check the existing service before starting it. Do not launch a second copy.
   If it reports older code, restart only through the rack's established
   service procedure and verify `/api/estado` again.
4. The public creation page must return HTTP 200 and load the reviewed E4
   assets. E4 merge does not itself deploy the public site. If the page or
   required assets are absent, stop with `NO_DATA · reviewed creation page is
   not served`; do not deploy from this procedure.
5. The app voice panel currently calls `POST /api/creaciones/voz`, while the
   reviewed server has no handler for that route. Do not treat a 404 as voice
   generation. The local `voz_creacion.generar()` procedure below uses the
   shipped local generator directly. If Piper or its model is unavailable,
   stop with the generator's `NO_DATA` cause.

## 1. Start and identify the existing PWA

Run from the repository root. Keep the first command's full output on the
rack; its process information is not PR evidence.

```sh
python3 - <<'PY'
import os
bind = os.environ.get("PRECEPTOROS_PWA_BIND", "127.0.0.1")
if bind not in ("127.0.0.1", "::1", "localhost"):
    raise SystemExit("NO_DATA · configured app bind is not loopback")
print("GREEN · configured bind is loopback")
PY

./bin/preceptoros-servicio estado
```

If the service is stopped, start the existing service:

```sh
./bin/preceptoros-servicio arranca
```

Expected: it reports the service started and the HTTP probe responds. If it is
already running, do not start another process. An address-in-use error, an
unexpected bind, or an unresponsive service is a stop condition with the
specific cause recorded as `NO_DATA`.

Read readiness and version without copying model paths or other local state:

```sh
curl --noproxy '*' --max-time 5 -fsS http://127.0.0.1:8740/api/estado |
python3 -c 'import json,sys; d=json.load(sys.stdin); v=d.get("version") or {}; ok=(d.get("estado")=="ok" and bool(v.get("huella")) and not v.get("faltan")); print(("GREEN" if ok else "NO_DATA")+" · app state="+str(d.get("estado"))+" · version="+str(v.get("fecha"))+"/"+str(v.get("huella"))+" · files="+str(v.get("ficheros"))+" · missing="+str(len(v.get("faltan",[])))); sys.exit(0 if ok else 1)'
```

Expected: `GREEN`, state `ok`, a non-empty version fingerprint, and zero
missing shell files. Save only those fields, the HTTP status, and the reviewed
commit. Do not copy the raw response.

## 2. Generate one local voice profile and statement

Use a temporary directory outside the repository. The statement becomes
public in the signed creation package; enter only text the author intends to
publish. The generator returns `NO_DATA` rather than changing voice or using a
remote service if its local engine or model is missing.

```sh
umask 077
F3_OUTPUT_DIR="$(mktemp -d)"
export F3_OUTPUT_DIR
python3 - <<'PY'
import base64
import hashlib
import json
import os
from getpass import getpass
from pathlib import Path
from voz_creacion import generar

text = getpass("Author statement (it will be public in the creation): ")
result = generar(text)
if result.get("estado") != "ok":
    raise SystemExit("NO_DATA · " + str(result.get("causa", "local voice generation failed")))
catalog, declaration = result["catalog"], result["declaration"]
if catalog["profile_id"] != declaration["profile_id"]:
    raise SystemExit("NO_DATA · voice profile mismatch")
out = Path(os.environ["F3_OUTPUT_DIR"])
files = {
    "creation-voice.json": json.dumps(catalog, ensure_ascii=False).encode(),
    "creation-declaration.json": json.dumps(declaration, ensure_ascii=False).encode(),
    "declaration.wav": base64.b64decode(declaration["data"], validate=True),
}
for name, data in files.items():
    with (out / name).open("xb") as stream:
        stream.write(data)
wav_hash = hashlib.sha256(files["declaration.wav"]).hexdigest()
if wav_hash != declaration["sha256"]:
    raise SystemExit("NO_DATA · generated WAV hash mismatch")
print("GREEN · one profile; catalog, declaration, and WAV ready")
print("profile_id=" + catalog["profile_id"])
print("declaration_wav_sha256=" + wav_hash)
PY
```

Expected: `GREEN`, one `profile_id`, and a matching WAV hash. A generator
failure, oversized catalog, invalid WAV, or profile change is `NO_DATA` with
the returned cause; do not substitute a different voice silently.

## 3. Create and sign in the web page

1. In a browser on the rack, open `https://preceptoros.org/creation.html`.
   Confirm HTTP 200 and that the page loads the reviewed E4 scripts. If E4 has
   not been deployed, stop with `NO_DATA · public creation page not deployed`.
2. Use the web identity controls to create or unlock the author's web identity.
   Its private key stays in that browser; do not export or capture it.
3. Choose `creation-voice.json`, `creation-declaration.json`, and
   `declaration.wav` from the temporary output directory, then activate **Load
   local voice files**. Confirm one profile is shown and play the statement.
4. Draw one ribbon using keyboard guidance. Repeat the state when needed; record
   whether the audible guidance worked. If available, repeat with a physical
   touch input. Emulated input is not evidence of physical touch.
5. Activate **Sign drawing and statement**, then **Download creation**. Keep
   the downloaded JSON outside the worktree. The signature binds the exact
   manifest bytes and the manifest hashes bind the frame and WAV bytes.

Expected: the page reports a signed creation and the download exists. If the
voice does not play, the web identity cannot sign, or the signature does not
verify, stop with the observed `NO_DATA` cause or validation failure.

## 4. Verify the downloaded bytes locally

Set `PACKAGE_FILE` to the downloaded package path in the current shell. Do not
paste that path into a receipt. This command verifies Ed25519 with OpenSSL and
prints only hashes and the content-derived creation ID.

```sh
python3 - "$PACKAGE_FILE" <<'PY'
import hashlib
import json
import sys
from pathlib import Path
from creacion_import import validate

raw = Path(sys.argv[1]).read_bytes()
value = validate(raw)
files = value["files"]
receipt = {
    "package_sha256": hashlib.sha256(raw).hexdigest(),
    "creation_id": value["id"],
    "manifest_sha256": hashlib.sha256(value["manifest_bytes"]).hexdigest(),
    "frame_sha256": hashlib.sha256(files["frame.json"]).hexdigest(),
    "audio_sha256": hashlib.sha256(files["declaration.wav"]).hexdigest(),
    "signature": "VERIFIED",
}
if receipt["creation_id"] != receipt["manifest_sha256"]:
    raise SystemExit("FAIL · creation ID differs from exact manifest hash")
print(json.dumps(receipt, sort_keys=True))
PY
```

Expected: exit 0 and `signature=VERIFIED`. Record the package SHA-256, creation
ID, frame SHA-256, and audio SHA-256. A bad signature, hash mismatch, missing
OpenSSL, invalid WAV, or malformed package stops the journey; record the exact
bounded cause, not the package contents.

## 5. Import/publish through the rack UI

1. Open `http://127.0.0.1:8740/app.html` in the rack browser.
2. Open **Settings → Publicar una creación firmada**.
3. Select the exact JSON verified in step 4. File selection alone must not send
   anything. Activate **Verificar e importar** once to submit the package.
4. Record the HTTP result and returned relative URL. First publication expects
   HTTP 201; an idempotent repeat may return HTTP 200. The status must be
   `publicado`, and the returned creation ID must equal step 4's ID.

Expected: the UI presents `/creaciones/<id>`. A rejected origin, invalid
signature, wrong ID, or failed write is a failure; do not label it published.

## 6. Independently read and download the published bytes

This read uses a fresh HTTP client and bypasses browser storage. Set
`PACKAGE_FILE` and `CREATION_ID` from the sanitized step 4 receipt.

```sh
python3 - "$PACKAGE_FILE" "$CREATION_ID" <<'PY'
import hashlib
import sys
from http.client import HTTPConnection
from pathlib import Path

expected = Path(sys.argv[1]).read_bytes()
identifier = sys.argv[2]
if len(identifier) != 64 or any(ch not in "0123456789abcdef" for ch in identifier):
    raise SystemExit("FAIL · invalid creation ID")
connection = HTTPConnection("127.0.0.1", 8740, timeout=5)
connection.request("GET", "/api/creaciones/" + identifier,
                   headers={"Cache-Control": "no-cache"})
response = connection.getresponse()
received = response.read()
no_store = response.getheader("Cache-Control", "").lower() == "no-store"
connection.close()
same = received == expected
print("HTTP=" + str(response.status) + " no_store=" + str(no_store)
      + " exact_bytes=" + str(same)
      + " package_sha256=" + hashlib.sha256(received).hexdigest())
if response.status != 200 or not no_store or not same:
    raise SystemExit("FAIL · independent package read differs")
print("GREEN · independent read returned the exact signed package")
PY
```

Expected: HTTP 200, `no_store=True`, exact bytes, and the same package SHA-256
as step 4. A mismatch is `FAIL`, not `NO_DATA`.

Now open a separate private window or browser profile on the same rack and
navigate to `http://127.0.0.1:8740/creaciones/<id>`. Do not reuse the author's
browser storage. Expected: **Signature verified · `<id>`**, the same ribbon,
and the audio control plays the signed statement through physical output.
Capture the browser context as “independent”; do not capture private profile
data. Afterward restart the existing PWA using its normal rack procedure and
repeat both reads. The same ID and package hash must remain.

## 7. Run the socket-enabled judges on the rack

Run from a checkout containing E8 (`4fe095c` or its descendant). These judges
were `NO_DATA` in the authoring sandbox because it denied loopback binds; on the
rack, a bind denial remains `NO_DATA`, never a pass.

```sh
python3 -m unittest test_creacion_publicacion
python3 -m unittest test_creacion_recorrido
python3 -m unittest \
  test_creacion_recorrido.CreationJourney.test_upload_fresh_read_fixed_resources_and_restart
CREATION_JOURNEY_SABOTAGE=1 python3 -m unittest \
  test_creacion_recorrido.CreationJourney.test_sabotage_switch_rejects_changed_signed_bytes
python3 -m unittest \
  test_creacion_recorrido.CreationJourney.test_sabotage_switch_rejects_changed_signed_bytes
TMPDIR=/tmp ./bin/pruebas --rapido
```

Expected on the rack: publication 7/7; journey 3/3 with no socket skip; the
focused restart judge 1/1; both sabotage commands pass; the app corridor is
green. The sabotage switch bypasses only the signed file hash/size comparison
for the deliberately altered sample bytes. The following run without the
switch must still reject those bytes. Any other test failure remains a failure.

## 8. E8-final human gesture and LIVE evidence

The creation author signature and the host node's signed credential are
separate proofs. The existing export UI handles the **host node credential**;
it does not export or sign the artwork.

1. After steps 1–7, the Sovereign opens **Settings → Identidad del nodo**.
2. The Sovereign selects the already signed host-node credential JSON.
3. The Sovereign explicitly activates **Enviar a la aduana** once. File
   selection alone sends nothing. The operator records the response status and
   sanitized receipt state.
4. If the receipt says `encolado`, record exactly `encolado · queued`; it does
   not prove delivery, independent creation read, or LIVE. Never relabel it.
5. Attach only a scrubbed evidence receipt containing:
   - reviewed app commit and `/api/estado` version fingerprint;
   - HTTP status for import, independent GET, and post-restart GET;
   - package SHA-256, creation ID, manifest SHA-256, frame SHA-256, and audio
     SHA-256 before and after read-back;
   - signature-verification result and viewer result from a fresh browser
     context;
   - measured physical audio playback and physical touch result, each with its
     device-independent method and date;
   - the node-credential export receipt state, kept separate from creation
     evidence.

Only the Mesa may seal LIVE after reviewing the independent HTTP read, exact
hash continuity, signature, persistence after restart, rendered drawing,
physical audio evidence, touch evidence, and the Sovereign's explicit
credential-export gesture. This runbook and its test fixture never award that
seal. `encolado` alone is not LIVE.

## Current authoring-session limits

`NO_DATA · this sandbox cannot exercise the rack browser, bind its loopback
server, play physical audio, or measure a physical touch surface.` The public
E4 deployment, local Piper/model availability, independent rack browser, real
author creation, host credential gesture, persistence on the rack, and LIVE
decision remain unmeasured here. Record each as `NO_DATA` with its observed
cause until the rack procedure produces evidence.
