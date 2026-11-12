#!/usr/bin/env python3
"""icons_from_emblem.py · the three install icons of the app, generated from the emblem.

    python3 icons_from_emblem.py              # says what would change, touches nothing
    python3 icons_from_emblem.py --escribir   # writes the files
    python3 icons_from_emblem.py --comprobar  # exits 1 if what is published is not what this generates

WHY. Order of the Sovereign, 2026-11-11: the emblem is the face of the preceptor, in dots, the
same on the web and in the app. The source is assets/emblem/preceptor_face.txt, an ASCII drawing
with ten levels of ink (" .:-=+*#%@"). Each character becomes one dot whose size is its level;
the lit eye is violet, as on the canon bust. The web repository holds the same source and the
same drawing code. No font is used: same Pillow, same bytes. Nothing here is painted by hand,
and what is published must be exactly what this generates (test_icons_emblem.py).
"""
import argparse
import hashlib
import io
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent
A = RAIZ / "assets"
FUENTE = RAIZ / "assets" / "emblem" / "preceptor_face.txt"
RAMPA = " .:-=+*#%@"
FONDO = (0x1E, 0x18, 0x26)          # background_color of the manifest
TONO = (0xF2, 0xF5, 0xF7)            # the ink of the hub
OJO = (0xB5, 0x81, 0xE9)             # the lit eye: violet, the bright band of FIRMADO (hue 270) in semantic_table.js


def rejilla():
    """The drawing as rows of ink levels 0..1. A character outside the ramp is an error, not a guess."""
    filas = FUENTE.read_text(encoding="ascii").split("\n")
    while filas and not filas[-1]:
        filas.pop()
    ancho = max(len(f) for f in filas)
    for f in filas:
        raros = set(f) - set(RAMPA)
        if raros:
            raise ValueError("character outside the ramp: %r" % sorted(raros))
    return [[RAMPA.index(c) / 9 for c in f.ljust(ancho)] for f in filas]


def ojo(g):
    """The lit eye: the brightest 5x3 window in the upper right quarter of the face."""
    mejor, donde = -1.0, (0, 0)
    for y in range(len(g) // 5, len(g) // 2):
        for x in range(len(g[0]) // 2, len(g[0]) * 3 // 4):
            s = sum(g[y + j][x + i] for j in range(3) for i in range(5))
            if s > mejor:
                mejor, donde = s, (x + 2, y + 1)
    return donde


def lienzo(g, ancho, alto, frac, recorte=None):
    """Draws at 4x and reduces. A character cell is twice as tall as wide, as in a terminal."""
    from PIL import Image, ImageDraw
    ex, ey = ojo(g)
    if recorte:
        x0, y0, x1, y1 = recorte
        g = [f[x0:x1] for f in g[y0:y1]]
        ex, ey = ex - x0, ey - y0
    cols, filas, s = len(g[0]), len(g), 4
    cw = min(ancho * frac / cols, alto * frac / (filas * 2))
    ch = cw * 2
    ox, oy = (ancho - cols * cw) / 2, (alto - filas * ch) / 2
    im = Image.new("RGB", (ancho * s, alto * s), FONDO)
    d = ImageDraw.Draw(im)
    for y, fila in enumerate(g):
        for x, v in enumerate(fila):
            if not v:
                continue
            cerca = ((x - ex) ** 2 + ((y - ey) * 2) ** 2) ** 0.5 <= 3.2
            r = cw * 0.5 * (0.35 + 0.75 * v) * s
            cx, cy = (ox + (x + 0.5) * cw) * s, (oy + (y + 0.5) * ch) * s
            d.ellipse([cx - r, cy - r * 1.6, cx + r, cy + r * 1.6], fill=OJO if cerca else TONO)
    return im.resize((ancho, alto), Image.LANCZOS)


def paleta():
    """Sixteen fixed colours: twelve steps from background to ink, four from background to the eye."""
    from PIL import Image
    def paso(a, b, t):
        return [round(a[i] + (b[i] - a[i]) * t) for i in range(3)]
    colores = [paso(FONDO, TONO, i / 11) for i in range(12)] + [paso(FONDO, OJO, i / 4) for i in range(1, 5)]
    pal = Image.new("P", (1, 1))
    pal.putpalette(sum(colores, []) + colores[0] * (256 - len(colores)))
    return pal


def png(g, ancho, alto, frac):
    from PIL import Image
    b = io.BytesIO()
    # A fixed palette without dither keeps the eye violet and makes the file a fifth of its true-colour size.
    lienzo(g, ancho, alto, frac).quantize(palette=paleta(), dither=Image.Dither.NONE).save(b, "PNG", optimize=True)
    return b.getvalue()


def ficheros():
    g = rejilla()
    return {
        "icono-192.png": png(g, 192, 192, 0.86),
        "icono-512.png": png(g, 512, 512, 0.86),
        # maskable: Android crops to a circle of radius 0.40 * side; the drawing stays inside it.
        "icono-512-maskable.png": png(g, 512, 512, 0.62),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--escribir", action="store_true")
    ap.add_argument("--comprobar", action="store_true")
    a = ap.parse_args(argv)
    distintos = []
    for nombre, datos in ficheros().items():
        ruta = A / nombre
        igual = ruta.is_file() and ruta.read_bytes() == datos
        if not igual:
            distintos.append(nombre)
        print("%-28s %7d B  %s  %s" % (nombre, len(datos), hashlib.sha256(datos).hexdigest()[:12],
                                      "IGUAL" if igual else "CAMBIA"))
        if a.escribir and not igual:
            ruta.write_bytes(datos)
    if a.comprobar:
        return 1 if distintos else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
