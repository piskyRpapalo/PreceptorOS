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

import hashlib
import json
import re

import audio_feedback as AF
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
LOCAL_READS = frozenset({"signatures", "lab", "preceptors", "devices", "models", "report"})


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
        if state == "ACTED" and local and tool == "report":
            # The self-report: the read ran under its contract; what it found is said answer by answer.
            ev = m.get("evidencia") if isinstance(m.get("evidencia"), dict) else {}
            got = ev.get("informe") if isinstance(ev.get("informe"), dict) else {}
            answers = {k: got.get(k) if got.get(k) in ("MEASURED", "NO_DATA") else "NO_DATA" for k in REPORT_ANSWERS}
            missing = [k for k in REPORT_ANSWERS if answers[k] != "MEASURED"]
            turn.update(state="ACTED", evidence=evidence, answers=answers,
                        cause="report_has_no_data" if missing else None,
                        sentence="Hexelion answered from its own records; no model ran."
                                 + (" NO_DATA: %s." % ", ".join(missing) if missing else ""))
        elif state == "ACTED":
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


# Acho (autonomy parity): how a turn sounds is decided here, with its sentence, so ear and eye cannot disagree. The
# class names are the ones Grok's toolkit proposes (acho-from-action/1); that mapper is not imported while its
# contract is open (P1, NO_DATA(p1_contract_unstable)), so the class comes from the turn's own state only.
BRIDGE_CAUSES = frozenset({"mcp_nativo_missing", "mcp_nativo_timeout", "mcp_nativo_unrunnable", "mcp_s3_not_installed",
                           "mcp_reply_invalid", "station_endpoint_not_configured", "station_unavailable",
                           "station_timeout"})
# REPLIED is another voice's own words, checked by nobody here: a proposal, never the success class (APP-P1-ACHO).
ACHO = {"ANSWERED": "ok", "ACTED": "ok", "LOCAL_SENSOR": "ok", "REPLIED": "proposed", "ANSWERED_UNVERIFIED": "empty",
        "ACTION_UNVERIFIED": "uncertain", "NO_REPLY_RECORDED": "unanswered"}   # an unproven action may have happened


def acho_class(turn):
    """The Acho class of one turn; anything not in the table is `empty` (never a success sound)."""
    state, cause = turn.get("state"), str(turn.get("cause") or "")
    if state == "ACTION_REFUSED":
        return "exec_fail" if cause.startswith("rc ") else "fence"
    if state == "NO_ANSWER":
        return "bridge_down" if cause in BRIDGE_CAUSES else "empty"
    if state == "ACTED" and cause == "report_has_no_data":
        return "empty"           # the report ran, but what it reports is missing evidence: never the success mark
    return ACHO.get(state, "empty")


MAX_TURN_B = 1024
# The self-report's text budget: inside the chat envelope (1,023 B, estado_compacto) the reply still carries the action
# fields, the report_ref and at least the cut turn (measured: test_self_report, a report at its full budget).
REPORT_TEXT_B = 480
REPORT_NEXT = "Read the four answers in the thread."
# What a chat reply carries to Talk: the Notebook row's own state, cause and words (autonomy parity), nothing else.
TALK_FIELDS = ("n", "state", "cause", "sentence", "next", "acho")


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
        # A report proposes nothing to merge: its next step is to read its four answers (and it keeps the row bounded).
        t["next"] = REPORT_NEXT if "answers" in t else NEXT[t["state"]]
        t["reader"] = "%s asked %s. %s %s" % (t["asked_by_name"], t["to_name"], t["sentence"], t["next"])
        clase = acho_class(t)
        t["acho"] = {"class": clase, "motif": AF.motif_for_class(clase), "sound": "off_until_turned_on",
                     "words": "reader"}
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


# Proposal for S5 (not wired; the native MCP server is unchanged): the compact answer a read-only `turns` tool would
# give. An MCP line must stay under 1,024 B (mcp_transport.LIMIT) once wrapped in JSON-RPC, so the summary carries the
# last turn's own state, cause and sentence plus the counts, and gives way (sentence first) rather than grow.
STATUS_SCHEMA = "preceptoros.hexelion-status/1"
MCP_LINE_B = 1024


