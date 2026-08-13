#!/usr/bin/env python3
"""M2 · el Agua · la conversacion de recuperacion, en siete pasos.

sistema: MVP · solo biblioteca estandar. Sin red, sin dependencias.
Uso:  python3 aurelius.py [--db RUTA]
      python3 aurelius.py --view [--db RUTA]     solo mirar
      python3 aurelius.py --export [--db RUTA]   markdown redactado
      python3 aurelius.py --backup [FICHERO]     copia entera y comprobada

Cada pregunta abre el campo real que va a rellenar. Nada se pregunta en
abstracto, y ningun campo se rellena por la persona: si no sabe, NO_DATA.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memory as M
import tono as T

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
    T.despertar(M.mensaje_estado(est, rec))
    print("What I know about myself, without any memory at all:")
    print(f"  - a memory has 4 fields: what, why, where, learned")
    print(f"  - absence is written as {M.AUSENTE}, never left blank")
    print(f"  - my memory would live in: {ruta}")
    print(f"  - nothing leaves this machine unless you export it\n")
    if est == "SIN_ESQUEMA":
        if T.eleccion("Create my memory now?",
                      [("si", "Yes, create it"),
                       ("no", "No, not yet")]) != "si":
            print("\nNothing created. I keep no record of this session.")
            return False
        M.crear(ruta)
        print(f"\nCreated: {ruta}")
    return True


def paso0_presentacion(c):
    """Dos preguntas antes de la primera: donde estoy y como te llamo.

    Van antes del bucle a proposito. Preguntarlas despues seria pedirle a la
    persona que se presente a alguien que ya le ha sacado un recuerdo. Y no se
    guardan como recuerdos: son el marco, no lo que le paso a nadie.
    """
    perfil = M.leer_perfil(c)
    sabidas = {k: v for k, v in perfil.items() if v != M.AUSENTE}
    # Lo ya contestado no se vuelve a preguntar. Volver a pedirle el nombre a
    # quien ya lo dio es exactamente la amnesia que esto viene a arreglar, y
    # ademas pisaria su respuesta con la de hoy.
    if sabidas:
        print("\n" + " · ".join(f"{k}: {v}" for k, v in sabidas.items()))
    faltan = [k for k in M.CLAVES_PERFIL if perfil.get(k) == M.AUSENTE]
    if not faltan:
        return

    print("\n--- first, two questions that are not memories " + "-" * 12)
    print("I keep two things apart: who you are and where I am (this part),")
    print("and what you remember (everything after). Neither answer is")
    print(f"required. Press enter and it stays as {M.AUSENTE} — which is an")
    print("answer too: it says nobody told me, instead of me pretending.\n")

    preguntas = {
        "device": "Where am I?  (the machine I'm running on, in your words)  ",
        "name": "How should I call you?  ",
    }
    for clave in faltan:
        M.escribir_perfil(c, clave, preguntar(preguntas[clave]))

    print(f"\n{M.vista_perfil(c)}")
    if M.AUSENTE in M.vista_perfil(c):
        print(f"({M.AUSENTE} is not a blank cell: it is a question nobody")
        print(" answered. Nothing is lost by leaving it that way.)")


def paso2_primer_recuerdo(c):
    print("\n--- now a memory, one field at a time " + "-" * 20)
    print("A memory here is just something that happened to you and that you")
    print("decided was worth keeping. It does not have to be important.\n")
    print("  e.g.  the printer finally worked after I changed one cable")
    print("        I broke the database and got it back from a copy")
    print("        someone explained DNS to me and this time I got it\n")

    what = preguntar("So — what happened?  ", permitir_vacio=False)
    if what is None:
        print("Without a 'what' there is no memory. Nothing written,")
        print("and nothing wrong: come back when there is something.")
        return None

    print(f"\nThe next three can stay empty. Enter leaves them as {M.AUSENTE},")
    print("and a memory with declared gaps is still a memory — it is more")
    print("honest than one where I guessed the parts you did not tell me.\n")
    why = preguntar("Why does it matter to you?  (enter = NO_DATA)  ")
    where = preguntar("Is there a file, a photo, a note that backs it?  (enter = NO_DATA)  ")
    learned = preguntar("Did you learn anything you'd tell someone else?  (enter = for later)  ")
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


def paso8_sello(c, ruta):
    """Ofrece sellar el estado de la memoria. Opcional siempre."""
    try:
        import manifest as MF
    except ImportError:
        T.ofrecer_sello(disponible=False)
        return None
    if not T.ofrecer_sello(disponible=True):
        return None
    nombre = None
    try:
        # La clave del perfil es "name": M-D60 nombro asi lo que la propuesta
        # llamaba "called_you". Se aplica el equivalente, no el literal.
        v = M.leer_perfil(c, "name")
        nombre = None if v == M.AUSENTE else v
    except AttributeError:
        pass
    texto = MF.firmar(MF.generar(c), nombre=nombre)
    destino = os.path.join(os.path.dirname(os.path.abspath(ruta)),
                           "manifest-latest.txt")
    with open(destino, "w", encoding="utf-8") as fh:
        fh.write(texto)
    T.despacio(f"Sealed: {destino}")
    T.despacio("Keep a copy somewhere else: a seal next to what it certifies "
               "is lost with it.")
    return destino


def respaldo(ruta, destino=None):
    """Una copia que se puede llevar a otro disco, y que se ha leido entera.

    No se copia el .db con `cp`: con diario WAL eso puede producir un fichero
    valido y vacio. Se usa la copia de SQLite, que consolida el WAL, y se
    cuentan las filas EN LA COPIA antes de anunciarla.
    """
    try:
        destino, rec = M.respaldar(ruta, destino)
    except (FileNotFoundError, FileExistsError, M.RespaldoNoVerificado) as e:
        print(f"NOT BACKED UP · {e}", file=sys.stderr)
        return 2
    print(f"Backup: {destino}")
    print(f"  read back from the copy: {rec['engrams']} memories, "
          f"{rec['links']} links, {rec['profile']} profile entries")
    print("  one file, nothing left in a journal beside it")
    print("Keep it on another disk: a copy next to the original is lost with it.")
    return 0


def sesion(ruta):
    if not paso1_declaracion(ruta):
        return 0
    with M.abrir(ruta) as c:
        paso0_presentacion(c)
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
        paso8_sello(c, ruta)
        print("\nMission M2 complete: "
              + ("yes" if M.mision_completa(c) else "no — nothing was written"))
    return 0


def main():
    ap = argparse.ArgumentParser(description="Aurelius M2 · the Water")
    ap.add_argument("--db", default=RUTA_DEFECTO)
    ap.add_argument("--view", action="store_true")
    ap.add_argument("--export", action="store_true")
    ap.add_argument("--backup", nargs="?", const="", metavar="FILE",
                    help="verified copy of the whole memory, WAL included")
    a = ap.parse_args()

    est, rec = M.estado(a.db)
    if a.backup is not None:
        if est == "SIN_ESQUEMA":
            print(M.mensaje_estado(est, rec))
            return 1
        return respaldo(a.db, a.backup or None)
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
