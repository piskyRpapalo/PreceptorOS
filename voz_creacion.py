"""Explicit, local creation voice. A profile change invalidates the entire batch."""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import threading

import voz

LIMITE = 25 * 1024 * 1024
PARAMETROS = dict(pitch=1.12, saturacion=1.05, reverb_decay=0.2,
                  length_scale=1.2, sentence_silence=0.8)
INVENTARIO = dict(add='Point added', undo='Undo', redo='Redo', border='Edge',
                  reject='Rejected', repeat='Current drawing', cyan='Cyan',
                  ink='Ink', x='X', y='Y', points='Points', signing='Signing',
                  signed='Signed', exported='Exported', published='Published',
                  unavailable='Voice unavailable', ready='Ready',
                  empty='No points', limit='Frame size limit reached')
INVENTARIO.update({f'digit_{i}': word for i, word in enumerate(
    ('Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine'))})
_LOCK = threading.Lock()


class VoiceError(ValueError):
    """Only locally authored, public-safe causes may leave this module."""


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _json(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def _file_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _profile():
    if not voz.piper_disponible():
        raise VoiceError('local voice engine or model unavailable')
    return _json({'engine': 'voz.py/piper',
                  'engine_sha256': _file_hash(voz.piper_binario()),
                  'model_sha256': _file_hash(voz.MODELO_DEFECTO),
                  'config_sha256': _file_hash(voz.MODELO_DEFECTO + '.json'),
                  'processor_sha256': _file_hash(voz.__file__),
                  'parameters': PARAMETROS})


def validar_wav(data):
    """The shared cut is RIFF PCM16 mono, exactly fmt(16) followed by data."""
    if len(data) < 46 or len(data) > LIMITE:
        raise VoiceError('invalid WAV size')
    if data[:4] != b'RIFF' or data[8:12] != b'WAVE' or data[12:16] != b'fmt ':
        raise VoiceError('invalid WAV header')
    total, = struct.unpack_from('<I', data, 4)
    fmt, codec, channels, rate, byte_rate, align, bits = struct.unpack_from('<IHHIIHH', data, 16)
    size, = struct.unpack_from('<I', data, 40)
    if (total != len(data) - 8 or fmt != 16 or codec != 1 or channels != 1
            or not 8000 <= rate <= 96000 or byte_rate != rate * 2
            or align != 2 or bits != 16 or data[36:40] != b'data'
            or size != len(data) - 44 or size % 2):
        raise VoiceError('invalid WAV PCM16 mono layout')


def _clip(text, directory, profile):
    if _profile() != profile:
        raise VoiceError('voice profile changed during generation')
    output = Path(directory) / 'voice.wav'
    if not voz.hablar(text, str(output), **PARAMETROS):
        raise VoiceError('local voice generation failed')
    if _profile() != profile:
        raise VoiceError('voice profile changed during generation')
    if output.stat().st_size > LIMITE:
        raise VoiceError('voice package size limit exceeded')
    data = output.read_bytes()
    validar_wav(data)
    return dict(text=text, size=len(data), sha256=_sha(data),
                data=base64.b64encode(data).decode('ascii'))


def generar(texto):
    """Return complete downloads or a small sanitized NO_DATA receipt; no I/O outside temp."""
    try:
        if not isinstance(texto, str) or not texto.strip() or len(texto.encode('utf-8')) > 1024:
            raise VoiceError('author statement must contain 1 to 1024 UTF-8 bytes')
        with _LOCK, tempfile.TemporaryDirectory() as temporary:
            profile = _profile()
            profile_id = _sha(profile.encode('utf-8'))
            catalog = dict(schema='preceptoros.creation-voice/1', profile=profile,
                           profile_id=profile_id, clips={})
            for name, phrase in INVENTARIO.items():
                catalog['clips'][name] = _clip(phrase, temporary, profile)
                if len(_json(catalog).encode('utf-8')) > LIMITE:
                    raise VoiceError('voice catalog size limit exceeded')
            declaration = dict(schema='preceptoros.creation-declaration/1',
                               profile_id=profile_id, **_clip(texto, temporary, profile))
            if len(_json(declaration).encode('utf-8')) > LIMITE:
                raise VoiceError('voice declaration size limit exceeded')
            result = dict(estado='ok', catalog=catalog, declaration=declaration)
            if len(_json(result).encode('utf-8')) > LIMITE:
                raise VoiceError('voice downloads size limit exceeded')
            return result
    except UnicodeError:
        return dict(estado='NO_DATA', causa='author statement must be valid UTF-8')
    except VoiceError as error:
        return dict(estado='NO_DATA', causa=str(error))
    except Exception:
        return dict(estado='NO_DATA', causa='local voice generation failed or resources unavailable')
