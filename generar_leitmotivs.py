#!/usr/bin/env python3
"""Genera los 6 leitmotivs de M3 en ~/.aurelius/sonidos/"""
import wave, math, struct, os

SONIDOS_DIR = os.path.expanduser("~/.aurelius/sonidos")
os.makedirs(SONIDOS_DIR, exist_ok=True)

FRAMERATE = 22050
DURACION = 2.5

def generar_wav(nombre, frecuencias, tipo='sostenida'):
    n_samples = int(FRAMERATE * DURACION)
    samples = []
    for i in range(n_samples):
        t = i / FRAMERATE
        val = 0.0
        for freq in frecuencias:
            if tipo == 'ascendente':
                f_t = frecuencias[0] + (frecuencias[1] - frecuencias[0]) * (t / DURACION)
                val += math.sin(2 * math.pi * f_t * t)
            elif tipo == 'electrico':
                val += math.sin(2 * math.pi * freq * t) * 0.7
                val += math.sin(2 * math.pi * 60 * t) * 0.3
            else:
                val += math.sin(2 * math.pi * freq * t)
        envelope = 1.0
        if i < FRAMERATE * 0.2:
            envelope = i / (FRAMERATE * 0.2)
        elif i > n_samples - FRAMERATE * 0.5:
            envelope = (n_samples - i) / (FRAMERATE * 0.5)
        val *= envelope * 0.3
        val += (hash(str(i)) % 200 - 100) / 10000  # Ruido sutil
        val = max(-1.0, min(1.0, val))
        samples.append(int(val * 32767))
    ruta = os.path.join(SONIDOS_DIR, f"{nombre}.wav")
    with wave.open(ruta, 'w') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(FRAMERATE)
        w.writeframes(struct.pack(f'<{len(samples)}h', *samples))
    print(f"  ✓ Generado: {ruta}")

generar_wav("sala_1_prohairesis", [220])
generar_wav("sala_2_safehouse", [110, 165])
generar_wav("sala_3_horme", [330, 415])
generar_wav("sala_4_prosoche", [440], 'electrico')
generar_wav("sala_5_katalepsis", [440, 660], 'ascendente')
generar_wav("sala_6_hupexairesis", [220, 330, 440])
print("\n✓ Todos los leitmotivs generados")
