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

Y DESDE EL 2026-09-13, DOS CLASES DE PAR
-----------------------------------------
La web ya no manda una sola cosa por estos diez campos. Manda CORRECCIONES
--una respuesta mejor-- y REESCRITURAS --un PROMPT mejor, la persona volvio a
preguntar lo mismo con otras palabras--. El esquema es identico y el
significado es el contrario, asi que la clase se guarda en su propia columna y
el reparto se hace aqui. La explicacion entera esta junto a `_clase()`, que es
donde se decide; si solo se lee una cosa de este fichero, que sea esa.

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
ESQUEMAS = (1, "preceptoros/correcciones/1")

# LAS DOS FORMAS DEL PAQUETE, y la segunda llego el 2026-09-13.
#
# `taller.js` escribia `{esquema: 1, correcciones: [...]}`. La puerta de
# exportacion nueva de la web --`bronce.js`-- escribe
# `{esquema: "preceptoros/correcciones/1", pares: [...]}`. Medido: el importador
# rechazaba el fichero ENTERO, devolviendo None, y quien lo hubiera exportado no
# habria sabido por que. Un exportador y un importador que dicen ser el mismo
# esquema y no se entienden son dos esquemas.
#
# Se aceptan las dos y no se migra la vieja: hay paquetes exportados ahi fuera,
# en aparatos de gente, y romperlos para tener una sola forma seria cobrarle a
# quien ya hizo el trabajo.
LISTAS = ("pares", "correcciones")


def _lista(d):
    for nombre in LISTAS:
        if isinstance(d.get(nombre), list):
            return d[nombre]
    return None

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
    # `senal` vive AQUI y `tipo` vive en `captura.RASTRO`, y el reparto no es
    # capricho. `captura.pares()` --el que arma el dataset-- filtra por `tipo`,
    # asi que esa columna tiene que existir en TODA memoria, tambien en una que
    # no haya importado nunca nada; si viviera aqui, `pares()` reventaria con
    # «no such column» en una base recien creada. `senal` no la lee nadie de
    # captura: solo la escribe este importador, que es la definicion de lo que
    # va en PROCEDENCIA -- lo que unicamente se sabe al importar.
    #
    # Es la misma pareja `tipo`/`senal` que `ingesta.asegurar_columnas()` anade
    # en el rack, repartida segun el esquema de ESTA app en vez de copiada.
    ("senal", "text not null default 'NO_DATA'"),
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
    if _lista(d) is None:
        return None
    return d


# VERIFICAR LA FIRMA CUANDO SE PUEDE, Y DECIRLO CUANDO NO.
#
# La cabecera de este fichero decia «la biblioteca estandar de Python no trae
# Ed25519... hasta ese dia, firma_ok vale NO_DATA». Era cierto y sigue siendolo
# para la Boveda --el producto que se instala la gente, que promete stdlib y no
# se le puede meter una dependencia--. Pero en un nodo donde `cryptography` YA
# esta (medido el 2026-09-13: 46.0.5 en el soberano), seguir diciendo NO_DATA es
# tirar una comprobacion que se puede hacer.
#
# Asi que es OPCIONAL de verdad: si la biblioteca esta, se verifica y `firma_ok`
# pasa a «si» o «no»; si no esta, se queda en NO_DATA con su causa. La promesa
# de stdlib no se rompe --el import falla y el guion sigue-- y el nodo que puede
# comprobar, comprueba.
#
# QUE SE VERIFICA: los bytes que firmo el navegador. `bronce.js` los manda en
# `canonico`; si no vienen, no se reconstruyen aqui --reconstruirlos exige que
# dos serializadores coincidan caracter a caracter, y esa suposicion es
# justamente lo que un verificador no debe hacer--. Sin `canonico`, NO_DATA.
# LA FIRMA NO SE VERIFICA AQUI, Y AHORA SE SABE POR QUE EXACTAMENTE.
#
# Estuve a punto de meter `cryptography` para comprobar el Ed25519, porque en el
# nodo soberano esta instalado. `test_superficie.py` lo paro: analiza los imports
# de todo lo alcanzable desde las puertas y `PERMITIDAS_EN_EL_CAMINO` esta VACIO
# a proposito. Da igual que el import vaya dentro de una funcion -- el analisis
# es estatico, y tiene que serlo: la promesa publica «MVP Python stdlib only» es
# sobre lo que se INSTALA, no sobre lo que se ejecuta hoy aqui.
#
# Y el gate tenia razon en algo mas de fondo: verificar firmas es trabajo del
# RACK, no de la Boveda. `hexelion/laboratorio/ingesta.py` ya lo hace con
# `cryptography`, en un sitio donde esa dependencia esta declarada y no promete
# nada a nadie. Meterla aqui habria movido una frontera para ganar una
# comprobacion que ya existe al otro lado.
#
# LO QUE SI SE COMPRUEBA, Y CON BIBLIOTECA ESTANDAR: que el texto firmado sea el
# que se guarda. `bronce.js` manda en `canonico` los bytes exactos que se
# firmaron; reconstruirlos desde `par` es `json.dumps` y comparar dos cadenas.
# Eso caza el ataque que de verdad importa --firmar un par honesto, cambiarle el
# contenido y dejar la firma-- sin tocar una sola curva eliptica. Es el mismo
# agujero que se cerro en `ingesta.py` el 2026-09-13 y que aqui seguia abierto.

