"""Pruebas de estado.py. El disco manda sobre la bandera, y escribir es todo o nada."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import estado as E


class Lectura(unittest.TestCase):
    def test_1_sin_fichero_todo_es_falso(self):
        with TemporaryDirectory() as d:
            self.assertEqual(E.leer(Path(d)), dict(E.VACIO))

    def test_2_json_corrupto_no_mata_ni_obliga_a_redescargar(self):
        with TemporaryDirectory() as d:
            (Path(d) / E.FICHERO).write_text('{"cerebro_desc', encoding="utf-8")
            self.assertEqual(E.leer(Path(d)), dict(E.VACIO))

    def test_3_claves_ausentes_se_asumen_falsas_y_las_de_mas_se_ignoran(self):
        with TemporaryDirectory() as d:
            (Path(d) / E.FICHERO).write_text(
                '{"ritual_firmado": true, "colonias_en_marte": true}', encoding="utf-8")
            leido = E.leer(Path(d))
            self.assertTrue(leido["ritual_firmado"])
            self.assertFalse(leido["cerebro_descargado"])
            self.assertNotIn("colonias_en_marte", leido)


class Escritura(unittest.TestCase):
    def test_4_ida_y_vuelta(self):
        with TemporaryDirectory() as d:
            E.escribir({"cerebro_descargado": True}, Path(d))
            self.assertTrue(E.leer(Path(d))["cerebro_descargado"])

    def test_5_no_queda_parcial(self):
        with TemporaryDirectory() as d:
            E.fijar("voz_descargada", True, Path(d))
            self.assertEqual(list(Path(d).glob("*.partial")), [])

    def test_6_fijar_no_pisa_las_otras_banderas(self):
        with TemporaryDirectory() as d:
            E.escribir({"cerebro_descargado": True, "ritual_firmado": True}, Path(d))
            E.fijar("voz_descargada", True, Path(d))
            leido = E.leer(Path(d))
            self.assertEqual([leido[b] for b in E.BANDERAS], [True, True, True])

    def test_7_bandera_inventada_se_rechaza(self):
        with TemporaryDirectory() as d:
            with self.assertRaises(KeyError):
                E.fijar("modo_dios", True, Path(d))

    def test_8_el_fichero_escrito_es_json_valido_y_completo(self):
        with TemporaryDirectory() as d:
            E.escribir({}, Path(d))
            datos = json.loads((Path(d) / E.FICHERO).read_text(encoding="utf-8"))
            self.assertEqual(sorted(datos), sorted(E.BANDERAS))


class ElDiscoManda(unittest.TestCase):
    def test_9_bandera_que_miente_se_corrige_y_se_declara(self):
        with TemporaryDirectory() as d:
            E.escribir({"cerebro_descargado": True}, Path(d))
            despues, mentian = E.reconciliar(
                {"cerebro_descargado": lambda: False}, Path(d))
            self.assertFalse(despues["cerebro_descargado"])
            self.assertEqual(mentian, ["cerebro_descargado"])
            self.assertFalse(E.leer(Path(d))["cerebro_descargado"])

    def test_10_bandera_que_dice_la_verdad_no_se_reescribe(self):
        with TemporaryDirectory() as d:
            E.escribir({"cerebro_descargado": True}, Path(d))
            antes = (Path(d) / E.FICHERO).read_bytes()
            _, mentian = E.reconciliar({"cerebro_descargado": lambda: True}, Path(d))
            self.assertEqual(mentian, [])
            self.assertEqual((Path(d) / E.FICHERO).read_bytes(), antes)

    def test_11_el_ritual_sobrevive_a_la_reconciliacion(self):
        with TemporaryDirectory() as d:
            E.escribir({"ritual_firmado": True, "cerebro_descargado": True}, Path(d))
            despues, _ = E.reconciliar({"cerebro_descargado": lambda: False}, Path(d))
            self.assertTrue(despues["ritual_firmado"],
                            "perder el cerebro no debe borrar el ritual")

    def test_12_estado_perdido_se_reconstruye_del_disco_sin_redescargar(self):
        with TemporaryDirectory() as d:
            despues, mentian = E.reconciliar(
                {"cerebro_descargado": lambda: True}, Path(d))
            self.assertTrue(despues["cerebro_descargado"])
            self.assertEqual(mentian, ["cerebro_descargado"])


class Frontera(unittest.TestCase):
    def test_13_el_estado_no_guarda_datos_de_la_persona(self):
        """Nombre, idioma y ritmo viven en la tabla profile. Aquí no."""
        for prohibida in ("nombre", "name", "idioma", "language", "ritmo"):
            self.assertNotIn(prohibida, E.BANDERAS)
        self.assertEqual(len(E.BANDERAS), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
