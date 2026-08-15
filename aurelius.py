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
import textos as TX
import tono as T

import casa as _casa
import descarga as _descarga
import estado as _estado

RUTA_DEFECTO = os.path.expanduser("~/.aurelius/memory.db")

# --- catálogo de piezas · URLs y hashes pendientes de confirmación ---
CEREBRO = _descarga.Pieza(
    nombre="Qwen3-4B-Instruct-2507 Q4_K_M",
    url="https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507-GGUF/resolve/main/qwen3-4b-instruct-2507-Q4_K_M.gguf",
    sha256="PENDIENTE_CONFIRMAR_POR_EL_SOBERANO",
    bytes=None,
    licencia="Apache-2.0",
    destino="modelos/qwen3-4b-instruct-2507-Q4_K_M.gguf",
)

VOZ = _descarga.Pieza(
    nombre="Piper es_ES-sharvard speaker_0",
    url="https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx",
    sha256="PENDIENTE_CONFIRMAR_POR_EL_SOBERANO",
    bytes=None,
    licencia="MIT",
    destino="voz/es_ES-sharvard-medium.onnx",
)


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


def tx(idioma, clave, **kw):
    return TX.texto(idioma, clave, **kw)


def elegir(pregunta, opciones, idioma=TX.DEFECTO, ayuda=None, rechazo=None,
           reintentos=8):
    """Pregunta numerada. Devuelve la CLAVE elegida, nunca el indice.

    Se aceptan numeros, y solo numeros. La version anterior tambien admitia la
    clave interna ("si"), lo que producia una pregunta que aceptaba "si" y
    rechazaba "yes" sin decir por que: el carbono escribio "yes" tres veces
    antes de entender que se esperaba un "1". Una gramatica sola y dicha en el
    enunciado vale mas que dos gramaticas y ninguna explicada.

    Tres reglas que vienen de `tono` y no se tocan:
      · Enter en vacio no elige. Volver a preguntar es respetar a quien duda.
      · Lo que no es una opcion se declara Y se dice que numeros valen.
      · Fin de entrada devuelve None. Nadie elige en nombre de nadie.
    """
    numeros = TX.lista_numeros(len(opciones), idioma)
    for _ in range(reintentos):
        T.despacio(pregunta)
        for i, (_clave, texto) in enumerate(opciones, 1):
            print(f"  {i}) {texto}")
        if ayuda:
            print(f"  ({ayuda})")
        try:
            linea = input("  > ").strip()
        except EOFError:
            print()
            return None
        if not linea:
            continue
        if linea.isdigit() and 1 <= int(linea) <= len(opciones):
            return opciones[int(linea) - 1][0]
        print("  " + ((rechazo or tx(idioma, "rechazo",
                                     entrada="{entrada}", numeros=numeros))
                      .format(entrada=linea)))
    return None


# --- paso 0 · el idioma, antes que nada -----------------------------------

def paso_idioma(ruta):
    """La primera pregunta de la sesion (D74). Devuelve el codigo o None.

    Se hace en los dos idiomas porque todavia no hay uno elegido, y va antes
    de la de crear: preguntar en un idioma que nadie eligio ya es elegirlo.
    Un idioma ya contestado no se vuelve a preguntar — misma regla que el
    resto del perfil.
    """
    est, _ = M.estado(ruta)
    if est != "SIN_ESQUEMA":
        with M.abrir(ruta) as c:
            guardado = M.leer_perfil(c, "language")
        if guardado != M.AUSENTE:
            return guardado
    return elegir(TX.PREGUNTA_IDIOMA, TX.IDIOMAS, ayuda=TX.AYUDA_IDIOMA,
                  rechazo=TX.RECHAZO_IDIOMA)


def recordar_idioma(c, idioma):
    """Guarda lo elegido. No elegir no se guarda: se queda en NO_DATA.

    Escribir "en" porque nadie contesto convertiria una ausencia en una
    respuesta, y el perfil dejaria de distinguir a quien eligio ingles de
    quien no eligio nada.
    """
    if idioma:
        M.escribir_perfil(c, "language", idioma)


