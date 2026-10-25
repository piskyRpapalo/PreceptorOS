/* Proposed phone flow. The phone holds no signing function. */
(function (root) {
  'use strict';
  var schemaName = 'preceptoros.cedula-nodo/1';
  var nodePattern = /^nodo\.[0-9]{1,6}\.[a-z0-9][a-z0-9-]{0,30}$/;
  var stateNames = Object.freeze({ draft: 'draft', preview: 'preview', consented: 'consented',
    submitting: 'submitting', pendingUntrusted: 'pending_untrusted', catalogStub: 'catalog_stub', failed: 'failed' });
  var doorOneUrl = 'https://api.preceptoros.org/api/v1/cedulas';

  function canonical(value) {
    if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
    if (value && typeof value === 'object') {
      return '{' + Object.keys(value).sort().map(function (key) {
        return JSON.stringify(key) + ':' + canonical(value[key]);
      }).join(',') + '}';
    }
    return JSON.stringify(value);
  }

  async function digest(value) {
    if (!root.crypto || !root.crypto.subtle || !root.TextEncoder) throw new Error('secure_hash_unavailable');
    var bytes = new root.TextEncoder().encode(value);
    var hash = await root.crypto.subtle.digest('SHA-256', bytes);
    return Array.from(new Uint8Array(hash)).map(function (b) { return b.toString(16).padStart(2, '0'); }).join('');
  }

  async function createRequest(node) {
    if (!nodePattern.test(String(node || ''))) throw new Error('invalid_node_name');
    var cedula = { esquema: schemaName, nodo: node, admin: null, dispositivos: [],
      firma: null, firma_ssh: null, autenticidad: 'NO_DATA' };
    cedula.sha256 = await digest(canonical(cedula));
    return cedula;
  }

  function pendingSigner() {
    return Promise.resolve({ state: 'pending', cause: 'signature_missing',
      detail: 'The phone never signs; the Sovereign must be present at the rack ceremony.' });
  }

  function testStubSigner(cedula) {
    return Promise.resolve({ state: 'pending', cause: 'signature_missing',
      label: 'test_stub_no_signature', cedula: cedula });
  }

  function doorOneAdapter(fetchImpl) {
    var send = fetchImpl || root.fetch.bind(root);
    return {
      endpoint: doorOneUrl,
      submitPending: async function (cedula, consent) {
        if (consent !== true) throw new Error('explicit_consent_required');
        if (!cedula || cedula.esquema !== schemaName || cedula.firma !== null || cedula.firma_ssh !== null) {
          throw new Error('pending_cedula_required');
        }
        var canonicalBody = Object.assign({}, cedula);
        delete canonicalBody.sha256;
        if (await digest(canonical(canonicalBody)) !== cedula.sha256) throw new Error('cedula_hash_mismatch');
        if (new root.TextEncoder().encode(JSON.stringify(cedula)).length >= 1024) {
          throw new Error('cedula_too_large');
        }
        var response = await send(doorOneUrl, { method: 'POST', cache: 'no-store',
          headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ cedula: cedula }) });
        var resultBody;
        try { resultBody = await response.json(); } catch (_error) { resultBody = {}; }
        var receiptValid = typeof resultBody.receipt_id === 'string' && resultBody.receipt_id.length > 0
          && resultBody.cedula_sha256 === cedula.sha256;
        if (resultBody.receipt === 'test_stub_only' && resultBody.persisted === false && receiptValid) return resultBody;
        if (response.ok && resultBody.state === 'pending' && resultBody.trust === 'untrusted'
            && resultBody.cause && receiptValid) return resultBody;
        var errorCause = response.ok && !receiptValid ? 'receipt_unverified'
          : resultBody.cause || (response.status === 404 ? 'route_unavailable' : 'receipt_unavailable');
        var error = new Error(errorCause);
        error.cause = errorCause;
        error.httpStatus = response.status;
        throw error;
      }
    };
  }

  async function runDryRun(node, signer, adapter) {
    var state = stateNames.draft;
    var transitions = [state];
    var cedula = await createRequest(node);
    state = stateNames.preview;
    transitions.push(state);
    var signerResult = await signer(cedula);
    if (!signerResult || signerResult.state !== 'pending' || cedula.firma !== null || cedula.firma_ssh !== null) {
      transitions.push(stateNames.failed);
      return { state: stateNames.failed, transitions: transitions, cedula: cedula, cause: 'phone_signing_forbidden' };
    }
    state = stateNames.consented;
    transitions.push(state);
    state = stateNames.submitting;
    transitions.push(state);
    var receipt = await adapter.submitPending(cedula, true);
    if (receipt.receipt === 'test_stub_only' && receipt.catalog && receipt.catalog.state === 'stub_not_published') {
      transitions.push(stateNames.catalogStub);
      return { state: stateNames.catalogStub, transitions: transitions, cedula: cedula, signer: signerResult, receipt: receipt };
    }
    transitions.push(stateNames.pendingUntrusted);
    return { state: stateNames.pendingUntrusted, transitions: transitions, cedula: cedula, signer: signerResult, receipt: receipt };
  }

  function mount(document, fetchImpl) {
    var form = document.getElementById('node-registration-form');
    if (!form) return;
    var input = document.getElementById('node-registration-name');
    var status = document.getElementById('node-registration-status');
    var preview = document.getElementById('node-registration-preview');
    var signerStatus = document.getElementById('node-registration-signer');
    var consent = document.getElementById('node-registration-consent');
    var submit = document.getElementById('node-registration-submit');
    var pendingCedula = null;
    var submitted = false;
    var adapter = doorOneAdapter(fetchImpl);

    form.addEventListener('submit', async function (event) {
      event.preventDefault();
      pendingCedula = null;
      submitted = false;
      consent.checked = false;
      submit.disabled = true;
      try {
        pendingCedula = await createRequest(input.value.trim());
        preview.textContent = JSON.stringify(pendingCedula, null, 2);
        signerStatus.textContent = text('node_registration_signer_pending');
        status.textContent = text('node_registration_draft_ready');
        consent.disabled = false;
      } catch (error) {
        status.textContent = text('node_registration_invalid') + ' ' + error.message;
        preview.textContent = '';
        signerStatus.textContent = text('node_registration_signer_pending');
      }
    });

    consent.addEventListener('change', function () {
      submit.disabled = submitted || !pendingCedula || !consent.checked;
    });

    submit.addEventListener('click', async function (event) {
      event.preventDefault();
      if (!pendingCedula || !consent.checked) return;
      submitted = true;
      submit.disabled = true;
      status.textContent = text('node_registration_sending');
      try {
        await pendingSigner();
        var receipt = await adapter.submitPending(pendingCedula, consent.checked);
        status.textContent = text('node_registration_pending') + ' ' + receipt.cause
          + ' · ' + receipt.receipt_id;
      } catch (error) {
        status.textContent = text('node_registration_unavailable') + ' ' + (error.cause || 'network_unavailable');
      } finally {
        submit.disabled = submitted || !consent.checked;
      }
    });
  }

  function text(key) {
    return typeof root.PreceptorNodeRegistrationText === 'function'
      ? root.PreceptorNodeRegistrationText(key) : key;
  }

  if (typeof module === 'object' && module.exports) {
    module.exports = Object.freeze({ schemaName: schemaName, states: stateNames, doorOneUrl: doorOneUrl,
      canonical: canonical, createRequest: createRequest, pendingSigner: pendingSigner,
      testStubSigner: testStubSigner, doorOneAdapter: doorOneAdapter, runDryRun: runDryRun, mount: mount });
  } else {
    root.PreceptorNodeRegistration = Object.freeze({ schemaName: schemaName, states: stateNames,
      createRequest: createRequest, pendingSigner: pendingSigner,
      doorOneAdapter: doorOneAdapter, mount: mount });
  }
})(typeof globalThis !== 'undefined' ? globalThis : this);
