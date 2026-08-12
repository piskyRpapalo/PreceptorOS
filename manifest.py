#!/usr/bin/env python3
"""M2 · cierre · el manifiesto de la memoria y su firma.

sistema: MVP · solo biblioteca estandar. Se apoya en memory.py y NO lo modifica.

Que es un manifiesto: la lista de lo que habia en la memoria en un instante.
No guarda los recuerdos: guarda su HUELLA. Asi se puede demostrar que la
memoria no ha cambiado sin transcribir una sola palabra de lo que dice.

Cuatro reglas que este modulo no negocia:
  1. El hash cubre SOLO el cuerpo, entre marcadores. La firma va fuera, para
     que firmar no invalide el sello. Es la leccion aprendida con los
     expedientes: si el hash abarca la firma, firmar rompe el hash.
  2. Firmar NO muta la memoria. Ni un recuerdo, ni una fecha. Este modulo
     abre la base solo para leer.
  3. Sin nombre, se firma como NO_DATA y la firma sigue siendo valida. Una
     firma anonima es una firma; una firma inventada no.
  4. Verificar es RECALCULAR. Si la memoria avanzo, el manifiesto deja de
     cuadrar, y eso es correcto: significa que hay vida despues de la firma.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import memory as M

MARCA_INICIO = "<!-- BODY:START -->"
MARCA_FIN = "<!-- BODY:END -->"
CAMPOS_HUELLA = ("what", "why", "where_ref", "learned")


def _sha256(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _ahora():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _huella(fila):
    """Huella de un recuerdo: 16 hex sobre sus cuatro campos.

    Se unen con un separador que no puede aparecer en el texto de la persona,
    para que dos recuerdos distintos no puedan producir la misma huella por
    como caen las fronteras entre campos.
    """
    crudo = "\x1f".join(str(fila[k]) for k in CAMPOS_HUELLA)
    return _sha256(crudo)[:16]


# --- generar ---------------------------------------------------------------

def generar(c, cuando=None):
    """Manifiesto sin firmar, con el hash del cuerpo ya declarado.

    Solo lee. Cuenta los recuerdos ACTIVOS: un recuerdo archivado no forma
    parte del estado que se firma, y por eso archivar invalida el manifiesto.
    """
    filas = [dict(r) for r in c.execute(
        "select * from engrams where status='activo' order by id")]
    enlaces = c.execute("select count(*) from links").fetchone()[0]
    archivados = c.execute(
        "select count(*) from engrams where status='archivado'").fetchone()[0]
    huecos = M.recuento_huecos(c)

    # El encabezado va DENTRO de la region firmada. El motivo: si quedara
    # fuera, alguien podria falsificar los recuentos o la fecha sin romper el
    # hash, y el manifiesto afirmaria algo falso con sello valido. La region
    # existe para excluir la FIRMA, no para excluir lo que se afirma.
    dentro = [
        f"generated: {cuando or _ahora()}",
        f"memories: {len(filas)}   links: {enlaces}   archived: {archivados}",
        f"gaps: why {huecos['why']} · where {huecos['where_ref']} · "
        f"learned {huecos['learned']}",
        "",
    ]
    dentro += [f"{f['id']} · {_huella(f)}" for f in filas]
    cuerpo_txt = "\n".join(dentro)

    # El hash se calcula sobre lo que devuelve cuerpo(), NUNCA sobre el texto
    # que acabamos de construir. Parece lo mismo y no lo es: la extraccion
    # normaliza los saltos de linea del borde, asi que con memoria vacia el
    # cuerpo construido termina en linea en blanco y el extraido no. Una sola
    # definicion de "cuerpo" elimina toda esa clase de fallo de un golpe.
    provisional = "\n".join(["MEMORY MANIFEST", MARCA_INICIO, cuerpo_txt,
                             MARCA_FIN])
    return f"{provisional}\nsha256(body): {_sha256(cuerpo(provisional))}\n"


# --- cuerpo y hash ---------------------------------------------------------

def cuerpo(texto):
    """Lo que hay entre marcadores, sin los marcadores. Cadena vacia si no hay."""
    try:
        i = texto.index(MARCA_INICIO) + len(MARCA_INICIO)
        j = texto.index(MARCA_FIN)
    except ValueError:
        return ""
    return texto[i:j].strip("\n")


def hash_cuerpo(texto):
    return _sha256(cuerpo(texto))


def lineas_huella(texto):
    """Solo las lineas de huella del cuerpo, sin el encabezado.

    Existe para que nadie tenga que contar lineas del cuerpo a mano: el
    encabezado vive dentro de la region firmada, asi que "cuantas lineas
    tiene el cuerpo" no es lo mismo que "cuantos recuerdos hay".
    """
    import re as _re
    return [l for l in cuerpo(texto).splitlines()
            if _re.match(r"^\d+ · [0-9a-f]{16}$", l.strip())]


def hash_declarado(texto):
    for linea in texto.splitlines():
        if linea.startswith("sha256(body):"):
            return linea.split(":", 1)[1].strip()
    return None


def fecha_generacion(texto):
    """La fecha que el manifiesto declara. Se necesita para regenerar el mismo
    cuerpo al verificar: si se regenerase con la fecha de hoy, la vigencia
    fallaria siempre y el mecanismo no serviria para nada."""
    for linea in cuerpo(texto).splitlines():
        if linea.startswith("generated:"):
            return linea.split(":", 1)[1].strip()
    return None


# --- firmar ----------------------------------------------------------------

def firmar(texto, nombre=None, cuando=None):
    """Anade la firma DESPUES del marcador de fin y del hash declarado.

    No toca la base de datos. No recibe conexion a proposito: asi no puede
    escribir aunque alguien lo intente.
    """
    quien = nombre if nombre and str(nombre).strip() else M.AUSENTE
    linea_firma = (f"signed_by: {quien}\n"
                   f"signed_at: {cuando or _ahora()}\n")
    if not texto.endswith("\n"):
        texto += "\n"
    return texto + linea_firma


def firmante(texto):
    for linea in texto.splitlines():
        if linea.startswith("signed_by:"):
            return linea.split(":", 1)[1].strip()
    return None


# --- verificar -------------------------------------------------------------

def verificar(texto, c):
    """(ok, motivo). Dos comprobaciones, y las dos tienen que pasar.

    integridad · el hash declarado es el del cuerpo que el fichero lleva
    vigencia   · ese cuerpo es el que la memoria produce AHORA
    """
    declarado = hash_declarado(texto)
    if declarado is None:
        return False, "integridad: el manifiesto no declara hash del cuerpo"
    real = hash_cuerpo(texto)
    if declarado != real:
        return False, ("integridad: el hash declarado no coincide con el cuerpo. "
                       "El manifiesto fue alterado despues de generarse")

    actual = generar(c, cuando=fecha_generacion(texto))
    cuerpo_firmado = cuerpo(texto)
    cuerpo_actual = cuerpo(actual)
    if cuerpo_actual != cuerpo_firmado:
        # Se cuentan HUELLAS, no lineas del cuerpo: el encabezado tambien vive
        # dentro de la region firmada, y contarlo como recuerdos produciria un
        # motivo con cifras falsas. Un mensaje de error que miente es peor que
        # no dar detalle.
        n_antes = len(lineas_huella(texto))
        n_ahora = len(lineas_huella(actual))
        detalle = (f"{n_antes} recuerdos firmados, {n_ahora} ahora"
                   if n_antes != n_ahora
                   else "mismo numero de recuerdos, contenido distinto")
        return False, (f"vigencia: la memoria cambio desde la firma "
                       f"({detalle}). El manifiesto es historia, no estado")
    return True, "ok: integridad y vigencia"


# --- interfaz de linea de comandos ----------------------------------------

def main(argv):
    import argparse
    import os
    ap = argparse.ArgumentParser(description="Memory manifest · sign and verify")
    ap.add_argument("--db", default=os.path.expanduser("~/.aurelius/memory.db"))
    ap.add_argument("--sign", action="store_true", help="generate and sign")
    ap.add_argument("--verify", metavar="FILE", help="verify a manifest file")
    ap.add_argument("--out", metavar="FILE", help="write the manifest here")
    a = ap.parse_args(argv)

    est, rec = M.estado(a.db)
    if est == "SIN_ESQUEMA":
        print(M.mensaje_estado(est, rec))
        return 1

    if a.verify:
        with M.abrir(a.db) as c:
            ok, motivo = verificar(open(a.verify, encoding="utf-8").read(), c)
        print(("VALID   · " if ok else "INVALID · ") + motivo)
        return 0 if ok else 1

    with M.abrir(a.db) as c:
        nombre = None
        try:
            v = M.leer_perfil(c, "called_you")
            nombre = None if v == M.AUSENTE else v
        except AttributeError:
            nombre = None      # base sin tabla de perfil: se firma anonimo
        texto = generar(c)
        if a.sign:
            texto = firmar(texto, nombre=nombre)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(texto)
        print(f"written: {a.out}")
    else:
        print(texto, end="")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