# --- los siete pasos -------------------------------------------------------


def ritual(c, idioma=TX.DEFECTO):
    """Primer contacto. Escribe en profile (memoria SQLite), no en estado.json."""
    print(tx(idioma, "final"))
    nombre = preguntar("¿Cómo te llamas? (Enter para NO_DATA) ")
    if nombre:
        M.escribir_perfil(c, "name", nombre)
    lengua = elegir("Idioma / Language", [("es", "español"), ("en", "english")],
                    idioma, ayuda="Escribe 1 o 2")
    if lengua:
        M.escribir_perfil(c, "language", lengua)
    ritmo = preguntar("Ritmo de respuesta (0-9, Enter para NO_DATA) ")
    if ritmo and ritmo.isdigit():
        M.escribir_perfil(c, "ritmo", ritmo)
    print("Ritual completado. Tu perfil está en la memoria.")


def paso1_declaracion(ruta, idioma=TX.DEFECTO):
    est, rec = M.estado(ruta)
    T.despertar(M.mensaje_estado(est, rec, idioma))
    print(tx(idioma, "sabe_de_mi"))
    print(tx(idioma, "bullet_campos"))
    print(tx(idioma, "bullet_ausencia", ausente=M.AUSENTE))
    print(tx(idioma, "bullet_vive", ruta=ruta))
    print(tx(idioma, "bullet_frontera") + "\n")
    if est == "SIN_ESQUEMA":
        if elegir(tx(idioma, "crear_pregunta"),
                  [("si", tx(idioma, "crear_si")),
                   ("no", tx(idioma, "crear_no"))], idioma) != "si":
            print(tx(idioma, "nada_creado"))
            return False
        M.crear(ruta)
        print(tx(idioma, "creado", ruta=ruta))
    return True


def paso0_presentacion(c, idioma=TX.DEFECTO):
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
    # El idioma es del perfil pero no se pregunta aqui: ya se contesto antes de
    # que existiera la base. Se filtra por las preguntas que este paso sabe
    # hacer, no por la lista de claves, para que anadir una clave manana no
    # reviente este bucle con un KeyError.
    preguntas = {
        "device": tx(idioma, "perfil_device"),
        "name": tx(idioma, "perfil_name"),
    }
    faltan = [k for k in M.CLAVES_PERFIL
              if perfil.get(k) == M.AUSENTE and k in preguntas]
    if not faltan:
        return

    print(tx(idioma, "perfil_cabecera") + "-" * 12)
    print(tx(idioma, "perfil_intro", ausente=M.AUSENTE))

    for clave in faltan:
        M.escribir_perfil(c, clave, preguntar(preguntas[clave]))

    print(f"\n{M.vista_perfil(c)}")
    if M.AUSENTE in M.vista_perfil(c):
        print(tx(idioma, "perfil_nota", ausente=M.AUSENTE))


def paso2_primer_recuerdo(c, idioma=TX.DEFECTO):
    print(tx(idioma, "recuerdo_cabecera") + "-" * 20)
    print(tx(idioma, "recuerdo_intro"))
    print(tx(idioma, "recuerdo_ejemplos"))

    what = preguntar(tx(idioma, "recuerdo_que"), permitir_vacio=False)
    if what is None:
        print(tx(idioma, "recuerdo_sin_que"))
        return None

    print(tx(idioma, "recuerdo_opcionales", ausente=M.AUSENTE))
    why = preguntar(tx(idioma, "recuerdo_porque", ausente=M.AUSENTE))
    where = preguntar(tx(idioma, "recuerdo_donde", ausente=M.AUSENTE))
    learned = preguntar(tx(idioma, "recuerdo_aprendido"))
    fila = M.escribir_engrama(c, what=what, why=why or None,
                              where_ref=where or None, learned=learned or "")
    print(tx(idioma, "recuerdo_guardado"))
    vacio = tx(idioma, "recuerdo_vacio")
    for k in ("id", "what", "why", "where_ref", "learned"):
        print(f"  {k:<10} {fila[k] if fila[k] != '' else vacio}")
    return fila


