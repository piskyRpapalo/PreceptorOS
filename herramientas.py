#!/usr/bin/env python3
"""herramientas.py · lo que la base ya sabe, puesto delante del modelo.

sistema: MVP · solo biblioteca estándar. Sin red, sin dependencias.

ESTO NO ES TOOL-CALLING, Y ES UNA DECISIÓN
------------------------------------------
El motor de esta app es `texto -> texto`: un binario de completación, sin API
de herramientas. Se podría montar encima un protocolo -- que el modelo escriba
`BUSCAR: x`, parsearlo, ejecutarlo y devolvérselo en un segundo turno -- y se
descartó por tres medidas que ya están en el canon del nodo:

1. El modelo genera a ~5 tok/s. Cada herramienta costaría un turno entero de
   ida y vuelta, o sea minutos de pared por consulta.
2. Los modelos que esta app usa son pequeños, y ya se les ha visto fallar el
   formato: el LoRA se contradice ante «dame el enlace» -- dice NO_DATA y a
   continuación lista cuatro URLs.
3. La Regla de oro dice que lo determinista se resuelve sin LLM. Buscar en una
   tabla es determinista. Pedirle a un modelo que decida buscar, y confiar en
   que además acierte la sintaxis, es gastar el recurso caro en lo que el
   barato hace mejor.

Así que la app busca ANTES de preguntar y le pone delante lo que viene a
cuento. El modelo no elige qué mirar: lee. Es menos vistoso y falla menos.

LO QUE NO SE HACE, QUE ES LA MITAD DEL CONTRATO
-----------------------------------------------
* Sin nada que recuperar no se inyecta NADA, ni un encabezado vacío. Un
  «esto es lo que recuerdo: (nada)» le enseña al modelo a hablar de su propio
  vacío, justo en el primer turno de alguien que acaba de entrar.
* Lo archivado no vuelve. `memory.buscar` ya lo respeta, y aquí no se le
  levanta la excepción: un recuerdo archivado que reaparece por la puerta de
  atrás del contexto no estaría archivado.
* Un proyecto pausado no es lo que alguien tiene entre manos. Solo sale
  `activo`; los otros dos estados del vocabulario existen precisamente para
  poder no salir.
* Nunca se parte un recuerdo. Cuando no cabe, se recorta la LISTA, no el
  contenido: media frase se lee como algo que la persona dijo a medias, y el
  modelo no tiene forma de saber que el corte lo puso un presupuesto.
* Si falta el índice de búsqueda, el turno sigue vivo y se da lo que se pueda.
  `memory.buscar` levanta `BusquedaNoDisponible` a propósito -- cero por avería
  no es cero por no haber -- pero esa distinción es para quien audita, no para
  quien está hablando.

EL PRESUPUESTO, QUE SALE DE UNA CUENTA
--------------------------------------
La ventana medida en este nodo son 32.768 tokens, y a unos cuatro caracteres
por token eso son ~131.000 caracteres. El techo de aquí son 1.200, o sea el
0,9 %. Es deliberadamente pequeño por dos razones que el número grande no ve:
esto viaja ENTERO en cada turno, así que compite con la conversación; y se
queda por debajo de los 1.500 que suman los tres campos del harness, porque lo
que la persona escribió sobre sí misma a propósito no debe pesar menos que lo
que la búsqueda haya dragado.
"""
from __future__ import annotations

import memory as M
import proyectos as PR
import textos as TX

# Cuántos recuerdos como mucho. A ~200 caracteres cada uno, cinco llenan el
# presupuesto; pedir más solo sirve para que el techo los tire después.
LIMITE = 5

# El techo, en caracteres. La cuenta está arriba, en el docstring del módulo.
TECHO = 1200

# Los rótulos. Se dicen en positivo y con una instrucción concreta -- «úsalo si
# viene a cuento» --, no «no lo recites»: una orden solo negativa invita al
# modelo a hacer justo lo que se le nombra. Es la misma lección que ya está
# medida en `conversacion.PRIMER_ENCUENTRO`.
ROTULOS = {
    "es": {
        "memoria": ("Esto lo escribió la persona con la que hablas, en su "
                    "propia memoria. Úsalo si viene a cuento, con sus palabras:"),
        "proyectos": "Lo que tiene entre manos ahora mismo:",
        "perfil": "Lo que te ha contado de sí misma:",
    },
    "en": {
        "memoria": ("The person you are talking to wrote this in their own "
                    "memory. Use it if it is relevant, in their words:"),
        "proyectos": "What they have in hand right now:",
        "perfil": "What they have told you about themselves:",
    },
}


