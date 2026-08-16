#!/usr/bin/env python3
"""Los 6 leitmotivs de M3, fabricados aqui y no descargados.

sistema: MVP · solo biblioteca estandar. Sin red.

Viaja con el repo para que un clon limpio suene igual que esta maquina. Eso
solo es cierto si el generador es DETERMINISTA, y hasta D78 no lo era: el
ruido de fondo salia de `hash(str(i))`, y el hash de `str` en Python esta
aleatorizado por proceso (PYTHONHASHSEED). Dos ejecuciones en la MISMA maquina
daban sha256 distintos; dos clones, sonidos distintos. Aqui el ruido sale de
un `random.Random` sembrado con el nombre de la sala: la misma sala suena
igual en todas partes y para siempre, y dos salas distintas suenan distinto.

`random.Random(cadena)` siembra por sha512 del texto, no por `hash()`: no lo
toca PYTHONHASHSEED.

Nada se escribe al importar este modulo. La ruta se pasa o se pide, pero el
import no crea directorios: un modulo que escribe en la casa de la persona
solo por ser importado no se puede probar sin tocarla.
"""
from __future__ import annotations

import math
import os
import random
import struct
import wave

import casa as _casa

FRAMERATE = 22050
DURACION = 2.5

# La tabla es el canon: nombre, frecuencias y timbre de cada sala. Los nombres
# tienen que coincidir con `voz.tocar_leitmotiv`.
LEITMOTIVS = (
    ("sala_1_prohairesis", (220,), "sostenida"),
    ("sala_2_safehouse", (110, 165), "sostenida"),
    ("sala_3_horme", (330, 415), "sostenida"),
    ("sala_4_prosoche", (440,), "electrico"),
    ("sala_5_katalepsis", (440, 660), "ascendente"),
    ("sala_6_hupexairesis", (220, 330, 440), "sostenida"),
)


def directorio_defecto() -> str:
    """Donde viven los sonidos. Se calcula al llamar, no al importar."""
    return os.path.join(str(_casa.raiz()), "sonidos")


def _muestras(nombre: str, frecuencias, tipo: str) -> list[int]:
    """La onda de una sala. Misma entrada, misma salida, siempre."""
    # Sembrado con el nombre de la sala: determinista entre procesos y entre
    # maquinas, y distinto para cada sala.
    rng = random.Random(nombre)
    n_samples = int(FRAMERATE * DURACION)
    ataque = FRAMERATE * 0.2
    caida = FRAMERATE * 0.5
    muestras = []

    for i in range(n_samples):
        t = i / FRAMERATE
        if tipo == "ascendente":
            # UN barrido, no uno por frecuencia. Antes esto vivia dentro de
            # `for freq in frecuencias` sin usar `freq`, asi que sumaba el
            # mismo barrido tantas veces como frecuencias hubiera: la sala 5
            # sonaba al doble de volumen que el resto por un bucle de mas.
            f_t = frecuencias[0] + (frecuencias[-1] - frecuencias[0]) * (t / DURACION)
            val = math.sin(2 * math.pi * f_t * t)
        elif tipo == "electrico":
            val = 0.0
            for freq in frecuencias:
                val += math.sin(2 * math.pi * freq * t) * 0.7
                val += math.sin(2 * math.pi * 60 * t) * 0.3
        else:
            val = 0.0
            for freq in frecuencias:
                val += math.sin(2 * math.pi * freq * t)

        if i < ataque:
            envolvente = i / ataque
        elif i > n_samples - caida:
            envolvente = (n_samples - i) / caida
        else:
            envolvente = 1.0

        val *= envolvente * 0.3
        val += (rng.randrange(200) - 100) / 10000      # ruido sutil
        muestras.append(int(max(-1.0, min(1.0, val)) * 32767))

    return muestras


def generar_wav(nombre: str, frecuencias, tipo: str = "sostenida",
                destino: str | None = None) -> str:
    """Escribe el WAV de una sala y devuelve su ruta."""
    destino = destino or directorio_defecto()
    os.makedirs(destino, exist_ok=True)
    muestras = _muestras(nombre, frecuencias, tipo)
    ruta = os.path.join(destino, f"{nombre}.wav")
    with wave.open(ruta, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(FRAMERATE)
        w.writeframes(struct.pack(f"<{len(muestras)}h", *muestras))
    return ruta


def faltan(destino: str | None = None) -> list[str]:
    """Los leitmotivs que no estan en disco. Lista vacia = estan los seis."""
    destino = destino or directorio_defecto()
    return [n for n, _, _ in LEITMOTIVS
            if not os.path.isfile(os.path.join(destino, f"{n}.wav"))]


def generar_todos(destino: str | None = None, forzar: bool = False) -> list[str]:
    """Genera los que falten. Con `forzar`, los seis."""
    destino = destino or directorio_defecto()
    pendientes = [n for n, _, _ in LEITMOTIVS] if forzar else faltan(destino)
    hechos = []
    for nombre, frecuencias, tipo in LEITMOTIVS:
        if nombre in pendientes:
            hechos.append(generar_wav(nombre, frecuencias, tipo, destino))
    return hechos


def asegurar(destino: str | None = None) -> list[str]:
    """Deja los seis en disco. Nunca bloquea: si no puede, se calla y sigue.

    La llama `fuga.ejecutar()` al entrar en M3. Un clon limpio no tenia
    sonidos hasta que alguien ejecutara esto a mano, que es justo lo que un
    generador que viaja con el repo venia a evitar. Y si el disco esta lleno o
    de solo lectura, M3 se hace igual: la musica es un adorno del relato, no
    un requisito -- misma regla que la voz y el oido.
    """
    try:
        return generar_todos(destino)
    except OSError:
        return []


def main():
    destino = directorio_defecto()
    hechos = generar_todos(destino, forzar=True)
    for ruta in hechos:
        print(f"  ✓ Generado: {ruta}")
    print(f"\n✓ Los {len(hechos)} leitmotivs en {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
