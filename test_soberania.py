"""Pruebas de soberania.py. El suelo se demuestra, no se promete.

Cada caso ataca una forma distinta de acabar en un nivel que nadie concedio:
sin fichero, con el fichero roto, con el disco mudo, con la red caida, con una
capacidad que no existe. Todas tienen que terminar en el mismo sitio -- el 0 --
y ninguna puede terminar en una excepcion: un modulo de permisos que revienta
deja al que llama decidiendo por su cuenta, que es justo lo que no puede pasar.

La red NO se simula cayendose de verdad. Se le miente al modulo con
`unittest.mock` y se comprueba que quien dependia de ella dice NO_DATA con su
causa en vez de romperse. Una prueba que necesita red para demostrar que no
hace falta red seria su propia contradiccion.
"""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import estado as E
import soberania as S


class ElSuelo(unittest.TestCase):
    """Sin dato no hay permiso. Ni excepcion, ni None, ni un nivel de cortesia."""

    def test_1_sin_fichero_de_estado_el_nivel_es_cero(self):
        with TemporaryDirectory() as d:
            n = S.obtener_nivel(Path(d), argv=[])
            self.assertIsInstance(n, int)
            self.assertEqual(n, S.SANTUARIO)

    def test_2_estado_corrupto_da_cero_y_lo_declara(self):
        with TemporaryDirectory() as d:
            (Path(d) / E.FICHERO).write_text('{"nivel_sobera', encoding="utf-8")
            self.assertEqual(S.obtener_nivel(Path(d), argv=[]), S.SANTUARIO)
            causa = S.causa("inferencia_local", Path(d), argv=[])
            self.assertIn(S.NO_DATA, causa)

    def test_3_estado_ilegible_da_cero_sin_reventar(self):
        """El disco no responde. Un permiso no se hereda de un error de E/S."""
        with TemporaryDirectory() as d:
            E.fijar_nivel(3, Path(d))
            with mock.patch.object(E, "nivel", side_effect=OSError("disco mudo")):
                self.assertEqual(S.obtener_nivel(Path(d), argv=[]), S.SANTUARIO)

    def test_4_un_nivel_legitimo_si_se_lee(self):
        """El control negativo. Si esto pasara siempre, las otras no probarian nada."""
        with TemporaryDirectory() as d:
            E.fijar_nivel(2, Path(d))
            self.assertEqual(S.obtener_nivel(Path(d), argv=[]), 2)


class ElColapso(unittest.TestCase):
    """Se cae de golpe, no baja de nivel en nivel."""

    def test_5_nivel_dos_y_se_firma_el_corte_da_cero_inmediato(self):
        with TemporaryDirectory() as d:
            E.fijar_nivel(2, Path(d))
            self.assertEqual(S.obtener_nivel(Path(d), argv=[]), 2)
            self.assertEqual(S.modo_santuario(Path(d)), S.SANTUARIO)
            try:
                self.assertEqual(S.obtener_nivel(Path(d), argv=[]), S.SANTUARIO)
            finally:
                S.salir_de_santuario(Path(d))

    def test_6_el_colapso_no_pasa_por_el_uno_ni_por_el_dos(self):
        """No hay estado intermedio observable: se pide el corte y ya esta en 0."""
        with TemporaryDirectory() as d:
            E.fijar_nivel(3, Path(d))
            try:
                S.modo_santuario(Path(d))
                vistos = [S.obtener_nivel(Path(d), argv=[]) for _ in range(5)]
                self.assertEqual(vistos, [S.SANTUARIO] * 5)
            finally:
                S.salir_de_santuario(Path(d))

    def test_7_el_centinela_solo_corta_no_borra_lo_declarado(self):
        with TemporaryDirectory() as d:
            E.fijar_nivel(3, Path(d))
            antes = (Path(d) / E.FICHERO).read_bytes()
            try:
                S.modo_santuario(Path(d))
                self.assertTrue(E.ruta_centinela(Path(d)).exists())
                self.assertEqual((Path(d) / E.FICHERO).read_bytes(), antes)
            finally:
                S.salir_de_santuario(Path(d))
            self.assertEqual(S.obtener_nivel(Path(d), argv=[]), 3)

    def test_8_la_bandera_de_linea_de_ordenes_corta_sin_tocar_el_disco(self):
        with TemporaryDirectory() as d:
            E.fijar_nivel(3, Path(d))
            self.assertEqual(
                S.obtener_nivel(Path(d), argv=["--santuario"]), S.SANTUARIO)
            self.assertFalse(E.ruta_centinela(Path(d)).exists(),
                             "la bandera corta en este proceso, no escribe nada")
            self.assertEqual(S.obtener_nivel(Path(d), argv=[]), 3)

    def test_9_un_argv_ilegible_se_lee_como_corte(self):
        class Hostil:
            def __contains__(self, otro):
                raise RuntimeError("argv hostil")
            def __iter__(self):
                raise RuntimeError("argv hostil")
        with TemporaryDirectory() as d:
            E.fijar_nivel(3, Path(d))
            self.assertEqual(S.obtener_nivel(Path(d), argv=Hostil()), S.SANTUARIO)


