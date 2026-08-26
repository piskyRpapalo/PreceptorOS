#!/usr/bin/env python3
"""version.py · qué cara está sirviendo esta copia. **Solo biblioteca estándar.**

POR QUÉ EXISTE
--------------
Dos instalaciones de PreceptorOS pueden estar en versiones distintas sin que se
note: la del teléfono guarda el armazón en el service worker y sigue enseñando
la cara de anteayer mientras el servidor ya sirve otra. El síntoma es el peor
posible — todo funciona, y las dos personas creen estar mirando lo mismo.

Así que la versión no es una etiqueta que alguien escribe a mano: es la
**huella del armazón que se sirve**. Cambia exactamente cuando cambia la cara, y
no cambia cuando no. Un número que hay que acordarse de subir es un número que
un día no se sube.

NO SE APOYA EN GIT. Quien descarga el fichero suelto no tiene repositorio, y una
versión que solo existe dentro de un clon no sirve para comparar dos
instalaciones — que es justo para lo que existe esto.
"""
from __future__ import annotations

import hashlib
import os
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
AUSENTE = "NO_DATA"

# El armazón: lo que el navegador guarda y por tanto lo que se puede quedar
# viejo. Si algún día `sw.js` cachea otra cosa, esta lista se queda corta y hay
# que ampliarla — por eso `sw.js` está dentro: al tocarlo, la huella cambia.
ARMAZON = (
    "interface/dashboard.html", "interface/dashboard.css", "interface/dashboard.js",
    "interface/app.html", "interface/app.css", "interface/app.js",
    "interface/compass.css", "interface/compass.js", "interface/sw.js",
    "interface/manifest.json", "assets/compass.svg",
)


def _leer(rel):
    ruta = os.path.join(AQUI, rel)
    try:
        with open(ruta, "rb") as fh:
            return fh.read(), os.stat(ruta).st_mtime
    except OSError:
        return None, None


def version(base=None):
    """`{huella, fecha, ficheros, faltan}`. Lo que falta se dice, no se salta.

    La huella cubre el NOMBRE y el contenido de cada pieza: si un fichero
    desapareciera, dos árboles distintos podrían dar la misma huella sumando
    los bytes que quedan.
    """
    global AQUI
    raiz = base or AQUI
    h = hashlib.sha256()
    reciente, contados, faltan = 0.0, 0, []
    for rel in ARMAZON:
        ruta = os.path.join(raiz, rel)
        try:
            with open(ruta, "rb") as fh:
                crudo = fh.read()
            mtime = os.stat(ruta).st_mtime
        except OSError:
            faltan.append(rel)
            continue
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(crudo)
        contados += 1
        reciente = max(reciente, mtime)
    return {
        "huella": h.hexdigest()[:12] if contados else AUSENTE,
        "fecha": (time.strftime("%Y-%m-%d", time.gmtime(reciente))
                  if reciente else AUSENTE),
        "ficheros": contados,
        "faltan": faltan,
    }


def corta(base=None):
    """`fecha·huella`, o NO_DATA. Lo que se enseña en una esquina."""
    v = version(base)
    if v["huella"] == AUSENTE:
        return AUSENTE
    return f"{v['fecha']}·{v['huella'][:8]}"


if __name__ == "__main__":
    import json
    print(json.dumps(version(), indent=2, ensure_ascii=False))
