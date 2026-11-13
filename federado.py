"""Federated view · the APP reads LAB's node evidence and the private device registry; it never collects.

Commission 2026-11-13 (Entrega C): one app, many nodes. The physical census is LAB's (Codex CLI,
`bin/federated_node_snapshot.py`, LAB #178): one manifest per node backend (`preceptoros.lab.node-metadata-parts/1`)
whose model parts are pinned by SHA-256 and whose rebuilt snapshot must match `snapshot_ref`. This module:

  * reads those receipts from a local LAB clone at a git ref (git show; the working tree is never touched),
  * re-checks every part hash and the snapshot digest, and judges age with ITS OWN ceiling (never the receipt's),
  * joins them with the person's private device registry (<casa>/federado/dispositivos.json: names stay off-repo),
  * says per device which roles are DECLARED and which have evidence, and which are reserved to Acurast.

States: OBSERVED (metadata within ceiling) · STALE (integrity, too old) · DECLARED (registry only) ·
NO_DATA(cause). A hash proves integrity, not authenticity. An installed model is not an available model, and a
snapshot is never a dispatch grant. No network, no device access, no selector, no telemetry.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import re
from pathlib import Path

SCHEMA = "preceptoros.federated-view/1"
MANIFEST_SCHEMA = "preceptoros.lab.node-metadata-parts/1"
SNAPSHOT_SCHEMA = "preceptoros.lab.node-metadata/1"
REGISTRY_SCHEMA = "preceptoros.device-registry/1"
MAX_AGE_S = 120                     # LAB's ceiling (federated_node_snapshot.MAX_AGE_SECONDS); ours, not the receipt's
NODES = ("node-a", "node-b", "node-c", "node-d", "node-e")
ROLES = ("APP_CLIENT", "LOCAL_AI", "MODEL_SERVER", "SENSOR", "BENCH_WORKER", "ACURAST_EXTERNAL")
MAX_DEVICES = 16
_MANIFEST = re.compile(r"^\d{8}-federated-(node-[a-e])(?:-([a-z]{1,16}))?\.json$")
_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")


def no_data(cause):
    return {"state": "NO_DATA", "cause": cause}


def digest(value):
    """LAB's digest: sha256 of sorted-key compact ASCII JSON."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def _json(raw):
    def unique(pairs):
        out = {}
        for k, v in pairs:
            if k in out:
                raise ValueError("duplicate_key")
            out[k] = v
        return out
    if not isinstance(raw, bytes) or len(raw) >= 16384:
        raise ValueError("source_byte_limit")
    def invalid(_):
        raise ValueError("nonfinite_json")
    def finite(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError("nonfinite_json")
        return parsed
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique,
                      parse_constant=invalid, parse_float=finite)


def rebuild(manifest_raw, files, *, name=None):
    """(snapshot, None) or (None, cause). `files` maps receipt file name -> raw bytes."""
    try:
        doc = _json(manifest_raw)
    except (UnicodeError, ValueError, RecursionError):
        return None, "manifest_invalid_json"
    if not isinstance(doc, dict) or doc.get("schema") != MANIFEST_SCHEMA or not isinstance(doc.get("header"), dict) \
            or not isinstance(doc.get("parts"), list) or len(doc["parts"]) > 26 \
            or type(doc.get("model_count")) is not int or not 0 <= doc["model_count"] <= 256 \
            or not _SHA.fullmatch(str(doc.get("snapshot_ref", ""))):
        return None, "manifest_schema"
    models, seen = [], set()
    for part in doc["parts"]:
        if (not isinstance(part, dict) or set(part) != {"file", "sha256", "count"}
                or type(part.get("file")) is not str or part["file"] in seen
                or type(part.get("count")) is not int or not 0 <= part["count"] <= 256):
            return None, "part_manifest_invalid"
        if name and not re.fullmatch(re.escape(name[:-5]) + r"-models-[1-9][0-9]*\.json", part["file"]):
            return None, "part_identity_mismatch"
        seen.add(part["file"])
        if part.get("file") not in files:
            return None, "part_missing"
        raw = files[part["file"]]
        if not isinstance(raw, bytes) or len(raw) >= 16384:
            return None, "part_byte_limit"
        if hashlib.sha256(raw).hexdigest() != part.get("sha256"):
            return None, "part_hash_mismatch"
        try:
            rows = _json(raw)
        except (UnicodeError, ValueError, RecursionError):
            return None, "part_invalid_json"
        if (not isinstance(rows, list) or len(rows) != part.get("count")
                or len(models) + len(rows) > 256):
            return None, "part_count_mismatch"
        if any(type(row) is not dict or any(type(row.get(k)) is not str or not _SHA.fullmatch(row[k])
               for k in ("model_ref", "model_version")) for row in rows):
            return None, "model_identity_invalid"
        models.extend(rows)
    if len(models) != doc.get("model_count"):
        return None, "model_count_mismatch"
    snapshot = dict(doc["header"], models=models)
    if snapshot.get("schema") != SNAPSHOT_SCHEMA or digest(snapshot) != doc["snapshot_ref"]:
        return None, "snapshot_integrity"
    return snapshot, None


