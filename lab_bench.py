"""Lab benchmark receipts (LAB #173, schema bench-repro-01-v1) -> one checked projection for Lab and Notebook.

Codex CLI's runner writes receipt files in the LAB repository: each file holds `executions[]`, every execution a
`receipt` and its `receipt_sha256`, plus an `integrity_recipe`, a `measurement_command` and a DECLARED
`machine_class`. This module never trusts a figure it cannot re-derive:

  * every `receipt_sha256` is recomputed with the recipe the file states (sorted keys, compact separators, ASCII);
  * every `comparison_key` is recomputed from the experiment controls (schema, fixture, input, settings, model
    digest, runtime version). It matches controls only: never hardware, quality or authenticity;
  * throughput stays per sample, with wall time and load time kept apart, never averaged into one number;
  * every NO_DATA field of the receipt (egress, backend, CPU/GPU split, power, RAM, hardware) is carried with its
    cause, and the machine class stays DECLARED: a declared machine is not a measured backend.

Output: `<home>/notebook/bench.json` (schema preceptoros.lab-bench/1, at most 8 KiB, mode 0600, atomic), with a
`projection_sha256` the reader recomputes. Sources: a folder, or a git ref read with `git show` (the checkout is
never changed). No network, no scheduler, no signing.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SCHEMA = "preceptoros.lab-bench/1"
RECEIPT_SCHEMA = "bench-repro-01-v1"
MAX_SOURCE = 1 << 20
MAX_OUT = 8192
MAX_RUNS = 6
NO_DATA_FIELDS = ("server_egress", "inference_backend", "cpu_gpu_split", "power", "ram", "hardware_class")
CONTROLS = ("schema", "fixture_sha256", "input_sha256", "settings", "model_digest", "ollama_version")
_NAME = re.compile(r"^\d{8}-[a-z0-9][a-z0-9._-]{0,80}\.json$")
_SHA = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def receipt_fingerprint(receipt):
    """The recipe LAB #173 states: UTF-8 json.dumps(receipt, sort_keys=True, separators=(',', ':'), ensure_ascii=True)."""
    return _sha(json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=True))


def comparison_key(receipt):
    return _sha(json.dumps({k: receipt[k] for k in CONTROLS}, sort_keys=True))


def _unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate_key")
        out[key] = value
    return out


def _short(value, n=12):
    return value[:n] if isinstance(value, str) and _SHA.fullmatch(value) or (isinstance(value, str) and _COMMIT.fullmatch(value)) else None


def _num(value, low, high):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and low <= value <= high else None


def _absent(receipt, name):
    field = receipt.get(name)
    if isinstance(field, dict) and field.get("state") == "NO_DATA" and isinstance(field.get("cause"), str):
        return {"field": name, "cause": field["cause"][:60]}
    return {"field": name, "cause": "field_missing_or_not_no_data"}


def check_execution(execution):
    """One execution -> (row, None) or (None, cause). Nothing is copied that was not checked."""
    if not isinstance(execution, dict) or not isinstance(execution.get("receipt"), dict):
        return None, "execution_invalid"
    r, stated = execution["receipt"], execution.get("receipt_sha256")
    if r.get("schema") != RECEIPT_SCHEMA:
        return None, "schema_not_bench_repro_01_v1"
    if not isinstance(stated, str) or not _SHA.fullmatch(stated) or receipt_fingerprint(r) != stated:
        return None, "receipt_fingerprint_mismatch"
    try:
        key_ok = comparison_key(r) == r.get("comparison_key")
    except (KeyError, TypeError, ValueError):
        key_ok = False
    source = r.get("source") if isinstance(r.get("source"), dict) else {}
    samples = []
    for s in r.get("samples") if isinstance(r.get("samples"), list) else []:
        if not isinstance(s, dict):
            continue
        samples.append({"attempt": _num(s.get("attempt"), 1, 99), "state": "MEASURED" if s.get("state") == "MEASURED" else "NO_DATA",
                        "tokens_per_s": _num(s.get("generation_tokens_per_s"), 0, 100000),
                        "wall_ms": round(s["wall_ns"] / 1e6) if _num(s.get("wall_ns"), 1, 10 ** 13) else None,
                        "load_ms": round(s["load_ns"] / 1e6) if _num(s.get("load_ns"), 0, 10 ** 13) is not None else None,
                        "response": _short(s.get("response_sha256"))})
    row = {"receipt": stated[:16], "fingerprint": "RECHECKED", "comparison_key": "RECHECKED" if key_ok else "MISMATCH",
           "comparison_key_short": _short(r.get("comparison_key")),
           "state": r.get("state") if r.get("state") in ("MEASURED", "NO_DATA", "FAILED") else "NO_DATA",
           "cause": r.get("cause") if isinstance(r.get("cause"), str) else None,
           "experiment": str(r.get("experiment_id") or "")[:40], "date": str(r.get("date_utc") or "")[:25],
           "model": str(r.get("model_name") or "")[:40], "model_digest": _short(r.get("model_digest")),
           "model_stable": r.get("model_stable") is True, "runtime": str(r.get("ollama_version") or "")[:16],
           "commit": _short(source.get("commit")), "runner": _short(source.get("runner_sha256")),
           "fixture": _short(r.get("fixture_sha256")), "input": _short(r.get("input_sha256")),
           "attempted": _num(r.get("attempted"), 0, 999), "succeeded": _num(r.get("succeeded"), 0, 999),
           "failed": _num(r.get("failed"), 0, 999), "byte_identical": r.get("byte_identical") is True,
           "samples": samples[:4], "not_measured": [_absent(r, name) for name in NO_DATA_FIELDS]}
    return row, None


