#!/usr/bin/env python3
"""entorno.py · las variables de entorno, con el nombre viejo aún válido.

**Solo stdlib.**

POR QUÉ EXISTE
--------------
Mandato 1 renombra el producto. Las variables de entorno son la parte del
renombrado que **no vive en este repositorio**: viven en el `.bashrc` de quien
lo usa, en el `.service` que se escribió hace un mes, en el guion que alguien
puso en su teléfono, y en la nota que se guardó en un cuaderno. Cambiarlas de
golpe no rompe el producto — rompe las máquinas de otros, en silencio, y el
síntoma es que una opción que llevaba meses funcionando deja de tener efecto
sin que nada falle.

Por eso el nombre nuevo manda y el viejo **sigue funcionando**, con un aviso
por consola la primera vez que se usa cada uno. El aviso va a `stderr` y una
sola vez por variable y proceso: repetirlo en cada turno lo convertiría en
ruido, y el ruido se apaga.

LA REGLA DE LA PRECEDENCIA
--------------------------
Si están las dos puestas, gana la nueva. Quien se ha molestado en poner el
nombre nuevo ya migró; que la vieja lo pisara sería castigar justo a quien hizo
los deberes.

FECHA DE MUERTE, ESCRITA
------------------------
`SOPORTE_NOMBRE_VIEJO_HASTA` no es decorativa. Una compatibilidad sin fecha se
queda para siempre, y dentro de tres años nadie sabrá si se puede quitar. Ese
día se borra este puente, no antes.
"""
from __future__ import annotations

import os
import sys

PREFIJO = "PRECEPTOROS_"
PREFIJO_ANTERIOR = "AURELIUS_"

# 90 días desde el renombrado (2026-08-25). Ver el docstring: la fecha existe
# para que el puente se pueda quitar sin discutirlo de memoria.
SOPORTE_NOMBRE_VIEJO_HASTA = "2026-11-23"

_ya_avisado = set()


def _avisar(viejo, nuevo):
    if viejo in _ya_avisado:
        return
    _ya_avisado.add(viejo)
    print(f"Aviso · `{viejo}` pasó a llamarse `{nuevo}`. La vieja sigue "
          f"funcionando hasta el {SOPORTE_NOMBRE_VIEJO_HASTA}; después, no.",
          file=sys.stderr)


def leer(sufijo, defecto=""):
    """El valor de la variable, por su nombre nuevo o por el viejo.

    `sufijo` va SIN prefijo: `leer("MOTOR")` mira `PRECEPTOROS_MOTOR` y, si no
    está, `AURELIUS_MOTOR`.
    """
    nuevo = PREFIJO + sufijo
    if nuevo in os.environ:
        return os.environ[nuevo]
    viejo = PREFIJO_ANTERIOR + sufijo
    if viejo in os.environ:
        _avisar(viejo, nuevo)
        return os.environ[viejo]
    return defecto


def puesta(sufijo):
    """Si la variable está declarada, con cualquiera de los dos nombres.

    Distinto de `leer(...) != ""`: una variable puesta a cadena vacía ESTÁ
    puesta, y hay opciones donde eso significa algo.
    """
    return (PREFIJO + sufijo) in os.environ or \
           (PREFIJO_ANTERIOR + sufijo) in os.environ


def activa(sufijo):
    """El patrón `== "1"`, que es como se leen las banderas en este árbol."""
    return leer(sufijo).strip() == "1"


def nombres(sufijo):
    """Los dos nombres de una variable. Para mensajes de ayuda."""
    return PREFIJO + sufijo, PREFIJO_ANTERIOR + sufijo
