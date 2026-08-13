#!/usr/bin/env python3
"""Tono de conversacion: ritmo, pausas y elecciones. Nada mas.

sistema: MVP · solo biblioteca estandar.

Lo que este modulo ES: la cadencia con la que el producto habla. Texto y
temporizacion. Cero dependencias.

Lo que este modulo NO ES, y no puede llegar a ser: el caracter. El caracter
vive en el Preceptor, en la maquina de su dueno, y no viaja al clon publico.
Aqui no hay nada que sepa de modelos: el tono funciona igual con o sin ellos,
y por eso puede publicarse.

Interruptor: la variable de entorno AURELIUS_RITMO. 1.0 es el ritmo normal,
0 desactiva toda espera. Los tests la fijan a 0, porque una suite lenta se
deja de correr y un mecanismo que no se corre no protege nada.
"""
from __future__ import annotations

import os
import sys
import time

_RITMO = float(os.environ.get("AURELIUS_RITMO", "1.0"))


def fijar_ritmo(valor):
    """Cambia el ritmo en caliente. 0 desactiva las esperas."""
    global _RITMO
    _RITMO = float(valor)


def ritmo():
    return _RITMO


# --- cadencia --------------------------------------------------------------

def pausa(segundos):
    """Espera, o no espera nada si el ritmo esta apagado."""
    if _RITMO <= 0:
        return
    time.sleep(segundos * _RITMO)


def despacio(texto, cps=90, fin="\n"):
    """Escribe el texto a un ritmo legible, caracter a caracter.

    Con el ritmo apagado imprime de golpe. El texto resultante es IDENTICO en
    los dos modos: la cadencia no puede cambiar lo que se dice, solo cuando se
    dice. Un tono que altera el contenido no es tono, es otra cosa.
    """
    if _RITMO <= 0 or not sys.stdout.isatty():
        print(texto, end=fin)
        return
    espera = 1.0 / max(cps, 1) * _RITMO
    for caracter in texto:
        sys.stdout.write(caracter)
        sys.stdout.flush()
        # Los signos de puntuacion respiran un poco mas: es lo que separa
        # una maquina escribiendo de alguien hablando.
        time.sleep(espera * (6 if caracter in ".!?" else
                             3 if caracter in ",;:—" else 1))
    sys.stdout.write(fin)
    sys.stdout.flush()


def latido(veces=3, punto="."):
    """Puntos suspensivos con ritmo. Sirve para que un silencio se note."""
    if _RITMO <= 0:
        print(punto * veces)
        return
    for _ in range(veces):
        sys.stdout.write(punto)
        sys.stdout.flush()
        time.sleep(0.4 * _RITMO)
    sys.stdout.write("\n")
    sys.stdout.flush()


def regla(ancho=64, caracter="─"):
    print(caracter * ancho)


# --- eleccion --------------------------------------------------------------

def eleccion(pregunta, opciones, reintentos=8):
    """Elige entre opciones numeradas. Devuelve la CLAVE, nunca el indice.

    `opciones` es [(clave, texto), ...].

    Tres reglas:
      · Enter en vacio no elige. Volver a preguntar es respetar a quien duda.
      · Una entrada que no corresponde a ninguna opcion se declara y se repite.
      · Fin de entrada devuelve None. Nadie elige en nombre de nadie.
    """
    for _ in range(reintentos):
        despacio(pregunta)
        for i, (_clave, texto) in enumerate(opciones, 1):
            print(f"  {i}) {texto}")
        try:
            linea = input("  > ").strip()
        except EOFError:
            print()
            return None
        if not linea:
            continue
        if linea.isdigit() and 1 <= int(linea) <= len(opciones):
            return opciones[int(linea) - 1][0]
        for clave, _texto in opciones:
            if linea.lower() == clave.lower():
                return clave
        print(f"  '{linea}' no es una de las opciones. Elige un numero.")
    return None


# --- el paso 8 · la oferta de sellar --------------------------------------

def ofrecer_sello(disponible=True):
    """Ofrece cerrar la sesion sellando el estado de la memoria.

    Devuelve True solo si la persona lo pide y el mecanismo existe. Si no
    existe, se dice y se sigue: una oferta que no se puede cumplir se declara,
    no se esconde. Es el cierre natural de una sesion, y un mecanismo ofrecido
    donde toca se usa; uno que hay que recordar invocar, no.
    """
    regla()
    if not disponible:
        despacio("Sealing today's state is not available: the manifest "
                 "module is not here.")
        despacio("Your memory is safe anyway. Nothing was lost.")
        return False
    despacio("Before you go: I can seal what your memory looks like right now.")
    despacio("A seal proves nothing changed, without saying what it says.")
    respuesta = eleccion(
        "Seal today?",
        [("si", "Yes, seal it"),
         ("no", "Not now — I can do it any time")])
    if respuesta == "si":
        despacio("Sealing.")
        latido()
        return True
    despacio("Not sealed. The memory keeps growing.")
    return False


# --- despertar ------------------------------------------------------------

def despertar(estado_texto):
    """La entrada en escena. Se llama una vez, al arrancar.

    No inventa nada: recibe el texto de estado que produce la memoria y le
    pone cadencia. Si la memoria dice que esta vacia, esto no lo disimula.
    """
    regla()
    despacio("AURELIUS", cps=6)
    pausa(0.6)
    latido(3)
    pausa(0.3)
    despacio(estado_texto)
    regla()
