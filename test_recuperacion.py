# tests/test_recuperacion.py
import os
import sys
import sqlite3
import tempfile
import time
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from memory import respaldar


def crear_memoria_prueba(ruta_original):
    """
    Crea una memoria mínima con las tablas reales observadas.
    """
    conn = sqlite3.connect(ruta_original)
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE engrams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            "what" TEXT NOT NULL,
            "why" TEXT,
            "where" TEXT,
            "learned" TEXT,
            archived INTEGER DEFAULT 0
        )
    ''')

    cur.execute('''
        CREATE TABLE links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source INTEGER,
            target INTEGER
        )
    ''')

    cur.execute('''
        CREATE TABLE profile (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE fuga_sala (
            sala TEXT PRIMARY KEY,
            estado TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE fuentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            url TEXT
        )
    ''')

    rows = [
        ('prueba real', 'razon de prueba', 'lugar de prueba', 'aprendido de prueba', 0),
        ('prueba NO_DATA', 'NO_DATA', 'NO_DATA', 'NO_DATA', 0),
        ('prueba archivada', 'razon', 'lugar', 'aprendido', 1),
    ]

    cur.executemany(
        '''
        INSERT INTO engrams ("what", "why", "where", "learned", archived)
        VALUES (?, ?, ?, ?, ?)
        ''',
        rows,
    )

    conn.commit()
    conn.close()


class TestRecuperacion(unittest.TestCase):

    def test_integridad_tras_destruccion_y_resurreccion(self):
        """
        1. Crea una memoria temporal con datos reales y NO_DATA.
        2. Archiva un registro (archivar no es borrar).
        3. Ejecuta el mecanismo de copia de seguridad.
        4. Destruye el original.
        5. Restaura desde la copia.
        6. Exige que todo siga exacto, sin pérdidas silenciosas.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            ruta_original = os.path.join(tmpdir, 'memory.db')
            destino_previsto = os.path.join(tmpdir, 'memory_backup.tgz')

            crear_memoria_prueba(ruta_original)

            # [Fase 2: Copia]
            t0 = time.perf_counter()
            destino, recuentos = respaldar(ruta_original, destino_previsto)
            duracion_copia = time.perf_counter() - t0

            print(f'\nTIEMPO COPIA: {duracion_copia:.3f}s')
            print('DESTINO:', destino)
            print('RECUENTOS:', recuentos)

            # Verificar que el respaldo existe y es un fichero
            self.assertTrue(os.path.isfile(destino), "El respaldo debe ser un fichero")
            
            # Verificar recuentos
            self.assertIsInstance(recuentos, dict, "Los recuentos deben ser un diccionario")
            self.assertIn('engrams', recuentos, "Debe reportar recuento de engrams")
            self.assertEqual(recuentos['engrams'], 3, "Debe respaldar los 3 engrams")

            # [Fase 3: Destrucción]
            os.remove(ruta_original)
            self.assertFalse(os.path.exists(ruta_original), "El original debe destruirse")

            # [Fase 4: Resurrección]
            # El respaldo es directamente una copia SQLite, no un tarball
            # Lo abrimos directamente con sqlite3.connect()
            ruta_restaurada = destino  # El destino ES la memoria restaurada

            self.assertTrue(
                os.path.exists(ruta_restaurada),
                f"La memoria restaurada debe existir en {ruta_restaurada}",
            )

            # [Fase 5: Asertos de Doctrina]
            t0 = time.perf_counter()
            conn = sqlite3.connect(ruta_restaurada)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            duracion_apertura = time.perf_counter() - t0

            print(f'TIEMPO APERTURA: {duracion_apertura:.3f}s')

            # Verificar que todas las tablas existen
            tablas = cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            nombres_tablas = {row['name'] for row in tablas}
            
            for tabla_esperada in ['engrams', 'links', 'profile', 'fuga_sala', 'fuentes']:
                self.assertIn(
                    tabla_esperada,
                    nombres_tablas,
                    f"La tabla {tabla_esperada} debe existir en la restauración",
                )

            # Verificar NO_DATA persiste
            cur.execute(
                '''
                SELECT "what", "why", "where", "learned", archived
                FROM engrams
                WHERE "what" = ?
                ''',
                ('prueba NO_DATA',),
            )
            row = cur.fetchone()

            self.assertIsNotNone(row, "NO_DATA debe persistir")
            self.assertEqual(row['why'], 'NO_DATA', "why debe ser NO_DATA")
            self.assertEqual(row['where'], 'NO_DATA', "where debe ser NO_DATA")
            self.assertEqual(row['learned'], 'NO_DATA', "learned debe ser NO_DATA")

            # Verificar archivado (no borrado)
            cur.execute(
                '''
                SELECT archived
                FROM engrams
                WHERE "what" = ?
                ''',
                ('prueba archivada',),
            )
            row = cur.fetchone()

            self.assertIsNotNone(row, "El registro archivado debe existir")
            self.assertEqual(row['archived'], 1, "Archivar no es borrar")

            # Verificar integridad total
            cur.execute('SELECT COUNT(*) AS n FROM engrams')
            row = cur.fetchone()
            self.assertEqual(row['n'], 3, f"Deben persistir los 3 engrams, pero hay {row['n']}")

            # Verificar que los datos reales persisten
            cur.execute(
                '''
                SELECT "what", "why", "where", "learned"
                FROM engrams
                WHERE "what" = ?
                ''',
                ('prueba real',),
            )
            row = cur.fetchone()
            self.assertIsNotNone(row, "Los datos reales deben persistir")
            self.assertEqual(row['why'], 'razon de prueba', "Los datos deben ser idénticos")

            conn.close()

    def test_respaldo_nunca_sobrescribe(self):
        """Si el destino ya existe, respaldar() debe fallar cerrado."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ruta_original = os.path.join(tmpdir, 'memory.db')
            destino_previsto = os.path.join(tmpdir, 'memory_backup.tgz')

            crear_memoria_prueba(ruta_original)

            # Creamos un destino existente.
            with open(destino_previsto, 'wb') as f:
                f.write(b'destino existente')

            with self.assertRaises(FileExistsError):
                respaldar(ruta_original, destino_previsto)

    def test_respaldo_es_copia_sqlite_directa(self):
        """
        Verifica que el respaldo es una copia directa del SQLite,
        no un tarball comprimido.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            ruta_original = os.path.join(tmpdir, 'memory.db')
            destino_previsto = os.path.join(tmpdir, 'memory_backup.tgz')

            crear_memoria_prueba(ruta_original)

            destino, _ = respaldar(ruta_original, destino_previsto)

            # Leer primeros bytes
            with open(destino, 'rb') as f:
                magic = f.read(16)

            # SQLite files start with "SQLite format 3"
            self.assertEqual(
                magic[:15],
                b'SQLite format 3',
                "El respaldo debe ser una copia SQLite directa",
            )

            # Debe ser abrible como SQLite
            conn = sqlite3.connect(destino)
            tablas = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            conn.close()

            self.assertGreater(len(tablas), 0, "El respaldo debe tener tablas")


if __name__ == '__main__':
    unittest.main(verbosity=2)
