"""lora_dataset.py · local LoRA dataset built ONLY from verified building-proof receipts.

Edge E of the F0 loop (odd/tasks/f0-one-loop-20261107.md): the LoRA eats measured
questions and signed feedback. No receipt, no row. The dataset is a local JSONL file;
nothing leaves the building and nothing is trained here (training stays NO_DATA, see
`lab.CAUSA_SIN_LORA`).

The signature verifier is injected (`prueba_edificio.verificar` in production) so this
module stays pure: no network, no child processes, no clock.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import tempfile

SCHEMA = "preceptoros.lora-dataset/1"
PROOF_SCHEMA = "preceptoros.building-proof/1"


def _sha(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _causa(item, verificar):
    """None when the item may become a row, else the rejection cause (first failure wins)."""
    if not isinstance(item, dict):
        return "malformed_item"
    sobre, pregunta, respuesta = item.get("sobre"), item.get("pregunta"), item.get("respuesta")
    recibo = sobre.get("recibo") if isinstance(sobre, dict) else None
    if (not isinstance(recibo, dict) or recibo.get("esquema") != PROOF_SCHEMA
            or not isinstance(pregunta, str) or not isinstance(respuesta, str)
            or not isinstance(recibo.get("id"), str) or not recibo["id"]):
        return "malformed_item"
    try:
        veredicto = verificar(sobre)
    except Exception:
        return "verifier_error"
    if not isinstance(veredicto, dict) or veredicto.get("estado") != "VERIFICADA":
        causa = veredicto.get("causa") if isinstance(veredicto, dict) else None
        return causa if isinstance(causa, str) and causa else "not_verified"
    if _sha(pregunta) != recibo.get("pregunta_sha256") or _sha(respuesta) != recibo.get("respuesta_sha256"):
        return "hash_mismatch"
    # decision mia (sin firma): `bytes` of a proof = UTF-8 bytes of question + answer.
    if recibo.get("bytes") != len(pregunta.encode("utf-8")) + len(respuesta.encode("utf-8")):
        return "bytes_mismatch"
    return None


def filas(items, verificar):
    """(rows, rejections). Only verified receipts with matching hashes become rows."""
    salida, rechazos, vistos = [], [], set()
    for indice, item in enumerate(items or []):
        causa = _causa(item, verificar)
        if causa is None and item["sobre"]["recibo"]["id"] in vistos:
            causa = "duplicate_receipt"
        if causa is not None:
            rechazos.append({"indice": indice, "causa": causa})
            continue
        recibo = item["sobre"]["recibo"]
        vistos.add(recibo["id"])
        salida.append({"recibo_id": recibo["id"], "edificio": recibo.get("edificio"),
                       "fecha": recibo.get("fecha"), "pregunta": item["pregunta"],
                       "respuesta": item["respuesta"]})
    return salida, rechazos


def escribir(filas_, destino):
    """Atomically write JSONL to `destino`; return its receipt. Zero rows writes nothing."""
    if not filas_:
        return {"estado": "NO_DATA", "causa": "no_verified_receipts"}
    raw = "".join(json.dumps(f, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
                  for f in filas_).encode("utf-8")
    destino = pathlib.Path(destino)
    fd, tmp = tempfile.mkstemp(prefix=".lora-", dir=destino.parent)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(raw)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, destino)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return {"esquema": SCHEMA, "filas": len(filas_), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}
