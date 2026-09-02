#!/usr/bin/env python3
"""Pruebas de `calibrar_caras.py`. Se escriben ANTES que el codigo del grupo.

No prueban "que salga una cara bonita" -- eso lo juzga el ojo del Soberano
sobre la lamina. Prueban las cuatro invariantes que, si se rompen, producen
exactamente el salto visual que esta herramienta existe para matar:

  1. una rejilla 2x2 se parte en cuatro baldosas y en orden de lectura
  2. el damero pintado del fondo se va, y la figura se queda
  3. una mota suelta en un borde no puede definir el encuadre
  4. todos los fotogramas de un grupo salen con la misma transformacion:
     misma lona, y la cabeza de referencia en el mismo sitio

La cuarta es la que importa. Calibrar fotograma a fotograma alinea cada uno
consigo mismo y desalinea la secuencia: la cabeza late. Aqui se comprueba con
tres lonas sinteticas que comparten cabeza y cambian de escombro, midiendo el
centro de masa de la mitad donde esta la cabeza.

Y no basta con ver el grupo en verde: la ultima comprobacion mide TAMBIEN el
camino de uno en uno, y exige que ese SI se mueva. Una invariante que se
cumpliria igual sin la herramienta no esta probando la herramienta.

Todo vive dentro de funciones a proposito. La primera version corria en el
cuerpo del modulo y terminaba en `sys.exit`, y eso revienta a pytest con un
INTERNALERROR al importarlo -- el gate del repo dejaba de correr entero por
culpa de una prueba. Se corre igual a mano:

    python3 herramientas/test_calibrar_caras.py
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import calibrar_caras as cc


def damero(lado, claro=(255, 255, 255), oscuro=(227, 227, 224), celda=16):
    """El fondo que traen los originales: no es transparencia, es un dibujo."""
    im = Image.new("RGB", (lado, lado), claro)
    d = ImageDraw.Draw(im)
    for y in range(0, lado, celda):
        for x in range(0, lado, celda):
            if (x // celda + y // celda) % 2:
                d.rectangle([x, y, x + celda - 1, y + celda - 1], fill=oscuro)
    return im


def cabeza(lado, cx, cy, r, color=(40, 40, 48)):
    """Una figura opaca sobre el damero, con el centro donde se le diga."""
    im = damero(lado)
    ImageDraw.Draw(im).ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    return im


def centro_opaco(im):
    """Centro de masa de lo opaco en la MITAD IZQUIERDA.

    La izquierda es donde esta la cabeza en las tres lonas; el escombro solo
    crece hacia la derecha. Si la transformacion es la misma, este punto no se
    mueve ni un pixel.
    """
    a = im.getchannel("A")
    w, h = a.size
    sx = sy = n = 0
    for y in range(h):
        for x in range(w // 2):
            if a.getpixel((x, y)) > 8:
                sx += x
                sy += y
                n += 1
    return (round(sx / n, 1), round(sy / n, 1)) if n else None


def comprobar(hablar=True):
    """Corre las nueve comprobaciones. Devuelve la lista de fallos."""
    fallos = []

    def caso(nombre, cond, detalle=""):
        if hablar:
            print(f"  {'ok   ' if cond else 'FALLO'} {nombre}"
                  + (f" · {detalle}" if detalle else ""))
        if not cond:
            fallos.append(nombre)

    # 1 · la rejilla se parte en orden de lectura
    rejilla = Image.new("RGB", (64, 64))
    for i, (c, f) in enumerate([(0, 0), (1, 0), (0, 1), (1, 1)]):
        rejilla.paste(Image.new("RGB", (32, 32), (i * 60, 0, 0)), (c * 32, f * 32))
    baldosas = cc.partir(rejilla, 2, 2)
    tonos = [b.getpixel((5, 5))[0] for b in baldosas]
    caso("una rejilla 2x2 da cuatro baldosas", len(baldosas) == 4, str(len(baldosas)))
    caso("y en orden de lectura, no por columnas",
         tonos == [0, 60, 120, 180], str(tonos))

    # 2 · el damero se va y la figura se queda
    im = cabeza(160, 80, 80, 50)
    con_alfa, quitado = cc.alfa_por_perimetro(im, cc.TOLERANCIA)
    caso("el damero se va", quitado > 0.60, f"quitado {quitado:.0%}")
    caso("el centro de la figura sigue opaco",
         con_alfa.getchannel("A").getpixel((80, 80)) > 200)
    caso("la esquina queda transparente",
         con_alfa.getchannel("A").getpixel((2, 2)) == 0)

    # 3 · una mota en el borde no define el encuadre
    sucia = con_alfa.copy()
    sucia.putpixel((1, 80), (255, 0, 0, 255))     # una sola, pegada al borde
    robusta, cruda = cc.caja_robusta(sucia), sucia.getchannel("A").getbbox()
    caso("la caja robusta ignora la mota", robusta[0] > 5, str(robusta))
    caso("la caja cruda SI se la come", cruda[0] <= 1, str(cruda))

    # 4 · la invariante de grupo: una transformacion para todos
    marcos = []
    for extra in (0, 60, 120):
        m = cabeza(400, 150, 200, 90)
        if extra:
            ImageDraw.Draw(m).rectangle([260, 190, 260 + extra, 210],
                                        fill=(40, 40, 48))
        marcos.append(m)

    salidas = cc.calibrar_grupo(marcos, referencia=0, lado=128, ocupacion=0.92,
                                tolerancia=cc.TOLERANCIA, encuadre="union")
    caso("todas las salidas miden lo mismo",
         len({s.size for s in salidas}) == 1, str({s.size for s in salidas}))

    centros = [centro_opaco(s) for s in salidas]
    mx = max(abs(c[0] - centros[0][0]) for c in centros)
    my = max(abs(c[1] - centros[0][1]) for c in centros)
    caso("la cabeza NO se mueve entre fotogramas del grupo",
         mx <= 1.0 and my <= 1.0, f"deriva max x={mx} y={my}")

    sueltas = [cc.calibrar(cc.alfa_por_perimetro(m, cc.TOLERANCIA)[0], 128, 0.92)
               for m in marcos]
    c2 = [centro_opaco(s) for s in sueltas]
    d2 = max(abs(c[0] - c2[0][0]) for c in c2)
    caso("y calibrando uno a uno se movia (por eso existe el grupo)",
         d2 > 2.0, f"deriva x={d2}")

    return fallos


def test_calibrar_caras():
    """Puerta para pytest. El gate del repo lo recoge por aqui."""
    assert comprobar(hablar=False) == []


if __name__ == "__main__":
    f = comprobar()
    print(f"\n{'VERDE' if not f else 'ROJO'} · {9 - len(f)}/9")
    sys.exit(1 if f else 0)
