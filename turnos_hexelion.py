"""What happened to each request · the shared thread read as turns (META-HARNESS-01).

The Sovereign talks to Hexelion through `/api/hexelion/chat`, and can address a rack preceptor with @name; both
land in the shared `orquesta` thread (canales.py). This adapter reads that thread, already projected by
conversacion_comun, and pairs every request with what followed it:

  ANSWERED            Hexelion answered with model, time and verified sources
  ANSWERED_UNVERIFIED words in Hexelion's voice without model or time: shown, but not counted as evidence
  LOCAL_SENSOR        a local tool answered (energy); no model ran
  NO_ANSWER           the door recorded that no answer came, and its cause
  REPLIED             an addressed rack preceptor wrote back in its own voice
  NO_REPLY_RECORDED   nothing came back. This screen cannot see a process, so it never says one is running.

Each turn carries one `sentence`: the same words for the screen and the screen reader, built from the same fields
the machine reads. Pure: no network, no clock of its own, no writes.
"""
from __future__ import annotations

import conversacion_comun as C

SCHEMA = "preceptoros.hexelion-turns/1"
MAX_TURNS = 12
REPLIERS = {"hexelion", "orquestador", "hexelion-door"}
NEXT = {
    "ANSWERED": "Read the sources before acting on it.",
    "ANSWERED_UNVERIFIED": "Treat it as unverified; ask again for a sourced answer.",
    "LOCAL_SENSOR": "Nothing to do: it is a reading, not advice.",
    "NO_ANSWER": "Fix the cause or ask again later; nothing is working on this request now.",
    "REPLIED": "Read the reply; it is a message, not a permission.",
    "NO_REPLY_RECORDED": "Nothing is recorded as working on it. Ask again, or ask on the Mesa.",
}


# Plain sentences for the door's known causes; any other cause is read out as its code, never guessed at.
CAUSES = {
    "no_exact_quote_in_sources": "Hexelion searched your memory and found no exact quote, so it gave no answer.",
    "station_endpoint_not_configured": "The local model is not connected to this app server, so nobody answered.",
    "station_unavailable": "The local model did not respond, so nobody answered.",
    "station_timeout": "The local model took too long and was stopped, so nobody answered.",
    "no_matches": "Your memory has nothing on this yet, so Hexelion did not ask the model.",
}


def _name(voice):
    return C.identity(voice)["name"]


def _ms(machine):
    ms = machine.get("ms")
    return round(ms) if isinstance(ms, (int, float)) and not isinstance(ms, bool) and ms > 0 else None


def _close(turn, reply):
    """Fill a turn from the message that answered it."""
    m = reply.get("maquina") if isinstance(reply.get("maquina"), dict) else {}
    voice = reply.get("voz")
    turn.update(answered_by=voice, answered_by_name=_name(voice), answer_n=reply.get("n"), answered_at=reply.get("t"))
    if voice == "hexelion-door":
        cause = m.get("causa") if isinstance(m.get("causa"), str) else "cause_not_given"
        turn.update(state="NO_ANSWER", cause=cause[:80], answered_by=None, answered_by_name=None,
                    sentence=CAUSES.get(cause, "Hexelion did not answer: %s." % cause[:80].replace("_", " ")))
    elif voice == "orquestador":
        turn.update(state="LOCAL_SENSOR", evidence="local sensor reading; no model",
                    sentence="A local sensor answered; no model ran.")
    elif voice == "hexelion":
        model, ms = m.get("modelo"), _ms(m)
        sources = m.get("fuentes") if isinstance(m.get("fuentes"), list) else []
        if isinstance(model, str) and model and ms:
            turn.update(state="ANSWERED", model=model[:60], ms=ms, sources=len(sources),
                        evidence="%d verified source%s" % (len(sources), "" if len(sources) == 1 else "s"),
                        sentence="Hexelion answered in %.1f s with %d verified source%s (%s)." % (
                            ms / 1000, len(sources), "" if len(sources) == 1 else "s", model[:60]))
        else:
            turn.update(state="ANSWERED_UNVERIFIED", cause="reply_without_model_or_time",
                        sentence="Words in Hexelion's voice arrived without model or time; they are not evidence.")
    else:
        turn.update(state="REPLIED", sentence="%s replied in its own voice." % _name(voice))


def turns(messages, now_iso=""):
    """Thread messages (canales.lee shape, in order) -> the last MAX_TURNS turns, newest first."""
    out, open_hexelion, open_addressed = [], {}, {}
    for m in messages:
        if not isinstance(m, dict) or not isinstance(m.get("n"), int):
            continue
        machine = m.get("maquina") if isinstance(m.get("maquina"), dict) else {}
        voice = m.get("voz")
        if voice == "soberano" or (voice in C.BY_ID and C.BY_ID[voice]["kind"] == "rack-cli" and machine.get("para") is None
                                   and m.get("rol") == "rack CLI agent"):
            to = machine.get("para") if voice == "soberano" else None
            if to is not None and to not in C.BY_ID:
                continue
            turn = {"n": m["n"], "asked_at": m.get("t"), "asked_by": voice, "asked_by_name": _name(voice),
                    "to": to or "hexelion", "to_name": _name(to or "hexelion"), "question": str(m.get("texto") or "")[:160],
                    "state": "NO_REPLY_RECORDED", "evidence": "none", "answered_by": None, "answered_by_name": None,
                    "sentence": "No reply is recorded for this request."}
            out.append(turn)
            if to:
                open_addressed.setdefault(to, []).append(turn)
            else:
                open_hexelion[m["n"]] = turn
            continue
        if voice in REPLIERS:
            target = machine.get("pregunta_n")
            turn = open_hexelion.pop(target, None) if isinstance(target, int) else None
            if turn is None and not isinstance(target, int) and open_hexelion:   # older replies: the latest open one
                turn = open_hexelion.pop(max(open_hexelion))
            if turn is not None:
                _close(turn, m)
            continue
        if voice in open_addressed and open_addressed[voice]:
            _close(open_addressed[voice].pop(0), m)
    for t in out:
        t["next"] = NEXT[t["state"]]
        t["reader"] = "%s asked %s. %s %s" % (t["asked_by_name"], t["to_name"], t["sentence"], t["next"])
    return list(reversed(out))[:MAX_TURNS]


def project(lectura, now_iso):
    """The projection Notebook and Lab read. NO_DATA with cause when the thread cannot be read."""
    base = {"schema": SCHEMA, "observed_at": now_iso,
            "limits": "Reads the shared thread only. It cannot see processes, so it never reports one as running."}
    if not isinstance(lectura, dict) or lectura.get("estado") != "MEDIDO":
        cause = lectura.get("causa") if isinstance(lectura, dict) else None
        return dict(base, state="NO_DATA", cause=str(cause or "thread_unreadable"), turns=[], counts={})
    rows = turns(lectura.get("mensajes") or [], now_iso)
    counts = {}
    for t in rows:
        counts[t["state"]] = counts.get(t["state"], 0) + 1
    return dict(base, state="MEASURED" if rows else "NO_DATA", cause=None if rows else "no_request_in_thread",
                turns=rows, counts=dict(sorted(counts.items())))
