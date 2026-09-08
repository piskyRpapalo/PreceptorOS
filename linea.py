#!/usr/bin/env python3
"""linea.py · el registro que no se puede reescribir sin que se note.

**Solo biblioteca estandar.**

POR QUE ESTO SE PUEDE CONSTRUIR HOY Y LA FIRMA NO
--------------------------------------------------
El Sello Soberano lleva semanas bloqueado por la misma pared: la biblioteca
estandar no trae Ed25519. Pero al leer que exigen de verdad las normas, resulta
que esa pared solo cruza una parte del camino, y no la mas grande.

  · **AI Act art. 12** pide que el sistema registre eventos a lo largo de su
    vida y que ese registro permita TRAZABILIDAD. Pide un registro fiel; no
    pide que este firmado.
  · **ISO 27001 A.5.33** pide proteger los registros contra perdida,
    destruccion y FALSIFICACION. Falsificacion detectable, no imposible.
  · **ISO 42001 §8.3** pide poder demostrar que se sabia en cada momento.

Ninguna de las tres pide NO REPUDIO para el registro interno. El no repudio
--probar ante un tercero quien produjo algo, incluso contra su propio
interes-- hace falta cuando el artefacto SALE hacia alguien que no confia en
quien lo emite. Eso es el Sello Soberano, y ahi si hace falta una firma con
dueno.

La consecuencia practica, y es la que desatasca el trabajo: **lo que las normas
exigen del registro se cubre con integridad encadenada, y eso es `hashlib`.**
La dependencia criptografica deja de bloquear el noventa por ciento y se queda
donde de verdad pertenece: en el certificado que se entrega a un tercero.

QUE GARANTIZA ESTA PIEZA, DICHO SIN ADORNO
-------------------------------------------
Cada evento lleva la huella del anterior dentro de la suya. Cambiar un evento
viejo obliga a recalcular todos los que vinieron despues, y eso `verificar()`
lo ve. Lo que se obtiene es **evidencia de manipulacion**, no imposibilidad de
manipularla.

Y hay que decir el limite, porque un auditor lo va a preguntar: quien tenga
acceso de escritura al fichero puede reescribir la cadena ENTERA y volver a
encadenarla, y entonces cuadra. Contra eso solo hay dos remedios, y ninguno es
un hash: un ancla externa --publicar la ultima huella donde no se pueda
retocar-- o una firma con clave. El primero cuesta poco y ya se puede preparar;
el segundo espera a la decision del Soberano. Mientras tanto, esto detecta
exactamente lo que dice detectar: la manipulacion PARCIAL, que es la que ocurre
cuando alguien arregla una fila incomoda.

APPEND-ONLY DE VERDAD: NO SE PISA, SE RECTIFICA
------------------------------------------------
Aqui no hay `update` y no hay `delete`. Una correccion no cambia el evento
viejo: escribe uno nuevo que lo apunta. Una revocacion de consentimiento no
borra el consentimiento: anota que se retiro, y desde cuando. El estado es el
PLIEGUE de la linea, no una celda que alguien sobrescribio -- y por eso la
pregunta «que sabia el sistema el martes» tiene respuesta.
"""
from __future__ import annotations

import hashlib
import json

# El ancla legislativa de esta pieza vive en `normas.py`, no aqui: una cita
# repetida en cada modulo es una cita que en algun modulo se escribira distinto.
# `normas.citas("linea")` devuelve los articulos que juzgan este registro.
CONCEPTO = "linea"

ESQUEMA = """
create table if not exists eventos (
    id        integer primary key autoincrement,
    cuando    text not null default (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    tipo      text not null,
    sujeto    text not null,
    datos     text not null default 'NO_DATA',
    actor     text not null default 'NO_DATA',
    anterior  text not null,
    huella    text not null
);
create index if not exists eventos_cuando on eventos(cuando);
create index if not exists eventos_sujeto on eventos(sujeto);
"""

