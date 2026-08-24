#!/usr/bin/env python3
"""path.py · D2 · los caminos de aprendizaje. **Solo stdlib.**

QUÉ ES Y QUÉ NO
---------------
Un *path* es una secuencia de pasos que la persona puede seguir para aprender
algo: terminal, Python, lo que sea. Vive en un JSON, se lee con `json` y se
enseña tal cual.

**No es El Camino.** El Camino (M0-M7) es la campaña del producto y tiene ocho
peldaños, ni uno más. Un path es contenido que la persona elige, añade o borra
sin que la campaña cambie. Por eso vive en un fichero suyo y no en `memory.db`:
un path no es un recuerdo, es material de estudio, y borrarlo no debe rozar la
regla de cero DELETE que protege lo que ella escribió.

**No invoca al modelo, y no toca la red.** Un path que necesitara un LLM para
leerse dejaría de poder leerse en la mitad de las máquinas donde este producto
tiene que funcionar. Hay una prueba que lo vigila.

DÓNDE VIVE, Y POR QUÉ ASÍ
-------------------------
Dos fuentes, y la de la persona manda:

- `paths/` junto al programa -- los que vienen con el producto. **Solo lectura.**
- `casa.raiz()/path/` -- los suyos. Si repite un `id`, gana el suyo.

No se copian los de fábrica a su casa en el primer arranque. Escribir en su
carpeta algo que no pidió es empezar a decidir por ella, y además convierte una
mejora del producto en una copia vieja que ya nadie actualiza.

LO QUE ROMPE, ROMPE EN VOZ ALTA
-------------------------------
Un path mal formado se nombra y se salta; no desaparece en silencio. Un
catálogo que esconde lo roto enseña menos de lo que hay y no hay forma de
notarlo desde dentro.
"""
from __future__ import annotations

import json
import os

import casa as _casa

CARPETA = "path"
EXTENSION = ".json"
AUSENTE = "NO_DATA"

# El `id` se usa para encontrar un fichero. Sin esta lista, un `id` como
# `../../.ssh/id_ed25519` haría que `leer()` sirviera cualquier cosa del disco.
# No es paranoia: el `id` llega desde la interfaz, y la interfaz lo recibe de
# fuera.
ID_VALIDO = set("abcdefghijklmnopqrstuvwxyz0123456789-_")

CAMPOS_PASO = ("porque", "hacer", "comprobar")


class PathIlegible(ValueError):
    """El fichero no es un path válido. Se dice cuál y por qué."""


def carpeta_persona(base=None):
    """La carpeta de paths de la persona. No la crea."""
    return (base or _casa.raiz()) / CARPETA


def carpeta_producto():
    """Los que vienen de fábrica. Junto al programa, y de solo lectura."""
    from pathlib import Path
    return Path(os.path.dirname(os.path.abspath(__file__))) / "paths"


def asegurar(base=None):
    """Crea la carpeta de la persona si falta. No escribe nada dentro."""
    destino = carpeta_persona(base)
    destino.mkdir(parents=True, exist_ok=True)
    return destino


def _id_limpio(ident):
    ident = (ident or "").strip().lower()
    if not ident or not set(ident) <= ID_VALIDO:
        return None
    return ident


def validar(datos):
    """Devuelve la lista de problemas. Vacía significa válido.

    Devuelve problemas en vez de levantar a la primera: quien escribe un path
    quiere ver TODO lo que le falta de una vez, no descubrirlo de uno en uno.
    """
    problemas = []
    if not isinstance(datos, dict):
        return ["el fichero no contiene un objeto JSON"]

    if _id_limpio(datos.get("id")) is None:
        problemas.append(
            "`id` ausente o con caracteres no permitidos "
            "(solo minúsculas, dígitos, guion y guion bajo)")
    if not str(datos.get("titulo", "")).strip():
        problemas.append("`titulo` ausente: un path sin título no se puede elegir")

    pasos = datos.get("pasos")
    if not isinstance(pasos, list) or not pasos:
        problemas.append("`pasos` ausente o vacío: un path sin pasos no es un path")
        return problemas

    vistos = set()
    for i, paso in enumerate(pasos):
        donde = f"paso {i + 1}"
        if not isinstance(paso, dict):
            problemas.append(f"{donde}: no es un objeto")
            continue
        pid = _id_limpio(paso.get("id"))
        if pid is None:
            problemas.append(f"{donde}: `id` ausente o con caracteres no permitidos")
        elif pid in vistos:
            problemas.append(f"{donde}: `id` repetido (`{pid}`)")
        else:
            vistos.add(pid)
        if not str(paso.get("titulo", "")).strip():
            problemas.append(f"{donde}: `titulo` ausente")
    return problemas


