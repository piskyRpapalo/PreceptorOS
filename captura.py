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

import linea as _linea
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
    # --- LO QUE CONVIERTE EL CUADERNO EN PRECEPTOR DE LoRAs (2026-09-08) ---
    ("tarea", "text not null default 'NO_DATA'"),
    ("arnes", "text not null default 'NO_DATA'"),
    ("veredicto", "text not null default 'NO_DATA'"),
    ("juez", "text not null default 'NO_DATA'"),
    ("juzgado", "text"),
    # --- LA CLASE DEL PAR (2026-09-13) ------------------------------------
    #
    # Por que el defecto es `correccion` y no `NO_DATA`, que es el defecto de
    # todo lo demas en esta tupla. Porque aqui NO hay hueco: un turno guardado
    # antes de hoy es una correccion, que es lo UNICO que podia ser -- no
    # existia otra clase por la que hubiera entrado. `NO_DATA` diria «no se
    # sabe» de algo que si se sabe, y ademas dejaria fuera del dataset a todos
    # los turnos viejos, porque el filtro de `pares()` es positivo.
    #
    # `ALTER TABLE ADD COLUMN` con NOT NULL y DEFAULT rellena las filas que ya
    # estan con ese defecto, asi que la migracion no deja NULLs que luego haya
    # que interpretar.
    ("tipo", "text not null default 'correccion'"),
)

# --- LOS TRES VOCABULARIOS CERRADOS ---------------------------------------
#
# POR QUE CERRADOS, y no texto libre. `proyectos.ESTADOS` y `herramientas.FOCOS`
# ya lo son, y por el mismo motivo: un campo libre no se puede agrupar. Con
# `modelo` de texto libre --que es lo que habia-- la pregunta «como le fue a
# este modelo en esta tarea» no tiene respuesta, tiene un `group by` sobre
# cadenas que alguien escribio a mano en cuatro sitios distintos.
#
# Y ESA PREGUNTA ES EL PRODUCTO. Una base que no la contesta guarda turnos; una
# que la contesta es un preceptor de LoRAs.

# LA TAREA SALE DE LOS OCHO COMANDOS QUE YA ESTAN EN PRODUCCION en la web
# (`servicios.json`), y no de una lista nueva. `comandos.js` lo dice mejor de lo
# que lo diria yo: «EL COMANDO NO SE TRADUCE, LO QUE HACE SI. Un comando es un
# IDENTIFICADOR». Eso los hace estables en las ocho lenguas y en las dos caras.
#
# Y ES EL PARALELO QUE PEDIA EL SOBERANO: los atajos de la web y los de la app
# comparten etiqueta, asi que un turno de una y otro de la otra son COMPARABLES
# -- un LoRA entrenado con los de aqui se puede medir contra los de alla. Con
# dos vocabularios distintos, esa comparacion no existiria y nadie lo notaria.
#
# `libre` es la conversacion sin atajo, que es la mayoria: se declara en vez de
# dejarla en NO_DATA, porque «no vino por un atajo» es un hecho, no un hueco.
TAREAS = ("instalar", "perfil", "dataset", "script", "eco", "formatos",
          "auditar", "frontera", "libre")

# EL ARNES · la dimension del arnes doble. La MISMA base sirve a la IA de dentro
# y a la de fuera, y sin esta columna sus turnos se mezclan: la media de un
# modelo local a 5 tok/s con la de uno de frontera no describe a ninguno de los
# dos.
ARNESES = ("app", "web", "externo")