def paso5_enlace(c, idioma=TX.DEFECTO):
    filas = [dict(r) for r in c.execute(
        "select id, what from engrams where status='activo' order by id")]
    if len(filas) < 2:
        return
    if elegir(tx(idioma, "enlace_pregunta"),
              [("si", tx(idioma, "enlace_si")),
               ("no", tx(idioma, "enlace_no"))], idioma) != "si":
        return
    for f in filas:
        print(f"  {f['id']}: {f['what'][:60]}")
    a = preguntar(tx(idioma, "enlace_desde"))
    b = preguntar(tx(idioma, "enlace_hasta"))
    label = preguntar(tx(idioma, "enlace_como", ausente=M.AUSENTE))
    if a.isdigit() and b.isdigit():
        M.escribir_enlace(c, int(a), int(b), label or None)
        print(tx(idioma, "enlace_guardado"))


def paso6_vista(c, idioma=TX.DEFECTO):
    print(tx(idioma, "vista_tabla") + "=" * 52)
    print(M.vista_tabla(c))
    print(tx(idioma, "vista_arbol") + "=" * 53)
    print(M.vista_arbol(c))
    print(tx(idioma, "vista_recuento") + "=" * 52)
    print(M.vista_recuento(c))


def paso7_cierre(c, ruta, idioma=TX.DEFECTO):
    print(tx(idioma, "cierre_cabecera") + "-" * 40)
    r = M.recuento_huecos(c)
    print(tx(idioma, "cierre_recuento",
             engrams=r["engrams"], huecos=r["total"],
             nombre_r=TX.plural(idioma, r["engrams"], "palabra_recuerdo",
                                "palabra_recuerdos"),
             nombre_h=TX.plural(idioma, r["total"], "palabra_hueco",
                                "palabra_huecos")))
    print(tx(idioma, "cierre_viven", ruta=ruta))
    red = cargar_redactor()
    print(tx(idioma, "cierre_frontera")
          + tx(idioma, "cierre_frontera_ok" if red else "cierre_frontera_no"))
    resp = preguntar(tx(idioma, "cierre_pregunta"))
    if resp:
        M.escribir_engrama(c, what=resp,
                           why=tx(idioma, "cierre_intencion_why"),
                           origin="intencion")
        print(tx(idioma, "cierre_intencion"))


def ofrecer_sello(idioma=TX.DEFECTO, disponible=True):
    """La oferta de sellar, en el idioma de la sesion.

    Es `tono.ofrecer_sello` con el texto traido al producto. La cadencia sigue
    siendo de `tono` —regla, despacio, latido— y `tono.py` no se toca: su texto
    estaba en un solo idioma porque cuando se escribio el producto hablaba uno.
    El tono es CUANDO se dice algo; QUE se dice es del producto, y desde D74 el
    producto lo dice en dos idiomas.

    Devuelve True solo si la persona lo pide y el mecanismo existe. Si no
    existe, se dice y se sigue: una oferta que no se puede cumplir se declara.
    """
    T.regla()
    if not disponible:
        T.despacio(tx(idioma, "sello_no_hay"))
        T.despacio(tx(idioma, "sello_no_hay_2"))
        return False
    T.despacio(tx(idioma, "sello_intro"))
    T.despacio(tx(idioma, "sello_intro_2"))
    if elegir(tx(idioma, "sello_pregunta"),
              [("si", tx(idioma, "sello_si")),
               ("no", tx(idioma, "sello_no"))], idioma) == "si":
        T.despacio(tx(idioma, "sello_sellando"))
        T.latido()
        return True
    T.despacio(tx(idioma, "sello_no_sellado"))
    return False


def paso8_sello(c, ruta, idioma=TX.DEFECTO):
    """Ofrece sellar el estado de la memoria. Opcional siempre."""
    try:
        import manifest as MF
    except ImportError:
        ofrecer_sello(idioma, disponible=False)
        return None
    if not ofrecer_sello(idioma, disponible=True):
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
    T.despacio(tx(idioma, "sello_escrito", destino=destino))
    T.despacio(tx(idioma, "sello_copia"))
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



