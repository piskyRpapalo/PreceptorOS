/* Local-first node identity and explicit, credential-hiding building action. */
(function (root) {
  "use strict";

  var identitySchema = "preceptoros.pwa-node-identity/1";
  var actionSchema = "preceptoros.pwa-edificio-accion/1";
  var assignedNode = "primer-ancla";

  function text(key, values) {
    return typeof root.PreceptorNodeBuildingText === "function"
      ? root.PreceptorNodeBuildingText(key, values || {}) : key;
  }

  function mount(document, fetchImpl) {
    var fetcher = fetchImpl || root.fetch.bind(root);
    var identityForm = document.getElementById("node-identity-form");
    var buildingForm = document.getElementById("node-building-form");
    if (!identityForm || !buildingForm) return;
    var identityRead = document.getElementById("node-identity-read");
    var nodeInput = document.getElementById("node-identity-id");
    var identityConsent = document.getElementById("node-identity-consent");
    var identityButton = document.getElementById("node-identity-save");
    var identityStatus = document.getElementById("node-identity-status");
    var buildingConsent = document.getElementById("node-building-consent");
    var buildingButton = document.getElementById("node-building-submit");
    var buildingStatus = document.getElementById("node-building-status");
    var configured = false;

    function lockIdentity(nodeId) {
      configured = true;
      nodeInput.value = nodeId;
      nodeInput.disabled = true;
      identityConsent.checked = false;
      identityConsent.disabled = true;
      identityButton.disabled = true;
      identityRead.disabled = true;
      buildingConsent.disabled = nodeId !== assignedNode;
      buildingButton.disabled = nodeId !== assignedNode;
      identityStatus.textContent = text("node_building_saved", { id: nodeId });
      if (nodeId !== assignedNode) {
        buildingStatus.textContent = text("node_building_no_assignment");
      }
    }

    function post(url, body) {
      return fetcher(url, { method: "POST", cache: "no-store", credentials: "same-origin",
        headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
        .then(function (response) {
          return response.json().catch(function () { return {}; }).then(function (data) {
            return { ok: response.ok, data: data };
          });
        });
    }

    identityRead.addEventListener("click", function () {
      identityRead.disabled = true;
      fetcher("/api/nodo/identity", { method: "GET", cache: "no-store", credentials: "same-origin" })
        .then(function (response) {
          return response.json().then(function (data) {
            if (response.ok && data && data.estado === "configurada" && typeof data.node_id === "string") {
              lockIdentity(data.node_id);
            } else {
              identityStatus.textContent = text("node_building_cause", { cause: "identidad_no_provisionada" });
              identityRead.disabled = false;
            }
          });
        }).catch(function () {
          identityStatus.textContent = text("node_building_unavailable");
          identityRead.disabled = false;
        });
    });

    identityForm.addEventListener("submit", function (event) {
      event.preventDefault();
      if (configured || !identityConsent.checked || !nodeInput.reportValidity()) return;
      identityButton.disabled = true;
      identityRead.disabled = true;
      identityStatus.textContent = text("node_building_saving");
      post("/api/nodo/identity", { esquema: identitySchema, node_id: nodeInput.value.trim() })
        .then(function (result) {
          if (result.ok && result.data.estado === "provisionada") {
            lockIdentity(result.data.node_id);
          } else {
            identityStatus.textContent = text("node_building_cause", { cause: result.data.causa || "provision_no_confirmada" });
            identityButton.disabled = false;
            identityRead.disabled = false;
          }
        }).catch(function () {
          identityStatus.textContent = text("node_building_cause", { cause: "provision_local_no_confirmada" });
          identityButton.disabled = false;
          identityRead.disabled = false;
        });
    });

    buildingConsent.addEventListener("change", function () {
      buildingButton.disabled = !configured || !buildingConsent.checked;
    });

    buildingForm.addEventListener("submit", function (event) {
      event.preventDefault();
      if (!configured || !buildingConsent.checked) return;
      buildingButton.disabled = true;
      buildingStatus.textContent = text("node_building_sending");
      post("/api/nodo/edificio", { esquema: actionSchema, confirmar: true })
        .then(function (result) {
          var data = result.data || {};
          if (result.ok && data.estado === "recibido") {
            buildingStatus.textContent = text("node_building_received", {
              building: data.edificio, node: data.nodo, receipt: data.recibo_sha256
            });
          } else {
            buildingStatus.textContent = text("node_building_failed", { cause: data.causa || "declaracion_no_confirmada" });
          }
          buildingButton.disabled = !buildingConsent.checked;
        }).catch(function () {
          buildingStatus.textContent = text("node_building_not_confirmed");
          buildingButton.disabled = !buildingConsent.checked;
        });
    });
  }

  if (typeof module === "object" && module.exports) {
    module.exports = Object.freeze({ mount: mount, identitySchema: identitySchema, actionSchema: actionSchema });
  } else if (root.document) {
    mount(root.document, root.fetch.bind(root));
  }
})(typeof globalThis !== "undefined" ? globalThis : this);
