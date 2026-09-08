#!/usr/bin/env python3
"""El medidor de la app, hablando el esquema que la web publica.

EL DESENCUENTRO QUE CIERRA
--------------------------
`metricas.py` mide once campos y los emite como una lista plana de
`{clave, estado, valor, unidad, como}`. La web publica `medidas.json`, que es
una tabla: `modelo`, `maquina`, una `ventana` y unas `lineas` con backend,
prompt y generacion. Los dos hablan de lo mismo --que va este modelo en esta
maquina-- y no se entendian. El resultado practico: «mide tu equipo y guarda el
resultado» producia un fichero que no encajaba en ningun sitio.

Aqui no se mide nada nuevo. Se TRADUCE, y el contrato del destino manda: los
nombres, las unidades y la regla del hueco son los de `medidas.json`, no los de
esta casa. Traducir hacia el esquema del otro es lo que hace que un tester se
convierta en una fila el dia que el tablon abra.

LA REGLA DEL HUECO, QUE ES LA UNICA QUE IMPORTA
-----------------------------------------------
El contrato lo dice con estas palabras: *«un campo a null se pinta como NO_DATA
con su causa al lado. NUNCA se rellena con una estimacion para que la tabla
quede bonita: una cifra sin procedencia es peor que un hueco»*. Asi que aqui
ningun campo se deduce, se promedia ni se hereda. Lo que no se midio sale
`null` Y ADEMAS deja una linea en `huecos` diciendo por que -- un null sin causa
obliga al que lo lea a adivinar si falto el dato o falto el medidor.

LO QUE ESTA APP APORTA Y LA WEB DECLARA COMO HUECO
--------------------------------------------------
De los cuatro huecos que `medidas.json` declara hoy --media por hora, sha256,
TTFT y firma--, este traductor puede llenar **TTFT**: `metricas` cronometra el
primer trozo de cada turno. No es poca cosa; es la cifra que distingue un
modelo que tarda en arrancar de uno que va lento.

Los otros tres siguen abiertos y se dicen: la media por hora necesita que
alguien cierre ventanas (aqui `muestras` vale 1 y se declara), el sha256
necesita que el fichero del modelo publique su huella, y la firma necesita
Ed25519, que no esta en la biblioteca estandar.

EL BACKEND SE PREGUNTA, NO SE SUPONE
------------------------------------
`lineas[].backend` es obligatorio en el contrato, y con razon: la misma maquina
y el mismo modelo dan cifras que se diferencian en un factor de tres segun
corran en CPU o en la iGPU. Se lee de la columna PROCESSOR de `ollama ps`, que
es quien lo sabe -- no del nombre del proceso ni de una variable de entorno que
alguien puso una vez. Si no hay modelo cargado, no hay backend que declarar y
sale `null` con su causa, que es distinto de decir CPU por defecto.
"""
from __future__ import annotations

import os
import platform
import subprocess

ESQUEMA = 1

# La columna de `ollama ps` que dice donde corre. Se busca por su NOMBRE en la
# cabecera y se corta por posicion, porque las celdas llevan espacios dentro
# --«15 GB», «100% GPU»-- y partir por espacios devolveria trozos.
COLUMNA_BACKEND = "PROCESSOR"


