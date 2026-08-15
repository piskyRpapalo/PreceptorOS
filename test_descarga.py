"""Pruebas de descarga.py. Deterministas y sin red: el origen se sustituye.

Cada prueba que dice "falla" comprueba además que NO queda basura y que NO
aparece el fichero final. Un fallo que deja medio fichero es peor que el
fallo, porque el siguiente arranque lo encuentra y se lo cree.
"""

import hashlib
import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import descarga as D

CUERPO = b"cerebro de mentira" * 1000
HUELLA = hashlib.sha256(CUERPO).hexdigest()


def pieza(sha=HUELLA, tam=len(CUERPO), destino="modelos/prueba.gguf"):
    return D.Pieza(
        nombre="Prueba", url="https://ejemplo.invalid/m.gguf",
        sha256=sha, bytes=tam, licencia="Apache-2.0", destino=destino,
    )


class FlujoFalso(io.BytesIO):
    """Un origen sin red. `url` imita el atributo de la respuesta real."""
    url = "https://ejemplo.invalid/m.gguf"


def origen(cuerpo=CUERPO, total="auto", url=None):
    """Sustituye a abrir(): devuelve (flujo, total, url_final)."""
    def _abrir(_url):
        t = len(cuerpo) if total == "auto" else total
        f = FlujoFalso(cuerpo)
        if url:
            f.url = url
        return f, t, f.url
    return _abrir


class Huellas(unittest.TestCase):
    def test_1_huella_por_trozos_coincide_con_la_directa(self):
        with TemporaryDirectory() as d:
            r = Path(d) / "x.bin"
            r.write_bytes(CUERPO)
            self.assertEqual(D.huella_fichero(r, bloque=7), HUELLA)

    def test_2_sin_total_no_hay_porcentaje_inventado(self):
        self.assertIn("NO_DATA", D.barra(1234, None))
        self.assertNotIn("%", D.barra(1234, None))
        self.assertEqual(D.humano(None), "NO_DATA")

    def test_3_flujo_devuelve_bytes_y_huella(self):
        with TemporaryDirectory() as d:
            p = Path(d) / "p.partial"
            n, h = D.escribir_flujo(FlujoFalso(CUERPO), p, len(CUERPO), None)
        self.assertEqual((n, h), (len(CUERPO), HUELLA))


class Transporte(unittest.TestCase):
    def test_4_http_pelado_se_rechaza_sin_tocar_la_red(self):
        with self.assertRaises(D.TransporteInseguro):
            D.abrir("http://ejemplo.invalid/m.gguf")

    def test_5_redireccion_que_degrada_se_rechaza(self):
        """Se pide https y el servidor redirige a http: urllib la sigue en
        silencio. Aquí se comprueba que abrir() la caza y cierra el flujo."""
        class Respuesta(io.BytesIO):
            url = "http://cdn.invalid/m.gguf"
            headers = {"Content-Length": "10"}
            cerrado = False

            def close(self):
                type(self).cerrado = True

        with mock.patch.object(D.urllib.request, "urlopen",
                               lambda *a, **k: Respuesta(b"0123456789")):
            with self.assertRaises(D.TransporteInseguro):
                D.abrir("https://ejemplo.invalid/m.gguf")
        self.assertTrue(Respuesta.cerrado, "el flujo degradado quedó abierto")

    def test_5b_sin_red_es_ausencia_declarada_no_averia(self):
        def cae(*a, **k):
            raise D.urllib.error.URLError("Name or service not known")

        with mock.patch.object(D.urllib.request, "urlopen", cae):
            with self.assertRaises(D.SinRed):
                D.abrir("https://ejemplo.invalid/m.gguf")


