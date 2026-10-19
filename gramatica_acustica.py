"""Closed deterministic speech labels for app orchestrator responses.

This supplies text for a web client to speak. It does not synthesize audio,
decide state, or infer a cause from free text.
"""
from __future__ import annotations


# Only reachable intent/state pairs are part of the contract. Each pair has
# exactly one machine reason and one short Spanish utterance.
_PARES = {
    ("DEPLOY_BUILDING", "PROPOSED"):
        ("deploy_signature_required", "Despliegue propuesto. Requiere FIRMO."),
    ("DEPLOY_BUILDING", "NO_DATA"):
        ("deploy_rejected", "Despliegue no disponible. Consulte la causa."),
    ("QUERY_STATE", "MEASURED"):
        ("query_source_measured", "Consulta respondida con una fuente medida."),
    ("QUERY_STATE", "STALE"):
        ("query_source_stale", "El estado procede de una fuente caducada."),
    ("QUERY_STATE", "NO_DATA"):
        ("query_source_unavailable", "Consulta sin datos. Consulte la causa."),
    ("UPDATE_RAG", "NO_DATA"):
        ("chat_write_forbidden", "Actualización bloqueada desde el chat."),
}

PARES_VALIDOS = frozenset(_PARES)


def frase(intent, estado):
    """Return the fixed reason code and utterance for one valid pair."""
    try:
        motivo, habla = _PARES[(intent, estado)]
    except (KeyError, TypeError) as exc:
        raise ValueError("intent/state pair is outside the acoustic grammar") from exc
    return {"motivo": motivo, "habla": habla}


def pares():
    """Expose a detached mapping for schema generation and parity checks."""
    return {clave: {"motivo": valor[0], "habla": valor[1]}
            for clave, valor in _PARES.items()}