# LA CLASE DEL PAR · el vocabulario que impide entrenar con lo contrario de lo
# que se cree (2026-09-13). Desde hoy la web manda DOS cosas por el mismo
# esquema de diez campos, y solo una de las dos se puede entrenar:
#
#   correccion · alguien leyo una respuesta mala y escribio la BUENA. El campo
#                `correccion` es una RESPUESTA mejor. Es lo de siempre.
#   reescritura · la persona pregunto, no le sirvio, y volvio a preguntar lo
#                mismo con otras palabras. Aqui `correccion` NO es una
#                respuesta: es un PROMPT mejor.
#
# LA TRAMPA, dicha antes de que muerda: meter el `correccion` de una
# reescritura donde va una respuesta entrena al modelo a CONTESTAR UNA PREGUNTA
# CON OTRA PREGUNTA. El esquema es identico, el significado es el contrario, y
# nada en la tabla lo avisaria. Por eso la clase es una columna y no un matiz
# que haya que recordar.
#
# Es el mismo reparto que hace el rack en `hexelion/laboratorio/ingesta.py`, y
# se declara aqui por el mismo motivo que `ARNESES`: un filtro que se escribe a
# mano en cada consulta se olvida en una.
TIPOS = ("correccion", "reescritura")

# EL VEREDICTO, Y AQUI VA LA DOCTRINA DENTRO DEL ESQUEMA.
#
# Tres de los seis son ACIERTOS, y dos de esos tres los cuenta como fallo
# cualquier banco de pruebas de fuera:
#
#   no_data   · dijo «no lo se» cuando de verdad no lo sabia.
#   traspaso  · dijo «esto me excede, le toca a otro» y le tocaba.
#
# Un banco que los puntue como error entrena al modelo a INVENTAR antes que a
# callarse -- que es exactamente el comportamiento que esta casa lleva un mes
# combatiendo. Si el vocabulario no distingue «callarse bien» de «fallar», el
# entrenamiento castigara justo lo que la doctrina exige.
#
#   mudo      · el reverso: dijo NO_DATA teniendo el dato delante. ESO si es
#               fallo, y es distinto de alucinar: no invento, se rindio.
#   alucinacion · afirmo algo que no estaba en `ctx_ids` y no es cierto. Con el
#               rastro del contexto esto dejo de ser una intuicion y es una
#               consulta.
#
# `NO_DATA` --el defecto-- significa NADIE LO HA JUZGADO. No es un cero: un
# turno sin juzgar no es un turno fallado, y confundirlos hundiria la nota de
# todo modelo nuevo por el mero hecho de ser nuevo.
VEREDICTOS = ("acierto", "no_data", "traspaso", "fallo", "alucinacion", "mudo")

# Los tres que cuentan a favor. Se declara la lista en vez de repetir el
# criterio en cada consulta: el dia que entre un veredicto nuevo, se decide su
# signo AQUI y una sola vez.
ACIERTOS = ("acierto", "no_data", "traspaso")


def _del_vocabulario(valor, vocabulario):
    """Un valor fuera de la lista no es un error: es NO_DATA.

    No se levanta y no se inventa. Levantar convertiria una etiqueta mal puesta
    en un turno perdido --y este cuaderno existe precisamente para no perder
    turnos--; aceptarla dejaria entrar `Instalar`, `instalar ` e `INSTALL` como
    tres tareas distintas, y entonces el `group by` vuelve a no significar nada.
    """
    v = str(valor or "").strip().lower()
    return v if v in vocabulario else "NO_DATA"

CLAVE_PERFIL = "captura"