class LaConexionQueSeCae(unittest.TestCase):
    """Sin red no hay error de red: hay NO_DATA con su causa."""

    def test_10_perdida_de_conexion_deja_el_nivel_en_cero(self):
        with mock.patch.object(S, "obtener_nivel", return_value=S.SANTUARIO):
            self.assertFalse(S.verificar_permiso("recursos_externos"))

    def test_11_la_funcion_protegida_dice_no_data_y_no_se_ejecuta(self):
        llamadas = []

        @S.exige("recursos_externos")
        def pedir_algo_de_fuera():
            llamadas.append(1)
            return "respuesta de la nube"

        with mock.patch.object(S, "obtener_nivel", return_value=S.SANTUARIO):
            resultado = pedir_algo_de_fuera()
        self.assertEqual(resultado, S.NO_DATA)
        self.assertEqual(llamadas, [], "la funcion protegida no puede haber corrido")

    def test_12_la_misma_funcion_corre_cuando_el_nivel_da(self):
        @S.exige("recursos_externos")
        def pedir_algo_de_fuera():
            return "respuesta de fuera"

        with mock.patch.object(S, "obtener_nivel", return_value=2):
            self.assertEqual(pedir_algo_de_fuera(), "respuesta de fuera")

    def test_13_ningun_mensaje_visible_parece_un_error_de_red(self):
        with TemporaryDirectory() as d:
            causa = S.causa("recursos_externos", Path(d), argv=[])
            bajo = causa.lower()
            for palabra in ("traceback", "connection", "conexion", "timeout",
                            "socket", "errno", "refused", "error"):
                self.assertNotIn(palabra, bajo, f"la causa suena a fallo: {causa!r}")
            self.assertTrue(causa.startswith(S.NO_DATA))


class LosPermisos(unittest.TestCase):
    """Una capacidad concreta, un nivel minimo, y ante la duda que no."""

    def test_14_capacidad_de_nivel_uno_con_nivel_cero_es_false(self):
        with TemporaryDirectory() as d:
            self.assertEqual(S.obtener_nivel(Path(d), argv=[]), S.SANTUARIO)
            self.assertFalse(S.verificar_permiso("inferencia_local", Path(d), argv=[]))

    def test_15_quien_llama_puede_decir_no_data_sin_romperse(self):
        with TemporaryDirectory() as d:
            if S.verificar_permiso("inferencia_local", Path(d), argv=[]):
                salida = "cerebro local"
            else:
                salida = S.causa("inferencia_local", Path(d), argv=[])
            self.assertTrue(salida.startswith(S.NO_DATA))
            self.assertIn("inferencia_local", salida)

    def test_16_cada_capacidad_se_concede_exactamente_desde_su_nivel(self):
        with TemporaryDirectory() as d:
            for capacidad, minimo in S.CAPACIDADES.items():
                for n in range(0, S.NIVEL_MAXIMO + 1):
                    E.fijar_nivel(n, Path(d))
                    with self.subTest(capacidad=capacidad, nivel=n):
                        self.assertEqual(
                            S.verificar_permiso(capacidad, Path(d), argv=[]),
                            n >= minimo)

    def test_17_una_capacidad_que_nadie_declaro_no_la_concede_ni_el_maximo(self):
        with TemporaryDirectory() as d:
            E.fijar_nivel(S.NIVEL_MAXIMO, Path(d))
            for inventada in ("modo_dios", "", None, 7, ["lista"], {"a": 1}):
                with self.subTest(capacidad=inventada):
                    self.assertFalse(
                        S.verificar_permiso(inventada, Path(d), argv=[]))

    def test_18_ninguna_capacidad_se_concede_en_el_santuario(self):
        with TemporaryDirectory() as d:
            for capacidad in S.CAPACIDADES:
                with self.subTest(capacidad=capacidad):
                    self.assertFalse(
                        S.verificar_permiso(capacidad, Path(d), argv=[]),
                        "el nivel 0 no concede nada por encima de si mismo")

    def test_19_el_nivel_cero_no_aparece_en_la_tabla_de_capacidades(self):
        """Lo que el santuario ya hace no pide permiso: pedirlo lo volveria opcional."""
        for capacidad, minimo in S.CAPACIDADES.items():
            with self.subTest(capacidad=capacidad):
                self.assertGreaterEqual(minimo, 1)
                self.assertLessEqual(minimo, S.NIVEL_MAXIMO)


