#!/usr/bin/env python3
"""La regla del NO_DATA aplicada a los numeros.

Los casos de esta suite no son inventados: son las afirmaciones reales con las
que los adaptadores de La Charla pasaron una corrida entera en verde el
2026-09-07.
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cifras as C                               # noqa: E402


class TestCifras(unittest.TestCase):

    # --- lo que se escapo de verdad ---------------------------------------

    def test_los_200_gigas_que_pasaron_en_verde(self):
        """La afirmacion real. Son 4,4, y nadie los menciono en la pregunta."""
        s = C.sin_respaldo("El modelo base ocupa unos 200 gigas.",
                           "cuanto ocupa el modelo base")
        self.assertEqual(s, ["200 gb"])

    def test_los_8_GB_de_una_maquina_que_no_ha_visto(self):
        s = C.sin_respaldo("Con los 8 GB que tienes va justo.", "va a ir bien?")
        self.assertEqual(s, ["8 gb"])

    # --- lo que NO debe marcar --------------------------------------------

    def test_repetir_lo_que_dijo_la_persona_es_escuchar(self):
        s = C.sin_respaldo("Con 16 GB vas sobrado para ese modelo.",
                           "Tengo 16 GB de RAM, cual me recomiendas")
        self.assertEqual(s, [])

    def test_lo_que_la_app_sabe_de_la_maquina_tambien_respalda(self):
        s = C.sin_respaldo("Tu equipo declara 16 hilos, asi que cabe.",
                           "cabra?",
                           "AMD Ryzen 7 255 · 16 hilos · Linux")
        self.assertEqual(s, [])

    def test_la_misma_cifra_en_otra_grafia_sigue_teniendo_respaldo(self):
        """«16 gigas» y «16 GB» son el mismo hecho escrito de dos maneras."""
        s = C.sin_respaldo("Con 16 gigas vas bien.", "tengo 16 GB")
        self.assertEqual(s, [])

    def test_un_texto_sin_numeros_no_marca_nada(self):
        self.assertEqual(C.sin_respaldo("Depende de tu maquina.", "?"), [])

    def test_un_numero_sin_unidad_no_es_una_medida(self):
        """«el paso 3» o «la version 2» no son cantidades que contrastar."""
        self.assertEqual(C.sin_respaldo("Ve al paso 3 y luego al 4.", ""), [])

    # --- el aviso ----------------------------------------------------------

    def test_sin_hallazgos_no_hay_linea(self):
        self.assertEqual(C.aviso([]), "")

    def test_el_aviso_dice_lo_que_se_hizo_y_no_lo_que_no_se_sabe(self):
        """Decir «esta cifra es falsa» seria afirmar algo no comprobado.

        Es el mismo defecto que este modulo denuncia, cometido por el modulo.
        """
        a = C.aviso(["200 gb"])
        self.assertIn("200 gb", a)
        self.assertIn("nadie las ha comprobado", a)
        for palabra in ("falsa", "mentira", "inventada", "incorrecta"):
            self.assertNotIn(palabra, a.lower())

    def test_el_aviso_habla_el_idioma_del_turno(self):
        self.assertIn("no backing", C.aviso(["8 gb"], idioma="en"))

    # --- la forma ----------------------------------------------------------

    def test_los_decimales_a_la_espanola_y_a_la_inglesa_son_el_mismo_numero(self):
        self.assertEqual(C.cantidades("4,4 GB"), C.cantidades("4.4 GB"))

    def test_los_millares_no_se_leen_como_decimales_ni_al_reves(self):
        """Un normalizador que cambia el valor fabrica y esconde hallazgos.

        La primera version quitaba todos los puntos, asi que «4.4 GB» le salia
        cuarenta y cuatro gigas: marcaba una cifra que la pregunta si
        respaldaba, y habria dejado pasar la que no.
        """
        self.assertEqual(C.cantidades("4.4 GB"), {("4.4", "gb")})
        self.assertEqual(C.cantidades("1.000 GB"), {("1000", "gb")})
        self.assertEqual(C.cantidades("1,000 GB"), {("1000", "gb")})
        self.assertEqual(C.cantidades("1.234,5 GB"), {("1234.5", "gb")})

    def test_el_mismo_valor_escrito_distinto_es_el_mismo_valor(self):
        self.assertEqual(C.cantidades("0,50 GB"), C.cantidades("0.5 GB"))
        self.assertEqual(C.cantidades("4 GB"), C.cantidades("4,0 GB"))

    def test_el_porcentaje_y_los_tok_por_segundo_tambien_cuentan(self):
        s = C.sin_respaldo("Va a 40 tok/s y usa el 90% de la CPU.", "que tal va")
        self.assertEqual(s, ["40 tok/s", "90 %"])

    def test_ninguna_fuente_significa_que_nada_tiene_respaldo(self):
        """Sin fuentes no se calla: se marca todo. El lado seguro del error."""
        self.assertEqual(C.sin_respaldo("Ocupa 5 GB."), ["5 gb"])


if __name__ == "__main__":
    unittest.main()
