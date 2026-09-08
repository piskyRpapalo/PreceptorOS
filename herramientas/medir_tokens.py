#!/usr/bin/env python3
"""Mide cuantos CARACTERES entran en un token, contra los modelos de este rack.

POR QUE EXISTE. `memory.recuperar()` corta el contexto por presupuesto de
TOKENS, y la memoria solo sabe contar caracteres: contar tokens de verdad exige
un tokenizador, y el MVP es de biblioteca estandar. La salida es una constante
--`CARACTERES_POR_TOKEN`-- y una constante sin procedencia es una suposicion con
cara de dato. Esto es la procedencia.

NO SE EJECUTA EN EL PRODUCTO. Vive en `herramientas/` y necesita el venv de la
Forja (`~/.venvs/aurelius-forja`), que trae `transformers`. La memoria no
importa nada de aqui: se lee el numero, se escribe en `memory.py` con su fecha,
y este fichero queda para volver a medirlo cuando cambien los modelos servidos.

SE MIDE SOBRE EL CORPUS REAL --los engramas vivos y el glosario del Ojo-- y no
sobre texto de ejemplo: la proporcion depende del idioma y del vocabulario, y
esta casa escribe en castellano con terminos tecnicos ingleses dentro.

SE TOMA EL PEOR DE LOS TRES, no la media. Un presupuesto que se pasa no avisa:
simplemente hace esperar. Subestimar tokens es gastar mas de lo que se dijo, asi
que el error se inclina hacia el lado que sobra contexto y no hacia el que
sobra espera.

Uso:
    ~/.venvs/aurelius-forja/bin/python herramientas/medir_tokens.py
"""
import json
import os
import sqlite3
import sys

# Los tres que este rack sirve de verdad. Si manana sirve otro, se anade aqui y
# se vuelve a medir: la constante es de los modelos, no del idioma.
MODELOS = {
    "Llama-3.2-3B": "unsloth/Llama-3.2-3B-Instruct",
    "Qwen3-4B": "Qwen/Qwen3-4B-Instruct-2507",
    "Mistral-7B": "mistralai/Mistral-7B-Instruct-v0.3",
}


def hojas(o):
    """Todo el texto de un JSON anidado, sin saber su forma."""
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from hojas(v)
    elif isinstance(o, list):
        for v in o:
            yield from hojas(v)


def corpus():
    textos = []
    bd = os.path.expanduser("~/.preceptoros/memory.db")
    if os.path.exists(bd):
        c = sqlite3.connect(bd)
        c.row_factory = sqlite3.Row
        for r in c.execute("select what, why, where_ref, learned from engrams"):
            textos += [x for x in (r["what"], r["why"], r["where_ref"],
                                   r["learned"]) if x]
    ojo = os.path.expanduser("~/p0x/Alejandria/ojo/glosario.json")
    if os.path.exists(ojo):
        with open(ojo, encoding="utf-8") as f:
            textos += [t for t in hojas(json.load(f)) if len(t) > 20]
    return textos


def main():
    try:
        from transformers import AutoTokenizer
    except ImportError:
        print("NO_DATA · falta `transformers`. Usa el venv de la Forja:")
        print("  ~/.venvs/aurelius-forja/bin/python herramientas/medir_tokens.py")
        return 1

    textos = corpus()
    if not textos:
        print("NO_DATA · no hay corpus que medir (ni engramas ni glosario)")
        return 1
    texto = "\n".join(textos)
    print(f"corpus real: {len(textos)} textos · {len(texto)} caracteres\n")

    peor = None
    for nombre, mid in MODELOS.items():
        try:
            tk = AutoTokenizer.from_pretrained(mid, local_files_only=True)
            n = len(tk(texto, add_special_tokens=False)["input_ids"])
            ratio = len(texto) / n
            print(f"  {nombre:14} {n:7} tokens · {ratio:5.2f} car/token")
            peor = ratio if peor is None else min(peor, ratio)
        except Exception as e:
            # Un modelo que no esta en cache es un hueco declarado, no un fallo:
            # la constante sale de los que SI se pudieron medir, y se dice cual
            # falto para que nadie lea el resultado como si fueran los tres.
            print(f"  {nombre:14} NO_DATA · {type(e).__name__}")

    if peor is None:
        print("\nNO_DATA · ningun tokenizador disponible en cache")
        return 1
    print(f"\n  el PEOR de los medidos: {peor:.2f} car/token")
    print(f"  -> CARACTERES_POR_TOKEN en memory.py: {peor:.1f} o menos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
