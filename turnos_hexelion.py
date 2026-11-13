"""What happened to each request · the shared thread read as turns (META-HARNESS-01).

The Sovereign talks to Hexelion through `/api/hexelion/chat`, and can address a rack preceptor with @name; both
land in the shared `orquesta` thread (canales.py). This adapter reads that thread, already projected by
conversacion_comun, and pairs every request with what followed it:

  ANSWERED            Hexelion answered with model, time and verified sources
  ANSWERED_UNVERIFIED words in Hexelion's voice without model or time: shown, but not counted as evidence
  LOCAL_SENSOR        a local tool answered (energy); no model ran
  NO_ANSWER           the door recorded that no answer came, and its cause
  REPLIED             an addressed rack preceptor wrote back in its own voice
  ACTED               an action whose receipt carries the proof its tool's contract names (never `ok` alone)
  ACTION_REFUSED      the fence or the tool said no, with its cause
  ACTION_UNVERIFIED   an action receipt that does not prove success: missing proof, contradiction or no contract
  NO_REPLY_RECORDED   nothing came back. This screen cannot see a process, so it never says one is running.

Each turn carries one `sentence`: the same words for the screen and the screen reader, built from the same fields
the machine reads. Pure: no network, no clock of its own, no writes.
"""
from __future__ import annotations

import json
import re

import conversacion_comun as C

SCHEMA = "preceptoros.hexelion-turns/1"
MAX_TURNS = 12
REPLIERS = {"hexelion", "orquestador", "hexelion-door"}
NEXT = {
    "ANSWERED": "Read the sources before acting on it.",
    "ANSWERED_UNVERIFIED": "Treat it as unverified; ask again for a sourced answer.",
    "LOCAL_SENSOR": "Nothing to do: it is a reading, not advice.",
    "ACTED": "Check the result in the thread; anything to merge arrives as a draft HITL PR for you.",
    "ACTION_REFUSED": "Read the cause; the fence held, nothing changed.",
    "ACTION_UNVERIFIED": "Check the result yourself before relying on it; the receipt does not prove it.",
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
    "actions_person_only": "Only the person acts through Hexelion; a CLI agent uses its own tools.",
    "action_unknown": "That «/» action does not exist; the «?» button lists the ones that do.",
    "action_invalid": "That «/» action could not be read.",
    "action_takes_no_arguments": "That «/» action takes nothing after it.",
    "audit_count_1_to_20": "/registro takes a number from 1 to 20.",
    "worktree_name_invalid": "The worktree after @ is not a valid name.",
    "command_missing": "/ejecuta needs a command after it.",
    "write_needs_worktree": "/escribe needs @worktree first.",
    "write_path_or_separator_invalid": "/escribe needs a relative path, then « :: », then the text.",
    "mcp_nativo_missing": "The native MCP server is not installed on this rack, so Hexelion could not act.",
    "mcp_s3_not_installed": "The installed native MCP server is the read-only one (S-1); Hexelion needs S-3 to act.",
    "mcp_nativo_timeout": "The action took too long and was stopped.",
    "mcp_nativo_unrunnable": "The native MCP server could not be started.",
    "mcp_reply_invalid": "The native MCP server answered something unreadable, so nothing is claimed.",
    "quote_not_relevant": "Hexelion found exact quotes, but none shares a word with your question, so it gave no answer.",
}


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
LOCAL_READS = frozenset({"signatures", "lab", "preceptors", "devices", "models"})


def _int(v, lo, hi):
    return type(v) is int and lo <= v <= hi


# What each tool's own contract uses to confirm success (measured 2026-11-13 against the native server and
# hexelion_acciones.evidencia). `ok: true` is never enough on its own: the tool's proof must be in the receipt and
# agree with it. exec proves with rc == 0; the others carry no rc, so an rc there is a contradiction.
CONTRACTS = {
    "exec": lambda m, ev: _int(m.get("rc"), 0, 0) and ev.get("rc", 0) == 0,
    "write_file": lambda m, ev: m.get("rc") is None and _int(ev.get("bytes"), 0, 1 << 31)
    and isinstance(ev.get("sha256"), str) and bool(_SHA256.match(ev["sha256"])),
    "state": lambda m, ev: m.get("rc") is None and _int(ev.get("servicios"), 0, 4096),
    "capabilities": lambda m, ev: m.get("rc") is None and isinstance(ev.get("allowlist_version"), str)
    and 0 < len(ev["allowlist_version"]) <= 64,
    "audit_last": lambda m, ev: m.get("rc") is None and _int(ev.get("n"), 0, 20),
}
LOCAL_CONTRACT = lambda m, ev: _int(m.get("rc"), 0, 0) and isinstance(ev.get("fuente"), str) and 0 < len(ev["fuente"]) <= 80


def _action(m):
    """(state, cause) for one action receipt; success only when the tool's own contract confirms it."""
    tool, ok, local = m.get("herramienta"), m.get("ok"), m.get("via") == "lectura_local"
    ev = m.get("evidencia") if isinstance(m.get("evidencia"), dict) else {}
    if type(ok) is not bool:
        return "ACTION_UNVERIFIED", "receipt_ok_not_boolean"
    if not ok:
        if tool == "exec" and type(m.get("rc")) is int and m["rc"] == 0 and not m.get("causa"):
            return "ACTION_UNVERIFIED", "contradictory_receipt"
        return "ACTION_REFUSED", str(m.get("causa") or "rc %s" % m.get("rc"))[:80]
    if m.get("causa"):
        return "ACTION_UNVERIFIED", "contradictory_receipt"
    check = (LOCAL_CONTRACT if tool in LOCAL_READS else None) if local else CONTRACTS.get(tool)
    if check is None:
        return "ACTION_UNVERIFIED", "no_contract_for_tool"
    if tool == "exec" and type(m.get("rc")) is int and m["rc"] != 0:
        return "ACTION_UNVERIFIED", "contradictory_receipt"
    return ("ACTED", None) if check(m, ev) else ("ACTION_UNVERIFIED", "proof_missing")


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
    elif voice == "hexelion" and m.get("via") in ("mcp_nativo", "lectura_local"):
        tool = str(m.get("herramienta") or "?")[:24]
        local = m.get("via") == "lectura_local"
        evidence = "local read of an existing projection; no model" if local else "native MCP receipt; no model"
        state, cause = _action(m)
        if state == "ACTED":
            turn.update(state="ACTED", evidence=evidence,
                        sentence=("Hexelion read «%s» from the rack's own records; no model ran." % tool) if local
                        else ("Hexelion ran the action «%s» through the native MCP; no model ran." % tool))
        elif state == "ACTION_REFUSED":
            turn.update(state="ACTION_REFUSED", cause=cause, evidence=evidence,
                        sentence="Hexelion's action «%s» did not succeed: %s." % (tool, cause))
        else:
            turn.update(state="ACTION_UNVERIFIED", cause=cause, evidence=evidence,
                        sentence="Hexelion's action «%s» has a receipt that does not prove success (%s); "
                                 "it is not counted as done." % (tool, cause.replace("_", " ")))
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


MAX_TURN_B = 1024


def _bound(turn):
    """Every turn stays under 1,024 UTF-8 bytes: the quoted question gives way first, never the state or its cause."""
    size = lambda: len(json.dumps(turn, ensure_ascii=False).encode("utf-8"))
    while size() >= MAX_TURN_B and turn["question"]:
        turn["question"] = turn["question"][:max(0, len(turn["question"]) - 40)]
        turn["question_truncated"] = True


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
        _bound(t)
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
