"""Dónde vive lo tuyo.

Un solo módulo decide la raíz de configuración, y lo importan todos los que la
necesitan. Si cada uno la calculase por su cuenta, el día que cambie habría
que acertar en varios sitios a la vez -- y bastaría fallar en uno para que la
frontera leyese una configuración y el resto del programa otra.

Regla: `~/.preceptoros/` es de la persona. El directorio del programa es del
producto. Nada de lo que la persona ajusta se escribe jamás junto al script.
"""

from pathlib import Path

# La configuración personal vive en una carpeta oculta del hogar.
NOMBRE = ".preceptoros"

# No se buscan carpetas heredadas con identificadores retirados del árbol.
# La persona conserva y migra sus datos localmente antes de iniciar esta versión.
NOMBRES_ANTERIORES = ()


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
    """No hay una ruta heredada pública que el producto pueda adoptar."""
    hogar = _hogar()
    if (hogar / NOMBRE).exists():
        return None
    for viejo in NOMBRES_ANTERIORES:
        candidata = hogar / viejo
        if candidata.exists():
            return candidata
    return None


def raiz():
    """Devuelve la ubicación canónica de los datos de la persona."""
    return heredada() or (_hogar() / NOMBRE)


def asegurar(base=None):
    """Crea la casa si falta. Si ya existe, no toca nada de lo que hay dentro."""
    base = base or raiz()
    try:
        base.mkdir(parents=True, exist_ok=True)
    except OSError:
        raise CasaInaccesible(f"no tengo permiso para crear tu casa en {base}") from None
    return base