class FalloCerrado(unittest.TestCase):
    """Ni una excepcion hacia fuera, ni un dato a medio escribir."""

    def test_20_la_api_publica_no_lanza_jamas(self):
        rotos = (
            None, 0, "", "  ", "2", -1, 4, 99, 3.5, True, [1], {"a": 1},
            object(), Path("/no/existe/en/ningun/sitio"),
        )
        with TemporaryDirectory() as d:
            for valor in rotos:
                with self.subTest(valor=repr(valor)):
                    try:
                        S.obtener_nivel(valor, argv=[])
                        S.verificar_permiso(valor, Path(d), argv=[])
                        S.causa(valor, Path(d), argv=[])
                        S.santuario_activo(valor, argv=[])
                    except Exception as e:                       # noqa: BLE001
                        self.fail(f"la api lanzo {type(e).__name__}: {e}")

    def test_21_obtener_nivel_devuelve_siempre_un_entero_en_rango(self):
        with TemporaryDirectory() as d:
            for crudo in ('{"nivel_soberania": 9}', "no soy json", "[]",
                          '{"nivel_soberania": "dos"}', ""):
                (Path(d) / E.FICHERO).write_text(crudo, encoding="utf-8")
                n = S.obtener_nivel(Path(d), argv=[])
                with self.subTest(crudo=crudo):
                    self.assertIsInstance(n, int)
                    self.assertNotIsInstance(n, bool)
                    self.assertGreaterEqual(n, S.SANTUARIO)
                    self.assertLessEqual(n, S.NIVEL_MAXIMO)

    def test_22_el_colapso_no_deja_ficheros_a_medias(self):
        with TemporaryDirectory() as d:
            E.fijar_nivel(2, Path(d))
            try:
                S.modo_santuario(Path(d))
            finally:
                restos = sorted(p.name for p in Path(d).glob("*.partial"))
                S.salir_de_santuario(Path(d))
            self.assertEqual(restos, [], f"quedo trabajo a medias: {restos}")

    def test_23_el_estado_sigue_siendo_json_valido_despues_del_corte(self):
        with TemporaryDirectory() as d:
            E.fijar_nivel(2, Path(d))
            try:
                S.modo_santuario(Path(d))
                datos = json.loads(
                    (Path(d) / E.FICHERO).read_text(encoding="utf-8"))
            finally:
                S.salir_de_santuario(Path(d))
            self.assertEqual(sorted(datos), sorted(E.CLAVES))

    def test_24_el_colapso_aguanta_un_disco_que_no_deja_escribir(self):
        """Aunque el centinela no se pueda poner, el corte manda en este proceso."""
        with TemporaryDirectory() as d:
            E.fijar_nivel(3, Path(d))
            with mock.patch.object(E, "ruta_centinela",
                                   side_effect=OSError("solo lectura")):
                self.assertEqual(S.modo_santuario(Path(d)), S.SANTUARIO)
            try:
                self.assertEqual(S.obtener_nivel(Path(d), argv=[]), S.SANTUARIO)
            finally:
                S.salir_de_santuario(Path(d))

    def test_25_salir_del_santuario_no_sube_el_nivel_por_su_cuenta(self):
        with TemporaryDirectory() as d:
            S.modo_santuario(Path(d))
            self.assertEqual(S.salir_de_santuario(Path(d)), S.SANTUARIO)
            self.assertFalse(E.ruta_centinela(Path(d)).exists())

    def test_26_el_modulo_no_abre_un_solo_socket(self):
        fuente = Path(__file__).with_name("soberania.py").read_text(encoding="utf-8")
        for prohibido in ("import socket", "urllib", "http.client", "requests",
                          "subprocess", "ssl", "asyncio"):
            self.assertNotIn(prohibido, fuente,
                             f"el guardian no puede depender de {prohibido}")


