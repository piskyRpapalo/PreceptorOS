"""Descarga verificada de piezas grandes -- cerebro y voz -- con la biblioteca
estándar y nada más.

Contrato:

* Nada se da por bueno hasta que su huella coincide. El fichero final no
  existe antes de esa comprobación: se escribe en `.partial` y se renombra.
* Ningún mensaje de éxito precede a la comprobación que lo justifica.
* Cualquier fallo -- red, espacio, huella, transporte -- deja el destino como
  estaba. No hay estados a medias.
* Sin red no hay excepción que mate el programa: hay ausencia declarada.

Las cifras que se anuncian antes de descargar son las declaradas en el
catálogo. Si el servidor anuncia otro tamaño, se para: haber prometido un
peso y bajar otro convierte el aviso en decoración.
"""

import hashlib
import os
import shutil
import sys
import urllib.error
import urllib.request
from collections import namedtuple

import casa as _casa

BLOQUE = 65536
MARGEN_DISCO = 64 * 1024 * 1024
AGENTE = "aurelius/1.0 (+stdlib urllib)"
TIEMPO_ESPERA = 30

# nombre     : lo que se le dice a la persona
# url        : origen, obligatoriamente https
# sha256     : huella publicada, minúsculas
# bytes      : peso declarado en el catálogo, o None si no se publica
# licencia   : texto corto que se muestra antes de pedir el sí
# destino    : ruta relativa a la casa
Pieza = namedtuple("Pieza", "nombre url sha256 bytes licencia destino")


class DescargaFallida(RuntimeError):
    """La pieza no está disponible. El destino queda como estaba."""


class TransporteInseguro(DescargaFallida):
    """El origen no es https, o una redirección degradó el transporte."""


class EspacioInsuficiente(DescargaFallida):
    """No cabe. Se declara antes de escribir un solo byte."""


class HuellaNoCoincide(DescargaFallida):
    """Lo descargado no es lo publicado. Se borra."""


class SinRed(DescargaFallida):
    """No se pudo alcanzar el origen. Ausencia, no avería."""


def casa():
    """Raíz de configuración. La decide casa.py; aquí solo se traduce el fallo."""
    try:
        return _casa.raiz()
    except _casa.CasaInaccesible as e:
        raise DescargaFallida(str(e)) from None


def asegurar_casa(raiz=None):
    """Crea la casa si falta. No toca nada si ya existe."""
    try:
        return _casa.asegurar(raiz)
    except _casa.CasaInaccesible as e:
        raise DescargaFallida(str(e)) from None


def humano(n):
    """Bytes a una unidad legible. None se dice NO_DATA, no se estima."""
    if n is None:
        return "NO_DATA"
    for unidad in ("B", "KiB", "MiB", "GiB"):
        if n < 1024 or unidad == "GiB":
            return f"{n:.1f} {unidad}" if unidad != "B" else f"{n} B"
        n /= 1024.0


def barra(leidos, total, ancho=32):
    """Una línea de progreso. Sin total no hay porcentaje: hay bytes."""
    if not total:
        return f"  {humano(leidos)} de NO_DATA"
    hechos = min(ancho, int(ancho * leidos / total))
    fraccion = 100.0 * leidos / total
    return f"  [{'#' * hechos}{'.' * (ancho - hechos)}] {fraccion:5.1f} %  {humano(leidos)}"


def huella_fichero(ruta, bloque=BLOQUE):
    """sha256 leyendo por trozos. Un fichero de gigas no entra en memoria."""
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for trozo in iter(lambda: f.read(bloque), b""):
            h.update(trozo)
    return h.hexdigest()


def comprobar_espacio(raiz, necesarios):
    """Se pregunta al disco antes de empezar, no cuando ya no cabe."""
    if not necesarios:
        return None
    libre = shutil.disk_usage(raiz).free
    if libre < necesarios + MARGEN_DISCO:
        raise EspacioInsuficiente(
            f"hacen falta {humano(necesarios + MARGEN_DISCO)} y hay {humano(libre)}"
        )
    return libre


