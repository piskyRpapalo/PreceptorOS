#!/usr/bin/env python3
"""Une los ocho bustos en una sola tira horizontal. Herramienta de FORJA.

Esto NO es parte del producto: se ejecuta a mano, su salida (`preceptor-up-v2.webp`)
se versiona en `assets/`, y el producto solo ve el fichero resultante. Por eso
puede permitirse Pillow, que el backend no puede. Si algun dia Pillow no esta,
la tira ya generada sigue en el arbol y la app sigue funcionando: una
herramienta de forja ausente no es una averia.

DEPENDENCIA DECLARADA · Pillow (medido: 12.1.1 en `soberano`, 2026-09-02).
Alternativa sin Pillow, si hiciera falta: `ffmpeg -i busto-%d.webp -filter_complex
hstack=inputs=8`. En este nodo NO hay `magick`; `ffmpeg` si esta en /usr/bin.

POR QUE 2048x256 Y NO 4096x512
------------------------------
Los ocho originales miden 256x256 (medido, no supuesto). Escalar x2 con NEAREST
no anade un solo pixel de detalle: solo duplica los que ya hay. Medido el
2026-09-02 sobre la tira real:

    2048x256  webp lossless   469 110 b     <- esta
    4096x512  webp lossless   551 044 b     (+82 KB por cero detalle)

Firmado por el Soberano: «un upscale x2 de un original de 256px es
deshonestidad visual». La tira se guarda a resolucion nativa.

POR QUE WEBP Y NO PNG
---------------------
Misma imagen, sin perdida, medida el mismo dia:

    2048x256  png  optimize   841 754 b
    2048x256  webp lossless   469 110 b     <- esta, -44%

`lossless=True`: los pixeles son identicos, byte a byte, tras decodificar. No
es una compresion con perdida disfrazada de ahorro. El precedente ya estaba en
la casa: `.telon` carga `marble-violet.webp` como fondo CSS desde agosto, asi
que el formato ya viajaba en este mismo fichero de estilos.

EL ORDEN, Y POR QUE ESTE
------------------------
Los ocho ficheros NO son fotogramas de una secuencia: son ocho ESTADOS con
nombre propio. Ponerlos en fila obliga a elegir un orden, y esa eleccion es
narrativa. Se eligio por la curva de pixeles calidos (el ambar del ojo), medida
frame a frame:

    dormido    18      halo       395
    grieta      0      despierto  684
    rompe     413      corazon    634
    ojo       506      oscuro     669

De apagado a encendido. Firmado por el Soberano el 2026-09-02.

EL REPOSO ES EL INDICE 5 (`despierto`), no el ultimo. El despertar del busto
recorre 0..5 y se para ahi; los indices 6 y 7 existen para el telon, que si
llega hasta el final. Quien toque el orden tiene que tocar TAMBIEN las tres
reglas de `dashboard.css` que lo dan por sabido -- por eso las constantes de
abajo llevan el numero al lado.
"""
from __future__ import annotations

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(AQUI), "assets")

# El orden firmado. Cambiar esto rompe `dashboard.css`: ver REPOSO abajo.
ORDEN = ("dormido", "grieta", "rompe", "ojo",
         "halo", "despierto", "corazon", "oscuro")

# Indice del fotograma de reposo del busto del tablero.
#   background-position del reposo = REPOSO / (len(ORDEN) - 1) * 100
#   = 5 / 7 * 100 = 71.4286%   <- este numero vive tambien en dashboard.css
REPOSO = 5

LADO = 256          # medido en los ocho originales, no elegido
SALIDA = "preceptor-up-v2.webp"


def medir(rutas):
    """Ningun fotograma entra sin que se haya mirado su tamano.

    Una tira con un frame de otro tamano no falla: se descuadra en silencio y
    la cara aparece cortada en el telefono de alguien. Eso se para aqui.
    """
    from PIL import Image
    marcos = []
    for r in rutas:
        im = Image.open(r).convert("RGBA")
        if im.size != (LADO, LADO):
            raise SystemExit(
                f"PARADA · {os.path.basename(r)} mide {im.size}, se esperaba "
                f"({LADO}, {LADO}). La tira no se genera con un frame que no "
                f"cuadra: se descuadraria sin dar error.")
        marcos.append(im)
    return marcos


def unir(marcos):
    from PIL import Image
    tira = Image.new("RGBA", (LADO * len(marcos), LADO), (0, 0, 0, 0))
    for i, m in enumerate(marcos):
        tira.paste(m, (i * LADO, 0))
    return tira


def main(argv):
    try:
        import PIL                                          # noqa: F401
    except ImportError:
        raise SystemExit(
            "PARADA · Pillow no esta. Es una herramienta de forja, no del\n"
            "         producto: la tira ya generada sigue en assets/ y la app\n"
            "         funciona igual. Para regenerarla: pip install --user Pillow\n"
            "         o  ffmpeg -i busto-%d.webp -filter_complex hstack=inputs=8")

    rutas = [os.path.join(ASSETS, f"busto-{n}.webp") for n in ORDEN]
    faltan = [r for r in rutas if not os.path.isfile(r)]
    if faltan:
        raise SystemExit("PARADA · no estan: "
                         + ", ".join(os.path.basename(f) for f in faltan))

    tira = unir(medir(rutas))
    destino = os.path.join(ASSETS, SALIDA)
    tira.save(destino, lossless=True, quality=100, method=6)

    n = os.path.getsize(destino)
    print(f"{SALIDA}  {tira.size[0]}x{tira.size[1]}  {n:,} b")
    for i, nombre in enumerate(ORDEN):
        pos = i / (len(ORDEN) - 1) * 100
        marca = "  <- reposo del busto" if i == REPOSO else ""
        print(f"  [{i}] busto-{nombre:<10} background-position: {pos:7.4f}%{marca}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
