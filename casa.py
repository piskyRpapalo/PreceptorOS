"""Dónde vive lo tuyo.

Un solo módulo decide la raíz de configuración, y lo importan todos los que la
necesitan. Si cada uno la calculase por su cuenta, el día que cambie habría
que acertar en varios sitios a la vez -- y bastaría fallar en uno para que la
frontera leyese una configuración y el resto del programa otra.

Regla: `~/.aurelius/` es de la persona. El directorio del programa es del
producto. Nada de lo que la persona ajusta se escribe jamás junto al script.
"""

from pathlib import Path

NOMBRE = ".aurelius"


class CasaInaccesible(RuntimeError):
    """No se puede determinar o crear la carpeta personal. No se inventa otra."""


def raiz():
    """La carpeta personal. Sin adivinar: si el entorno no la declara, se para."""
    try:
        return Path.home() / NOMBRE
    except RuntimeError:
        raise CasaInaccesible(
            "no puedo determinar tu carpeta personal, y no me invento una"
        ) from None


def asegurar(base=None):
    """Crea la casa si falta. Si ya existe, no toca nada de lo que hay dentro."""
    base = base or raiz()
    try:
        base.mkdir(parents=True, exist_ok=True)
    except OSError:
        raise CasaInaccesible(f"no tengo permiso para crear tu casa en {base}") from None
    return base