def freshness(snapshot, now):
    try:
        seen = dt.datetime.fromisoformat(snapshot["observed_at"].replace("Z", "+00:00"))
        if seen.utcoffset() is None:
            return no_data("timezone_required"), None
        age = (now - seen).total_seconds()
    except (KeyError, TypeError, ValueError, AttributeError):
        return no_data("observed_at_invalid"), None
    if age < 0:
        return no_data("future_observation"), age
    return ({"state": "OBSERVED", "cause": "metadata_snapshot_only"} if age <= MAX_AGE_S else
            {"state": "STALE", "cause": "observation_expired"}), age


def _host(snapshot):
    host = snapshot.get("host") if isinstance(snapshot.get("host"), dict) else {}
    if host.get("state") == "NO_DATA":
        return {"state": "NO_DATA", "cause": host.get("cause")}
    mem = host.get("memory_bytes") if isinstance(host.get("memory_bytes"), dict) else {}
    return {"architecture": host.get("architecture"), "cpu_count": host.get("cpu_count"),
            "ram_total_bytes": mem.get("MemTotal"), "ram_available_bytes": mem.get("MemAvailable")}


def backends(files, now):
    """Every node backend LAB published, re-checked. Nodes without any receipt are NO_DATA(no_lab_receipt)."""
    rows = []
    for name in sorted(files):
        m = _MANIFEST.fullmatch(name)
        if not m or m.group(2) == "summary":
            continue
        node, backend = m.group(1), m.group(2) or "default"
        if backend.startswith("models"):
            continue
        snapshot, cause = rebuild(files[name], files, name=name)
        row = {"node": node, "backend": backend, "file": name}
        if snapshot is None:
            rows.append(dict(row, **no_data(cause)))
            continue
        if snapshot.get("node") != node:
            rows.append(dict(row, **no_data("node_identity_mismatch")))
            continue
        if snapshot.get("catalog_state") not in ("VERIFIED", "OBSERVED"):
            rows.append(dict(row, **no_data("catalog_not_observed")))
            continue
        resident = snapshot.get('resident_count')
        if type(resident) is int and (resident < 0 or resident > len(snapshot['models'])):
            rows.append(dict(row, **no_data('resident_catalog_contradiction')))
            continue
        state, age = freshness(snapshot, now)
        models = snapshot.get("models") or []
        version = snapshot.get('backend_version')
        version = version.get('value') if isinstance(version, dict) else None
        version = version if isinstance(version, str) and re.fullmatch(r'\d+\.\d+\.\d+[a-z0-9.+-]{0,32}', version) else None
        row.update(state, observed_at=snapshot.get("observed_at"), age_s=None if age is None else int(age),
                   host=_host(snapshot), backend_version=version,
                   catalog_state=snapshot.get("catalog_state"), models_installed=len(models),
                   models_resident=snapshot.get("resident_count") if type(snapshot.get("resident_count")) is int
                       and 0 <= snapshot['resident_count'] <= 256 else None,
                   source_ref=digest(snapshot), verification={"state": "VERIFIED", "scope": "receipt_integrity_only"},
                   inference=no_data("no_independent_task_witness"),
                   admission=no_data("no_independent_task_resource_witness"))
        try:
            row['expires_at'] = ((dt.datetime.fromisoformat(snapshot['observed_at'].replace('Z', '+00:00'))
                                 + dt.timedelta(seconds=MAX_AGE_S)).isoformat() if age is not None else None)
        except (OverflowError, ValueError, TypeError, AttributeError):
            rows.append(dict(row, **no_data('observed_at_invalid')))
            continue
        rows.append(row)
    seen = {r["node"] for r in rows}
    rows += [{"node": n, "backend": None, **no_data("no_lab_receipt")} for n in NODES if n not in seen]
    return sorted(rows, key=lambda r: (r["node"], r["backend"] or ""))