# LA VISTA DE ESTUDIOS · un turno que puede ENSEÑAR algo.
#
# Un estudio no es un turno. Un turno es lo que pasó; un estudio es un turno
# del que se puede aprender, y eso depende de tres cosas que la tabla ya sabe
# --- consentimiento, clase y veredicto --- pero que hay que leer juntas. Cada
# consulta que las combinara a mano acabaría combinándolas distinto.
#
# LO QUE LA VISTA NO ENSEÑA, y es su regla principal: ni `prompt`, ni
# `respuesta`, ni `correccion` en crudo. Solo sus LARGOS. Lo que se mide de un
# estudio --- cuántos hay, de qué clase, con qué veredicto --- no necesita el
# texto de nadie, y una vista que lo expusiera acabaría copiada en un informe,
# en un log o en `loops.db`. El texto lo ve su dueño; el laboratorio ve la forma.
#
# `fue_corregido` es un SÍ/NO y no un largo, porque `corregido` guarda la FECHA
# en que se corrigió, no el texto (ver `corregir()` más abajo). Medir su
# longitud daría 19 --- los caracteres de un `datetime` --- y ese 19 parecería
# un dato.
#
# Los cuatro estados, y por qué `sin_consentimiento` va PRIMERO en el CASE: un
# turno sin consentimiento no es material de nadie, tenga la corrección que
# tenga. Poner esa rama la primera hace imposible que otra la adelante.
#
# POR QUÉ `tipo` NO ENTRA EN EL ÍNDICE, aunque la vista lo lea. Lo llevaba, y
# rompió `test_los_turnos_viejos_ganan_la_clase_sin_perderse`: esa prueba
# simula una memoria anterior a la clase QUITANDO la columna, y sqlite se niega
# a soltar una columna que un índice nombra. El índice habría bloqueado el
# camino de migración que la casa tiene escrito y probado.
#
# Y sacarlo no cuesta nada, que es lo que lo convierte en decisión y no en
# rodeo: `tipo` tiene DOS valores. Una columna de cardinalidad dos en la
# tercera posición de un índice compuesto no separa casi nada; lo que separa de
# verdad es `consent`, y después el veredicto y el arnés.
ESQUEMA_ESTUDIOS = """
create view if not exists estudios as
select
    id                as turno_id,
    cuando, arnes, tarea, veredicto, tipo, consent, juez, juzgado, motivo,
    ctx_completo, ctx_fuera,
    case
        when consent <> 1 or consent is null then 'sin_consentimiento'
        when tipo = 'reescritura'
             or coalesce(correccion, '') <> ''        then 'entrenable'
        when veredicto in ('fallo','alucinacion','no_data','traspaso','mudo')
                                                      then 'diagnostico'
        else 'juzgado'
    end               as estado,
    case when coalesce(corregido, '') <> '' then 1 else 0 end as fue_corregido,
    length(prompt)                      as prompt_len,
    length(respuesta)                   as respuesta_len,
    length(coalesce(correccion, ''))    as correccion_len
from turnos;
create index if not exists idx_turnos_estudio
    on turnos(consent, veredicto, arnes, tarea);
create index if not exists idx_turnos_tiempo_arnes
    on turnos(cuando, arnes);
"""


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
    # La vista y sus indices van DESPUES de las columnas del rastro: la vista
    # las nombra, y sobre una tabla vieja que aun no las tenga fallaria al
    # crearse. El orden no es estetico.
    c.executescript(ESQUEMA_ESTUDIOS)


def activa(perfil):
    """¿Quiere la persona este cuaderno? Por defecto sí; apagarlo es una palabra.

    Se lee del perfil y no de una constante: una preferencia que vive en el
    código es una preferencia del programador.
    """
    return str((perfil or {}).get(CLAVE_PERFIL, "si")).strip().lower() not in (
        "no", "0", "false", "off")


def registrar(c, prompt, respuesta, modelo="NO_DATA", idioma="NO_DATA",
              rastro=None, tarea=None, arnes=None):
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
            "ctx_ids, ctx_tokens, ctx_fuera, ctx_completo, tarea, arnes) "
            "values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (prompt.strip(), respuesta.strip(), modelo or "NO_DATA",
             idioma or "NO_DATA",
             ids if ids else "NO_DATA",
             r.get("tokens"), r.get("fuera"),
             None if r.get("completo") is None else int(r["completo"]),
             _del_vocabulario(tarea, TAREAS),
             _del_vocabulario(arnes, ARNESES)))
        return cur.lastrowid
    except Exception:
        # Se caza TODO a proposito, y no es pereza. El contrato de esta
        # funcion es que no levanta: se la llama con la respuesta ya en la
        # pantalla de la persona, y a esas alturas cualquier excepcion --de
        # sqlite, del disco, o de un objeto que no era el que se esperaba--
        # convertiria un cuaderno al margen en una conversacion rota. Se
        # devuelve None, que es decir "no se guardo", y eso es honesto.
        return None


