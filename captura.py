#!/usr/bin/env python3
"""captura.py · el par completo, con su consentimiento. **Solo stdlib.**

POR QUÉ EXISTE
--------------
Medido el 2026-08-21: este producto no guardaba ni un solo turno. `salidas`
registra lo que el modelo dijo **sin la pregunta que lo provocó**, y media pieza
no es un par. Los dos turnos reales que un desconocido tecleó en un teléfono el
2026-08-20 se midieron, se citaron en un reporte y se perdieron, porque no había
dónde ponerlos.

Sin pares no hay datos, y sin datos ningún modelo afinado aprende una voz: son
3.609 tokens contra 5,9 M de parámetros, y eso ya se midió tres veces por tres
vías distintas. Esto es la tubería que lo arregla. **No entrena nada.**

LO QUE ESTO NO ES
-----------------
* **No es telemetría.** No abre un socket, no toca la red, y escribe en el mismo
  fichero de la persona donde ya vive todo lo demás. Nada sale de la máquina.
* **No es un permiso implícito.** Que un turno esté capturado no significa que
  pueda entrenar. `consent` nace en 0 y solo el carbono lo sube. Un par sin
  consentimiento es un recuerdo de la persona, no material de nadie.
* **No decide nada sobre el turno.** Se llama después de que la respuesta ya
  esté dada, y si falla, se calla: una captura rota jamás puede tumbar una
  conversación. El turno es del producto; esto es un cuaderno al margen.

CÓMO SE APAGA
-------------
`captura: no` en el perfil. Quien no quiera un cuaderno al margen no lo tiene, y
el resto del producto funciona igual.
"""
from __future__ import annotations

import sqlite3

ESQUEMA_TURNOS = """
create table if not exists turnos (
    id            integer primary key autoincrement,
    cuando        text not null default (datetime('now')),
    prompt        text not null,
    respuesta     text not null,
    modelo        text not null default 'NO_DATA',
    idioma        text not null default 'NO_DATA',
    consent       integer not null default 0,
    correccion    text,
    corregido     text,
    motivo        text not null default 'NO_DATA'
);
"""

# --- EL RASTRO DE LO QUE SE LE PUSO DELANTE (2026-09-08) -------------------
#
# LO QUE FALTABA PARA QUE «ES MEDIBLE» FUERA VERDAD. Un turno guardaba el
# prompt, la respuesta y el modelo -- y no guardaba QUE CONTEXTO viajo con
# ellos. Con eso, dos averias que piden arreglos OPUESTOS son
# indistinguibles desde la tabla:
#
#   a) el modelo ALUCINO: el recuerdo estaba delante y no lo uso.
#      -> se arregla con datos de entrenamiento.
#   b) la BUSQUEDA fallo: el recuerdo nunca llego.
#      -> se arregla con recuperacion, y ningun LoRA del mundo lo cura.
#
# Confundirlas es entrenar un modelo para tapar un fallo de consulta. Y es la
# clase de error que no se nota: el modelo mejora un poco --aprende a
# improvisar mejor sin el dato-- y la busqueda sigue rota.
#
# CUATRO COLUMNAS Y NINGUN TEXTO. No se guarda el bloque de contexto: se
# guarda su HUELLA -- que engramas viajaron, cuanto costaron, cuantos se
# quedaron fuera y si cabia todo. El contenido ya esta en `engrams`, y
# duplicarlo aqui seria tener dos copias del mismo recuerdo que envejecen por
# separado. Los ids bastan para reconstruir el turno exacto.
#
# Y VAN CON LOS METADATOS, NO CON EL TEXTO. `modelo` e `idioma` se guardan
# siempre; `prompt` y `respuesta` son lo que el consentimiento gobierna. Esto
# es de la misma familia que los primeros: describe lo que hizo la MAQUINA,
# no lo que dijo la persona. Son ids de su propia memoria local y no salen de
# su aparato.
RASTRO = (
    ("ctx_ids", "text not null default 'NO_DATA'"),
    ("ctx_tokens", "integer"),
    ("ctx_fuera", "integer"),
    ("ctx_completo", "integer"),
)

CLAVE_PERFIL = "captura"


def asegurar(c):
    """Crea la tabla si falta. Migración aditiva, como el resto de la casa.

    Una memoria creada antes de que esto existiera no tiene la tabla, y el día
    que se actualice el producto no debe encontrarse con un error: se le añade.

    Y las columnas del rastro se añaden UNA A UNA sobre la tabla que ya exista.
    Las memorias con turnos guardados desde antes del 2026-09-08 no las tienen,
    y no se les puede pedir que empiecen de cero: sus turnos viejos se quedan
    con `ctx_ids = 'NO_DATA'`, que es lo correcto -- no es que no viajara
    contexto, es que no se anotó. Ausente y vacío no son lo mismo, aquí
    tampoco.
    """
    c.executescript(ESQUEMA_TURNOS)
    ya = {d[1] for d in c.execute("pragma table_info(turnos)")}
    for nombre, tipo in RASTRO:
        if nombre not in ya:
            c.execute(f"alter table turnos add column {nombre} {tipo}")


def activa(perfil):
    """¿Quiere la persona este cuaderno? Por defecto sí; apagarlo es una palabra.

    Se lee del perfil y no de una constante: una preferencia que vive en el
    código es una preferencia del programador.
    """
    return str((perfil or {}).get(CLAVE_PERFIL, "si")).strip().lower() not in (
        "no", "0", "false", "off")