def sentence(row, machine):
    rates = [s["tokens_per_s"] for s in row["samples"] if s["tokens_per_s"] is not None]
    walls = [s["wall_ms"] for s in row["samples"] if s["wall_ms"] is not None]
    if row["state"] != "MEASURED" or not rates:
        return "%s: no throughput was measured (%s)." % (row["model"] or "NO_DATA", row["cause"] or "no measured sample")
    span = ("%.1f" % rates[0]) if len(rates) == 1 else ("%.1f–%.1f" % (min(rates), max(rates)))
    return ("%s generated %s tokens/s over %d sample%s (wall %s s, load counted apart), as reported by the runner on a "
            "machine declared %s. Backend, CPU/GPU split, power and RAM were not measured." % (
                row["model"], span, len(rates), "" if len(rates) == 1 else "s",
                " / ".join("%.1f" % (w / 1000) for w in walls) or "NO_DATA", machine))


def project(files, now):
    """[(name, raw bytes)] -> the projection. Pure: same input, same output."""
    runs, rejected, read = [], {}, 0
    for name, raw in sorted(files):
        read += 1
        try:
            doc = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique)
        except (UnicodeError, ValueError, RecursionError):
            rejected["invalid_json"] = rejected.get("invalid_json", 0) + 1
            continue
        if not isinstance(doc, dict) or not isinstance(doc.get("executions"), list):
            rejected["not_a_bench_file"] = rejected.get("not_a_bench_file", 0) + 1
            continue
        mc = doc.get("machine_class") if isinstance(doc.get("machine_class"), dict) else {}
        machine = ("%s (DECLARED)" % str(mc.get("value"))[:32]) if mc.get("state") == "DECLARED" and mc.get("value") else "NO_DATA"
        for execution in doc["executions"]:
            row, cause = check_execution(execution)
            if row is None:
                rejected[cause] = rejected.get(cause, 0) + 1
                continue
            row.update(file=name[:90], machine=machine, sentence=sentence(row, machine))
            runs.append(row)
    runs = sorted(runs, key=lambda r: r["date"])[-MAX_RUNS:]
    out = {"schema": SCHEMA, "observed_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
           "state": "DECLARED" if runs else "NO_DATA",
           "cause": "runner_reported_fingerprints_rechecked" if runs else ("no_valid_bench_receipt" if read else "source_empty"),
           "counts": {"files": read, "runs": len(runs), "rejected": dict(sorted(rejected.items()))},
           "limits": "Throughput only: no quality, fairness, energy or authenticity claim. Comparison keys match controls, not hardware.",
           "runs": runs}
    while len(encode(out)) > MAX_OUT and out["runs"]:
        out["runs"].pop(0)
        out["counts"]["runs"] = len(out["runs"])
    out["projection_sha256"] = projection_fingerprint(out["runs"])
    return out


def projection_fingerprint(runs):
    return _sha(json.dumps(runs, sort_keys=True, separators=(",", ":"), ensure_ascii=True))


def encode(obj):
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def from_folder(folder):
    out = []
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return out
    for name in names:
        path = Path(folder) / name
        if not _NAME.fullmatch(name) or path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_SOURCE:
            continue
        out.append((name, path.read_bytes()))
    return out


def from_git(repo, ref, prefix="benchmarks/receipts/"):
    """Read receipt files at `ref` with git ls-tree / git show: the working tree and the index are never touched."""
    listing = subprocess.run(["git", "-C", repo, "ls-tree", "--name-only", ref, prefix], capture_output=True, text=True, timeout=20)
    if listing.returncode != 0:
        return []
    out = []
    for path in listing.stdout.split():
        name = path.rsplit("/", 1)[-1]
        if not _NAME.fullmatch(name):
            continue
        shown = subprocess.run(["git", "-C", repo, "show", "%s:%s" % (ref, path)], capture_output=True, timeout=20)
        if shown.returncode == 0 and len(shown.stdout) <= MAX_SOURCE:
            out.append((name, shown.stdout))
    return out


def write(root, projection):
    directory, target = Path(root) / "notebook", Path(root) / "notebook" / "bench.json"
    if Path(root).is_symlink() or directory.is_symlink() or target.is_symlink():
        raise OSError("symlink_forbidden")
    payload = encode(projection)
    if len(payload) > MAX_OUT + 256:
        raise ValueError("projection_oversized")
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    temp = directory / (".bench.%d.tmp" % os.getpid())
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, target)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check LAB bench-repro-01-v1 receipts and write the Lab/Notebook projection.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--receipts", help="folder holding YYYYMMDD-name.json receipt files")
    source.add_argument("--git", nargs=2, metavar=("REPO", "REF"), help="read benchmarks/receipts at REF with git show")
    parser.add_argument("--dry-run", action="store_true", help="print counts only; write nothing")
    args = parser.parse_args(argv)
    files = from_folder(args.receipts) if args.receipts else from_git(*args.git)
    projection = project(files, dt.datetime.now(dt.timezone.utc))
    said = {"schema": SCHEMA, "state": projection["state"], "cause": projection["cause"], "counts": projection["counts"]}
    if not args.dry_run:
        import casa
        said["written"] = str(write(casa.raiz(), projection)).replace(str(Path.home()), "~")
    print(json.dumps(said, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
