"""Dónde vive lo tuyo.

Un solo módulo decide la raíz de configuración, y lo importan todos los que la
necesitan. Si cada uno la calculase por su cuenta, el día que cambie habría
que acertar en varios sitios a la vez -- y bastaría fallar en uno para que la
frontera leyese una configuración y el resto del programa otra.

Regla: `~/.aurelius/` es de la persona. El directorio del programa es del
producto. Nada de lo que la persona ajusta se escribe jamás junto al script.
"""

from pathlib import Path

# Mandato 1 · el renombrado. Con punto delante, como estaba: `.preceptoros` y
# no `preceptoros`. Sin el punto, la carpeta deja de estar oculta y aparece en
# medio del home de la persona junto a Documentos y Descargas -- eso no es
# renombrar, es cambiar donde vive y como se ve, y no estaba en la orden.
NOMBRE = ".preceptoros"

# Los nombres que esta casa ha tenido antes, del mas reciente al mas antiguo.
# Existe por el renombrado del producto (Mandato 1): el dia que `NOMBRE`
# cambie, en el disco de la persona siguen colgando de la casa VIEJA su
# memoria, su perfil, su voz y varios gigas de modelos. Medido el 2026-08-24:
# 2,4 GB en el Beelink y otros 2,4 GB en el Doogee.
#
# Sin esto, cambiar una constante haria que el producto arrancara **como si
# fuera nuevo**. No reventaria -- eso seria mejor -- : ensenaria una memoria
# vacia y una campana sin empezar, y la persona creeria que lo ha perdido todo.
# Un fallo que se parece a un primer arranque es el peor de todos, porque no
# parece un fallo.
NOMBRES_ANTERIORES = (".aurelius",)


class CasaInaccesible(RuntimeError):
    """No se puede determinar o crear la carpeta personal. No se inventa otra."""


def _hogar():
    try:
        return Path.home()
    except RuntimeError:
        raise CasaInaccesible(
            "no puedo determinar tu carpeta personal, y no me invento una"
        ) from None


def heredada():
    """La casa con el nombre viejo, si existe y la nueva todavia no.

    Devuelve None cuando no hay nada que heredar -- que es el caso normal.
    """
    hogar = _hogar()
    if (hogar / NOMBRE).exists():
        return None
    for viejo in NOMBRES_ANTERIORES:
        candidata = hogar / viejo
        if candidata.exists():
            return candidata
    return None


def raiz():
    """La carpeta personal. Sin adivinar: si el entorno no la declara, se para.

    Si el producto se renombro y la casa nueva aun no existe pero la vieja si,
    se ADOPTA la vieja en su sitio. No se mueve nada: mover gigas de modelos es
    una decision de la persona, y a medio camino en un telefono con la bateria
    al 12 % es una forma nueva de perderlo todo. Lo suyo se queda donde esta y
    sigue funcionando; `heredada()` deja que la interfaz lo diga en voz alta y
    ofrezca mudarlo cuando ella quiera.
    """
    return heredada() or (_hogar() / NOMBRE)


def asegurar(base=None):
    """Crea la casa si falta. Si ya existe, no toca nada de lo que hay dentro."""
    base = base or raiz()
    try:
        base.mkdir(parents=True, exist_ok=True)
    except OSError:
        raise CasaInaccesible(f"no tengo permiso para crear tu casa en {base}") from None
    return base
