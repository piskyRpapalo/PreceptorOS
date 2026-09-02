#!/usr/bin/env python3
"""La Huella Soberana · quien eres para esta máquina, y para nadie más.

**Solo biblioteca estándar.**

EL NOMBRE, Y POR QUÉ NO ES EL DEL PLAN
--------------------------------------
El plan de misión pedía «una huella Ed25519». No la hay, y no por descuido:
la biblioteca estándar de Python **no trae Ed25519**. Traerlo exige
`cryptography` (dependencia pesada, que además no está en el Termux del
cliente) o escribir la primitiva a mano, que es criptografía sin auditar.

Las dos rompen las reglas que sostienen este producto. Así que esto es lo que
de verdad hace —`sha256` de una semilla aleatoria local— y se llama por su
nombre: **Huella Soberana (SHA256)**. Llamar Ed25519 a un sha256 sería mentir
sobre la primitiva justo en la pantalla que promete transparencia.

Firmado por el Soberano el 2026-09-02: «la doctrina valora la corrección
técnica sobre la consistencia con un error pasado».

Y hay una línea de la doctrina que esto respeta al llamarse como se llama:
*jamás se firma valor*. Esto **no es una clave**. No firma nada, no autentica
nada y no da acceso a nada. Es un nombre pseudónimo y estable para una
instalación. Si algún día hace falta firmar, hará falta otra cosa —y tendrá
que ser una decisión aparte, no una función que ya estaba aquí y «servía».

DE DÓNDE SALE
-------------
De `os.urandom`, y de nada más. No del usuario, no del hostname, no de la MAC.
Eso importa más de lo que parece: una huella derivada del entorno haría que
dos instalaciones del mismo equipo dieran la misma —o sea que la persona sería
rastreable entre ellas— y que dos personas con el mismo modelo de portátil
fueran indistinguibles. Azar local es lo único que da un identificador que
identifica a la instalación y a nada más.

UNA SEMILLA ROTA NO SE SUSTITUYE
--------------------------------
Si el fichero está pero no se puede leer como semilla, se declara `NO_DATA`
con su causa y **no se toca**. Regenerar en silencio convertiría a la persona
en otra sin avisarle, y encima destruiría una semilla que quizá se podía
recuperar de una copia. Un fallo que se parece a un primer arranque es el peor
de todos, porque no parece un fallo.
"""
from __future__ import annotations

import hashlib
import os

NOMBRE = "huella.semilla"
BYTES = 32                    # 256 bits de azar: el ancho del sha256 que sale
AUSENTE = "NO_DATA"


def _ruta(raiz):
    return os.path.join(str(raiz), NOMBRE)


def _nacer(ruta):
    """Escribe la semilla una sola vez, y solo si no había ninguna.

    `O_EXCL` y no un `if not exists`: entre la comprobación y la escritura cabe
    otro proceso, y dos procesos generando la semilla a la vez dejarían a uno
    de los dos con una identidad que el disco ya no tiene. Con `O_EXCL` el
    segundo falla, vuelve a leer, y los dos ven la misma.

    `0o600` desde el descriptor, no con un `chmod` después: entre el `open` y
    el `chmod` el fichero existe con los permisos del `umask`.
    """
    semilla = os.urandom(BYTES)
    fd = os.open(ruta, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(fd, semilla)
        os.fsync(fd)
    finally:
        os.close(fd)
    return semilla


def _corta(hexa):
    """Cuatro grupos de cuatro. Para comparar a ojo, que es para lo que sirve.

    Un hexadecimal de 64 caracteres seguidos no lo compara nadie: se mira el
    principio, se mira el final y se da por bueno el medio. Cuatro grupos
    cortos se leen en voz alta y se cotejan de verdad.
    """
    return " ".join(hexa[i:i + 4] for i in range(0, 16, 4))


def leer(raiz):
    """El paquete de identidad. Nunca lanza: devuelve el hueco declarado.

    {"estado", "huella", "corta", "causa"} — `huella` es None exactamente
    cuando `estado` no es "ok", y entonces `causa` dice por qué. Ningún camino
    devuelve una huella inventada.
    """
    ruta = _ruta(raiz)
    try:
        os.makedirs(str(raiz), exist_ok=True)
    except OSError as e:
        return {"estado": AUSENTE, "huella": None, "corta": None,
                "causa": f"no hay donde guardar la identidad ({type(e).__name__})"}

    try:
        with open(ruta, "rb") as fh:
            semilla = fh.read()
    except FileNotFoundError:
        try:
            semilla = _nacer(ruta)
        except FileExistsError:
            # Otro proceso ganó la carrera. Se lee la suya: hay una sola.
            try:
                with open(ruta, "rb") as fh:
                    semilla = fh.read()
            except OSError as e:
                return {"estado": AUSENTE, "huella": None, "corta": None,
                        "causa": f"la semilla no se deja leer ({type(e).__name__})"}
        except OSError as e:
            return {"estado": AUSENTE, "huella": None, "corta": None,
                    "causa": f"no se pudo crear la identidad ({type(e).__name__})"}
    except OSError as e:
        return {"estado": AUSENTE, "huella": None, "corta": None,
                "causa": f"la semilla no se deja leer ({type(e).__name__})"}

    if len(semilla) != BYTES:
        # Está y no cuadra. Se dice; no se sustituye.
        return {"estado": AUSENTE, "huella": None, "corta": None,
                "causa": (f"la semilla mide {len(semilla)} bytes y deberían ser "
                          f"{BYTES}: no se sustituye, porque una identidad que "
                          f"se regenera sola es otra persona")}

    hexa = hashlib.sha256(semilla).hexdigest()
    return {"estado": "ok", "huella": hexa, "corta": _corta(hexa), "causa": None}
