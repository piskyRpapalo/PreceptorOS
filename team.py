"""Harness team contract, preceptoros.team/1. Disk only in load/save."""
import json
import os
import re
import tempfile
import unicodedata

SCHEMA = "preceptoros.team/1"
GLYPHS = ("✦", "◆", "☺", "⋮", "?", "⌁", "◇", "◉", "▲", "●")
COLORS = {"sea": "#64ae91", "blue": "#348ea2", "grass": "#6eb75d", "sand": "#d8be78",
     "clay": "#c19964", "sun": "#eacb56", "sky": "#45cbd4", "moss": "#a9bf68"}
FORMS = {  # None: the agent's ask is the style
  "tips": "Present each exact quote as a practical tip.",
  "key_points": "Present each exact quote as one key point.",
  "easy": "Pick the plainest exact quotes; a child should follow them.",
  "steps": "Order the exact quotes as steps, first to last.",
  "ask_me": "End with one exact quote the user can check with yes or no.",
  "free": None,
}
_AGENT = ("id", "name", "glyph", "color", "form", "ask")  # ordered: house() zips it
_TEAM = ("esquema", "agents", "active")
_ID = re.compile(r"[a-z0-9-]{1,24}")


def _control(text):  # any Unicode C* category
  return any(unicodedata.category(c).startswith("C") for c in text)


def validate_agent(a):
  if type(a) is not dict or set(a) != set(_AGENT):
    return ["agent_keys"]
  ask = a["ask"]
  fails = [k for k, good in (
    ("id", type(a["id"]) is str and _ID.fullmatch(a["id"])),
    ("name", type(a["name"]) is str and 1 <= len(a["name"]) <= 24 and not _control(a["name"])),
    ("glyph", a["glyph"] in GLYPHS),
    ("color", type(a["color"]) is str and a["color"] in COLORS),
    ("form", type(a["form"]) is str and a["form"] in FORMS),
  ) if not good]
  if type(ask) is not str:
    return fails + ["ask"]
  fails += [code for code, bad in (
    ("ask_size", len(ask.encode("utf-8", "surrogatepass")) > 200),
    ("ask_url_or_fence", re.search(r"https?://|www\.|```|\"\"\"|'''", ask, re.I)),
    ("ask_control", _control(ask)),
    ("ask_not_empty", a["form"] != "free" and ask != ""),
  ) if bad]
  return fails


def _dump(e):
  return json.dumps(e, ensure_ascii=False, separators=(",", ":"))


def validate_team(e):
  if type(e) is not dict or set(e) != set(_TEAM):
    return ["team_keys"]
  fails = [] if e["esquema"] == SCHEMA else ["esquema"]
  agents, ids = e["agents"], []
  if type(agents) is not list or not 1 <= len(agents) <= 6:
    fails.append("agents_count")
  else:
    for a in agents:
      fails += validate_agent(a)
      if type(a) is dict and type(a.get("id")) is str:
        ids.append(a["id"])
    if len(set(ids)) != len(ids):
      fails.append("agent_id_duplicate")
  if type(e["active"]) is not str or e["active"] not in ids:
    fails.append("active_missing")
  # dump is safe here
  if not fails and len(_dump(e).encode("utf-8")) > 4096:
    fails.append("too_large")
  return fails


def house():
  rows = (("tips", "Advice", "✦", "sun", "tips"),
      ("key-points", "Key points", "◆", "blue", "key_points"),
      ("easy", "Simple words", "☺", "grass", "easy"),
      ("steps", "Steps", "⋮", "sand", "steps"),
      ("ask-me", "Check questions", "?", "sky", "ask_me"))
  return {"esquema": SCHEMA, "active": "tips", "agents": [
    dict(zip(_AGENT, row + ("",))) for row in rows]}


def instruction(agente):
  fails = validate_agent(agente)
  if fails:
    raise ValueError("agent invalid: " + ",".join(fails))
  fixed = FORMS[agente["form"]]
  texto = (agente["ask"] if fixed is None else fixed).strip().rstrip(".")
  return "Style: " + texto + ". "


def _unique(pares):
  out = dict(pares)
  if len(out) != len(pares):
    raise ValueError("duplicate_key")
  return out


def load(ruta):
  """Falls back to house() with a cause; a valid team comes back with None."""
  try:
    with open(ruta, "rb") as f:
      raw = f.read(4097)
  except OSError as err:
    return house(), "missing" if isinstance(err, FileNotFoundError) else "unreadable"
  if len(raw) > 4096:
    return house(), "too_large"
  try:
    e = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique)
  except (ValueError, RecursionError):
    return house(), "not_json"
  fails = validate_team(e)
  return (house(), fails[0]) if fails else (e, None)


def save(ruta, e):
  """Atomic write; [] on success, else the failures with nothing written."""
  fails = validate_team(e)
  if fails:
    return fails
  fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(ruta)), prefix=".team-")
  try:
    with os.fdopen(fd, "wb") as f:
      f.write(_dump(e).encode("utf-8"))
    os.replace(tmp, ruta)
  finally:
    if os.path.exists(tmp):
      os.unlink(tmp)
  return []


def lab_card(agente, edad=0):
  fails = validate_agent(agente)
  if fails:
    raise ValueError("agent invalid: " + ",".join(fails))
  if type(edad) is not int or edad < 0:
    raise ValueError("edad_invalid")
  return {"esquema": "preceptoros.fabrica/1", "id": "harness-" + agente["id"],
      "titulo": agente["name"], "estado": "PROPUESTA",
      "novedades": "Harness " + agente["glyph"] + " form " + agente["form"] + ".",
      "agentes": [agente["id"]], "edad": edad}
