# Aula connection and ACL preparation · body phases 1.2 / 1.3

## Explore · measured 2026-11-03

Reading depth: installed Open WebUI connection/config, authentication and
model-access functions; read-only selected database fields; loopback HTTP
version/catalogs and unauthenticated API. No credentials, user records or
private model names were printed. No administrative change was performed.
Authority: Sovereign backend commission; firmas/LIBRO_DE_FIRMAS.md and
DECISIONES_MAIN consulted. This is preparation for MANOS, not commissioning.

| Measurement | Result / limit |
|---|---|
| GET /api/version and installed package metadata | 0.11.1 |
| Active user service / listening socket | Active; loopback port 8080 |
| Unit and process OLLAMA_BASE_URL | http://127.0.0.1:11434 |
| Read-only config table | key/value rows, not legacy config.data |
| Persisted ollama.base_urls | One non-loopback HTTP destination, port 11434; neither declared local URL nor tunnel |
| Persisted ollama.api_configs | Index 0 enabled, empty prefix/model_ids; connection_type local |
| ollama.enable | true |
| API keys / endpoint restrictions | Both false; allowed-endpoint string empty |
| User roles | One admin; zero non-admin accounts |
| Model registry / groups / access grants | One model row; zero groups / grants |
| GET local :11434/api/tags | 200; 29 catalog entries |
| GET tunnel :21434/api/tags | 200; 15 catalog entries |
| GET aula /api/models without credentials | 401 |

Catalog counts prove reachability, not inference or LoRA identity. No authorized
LoRA ID was supplied or established. An absent label cannot prove a model is
or is not an adapter. A UI name, alias or count is not an authorization.

Installed source: routers/ollama.py:224–229 resolves persisted Config values;
GET /ollama/config:287–293 uses the same resolver and requires admin.
POST /ollama/config/update:303–330 persists the list/configs and clears model
caches. Therefore the unit's variable alone does not establish the selected
runtime connections. The DB snapshot plus resolver explains precedence; an
authenticated live GET /ollama/config remains NO_DATA, no admin session used.

Source provenance (SHA-256 of installed files, not an upstream version claim):

- routers/ollama.py: 8fd607285bbce3881c1a1eb3cd9bac0e218d0a878eabb15366e87c882eacb531
- utils/auth.py: b67719dca41439a2a407b6207f89ed127b9e363403cc2ffa30f1148ba7a22f69
- utils/access_control/__init__.py: af269f2055421e27f7268a4bd8238769f22c99c59059c5b153fdeeb6581fa8f7

## Implement · MANOS sequence, one operation at a time

Do not execute these administrative steps as an agent. Preserve admin access,
the database, chats and both model catalogs. Do not reset the database, disable
persistence, change global OLLAMA_HOST, edit units or restart all services.

### 1. Capture the return point privately

MANOS opens the current admin session. Record the installed version and the
three measurements above again. Create a private 0700 directory outside Git
and served roots. Assign its path to AULA_PRIVATE_DIR. Use a separate 0600
curl configuration file AULA_ADMIN_CURL containing the existing admin-session
authorization; never copy it to a PR, model prompt, shell history or receipt.
No new key is needed for these reads. Use SQLite's online backup facility to
back up the running database including committed WAL data; do not copy only
webui.db while it is live. Keep backup permissions 0600 and record its digest
privately. Do not publish database contents or a user-bearing hash manifest.

Capture the effective connection response without terminal output:

```sh
curl --fail --silent --show-error --config "$AULA_ADMIN_CURL" \
  http://127.0.0.1:8080/ollama/config \
  --output "$AULA_PRIVATE_DIR/connections.before.json"
```

The private config must contain fail-on-error/timeouts, no verbose tracing,
and only the intended loopback destination. Verify the result is the expected
object with ENABLE_OLLAMA_API, OLLAMA_BASE_URLS and OLLAMA_API_CONFIGS. If the
version/config differs from the measured snapshot, stop this operation and
re-plan from the new response. Capture admin model/ACL settings separately
through the UI and preserve existing user permissions. There is no user/key
inventory permission to enlarge here.

### 2. Stage exactly two explicit connections

In Admin Settings → Connections, change the single stale connection to
http://127.0.0.1:11434 and add http://127.0.0.1:21434 as a separate second
Ollama connection. Preview before saving. The original non-loopback URL is
retained in connections.before.json for return, never in public artifacts.
Keep index association of every api_config explicit. If additional connections,
provider credentials, headers or nonempty filters appear, reconcile them
before saving; never overwrite an unknown config with an empty dictionary.
The measured first connection has no prefix/model allowlist. Preserve local
model IDs and local availability. Give the second connection a distinct prefix
only if required to avoid a measured ID collision; use its resulting exact
catalog IDs consistently for registry/ACL tests, never guess the prefix syntax.

Equivalent API operation for a privately reviewed payload (MANOS only):

```sh
curl --fail --silent --show-error --config "$AULA_ADMIN_CURL" \
  --request POST --header 'Content-Type: application/json' \
  --data-binary @"$AULA_PRIVATE_DIR/connections.proposed.json" \
  http://127.0.0.1:8080/ollama/config/update \
  --output "$AULA_PRIVATE_DIR/connections.applied.json"
```

The proposed object must retain ENABLE_OLLAMA_API=true and reviewed configs,
with OLLAMA_BASE_URLS=["http://127.0.0.1:11434","http://127.0.0.1:21434"].
Both config indexes must be explicit. The source drops config indexes outside
that list. Read GET /ollama/config back and compare; HTTP 200 alone is not
configuration verification. Recheck catalog separation and an existing local
mini as admin. No service restart is required by this endpoint's implementation.

