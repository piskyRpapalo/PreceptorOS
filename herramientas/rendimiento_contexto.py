#!/usr/bin/env python3
"""Cuanto contexto viajo, y cuanto de el sobro.

POR QUE EXISTE. El techo de `herramientas.TECHO` son 456 tokens y esa cifra la
elegi yo. Es un juicio, no una medida. Con el rastro que `captura` guarda desde
el 2026-09-08 --`ctx_ids`, `ctx_tokens`, `ctx_fuera`, `ctx_completo`-- el techo
puede salir de datos: cual es el presupuesto por debajo del cual no se habria
perdido nada.

LO QUE SE MIDE EXACTO Y LO QUE NO, dicho antes de la primera cifra:

  EXACTO ...... cuantos tokens viajaron, cuantos engramas, cuantos se quedaron
                fuera, y cada cuanto el turno se contesto con parte de lo que
                habia. Son columnas; no hay nada que interpretar.

  HEURISTICO .. si un engrama que viajo se USO. Eso, sin un juez, no se puede
                saber: haria falta que alguien --persona o modelo-- leyera la
                respuesta y dijera de donde salio. Lo que se hace aqui es mirar
                si la respuesta comparte terminos largos con el engrama, y se
                marca como lo que es. Un numero heuristico con cara de medida
                es exactamente lo que este proyecto no publica.

Asi que la salida separa las dos cosas y la segunda va rotulada. La decision
del techo se toma con la primera; la segunda solo dice por donde mirar.

Uso:
    python3 herramientas/rendimiento_contexto.py [ruta.db]
"""
import os
import re
import sqlite3
import sys

# Palabras de seis letras o mas: las cortas --«el», «que», «para»-- salen en
# cualquier texto y harian que toda respuesta pareciera usar todo engrama.
# Seis y no cinco porque en castellano las de cinco todavia son muy comunes; es
# un corte declarado, no medido, y por eso lo de abajo es heuristico.
LARGA = re.compile(r"[a-záéíóúñü]{6,}", re.I)


def _terminos(texto):
    return {p.lower() for p in LARGA.findall(texto or "")}


def percentil(valores, p):
    """Sin numpy: el MVP es de biblioteca estandar y esto tambien."""
    if not valores:
        return None
    v = sorted(valores)
    i = min(len(v) - 1, max(0, int(round((p / 100) * (len(v) - 1)))))
    return v[i]


def main(ruta=None):
    ruta = ruta or os.path.expanduser("~/.preceptoros/memory.db")
    if not os.path.exists(ruta):
        print(f"NO_DATA · no hay memoria en {ruta}")
        return 1
    c = sqlite3.connect(ruta)
    c.row_factory = sqlite3.Row

    try:
        filas = list(c.execute(
            "select id, respuesta, ctx_ids, ctx_tokens, ctx_fuera, ctx_completo "
            "from turnos where ctx_ids != 'NO_DATA'"))
    except sqlite3.OperationalError:
        print("NO_DATA · esta memoria es anterior al rastro de contexto.")
        print("  Los turnos guardados desde el 2026-09-08 lo traen; los de antes no.")
        return 1

    total, = c.execute("select count(*) from turnos").fetchone()
    if not filas:
        # EL CASO DE HOY, y se dice entero en vez de imprimir ceros. Una tabla
        # de ceros se lee como «todo va bien»; esto se lee como lo que es.
        print(f"NO_DATA · {total} turnos guardados, NINGUNO con rastro de contexto.")
        print()
        print("  No es una averia: el rastro nacio el 2026-09-08 y solo lo llevan")
        print("  los turnos posteriores. Esta herramienta empieza a poder decir")
        print("  algo en cuanto la app registre turnos pasando `rastro=` a")
        print("  `captura.registrar`. Hasta entonces el techo sigue siendo un")
        print("  juicio (456 tokens) y aqui se dice, en vez de fingir una medida.")
        return 0

    # --- LO EXACTO ---------------------------------------------------------
    tokens = [f["ctx_tokens"] for f in filas if f["ctx_tokens"] is not None]
    parciales = sum(1 for f in filas if f["ctx_completo"] == 0)
    fuera = [f["ctx_fuera"] for f in filas if f["ctx_fuera"] is not None]

    print(f"MEDIDO · {len(filas)} turnos con rastro (de {total} guardados)\n")
    print(f"  tokens de contexto   p50 {percentil(tokens, 50)} · "
          f"p90 {percentil(tokens, 90)} · max {max(tokens) if tokens else None}")
    print(f"  turnos parciales     {parciales} de {len(filas)} "
          f"({parciales * 100 // len(filas)} %) se contestaron con parte de lo que habia")
    print(f"  engramas fuera       media {sum(fuera)/len(fuera):.2f}" if fuera
          else "  engramas fuera       NO_DATA")
    print()
    print("  LECTURA. Un porcentaje alto de parciales dice que el techo aprieta,")
    print("  no que el modelo falle. Si ademas la tasa de acierto de esos mismos")
    print("  turnos es baja (`captura.rendimiento`), el arreglo es presupuesto,")
    print("  no entrenamiento.")

    # --- LO HEURISTICO -----------------------------------------------------
    ids_c = {}
    for e in c.execute("select id, what, why, learned from engrams"):
        ids_c[e["id"]] = _terminos(" ".join(
            x for x in (e["what"], e["why"], e["learned"]) if x))

    viajaron = tocados = 0
    for f in filas:
        resp = _terminos(f["respuesta"])
        for sid in (f["ctx_ids"] or "").split(","):
            if not sid.strip().isdigit():
                continue
            t = ids_c.get(int(sid))
            if t is None:
                continue          # el engrama se archivo o se borro despues
            viajaron += 1
            if t & resp:
                tocados += 1

    print()
    print("HEURISTICO · no es una medida, es por donde mirar")
    if not viajaron:
        print("  NO_DATA · ningun engrama del rastro sigue en la tabla")
        return 0
    print(f"  {viajaron} engramas viajaron · {tocados} comparten algun termino")
    print(f"  largo con su respuesta ({tocados * 100 // viajaron} %).")
    print("  El resto PUEDE haber sido coste puro -- o puede haberse usado sin")
    print("  repetir ni una palabra, que es lo que hace un buen resumen. Por eso")
    print("  esto no decide nada solo: senala turnos para que los mire un juez.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