# Palabras que no seleccionan nada. La lista es corta a propósito: cada entrada
# es una palabra que aparece en casi cualquier frase, así que buscarla devuelve
# de todo -- y devolver de todo, con un techo de 1.200 caracteres, es peor que
# no devolver nada, porque lo que sí venía a cuento se queda fuera por sitio.
#
# Es una limitación declarada, no un lematizador a medias: no se derivan formas
# ni se quitan plurales. Lo que hay es una lista de function words de las dos
# lenguas que el prompt de sistema habla.
VACIAS = {
    "es": {
        "a", "al", "algo", "ahora", "aqui", "aquí", "asi", "así", "cada",
        "como", "cómo", "con", "cual", "cuál", "cuando", "cuándo", "de", "del",
        "desde", "donde", "dónde", "dos", "el", "él", "ella", "ellos", "en",
        "era", "eres", "es", "esa", "ese", "eso", "esta", "está", "este",
        "esto", "estoy", "fue", "ha", "hace", "han", "hay", "he", "la", "las",
        "le", "les", "lo", "los", "mas", "más", "me", "mi", "mis", "mucho",
        "muy", "nada", "ni", "no", "nos", "o", "os", "para", "pero", "por",
        "porque", "que", "qué", "quien", "quién", "se", "ser", "si", "sí",
        "sin", "sobre", "son", "soy", "su", "sus", "tambien", "también",
        "tanto", "te", "tengo", "tiene", "todo", "tu", "tú", "tus", "un",
        "una", "unas", "unos", "y", "ya", "yo",
    },
    "en": {
        "a", "about", "all", "am", "an", "and", "any", "are", "as", "at", "be",
        "been", "but", "by", "can", "could", "did", "do", "does", "for",
        "from", "had", "has", "have", "he", "her", "his", "how", "i", "if",
        "in", "is", "it", "its", "me", "much", "my", "no", "not", "of", "on",
        "or", "our", "out", "she", "so", "some", "than", "that", "the",
        "their", "them", "then", "there", "these", "they", "this", "those",
        "to", "up", "very", "was", "we", "were", "what", "when", "where",
        "which", "who", "why", "will", "with", "would", "you", "your",
    },
}

# Por debajo de esto una palabra no selecciona: son artículos, siglas sueltas y
# restos de puntuación. Se mide en caracteres alfanuméricos, no en longitud
# bruta, para que «C++» no cuente tres.
LARGO_MINIMO = 3


def _terminos(consulta, idioma):
    """Una pregunta -> las palabras que de verdad seleccionan algo.

    ESTE ES EL PASO QUE FALTABA, Y NO ES COSMÉTICO
    ----------------------------------------------
    `memory.buscar` une los términos con espacio, y en FTS5 eso es un AND
    implícito: pide TODAS las palabras. Es la semántica correcta para la caja
    de búsqueda, donde escribir más palabras debe estrechar el resultado.

    Es la equivocada para un turno. «¿cómo se llama mi hija?» contra el
    recuerdo «mi hija se llama Vera» no casa por una sola palabra --«cómo»--
    que no está en el recuerdo y no significa nada. Medido: sin este paso, la
    recuperación devuelve vacío en casi cualquier pregunta redactada como
    pregunta, y lo hace EN SILENCIO. Parece que funciona; nunca recupera.

    Por eso la conversión pregunta -> consulta vive aquí y no en `memory`: la
    caja de búsqueda quiere estrechar, un turno quiere encontrar. Son dos
    trabajos distintos sobre el mismo índice, y mezclarlos rompería el que ya
    funciona.
    """
    fuera = []
    vacias = VACIAS[TX.normalizar(idioma)]
    for bruta in str(consulta or "").split():
        limpia = "".join(ch for ch in bruta if ch.isalnum() or ch in "-_+#")
        if len(limpia) < LARGO_MINIMO:
            continue
        if limpia.lower() in vacias:
            continue
        if limpia.lower() in fuera:
            continue
        fuera.append(limpia.lower())
    return fuera


