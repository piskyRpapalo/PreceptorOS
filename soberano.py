#!/usr/bin/env python3
"""Quien manda en ESTE aparato. Un codigo, no una contrasena.

sistema: MVP · solo biblioteca estandar.

QUE RESUELVE. El Soberano pidio «una cuenta admin en el Beelink, y una
estructura para entrar». La app no tiene cuentas y no las va a tener: su
identidad es una clave Ed25519 que el navegador genera y no puede exportar, y
la doctrina lo dice con todas las letras -- «no hay contrasena que olvidar ni
servidor que la guarde». Anadir una contrasena aqui seria estrenar justo lo que
el producto promete no tener.

ASI QUE NO SE CREA UNA CUENTA: SE DECLARA UNA. En este aparato hay exactamente
un Soberano, y es el codigo de vinculo de SU identidad -- el mismo que la web
ya deriva y ensena en el onboarding. Se declara una vez, queda en `profile`, y
a partir de ahi la app sabe cual de las identidades que la visitan es la de
quien manda.

EL CODIGO NO SE INVENTA AQUI. Es el mismo que calcula `onboarding.js` en el
navegador, byte a byte: SHA-256 de la clave publica, un caracter por byte, doce,
en tres grupos de cuatro. El alfabeto son 32 simbolos sin I, L, O ni U --se
confunden al teclear en un telefono-- y hay una prueba en la web que cruza las
dos implementaciones. Dos derivaciones distintas del mismo codigo en dos sitios
es como se rompen los vinculos sin que nadie se entere.

LO QUE ESTO ES Y LO QUE NO, dicho antes de que alguien se confie:

  ES     · una DECLARACION de propiedad en un aparato que ya es tuyo. Sirve
           para que la app sepa a quien obedecer cuando haya mas de una
           identidad, y para que la interfaz pueda ensenar lo que solo tu debes
           ver.

  NO ES  · autenticacion criptografica. El codigo se DERIVA de una clave
           publica, y una clave publica es publica: quien lo vea puede
           escribirlo. Verificar de verdad exige comprobar una FIRMA Ed25519, y
           eso no esta en la biblioteca estandar -- entra el dia que entre una
           dependencia, y ese dia es una decision del Soberano, no un detalle
           de implementacion.

  El modelo de amenaza que si cubre: tu maquina, tu red local, tu app. El que
  no: cualquiera con acceso a tu pantalla. Se dice aqui para que nadie lo
  descubra el dia que importe.
"""
from __future__ import annotations

import hashlib

# Los mismos 32 simbolos que `onboarding.js`. Sin I, L, O ni U: se confunden al
# teclear en un telefono, y este codigo se copia mirando una pantalla.
ALFABETO = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
CLAVE_PERFIL = "soberano"


def codigo_de(publica_hex):
    """El codigo de vinculo de una clave publica. Determinista y sin sal.

    La misma identidad da siempre el mismo codigo, aqui y en el navegador. Sin
    sal a proposito: una sal haria que el codigo de la web y el de la app no
    coincidieran, y entonces no vincularian nada.
    """
    try:
        crudo = bytes.fromhex(str(publica_hex or "").strip())
    except ValueError:
        return None
    if not crudo:
        return None
    h = hashlib.sha256(crudo).digest()
    s = "".join(ALFABETO[b % 32] for b in h[:12])
    return f"{s[:4]}-{s[4:8]}-{s[8:12]}"


def normalizar(codigo):
    """Mayusculas y con guiones, venga como venga.

    Quien lo copia de una pantalla lo escribe como puede: en minusculas, sin
    guiones, con un espacio en medio. Un codigo que solo vale escrito de una
    manera es un codigo que se teclea tres veces.
    """
    s = "".join(ch for ch in str(codigo or "").upper()
                if ch in ALFABETO)
    if len(s) != 12:
        return None
    return f"{s[:4]}-{s[4:8]}-{s[8:12]}"


def quien(c):
    """El codigo del Soberano declarado, o None si no hay ninguno.

    None NO es «no hay Soberano»: es «nadie lo ha declarado todavia». La
    diferencia importa porque la interfaz tiene que poder OFRECER declararlo, y
    para eso necesita distinguir el hueco del vacio.
    """
    import memory as M
    v = M.leer_perfil(c, CLAVE_PERFIL)
    return v if v and v != "NO_DATA" else None


def declarar(c, codigo):
    """Declara un codigo como el del Soberano de este aparato.

    SOLO SI NO HAY OTRO. Sobrescribir en silencio convertiria esto en un
    «ultimo que llega manda», que es lo contrario de lo que sirve. Para cambiar
    de Soberano hay que retirar el anterior a proposito -- un gesto, no un
    efecto colateral.

    Devuelve el codigo declarado, o None si no se pudo.
    """
    import memory as M
    n = normalizar(codigo)
    if n is None:
        return None
    ya = quien(c)
    if ya and ya != n:
        return None
    M.guardar_perfil(c, {CLAVE_PERFIL: n})
    return n


def retirar(c):
    """Deja el aparato sin Soberano. Explicito, y por eso existe."""
    import memory as M
    M.guardar_perfil(c, {CLAVE_PERFIL: "NO_DATA"})
    return True


def es_soberano(c, codigo):
    """Si ese codigo es el declarado aqui.

    Sin Soberano declarado devuelve False y no True: un aparato sin dueno no es
    un aparato de todos. Lo que hay que hacer entonces es declararlo, y la
    interfaz lo sabe porque `quien` devuelve None.
    """
    ya = quien(c)
    n = normalizar(codigo)
    return bool(ya and n and ya == n)