def _actor_de(juez):
    """De quien juzga a la clase de actor que entiende la linea.

    El juez se guarda TAL CUAL --el tag completo del modelo, o el nombre del
    comprobador-- porque su vocabulario esta abierto a proposito. La linea, en
    cambio, tiene tres clases cerradas, y la diferencia entre ellas es la que
    importa ante un auditor: un acierto firmado por un script que compara
    contra el dato real no vale lo mismo que uno firmado por un modelo que
    opina.

    Lo que no se reconoce cae a NO_DATA en vez de adivinarse. Llamar «modelo» a
    un juez desconocido porque «suena a modelo» seria atribuir una clase de
    evidencia por el aspecto del nombre.
    """
    j = str(juez or "").strip().lower()
    if j in ("carbono", "humano", "persona"):
        return "carbono"
    if j.startswith("determinista") or j.startswith("script") or j.startswith("test"):
        return "determinista"
    if j in ("", "no_data"):
        return "NO_DATA"
    return "modelo"


def juzgar(c, turno_id, veredicto, juez="NO_DATA", motivo="NO_DATA"):
    """Anota como le fue a un turno, y QUIEN lo dice.

    EL JUEZ ES OBLIGATORIO EN EL ESQUEMA aunque su valor pueda ser NO_DATA, y
    esa asimetria es deliberada: un veredicto sin juez es una opinion con cara
    de medida. Aqui pueden juzgar tres clases de cosa --el carbono, otro modelo
    del rack, o un comprobador determinista-- y no valen lo mismo. Un acierto
    firmado por un script que compara contra el dato real no es un acierto
    firmado por un modelo que opina; mezclarlos daria una nota media que no
    describe nada.

    Se guarda el juez TAL CUAL lo pasen --el nombre del modelo con su tag
    completo, o el del comprobador-- porque el vocabulario de jueces todavia no
    existe y fingir uno cerrado seria peor que dejarlo abierto y decirlo.

    UN VEREDICTO SE PUEDE CAMBIAR, y esta columna no lleva historial. Aqui
    vive el veredicto VIGENTE y nada mas: esto es el cuaderno de lo que paso,
    no el de quien opino que.

    Y LA OTRA TABLA LLEGO, el 2026-09-08. Este parrafo decia que seguir la
    pista de los cambios de veredicto seria «otra tabla y otra conversacion»;
    esa tabla es `linea.py`, asi que la conversacion es esta. Cada juicio deja
    ademas un evento con su juez y su hora, y por eso ahora se puede contestar
    «quien cambio este veredicto y cuando» sin anadir ni una columna a esta
    tabla, que es exactamente lo que aquel parrafo pedia que no se hiciera.

    Devuelve True si se anoto, False si no. **Nunca levanta**, por el mismo
    contrato que `registrar`: esto se llama despues del turno, y a esas alturas
    un fallo aqui no puede llevarse por delante nada.
    """
    v = _del_vocabulario(veredicto, VEREDICTOS)
    if v == "NO_DATA":
        # Un veredicto fuera del vocabulario NO se guarda como NO_DATA: eso
        # borraria uno anterior valido con un valor que significa «sin juzgar».
        # Se rechaza y se dice.
        return False
    try:
        asegurar(c)
        c.execute("update turnos set veredicto=?, juez=?, motivo=?, "
                  "juzgado=datetime('now') where id=?",
                  (v, str(juez or "NO_DATA"), str(motivo or "NO_DATA"),
                   int(turno_id)))
        # El evento va ANTES del commit, dentro de la misma transaccion: si no
        # se puede anotar, no se guarda el veredicto tampoco. Y aqui `anotar`
        # queda dentro del `try` que ya existia porque el contrato de esta
        # funcion es no levantar nunca -- se llama despues del turno. Un
        # veredicto perdido es un dato menos; un turno roto por anotar un
        # veredicto seria una averia peor que la que se evita.
        _linea.anotar(c, "veredicto", f"turno:{int(turno_id)}",
                      {"veredicto": v, "juez": str(juez or "NO_DATA")},
                      _actor_de(juez))
        c.commit()
        return True
    except Exception:
        # EL ROLLBACK ES LO QUE HACE CIERTO EL COMENTARIO DE ARRIBA. Sin el, la
        # ordenacion no protegia nada: `memory.abrir` hace `commit()` al salir
        # con normalidad, y esta funcion --que por contrato no levanta-- salia
        # con normalidad tambien. Resultado medido el 2026-09-08: `juzgar`
        # devolvia False mientras el veredicto quedaba comprometido en
        # `memory.db` sin un solo evento en la linea. Un veredicto sin registro
        # es, ante el art. 12, un veredicto que no ocurrio -- y el peor de los
        # tres estados posibles, porque el sistema sigue COMO SI hubiera
        # quedado registro y ademas te ha dicho que fallo.
        #
        # Deshacer aqui no rompe el contrato de no levantar: sigue devolviendo
        # False. Lo que cambia es que ahora False significa «no quedo nada»,
        # que es lo que quien llama ya creia que significaba.
        try:
            c.rollback()
        except Exception:                                       # noqa: BLE001
            # Si ni el rollback se puede, no hay nada mas que esta funcion
            # pueda hacer sin levantar. El False sigue siendo verdad.
            pass
        return False


