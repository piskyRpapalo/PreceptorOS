#!/usr/bin/env python3
"""voz.py · La garganta de Aurelius.

Encapsula Piper TTS + efectos de post-procesamiento (pitch, saturación,
reverb, filtros). Todo el audio se genera localmente, sin red.

Doctrina:
- Si Piper no existe o falla, voz.py devuelve None y Aurelius escribe en
  texto plano. Nunca bloquea la misión.
- Los efectos son opcionales y configurables por perfil.
"""
from __future__ import annotations

import subprocess
import wave
import math
import struct
import os
import tempfile
from typing import Optional

PIPER = os.path.expanduser("~/piper/build/piper")
ESPEAK_DATA = os.path.expanduser("~/piper/build/pi/share/espeak-ng-data")
VOZ_DIR = os.path.expanduser("~/.aurelius/voz")
SONIDOS_DIR = os.path.expanduser("~/.aurelius/sonidos")

# Modelo por defecto (davefx = masculino grave)
MODELO_DEFECTO = os.path.join(VOZ_DIR, "es_ES-davefx-medium.onnx")


def piper_disponible() -> bool:
    """True si Piper está compilado y el modelo existe."""
    return os.path.isfile(PIPER) and os.path.isfile(MODELO_DEFECTO)


def generar_base(texto: str, salida: str,
                 length_scale: float = 1.2,
                 sentence_silence: float = 0.8) -> bool:
    """Genera audio base con Piper. Devuelve True si OK."""
    if not piper_disponible():
        return False
    cmd = [
        PIPER, "--model", MODELO_DEFECTO,
        "--output_file", salida,
        "--espeak_data", ESPEAK_DATA,
        "--length-scale", str(length_scale),
        "--sentence-silence", str(sentence_silence),
    ]
    try:
        r = subprocess.run(cmd, input=texto, capture_output=True,
                           text=True, timeout=30)
        return r.returncode == 0
    except Exception:
        return False


def resample_grave(samples: list[int], factor: float) -> list[int]:
    """Factor > 1 = estira la onda = más grave."""
    new_length = int(len(samples) * factor)
    result = []
    for i in range(new_length):
        src_pos = i / factor
        src_idx = int(src_pos)
        frac = src_pos - src_idx
        if src_idx + 1 < len(samples):
            val = samples[src_idx] * (1 - frac) + samples[src_idx + 1] * frac
        elif src_idx < len(samples):
            val = samples[src_idx]
        else:
            val = 0
        result.append(int(val))
    return result


def aplicar_efectos(entrada: str, salida: str,
                    pitch: float = 1.12,
                    saturacion: float = 1.05,
                    reverb_decay: float = 0.2,
                    reverb_ms: int = 60) -> bool:
    """Aplica pitch grave + saturación + reverb. Devuelve True si OK."""
    try:
        with wave.open(entrada, 'rb') as w:
            framerate = w.getframerate()
            frames = w.readframes(w.getnframes())
        samples = list(struct.unpack(f'<{len(frames)//2}h', frames))

        # 1. Pitch shift grave
        if pitch != 1.0:
            samples = resample_grave(samples, pitch)

        # 2. Saturación suave
        if saturacion != 1.0:
            for i in range(len(samples)):
                x = samples[i] / 32768.0
                samples[i] = int(32767 * math.tanh(x * saturacion))

        # 3. Reverb sutil
        if reverb_decay > 0:
            delay = int(framerate * reverb_ms / 1000)
            reverb = samples.copy()
            for i in range(delay, len(samples)):
                reverb[i] = int(samples[i] + reverb_decay * samples[i - delay])
                reverb[i] = max(-32768, min(32767, reverb[i]))
            samples = reverb

        with wave.open(salida, 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(framerate)
            w.writeframes(struct.pack(f'<{len(samples)}h', *samples))
        return True
    except Exception:
        return False


def hablar(texto: str, salida: str,
           pitch: float = 1.12,
           saturacion: float = 1.05,
           reverb_decay: float = 0.2,
           length_scale: float = 1.2,
           sentence_silence: float = 0.8) -> Optional[str]:
    """API principal: genera un WAV con la voz de Aurelius.

    Devuelve la ruta del WAV final, o None si la voz no está disponible.
    """
    if not piper_disponible():
        return None
    with tempfile.TemporaryDirectory() as tmpdir:
        base = os.path.join(tmpdir, "base.wav")
        if not generar_base(texto, base, length_scale, sentence_silence):
            return None
        if not aplicar_efectos(base, salida, pitch, saturacion,
                               reverb_decay):
            return None
    return salida


def tocar_leitmotiv(sala: int) -> Optional[str]:
    """Devuelve la ruta del leitmotiv de una sala (1-6), o None."""
    nombres = {
        1: "sala_1_prohairesis",
        2: "sala_2_safehouse",
        3: "sala_3_horme",
        4: "sala_4_prosoche",
        5: "sala_5_katalepsis",
        6: "sala_6_hupexairesis",
    }
    nombre = nombres.get(sala)
    if nombre is None:
        return None
    ruta = os.path.join(SONIDOS_DIR, f"{nombre}.wav")
    return ruta if os.path.isfile(ruta) else None


if __name__ == "__main__":
    # Prueba rápida
    out = os.path.expanduser("~/p0x/aurelius-mvp/test_voz_modulo.wav")
    ruta = hablar("A... aaa... aurelius! donde... estoy?", out)
    if ruta:
        print(f"✓ Audio generado: {ruta}")
    else:
        print("✗ Piper no disponible. Aurelius escribirá en texto plano.")
