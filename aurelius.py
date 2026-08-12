#!/usr/bin/env python3
"""M2 · el Agua · la conversacion de recuperacion, en siete pasos.

sistema: MVP · solo biblioteca estandar. Sin red, sin dependencias.
Uso:  python3 aurelius.py [--db RUTA]
      python3 aurelius.py --view [--db RUTA]     solo mirar
      python3 aurelius.py --export [--db RUTA]   markdown redactado

Cada pregunta abre el campo real que va a rellenar. Nada se pregunta en
abstracto, y ningun campo se rellena por la persona: si no sabe, NO_DATA.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memory as M

RUTA_DEFECTO = os.path.expanduser("~/.aurelius/memory.db")


# --- guardrails: se inyecta, no se copia ----------------------------------

def cargar_redactor():
    """Busca el guardrails del producto. Si no esta, la frontera queda cerrada.
    No se copia ninguna regla desde otro arbol: se comparten patrones, no
    lexicos, y aqui ni siquiera hace falta conocerlos."""
    try:
        from guardrails import redactar_salida  # type: ignore
        return redactar_salida
    except Exception:
        return None


def preguntar(texto, permitir_vacio=True):
    try:
        r = input(texto)
    except EOFError:
        return ""
    r = r.strip()
    if r == "" and not permitir_vacio:
        return None
    return r


def si_no(texto):
    r = preguntar(f"{texto} [y/N] ").lower()
    return r in ("y", "yes", "s", "si", "sí")


# --- los siete pasos -------------------------------------------------------

def paso1_declaracion(ruta):
    est, rec = M.estado(ruta)
    print(f"\n{M.mensaje_estado(est, rec)}\n")
    print("What I know about myself, without any memory at all:")
    print(f"  - a memory has 4 fields: what, why, where, learned")
    print(f"  - absence is written as {M.AUSENTE}, never left blank")
    print(f"  - my memory would live in: {ruta}")
    print(f"  - nothing leaves this machine unless you export it\n")
    if est == "SIN_ESQUEMA":
        if not si_no("Create my memory now?"):
            print("\nNothing created. I keep no record of this session.")
            return False
        M.crear(ruta)
        print(f"\nCreated: {ruta}")
    return True


def paso2_primer_recuerdo(c):
    print("\n--- a memory, field by field " + "-" * 30)
    what = preguntar("what happened / what is it?  ", permitir_vacio=False)
    if what is None:
        print("Without a 'what' there is no memory. Nothing written.")
        return None
    why = preguntar("why does it matter?  (enter = NO_DATA)  ")
    where = preguntar("where is the thing that backs it?  (enter = NO_DATA)  ")
    learned = preguntar("what did you learn?  (enter = leave for later)  ")
    fila = M.escribir_engrama(c, what=what, why=why or None,
                              where_ref=where or None, learned=learned or "")
    print("\nSaved, exactly as you wrote it:")
    for k in ("id", "what", "why", "where_ref", "learned"):
        print(f"  {k:<10} {fila[k] if fila[k] != '' else '(empty, for later)'}")
    return fila


def paso5_enlace(c):
    filas = [dict(r) for r in c.execute(
        "select id, what from engrams where status='activo' order by id")]
    if len(filas) < 2:
        return
    if not si_no("\nAre two of these related?"):
        return
    for f in filas:
        print(f"  {f['id']}: {f['what'][:60]}")
    a = preguntar("from id:  ")
    b = preguntar("to id:  ")
    label = preguntar("in your own words, how?  (enter = NO_DATA)  ")
    if a.isdigit() and b.isdigit():
        M.escribir_enlace(c, int(a), int(b), label or None)
        print("Link saved.")


def paso6_vista(c):
    print("\n=== TABLE " + "=" * 52)
    print(M.vista_tabla(c))
    print("\n=== TREE " + "=" * 53)
    print(M.vista_arbol(c))
    print("\n=== COUNT " + "=" * 52)
    print(M.vista_recuento(c))


def paso7_cierre(c, ruta):
    print("\n--- honest closing " + "-" * 40)
    r = M.recuento_huecos(c)
    print(f"I have {r['engrams']} memories and {r['total']} declared gaps.")
    print(f"They live in {ruta}. You can copy that file and take it with you.")
    red = cargar_redactor()
    print("Redaction at the border: "
          + ("ready" if red else "NOT AVAILABLE — export is blocked"))
    resp = preguntar("\nWhich piece do you want to understand first?  ")
    if resp:
        M.escribir_engrama(c, what=resp, why="the next thing I want to learn",
                           origin="intencion")
        print("Saved as an intention. It orients the next mission.")


def sesion(ruta):
    if not paso1_declaracion(ruta):
        return 0
    with M.abrir(ruta) as c:
        while True:
            paso2_primer_recuerdo(c)
            n = c.execute("select count(*) from engrams "
                          "where status='activo'").fetchone()[0]
            print(f"\n{n} memories. Three is a good start — not a requirement.")
            if not si_no("Add another?"):
                break
        paso5_enlace(c)
        paso6_vista(c)
        paso7_cierre(c, ruta)
        print("\nMission M2 complete: "
              + ("yes" if M.mision_completa(c) else "no — nothing was written"))
    return 0


def main():
    ap = argparse.ArgumentParser(description="Aurelius M2 · the Water")
    ap.add_argument("--db", default=RUTA_DEFECTO)
    ap.add_argument("--view", action="store_true")
    ap.add_argument("--export", action="store_true")
    a = ap.parse_args()

    est, rec = M.estado(a.db)
    if a.view or a.export:
        if est == "SIN_ESQUEMA":
            print(M.mensaje_estado(est, rec))
            return 1
        with M.abrir(a.db) as c:
            if a.view:
                paso6_vista(c)
                return 0
            try:
                texto, hallazgos = M.exportar(c, redactor=cargar_redactor())
            except M.FronteraSinFiltro as e:
                print(f"BLOCKED · {e}", file=sys.stderr)
                return 2
            print(texto)
            total = sum(h["count"] for h in hallazgos)
            detalle = ", ".join(
                "{}x{}".format(h["policy"], h["count"]) for h in hallazgos)
            print("\n<!-- redacted: {} items · {} -->".format(
                total, detalle or "none"))
            return 0
    return sesion(a.db)


if __name__ == "__main__":
    sys.exit(main())