def _mcp_line(summary):
    reply = {"jsonrpc": "2.0", "id": 3, "result": {"content": [{"type": "text", "text": json.dumps(
        summary, ensure_ascii=False, separators=(",", ":"), sort_keys=True)}]}}
    return len(json.dumps(reply, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")) + 1


def mcp_summary(projection, tasks=None):
    """projection (preceptoros.hexelion-turns/1) [+ tasks projection] -> a summary that fits one MCP line."""
    if not isinstance(projection, dict) or projection.get("schema") != SCHEMA:
        return {"schema": STATUS_SCHEMA, "state": "NO_DATA", "cause": "turns_projection_invalid"}
    rows = projection.get("turns") if isinstance(projection.get("turns"), list) else []
    last = rows[0] if rows and isinstance(rows[0], dict) else None
    out = {"schema": STATUS_SCHEMA, "state": projection.get("state"), "cause": projection.get("cause"),
           "counts": projection.get("counts") or {},
           "last": ({k: last.get(k) for k in ("n", "state", "cause", "sentence")} if last else None)}
    if isinstance(tasks, dict) and tasks.get("schema") == "preceptoros.hexelion-tasks/1":
        # The counters' own state travels with them: a null is unknown, never zero (tareas_hexelion.COUNTERS, APP-P0-TRUTH).
        c = tasks.get("counters") if isinstance(tasks.get("counters"), dict) else \
            {"state": "NO_DATA", "cause": "counters_not_stated", "complete_ref": None, "known_counts_are": "at_least"}
        known = c.get("state") == "MEASURED"
        out["tasks"] = {"state": tasks.get("state"), "cause": tasks.get("cause"), "counters": c,
                        "needs_you": tasks.get("needs_you") if known else (tasks.get("needs_you") or None),
                        "blocks_new_work": tasks.get("blocks_new_work") if known else (tasks.get("blocks_new_work") or None)}
    else:
        out["tasks"] = {"state": "NO_DATA", "cause": "tasks_projection_missing"}
    if _mcp_line(out) >= MCP_LINE_B and out["last"]:
        out["last"] = {k: out["last"][k] for k in ("n", "state", "cause")}
        out["last"]["sentence_cut"] = "mcp_line"
    if _mcp_line(out) >= MCP_LINE_B:
        out = {"schema": STATUS_SCHEMA, "state": "NO_DATA", "cause": "summary_exceeds_mcp_line"}
    return out


# The four questions (APP-P3, Mesa #3 round 7): «what are you doing, what have you achieved, how do you know, what do
# you need from me?». One projection over the turns, the tasks reading and the signature list the door already reads.
# No engine, no agent state of its own: every answer names the projection it rests on, and an answer it cannot read
# is NO_DATA with that projection's cause. It never says a process is running and never turns an unknown into zero.
REPORT_SCHEMA = "preceptoros.hexelion-self-report/1"
REPORT_ANSWERS = ("doing", "achieved", "how", "needs")
ACHIEVED = ("ACTED", "ANSWERED", "LOCAL_SENSOR")      # each carries its own contract's evidence; REPLIED is a proposal


def _ns(rows):
    return ", ".join(str(t["n"]) for t in rows[:4]) + (" and %d more" % (len(rows) - 4) if len(rows) > 4 else "")


def self_report(turns_projection, tasks_projection, signatures, is_report=lambda q: False):
    """(turns /1, tasks /1, (ok, cause, n_waiting|None)) -> the four answers, each {state, sentence, refs}."""
    tp = turns_projection if isinstance(turns_projection, dict) and turns_projection.get("schema") == SCHEMA else {}
    kp = tasks_projection if isinstance(tasks_projection, dict) and \
        tasks_projection.get("schema") == "preceptoros.hexelion-tasks/1" else {}
    rows = [t for t in (tp.get("turns") or []) if isinstance(t, dict) and not is_report(t.get("question"))]
    read = tp.get("state") == "MEASURED"
    words = lambda code: str(code or "no cause given").replace("_", " ")
    counters = kp.get("counters") if isinstance(kp.get("counters"), dict) else {"state": "NO_DATA",
                                                                                 "cause": "counters_not_stated"}
    tasks_read = kp.get("state") == "MEASURED"
    # A window is not a census: the queue is counted only when the host attested a complete reading and every row
    # was read (tareas_hexelion counters MEASURED). Otherwise the rows are "at least N visible" with the cause.
    census = tasks_read and counters.get("state") == "MEASURED"
    gap = None if census else (counters.get("cause") or "counters_not_stated")
    visible = len(kp.get("tasks") or [])

    # 1 · Doing: only the task reading can say it, and it never says "running".
    if not kp:
        doing = {"state": "NO_DATA", "cause": "tasks_projection_missing",
                 "sentence": "Doing: NO_DATA: I cannot read my tasks. I never say a process is running."}
    elif not tasks_read:
        doing = {"state": "NO_DATA", "cause": kp.get("cause"),
                 "sentence": "Doing: NO_DATA: I cannot see my tasks (%s). I never say a process is running."
                             % words(kp.get("cause"))}
    else:
        b = kp.get("blocks_new_work")
        blocks = "; %s%d block new work (no known result)" % ("" if census else "at least ", b) if b else ""
        doing = {"state": "MEASURED" if census else "NO_DATA", "cause": gap,
                 "sentence": ("Doing: %d task(s) recorded (complete reading)%s." % (visible, blocks) if census else
                              "Doing: at least %d task(s) visible; completeness NO_DATA (%s)%s."
                              % (visible, words(gap), blocks) if visible else
                              "Doing: NO_DATA: no task visible; completeness NO_DATA (%s)." % words(gap))
                             + " I never say a process is running."}
    last = rows[0] if rows else None
    if last:
        doing["sentence"] += " Your last request (message %d): %s" % (last["n"], last["sentence"])

    # 2 · Achieved: requests closed with their own contract's evidence; simulated or unchecked results do not count.
    done = [t for t in rows if t.get("state") in ACHIEVED]
    tasks_done = [t for t in (kp.get("tasks") or []) if t.get("state") == "DONE_CHECKED"
                  and (t.get("evidence") or {}).get("origin") == "MEASURED"]
    if not read:
        achieved = {"state": "NO_DATA", "cause": tp.get("cause") or "turns_projection_invalid",
                    "sentence": "Achieved: NO_DATA (%s)." % words(tp.get("cause") or "turns_projection_invalid")}
    else:
        achieved = {"state": "MEASURED", "cause": None,
                    "sentence": "Achieved: %d of the last %d requests closed with evidence%s; %s."
                                % (len(done), len(rows), " (messages %s)" % _ns(done) if done else "",
                                   ("%d task(s) checked" % len(tasks_done) if census else
                                    "at least %d task(s) checked" % len(tasks_done) if tasks_done else
                                    "tasks NO_DATA (%s)" % words(gap)) if tasks_read else "tasks NO_DATA")}

    # 3 · How I know: the projections and refs these answers rest on.
    how = {"state": "MEASURED" if read and census else "NO_DATA",
           "cause": None if read and census else (achieved["cause"] if not read else gap),
           "sentence": "How I know: %s; tasks %s; no model ran for this report." % (
               ("the shared thread, messages %d to %d" % (rows[-1]["n"], rows[0]["n"]) if rows else
                "the shared thread, no request in it") if read else "the thread NO_DATA",
               "read in full" if census else ("%d visible row(s) only" % visible     # the cause is in Doing
                                              if tasks_read and visible else "NO_DATA (%s)" % words(gap or kp.get("cause"))))}

    # 4 · Needs from you: a clear only over measured zeros; anything unread is said as unknown with its cause.
    ok, s_cause, waiting = signatures
    parts, known = [], True
    if ok and isinstance(waiting, int):
        parts.append("%d wait(s) for your signature" % waiting if waiting else "no signature waits")
    else:
        known = False
        parts.append("signatures unknown (%s)" % words(s_cause))
    if counters.get("state") == "MEASURED":
        n = (kp.get("needs_you") or 0) + (kp.get("decisions_for_you") or 0)
        if n:
            parts.append("%d task decision(s) yours" % n)
    else:
        known = False
        seen = (kp.get("needs_you") or 0) + (kp.get("decisions_for_you") or 0)
        parts.append(("at least %d task decision(s) yours; others " % seen if seen else "task decisions ")
                     + "unknown (%s)" % words(counters.get("cause")))
    unclear = [t for t in rows if t.get("state") in ("ACTION_UNVERIFIED", "ANSWERED_UNVERIFIED")]
    if unclear:
        parts.append("check message(s) %s yourself" % _ns(unclear))
    clear = known and not unclear and all(p.startswith("no ") for p in parts)
    needs = {"state": "MEASURED" if known else "NO_DATA", "cause": None if known else "needs_partly_unknown",
             "sentence": ("Needs from you: nothing now (measured)." if clear else "Needs from you: " + "; ".join(parts) + ".")}

    answers = {"doing": doing, "achieved": achieved, "how": how, "needs": needs}
    # The four answers are never cut: within REPORT_TEXT_B the quoted last request gives way first, then the reference
    # to it, then lists of message numbers become counts (refs.turns keeps them), then the standing "never running".
    size = lambda: len(" ".join(v["sentence"] for v in answers.values()).encode("utf-8"))
    if last and size() > REPORT_TEXT_B:
        doing["sentence"] = doing["sentence"][:doing["sentence"].index(" Your last request")] + \
            " Your last request is message %d." % last["n"]
    if last and size() > REPORT_TEXT_B:
        doing["sentence"] = doing["sentence"][:doing["sentence"].index(" Your last request")]
    if size() > REPORT_TEXT_B:                     # then lists of message numbers become counts; the refs stay in `refs.turns`
        achieved["sentence"] = re.sub(r" \(messages [^)]*\)", "", achieved["sentence"])
        needs["sentence"] = re.sub(r"check message\(s\) [^;.]*? yourself", "check %d message(s) yourself" % len(unclear),
                                   needs["sentence"])
    if size() > REPORT_TEXT_B:
        doing["sentence"] = doing["sentence"].replace(" I never say a process is running.", "")
    refs = {"turns": [t["n"] for t in rows], "tasks_cause": kp.get("cause"), "counters": counters.get("state"),
            "signatures_cause": s_cause}
    body = {"schema": REPORT_SCHEMA, "answers": {k: {"state": v["state"], "cause": v["cause"]} for k, v in answers.items()},
            "refs": refs, "text": " ".join(v["sentence"] for v in answers.values())}
    body["report_ref"] = hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True,
                                                   separators=(",", ":")).encode("utf-8")).hexdigest()
    return body