# Los campos del par en el ORDEN en que los escribe `corregir.js`. Importa:
# `JSON.stringify` conserva el orden de insercion, asi que un campo movido
# cambia los bytes.
CAMPOS_PAR = ("prompt", "respuesta", "correccion", "corregido", "modelo",
              "idioma", "motivo", "tarea", "consent", "origen")


def _canonico(par):
    orden = {k: par[k] for k in CAMPOS_PAR if k in par}
    for k, v in par.items():
        if k not in orden:
            orden[k] = v
    return json.dumps(orden, ensure_ascii=False, separators=(",", ":"))


def verificar_firma(reg):
    """«no» si el texto firmado no es el que se guarda. Nunca «si».

    Tres valores posibles en la columna y aqui solo se pueden dar dos: «no»
    --hay prueba de que el paquete se manipulo-- y `NO_DATA` --nadie ha
    comprobado la curva--. Devolver «si» exigiria verificar el Ed25519, y eso
    pasa en el rack. Un «si» desde aqui seria una garantia que este fichero no
    puede dar.
    """
    texto = reg.get("canonico")
    par = reg.get("par")
    if isinstance(texto, str) and isinstance(par, dict):
        if texto != _canonico(par):
            return "no"
    return "NO_DATA"


# --- DOS CLASES DE PAR, Y CONFUNDIRLAS ENVENENA EL DATASET -------------------
#
# Hasta el 2026-09-13 por esta puerta entraba una sola cosa: una CORRECCION.
# `corregir.js` deja que alguien lea una respuesta mala y escriba la buena, y
# `correccion` se guarda como LA RESPUESTA ELEGIDA, porque es lo que es.
#
# Desde hoy entra tambien una REESCRITURA, que `aprender.js` captura sin que
# nadie se siente a escribir: la persona pregunta, no le sirve, y vuelve a
# preguntar lo mismo con otras palabras. Es la senal mas valiosa que da la web
# --dice que NO se entendio, y lo dice sin pedirle trabajo a nadie--.
#
# Y trae una trampa que hay que nombrar antes de que muerda: en una
# reescritura, `correccion` NO es una respuesta mejor, es un PROMPT mejor.
# Guardarla en la columna `correccion` --que es de donde `captura.pares()` saca
# el lado ELEGIDO del par de preferencia-- entrenaria al modelo a CONTESTAR UNA
# PREGUNTA CON OTRA PREGUNTA. Los diez campos son identicos, el significado es
# el contrario, y nada en la tabla lo avisaria.
#
# EL REPARTO, que es el mismo que hace el rack:
#
#   correccion  · `correccion` -> columna `correccion`. Es una respuesta.
#   reescritura · `correccion` -> `senal.reescrito_a`, FUERA de las columnas de
#                 entrenamiento. `prompt` y `respuesta` se quedan con la forma
#                 que fallo y con lo que esa forma se llevo -- las dos cosas
#                 malas a proposito: juntas son el caso de estudio.
#
# DOS CERROJOS Y NO UNO. La columna `correccion` se queda vacia en una
# reescritura Y ADEMAS `captura.pares()` filtra por `tipo = 'correccion'`.
# Parece redundante y no lo es: el primero protege a quien lea la columna a
# pelo, el segundo a quien construya el dataset por la puerta buena. El dia que
# alguien cambie uno, el otro sigue de pie.
#
# UN PAQUETE SIN `tipo` ES UNA CORRECCION. No es una suposicion optimista: es
# lo UNICO que podian ser los paquetes anteriores a hoy, porque la otra clase
# no existia. Y `autoridad` es un BOOLEANO --«habia clave en ese momento»--, no
# un identificador: el QUIEN ya viaja en la firma, y confundir las dos cosas
# convertiria una senal agregada en un rastro personal.

