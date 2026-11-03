"""Explicit host-native text rendering; no microphone, shell or network."""
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import wave

import silencio

MAX_TEXT = 960
MAX_AUDIO = 8 * 1024 * 1024
_LOCK = threading.Lock()


class ReadingUnavailable(ValueError):
    pass


def synthesize(request):
    if (not isinstance(request, dict) or set(request) != {"text", "engine"}
            or request.get("engine") != "host-espeak-ng"
            or not isinstance(request.get("text"), str)):
        raise ReadingUnavailable("invalid_reading_request")
    text = request["text"]
    try:
        raw = text.encode("utf-8")
    except UnicodeError:
        raise ReadingUnavailable("invalid_text") from None
    if not text.strip() or len(raw) > MAX_TEXT or any(ord(c) < 32 and c not in "\n\t" for c in text):
        raise ReadingUnavailable("invalid_text")
    if silencio.apagado():
        raise ReadingUnavailable("hardware_declared_off")
    binary = shutil.which("espeak-ng")
    if not binary:
        raise ReadingUnavailable("host_native_voice_unavailable")
    if not _LOCK.acquire(blocking=False):
        raise ReadingUnavailable("host_native_voice_busy")
    try:
        with tempfile.TemporaryDirectory(prefix="app-reading-") as folder:
            output = Path(folder) / "reading.wav"
            result = subprocess.run([binary, "--stdin", "-v", "en", "-s", "160", "-w", str(output)],
                                    input=raw, capture_output=True, timeout=15, check=True)
            if result.returncode or not output.is_file() or not 44 < output.stat().st_size <= MAX_AUDIO:
                raise ReadingUnavailable("host_native_voice_failed")
            audio = output.read_bytes()
        with wave.open(io.BytesIO(audio), "rb") as wav:
            if (wav.getnchannels() != 1 or wav.getsampwidth() != 2
                    or wav.getcomptype() != "NONE" or not 8000 <= wav.getframerate() <= 96000
                    or not 0 < wav.getnframes() <= wav.getframerate() * 180):
                raise ReadingUnavailable("invalid_voice_audio")
            frames, rate = wav.getnframes(), wav.getframerate()
            if len(wav.readframes(frames)) != frames * 2:
                raise ReadingUnavailable("invalid_voice_audio")
        receipt = dict(state="ok", engine="host-espeak-ng", language="en",
                       text_sha256=hashlib.sha256(raw).hexdigest(),
                       audio_sha256=hashlib.sha256(audio).hexdigest(),
                       bytes=len(audio), duration_ms=round(1000 * frames / rate),
                       cause="native_synthesis_only_not_physical_audibility")
        assert len(json.dumps(receipt).encode()) < 1024
        return audio, receipt
    except ReadingUnavailable:
        raise
    except (OSError, subprocess.SubprocessError, wave.Error, EOFError):
        raise ReadingUnavailable("host_native_voice_failed") from None
    finally:
        _LOCK.release()
