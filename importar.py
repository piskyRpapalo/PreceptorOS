#!/usr/bin/env python3
"""El puente de vuelta: lo que se hizo en la web, dentro de TU memoria.

EL HUECO QUE CIERRA
-------------------
La web ya sabe hablar el idioma de esta app. `corregir.js` escribe sus campos
con los nombres de `captura.turnos` --prompt, respuesta, correccion, corregido,
modelo, idioma, motivo, consent-- uno a uno y a proposito, para que no hiciera
falta un traductor en medio. Pero el puente iba en UN SOLO SENTIDO: la persona
corregia respuestas en el navegador, se llevaba el paquete... y al llegar aqui
no habia donde meterlo. Quedaba en el portapapeles.

Esta es la pieza que convierte «probe la web» en «tengo mi memoria».

LO QUE NO HACE, Y ES LA MITAD DEL DISENO
----------------------------------------
**No verifica la firma, y lo dice en vez de sugerir lo contrario.** El paquete
viaja firmado con Ed25519, y la biblioteca estandar de Python no trae Ed25519
--la misma pared contra la que ya chocaron `huella.py` y `soberano.py`, y por
la misma razon se resolvieron diciendo la verdad en vez de renombrandola--. La
firma se GUARDA tal cual, entera, para el dia que entre una dependencia y se
pueda comprobar hacia atras. Hasta ese dia, `firma_ok` vale NO_DATA: ni 0 ni 1.
Un cero diria «se comprobo y fallo»; un uno mentiria. NO_DATA dice lo unico
cierto: nadie lo ha comprobado.

**No inventa la tarea, y desde el 2026-09-08 tampoco hace falta.** El paquete
de la web ahora la trae: los ocho comandos de `servicios.json` son los mismos
ocho de `captura.TAREAS`, y la web puede afirmarla porque ve el texto entero
que la persona escribio. Un paquete viejo que no la traiga entra en NO_DATA, y
sigue siendo lo correcto para el: `libre` significa «no vino por un atajo», que
es una afirmacion, y desde este lado --que solo recibe el paquete-- no se sabe.
La misma palabra vale o no vale segun quien pueda demostrarla.

Y se pasa por el vocabulario de `captura`, no se copia: una etiqueta que el
navegador escriba mal no puede meter una tarea nueva en la tabla por la puerta
de atras, que es justo donde el `group by` deja de significar algo.

**No importa lo que no entiende.** Una correccion sin `prompt` o sin
`respuesta` no es media correccion: es ruido con forma de dato. Se salta, se
cuenta y se dice cual. Se prefiere un informe con huecos a una tabla con
adivinanzas.

LO QUE SI PONE DE SU PARTE
--------------------------
`arnes = 'web'`, que es la unica columna que esta funcion puede rellenar con
certeza y la razon por la que el arnes doble existe: sin ella, los turnos del
navegador y los de la app se mezclan en la misma media y esa media no describe
a ninguno de los dos.

IMPORTAR DOS VECES NO DUPLICA. La persona va a pegar el mismo paquete mas de
una vez -- porque no recuerda si lo hizo, porque el paquete crecio con dos
correcciones nuevas, o porque cambio de aparato. La llave es la FIRMA: la misma
correccion firmada es la misma correccion. Sin firma, la llave es el par
(prompt, respuesta, corregido), que es lo mejor que hay cuando no hay firma --
y se dice que es lo mejor que hay, no que sea equivalente.
"""
from __future__ import annotations

import json

import captura
import linea as _linea

# El esquema que este importador entiende. La web lo escribe en `taller.js`
# como `esquema: ap.esquema_paquete || 1`. Se comprueba en vez de suponerse: un
# paquete de una version futura puede tener los mismos nombres y otro
# significado, y eso es peor que uno que no se parezca en nada.
ESQUEMAS = (1,)

# Las columnas que este importador anade a `turnos`, con la misma migracion
# aditiva que ya uso el rastro del contexto: una memoria creada antes de que
# esto existiera no las tiene, y no se le puede pedir que empiece de cero.
#
# `firma_ok` es texto y no un entero a proposito. Un booleano solo sabe decir
# si o no, y aqui la respuesta de hoy es «nadie lo ha comprobado» -- que es un
# tercer valor y el unico verdadero mientras no haya Ed25519.
PROCEDENCIA = (
    ("origen", "text not null default 'NO_DATA'"),
    ("firma", "text not null default 'NO_DATA'"),
    ("autor", "text not null default 'NO_DATA'"),
    ("firma_ok", "text not null default 'NO_DATA'"),
)


def asegurar(c):
    """Anade las columnas de procedencia si faltan. No borra ni reescribe nada."""
    captura.asegurar(c)
    ya = {d[1] for d in c.execute("pragma table_info(turnos)")}
    for nombre, tipo in PROCEDENCIA:
        if nombre not in ya:
            c.execute(f"alter table turnos add column {nombre} {tipo}")


