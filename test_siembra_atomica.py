"""La primera siembra de policies.json es atomica (APP-FLAKE, Mesa #3, 2026-11-13).

Causa medida del intermitente `test_canales --sabotaje`: 8 escritores en una casa nueva usan el filtro por primera
vez a la vez; `guardrails.ruta_politicas` veia que el fichero no existia y lo copiaba en su sitio, y otro proceso,
viendo ya el fichero, lo leia a medio copiar: «configuración de políticas mal formada», el canal rechaza la
escritura, el hijo muere y la prueba espera 120 s a una cola vacia. Sonda: 1/200 rondas con 8 procesos (fork).

Aqui la carrera es determinista: la copia se detiene a la mitad y un segundo lector llega en ese instante.
Antes: el lector lee media copia y falla. Ahora: el fichero no existe hasta que esta entero.
No se relaja ninguna prueba: test_canales y su sabotaje quedan como estaban.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import guardrails as G


class LaSiembraEsAtomica(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = mock.patch.dict(os.environ, {"HOME": self.tmp.name})
        self.env.start()
        self.ruta = mock.patch.object(G, "POLICIES_PATH", None)
        self.ruta.start()

    def tearDown(self):
        self.ruta.stop()
        self.env.stop()
        self.tmp.cleanup()

    def test_un_lector_que_llega_a_media_siembra_nunca_lee_media_copia(self):
        real, visto = shutil.copy2, {}

        def copia_lenta(src, dst, *a, **kw):
            if visto:                                   # el segundo lector siembra de verdad
                return real(src, dst, *a, **kw)
            datos = Path(src).read_bytes()
            Path(dst).write_bytes(datos[: len(datos) // 2])   # media copia escrita...
            visto["lector"] = None
            try:
                visto["lector"] = G._cargar_politicas()    # ...y otro primer uso llega justo ahora
            except G.PoliticasInvalidas as e:
                visto["lector"] = e
            Path(dst).write_bytes(datos)
            return dst

        with mock.patch.object(shutil, "copy2", copia_lenta):
            G._cargar_politicas()
        self.assertNotIsInstance(visto["lector"], G.PoliticasInvalidas, visto["lector"])
        destino = Path(self.tmp.name) / ".preceptoros" / "policies.json"
        self.assertEqual(json.loads(destino.read_text(encoding="utf-8")),
                         json.loads(G.DEFECTO_PATH.read_text(encoding="utf-8")))

    def test_no_quedan_temporales_ni_se_pisa_un_fichero_existente(self):
        G._cargar_politicas()
        casa = Path(self.tmp.name) / ".preceptoros"
        self.assertEqual(sorted(p.name for p in casa.iterdir() if p.name.startswith(".policies.")), [])
        propio = casa / "policies.json"
        propio.write_text("{}", encoding="utf-8")       # la persona ya ajusto su copia
        G.ruta_politicas()
        self.assertEqual(propio.read_text(encoding="utf-8"), "{}")

    def casa(self):
        return Path(self.tmp.name) / ".preceptoros"

    def restos(self):
        return sorted(p.name for p in self.casa().iterdir() if p.name.startswith(".policies.")) if self.casa().exists() else []

    def test_un_arranque_normal_siembra_lee_y_repite_igual(self):
        politicas = G._cargar_politicas()
        destino = self.casa() / "policies.json"
        self.assertEqual(json.loads(destino.read_text(encoding="utf-8")),
                         json.loads(G.DEFECTO_PATH.read_text(encoding="utf-8")))
        antes = destino.stat().st_mtime_ns
        self.assertEqual(G._cargar_politicas(), politicas)                 # segundo arranque: lee, no vuelve a sembrar
        self.assertEqual(destino.stat().st_mtime_ns, antes)
        self.assertEqual(self.restos(), [])

    def test_una_copia_que_falla_a_medias_no_deja_fichero_ni_finge_exito(self):
        def disco_lleno(src, dst, *a, **kw):
            datos = Path(src).read_bytes()
            Path(dst).write_bytes(datos[: len(datos) // 2])
            raise OSError(28, "No space left on device")

        with mock.patch.object(shutil, "copy2", disco_lleno):
            with self.assertRaises(G.PoliticasInvalidas):
                G._cargar_politicas()
        self.assertFalse((self.casa() / "policies.json").exists())        # nada a medias en el sitio de las politicas
        self.assertEqual(self.restos(), [])
        G._cargar_politicas()                                              # el siguiente arranque siembra entero

    def test_sin_enlaces_duros_se_para_sin_pisar_ni_dejar_restos(self):
        # Un sistema de ficheros sin enlaces duros: se para (PoliticasInvalidas) en vez de renombrar encima. Renombrar
        # podria pisar un fichero aparecido en el hueco; la decision de admitirlo es del Soberano (odd/tasks).
        with mock.patch.object(Path, "hardlink_to", side_effect=OSError(1, "Operation not permitted")):
            with self.assertRaises(G.PoliticasInvalidas):
                G._cargar_politicas()
        self.assertFalse((self.casa() / "policies.json").exists())
        self.assertEqual(self.restos(), [])


if __name__ == "__main__":
    unittest.main()