# Vocabulario cerrado, por la misma razon que el de `captura.TAREAS`: con tipo
# de texto libre, «que paso con el consentimiento» no tiene respuesta, tiene un
# `group by` sobre cadenas que alguien escribio a mano en cuatro sitios.
TIPOS = ("turno", "veredicto", "correccion", "consentimiento", "revocacion",
         "rectificacion", "importacion", "sello", "soberania")

# Quien lo hizo. Es el mismo vocabulario de jueces de `captura.juzgar`, y no es
# casualidad: un evento producido por el carbono y uno producido por un modelo
# no valen lo mismo ante un auditor, y mezclarlos daria una linea que no
# describe a ninguno de los dos.
ACTORES = ("carbono", "modelo", "determinista", "NO_DATA")

GENESIS = "GENESIS"


class LineaRota(Exception):
    """La cadena no cuadra. Se levanta con el id del primer evento que falla."""


class NoSePudoAnotar(Exception):
    """No se pudo escribir el evento.

    ESTA SI LEVANTA, y es la diferencia con `captura.registrar`, que nunca lo
    hace. Alli el contrato es correcto: se la llama con la respuesta ya en la
    pantalla de la persona, y un fallo del cuaderno no puede romper una
    conversacion.

    Aqui es al reves. Un evento de auditoria que no se escribe y no avisa deja
    al sistema funcionando COMO SI hubiera quedado registro, que es la unica
    forma de fallo que un registro de cumplimiento no puede permitirse. Quien
    llame decide si degrada o para; lo que no puede es no enterarse.
    """


def asegurar(c):
    """Crea la tabla si falta. Aditiva, como el resto de la casa."""
    c.executescript(ESQUEMA)


def _del_vocabulario(valor, vocabulario, defecto="NO_DATA"):
    v = str(valor or "").strip().lower()
    return v if v in vocabulario else defecto


def canonico(tipo, sujeto, datos, actor, cuando, anterior):
    """El texto exacto que se hashea. Determinista o no sirve de nada.

    `sort_keys` y separadores fijos porque dos diccionarios iguales tienen que
    dar la MISMA cadena: si el orden de las claves cambiara entre versiones de
    Python, toda la cadena vieja dejaria de verificar y pareceria manipulada.
    Un detector que grita cuando nadie ha tocado nada deja de leerse a la
    tercera vez.
    """
    cuerpo = {"tipo": tipo, "sujeto": sujeto, "datos": datos,
              "actor": actor, "cuando": cuando, "anterior": anterior}
    return json.dumps(cuerpo, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))


def _huella(*args):
    return hashlib.sha256(canonico(*args).encode("utf-8")).hexdigest()


def ultima(c):
    """(id, huella) del ultimo evento, o (None, GENESIS) si la linea esta vacia."""
    f = c.execute("select id, huella from eventos order by id desc limit 1").fetchone()
    return (f[0], f[1]) if f else (None, GENESIS)


def anotar(c, tipo, sujeto, datos=None, actor="NO_DATA"):
    """Escribe un evento al final de la linea. Devuelve (id, huella).

    `datos` viaja como JSON y se guarda tal cual se hashea: guardar una cosa y
    hashear otra es tener una huella que no verifica nada -- la misma leccion
    que `corregir.js` escribio para la firma del navegador.
    """
    t = _del_vocabulario(tipo, TIPOS)
    if t == "NO_DATA":
        raise NoSePudoAnotar(f"tipo desconocido: {tipo!r}. Los que hay: "
                             + ", ".join(TIPOS))
    if not str(sujeto or "").strip():
        raise NoSePudoAnotar("un evento sin sujeto no se puede consultar luego")
    a = _del_vocabulario(actor, ACTORES)
    try:
        asegurar(c)
        cuerpo = json.dumps(datos, sort_keys=True, ensure_ascii=False,
                            separators=(",", ":")) if datos is not None else "NO_DATA"
        cuando = c.execute(
            "select strftime('%Y-%m-%dT%H:%M:%fZ','now')").fetchone()[0]
        _, anterior = ultima(c)
        h = _huella(t, str(sujeto).strip(), cuerpo, a, cuando, anterior)
        cur = c.execute(
            "insert into eventos (cuando, tipo, sujeto, datos, actor, "
            "anterior, huella) values (?, ?, ?, ?, ?, ?, ?)",
            (cuando, t, str(sujeto).strip(), cuerpo, a, anterior, h))
        return cur.lastrowid, h
    except NoSePudoAnotar:
        raise
    except Exception as e:                                      # noqa: BLE001
        raise NoSePudoAnotar(str(e)) from e