def _clase(par):
    """(tipo, senal_json) del par. Fuera del vocabulario -> se dice y no entra.

    Un `tipo` que no este en `captura.TIPOS` NO se degrada a «correccion»: eso
    es exactamente como una clase desconocida acabaria en el dataset. Se
    devuelve tal cual para que el que llama lo rechace, que es fallar cerrado.
    """
    bruto = par.get("tipo")
    tipo = "correccion" if bruto is None or bruto == "" else str(bruto).strip().lower()
    senal = {
        "tipo": tipo,
        # Booleano, no identificador. `1 if ... else 0` y no el valor crudo:
        # asi un `autoridad: "davidpecero"` que llegara por error se guarda
        # como un 1 y no como un nombre.
        "autoridad": 1 if par.get("autoridad") else 0,
        "turnos_antes": par.get("turnos_antes"),
    }
    if tipo == "reescritura":
        # Lo bueno de una reescritura: la forma que SI decia lo que queria.
        # Aqui, y no en la columna `correccion`.
        senal["reescrito_a"] = (par.get("correccion") or "").strip()
    return tipo, json.dumps(senal, ensure_ascii=False, separators=(",", ":"))


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
    for i, reg in enumerate(_lista(paquete) or []):
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

        # LA CLASE SE DECIDE ANTES DE ESCRIBIR NADA, y una que no se reconoce
        # no entra. Degradarla a «correccion» --que es lo que haria un
        # `_del_vocabulario` aqui-- meteria en el dataset justo lo que no se
        # sabe leer. Fallar cerrado es que se quede fuera y se diga cual.
        tipo, senal = _clase(par)
        if tipo not in captura.TIPOS:
            informe["saltadas"].append(
                {"n": i, "motivo": f"clase de par desconocida: «{tipo}». Este "
                                   "importador solo sabe repartir "
                                   f"{' y '.join(captura.TIPOS)}, y una clase "
                                   "que no sabe leer no entra"})
            continue

        firma = (reg.get("firma") or "NO_DATA").strip() or "NO_DATA"

        # SE VERIFICA ANTES DE DEDUPLICAR, y el orden importa.
        #
        # La llave de identidad es la FIRMA. Asi que un par legitimo al que
        # alguien le cambie el contenido y le deje la firma original choca con
        # el que ya esta, se cuenta como «repetida» y se descarta. No entra
        # --eso esta bien-- pero con el orden viejo el intento no se contaba:
        # `firmas_rotas` decia CERO habiendo una manipulacion delante. Medido
        # el 2026-09-13 con un par firmado de verdad y su copia trucada.
        #
        # Un contador que dice cero cuando hubo un intento es peor que no
        # tenerlo: se mira, se ve limpio, y se deja de mirar.
        veredicto = verificar_firma(reg)
        if veredicto == "no":
            informe["firmas_rotas"] = informe.get("firmas_rotas", 0) + 1
            informe["saltadas"].append(
                # EL MOTIVO DICE LO QUE SE COMPROBO, ni mas ni menos. Decia
                # «la firma no corresponde a esa clave publica» y aqui NO se
                # mira ninguna clave: se compara el texto firmado con el que se
                # guarda. Un motivo que describe una comprobacion que no se hizo
                # manda a buscar el fallo donde no esta.
                {"n": i, "motivo": "el texto firmado (`canonico`) no es el que "
                                   "trae `par`: el paquete se manipulo despues "
                                   "de firmarse. No entra"})
            continue

        clave = _clave(par, firma)
        repetida = _ya_esta(c, clave)
        if repetida is not None:
            informe["repetidas"] += 1
            continue
        if firma == "NO_DATA":
            informe["saltadas"].append(
                {"n": i, "motivo": "sin firma: entra, pero sin procedencia"})
        elif veredicto == "si":
            informe["firmas_verificadas"] = informe.get("firmas_verificadas", 0) + 1
        else:
            informe["firmas_sin_verificar"] += 1

        cur = c.execute(
            "insert into turnos (prompt, respuesta, modelo, idioma, consent, "
            "correccion, corregido, motivo, tarea, arnes, "
            "origen, firma, autor, firma_ok, tipo, senal) "
            "values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (prompt, respuesta,
             (par.get("modelo") or "NO_DATA").strip() or "NO_DATA",
             (par.get("idioma") or "NO_DATA").strip() or "NO_DATA",
             # El consentimiento se COPIA, jamas se sube. Un importador que
             # convierta un 0 en un 1 «porque la persona lo trajo a mano» es
             # exactamente el traductor en medio donde se pierde el permiso.
             1 if str(par.get("consent") or "0").strip() in ("1", "true", "si")
             else 0,
             # EL CERROJO DE LA REESCRITURA. En una correccion, `correccion` es
             # una respuesta mejor y va aqui. En una reescritura es un PROMPT
             # mejor: la columna se queda VACIA y el texto viaja a
             # `senal.reescrito_a`. Si entrara aqui, `captura.pares()` lo
             # sacaria como el lado ELEGIDO de un par de preferencia.
             None if tipo == "reescritura"
             else (par.get("correccion") or "").strip() or None,
             (par.get("corregido") or "").strip() or None,
             (par.get("motivo") or "NO_DATA").strip() or "NO_DATA",
             # Del paquete si viene; si no, NO_DATA y nunca `libre`.
             captura._del_vocabulario(par.get("tarea"), captura.TAREAS),
             # Lo unico que este importador sabe con certeza.
             "web",
             (par.get("origen") or "NO_DATA").strip() or "NO_DATA",
             firma,
             (reg.get("autor") or "NO_DATA").strip() or "NO_DATA",
             # «si» / «no» / «NO_DATA», los tres valores que hay. Se escribe lo
             # que dijo `verificar_firma`, que es NO_DATA cuando no se pudo
             # comprobar y nunca un cero que fingiria una comprobacion fallida.
             veredicto,
             # La clase, y la senal con lo que no cabe en columnas propias
             # --`autoridad`, `turnos_antes` y, si es reescritura, el prompt
             # bueno--. `tipo` va aparte y no dentro del JSON porque es por
             # donde filtra el dataset: un filtro sobre texto JSON no es un
             # filtro, es una esperanza.
             tipo, senal))
        # EL EVENTO DE IMPORTACION, con la procedencia dentro. Es el que
        # contesta la pregunta que un auditor hace sobre cualquier dato que no
        # nacio aqui: de donde salio, quien lo firmo, y si esa firma se
        # comprobo. `firma_ok` viaja al evento con el mismo NO_DATA que va a la
        # tabla -- si el registro dijera que si y la tabla que no se sabe, el
        # registro seria el que miente.
        _linea.anotar(c, "importacion", f"turno:{cur.lastrowid}",
                      {"origen": (par.get("origen") or "NO_DATA"),
                       "autor": (reg.get("autor") or "NO_DATA"),
                       # El evento dice lo MISMO que la tabla. Si el registro
                       # dijera «si» y la tabla «no se sabe», el registro seria
                       # el que miente, y un registro que miente no audita nada.
                       "firma": firma, "firma_ok": veredicto}, "carbono")
        informe["nuevas"] += 1
        informe["ids"].append(cur.lastrowid)
    return informe
