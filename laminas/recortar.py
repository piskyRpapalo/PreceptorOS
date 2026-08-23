#!/usr/bin/env python3
"""Rehace `assets/` a partir de las laminas de `laminas/`.

Esto vivia en la historia de una terminal, que es como decir que no vivia en
ningun sitio: nadie podia repetir un recorte sin volver a adivinar los umbrales.
Aqui estan los numeros que se midieron sobre los ficheros, no estimados.

    python3 laminas/recortar.py

Necesita Pillow. NO es parte del producto -- el producto es biblioteca estandar
y no abre estas laminas jamas; solo lee lo que este script deja en `assets/`.
"""

from __future__ import annotations

import os
from collections import deque

from PIL import Image, ImageChops

AQUI = os.path.dirname(os.path.abspath(__file__))
CASA = os.path.dirname(AQUI)
SALIDA = os.path.join(CASA, "assets")

LAMINAS = {
    "titulo":  "1787443886.png",
    "violeta": "1787443916.png",
    "pizarra": "1787444210.png",
    "iconos":  "1787444220.png",
    "boton":   "1787444225.png",
}


def _lamina(clave):
    return Image.open(os.path.join(AQUI, LAMINAS[clave]))


def quitar_fondo(im, umbral=196, croma=14):
    """Alfa por inundacion desde los bordes, no por color en toda la imagen.

    Las laminas llegaron sin canal alfa: la transparencia venia pintada como un
    damero de DOS tonos casi blancos, con los bordes suavizados entre ellos. Un
    umbral simple se comia el tono claro y dejaba el otro como moteado -- y ese
    moteado entraba en la caja de recorte, que es por lo que el titulo salia
    descentrado en el telefono.

    La condicion buena es "claro Y sin color". El marmol de la pizarra tambien
    es casi blanco, asi que un filtro global de claros la borraria entera; al
    inundar desde fuera, el bronce del marco hace de dique y el interior se
    salva. Y el bronce es calido y saturado, asi que la exigencia de croma bajo
    nunca lo toca.
    """
    im = im.convert("RGBA")
    px = im.load()
    ancho, alto = im.size

    def es_fondo(p):
        r, g, b, a = p
        return a > 0 and min(r, g, b) > umbral and (max(r, g, b) - min(r, g, b)) < croma

    cola = deque([(x, y) for x in range(ancho) for y in (0, alto - 1)]
                 + [(x, y) for y in range(alto) for x in (0, ancho - 1)])
    visto = bytearray(ancho * alto)
    while cola:
        x, y = cola.popleft()
        if not (0 <= x < ancho and 0 <= y < alto) or visto[y * ancho + x]:
            continue
        visto[y * ancho + x] = 1
        if not es_fondo(px[x, y]):
            continue
        px[x, y] = (0, 0, 0, 0)
        cola.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    caja = im.getbbox()
    return im.crop(caja) if caja else im


def cuadrar(im, lado):
    im = im.crop(im.getbbox())
    borde = max(im.size)
    lienzo = Image.new("RGBA", (borde, borde), (0, 0, 0, 0))
    lienzo.paste(im, ((borde - im.width) // 2, (borde - im.height) // 2), im)
    return lienzo.resize((lado, lado), Image.LANCZOS)


def guardar(im, nombre, ancho=None):
    if ancho:
        im.thumbnail((ancho, ancho), Image.LANCZOS)
    ruta = os.path.join(SALIDA, nombre)
    if nombre.endswith(".jpg"):
        im.convert("RGB").save(ruta, quality=74, optimize=True)
    else:
        im.save(ruta, optimize=True)
    print(f"  {nombre:26} {im.size[0]}x{im.size[1]}  {os.path.getsize(ruta) // 1024} kB")


def marmol_teselable(lado=512):
    """La pizarra, recortada bien adentro del marco y cosida para poder repetirse.

    Sin coser, al repetir el fondo aparece una rejilla: la costura de la loseta
    se ve como una linea recta cada 240 pixeles y delata el truco. Se desplaza
    media loseta y se funde la union con una rampa, que es lo que borra la linea.
    """
    im = _lamina("pizarra").convert("RGB")
    ancho, alto = im.size
    # Bien adentro: el borde derecho del recorte grande arrastraba un reflejo
    # calido del bronce y teñia el fondo de la pantalla entera.
    d = im.crop((int(ancho * .26), int(alto * .28),
                 int(ancho * .70), int(alto * .72))).resize((lado, lado), Image.LANCZOS)
    medio = lado // 2
    desplazada = ImageChops.offset(d, medio, medio)
    mascara = Image.new("L", (lado, lado), 255)
    mp = mascara.load()
    for x in range(lado):
        for y in range(lado):
            b = min(abs(x - medio), abs(y - medio))
            mp[x, y] = 255 if b > 40 else int(255 * b / 40)
    return Image.composite(desplazada, d.transpose(Image.FLIP_LEFT_RIGHT), mascara)


def cortar_iconos(im):
    """Cinco iconos en una tira, separados por columnas vacias.

    NO se parte en cinco trozos iguales: medidos, los anchos son 305, 254, 267,
    291 y 333 pixeles. Un corte a ojo cercenaria tres de los cinco.
    """
    alfa = im.split()[3]
    ancho, alto = im.size
    llenas = [any(alfa.getpixel((x, y)) > 24 for y in range(0, alto, 2))
              for x in range(ancho)]
    tramos, inicio = [], None
    for x, hay in enumerate(llenas + [False]):
        if hay and inicio is None:
            inicio = x
        elif not hay and inicio is not None:
            if x - inicio > ancho // 20:
                tramos.append((inicio, x))
            inicio = None
    return tramos


def main():
    print("laminas -> assets")
    guardar(quitar_fondo(_lamina("titulo")), "titulo-aurelius.png", 420)
    guardar(quitar_fondo(_lamina("pizarra")), "marco-marmol.png", 420)
    guardar(quitar_fondo(_lamina("boton")), "boton-hablar.png", 300)
    guardar(marmol_teselable(), "fondo-marmol.jpg")

    tira = quitar_fondo(_lamina("iconos"))
    tramos = cortar_iconos(tira)
    nombres = ["memoria", "frontera", "camino", "perfil", "proyectos"]
    if len(tramos) != len(nombres):
        raise SystemExit(f"esperaba {len(nombres)} iconos y encontre {len(tramos)}; "
                         f"no se corta a ciegas")
    for (a, b), nombre in zip(tramos, nombres):
        icono = cuadrar(tira.crop((a, 0, b, tira.height)), 96)
        guardar(icono, f"icono-{nombre}.png")


if __name__ == "__main__":
    main()
