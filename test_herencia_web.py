import unittest
import tempfile
import shutil
from pathlib import Path
from herencia_web import verificar

class TestHerencia(unittest.TestCase):
    def setUp(self):
        self.origen = Path(__file__).parent / 'assets/herencia-web'
        self.sha_esperado = (Path(__file__).parent / 'config/herencia-web.sha256').read_text().strip()

    def test_manifiesto_correcto(self):
        with tempfile.TemporaryDirectory() as temporal:
            shutil.copytree(self.origen, Path(temporal) / 'copia')
            resultado = verificar(Path(temporal) / 'copia', self.sha_esperado)
            self.assertEqual(resultado['estado'], 'MEDIDO')
            self.assertEqual(resultado['semillas'], 9)
            self.assertEqual(resultado['bloques'], 79)

    def test_bloque_alterado(self):
        with tempfile.TemporaryDirectory() as temporal:
            shutil.copytree(self.origen, Path(temporal) / 'copia')
            (Path(temporal) / 'copia' / 'tabla' / 'bloque-000.bin').write_bytes(b'alterado')
            resultado = verificar(Path(temporal) / 'copia', self.sha_esperado)
            self.assertEqual(resultado['estado'], 'NO_DATA')
            self.assertTrue(resultado['causa'])

    def test_bloque_excedido(self):
        with tempfile.TemporaryDirectory() as temporal:
            shutil.copytree(self.origen, Path(temporal) / 'copia')
            (Path(temporal) / 'copia' / 'tabla' / 'bloque-000.bin').write_bytes(b'x' * 1025)
            resultado = verificar(Path(temporal) / 'copia', self.sha_esperado)
            self.assertEqual(resultado['estado'], 'NO_DATA')

    def test_enlace_fuera_del_paquete(self):
        with tempfile.TemporaryDirectory() as temporal1, tempfile.TemporaryDirectory() as temporal2:
            shutil.copytree(self.origen, Path(temporal1) / 'copia')
            (Path(temporal2) / 'external.bin').write_bytes((Path(temporal1) / 'copia' / 'tabla' / 'bloque-000.bin').read_bytes())
            (Path(temporal1) / 'copia' / 'tabla' / 'bloque-000.bin').unlink()
            (Path(temporal1) / 'copia' / 'tabla' / 'bloque-000.bin').symlink_to(Path(temporal2) / 'external.bin')
            resultado = verificar(Path(temporal1) / 'copia', self.sha_esperado)
            self.assertEqual(resultado['estado'], 'NO_DATA')

    def test_indice_excedido_con_hash_coherente(self):
        import hashlib
        with tempfile.TemporaryDirectory() as temporal:
            copia = Path(temporal) / 'copia'
            shutil.copytree(self.origen, copia)
            indice = copia / 'indice.json'
            contenido = indice.read_bytes() + b' ' * (1025 - indice.stat().st_size)
            indice.write_bytes(contenido)
            resultado = verificar(copia, hashlib.sha256(contenido).hexdigest())
            self.assertEqual(resultado['estado'], 'NO_DATA')
            self.assertTrue(resultado['causa'])

    def test_enlace_interno_tambien_se_rechaza(self):
        with tempfile.TemporaryDirectory() as temporal:
            copia = Path(temporal) / 'copia'
            shutil.copytree(self.origen, copia)
            bloque = copia / 'tabla' / 'bloque-000.bin'
            destino = copia / 'tabla' / 'copia.bin'
            destino.write_bytes(bloque.read_bytes())
            bloque.unlink()
            bloque.symlink_to(destino)
            self.assertEqual(verificar(copia, self.sha_esperado)['estado'], 'NO_DATA')

    def test_tabla_no_duplicada_en_fuentes(self):
        import re
        fuente = b''.join(p.read_bytes() for p in sorted((self.origen / 'tabla').glob('bloque-*.bin')))
        objeto = re.search(rb'var HUE\s*=\s*(\{[^{}]+\})', fuente).group(1)
        patron = rb"['\"]?([A-Z_]+)['\"]?\s*:\s*(\d+)"
        claves = set(dict(re.findall(patron, objeto)))
        raiz = Path(__file__).parent
        archivos = list(raiz.glob('*.py'))
        for carpeta in ('interface', 'assets', 'atlas'):
            archivos.extend((raiz / carpeta).rglob('*.js'))
        # La copia de la web en interface/face/bubble/ no es una segunda tabla:
        # son los bytes exactos de public/game/tabla_semantica.js, clavados por
        # sha256 en test_face.py. Una edicion local la pone roja alli.
        vendida = raiz / 'interface' / 'face' / 'bubble'
        archivos = [a for a in archivos if vendida not in a.parents]
        for archivo in archivos:
            for bloque in re.findall(rb'\{[^{}]+\}', archivo.read_bytes()):
                self.assertFalse(claves <= set(dict(re.findall(patron, bloque))),
                                 'tabla semantica duplicada en ' + archivo.name)

if __name__ == '__main__':
    unittest.main()
