#!/usr/bin/env python3
"""El interruptor de hardware. Un sitio, no uno por suite.

sistema: MVP · solo biblioteca estandar.

Aurelius puede abrir el microfono (`oido`), sintetizar voz (`voz`) y sacar
audio por el altavoz (`fuga._reproducir_wav`). Las tres cosas son opcionales
por doctrina, y las tres son inaceptables durante una tanda de pruebas: una
suite que graba la habitacion de quien la corre tarda minutos, escucha lo que
no le han dado, y ademas no prueba lo que dice probar -- si la respuesta entra
por el microfono, el guion de teclado no se usa nunca.

Eso ya paso una vez (D77, `test_fuga`), y se arreglo dentro de esa suite. Se
arregla aqui para que la siguiente no lo repita: el apagado es del PRODUCTO,
no de cada fichero de pruebas, y viaja por variable de entorno para que valga
tambien en los procesos hijo -- `test_idioma` arranca `aurelius.py` como
subproceso, y un mock en memoria no cruza esa frontera.

    AURELIUS_SIN_HARDWARE=1   ni microfono, ni sintesis, ni altavoz.

No es "modo test": es una declaracion sobre la MAQUINA, como `estado.json`.
Sirve igual para un servidor sin tarjeta de sonido o para quien no quiere que
un programa le encienda el microfono, que son casos reales y no pruebas.
"""
from __future__ import annotations

import os
import unittest

import entorno as _entorno

SUFIJO = "SIN_HARDWARE"
VARIABLE = _entorno.PREFIJO + SUFIJO
VARIABLE_ANTERIOR = _entorno.PREFIJO_ANTERIOR + SUFIJO


def apagado() -> bool:
    """True si esta maquina tiene el hardware declarado como apagado."""
    return _entorno.activa(SUFIJO)


def activar():
    """Apaga el hardware para este proceso y los que arranque.

    Pone los DOS nombres, y aqui si hace falta: esta variable no la lee solo
    este arbol -- viaja a procesos hijo, y entre ellos hay guiones de `bin/` y
    herramientas de fuera que todavia buscan el nombre viejo. Escribir solo el
    nuevo dejaria el microfono encendido en un hijo que creia estar en
    silencio, que es exactamente el fallo que este modulo existe para impedir.
    """
    os.environ[VARIABLE] = "1"
    os.environ[VARIABLE_ANTERIOR] = "1"


class SinHardware(unittest.TestCase):
    """Mixin para suites que tocan `voz`, `oido` o el altavoz.

    Apaga el hardware ANTES de cada caso y devuelve el entorno como estaba
    despues, tambien si el caso revienta. Que sea por caso y no por fichero
    importa: un caso que quiera hardware de verdad (`test_voz_cyber` con Piper
    instalado) lo enciende para el solo sin dejarlo encendido para el
    siguiente.
    """

    def setUp(self):
        super().setUp()
        self._silencio_antes = os.environ.get(VARIABLE)
        activar()

    def tearDown(self):
        if self._silencio_antes is None:
            os.environ.pop(VARIABLE, None)
        else:
            os.environ[VARIABLE] = self._silencio_antes
        super().tearDown()