def rendimiento(c, arnes=None, desde=None):
    """Como le fue a cada modelo en cada tarea. LA consulta del preceptor.

    Devuelve una fila por (modelo, tarea) con lo que hace falta para decidir
    que entrenar despues:

        {"modelo": "preceptor-charla-web:v1", "tarea": "instalar",
         "turnos": 42, "juzgados": 30, "aciertos": 24, "tasa": 0.8,
         "alucinaciones": 2, "mudos": 1,
         "ctx_tokens_medio": 312, "ctx_fuera_medio": 1.4,
         "parciales": 7}

    `tasa` SE CALCULA SOBRE LOS JUZGADOS, no sobre los turnos. Sobre el total,
    un modelo nuevo con noventa turnos sin juzgar sacaria un 0,05 y pareceria
    pesimo cuando lo unico que pasa es que nadie lo ha mirado. Sin juzgar no es
    fallado -- es la misma distincion que separa NO_DATA de cero en toda esta
    casa, y aqui decide a que modelo se le retira el apoyo.

    Y `tasa` es None cuando no hay ni un juzgado. No es cero: cero significa
    «se le miro y fallo todo».

    LAS DOS COLUMNAS DE CONTEXTO VAN AL LADO DE LA NOTA a proposito. Una tasa
    baja con `ctx_fuera_medio` alto NO es un modelo malo: es una recuperacion
    que no le esta llevando el dato, y se arregla con presupuesto, no con
    entrenamiento. Ese par de numeros juntos es la diferencia entre entrenar un
    LoRA y arreglar una consulta -- y separadas, esa diferencia no se ve.
    """
    asegurar(c)
    sql = ("select modelo, tarea, count(*) n, "
           "sum(veredicto != 'NO_DATA') juzgados, "
           "sum(veredicto in ('acierto','no_data','traspaso')) aciertos, "
           "sum(veredicto = 'alucinacion') alucinaciones, "
           "sum(veredicto = 'mudo') mudos, "
           "avg(ctx_tokens) ctxt, avg(ctx_fuera) ctxf, "
           "sum(ctx_completo = 0) parciales "
           "from turnos")
    donde, args = [], []
    if arnes:
        donde.append("arnes = ?")
        args.append(_del_vocabulario(arnes, ARNESES))
    if desde:
        donde.append("cuando >= ?")
        args.append(str(desde))
    if donde:
        sql += " where " + " and ".join(donde)
    sql += " group by modelo, tarea order by n desc"

    filas = []
    for r in c.execute(sql, args):
        juzgados, aciertos = r[3] or 0, r[4] or 0
        filas.append({
            "modelo": r[0], "tarea": r[1], "turnos": r[2],
            "juzgados": juzgados, "aciertos": aciertos,
            "tasa": (aciertos / juzgados) if juzgados else None,
            "alucinaciones": r[5] or 0, "mudos": r[6] or 0,
            "ctx_tokens_medio": round(r[7], 1) if r[7] is not None else None,
            "ctx_fuera_medio": round(r[8], 2) if r[8] is not None else None,
            "parciales": r[9] or 0,
        })
    return filas


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
    if cur.rowcount != 1:
        return False
    # O LOS DOS, O NINGUNO. El evento se escribe DESPUES del cambio y dentro de
    # la misma transaccion, y si falla se deja subir: `memory.abrir` hace
    # rollback y el cambio se deshace con el. Esa es la unica ordenacion que no
    # puede producir un consentimiento sin registro -- y un consentimiento sin
    # registro es, ante el art. 12, un consentimiento que no ocurrio.
    #
    # `revocacion` cuando baja y `consentimiento` cuando sube, y no un tipo
    # solo con un campo dentro: retirar un permiso es el evento que un auditor
    # busca por su nombre, y buscarlo dentro del JSON de otro tipo es la clase
    # de consulta que nadie escribe.
    _linea.anotar(c, "consentimiento" if si else "revocacion",
                  f"turno:{turno_id}",
                  {"consent": 1 if si else 0, "motivo": motivo}, "carbono")
    return True


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
    if cur.rowcount != 1:
        return False
    # El texto corregido NO viaja al evento, y es deliberado: la linea es un
    # registro de QUE PASO, no una segunda copia de la memoria. Guardar el
    # texto aqui lo duplicaria en un sitio que ademas no se puede rectificar
    # -- y entonces borrar una correccion de la memoria dejaria su contenido
    # vivo en la linea para siempre. Viaja su medida, que es lo que un auditor
    # necesita para saber que hubo correccion y de que tamano.
    _linea.anotar(c, "correccion", f"turno:{turno_id}",
                  {"largo": len(texto.strip()), "motivo": motivo}, "carbono")
    return True


