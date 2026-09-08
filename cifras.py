#!/usr/bin/env python3
"""cifras.py · la regla del NO_DATA aplicada a los numeros.

POR DONDE SE ESCAPO
-------------------
El 2026-09-07 los adaptadores de La Charla afirmaron que «el modelo base ocupa
unos 200 gigas» --son 4,4-- y que existe un equipo de desarrollo al que mandar
el feedback. La corrida entera devolvio codigo 0. Los sensores que habia miraban
la FORMA de la respuesta --identificadores, alfabeto, verbos de instalacion-- y
una cifra inventada tiene la forma perfecta.

Esa mitad se arreglo en la forja. Esta es la otra: la app corre modelos locales
con la misma familia de riesgo, y hasta hoy nada miraba sus numeros.

MARCA, NO CENSURA. Y ESA DISTINCION ES EL DISENO ENTERO
-------------------------------------------------------
`output_guard` BLOQUEA, y hace bien: un `rm -rf /` en una respuesta no tiene
lectura inocente. Una cifra sin respaldo si la tiene --puede ser correcta y
venir de donde este programa no mira--, asi que tirar la respuesta seria
cambiar un fallo por otro peor: la persona pierde una respuesta buena y encima
aprende a desconfiar del aviso.

Aqui se hace lo mismo que hace esta casa con todo lo que no sabe: se DECLARA.
La cifra se queda, con una linea al lado diciendo cual no se pudo contrastar.
Quien lee decide. Es literalmente el trato del NO_DATA, aplicado a los numeros.

QUE CUENTA COMO RESPALDO
------------------------
Lo que ENTRO en el turno --la pregunta y lo que la app sabe de esta maquina--,
no una lista de cifras permitidas. Una lista envejece y ademas es imposible:
las cifras legitimas de una conversacion son infinitas. Si la persona escribe
«tengo 16 GB», repetirle 16 GB es escuchar. Decir «200 gigas» sin que nadie los
haya mencionado, no.

La consecuencia honesta de esa eleccion: una cifra correcta que el modelo sepa
de su entrenamiento saldra marcada. Es el lado seguro del error -- marcar de mas
cuesta una linea de aviso; marcar de menos cuesta que una cifra inventada pase
por medida, que es como empezo todo esto.
"""
from __future__ import annotations

import re

# Las unidades van en sigla Y en palabra porque el modelo escribe «gigas» tan a
# menudo como «GB», y un patron que solo mire la sigla se pierde justo el caso
# real que dio origen a esto.
UNIDAD = (r"(?:GB|MB|TB|KB|GiB|MiB|GHz|MHz|mAh|tok(?:ens?)?/s|"
          r"gigas?|megas?|teras?|n[uú]cleos?|hilos?|par[áa]metros|"
          r"millones?|billones?|%|€|\$|W)")
# El cierre es `(?!\w)` y no `\b`, y la diferencia no es cosmetica: `\b` exige
# que haya un caracter de palabra en el borde, asi que detras de `%`, `€` o `$`
# --que no lo son-- nunca casaba. «usa el 90%» se colaba entero. Lo encontro la
# suite, no un usuario.
CANTIDAD = re.compile(r"(?<![\w/])(\d[\d.,]*)\s*(" + UNIDAD + r")(?!\w)", re.I)

# Las que significan lo mismo se comparan como lo mismo: si la pregunta dice
# «16 GB» y la respuesta «16 gigas», eso es respaldo, no invento.
FAMILIA = {"gb": "gb", "giga": "gb", "gigas": "gb", "gib": "gb",
           "mb": "mb", "mega": "mb", "megas": "mb", "mib": "mb",
           "tb": "tb", "tera": "tb", "teras": "tb",
           "nucleo": "nucleo", "nucleos": "nucleo",
           "núcleo": "nucleo", "núcleos": "nucleo",
           "hilo": "hilo", "hilos": "hilo"}


def _numero(crudo):
    """«4,4», «4.4», «1.000» y «1,000» dichos como un solo numero.

    La primera version quitaba todos los puntos y cambiaba las comas por
    puntos, o sea que leia «4.4 GB» como cuarenta y cuatro gigas. Un
    normalizador que cambia el valor no normaliza: fabrica un hallazgo donde no
    lo hay, y peor, se calla uno donde si lo hay.

    La regla es la de siempre en los dos idiomas: si hay dos separadores
    distintos, el ULTIMO es el decimal. Si solo hay uno y detras vienen
    exactamente tres cifras, es de millares --«1.000»--; en cualquier otro
    caso, decimal. «1.000» leido como mil y no como uno coma cero es la
    convencion que usan las dos grafias, y la ambiguedad que queda es la que
    tiene el texto original: aqui no se puede resolver mejor que en la cabeza
    de quien lo escribio.
    """
    n = crudo.strip().rstrip(".,")
    if "." in n and "," in n:
        decimal = "." if n.rindex(".") > n.rindex(",") else ","
        millares = "," if decimal == "." else "."
        n = n.replace(millares, "").replace(decimal, ".")
    elif "." in n or "," in n:
        sep = "." if "." in n else ","
        cabeza, _, cola = n.rpartition(sep)
        if len(cola) == 3 and cabeza:
            n = cabeza.replace(sep, "") + cola          # millares
        else:
            n = cabeza.replace(sep, "") + "." + cola
    # `0.50` y `0.5` son el mismo numero: se compara el VALOR, no la escritura.
    try:
        v = float(n)
        return str(int(v)) if v == int(v) else str(v)
    except ValueError:
        return n


def _normalizar(num, uni):
    u = uni.lower()
    return _numero(num), FAMILIA.get(u, u)


def cantidades(texto):
    """El conjunto de (numero, familia de unidad) que hay en un texto."""
    return {_normalizar(n, u) for n, u in CANTIDAD.findall(texto or "")}


def sin_respaldo(respuesta, *fuentes):
    """Las cantidades de la respuesta que no aparecen en ninguna fuente.

    Devuelve una lista ordenada de cadenas legibles, no el par crudo: lo que
    sale de aqui va a una linea que lee una persona, y «200 gb» se entiende
    donde `('200', 'gb')` no.
    """
    respaldo = set()
    for f in fuentes:
        respaldo |= cantidades(f)
    return sorted(f"{n} {u}" for n, u in cantidades(respuesta) - respaldo)


def aviso(sueltas, idioma="es"):
    """La linea que se pone al lado de la respuesta. Vacia si no hay nada.

    Se dice lo que se hizo --no se pudo contrastar-- y NO lo que no se sabe
    --que sea falso--. Un aviso que diga «esta cifra es falsa» estaria
    afirmando algo que este programa no ha comprobado, y seria exactamente el
    mismo defecto que denuncia.
    """
    if not sueltas:
        return ""
    lista = ", ".join(sueltas)
    if idioma == "en":
        return (f"[no backing: {lista}] — these figures did not come from your "
                "question nor from what this app knows about your machine. "
                "They may be right; nobody here checked them.")
    return (f"[sin respaldo: {lista}] — esas cifras no salen de tu pregunta ni "
            "de lo que esta app sabe de tu maquina. Pueden ser correctas; aqui "
            "nadie las ha comprobado.")