def _recuerdos(c, consulta, limite, idioma=None):
    """Los recuerdos que casan con ALGUNA palabra. Sin índice, lista vacía.

    Una consulta por término, y se funden los resultados. Se hace así --y no
    con un OR dentro de una sola consulta-- porque `_consulta_fts` entrecomilla
    cada palabra como frase literal para que teclear `C++` o un paréntesis no
    reviente la búsqueda; un `OR` colado ahí viajaría como la palabra "OR". La
    alternativa era relajar esa defensa en `memory` para todos sus llamantes, y
    no se toca una puerta que ya funciona por comodidad de un llamante nuevo.
    El coste es una consulta por palabra sobre un índice local: microsegundos.

    ORDEN: primero los que casan MÁS términos. Un recuerdo que responde a dos
    palabras de la pregunta viene más a cuento que uno que roza una, y con un
    techo de 1.200 caracteres el orden decide qué se queda fuera.

    Que falte FTS5 es una avería del índice, y el índice es opcional: la
    memoria manda sobre él y no al revés. Quien audita tiene
    `memory.estado_busqueda` para saber si hubo cero por avería o cero por no
    haber; quien está hablando no puede quedarse sin turno por eso.
    """
    terminos = _terminos(consulta, idioma)
    if not terminos:
        return []

    aciertos = {}                 # id -> [cuantos terminos, primera posicion]
    filas_por_id = {}
    for termino in terminos:
        try:
            filas = M.buscar(c, termino, limite=limite)
        except M.BusquedaNoDisponible:
            return []
        except Exception:
            # Una memoria a medio migrar no puede tumbar la conversación. Es la
            # misma postura que `asegurar_busqueda`, que devuelve None en vez de
            # levantar cuando el sqlite no trae el módulo.
            return []
        for posicion, f in enumerate(filas):
            ident = f.get("id")
            if ident is None:
                continue
            filas_por_id[ident] = f
            if ident in aciertos:
                aciertos[ident][0] += 1
            else:
                aciertos[ident] = [1, posicion]

    ordenados = sorted(aciertos.items(), key=lambda kv: (-kv[1][0], kv[1][1]))
    fuera = []
    for ident, _ in ordenados[:limite]:
        f = filas_por_id[ident]
        que = (f.get("what") or "").strip()
        if not que:
            continue
        porque = (f.get("why") or "").strip()
        # `NO_DATA` es la ausencia declarada del esquema, no un texto. Pasarla
        # al modelo le enseñaría a repetir un nombre interno.
        if porque and porque != "NO_DATA":
            que = f"{que} ({porque})"
        fuera.append(que)
    return fuera


def _proyectos(c):
    """Solo los activos, con su descripción si la tiene."""
    try:
        filas = PR.listar(c)
    except Exception:
        return []
    fuera = []
    for p in filas:
        if (p.get("estado") or "") != "activo":
            continue
        titulo = (p.get("titulo") or "").strip()
        if not titulo:
            continue
        desc = (p.get("descripcion") or "").strip()
        if desc and desc != "NO_DATA":
            titulo = f"{titulo} · {desc}"
        fuera.append(titulo)
    return fuera


def _cabe(partes, techo):
    """Mete líneas mientras quepan ENTERAS. La que no cabe se queda fuera.

    Devuelve el bloque ya unido. Se mide sobre el texto final --con sus saltos
    de línea-- y no sobre la suma de las piezas, porque el techo es lo que
    viaja, no lo que se pensaba mandar.
    """
    puestas = []
    for parte in partes:
        candidato = "\n".join(puestas + [parte])
        if len(candidato) > techo:
            continue
        puestas.append(parte)
    return "\n".join(puestas)


# --- las dos perillas del Laboratorio ---------------------------------------
#
# Se aceptan HOY aunque su interfaz no exista todavia. El motivo no es adelantar
# trabajo: es que el punto de inyeccion es uno solo, y si manana hay que abrirlo
# otra vez para meter un parametro, se abre con la interfaz ya colgando de el.
# Aqui son dos argumentos con su valor por defecto; ahi serian una migracion.

# LA PROFUNDIDAD · cuanto contexto viaja. El deslizador es 0-100 continuo, asi
# que se mapea por bandas y no por los cinco valores exactos: un 63 tiene que
# significar algo, no caerse al suelo.
#
# `perfil` es nombre e intereses, NO instrucciones -- esas ya viajan dentro del
# prompt de sistema, y meterlas otra vez aqui las mandaria dos veces en cada
# turno pagando dos veces su sitio en la ventana.
PROFUNDIDADES = (
    #  hasta, perfil, memorias, proyectos
    (13,      False,  0,        False),   # 0 · turno aislado
    (38,      True,   0,        False),   # 25 · solo perfil
    (63,      True,   1,        False),   # 50 · perfil + la memoria mas cercana
    (88,      True,   3,        True),    # 75 · perfil + top-3 + proyectos
    (101,     True,   20,       True),    # 100 · todo lo que quepa bajo el techo
)

