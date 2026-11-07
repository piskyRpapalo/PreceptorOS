"""lab_avisos: Lab notices from registry `evidencia` events, aging to NO_DATA."""
import datetime as dt
import hashlib
import json
import pathlib
import sqlite3
import tempfile
import unittest

import lab_avisos as A

NOW = dt.datetime(2026, 11, 7, 12, 0, tzinfo=dt.timezone.utc)


def iso(seconds_ago):
    return (NOW - dt.timedelta(seconds=seconds_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


class Avisos(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = pathlib.Path(self.tmp.name) / "casa"
        self.base.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def registro(self, filas):
        d = self.base / "registro"
        d.mkdir(exist_ok=True)
        con = sqlite3.connect(d / "eventos.db")
        con.execute("create table if not exists eventos (n integer primary key autoincrement, ts text not null,"
                    " maquina text not null, tipo text not null, actor text not null,"
                    " cuerpo_json text not null, no_data_json text not null, bloquea_json text)")
        for ts, tipo, cuerpo in filas:
            con.execute("insert into eventos (ts, maquina, tipo, actor, cuerpo_json, no_data_json)"
                        " values (?, 'x', ?, 'hexelion', ?, '[]')", (ts, tipo, json.dumps(cuerpo)))
        con.commit()
        con.close()

    def digest(self):
        return hashlib.sha256((self.base / "registro" / "eventos.db").read_bytes()).hexdigest()

    def test_missing_registry_propagates_no_data(self):
        estado, lista = A.avisos(self.base, NOW)
        self.assertEqual(estado["estado"], "NO_DATA")
        self.assertTrue(estado["causa"])
        self.assertEqual(lista, [])

    def test_only_evidence_events_become_notices(self):
        self.registro([(iso(10), "evidencia", {"texto": "benchmark receipt published"}),
                       (iso(10), "duda", {"duda": "not a notice"})])
        estado, lista = A.avisos(self.base, NOW)
        self.assertEqual(estado["estado"], "MEDIDO")
        self.assertEqual(len(lista), 1)
        self.assertTrue(lista[0]["id"].startswith("evidencia-"))
        self.assertEqual(lista[0]["atoms"][0]["r"], "benchmark receipt published")

    def test_seal_ages_live_stale_no_data(self):
        ttl = A.TTL_S
        self.registro([(iso(ttl - 1), "evidencia", {"texto": "fresh"}),
                       (iso(ttl * 2), "evidencia", {"texto": "stale"}),
                       (iso(ttl * 5), "evidencia", {"texto": "old"})])
        _, lista = A.avisos(self.base, NOW)
        seals = {a["atoms"][0]["r"]: (a["seal"], a["cause"]) for a in lista}
        self.assertEqual(seals["fresh"], ("LIVE", ""))
        self.assertEqual(seals["stale"], ("STALE", ""))
        self.assertEqual(seals["old"], ("NO_DATA", "aged_out"))

    def test_bad_or_future_timestamp_is_no_data(self):
        self.registro([("not a date", "evidencia", {"texto": "bad"}),
                       (iso(-600), "evidencia", {"texto": "future"})])
        _, lista = A.avisos(self.base, NOW)
        self.assertEqual({(a["seal"], a["cause"]) for a in lista}, {("NO_DATA", "timestamp_invalid")})

    def test_frame_shape_and_size(self):
        self.registro([(iso(5), "evidencia", {"texto": "x" * 590})])
        _, lista = A.avisos(self.base, NOW)
        a = lista[0]
        self.assertEqual(a["v"], "preceptoros.acho/1")
        for k in ("id", "t", "cv", "atoms", "bands", "change", "sound", "soundCause", "seal", "since", "cause"):
            self.assertIn(k, a)
        self.assertTrue(a["sound"].startswith("NO_DATA"))
        self.assertLess(A.tamano(a), 1024)
        self.assertNotIn("actions", a)

    def test_long_sentence_is_trimmed_to_fit(self):
        self.assertLess(A.tamano(A.aviso({"n": 1, "t": iso(1), "texto": "ñ" * 600}, NOW, A.TTL_S)), 1024)

    def test_reading_never_writes(self):
        self.registro([(iso(5), "evidencia", {"texto": "read only"})])
        antes = self.digest()
        A.avisos(self.base, NOW)
        self.assertEqual(antes, self.digest())

    def test_invalid_ttl_or_clock(self):
        self.assertEqual(A.avisos(self.base, NOW, ttl_s=0)[0]["causa"], "ttl_invalid")
        self.assertEqual(A.avisos(self.base, "now")[0]["causa"], "clock_invalid")

    def test_module_has_no_network_or_house_paths(self):
        src = pathlib.Path(A.__file__).read_text(encoding="utf-8")
        for bad in ("socket", "urllib", "http.client", "/home/"):
            self.assertNotIn(bad, src)


if __name__ == "__main__":
    unittest.main()