### 3. Bind identity before creating access

Prerequisite: odd/tasks/identity-aula-audit.md and the reviewed typed
browser→APP proof must be implemented and measured. The current visitor signer
only accepts invocation/adoption, so this prerequisite is presently NO_DATA.
Do not create a restricted user until it passes. The admin is never the visitor.

When satisfied, MANOS associates a non-admin technical login with the existing
verified subject and host consent evidence; no replacement signing identity.
Record subject, scope, expiration and revocation association privately. Keep
the API credential in the app's protected storage, outside browser/model access.
Do not turn on general signup to implement this association.

### 4. Apply server-side model ACL and endpoint limits

Select the exact real LoRA ID from the reachable catalog and its authority
record. Preserve a local copy of this decision and selected IDs; an unverified
candidate cannot be enabled. Register the required model/base-model entries
and grant read only to the associated restricted subject/group. Inspect inherited
base-model access as well. Keep foreign models private to their current owners;
do not create public read grants or grant the visitor admin/creation/sharing/
connection-management privileges. Admin and existing local minis keep access.

Connection model_ids filters only trim catalogs (ollama.py:422–425); they are
not ACL. The installed check_model_access function rejects unregistered and
ungranted models for non-admins and checks chained base models. Confirm
BYPASS_MODEL_ACCESS_CONTROL stays false and proxy passthrough stays disabled.
Do not rely on hiding a model in the selector or a prompt-level instruction.

Use Admin Settings to enable API keys and give only this restricted subject
the features.api_keys permission. Keep the API key separate from Ed25519.
Enable endpoint restrictions with only /api/models,/api/chat/completions for
the initial path. These restrictions are GLOBAL for API keys, not per key and
not a general session-authentication ACL. Check other clients before saving;
if an existing client needs another endpoint, review that scope explicitly.
The installed matcher accepts an exact allowed path or its slash descendants;
never allow /api or /ollama as a broad prefix. Do not enable file, tool, model
creation or admin endpoints merely to obtain chat access.

MANOS creates the restricted key via the user's normal authenticated session
(POST /api/v1/auths/api_key); stores it in a separate 0600 curl config named
AULA_RESTRICTED_CURL; never prints the returned key. Renewal replaces that
user's key; DELETE /api/v1/auths/api_key revokes it using the normal session,
not a restricted API key. API-key deletion alone does not revoke other login
sessions: the APP binding and technical login/session must also be disabled.

### 5. Measure direct API behavior before offering access

Prepare private JSON request files allowed.json and foreign.json with exact
catalog IDs, one short test message, stream=false and a small output budget.
Choose a real forbidden model; a nonexistent ID or blocked endpoint is not
evidence of model ACL. With the same restricted credential and allowed endpoint:

```sh
curl --silent --show-error --max-time 60 --config "$AULA_RESTRICTED_CURL" \
  --header 'Content-Type: application/json' \
  --data-binary @"$AULA_PRIVATE_DIR/foreign.json" \
  --output "$AULA_PRIVATE_DIR/foreign.response.json" \
  --write-out '%{http_code}\n' http://127.0.0.1:8080/api/chat/completions
```

Require 403 caused by model access, then repeat with allowed.json and require
a successful real completion plus attributable result. Save response bodies
privately; publish only status/cause. Test aliases and a direct base-model ID
as well; they cannot evade the grant. Test direct /ollama/api/chat access
under a non-admin session for model ACL if that session path is exposed. The
restricted API key should deny that route by endpoint policy regardless.
Test /api/models without a credential (401), an admin route with the restricted
key (403), and the revoked key (401 under the installed unknown-key path).
Revocation must also deny APP replay and new requests across restart.

MANOS then cuts only the tower tunnel, retaining an independent admin path.
The remote connection reports NO_DATA, never a fabricated completion or silent
substitution. Run a local mini as admin and confirm portal/app availability.
Restore the tunnel and recheck both catalogs. Pending inference/stream effects
must be reconciled before retry; do not repeat a dispatched write blindly.
Two natural heartbeat ticks remain a separate liveness measure: do not force
emissions or edit scripts/f1_heartbeat.py to test aula.

### Return for the affected step only

For a failed connection change, restore the captured connection object through
/ollama/config/update and verify the GET response. Do not restore the whole
database to undo an ACL edit: that could resurrect revoked keys and old state.
For a failed ACL/key step, deny APP access, revoke the new key, remove only the
new grant/login association and restore captured permission settings. For a
tunnel test, restore only that tunnel's prior state. Keep admin and local minis.

## Check / honest closure

This slice supplies no runtime code or credentials. Connection GET under admin,
second connection, restricted identity, ACL 403 with a real foreign model,
authorized LoRA completion, key/session revocation and tunnel-loss survival
are all NO_DATA pending the MANOS procedure and identity prerequisite.
Read-only observations above do not close phase 1.4 or commission control.
J-* mapping: NO_DATA, no specific code established for this slice.

Supporting upstream references (installed 0.11.1 source governs this runbook):
[API keys](https://docs.openwebui.com/features/authentication-access/api-keys/),
[hardening](https://docs.openwebui.com/getting-started/advanced-topics/hardening/),
[API endpoints](https://docs.openwebui.com/reference/api-endpoints/).