def leer(texto):
    """Convierte el texto pegado en un paquete, o devuelve None.

    Nunca levanta. Lo que llega aqui lo ha pegado una persona desde un
    portapapeles: llega cortado, con comillas tipograficas del correo, o vacio.
    Un rastro de pila no le dice nada a nadie; un None que el que llama
    convierte en una frase, si.
    """
    try:
        d = json.loads(texto)
    except Exception:
        return None
    if not isinstance(d, dict):
        return None
    if d.get("esquema") not in ESQUEMAS:
        return None
    if not isinstance(d.get("correcciones"), list):
        return None
    return d


def _clave(par, firma):
    """La llave de identidad de una correccion, para no duplicarla."""
    if firma and firma != "NO_DATA":
        return ("firma", firma)
    return ("par", (par.get("prompt") or "").strip(),
            (par.get("respuesta") or "").strip(),
            (par.get("corregido") or "").strip())


def _ya_esta(c, clave):
    if clave[0] == "firma":
        fila = c.execute("select id from turnos where firma = ?",
                         (clave[1],)).fetchone()
    else:
        fila = c.execute(
            "select id from turnos where prompt = ? and respuesta = ? "
            "and corregido = ?", clave[1:]).fetchone()
    return fila[0] if fila else None


def importar(c, paquete):
    """Escribe las correcciones del paquete en `turnos`. Devuelve el informe.

    El informe no es decoracion: es lo que la persona lee para saber que paso
    con lo suyo. Por eso lleva `saltadas` con su motivo y no solo un numero --
    «3 de 5» sin decir cuales ni por que obliga a confiar, y aqui no se pide
    confianza, se ensena el dato.
    """
    informe = {"entradas": 0, "nuevas": 0, "repetidas": 0,
               "saltadas": [], "ids": [], "firmas_sin_verificar": 0}
    if not paquete:
        return informe
    asegurar(c)
    for i, reg in enumerate(paquete.get("correcciones") or []):
        informe["entradas"] += 1
        if not isinstance(reg, dict):
            informe["saltadas"].append({"n": i, "motivo": "no es un objeto"})
            continue
        par = reg.get("par")
        if not isinstance(par, dict):
            informe["saltadas"].append({"n": i, "motivo": "sin bloque «par»"})
            continue
        prompt = (par.get("prompt") or "").strip()
        respuesta = (par.get("respuesta") or "").strip()
        if not prompt or not respuesta:
            informe["saltadas"].append(
                {"n": i, "motivo": "sin prompt o sin respuesta"})
            continue

        firma = (reg.get("firma") or "NO_DATA").strip() or "NO_DATA"
        clave = _clave(par, firma)
        repetida = _ya_esta(c, clave)
        if repetida is not None:
            informe["repetidas"] += 1
            continue
        if firma == "NO_DATA":
            informe["saltadas"].append(
                {"n": i, "motivo": "sin firma: entra, pero sin procedencia"})
        else:
            informe["firmas_sin_verificar"] += 1

        cur = c.execute(
            "insert into turnos (prompt, respuesta, modelo, idioma, consent, "
            "correccion, corregido, motivo, tarea, arnes, "
            "origen, firma, autor, firma_ok) "
            "values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (prompt, respuesta,
             (par.get("modelo") or "NO_DATA").strip() or "NO_DATA",
             (par.get("idioma") or "NO_DATA").strip() or "NO_DATA",
             # El consentimiento se COPIA, jamas se sube. Un importador que
             # convierta un 0 en un 1 «porque la persona lo trajo a mano» es
             # exactamente el traductor en medio donde se pierde el permiso.
             1 if str(par.get("consent") or "0").strip() in ("1", "true", "si")
             else 0,
             (par.get("correccion") or "").strip() or None,
             (par.get("corregido") or "").strip() or None,
             (par.get("motivo") or "NO_DATA").strip() or "NO_DATA",
             # Del paquete si viene; si no, NO_DATA y nunca `libre`.
             captura._del_vocabulario(par.get("tarea"), captura.TAREAS),
             # Lo unico que este importador sabe con certeza.
             "web",
             (par.get("origen") or "NO_DATA").strip() or "NO_DATA",
             firma,
             (reg.get("autor") or "NO_DATA").strip() or "NO_DATA",
             # Ni 0 ni 1: nadie lo ha comprobado.
             "NO_DATA"))
        # EL EVENTO DE IMPORTACION, con la procedencia dentro. Es el que
        # contesta la pregunta que un auditor hace sobre cualquier dato que no
        # nacio aqui: de donde salio, quien lo firmo, y si esa firma se
        # comprobo. `firma_ok` viaja al evento con el mismo NO_DATA que va a la
        # tabla -- si el registro dijera que si y la tabla que no se sabe, el
        # registro seria el que miente.
        _linea.anotar(c, "importacion", f"turno:{cur.lastrowid}",
                      {"origen": (par.get("origen") or "NO_DATA"),
                       "autor": (reg.get("autor") or "NO_DATA"),
                       "firma": firma, "firma_ok": "NO_DATA"}, "carbono")
        informe["nuevas"] += 1
        informe["ids"].append(cur.lastrowid)
    return informe