def pares(c, solo_consentidos=True):
    """Los turnos, listos para el constructor del dataset.

    Un turno corregido sale como par de preferencia; uno sin corregir, como
    turno a secas. La forma es la que ya espera `datos/ESQUEMA.md`.

    LAS REESCRITURAS NO SALEN DE AQUI, y es la linea que impide envenenar el
    entrenamiento. En una reescritura `correccion` es un PROMPT mejor, no una
    respuesta mejor; saldria por `elegido` --que es el lado bueno del par de
    preferencia-- y entrenaria al modelo a contestar una pregunta con otra
    pregunta. Valen mucho, pero para otra cosa: son REGLAS para la capa de
    prompt, no ejemplos para un LoRA. Quien las quiera, que las lea de la
    tabla mirando `tipo`.

    EL FILTRO ES POSITIVO --`tipo = 'correccion'`-- y no `!= 'reescritura'`,
    a proposito: asi FALLA CERRADO. El dia que entre una tercera clase por la
    web, se queda fuera del dataset hasta que alguien decida que es, en vez de
    colarse por no estar en la lista de excluidos.
    """
    asegurar(c)
    sql = ("select id, cuando, prompt, respuesta, correccion, idioma, motivo "
           "from turnos where tipo = 'correccion'")
    if solo_consentidos:
        sql += " and consent = 1"
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