def _ollama_ps():
    try:
        r = subprocess.run(["ollama", "ps"], capture_output=True, text=True,
                           timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def backend():
    """(valor, detalle, causa). `valor` es None cuando no hay nada que declarar.

    Devuelve los tres a la vez a proposito: un backend sin causa cuando falta
    obliga a quien lea la tabla a decidir si el medidor no supo o si no habia
    modelo, y esas dos cosas piden arreglos distintos.
    """
    salida = _ollama_ps()
    if salida is None:
        return None, None, "no se pudo preguntar a `ollama ps`"
    lineas = [l for l in salida.splitlines() if l.strip()]
    if not lineas:
        return None, None, "`ollama ps` no devolvio ni cabecera"
    cabecera = lineas[0]
    if COLUMNA_BACKEND not in cabecera:
        return None, None, f"`ollama ps` no trae columna {COLUMNA_BACKEND}"
    if len(lineas) < 2:
        return None, None, ("no hay ningun modelo cargado ahora mismo: no hay "
                            "backend que declarar. No es CPU por defecto")
    corte = cabecera.index(COLUMNA_BACKEND)
    # El siguiente encabezado marca donde acaba la columna. Si no hay siguiente,
    # llega hasta el final de la linea.
    resto = cabecera[corte + len(COLUMNA_BACKEND):]
    siguiente = len(cabecera)
    for palabra in resto.split():
        siguiente = cabecera.index(palabra, corte + len(COLUMNA_BACKEND))
        break
    celda = lineas[1][corte:siguiente].strip()
    if not celda:
        return None, None, "la columna PROCESSOR vino vacia"
    # «100% GPU» o «53%/47% CPU/GPU»: el reparto es el detalle, la ultima
    # palabra es el backend.
    partes = celda.split()
    return partes[-1], celda if len(partes) > 1 else None, None


# `platform.processor()` NO sirve aqui, y la trampa merece quedar escrita: en
# esta maquina devuelve la cadena «desconocido» --la palabra, traducida por el
# sistema-- en vez de una cadena vacia. O sea que es un valor VERDADERO que no
# dice nada, y un `x or y` no lo caza: se publica «desconocido · 16 hilos ·
# Linux» con toda la pinta de estar medido. Es la misma familia que el cero que
# finge ser un dato.
#
# El modelo de CPU lo sabe `/proc/cpuinfo`, que es donde se pregunta. Si no
# esta --otro sistema, un contenedor sin /proc-- se cae a `platform.machine()`,
# que dice menos y no miente.
def _cpu():
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            for linea in f:
                if linea.lower().startswith("model name"):
                    return linea.split(":", 1)[1].strip()
    except OSError:
        pass
    return ""


def maquina():
    """Una descripcion honesta de esta maquina, con lo que la stdlib sabe.

    No compite con la linea que el nodo soberano publica a mano --«Ryzen 7 255
    · 8 nucleos / 16 hilos · Radeon 780M · 64 GB»--, que la escribio alguien
    que miro el hardware. Esta se arma con lo que `platform` y `os` pueden
    afirmar sin instalar nada, y por eso dice menos. Decir menos y cierto es el
    trato de esta casa.
    """
    trozos = []
    proc = _cpu() or platform.machine()
    if proc:
        trozos.append(proc)
    n = os.cpu_count()
    if n:
        trozos.append(f"{n} hilos")
    trozos.append(platform.system() or "NO_DATA")
    return " · ".join(trozos)


def _valor(paquete, clave):
    """El valor de una clave MEDIDA, o None. Un NO_DATA aqui ya es None."""
    for m in (paquete or {}).get("metricas", []):
        if m.get("clave") == clave:
            return m.get("valor") if m.get("estado") in ("MEDIDO", "NORMA") else None
    return None


def _causa(paquete, clave):
    for m in (paquete or {}).get("metricas", []):
        if m.get("clave") == clave:
            return m.get("causa") or m.get("detalle") or "NO_DATA"
    return f"el medidor no emite «{clave}»"


def desde_paquete(paquete, ventana=None):
    """Traduce un paquete de `metricas` al esquema de `medidas.json`.

    `ventana` --(desde, hasta) en ISO-- se acepta y no se inventa: quien tiene
    los relojes de la sesion es quien llama, no este traductor. Sin ella, la
    ventana sale con sus dos extremos a null y su causa, que es exactamente lo
    que la web ya publica hoy para sus dos filas.
    """
    huecos = []

    nombre = _valor(paquete, "modelo_nombre")
    tam = _valor(paquete, "modelo_tamano_gb")
    if nombre and tam:
        modelo = f"{nombre} · {tam} GB"
    elif nombre:
        modelo = nombre
        huecos.append({"que": "tamano del modelo",
                       "causa": _causa(paquete, "modelo_tamano_gb")})
    else:
        modelo = None
        huecos.append({"que": "modelo",
                       "causa": _causa(paquete, "modelo_nombre")})

    b, detalle, causa_b = backend()
    if b is None:
        huecos.append({"que": "backend", "causa": causa_b})

    gen = _valor(paquete, "tokens_por_segundo")
    if gen is None:
        huecos.append({"que": "generacion (tok/s)",
                       "causa": _causa(paquete, "tokens_por_segundo")})

    ttft = _valor(paquete, "latencia_primer_token_ms")
    if ttft is None:
        huecos.append({"que": "TTFT",
                       "causa": _causa(paquete, "latencia_primer_token_ms")})

    # El prompt eval NO se mide en esta app, y no se deduce del otro numero.
    # Son dos velocidades distintas: en este hardware la de prompt casi triplica
    # a la de generacion, asi que copiar una en la otra no seria aproximar,
    # seria mentir por un factor de tres.
    huecos.append({"que": "prompt (tok/s)",
                   "causa": "esta app cronometra el turno entero, no la fase de "
                            "lectura del prompt por separado. No se deduce de "
                            "la generacion: en este hardware una casi triplica "
                            "a la otra"})
    huecos.append({"que": "media por hora",
                   "causa": "esta medida es UNA pasada, la del ultimo turno. La "
                            "forma ya es la de la ventana para que cerrar horas "
                            "sea volcar, no rehacer"})
    huecos.append({"que": "sha256",
                   "causa": "el fichero del modelo no publica su huella; sin "
                            "ella el nombre no identifica nada"})
    huecos.append({"que": "firma",
                   "causa": "firmar exige Ed25519 y la biblioteca estandar no "
                            "lo trae. La medida viaja sin firmar, y se dice"})

    desde, hasta = (ventana or (None, None))
    return {
        "esquema": ESQUEMA,
        "estado": "MEDIDO" if gen is not None else "NO_DATA",
        "nota": "emitido por la app PreceptorOS en la maquina de quien mide. "
                "Traduccion al esquema de medidas.json, sin medir nada nuevo.",
        "medido": None,
        "maquina": maquina(),
        "modelo": modelo,
        "ventana": {
            "periodo": "1h", "desde": desde, "hasta": hasta, "muestras": 1,
            "causa": "una pasada, no una media: el turno mas reciente",
        },
        "lineas": [{
            "backend": b,
            "detalle": detalle,
            "prompt": None,
            "generacion": gen,
            "ttft": ttft,
            "sha256": None,
            "firma": None,
        }],
        "huecos": huecos,
    }