class Colocacion(unittest.TestCase):
    def test_6_descarga_buena_coloca_y_no_deja_parcial(self):
        with TemporaryDirectory() as d, mock.patch.object(D, "abrir", origen()):
            f = D.descargar(pieza(), raiz=Path(d), salida=None)
            self.assertTrue(f.is_file())
            self.assertEqual(f.read_bytes(), CUERPO)
            self.assertEqual(list(f.parent.glob("*.partial")), [])

    def test_7_huella_mala_borra_todo_y_no_crea_el_final(self):
        malo = "0" * 64
        with TemporaryDirectory() as d, mock.patch.object(D, "abrir", origen()):
            with self.assertRaises(D.HuellaNoCoincide):
                D.descargar(pieza(sha=malo), raiz=Path(d), salida=None)
            hay = list((Path(d) / "modelos").glob("*"))
            self.assertEqual(hay, [], f"quedó basura: {hay}")

    def test_8_descarga_truncada_se_detecta_y_se_limpia(self):
        corto = CUERPO[:100]
        with TemporaryDirectory() as d, \
             mock.patch.object(D, "abrir", origen(corto, total=len(CUERPO))):
            with self.assertRaises(D.DescargaFallida):
                D.descargar(pieza(), raiz=Path(d), salida=None)
            self.assertEqual(list((Path(d) / "modelos").glob("*")), [])

    def test_9_catalogo_que_miente_para_antes_de_escribir(self):
        with TemporaryDirectory() as d, \
             mock.patch.object(D, "abrir", origen(total=999999)):
            with self.assertRaises(D.DescargaFallida) as ctx:
                D.descargar(pieza(), raiz=Path(d), salida=None)
            self.assertIn("no supe prometer", str(ctx.exception))
            self.assertEqual(list((Path(d) / "modelos").glob("*")), [])

    def test_10_interrupcion_no_deja_gigas_de_basura(self):
        class Rompe(FlujoFalso):
            def read(self, *a):
                raise KeyboardInterrupt

        def _abrir(_u):
            return Rompe(b""), len(CUERPO), "https://ejemplo.invalid/m.gguf"

        with TemporaryDirectory() as d, mock.patch.object(D, "abrir", _abrir):
            with self.assertRaises(KeyboardInterrupt):
                D.descargar(pieza(), raiz=Path(d), salida=None)
            self.assertEqual(list((Path(d) / "modelos").glob("*")), [])

    def test_11_sin_espacio_se_declara_antes_de_abrir_la_red(self):
        def jamas(_u):
            raise AssertionError("no debió abrirse la red")

        Uso = D.shutil.disk_usage(".").__class__
        with TemporaryDirectory() as d, mock.patch.object(D, "abrir", jamas), \
             mock.patch.object(D.shutil, "disk_usage",
                               lambda _p: Uso(total=1, used=1, free=10)):
            with self.assertRaises(D.EspacioInsuficiente):
                D.descargar(pieza(), raiz=Path(d), salida=None)

    def test_12_fichero_ya_correcto_no_se_vuelve_a_bajar(self):
        def jamas(_u):
            raise AssertionError("no debió abrirse la red")

        with TemporaryDirectory() as d:
            final = Path(d) / "modelos" / "prueba.gguf"
            final.parent.mkdir(parents=True)
            final.write_bytes(CUERPO)
            with mock.patch.object(D, "abrir", jamas):
                self.assertEqual(D.descargar(pieza(), raiz=Path(d), salida=None), final)


class ElDiscoManda(unittest.TestCase):
    def test_13_presente_es_falso_si_el_fichero_no_esta(self):
        with TemporaryDirectory() as d:
            self.assertFalse(D.presente(pieza(), raiz=Path(d)))

    def test_14_presente_es_falso_si_el_contenido_cambio(self):
        with TemporaryDirectory() as d:
            final = Path(d) / "modelos" / "prueba.gguf"
            final.parent.mkdir(parents=True)
            final.write_bytes(CUERPO + b"manoseado")
            self.assertFalse(D.presente(pieza(), raiz=Path(d)))

    def test_15_presente_es_cierto_solo_con_la_huella_publicada(self):
        with TemporaryDirectory() as d:
            final = Path(d) / "modelos" / "prueba.gguf"
            final.parent.mkdir(parents=True)
            final.write_bytes(CUERPO)
            self.assertTrue(D.presente(pieza(), raiz=Path(d)))


class Anuncio(unittest.TestCase):
    def test_16_el_anuncio_lleva_licencia_huella_y_aviso(self):
        s = io.StringIO()
        D.anunciar(pieza(), salida=s)
        t = s.getvalue()
        for esperado in ("Licencia", "Apache-2.0", HUELLA, "de cero"):
            self.assertIn(esperado, t)

    def test_17_peso_desconocido_se_dice_no_data(self):
        s = io.StringIO()
        D.anunciar(pieza(tam=None), salida=s)
        self.assertIn("NO_DATA", s.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
