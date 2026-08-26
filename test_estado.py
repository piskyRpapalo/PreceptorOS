"""Pruebas de estado.py. El disco manda sobre la bandera, y escribir es todo o nada.

Y el nivel de soberania: ante cualquier duda, el suelo. Un nivel ilegible, roto,
fuera de rango o ausente no concede nada -- y el centinela manda sobre lo que
diga el fichero sin llegar a tocarlo."""

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
            # CLAVES y no BANDERAS: el fichero lleva las tres banderas Y el
            # nivel. Si un dia se anade un campo y esta linea no se entera, el
            # estado escribiria algo que nadie declaro aqui.
            self.assertEqual(sorted(datos), sorted(E.CLAVES))


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


class NivelDeSoberania(unittest.TestCase):
    """El nivel es de la maquina, entero 0..3, y ante la duda baja."""

    def test_14_sin_fichero_el_nivel_es_el_suelo(self):
        with TemporaryDirectory() as d:
            self.assertEqual(E.leer(Path(d))[E.NIVEL], E.SANTUARIO)
            self.assertEqual(E.nivel(Path(d)), E.SANTUARIO)

    def test_15_un_nivel_declarado_se_lee(self):
        with TemporaryDirectory() as d:
            E.fijar_nivel(2, Path(d))
            self.assertEqual(E.nivel(Path(d)), 2)

    def test_16_todo_lo_que_no_es_un_entero_en_rango_cae_al_suelo(self):
        basura = (7, -1, 4, "2", 2.0, True, False, None, [2], {"n": 2})
        with TemporaryDirectory() as d:
            for valor in basura:
                with self.subTest(valor=valor):
                    (Path(d) / E.FICHERO).write_text(
                        json.dumps({E.NIVEL: valor}), encoding="utf-8")
                    self.assertEqual(E.nivel(Path(d)), E.SANTUARIO)

    def test_17_json_corrupto_no_concede_nivel(self):
        with TemporaryDirectory() as d:
            (Path(d) / E.FICHERO).write_text('{"nivel_sobera', encoding="utf-8")
            self.assertEqual(E.nivel(Path(d)), E.SANTUARIO)

    def test_18_fijar_nivel_no_pisa_las_banderas(self):
        with TemporaryDirectory() as d:
            E.escribir({"cerebro_descargado": True, "ritual_firmado": True}, Path(d))
            E.fijar_nivel(1, Path(d))
            leido = E.leer(Path(d))
            self.assertTrue(leido["cerebro_descargado"])
            self.assertTrue(leido["ritual_firmado"])
            self.assertEqual(leido[E.NIVEL], 1)

    def test_19_fijar_una_bandera_no_pierde_el_nivel(self):
        with TemporaryDirectory() as d:
            E.fijar_nivel(3, Path(d))
            E.fijar("voz_descargada", True, Path(d))
            self.assertEqual(E.nivel(Path(d)), 3)

    def test_20_un_nivel_fuera_de_rango_no_llega_al_disco(self):
        with TemporaryDirectory() as d:
            E.fijar_nivel(99, Path(d))
            datos = json.loads((Path(d) / E.FICHERO).read_text(encoding="utf-8"))
            self.assertEqual(datos[E.NIVEL], E.SANTUARIO)

    def test_21_escribir_a_medias_baja_el_nivel_nunca_lo_sube(self):
        with TemporaryDirectory() as d:
            E.fijar_nivel(2, Path(d))
            E.escribir({"cerebro_descargado": True}, Path(d))
            self.assertEqual(E.nivel(Path(d)), E.SANTUARIO)

    def test_22_el_nivel_no_se_reconcilia_contra_el_disco(self):
        with TemporaryDirectory() as d:
            E.fijar_nivel(2, Path(d))
            despues, mentian = E.reconciliar(
                {"cerebro_descargado": lambda: True}, Path(d))
            self.assertEqual(despues[E.NIVEL], 2)
            self.assertEqual(mentian, ["cerebro_descargado"])
            self.assertEqual(E.nivel(Path(d)), 2)


class ElCentinela(unittest.TestCase):
    """Un fichero vacio corta la corriente sin tocar el cableado."""

    def test_23_el_centinela_manda_sobre_la_declaracion(self):
        with TemporaryDirectory() as d:
            E.fijar_nivel(3, Path(d))
            E.ruta_centinela(Path(d)).write_text("", encoding="utf-8")
            self.assertEqual(E.nivel(Path(d)), E.SANTUARIO)

    def test_24_el_centinela_no_reescribe_lo_declarado(self):
        with TemporaryDirectory() as d:
            E.fijar_nivel(3, Path(d))
            antes = (Path(d) / E.FICHERO).read_bytes()
            E.ruta_centinela(Path(d)).write_text("", encoding="utf-8")
            E.nivel(Path(d))
            self.assertEqual((Path(d) / E.FICHERO).read_bytes(), antes)
            self.assertEqual(E.leer(Path(d))[E.NIVEL], 3)

    def test_25_quitar_el_centinela_devuelve_la_declaracion_intacta(self):
        with TemporaryDirectory() as d:
            E.fijar_nivel(2, Path(d))
            centinela = E.ruta_centinela(Path(d))
            centinela.write_text("", encoding="utf-8")
            self.assertEqual(E.nivel(Path(d)), E.SANTUARIO)
            centinela.unlink()
            self.assertEqual(E.nivel(Path(d)), 2)

    def test_26_declarar_nivel_con_el_centinela_puesto_no_lo_levanta(self):
        with TemporaryDirectory() as d:
            E.ruta_centinela(Path(d)).write_text("", encoding="utf-8")
            E.fijar_nivel(3, Path(d))
            self.assertTrue(E.ruta_centinela(Path(d)).exists(),
                            "declarar un nivel no puede borrar el centinela")
            self.assertEqual(E.nivel(Path(d)), E.SANTUARIO)


class Frontera(unittest.TestCase):
    def test_13_el_estado_no_guarda_datos_de_la_persona(self):
        """Nombre, idioma y ritmo viven en la tabla profile. Aquí no."""
        for prohibida in ("nombre", "name", "idioma", "language", "ritmo"):
            self.assertNotIn(prohibida, E.BANDERAS)
            self.assertNotIn(prohibida, E.CLAVES)
        self.assertEqual(len(E.BANDERAS), 3)
        self.assertEqual(len(E.CLAVES), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