def arranque(ruta):
    """Flujo de arranque del Preceptor §6. Se ejecuta ANTES de sesion()."""
    # 1. Casa
    try:
        _casa.asegurar()
    except _casa.CasaInaccesible as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # 2. Reconciliar banderas con el disco
    banderas, mentian = _estado.reconciliar({
        "cerebro_descargado": lambda: _descarga.presente(CEREBRO),
        "voz_descargada": lambda: _descarga.presente(VOZ),
    })
    if mentian:
        print(f"Tenía anotado que {', '.join(mentian)} estaba(n) y no lo(s) encuentro.")

    # 3. Abrir memoria para el ritual (perfil vive en SQLite)
    with M.abrir(ruta) as c:
        if not banderas["ritual_firmado"]:
            ritual(c)
            _estado.fijar("ritual_firmado", True)
            banderas["ritual_firmado"] = True

    # 4. Cerebro
    if not banderas["cerebro_descargado"]:
        _descarga.anunciar(CEREBRO)
        respuesta = preguntar("¿Descargar el cerebro? [s/N] ", permitir_vacio=False)
        if respuesta and respuesta.lower() in ("s", "si", "sí", "y", "yes"):
            try:
                _descarga.descargar(CEREBRO)
                _estado.fijar("cerebro_descargado", True)
                banderas["cerebro_descargado"] = True
            except _descarga.DescargaFallida as e:
                print(f"Descarga fallida: {e}")
        else:
            print("Modo solo memoria: sin cerebro, pregunto y recuerdo.")

    # 5. Voz
    if not banderas["voz_descargada"]:
        _descarga.anunciar(VOZ)
        respuesta = preguntar("¿Descargar la voz? [s/N] ", permitir_vacio=False)
        if respuesta and respuesta.lower() in ("s", "si", "sí", "y", "yes"):
            try:
                _descarga.descargar(VOZ)
                _estado.fijar("voz_descargada", True)
                banderas["voz_descargada"] = True
            except _descarga.DescargaFallida as e:
                print(f"Descarga fallida: {e}")
        else:
            print("Sin voz: escribiré en vez de hablar.")

    return banderas


def sesion(ruta):
    # El idioma es lo primero que se pregunta y lo primero que se sabe: todo lo
    # que viene despues se dice en el, incluido el mensaje de estado.
    idioma = paso_idioma(ruta)
    lengua = TX.normalizar(idioma)
    if not paso1_declaracion(ruta, lengua):
        return 0
    with M.abrir(ruta) as c:
        recordar_idioma(c, idioma)
        paso0_presentacion(c, lengua)
        while True:
            paso2_primer_recuerdo(c, lengua)
            n = c.execute("select count(*) from engrams "
                          "where status='activo'").fetchone()[0]
            print(tx(lengua, "bucle_recuento", n=n,
                     nombre_r=TX.plural(lengua, n, "palabra_recuerdo",
                                        "palabra_recuerdos")))
            if elegir(tx(lengua, "otro_pregunta"),
                      [("si", tx(lengua, "otro_si")),
                       ("no", tx(lengua, "otro_no"))], lengua) != "si":
                break
        paso5_enlace(c, lengua)
        paso6_vista(c, lengua)
        paso7_cierre(c, ruta, lengua)
        paso8_sello(c, ruta, lengua)
        print(tx(lengua, "final")
              + tx(lengua, "final_si" if M.mision_completa(c) else "final_no"))
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
                # Mirar no es una sesion, asi que aqui no se pregunta nada: se
                # usa el idioma que la persona ya eligio. Si no eligio ninguno,
                # NO_DATA cae al de por defecto sin decir una palabra.
                paso6_vista(c, TX.normalizar(M.leer_perfil(c, "language")))
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
    banderas = arranque(a.db)
    return sesion(a.db)


if __name__ == "__main__":
    sys.exit(main())
