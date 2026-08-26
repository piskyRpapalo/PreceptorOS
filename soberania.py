"""El guardian. Que puede hacer esta instalacion, y quien lo decide.

Un solo modulo responde a la pregunta «¿puedo hacer esto?», y lo hace de una
forma que no admite matices: **ante cualquier duda, no**. Sin fichero, con el
fichero roto, con el disco mudo, con una capacidad que nadie declaro, con el
argumento de linea de ordenes ilegible -- todos esos caminos terminan en el
mismo sitio, el nivel 0, y ninguno termina en una excepcion.

Que no lance importa tanto como que devuelva 0. Un modulo de permisos que
revienta deja al que llama decidiendo por su cuenta en mitad de un `except`, y
ahi es donde se cuelan los permisos que nadie concedio. Aqui la API publica
devuelve valores seguros y no propaga nada hacia fuera.

Y no hay `if` anidados que mantener en el resto del arbol: quien necesite un
permiso lo declara UNA vez, encima de su funcion, con `@exige("...")`. El
guardian es este fichero y nadie mas. Si manana la regla cambia, cambia aqui.

Solo biblioteca estandar. Ni un socket, ni una herramienta de fuera, ni una
sola linea que salga de la maquina: este modulo decide si se sale, asi que no
puede ser el que sale.
"""

import functools
import sys

import estado as _estado

# Lo que se devuelve cuando no hay dato. Se expone aqui para que los modulos
# de manana no cada uno el suyo: un hueco declarado con cinco nombres
# distintos deja de poder buscarse.
NO_DATA = "NO_DATA"

SANTUARIO = _estado.SANTUARIO
NIVEL_MAXIMO = _estado.NIVEL_MAXIMO

# El corte por linea de ordenes. Vale para el proceso entero y no escribe nada:
# es el que se usa cuando se quiere arrancar cortado una sola vez sin dejar
# rastro que luego haya que acordarse de quitar.
BANDERA = "--santuario"

# Cada capacidad con el nivel minimo que la concede. Es una tabla y no una
# cadena de `if` a proposito: se lee de un vistazo, y anadir una capacidad es
# anadir una linea, no tocar la logica del guardian.
#
# El nivel 0 no aparece, y no es un olvido: lo que el santuario ya hace no pide
# permiso. Meterlo en esta tabla lo volveria condicional, y el suelo dejaria de
# ser suelo.
CAPACIDADES = {
    # Nivel 1 · el arnes. Un modelo que vive en este disco y responde en esta
    # maquina. No sale de aqui.
    "inferencia_local": 1,
    # Nivel 2 · la expansion. Todo lo que cruza el borde de la maquina, se
    # llame como se llame. Un solo permiso para todo lo que sale, porque lo que
    # importa no es a donde va sino que se va.
    "recursos_externos": 2,
    "sincronizacion": 2,
    # Nivel 3 · el ecosistema. Vive fuera del producto y se engancha; el nucleo
    # no sabe que existe.
    "complementos": 3,
    "hardware_local": 3,
}

# Corte pedido en este proceso. Una vez puesto manda hasta que alguien llame a
# `salir_de_santuario()` -- que es un gesto explicito y no ocurre solo.
_CORTADO = False


def _por_bandera(argv=None):
    """¿Viene el corte en la linea de ordenes? Un argv que no se deja leer, si.

    El `except` es ancho y es deliberado: aqui no se distingue entre clases de
    fallo. Cualquier cosa que impida saber si el corte estaba pedido se
    resuelve como que si lo estaba.
    """
    try:
        candidatos = list(sys.argv[1:] if argv is None else argv)
    except Exception:                                            # noqa: BLE001
        return True
    return BANDERA in candidatos


def santuario_activo(base=None, argv=None):
    """¿Esta cortado ahora mismo? Por proceso, por bandera o por centinela."""
    if _CORTADO:
        return True
    if _por_bandera(argv):
        return True
    try:
        return bool(_estado.santuario_forzado(base))
    except Exception:                                            # noqa: BLE001
        return True


def obtener_nivel(base=None, argv=None):
    """El nivel en vigor: un entero de 0 a 3, y 0 ante cualquier duda.

    Nunca devuelve None, nunca devuelve un booleano y nunca lanza. Si el
    numero que llega del estado no es un entero en rango, no es un nivel: es
    una ausencia de dato, y una ausencia de dato no concede nada.
    """
    if santuario_activo(base, argv):
        return SANTUARIO
    try:
        n = _estado.nivel(base)
    except Exception:                                            # noqa: BLE001
        return SANTUARIO
    if isinstance(n, bool) or not isinstance(n, int):
        return SANTUARIO
    if n < SANTUARIO or n > NIVEL_MAXIMO:
        return SANTUARIO
    return n