# EL FOCO · de donde sale. Vocabulario cerrado, como `proyectos.ESTADOS`: fuera
# de la lista no hay foco, hay None, y quien llama decide.
#
# `proyecto` esta declarado y NO implementado, y se dice en vez de fingirse:
# `engrams` no tiene columna de proyecto y `proyectos` no tiene lista de
# engramas -- las dos tablas no se conocen. Filtrar por proyecto no es una
# consulta que falte escribir, es un dato que no existe. Hasta que el esquema
# crezca ese enlace, cae a `memoria` y esta fijado por prueba, para que el dia
# que alguien lo conecte se entere de que habia un contrato esperandolo.
FOCOS = ("memoria", "proyecto", "perfil", "libre")


def _plan(profundidad):
    """La banda que le toca a un valor del deslizador. None = lo de siempre."""
    if profundidad is None:
        return (False, LIMITE, True)
    try:
        v = max(0, min(100, int(profundidad)))
    except (TypeError, ValueError):
        return (False, LIMITE, True)
    for hasta, perfil, memorias, proyectos in PROFUNDIDADES:
        if v < hasta:
            return (perfil, memorias, proyectos)
    return (True, 20, True)


def _perfil(c):
    """Nombre e intereses, si los hay. Las instrucciones no: ya viajan."""
    try:
        p = M.leer_perfil(c)
    except Exception:
        return []
    fuera = []
    for clave in ("nombre", "intereses"):
        valor = (p.get(clave) or "").strip()
        if valor and valor != "NO_DATA":
            fuera.append(valor)
    return fuera


def recuperar(c, consulta, limite=LIMITE, techo=TECHO, idioma=None,
              profundidad=None, foco=None):
    """Lo que la base sabe y viene a cuento, listo para ir delante del modelo.

    Devuelve un bloque de texto, o cadena vacía si no hay nada. La cadena vacía
    es una respuesta completa, no un fallo: quien llama la concatena sin mirar.

    `consulta` es lo que acaba de escribir la persona. La búsqueda es léxica
    --encuentra las palabras que se escribieron, no lo que se quiso decir--, y
    eso es una limitación declarada de `memory.buscar`, no un paso intermedio
    hacia otra cosa.

    `profundidad` (0-100) y `foco` (`FOCOS`) son las dos perillas del
    Laboratorio. Con las dos en None se comporta como el día que nació, que es
    lo que el producto hace hoy: memorias y proyectos activos bajo el techo.
    """
    rot = ROTULOS[TX.normalizar(idioma)]

    quiere_perfil, cuantas, quiere_proyectos = _plan(profundidad)

    # El foco estrecha las fuentes; la profundidad decide cuánto de cada una.
    # Un foco fuera del vocabulario no es un foco: se ignora, y se sigue con lo
    # de siempre, en vez de dejar a alguien sin contexto por una errata.
    if foco in FOCOS:
        if foco == "libre":
            return ""
        if foco == "perfil":
            cuantas, quiere_proyectos, quiere_perfil = 0, False, True
        elif foco in ("memoria", "proyecto"):
            # `proyecto` cae aquí a propósito: ver FOCOS.
            quiere_proyectos, quiere_perfil = False, False
            if not cuantas:
                cuantas = limite

    bloques = []

    if quiere_perfil:
        suyo = _perfil(c)
        if suyo:
            bloques.append((rot["perfil"], suyo))

    recuerdos = _recuerdos(c, consulta, cuantas, idioma) if cuantas else []
    if recuerdos:
        bloques.append((rot["memoria"], recuerdos))

    activos = _proyectos(c) if quiere_proyectos else []
    if activos:
        bloques.append((rot["proyectos"], activos))

    if not bloques:
        return ""

    # El presupuesto se reparte entre los bloques que haya, y el encabezado
    # cuenta: un rótulo sin nada debajo es peor que no ponerlo.
    fuera = []
    resto = techo
    for rotulo, lineas in bloques:
        disponible = resto - len(rotulo) - 1
        if disponible <= 0:
            continue
        cuerpo = _cabe([f"- {l}" for l in lineas], disponible)
        if not cuerpo:
            continue
        trozo = f"{rotulo}\n{cuerpo}"
        fuera.append(trozo)
        resto -= len(trozo) + 2          # los dos saltos que lo separan

    return "\n\n".join(fuera)