def registry(base):
    """The person's declared devices (private file). (devices, None) or ([], cause)."""
    path = Path(base) / "federado" / "dispositivos.json"
    try:
        if path.is_symlink() or not path.is_file():
            return [], "registry_missing"
        if path.stat().st_size > 16384:
            return [], "registry_oversized"
        doc = _json(path.read_bytes())
    except (OSError, UnicodeError, ValueError, RecursionError):
        return [], "registry_invalid_json"
    devices = doc.get("devices") if isinstance(doc, dict) and doc.get("schema") == REGISTRY_SCHEMA else None
    if not isinstance(devices, list) or len(devices) > MAX_DEVICES:
        return [], "registry_schema"
    out, ids = [], set()
    for d in devices:
        if not isinstance(d, dict) or not _ID.fullmatch(str(d.get("id", ""))) or d["id"] in ids:
            return [], "registry_device_invalid"
        roles = d.get("roles")
        label = d.get("label")
        if not isinstance(label, str) or not 0 < len(label) <= 48 or not isinstance(roles, list) \
                or not set(roles) <= set(ROLES) or d.get("kind") not in ("rack_node", "mobile"):
            return [], "registry_device_invalid"
        if d["kind"] == "rack_node" and d.get("node") not in NODES:
            return [], "registry_node_invalid"
        ids.add(d["id"])
        out.append({"id": d["id"], "label": label, "kind": d["kind"], "node": d.get("node"), "roles": list(roles),
                    "acurast": d.get("acurast") if d.get("acurast") in ("lite", "core", "unknown") else None,
                    "parked": d.get("parked") is True})
    return out, None


def _role(device, role, by_node):
    """One role's evidence. Only MODEL_SERVER has a producer today (LAB node receipts)."""
    if role == "ACURAST_EXTERNAL":
        return {"role": role, "state": "DECLARED", "cause": "reserved_to_acurast_not_a_hexelion_worker"}
    if role == "MODEL_SERVER" and device["kind"] == "rack_node":
        rows = by_node.get(device["node"]) or []
        best = next((r for s in ("OBSERVED", "STALE") for r in rows if r["state"] == s), None)
        if best:
            return {"role": role, "state": best["state"], "cause": best["cause"], "observed_at": best["observed_at"],
                    "age_s": best["age_s"], "source_ref": best['source_ref'], "expires_at": best['expires_at'],
                    "verification": best['verification'], "inference": best['inference']}
        return {"role": role, **no_data(rows[0]["cause"] if rows else "no_lab_receipt")}
    return {"role": role, "state": "DECLARED", "cause": "no_producer_for_this_role"}


def project(files, base, now=None, source=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    rows = backends(files, now)
    by_node = {}
    for r in rows:
        by_node.setdefault(r["node"], []).append(r)
    devices, reg_cause = registry(base)
    for d in devices:
        d["evidence"] = [_role(d, role, by_node) for role in d["roles"]]
        if d["acurast"] == "core":
            d["coexistence"] = no_data("acurast_core_operationally_incompatible_do_not_install")
        elif d["acurast"]:
            d["coexistence"] = no_data("needs_bounded_test_and_owner_consent")
    return {"schema": SCHEMA, "observed_at": now.isoformat().replace("+00:00", "Z"), "source": source,
            "max_age_s": MAX_AGE_S, "backends": rows, "devices": devices, "registry_cause": reg_cause,
            "limits": "Integrity is not authenticity. Installed is not available. A snapshot is not a dispatch grant."}


def from_lab(base, repo=None, ref=None, now=None):
    """Read LAB receipts at a ref of a local clone. Never fetches: an old clone gives old (STALE) evidence."""
    import lab_bench
    repo = repo or os.environ.get("PRECEPTOROS_LAB_REPO") or str(Path.home() / "lab")
    ref = ref or os.environ.get("PRECEPTOROS_LAB_REF") or "origin/main"
    commit = lab_bench.resolve_ref(repo, ref)
    files = dict(lab_bench.from_git(repo, commit)) if commit else {}
    view = project(files, base, now, source={"ref": ref, "commit_sha": commit,
                                           "files": len(files), "state": "OBSERVED" if commit else "NO_DATA"})
    if not any(_MANIFEST.fullmatch(n) for n in files):
        view["lab_cause"] = "lab_federated_not_on_ref" if files else "lab_clone_or_ref_missing"
    return view