def exigido(capacidad):
    """El nivel minimo de una capacidad. Una que nadie declaro pide mas que el maximo.

    Devolver `NIVEL_MAXIMO + 1` y no `None` tiene un motivo: asi el que compara
    no necesita un caso especial, y no hay nivel alcanzable que la conceda. Un
    nombre mal escrito se queda fuera en vez de colarse.
    """
    try:
        return CAPACIDADES.get(capacidad, NIVEL_MAXIMO + 1)
    except Exception:                                            # noqa: BLE001
        return NIVEL_MAXIMO + 1


def verificar_permiso(capacidad, base=None, argv=None):
    """¿Concede esta instalacion esta capacidad concreta? True o False, nunca otra cosa."""
    return obtener_nivel(base, argv) >= exigido(capacidad)


def causa(capacidad, base=None, argv=None):
    """Por que no hay dato, en una linea que se puede enseñar.

    Cadena vacia si la capacidad SI esta concedida -- no hay nada que declarar.
    Si no lo esta, empieza por `NO_DATA` y dice que falta. No dice «fallo» ni
    nombra la red: no ha fallado nada, simplemente esta instalacion no llega
    ahi, y confundir las dos cosas es lo que hace que la gente busque averias
    que no existen.
    """
    if verificar_permiso(capacidad, base, argv):
        return ""
    pide = exigido(capacidad)
    if pide > NIVEL_MAXIMO:
        return f"{NO_DATA} · capacidad no declarada: «{capacidad}»"
    return (f"{NO_DATA} · «{capacidad}» pide nivel {pide} · "
            f"esta instalacion esta en el {obtener_nivel(base, argv)}")


def modo_santuario(base=None):
    """Colapsa al 0. En este proceso ya, y en el disco si el disco deja.

    Primero el corte en memoria y despues el centinela, y ese orden importa: si
    el disco esta lleno o de solo lectura, el corte ya esta hecho igualmente.
    Un interruptor que depende de poder escribir para apagar no es un
    interruptor.
    """
    global _CORTADO
    _CORTADO = True
    try:
        centinela = _estado.ruta_centinela(base)
        centinela.parent.mkdir(parents=True, exist_ok=True)
        centinela.write_text("", encoding="utf-8")
    except Exception:                                            # noqa: BLE001
        pass
    return SANTUARIO


def salir_de_santuario(base=None):
    """El camino de vuelta, que no es automatico: alguien tiene que pedirlo.

    Levanta el corte y quita el centinela. **No sube el nivel**: devuelve lo
    que estuviera declarado, que puede seguir siendo 0. Nada en este modulo
    sube un nivel -- eso lo firma una persona, en otro sitio.

    Si el corte vino por `BANDERA`, sigue puesto: la bandera gobierna el
    proceso entero y no se retira desde dentro.
    """
    global _CORTADO
    _CORTADO = False
    try:
        _estado.ruta_centinela(base).unlink()
    except Exception:                                            # noqa: BLE001
        pass
    return obtener_nivel(base)


def exige(capacidad, si_no=NO_DATA):
    """El patron de intercepcion: la funcion envuelta NO corre si el nivel no da.

    Se declara una vez y se olvida:

        @exige("recursos_externos")
        def traer_algo_de_fuera(...): ...

    Sin permiso devuelve `si_no` -- `NO_DATA` por defecto -- y el cuerpo no se
    ejecuta, asi que no hay a medio hacer nada que deshacer. Que el guardian
    este ARRIBA y no dentro es lo que impide que el arbol se llene de
    comprobaciones repetidas que un dia dejan de estar de acuerdo entre si.
    """
    def envoltorio(fn):
        @functools.wraps(fn)
        def guardado(*args, **kwargs):
            if not verificar_permiso(capacidad):
                return si_no
            return fn(*args, **kwargs)
        guardado.capacidad = capacidad
        return guardado
    return envoltorio


def _informe(base=None, argv=None):
    n = obtener_nivel(base, argv)
    lineas = [f"nivel en vigor: {n}"]
    if santuario_activo(base, argv):
        lineas.append("santuario activo · el corte manda sobre lo declarado")
    for capacidad in sorted(CAPACIDADES):
        concedida = verificar_permiso(capacidad, base, argv)
        marca = "si" if concedida else "no"
        lineas.append(f"  [{marca}] {capacidad} (pide {CAPACIDADES[capacidad]})")
    return "\n".join(lineas)


if __name__ == "__main__":
    orden = sys.argv[1] if len(sys.argv) > 1 else ""
    if orden == BANDERA:
        modo_santuario()
        print("santuario · nivel 0")
        print(_informe())
    elif orden == "--salir-santuario":
        print(f"corte retirado · nivel declarado: {salir_de_santuario()}")
    else:
        print(_informe())