def verificar(c):
    """Recorre la linea entera. Devuelve (ok, primer_id_roto, cuantos).

    No levanta: devuelve el veredicto. Un auditor pregunta «¿esta intacta?» y
    espera un si o un no con el sitio, no una excepcion que hay que capturar
    para poder contarla.
    """
    asegurar(c)
    anterior = GENESIS
    n = 0
    for f in c.execute("select id, cuando, tipo, sujeto, datos, actor, "
                       "anterior, huella from eventos order by id"):
        (eid, cuando, tipo, sujeto, datos, actor, ant_guardado, huella) = f
        if ant_guardado != anterior:
            return False, eid, n          # el eslabon no engancha con el previo
        if _huella(tipo, sujeto, datos, actor, cuando, anterior) != huella:
            return False, eid, n          # el contenido no da su propia huella
        anterior = huella
        n += 1
    return True, None, n


def tramo(c, desde=None, hasta=None, sujeto=None):
    """Los eventos de un intervalo. Es lo que dibuja la barra de tiempo.

    LA RESOLUCION ES EL MILISEGUNDO, y varios eventos seguidos comparten
    marca. No es un defecto y conviene decirlo antes de que alguien lo tome
    por uno: el ORDEN no lo da la fecha sino el `id`, que es monotono, y la
    cadena de huellas lo sella. La fecha sirve para recortar tramos, no para
    desempatar.

    Los extremos son ISO-8601 y se comparan como texto, que en ese formato es
    lo mismo que compararlos como fechas -- por eso `cuando` se escribe asi y
    no como epoch: una linea de tiempo que hay que convertir para leerla se
    consulta mal desde `sqlite3` a mano, y esa consulta a mano es exactamente
    lo que hara un auditor.
    """
    asegurar(c)
    sql = ["select * from eventos where 1=1"]
    args = []
    if desde:
        sql.append("and cuando >= ?"); args.append(desde)
    if hasta:
        sql.append("and cuando <= ?"); args.append(hasta)
    if sujeto:
        sql.append("and sujeto = ?"); args.append(sujeto)
    sql.append("order by id")
    return [dict(f) for f in c.execute(" ".join(sql), args)]


def pliegue(c, sujeto):
    """El estado ACTUAL de un sujeto, calculado plegando su linea.

    Aqui esta la diferencia entera entre esta tabla y una normal. El estado no
    se lee de una celda: se calcula recorriendo lo que paso. Por eso «que
    sabia el sistema el martes» tiene respuesta -- se pliega hasta el martes y
    ya esta.

    Devuelve el ultimo valor de cada clave vista, mas de donde salio: sin la
    procedencia, el pliegue seria otra celda mas y habriamos vuelto al
    principio.
    """
    estado, origen = {}, {}
    for e in tramo(c, sujeto=sujeto):
        if e["datos"] == "NO_DATA":
            continue
        try:
            d = json.loads(e["datos"])
        except ValueError:
            continue
        if not isinstance(d, dict):
            continue
        for k, v in d.items():
            estado[k] = v
            origen[k] = {"evento": e["id"], "cuando": e["cuando"],
                         "tipo": e["tipo"], "actor": e["actor"]}
    return {"estado": estado, "origen": origen}
