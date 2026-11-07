"""Tests for equipo.py (preceptoros.equipo/1). Offline; temporary files only."""
import os
import tempfile
import unittest

import equipo as E


def ag(**over):
  a = {"id": "a1", "name": "Agente", "glyph": "✦", "color": "sun", "form": "tips", "ask": ""}
  a.update(over)
  return a


def team(agents, active=None):
  return {"esquema": E.SCHEMA, "agents": agents,
      "active": agents[0]["id"] if active is None and agents else active}


def bad(x):
  return E.validar_agente(x) if isinstance(x, dict) else E.validar_equipo(x)


class CasaTest(unittest.TestCase):
  def test_casa_valid_within_budget(self):
    c = E.casa()
    self.assertEqual(E.validar_equipo(c), [])
    self.assertLessEqual(len(E._dump(c).encode("utf-8")), 4096)
    self.assertEqual(c["active"], "tips")


class AgentTest(unittest.TestCase):
  def test_closed_keys_and_known_values(self):
    self.assertEqual(bad(ag()), [])
    for x in (ag(extra=1), ag(glyph="x"), ag(color="LIVE"), ag(color="NO_DATA"),
         ag(color=["sun"]), ag(form="poem"), ag(id="Ab"), ag(id="a" * 25),
         ag(name=""), ag(name="a" * 25), ag(name="a\nb")):
      with self.subTest(agent=repr(x)[:40]):
        self.assertTrue(bad(x))
    self.assertEqual(bad(ag(id="a" * 24, name="ñ" * 24)), [])

  def test_ask_rules(self):
    for text in ("https://x.io", "HTTP://x", "www.x.io", "```c```", '"""x"""',
          "'''x'''", "tab\there", "bell\x07", "a" * 201, "ñ" * 101):
      with self.subTest(ask=text[:20]):
        self.assertTrue(bad(ag(form="free", ask=text)))
    self.assertEqual(bad(ag(form="free", ask="ñ" * 100)), [])
    self.assertEqual(bad(ag(form="free", ask="")), [])
    self.assertTrue(bad(ag(form="tips", ask="hola")))


class EquipoTest(unittest.TestCase):
  def test_count_duplicates_active_schema_extra(self):
    e = team([ag()])
    for x in (team([ag(id="a%d" % i) for i in range(7)]), team([]),
         team([ag(), ag(form="easy")]), team([ag()], active="nope"),
         team([ag(glyph="x")]), dict(e, esquema="preceptoros.equipo/2"),
         dict(e, extra=1)):
      with self.subTest(team=repr(x)[:40]):
        self.assertTrue(bad(x))


class InstruccionTest(unittest.TestCase):
  def test_style_prefix_budget_and_free_verbatim(self):
    for text in E.FORMS.values():
      if text is not None:
        self.assertLessEqual(len(text.encode("utf-8")), 160)
    for a in E.casa()["agents"]:
      s = E.instruccion(a)
      self.assertTrue(s.startswith("Style: "), s)
      self.assertLessEqual(len(s.encode("utf-8")), 240)
    self.assertEqual(E.instruccion(ag(form="free", ask="ñ" * 100)), "Style: " + "ñ" * 100 + ". ")
    with self.assertRaises(ValueError):
      E.instruccion(ag(form="poem"))


class FichaLabTest(unittest.TestCase):
  def test_fields_and_bounds(self):
    for a in E.casa()["agents"]:
      f = E.ficha_lab(a, edad=3)
      self.assertEqual((f["esquema"], f["id"], f["titulo"], f["estado"]),
              ("preceptoros.fabrica/1", "harness-" + a["id"], a["name"], "PROPUESTA"))
      self.assertEqual((f["agentes"], f["edad"]), ([a["id"]], 3))
      self.assertLessEqual(len(f["novedades"]), 100)
      self.assertIn(a["glyph"], f["novedades"])
      self.assertIn(a["form"], f["novedades"])
    self.assertLessEqual(len(E.ficha_lab(ag(form="free", ask="x" * 200))["novedades"]), 100)


class FicheroTest(unittest.TestCase):
  def setUp(self):
    self._d = tempfile.TemporaryDirectory()
    self.dir = self._d.name
    self.p = os.path.join(self.dir, "equipo.json")

  def tearDown(self):
    self._d.cleanup()

  def test_broken_duplicate_missing_oversize_give_casa_and_cause(self):
    self.assertEqual(E.cargar(self.p), (E.casa(), "missing"))
    for text, cause in (("{roto", "not_json"),
              ('{"esquema":"preceptoros.equipo/1","esquema":"x"}', "not_json"),
              (" " * 4097, "too_large")):
      with self.subTest(cause=cause):
        with open(self.p, "w", encoding="utf-8") as f:
          f.write(text)
        self.assertEqual(E.cargar(self.p), (E.casa(), cause))

  def test_guardar_invalid_writes_nothing_and_keeps_previous(self):
    self.assertTrue(E.guardar(self.p, team([ag(glyph="x")])))
    self.assertEqual(os.listdir(self.dir), [])
    self.assertEqual(E.guardar(self.p, E.casa()), [])
    with open(self.p, "rb") as f:
      before = f.read()
    self.assertTrue(E.guardar(self.p, team([ag(form="poem")])))
    with open(self.p, "rb") as f:
      self.assertEqual(f.read(), before)
    self.assertEqual(os.listdir(self.dir), ["equipo.json"])

  def test_roundtrip(self):
    mine = team([ag(id="voz", name="Voz", form="free", ask="ñ" * 100),
          ag(id="pasos", form="steps", glyph="⋮", color="clay")], active="voz")
    self.assertEqual(E.guardar(self.p, mine), [])
    self.assertEqual(E.cargar(self.p), (mine, None))
    self.assertEqual(os.listdir(self.dir), ["equipo.json"])


if __name__ == "__main__":
  unittest.main()