def abrir(url):
    """Abre el origen y devuelve (flujo, total, url_final).

    Se exige https en la petición y también en la url final: urllib sigue las
    redirecciones, y una redirección puede degradar el transporte sin avisar.
    """
    if not url.lower().startswith("https://"):
        raise TransporteInseguro("el origen debe ser https")
    peticion = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    try:
        flujo = urllib.request.urlopen(peticion, timeout=TIEMPO_ESPERA)
    except urllib.error.URLError as e:
        raise SinRed(f"no alcanzo el origen: {e.reason}") from None
    final = getattr(flujo, "url", url)
    if not str(final).lower().startswith("https://"):
        flujo.close()
        raise TransporteInseguro("una redirección salió de https")
    crudo = flujo.headers.get("Content-Length") if flujo.headers else None
    try:
        total = int(crudo) if crudo is not None else None
    except ValueError:
        total = None
    return flujo, total, str(final)


def escribir_flujo(flujo, parcial, total=None, salida=None, bloque=BLOQUE):
    """Vuelca el flujo al fichero parcial mostrando progreso.

    Devuelve (bytes_escritos, huella). No decide nada: no compara, no renombra
    y no felicita. Separado a propósito para poder probarlo sin red.
    """
    h = hashlib.sha256()
    leidos = 0
    ultimo = -1
    with open(parcial, "wb") as destino:
        for trozo in iter(lambda: flujo.read(bloque), b""):
            destino.write(trozo)
            h.update(trozo)
            leidos += len(trozo)
            if salida is not None:
                paso = leidos // (4 * 1024 * 1024)
                if paso != ultimo:
                    ultimo = paso
                    salida.write("\r" + barra(leidos, total))
                    salida.flush()
        destino.flush()
        os.fsync(destino.fileno())
    if salida is not None:
        salida.write("\r" + barra(leidos, total) + "\n")
        salida.flush()
    return leidos, h.hexdigest()


def anunciar(pieza, salida=sys.stdout):
    """Lo que se dice ANTES de pedir el sí. Ninguna cifra se estima."""
    salida.write(
        f"[AURELIUS] Pieza     : {pieza.nombre}\n"
        f"[AURELIUS] Licencia  : {pieza.licencia}\n"
        f"[AURELIUS] Peso      : {humano(pieza.bytes)}\n"
        f"[AURELIUS] SHA256    : {pieza.sha256}\n"
        f"[AURELIUS] Origen    : {pieza.url}\n"
        "[AURELIUS] Si interrumpes la descarga, se empieza de cero.\n"
    )
    salida.flush()


def descargar(pieza, raiz=None, salida=sys.stderr, forzar=False):
    """Descarga, verifica y coloca. Devuelve la ruta final.

    El orden importa y es el de D73: primero se comprueba, después se dice.
    """
    raiz = asegurar_casa(raiz)
    final = raiz / pieza.destino
    final.parent.mkdir(parents=True, exist_ok=True)

    if final.exists() and not forzar:
        if huella_fichero(final) == pieza.sha256:
            return final
        raise HuellaNoCoincide(
            f"{final} existe y su huella no es la publicada; no lo toco"
        )

    comprobar_espacio(final.parent, pieza.bytes)
    parcial = final.with_suffix(final.suffix + ".partial")

    flujo, total, _ = abrir(pieza.url)
    if pieza.bytes is not None and total is not None and total != pieza.bytes:
        flujo.close()
        raise DescargaFallida(
            f"el origen anuncia {humano(total)} y el catálogo dice "
            f"{humano(pieza.bytes)}; no descargo lo que no supe prometer"
        )
    try:
        escritos, obtenida = escribir_flujo(flujo, parcial, total, salida)
    except BaseException:
        # BaseException a propósito: KeyboardInterrupt entra aquí. No se traga
        # -- se relanza -- pero no se deja basura de gigas en el disco.
        parcial.unlink(missing_ok=True)
        raise
    finally:
        flujo.close()

    if total is not None and escritos != total:
        parcial.unlink(missing_ok=True)
        raise DescargaFallida(
            f"llegaron {humano(escritos)} de {humano(total)}: descarga truncada"
        )
    if obtenida != pieza.sha256:
        parcial.unlink(missing_ok=True)
        raise HuellaNoCoincide(
            f"esperaba {pieza.sha256[:16]}... y obtuve {obtenida[:16]}..."
        )

    os.replace(parcial, final)
    return final


def presente(pieza, raiz=None):
    """¿Está la pieza, y es la buena? El disco manda sobre cualquier bandera.

    Una bandera en un json dice lo que era verdad cuando se escribió. Si el
    fichero se borró o se cambió, la bandera miente y el disco no.
    """
    try:
        raiz = raiz or casa()
    except DescargaFallida:
        return False
    ruta = raiz / pieza.destino
    if not ruta.is_file():
        return False
    return huella_fichero(ruta) == pieza.sha256
