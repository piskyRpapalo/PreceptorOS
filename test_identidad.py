#!/usr/bin/env python3
"""R5 · La Identidad del Engrama · tres Rojos.

D11: Identidad por Origen. Dos engramas idénticos de distinto dispositivo son dos filas.
D12: Vía aditiva. Los engramas viejos no se tocan, su origen es NO_DATA.

Rojo N: dos memorias juntadas con mismo ID pero distinto origen ⇒ se conservan ambos.
Rojo O: mismo engrama exacto llegando dos veces del mismo origen ⇒ crea dos filas (By Origin).
Rojo P: engrama nacido antes de la decisión (sin origen) se lee y su origen es NO_DATA.

sistema: MVP · solo biblioteca estándar.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import memory

class TestIdentidadEngrama(unittest.TestCase):
    """R5 · Los tres Rojos de la identidad."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, 'memory.db')
        # Crear DB vacía para los tests
        memory.crear(self.db_path)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_rojo_n_choque_de_ids_conserva_ambos(self):
        """Dos memorias con engrama ID 1 pero distinto origen: al juntar, 2 filas."""
        # Simular memoria externa (otro dispositivo)
        ext_path = os.path.join(self.tmpdir.name, 'ext.db')
        memory.crear(ext_path)
        
        with memory.abrir(ext_path) as c_ext:
            memory.escribir_engrama(c_ext, what="Hola", why="test", origin="persona", origen_dispositivo="movil")
        
        with memory.abrir(self.db_path) as c_local:
            memory.escribir_engrama(c_local, what="Adios", why="test", origin="persona", origen_dispositivo="pc")
            
            # Importar la externa
            memory.importar(c_local, ext_path)
            
            # Deben haber 2 engramas (ninguno borrado)
            count = c_local.execute("SELECT count(*) FROM engrams").fetchone()[0]
            self.assertEqual(count, 2, "El choque de IDs debe conservar ambos engramas")

    def test_rojo_o_mismo_engrama_mismo_origen_crea_dos_filas(self):
        """Por Origen: el mismo engrama llegando dos veces del mismo sitio son 2 filas."""
        ext_path = os.path.join(self.tmpdir.name, 'ext.db')
        memory.crear(ext_path)
        
        with memory.abrir(ext_path) as c_ext:
            memory.escribir_engrama(c_ext, what="Hola", why="test", origin="persona", origen_dispositivo="movil")
        
        with memory.abrir(self.db_path) as c_local:
            # Importar dos veces
            memory.importar(c_local, ext_path)
            memory.importar(c_local, ext_path)
            
            count = c_local.execute("SELECT count(*) FROM engrams").fetchone()[0]
            self.assertEqual(count, 2, "Identidad por origen duplica si llega dos veces")

    def test_rojo_p_engrama_viejo_sin_origen_es_no_data(self):
        """Un engrama escrito antes de la columna origen debe leer origen como NO_DATA."""
        with memory.abrir(self.db_path) as c:
            # Escribir a pelo sin usar la función (simulando esquema viejo)
            c.execute("INSERT INTO engrams (what, why, where_ref, learned, origin) VALUES (?, ?, ?, ?, ?)",
                      ("Viejo", "test", "NO_DATA", "NO_DATA", "intencion"))
            c.commit()
            
            fila = c.execute("SELECT * FROM engrams WHERE what = 'Viejo'").fetchone()
            # La columna origen_dispositivo no existe en el INSERT viejo, pero la query la debe devolver como NO_DATA
            # Como usamos ALTER TABLE ADD COLUMN DEFAULT 'NO_DATA', esto se cumple a nivel SQL.
            # Para el test, verificamos que la columna existe y tiene NO_DATA
            origen_dev = c.execute("SELECT origen_dispositivo FROM engrams WHERE what = 'Viejo'").fetchone()[0]
            self.assertEqual(origen_dev, "NO_DATA", "El engrama viejo debe tener origen NO_DATA")


if __name__ == '__main__':
    unittest.main(verbosity=2)
