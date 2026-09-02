#!/usr/bin/env python3
"""Calibra caras a una caja identica. Herramienta de FORJA, no del producto.

Hermana de `unir_bustos.py` y con sus mismas reglas: se ejecuta a mano, su
salida se versiona en `assets/`, y el producto solo ve el fichero resultante.
Por eso puede permitirse Pillow, que el backend no puede.

DEPENDENCIA DECLARADA · Pillow (medido: 12.1.1 en `soberano`, 2026-09-02).
En este nodo no hay `magick` ni `cwebp`; Pillow es el unico procesador que hay.

EL PROBLEMA QUE RESUELVE, Y ESTA MEDIDO
---------------------------------------
La cara "salta" al cambiar de estado porque los fotogramas no comparten caja.
Medido sobre `assets/preceptor-up-v2.webp`, caja del contenido por fotograma:

    [0] (24, 5, 231, 251)   ancho 207
    [2] ( 9, 5, 247, 251)   ancho 238   <- 31 px mas ancho que el [0]
    [5] (24, 5, 231, 250)   ancho 207

En un circulo de 68 px, esos 31 px de 256 son 8 px de vaiven en pantalla. No
es un defecto de la animacion: es que cada dibujo viene con su propio encuadre.

UNA TRANSFORMACION POR GRUPO, NO UNA POR FOTOGRAMA
--------------------------------------------------
Es la regla central y viene de una medida. Los seis fotogramas de la apertura
ya vienen alineados en el origen:

    cara completa   caja=(130, 53, 900, 968)   alto 915
    cara rotura 1   caja=(127, 53, 995, 968)   alto 915
    cara rotura 2   caja=(127, 53,1019, 968)   alto 915
    cara rotura 4   caja=(127, 53,1017, 968)   alto 915

La `y` es identica en los cuatro. La cabeza no se mueve; lo que crece es el
ancho, porque salen esquirlas hacia la derecha. Calibrar cada fotograma por su
propia caja alinearia cada uno CONSIGO MISMO y desalinearia la secuencia: la
cabeza latiria al ritmo del escombro. Por eso el grupo se calcula una vez
--un recorte y una escala, tomados de un fotograma de referencia-- y se aplica
igual a todos. Asi la invariante no se comprueba: se cumple por construccion.

TRES ORIGINALES NO SON UNA CARA: SON CUATRO
-------------------------------------------
`4 colores simple`, `4colores+icono` y `HablaOjo` son rejillas 2x2 de baldosas
de 512x512, no tiras de 1x4. Redimensionarlas enteras a 256 meteria las cuatro
caras dentro de un icono. Se parten primero, en orden de lectura, que es el que
declaran sus propios nombres de fichero (1 bombilla, 2 libro, 3 gorro, 4
cerebro · 1 cerrada, 2 semi, 3 abierta, 4 silbar).

EL FONDO NO ES TRANSPARENTE: ES UN DAMERO PINTADO
-------------------------------------------------
Los originales son JPEG sin canal alfa, y lo que parece transparencia es un
tablero de ajedrez DIBUJADO dentro de la imagen. Medido, que se lleva el
relleno segun la tolerancia:

    tol  42 ->  0.2 %      no atraviesa el damero
    tol  80 ->  3.1 %
    tol 120 -> 56.5 %      aqui rompe, y es el defecto

Y sembrar en las cuatro esquinas no basta: la cabeza parte el fondo en islas y
las islas se quedan opacas. Con cuatro semillas, seis fotogramas devolvian la
caja entera. Se siembra en TODO el perimetro.

Cuando el recorte no es de fiar, no se entrega: si el relleno se lleva menos
del 2 % o mas del tope, el fichero sale como NO_DATA con su causa y no se
escribe nada. Un recorte malo entregado en silencio es peor que uno que falta,
porque el que falta se ve.

LO QUE NO HACE, Y SE DICE AQUI
------------------------------
No separa el ojo de la boca. La diferencia entre fotogramas consecutivos ocupa
el ancho entero (medido: bbox_diff = (0, 5, 256, 251) en todos los pares), asi
que de las tiras viejas no se puede extraer una capa de solo-boca ni una de
solo-ojo. Eso necesita dibujos nuevos por capa, no un script.

POR QUE WEBP, Y POR QUE CON PERDIDA
-----------------------------------
Firmado por el Soberano el 2026-09-02, en dos pasos y con una correccion por
el medio.

Primero se firmo webp SIN perdida, apoyandose en el -44 % que `unir_bustos.py`
tenia medido. Ese -44 % es de graficos planos. Estas caras son fotografia de
marmol y ahi lo sin-perdida no comprime: la tanda entera salio a 1.709 KB, casi
el doble de lo que se buscaba. Medido sobre `cara-completa-256`:

    modo       fichero    x38      dif max   dif media   canal alfa
    lossless    43,3 KB   1,61 MB        0        0,00   identico
    q95         22,8 KB   0,85 MB    12/255       0,45   identico
    q90         19,1 KB   0,71 MB    12/255       0,67   identico

La cifra que decide es la ultima columna: a q95 el canal alfa sale bit a bit
igual, asi que el borde del recorte --lo unico que un ojo pilla al vuelo-- no
se toca. Lo que pierde es 0,45 de 255 de media en el color del marmol.

Firmado q95 el 2026-09-02. `CALIDAD = 0` vuelve a sin perdida.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

TOLERANCIA = 120        # medida, no elegida: ver el bloque del damero
PASO_SEMILLA = 8        # cada cuantos pixeles se siembra el perimetro
UMBRAL_FILA = 0.005     # que fraccion de una fila tiene que ser opaca
CALIDAD = 95           # 0 = sin perdida. Firmado 95: ver la cabecera
RANGO_PLANO = 90        # recorrido de color por debajo del cual una isla se
                        # considera damero y no esquirla. Sale de la medida:
                        # el fondo da 60-63 y el marmol 155-251, asi que 90 cae
                        # en el hueco y no en el borde de ninguno de los dos.

ORIGEN = Path.home() / "p0x" / "Alejandria" / "Images-preceptorOS-head"

# El reparto de grupos. Vive aqui y no en un json porque es CONOCIMIENTO sobre
# unos ficheros concretos --que son rejilla, en que orden se leen, cual manda
# el encuadre-- y separarlo del codigo que lo usa solo aniade un fichero mas
# que puede quedarse desincronizado.
#
#   rejilla   · (columnas, filas) si el original trae varias caras, o None
#   nombres   · como se llama cada salida, en orden de lectura
#   referencia· indice del fotograma que fija la escala del grupo
#   clave     · si se le fabrica alfa. `Cara-logo` va en falso a proposito:
#               su fondo oscuro es el estilo pedido, no algo que sobre.
GRUPOS = {
    "apertura": {
        "fuentes": ["cara completa.jpeg", "cara rotura 1.jpeg", "cara rotura 2.jpeg",
                    "cara rotura 3.jpeg", "cara rotura 4.jpeg",
                    "cara-violeta-corazon.jpeg"],
        "rejilla": None,
        "nombres": ["cara-completa", "cara-rotura1", "cara-rotura2",
                    "cara-rotura3", "cara-rotura4", "cara-corazon"],
        "referencia": 0,
        "clave": True,
    },
    "habla": {
        "fuentes": ["HablaOjo violeta,1 boca cerrada, 2 boca semi abierta "
                    "3 boca abierta 4 silvar.jpeg"],
        "rejilla": (2, 2),
        "nombres": ["cara-habla1", "cara-habla2", "cara-habla3", "cara-habla4"],
        "referencia": 0,
        "clave": True,
    },
    "colores": {
        "fuentes": ["4 colores simple.jpeg"],
        "rejilla": (2, 2),
        "nombres": ["cara-color1", "cara-color2", "cara-color3", "cara-color4"],
        "referencia": 0,
        "halo_por_marco": True,
        "clave": True,
    },
    "iconos": {
        "fuentes": ["4colores+icono, 1 bombilla amariilla, 2 libro azul, "
                    "3 ver gorro escolar, 4 cerebro rosa.jpeg"],
        "rejilla": (2, 2),
        "nombres": ["cara-icono-bombilla", "cara-icono-libro",
                    "cara-icono-gorro", "cara-icono-cerebro"],
        "referencia": 0,
        "halo_por_marco": True,
        "clave": True,
    },
    "logo": {
        "fuentes": ["Cara-logo.jpeg"],
        "rejilla": None,
        "nombres": ["cara-logo"],
        "referencia": 0,
        "clave": False,
    },
}


def partir(im, columnas, filas):
    """Parte una rejilla en baldosas, en orden de lectura.

    Orden de LECTURA y no por columnas: es el que declaran los nombres de los
    propios ficheros («1 bombilla, 2 libro, 3 gorro, 4 cerebro»), y leerlos al
    reves emparejaria cada icono con el color de otro sin que nada fallara.
    """
    w, h = im.size
    return [im.crop((c * w // columnas, f * h // filas,
                     (c + 1) * w // columnas, (f + 1) * h // filas))
            for f in range(filas) for c in range(columnas)]


def alfa_por_perimetro(im, tolerancia=TOLERANCIA, paso=PASO_SEMILLA):
    """Devuelve la imagen con alfa y que fraccion se llevo el relleno.

    Se siembra en todo el perimetro y no solo en las esquinas: hay dibujos con
    el fondo partido en islas por la figura, y una isla que ninguna semilla
    alcanza se queda opaca y arruina el encuadre.
    """
    rgb = im.convert("RGB")
    w, h = rgb.size
    lienzo = rgb.copy()
    centinela = (255, 0, 255)
    px = lienzo.load()
    op = rgb.load()
    semillas = []
    for x in range(0, w, paso):
        semillas += [(x, 0), (x, h - 1)]
    for y in range(0, h, paso):
        semillas += [(0, y), (w - 1, y)]
    for s in semillas:
        if px[s] != centinela:
            ImageDraw.floodfill(lienzo, s, centinela, thresh=tolerancia)
    # UNA SOLA VUELTA, Y QUEDA DAMERO. Se intento una segunda y se descarto
    # con la lamina delante, el 2026-09-02.
    #
    # El problema real: `floodfill` compara cada candidato con el color de la
    # SEMILLA, no con el de su vecino, asi que las celdas del damero que la
    # cabeza deja encerradas no se alcanzan desde el perimetro y sobreviven.
    # Se ven cuadraditos alrededor de la cabeza en siete de los diecinueve
    # fotogramas: los cuatro de `colores`, `corazon`, `habla3`, `gorro` y
    # `cerebro`.
    #
    # La segunda vuelta sembraba desde los pixeles que ya tocan fondo limpio y
    # se parecen a un tono de fondo. Funciona en una prueba sintetica y ARRASA
    # con el material real: la cara es marmol BLANCO y el damero es blanco y
    # gris. No son parecidos, son el mismo color. Medido: el relleno pasaba del
    # 56 % al 91-95 % y en la lamina no quedaba mas que el ojo violeta flotando
    # sobre esquirlas. Aqui no hay ajuste de umbral que salve la diferencia,
    # porque no hay diferencia que medir.
    #
    # Asi que el damero residual NO es un defecto de esta herramienta: es el
    # material de origen. La salida limpia es pedir los originales con canal
    # alfa de verdad. Mientras tanto se entrega lo que hay, se dice, y no se
    # disimula rompiendo la cara.
    marca = Image.new("L", (w, h), 0)
    mp = marca.load()
    op = rgb.load()
    fuera = 0
    for y in range(h):
        for x in range(w):
            if px[x, y] == centinela and op[x, y] != centinela:
                mp[x, y] = 0
                fuera += 1
            else:
                mp[x, y] = 255
    salida = rgb.convert("RGBA")
    salida.putalpha(marca)
    return salida, fuera / (w * h)


def limpiar_islas(rgba, rango_plano=RANGO_PLANO):
    """Quita las celdas de damero que el relleno dejo encerradas.

    NO por color, que es justo lo que aqui no funciona: la cara es marmol
    blanco y el damero es blanco y gris. Se probo y arraso con la cara.

    Se hace por TEXTURA, y por eso si separa. Medido sobre
    `cara-violeta-corazon.jpeg`, recorrido de color dentro de una celda:

        fondo  (8,8)     60        fondo (40,8)     63
        marmol (480,500) 251       marmol(420,300) 155

    Una celda de damero es PLANA -- lo unico que la mueve es el ruido del
    jpeg. Una esquirla de marmol es un trozo renderizado en tres dimensiones,
    con su luz y su sombra: casi nunca es plana. Cada isla suelta se mide, y la
    que sea plana se va.

    APAGADO POR DEFECTO, y la lamina dice por que. El marmol TAMBIEN tiene
    zonas planas --una mejilla lisa, una frente-- y cuando el relleno de la
    primera vuelta las deja como isla separada, esto se las come: en la prueba
    del 2026-09-02 salieron agujeros blancos en la mejilla y en la frente de la
    secuencia de apertura. El "casi" de arriba es donde vive el fallo. Se deja
    en el arbol porque la medida es correcta y puede servir con otro material,
    pero hay que pedirlo a mano y mirar el resultado.

    La isla mas grande no se toca NUNCA, pase lo que pase con su medida: es la
    cabeza, y ninguna heuristica puede tener permiso para borrarla.
    """
    from PIL import ImageStat

    al = rgba.getchannel("A")
    rgb = rgba.convert("RGB")
    trabajo = al.point(lambda v: 255 if v > 8 else 0)
    w, h = trabajo.size
    px = trabajo.load()

    islas = []
    for y in range(0, h, 3):
        for x in range(0, w, 3):
            if px[x, y] != 255:
                continue
            ImageDraw.floodfill(trabajo, (x, y), 128)
            esta = trabajo.point(lambda v: 255 if v == 128 else 0)
            caja = esta.getbbox()
            if caja is None:
                continue
            n = esta.histogram()[255]
            recorte, mascara = rgb.crop(caja), esta.crop(caja)
            ext = ImageStat.Stat(recorte, mascara).extrema
            rango = max(hi - lo for lo, hi in ext)
            islas.append({"caja": caja, "px": n, "rango": rango, "marca": esta})
            # Se aparta con un valor propio para no volver a visitarla.
            trabajo.paste(64, (0, 0), esta)

    if not islas:
        return rgba, 0
    mayor = max(range(len(islas)), key=lambda i: islas[i]["px"])
    nueva = al.copy()
    quitadas = 0
    for i, isla in enumerate(islas):
        if i == mayor or isla["rango"] > rango_plano:
            continue
        nueva.paste(0, (0, 0), isla["marca"])
        quitadas += 1
    salida = rgba.copy()
    salida.putalpha(nueva)
    return salida, quitadas


def color_del_ojo(rgba, por_defecto=(109, 90, 224)):
    """El color mas saturado de la cara. Es el ojo: lo demas es marmol gris.

    Sirve para el halo, y sale de la propia lamina en vez de una tabla: el dia
    que entre una cara con el ojo de otro color, el halo la acompana sin que
    nadie tenga que acordarse de aniadirla a una lista.
    """
    chico = rgba.convert("RGBA").resize((64, 64), Image.LANCZOS)
    mejor, sat_mejor = por_defecto, 0
    px = chico.load()
    for y in range(64):
        for x in range(64):
            r, g, b, a = px[x, y]
            if a < 120:
                continue
            hi, lo = max(r, g, b), min(r, g, b)
            if hi < 60:
                continue
            sat = (hi - lo) / hi
            if sat > sat_mejor:
                sat_mejor, mejor = sat, (r, g, b)
    return mejor if sat_mejor > 0.25 else por_defecto


def con_halo(rgba, color=None, radio=6, fuerza=140):
    """Un resplandor del color del ojo pegado a la silueta.

    Idea del Soberano, y resuelve algo que el recorte no puede: con la cara
    blanca sobre un fondo claro, el borde no se lee. El halo lo dibuja. Va
    DETRAS de la figura --se compone la cara encima-- para que no le meta color
    al marmol; lo unico que tine es el aire de alrededor.
    """
    from PIL import ImageFilter

    color = color or color_del_ojo(rgba)
    silueta = rgba.getchannel("A").filter(ImageFilter.MaxFilter(radio * 2 + 1))
    silueta = silueta.filter(ImageFilter.GaussianBlur(radio))
    silueta = silueta.point(lambda v: min(fuerza, v))
    fondo = Image.new("RGBA", rgba.size, color + (0,))
    fondo.putalpha(silueta)
    fondo.alpha_composite(rgba)
    return fondo


def caja_robusta(im, umbral=UMBRAL_FILA):
    """Caja que ignora filas y columnas casi vacias.

    Una mota de ruido jpeg pegada a un borde no puede definir el encuadre de
    una cabeza. `getbbox()` crudo si se la come: basta un pixel.
    """
    al = im.getchannel("A")
    w, h = al.size
    px = al.load()
    # El suelo de 2 no es adorno. Con solo `umbral * w`, en una imagen de 160
    # px el listón queda en 0,8 y UN pixel suelto ya lo pasa: la funcion se
    # llamaba robusta y no lo era. Se descubrio con la prueba, no leyendola.
    minimo_x = max(2, umbral * w)
    minimo_y = max(2, umbral * h)
    fy = [y for y in range(h)
          if sum(1 for x in range(w) if px[x, y] > 8) > minimo_x]
    fx = [x for x in range(w)
          if sum(1 for y in range(h) if px[x, y] > 8) > minimo_y]
    if not fx or not fy:
        return None
    return (fx[0], fy[0], fx[-1] + 1, fy[-1] + 1)


def calibrar(im, lado, ocupacion):
    """Calibra UN fotograma por su propia caja.

    Sirve para imagenes sueltas. Para una secuencia NO sirve, y la prueba lo
    demuestra: alinea cada fotograma consigo mismo y desalinea el conjunto.
    """
    caja = caja_robusta(im) or im.getchannel("A").getbbox()
    if caja is None:
        raise ValueError("la imagen quedo entera transparente")
    recorte = im.crop(caja)
    alto = round(lado * ocupacion)
    escala = alto / recorte.height
    recorte = recorte.resize((max(1, round(recorte.width * escala)), alto),
                             Image.LANCZOS)
    lona = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    lona.paste(recorte, ((lado - recorte.width) // 2,
                         (lado - recorte.height) // 2), recorte)
    return lona


def calibrar_grupo(marcos, referencia, lado, ocupacion,
                   tolerancia=TOLERANCIA, encuadre="union", clave=True,
                   limpiar=False, halo=0, por_marco=False):
    """Una escala y un centro para TODO el grupo. Devuelve las lonas.

    `encuadre`:
      union  · el rectangulo elegido abarca todos los fotogramas. No se pierde
               una esquirla, y la cabeza sale mas pequena.
      cabeza · manda la caja del fotograma de referencia. La cabeza sale
               grande y lo que se salga del cuadrado se recorta.

    En los dos casos la transformacion es UNA, calculada antes del bucle. Que
    la cabeza no se mueva no es algo que se compruebe despues: es que a todos
    los fotogramas se les aplica exactamente el mismo recorte y la misma
    escala, asi que cualquier punto fijo del origen cae en el mismo pixel.
    """
    con_alfa, cajas = [], []
    for m in marcos:
        if clave:
            a, _ = alfa_por_perimetro(m, tolerancia)
            if limpiar:
                # Se limpia ANTES de medir la caja: una celda de damero suelta
                # a diez pixeles del borde estira el encuadre del grupo entero.
                # Va bajo bandera: ver el aviso en `limpiar_islas`.
                a, _ = limpiar_islas(a)
        else:
            a = m.convert("RGBA")
        con_alfa.append(a)
        cajas.append(caja_robusta(a) or (0, 0, *a.size))

    ref = cajas[referencia]
    if encuadre == "cabeza":
        sel = ref
    else:
        sel = (min(c[0] for c in cajas), min(c[1] for c in cajas),
               max(c[2] for c in cajas), max(c[3] for c in cajas))

    escala = (lado * ocupacion) / max(sel[2] - sel[0], sel[3] - sel[1])
    cx = (sel[0] + sel[2]) / 2
    cy = (sel[1] + sel[3]) / 2

    # UN color de halo para todo el grupo, sacado del fotograma de referencia.
    # Por fotograma seria peor: en la apertura el ojo aun no esta encendido en
    # los primeros, asi que cada uno elegiria un color distinto y el halo
    # parpadearia justo donde la secuencia tiene que fluir. En los grupos donde
    # cada cara ES de un color distinto --`colores`, `iconos`-- no se usa un
    # halo de grupo: se pide por fotograma desde fuera.
    color_grupo = color_del_ojo(con_alfa[referencia]) if halo and not por_marco else None

    lonas = []
    for a in con_alfa:
        color_ojo = color_del_ojo(a) if (halo and por_marco) else color_grupo
        w, h = a.size
        grande = a.resize((max(1, round(w * escala)), max(1, round(h * escala))),
                          Image.LANCZOS)
        lona = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
        lona.paste(grande, (round(lado / 2 - cx * escala),
                            round(lado / 2 - cy * escala)), grande)
        if halo:
            # El halo se pone al FINAL, sobre la lona ya calibrada, y no sobre
            # el original: asi su radio esta en pixeles de pantalla y mide lo
            # mismo en la de 256 y en la de 180. Puesto antes de escalar, la
            # pequena saldria con un halo mas fino que la grande.
            lona = con_halo(lona, color_ojo, radio=halo)
        lonas.append(lona)
    return lonas


def main(argv=None):
    ap = argparse.ArgumentParser(description="calibra caras a una caja identica")
    ap.add_argument("--grupo", action="append", choices=sorted(GRUPOS),
                    help="repetible. Sin ninguno, los hace todos")
    ap.add_argument("--origen", type=Path, default=ORIGEN)
    ap.add_argument("--destino", type=Path, action="append", required=True,
                    help="repetible: una carpeta por capa (app y web)")
    ap.add_argument("--lado", type=int, action="append",
                    help="repetible. Por defecto 256 y 180")
    ap.add_argument("--ocupacion", type=float, default=0.92)
    ap.add_argument("--tolerancia", type=int, default=TOLERANCIA)
    ap.add_argument("--tope", type=float, default=0.70,
                    help="fraccion maxima que puede llevarse el relleno")
    ap.add_argument("--encuadre", choices=("union", "cabeza"), default="union")
    ap.add_argument("--halo", type=int, default=0, metavar="RADIO",
                    help="resplandor del color del ojo pegado a la silueta. "
                         "Idea del Soberano: la cara es marmol blanco y sin el "
                         "borde no se lee sobre un fondo claro. 0 = sin halo")
    ap.add_argument("--calidad", type=int, default=CALIDAD,
                    help="calidad webp. 0 = sin perdida (pesa el doble y el "
                         "alfa sale igual: ver la cabecera)")
    ap.add_argument("--limpiar-islas", action="store_true",
                    help="quitar las islas planas de damero. APAGADO por "
                         "defecto: se probo el 2026-09-02 y abre agujeros en "
                         "la mejilla y la frente. El marmol tambien tiene "
                         "zonas planas, y la planitud no las distingue.")
    ap.add_argument("--barrido", action="store_true",
                    help="solo mide: que se lleva el relleno a varias tolerancias")
    ap.add_argument("--ejecutar", action="store_true",
                    help="sin esto no se escribe nada: solo se mide y se informa")
    a = ap.parse_args(argv)

    lados = a.lado or [256, 180]
    calidad = a.calidad
    grupos = a.grupo or sorted(GRUPOS)

    if a.barrido:
        print("[barrido] fraccion que se lleva el relleno por tolerancia")
        for g in grupos:
            for f in GRUPOS[g]["fuentes"]:
                fila = []
                for t in (42, 80, 120, 160, 200):
                    _, q = alfa_por_perimetro(Image.open(a.origen / f), t)
                    fila.append(f"{t:3d}:{q:5.1%}")
                print(f"  {f[:44]:46s} " + " ".join(fila))
        return 0

    print(f"[calibrar] grupos: {', '.join(grupos)} · lados {lados} · "
          f"tolerancia {a.tolerancia} · encuadre {a.encuadre}")
    if not a.ejecutar:
        print("[calibrar] cerrojo: no se escribe. Anade --ejecutar")

    escritos, saltados = 0, 0
    for nombre in grupos:
        g = GRUPOS[nombre]
        faltan = [f for f in g["fuentes"] if not (a.origen / f).is_file()]
        if faltan:
            print(f"  NO_DATA grupo {nombre} · no estan: {faltan}")
            saltados += 1
            continue

        marcos = []
        for f in g["fuentes"]:
            im = Image.open(a.origen / f)
            marcos += partir(im, *g["rejilla"]) if g["rejilla"] else [im]
        if len(marcos) != len(g["nombres"]):
            print(f"  NO_DATA grupo {nombre} · salen {len(marcos)} fotogramas "
                  f"y hay {len(g['nombres'])} nombres. No adivino cual es cual.")
            saltados += 1
            continue

        # El aviso de recorte dudoso se da por fotograma ANTES de calibrar: si
        # uno solo del grupo esta mal keyed, la transformacion de grupo lo
        # arrastra a todos y conviene verlo aqui, no en la lamina.
        malos = []
        if g["clave"]:
            for m, n in zip(marcos, g["nombres"]):
                _, q = alfa_por_perimetro(m, a.tolerancia)
                if not 0.02 <= q <= a.tope:
                    malos.append(f"{n} ({q:.0%})")
        if malos:
            print(f"  NO_DATA grupo {nombre} · el relleno se salio del rango "
                  f"2-{a.tope:.0%} en: {', '.join(malos)}. No se escribe el grupo.")
            saltados += 1
            continue

        print(f"\n  grupo {nombre} · {len(marcos)} fotogramas"
              f"{' (rejilla %dx%d)' % g['rejilla'] if g['rejilla'] else ''}")
        for lado in lados:
            lonas = calibrar_grupo(marcos, g["referencia"], lado, a.ocupacion,
                                   a.tolerancia, a.encuadre, g["clave"],
                                   limpiar=a.limpiar_islas, halo=a.halo,
                                   por_marco=g.get("halo_por_marco", False))
            for lona, n in zip(lonas, g["nombres"]):
                caja = caja_robusta(lona)
                print(f"    {n}-{lado}.webp  caja={caja}")
                if a.ejecutar:
                    for d in a.destino:
                        d.mkdir(parents=True, exist_ok=True)
                        if calidad:
                            lona.save(d / f"{n}-{lado}.webp",
                                      quality=calidad, method=6)
                        else:
                            lona.save(d / f"{n}-{lado}.webp", lossless=True)
                    escritos += 1

    print(f"\n[calibrar] {escritos} ficheros escritos · {saltados} grupos en NO_DATA")
    return 1 if saltados and not escritos else 0


if __name__ == "__main__":
    sys.exit(main())
