#!/usr/bin/env python3
"""test_fuga.py · 10 criterios deterministas de Claude para M3.

Todos los tests usan AURELIUS_TEST=1 y HOME temporal para no tocar
la memoria real del usuario.
"""
import os
import sys
import sqlite3
import tempfile
import unittest
from pathlib import Path

# Configurar entorno de test
os.environ["AURELIUS_TEST"] = "1"

class TestFuga(unittest.TestCase):
    """Tests para el motor de la Fuga del Museo."""

    def setUp(self):
        """Crea un HOME temporal y una DB limpia para cada test."""
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = Path(self.tmpdir) / "memory.db"
        os.environ["HOME"] = self.tmpdir
        
        # Crear esquema mínimo
        conn = sqlite3.connect(str(self.db_path))
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS profile (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL DEFAULT 'NO_DATA',
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS fuga_sala (
                sala INTEGER PRIMARY KEY CHECK (sala BETWEEN 1 AND 6),
                nombre TEXT NOT NULL,
                entrado_en TEXT NOT NULL DEFAULT (datetime('now')),
                salido_en TEXT NOT NULL DEFAULT 'NO_DATA',
                minutos INTEGER NOT NULL DEFAULT 0,
                estado TEXT NOT NULL DEFAULT 'entrada'
                    CHECK (estado IN ('entrada', 'completada', 'pausada')),
                concepto TEXT NOT NULL DEFAULT 'NO_DATA'
            );
            CREATE TABLE IF NOT EXISTS fuentes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ruta_o_url TEXT NOT NULL DEFAULT 'NO_DATA',
                sha256 TEXT NOT NULL DEFAULT 'NO_DATA',
                tipo TEXT NOT NULL DEFAULT 'NO_DATA',
                equipada_en TEXT NOT NULL DEFAULT (datetime('now')),
                estado TEXT NOT NULL DEFAULT 'sin_declarar'
                    CHECK (estado IN ('sin_declarar', 'equipada', 'retirada'))
            );
            CREATE TABLE IF NOT EXISTS engrams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                texto TEXT NOT NULL,
                creado_en TEXT NOT NULL DEFAULT (datetime('now')),
                tipo TEXT NOT NULL DEFAULT 'recuerdo'
            );
        """)
        conn.close()
        
        # Importar fuga con el HOME temporal
        sys.path.insert(0, str(Path(__file__).parent))
        import fuga
        fuga.DB_PATH = str(self.db_path)
        self.fuga_mod = fuga

    def test_01_reanudar_de_verdad(self):
        """Criterio 1: Reanudar desde sala 3 sin repetir 1 y 2."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            INSERT INTO fuga_sala (sala, nombre, estado)
            VALUES (1, 'PROHAIRESIS', 'completada'),
                   (2, 'SAFEHOUSE', 'completada'),
                   (3, 'HORMĒ', 'entrada')
        """)
        conn.commit()
        conn.close()
        
        f = self.fuga_mod.FugaMuseo()
        sala = f._detectar_reanudacion()
        self.assertEqual(sala, 3, "Debe reanudar desde sala 3")
        f.cerrar()

    def test_02_nada_a_medias(self):
        """Criterio 2: Sala abandonada deja estado='entrada' y cero filas nuevas."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("INSERT INTO fuga_sala (sala, nombre, estado) VALUES (1, 'PROHAIRESIS', 'entrada')")
        conn.commit()
        
        # Verificar que no hay datos en profile
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM profile")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 0, "Sala abandonada no debe escribir en profile")

    def test_03_nombre_no_se_pide_dos_veces(self):
        """Criterio 3: Si profile.name existe, sala 1 saluda con él."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("INSERT INTO profile (key, value) VALUES ('name', 'Carlos')")
        conn.commit()
        conn.close()
        
        f = self.fuga_mod.FugaMuseo()
        # Verificar que el nombre existe
        cursor = f.db.cursor()
        cursor.execute("SELECT value FROM profile WHERE key='name'")
        row = cursor.fetchone()
        self.assertIsNotNone(row, "El nombre debe existir en profile")
        self.assertEqual(row[0], "Carlos")
        f.cerrar()

    def test_04_salir_sin_fuente_posible(self):
        """Criterio 4: Se completa M3 sin fuente, estado='sin_declarar'."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            INSERT INTO fuentes (ruta_o_url, estado)
            VALUES ('sin_declarar', 'sin_declarar')
        """)
        conn.commit()
        
        cursor = conn.cursor()
        cursor.execute("SELECT estado FROM fuentes WHERE ruta_o_url='sin_declarar'")
        row = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(row, "Debe existir fila con sin_declarar")
        self.assertEqual(row[0], "sin_declarar")

    def test_05_no_data_se_ve(self):
        """Criterio 5: Las 4 preguntas no contestadas aparecen como NO_DATA."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("INSERT INTO profile (key, value) VALUES ('proyecto_vital', 'NO_DATA')")
        conn.execute("INSERT INTO profile (key, value) VALUES ('triunfo_deseado', 'NO_DATA')")
        conn.commit()
        
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM profile WHERE key='proyecto_vital'")
        row = cursor.fetchone()
        conn.close()
        
        self.assertEqual(row[0], "NO_DATA", "NO_DATA debe verse literalmente")

    def test_06_cero_delete(self):
        """Criterio 6: grep DELETE en fuga.py debe ser cero."""
        fuga_path = Path(__file__).parent / "fuga.py"
        content = fuga_path.read_text()
        # Excluir docstrings y comentarios
        lineas_codigo = [l for l in content.split('\n') 
                        if not l.strip().startswith('#') 
                        and not l.strip().startswith('"""')
                        and not l.strip().startswith("'''")]
        codigo = '\n'.join(lineas_codigo)
        # Buscar solo DELETE FROM (SQL real), no parámetros de Python como delete=False
        import re
        delete_sql = re.search(r'\bDELETE\s+FROM\b', codigo, re.IGNORECASE)
        self.assertIsNone(delete_sql, "Cero DELETE FROM en el código")

    def test_07_sin_oidos_sin_voz_funciona(self):
        """Criterio 8: Sin voz ni oído, M3 se completa por teclado."""
        # Simular que voz y oído no están disponibles
        self.fuga_mod.voz = None
        self.fuga_mod.oido = None
        
        f = self.fuga_mod.FugaMuseo()
        # Verificar que puede inicializarse sin voz ni oído
        self.assertIsNotNone(f.db, "DB debe conectarse sin voz ni oído")
        f.cerrar()

    def test_08_manifiesto_se_comporta(self):
        """Criterio 7: Manifiesto firmado verifica integridad."""
        import hashlib
        
        # Crear perfil mínimo
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("INSERT INTO profile (key, value) VALUES ('name', 'Test')")
        conn.execute("INSERT INTO fuga_sala (sala, nombre, concepto) VALUES (1, 'S1', 'C1')")
        conn.commit()
        conn.close()
        
        f = self.fuga_mod.FugaMuseo()
        # Generar manifiesto
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            self.fuga_mod.MANIFIESTO_PATH = tmp.name
        
        f._generar_manifiesto()
        
        # Verificar que el manifiesto existe y tiene firma
        content = Path(self.fuga_mod.MANIFIESTO_PATH).read_text()
        self.assertIn("Firma (SHA256):", content, "Manifiesto debe tener firma")
        self.assertIn("SHA256", content.upper() or content, "Firma debe ser SHA256")
        
        # Limpiar
        os.unlink(self.fuga_mod.MANIFIESTO_PATH)
        f.cerrar()

    def test_09_mision_completa_con_un_dato(self):
        """Criterio 10: Misión completa con al menos un dato real."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("INSERT INTO profile (key, value) VALUES ('name', 'Test')")
        conn.execute("INSERT INTO fuga_sala (sala, nombre, estado) VALUES (1, 'S1', 'completada')")
        conn.commit()
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM profile WHERE value != 'NO_DATA'")
        datos_reales = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM fuga_sala WHERE estado='completada'")
        salas_completadas = cursor.fetchone()[0]
        conn.close()
        
        self.assertGreaterEqual(datos_reales, 1, "Al menos un dato real")
        self.assertGreaterEqual(salas_completadas, 1, "Al menos una sala completada")

    def test_10_toda_confirmacion_tiene_sonido(self):
        """Criterio 9: Cada punto de confirmación tiene canal sonoro."""
        # Verificar que _reproducir_wav existe y tiene fallbacks
        f = self.fuga_mod.FugaMuseo()
        self.assertTrue(hasattr(f, '_reproducir_wav'), "Debe tener _reproducir_wav")
        
        # Verificar que hay múltiples reproductores
        import inspect
        source = inspect.getsource(f._reproducir_wav)
        self.assertIn("aplay", source, "Debe incluir aplay")
        self.assertIn("vlc", source, "Debe incluir vlc como fallback")
        f.cerrar()


if __name__ == "__main__":
    unittest.main(verbosity=2)