def _normalizar(datos):
    """Rellena lo opcional con NO_DATA. Lo que falta se ve; no se disimula."""
    datos = dict(datos)
    datos["id"] = _id_limpio(datos.get("id"))
    datos["titulo"] = str(datos.get("titulo", "")).strip()
    datos["idioma"] = str(datos.get("idioma") or AUSENTE).strip()
    datos["fuente"] = str(datos.get("fuente") or AUSENTE).strip()
    datos["version"] = datos.get("version", AUSENTE)
    pasos = []
    for paso in datos.get("pasos", []):
        p = dict(paso)
        p["id"] = _id_limpio(p.get("id"))
        p["titulo"] = str(p.get("titulo", "")).strip()
        for campo in CAMPOS_PASO:
            valor = str(p.get(campo) or "").strip()
            p[campo] = valor or AUSENTE
        pasos.append(p)
    datos["pasos"] = pasos
    return datos


def _cargar(ruta):
    """Lee y valida un fichero. Levanta PathIlegible con el motivo entero."""
    try:
        with open(ruta, encoding="utf-8") as f:
            datos = json.load(f)
    except json.JSONDecodeError as e:
        raise PathIlegible(f"{os.path.basename(ruta)}: JSON inválido ({e})") from None
    except OSError as e:
        raise PathIlegible(f"{os.path.basename(ruta)}: no se pudo leer ({e})") from None

    problemas = validar(datos)
    if problemas:
        raise PathIlegible(
            f"{os.path.basename(ruta)}: " + " · ".join(problemas))
    return _normalizar(datos)


def _fuentes(base=None):
    """(carpeta, etiqueta) de menos a más prioridad. La persona va la última."""
    return ((carpeta_producto(), "producto"),
            (carpeta_persona(base), "tuyo"))


def catalogo(base=None):
    """Todos los paths legibles, y aparte los que no lo son.

    Devuelve `{"paths": [...], "rotos": [...]}`. Los rotos llevan su motivo:
    un catálogo que los escondiera enseñaría menos de lo que hay sin que se
    pudiera notar desde dentro.
    """
    encontrados = {}
    rotos = []
    for carpeta, etiqueta in _fuentes(base):
        if not carpeta.is_dir():
            continue
        for fichero in sorted(carpeta.glob("*" + EXTENSION)):
            try:
                datos = _cargar(fichero)
            except PathIlegible as e:
                rotos.append({"fichero": str(fichero), "fuente": etiqueta,
                              "motivo": str(e)})
                continue
            datos["fuente_carpeta"] = etiqueta
            datos["ruta"] = str(fichero)
            # La persona pisa al producto: si se molestó en escribir un path
            # con el mismo id, es que quiere el suyo.
            encontrados[datos["id"]] = datos
    return {"paths": [encontrados[k] for k in sorted(encontrados)],
            "rotos": rotos}


def listar(base=None, idioma=None):
    """Resumen para elegir: id, título, cuántos pasos y de dónde sale."""
    cat = catalogo(base)
    fuera = []
    for p in cat["paths"]:
        if idioma is not None and p["idioma"] != idioma:
            continue
        fuera.append({"id": p["id"], "titulo": p["titulo"],
                      "idioma": p["idioma"], "pasos": len(p["pasos"]),
                      "fuente": p["fuente_carpeta"]})
    return fuera


def leer(ident, base=None):
    """Un path entero por su `id`, o None si no está.

    El `id` se limpia ANTES de tocar el disco: se usa para encontrar un
    fichero, y llega desde la interfaz.
    """
    limpio = _id_limpio(ident)
    if limpio is None:
        return None
    for p in catalogo(base)["paths"]:
        if p["id"] == limpio:
            return p
    return None


def vista(base=None, idioma=None):
    """Texto plano para enseñarlo. Sin datos dice que no hay, no un cero."""
    cat = catalogo(base)
    filas = listar(base, idioma)
    if not filas and not cat["rotos"]:
        return f"paths · {AUSENTE} (no hay ninguno todavía)"
    lineas = []
    for f in filas:
        lineas.append(f"  {f['id']:<28} {f['pasos']:>2} pasos · "
                      f"{f['idioma']} · {f['fuente']}  {f['titulo']}")
    if not filas:
        lineas.append(f"  {AUSENTE} (ninguno legible)")
    for r in cat["rotos"]:
        lineas.append(f"  ROTO · {r['motivo']}")
    return "\n".join(lineas)