class ElDecoradorFallaCerrado(unittest.TestCase):
    """El guardian de arriba, atacado por donde los otros casos no llegan.

    Los casos 11 y 12 mienten en `obtener_nivel`, asi que prueban el decorador
    pero saltan por encima de la logica que decide el nivel. Estos mienten un
    piso mas abajo -- en `estado` -- y dejan correr al guardian entero.
    """

    def test_27_capacidad_por_encima_del_nivel_declarado_da_no_data(self):
        llamadas = []

        @S.exige("hardware_local")                      # pide 3
        def tocar_un_aparato():
            llamadas.append(1)
            return "aparato"

        with mock.patch.object(E, "nivel", return_value=2), \
             mock.patch.object(E, "santuario_forzado", return_value=False):
            self.assertEqual(tocar_un_aparato(), S.NO_DATA)
        self.assertEqual(llamadas, [])

    def test_28_la_misma_capacidad_en_su_nivel_exacto_si_corre(self):
        @S.exige("hardware_local")
        def tocar_un_aparato():
            return "aparato"

        with mock.patch.object(E, "nivel", return_value=3), \
             mock.patch.object(E, "santuario_forzado", return_value=False):
            self.assertEqual(tocar_un_aparato(), "aparato")

    def test_29_el_centinela_apaga_en_caliente_algo_ya_concedido(self):
        """Concedido no es para siempre: el corte se nota en la siguiente llamada."""
        @S.exige("recursos_externos")
        def salir_fuera():
            return "fuera"

        with mock.patch.object(E, "nivel", return_value=3):
            with mock.patch.object(E, "santuario_forzado", return_value=False):
                self.assertEqual(salir_fuera(), "fuera")
            with mock.patch.object(E, "santuario_forzado", return_value=True):
                self.assertEqual(salir_fuera(), S.NO_DATA)

    def test_30_el_hueco_puede_declararse_con_otra_cosa_que_no_sea_no_data(self):
        @S.exige("recursos_externos", si_no=[])
        def traer_una_lista():
            return ["algo"]

        with mock.patch.object(S, "obtener_nivel", return_value=S.SANTUARIO):
            self.assertEqual(traer_una_lista(), [])

    def test_31_el_decorador_no_borra_la_funcion_que_envuelve(self):
        @S.exige("inferencia_local")
        def pensar_aqui():
            """Docstring que tiene que sobrevivir."""
            return "pensado"

        self.assertEqual(pensar_aqui.__name__, "pensar_aqui")
        self.assertIn("sobrevivir", pensar_aqui.__doc__)
        self.assertEqual(pensar_aqui.capacidad, "inferencia_local")

    def test_32_un_estado_que_revienta_no_deja_correr_la_funcion(self):
        llamadas = []

        @S.exige("inferencia_local")
        def pensar_aqui():
            llamadas.append(1)
            return "pensado"

        with mock.patch.object(E, "santuario_forzado",
                               side_effect=RuntimeError("estado roto")):
            self.assertEqual(pensar_aqui(), S.NO_DATA)
        self.assertEqual(llamadas, [], "un fallo del estado no puede abrir la puerta")


if __name__ == "__main__":
    unittest.main(verbosity=2)