def registrar(c, prompt, respuesta, modelo="NO_DATA", idioma="NO_DATA",
              rastro=None):
    """Guarda el par y devuelve su id, o None si no se pudo.

    **Nunca levanta.** Se llama con la respuesta ya entregada a la persona: a
    esas alturas, un fallo aquí no puede convertirse en un fallo del turno. Se
    devuelve None y el producto sigue -- que es distinto de fingir que se
    guardó.

    `rastro` es el informe que devuelve `memory.recuperar`, tal cual. Se acepta
    OPCIONAL y por defecto None, y eso es deliberado: quien llame sin él sigue
    funcionando igual, y su turno queda con `ctx_ids='NO_DATA'` -- que dice la
    verdad, «no se anotó», y no finge un cero. Un parámetro obligatorio aquí
    habría roto a todo el que ya llama, y la forma de romperlo habría sido
    perder turnos.
    """
    if not (prompt and respuesta):
        return None
    try:
        asegurar(c)
        r = rastro or {}
        ids = ",".join(str(e["id"]) for e in r.get("engramas", [])) if r else ""
        cur = c.execute(
            "insert into turnos (prompt, respuesta, modelo, idioma, "
            "ctx_ids, ctx_tokens, ctx_fuera, ctx_completo) "
            "values (?, ?, ?, ?, ?, ?, ?, ?)",
            (prompt.strip(), respuesta.strip(), modelo or "NO_DATA",
             idioma or "NO_DATA",
             ids if ids else "NO_DATA",
             r.get("tokens"), r.get("fuera"),
             None if r.get("completo") is None else int(r["completo"])))
        return cur.lastrowid
    except Exception:
        # Se caza TODO a proposito, y no es pereza. El contrato de esta
        # funcion es que no levanta: se la llama con la respuesta ya en la
        # pantalla de la persona, y a esas alturas cualquier excepcion --de
        # sqlite, del disco, o de un objeto que no era el que se esperaba--
        # convertiria un cuaderno al margen en una conversacion rota. Se
        # devuelve None, que es decir "no se guardo", y eso es honesto.
        return None


def consentir(c, turno_id, si=True, motivo="NO_DATA"):
    """Sube o baja el consentimiento de un turno. Solo lo llama el carbono.

    Se puede retirar. Un consentimiento que no se puede retirar no es un
    consentimiento: es una firma.
    """
    asegurar(c)
    if motivo and motivo != "NO_DATA":
        cur = c.execute(
            "update turnos set consent = ?, motivo = ? where id = ?",
            (1 if si else 0, motivo, turno_id))
    else:
        # Sin motivo propio NO se toca el campo. Consentir y corregir son dos
        # actos distintos que compartian columna, y el defecto de este pisaba
        # el porque de aquel: un par de preferencia perdia su motivo justo al
        # ser autorizado. Un par sin motivo no se puede auditar despues.
        cur = c.execute("update turnos set consent = ? where id = ?",
                        (1 if si else 0, turno_id))
    return cur.rowcount == 1


def corregir(c, turno_id, texto, motivo="NO_DATA"):
    """La persona pone otra cosa en lugar de lo que dijo el modelo.

    Se guardan LAS DOS: lo que dijo el modelo sigue en `respuesta` y lo que la
    persona puso va a `correccion`. Ese par -- rechazado y elegido -- es
    exactamente lo que vale para entrenar preferencia, y borrar el original lo
    destruiría.

    Corregir NO consiente. Son dos actos distintos y se piden por separado.
    """
    if not texto or not texto.strip():
        return False
    asegurar(c)
    cur = c.execute(
        "update turnos set correccion = ?, motivo = ?, "
        "corregido = datetime('now') where id = ?",
        (texto.strip(), motivo, turno_id))
    return cur.rowcount == 1


def pares(c, solo_consentidos=True):
    """Los turnos, listos para el constructor del dataset.

    Un turno corregido sale como par de preferencia; uno sin corregir, como
    turno a secas. La forma es la que ya espera `datos/ESQUEMA.md`.
    """
    asegurar(c)
    sql = ("select id, cuando, prompt, respuesta, correccion, idioma, motivo "
           "from turnos")
    if solo_consentidos:
        sql += " where consent = 1"
    sql += " order by id"
    fuera = []
    for id_, cuando, prompt, resp, corr, idioma, motivo in c.execute(sql):
        if corr:
            fuera.append({"clase": "preferencia", "id": f"turno/{idioma}/{id_}",
                          "idioma": idioma, "prompt": prompt,
                          "elegido": corr, "rechazado": resp,
                          "motivo": motivo, "cuando": cuando})
        else:
            fuera.append({"clase": "turno", "id": f"turno/{idioma}/{id_}",
                          "idioma": idioma, "prompt": prompt,
                          "elegido": resp, "motivo": motivo, "cuando": cuando})
    return fuera


def recuento(c):
    """Cuántos hay y cuántos pueden entrenar. La diferencia es el dato."""
    asegurar(c)
    fila = c.execute(
        "select count(*), coalesce(sum(consent), 0), "
        "count(correccion) from turnos").fetchone()
    return {"turnos": fila[0], "consentidos": fila[1], "corregidos": fila[2]}
