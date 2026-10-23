"""Validate and persist browser-authored creation packages.

The author signature covers the exact UTF-8 manifest bytes.  The host node's
charter is a separate identity and is neither read nor changed here.
"""
from __future__ import annotations

import base64
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

SCHEMA = "preceptoros.creation/1"
MAX_PACKAGE = 25 * 1024 * 1024
MAX_FRAME = 1024
NAMES = ("frame.json", "declaration.wav")
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
HEX_128 = re.compile(r"^[0-9a-f]{128}$")


class CreationError(ValueError):
    """A bounded public cause; never includes input values or local paths."""


def _fail(cause: str):
    raise CreationError("NO_DATA · " + cause)


def _exact(obj, keys, label):
    if not isinstance(obj, dict) or set(obj) != set(keys):
        _fail(label + " fields")


def _text(value, maximum, label):
    if not isinstance(value, str) or not value.strip():
        _fail(label + " text")
    try:
        if len(value.encode("utf-8", "strict")) > maximum:
            _fail(label + " text")
    except UnicodeError:
        _fail(label + " UTF-8")
    return value


def _hex(value, pattern, label):
    if not isinstance(value, str) or not pattern.fullmatch(value):
        _fail(label + " encoding")
    return bytes.fromhex(value)


def _json(raw):
    def invalid(_):
        raise ValueError("invalid JSON number")
    try:
        return json.loads(raw, parse_constant=invalid)
    except (ValueError, TypeError, UnicodeError, RecursionError):
        _fail("invalid JSON")


def _wav(data):
    if len(data) < 46:
        _fail("WAV length")
    try:
        riff, size, wave, fmt, fmt_size, codec, channels, rate, byte_rate, align, bits, block, samples = \
            data[:4], int.from_bytes(data[4:8], "little"), data[8:12], data[12:16], \
            int.from_bytes(data[16:20], "little"), int.from_bytes(data[20:22], "little"), \
            int.from_bytes(data[22:24], "little"), int.from_bytes(data[24:28], "little"), \
            int.from_bytes(data[28:32], "little"), int.from_bytes(data[32:34], "little"), \
            int.from_bytes(data[34:36], "little"), data[36:40], int.from_bytes(data[40:44], "little")
    except (IndexError, ValueError):
        _fail("WAV header")
    if (riff != b"RIFF" or wave != b"WAVE" or fmt != b"fmt " or block != b"data"
            or size != len(data) - 8 or fmt_size != 16 or codec != 1 or channels != 1
            or not 8000 <= rate <= 96000 or byte_rate != rate * 2 or align != 2
            or bits != 16 or samples != len(data) - 44 or samples < 2 or samples % 2):
        _fail("WAV PCM16 mono format")
    return data


def _frame(data):
    if not 0 < len(data) < MAX_FRAME:
        _fail("frame byte limit")
    try:
        frame = _json(data.decode("utf-8", "strict"))
    except UnicodeError:
        _fail("frame UTF-8")
    _exact(frame, ("v", "id", "cv", "style", "atoms"), "frame")
    if (frame["v"] != "preceptoros.bubble/1" or not isinstance(frame["id"], str)
            or not re.fullmatch(r"[A-Z0-9_-]{1,32}", frame["id"])
            or frame["cv"] != [412, 515] or frame["style"] not in ("volume", "etch", "clear")
            or not isinstance(frame["atoms"], list) or len(frame["atoms"]) != 1):
        _fail("frame schema")
    atom = frame["atoms"][0]
    _exact(atom, ("k", "i"), "atom")
    if atom["k"] != "keepsake" or not isinstance(atom["i"], list) or len(atom["i"]) != 1:
        _fail("frame atom")
    ribbon = atom["i"][0]
    _exact(ribbon, ("o", "f", "s", "d", "lw", "pts"), "ribbon")
    points = ribbon["pts"]
    if (ribbon["o"] != "ribbon" or ribbon["f"] != "cyan" or ribbon["s"] != "ink"
            or isinstance(ribbon["d"], bool) or ribbon["d"] != 0
            or isinstance(ribbon["lw"], bool) or ribbon["lw"] != 2.5 or not isinstance(points, list)
            or len(points) < 2):
        _fail("frame ribbon")
    for point in points:
        if (not isinstance(point, list) or len(point) != 2
                or any(isinstance(n, bool) or not isinstance(n, (int, float))
                       or isinstance(n, float) and (not math.isfinite(n) or not n.is_integer())
                       for n in point)
                or not 0 <= point[0] <= 412 or not 0 <= point[1] <= 515):
            _fail("frame coordinates")
    return frame


def _manifest(raw):
    _text(raw, 16384, "manifest")
    value = _json(raw)
    _exact(value, ("schema", "author", "description", "voice_profile", "files"), "manifest")
    if value["schema"] != SCHEMA:
        _fail("manifest schema")
    _text(value["author"], 256, "author")
    _text(value["description"], 4096, "description")
    _hex(value["voice_profile"], HEX_64, "voice profile")
    files = value["files"]
    if not isinstance(files, list) or len(files) != 2:
        _fail("file inventory")
    for i, descriptor in enumerate(files):
        _exact(descriptor, ("name", "size", "sha256"), "file")
        size = descriptor["size"]
        if (descriptor["name"] != NAMES[i] or isinstance(size, bool)
                or not isinstance(size, (int, float))
                or isinstance(size, float) and (not math.isfinite(size) or not size.is_integer())
                or not 1 <= size <= MAX_PACKAGE):
            _fail("file descriptor")
        _hex(descriptor["sha256"], HEX_64, "file digest")
    return value


def _decode(value):
    if not isinstance(value, str) or len(value) > MAX_PACKAGE * 4 // 3 + 8:
        _fail("base64 encoding")
    try:
        data = base64.b64decode(value, validate=True)
    except (ValueError, TypeError):
        _fail("base64 encoding")
    if base64.b64encode(data).decode("ascii") != value:
        _fail("base64 padding")
    return data


def _verify_signature(public_key: bytes, signature: bytes, manifest: bytes,
                      executable="openssl"):
    command = shutil.which(executable) if os.path.sep not in executable else executable
    if not command or not os.path.isfile(command):
        _fail("OpenSSL unavailable for Ed25519 verification")
    try:
        with tempfile.TemporaryDirectory(prefix="creation-verify-") as directory:
            root = Path(directory)
            # Ed25519 raw public key wrapped in the RFC 8410 SubjectPublicKeyInfo.
            der = bytes.fromhex("302a300506032b6570032100") + public_key
            key, sig, message = root / "author.der", root / "author.sig", root / "manifest.bin"
            key.write_bytes(der)
            sig.write_bytes(signature)
            message.write_bytes(manifest)
            result = subprocess.run([command, "pkeyutl", "-verify", "-pubin", "-inkey", str(key),
                                     "-keyform", "DER", "-rawin", "-in", str(message),
                                     "-sigfile", str(sig)], capture_output=True,
                                    timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired):
        _fail("OpenSSL Ed25519 verification unavailable")
    if result.returncode:
        _fail("author signature invalid")


def validate(raw: bytes | str, openssl="openssl"):
    """Return verified package fields while retaining the original manifest."""
    if isinstance(raw, str):
        try:
            raw = raw.encode("utf-8", "strict")
        except UnicodeError:
            _fail("package UTF-8")
    if not isinstance(raw, bytes) or len(raw) > MAX_PACKAGE:
        _fail("package byte limit")
    try:
        package = _json(raw.decode("utf-8", "strict"))
    except UnicodeError:
        _fail("package UTF-8")
    _exact(package, ("schema", "manifest", "public_key", "signature", "files"), "package")
    if package["schema"] != SCHEMA:
        _fail("package schema")
    manifest_raw = package["manifest"]
    if not isinstance(manifest_raw, str):
        _fail("manifest encoding")
    try:
        manifest_bytes = manifest_raw.encode("utf-8", "strict")
    except UnicodeError:
        _fail("manifest UTF-8")
    manifest = _manifest(manifest_raw)
    files = package["files"]
    _exact(files, NAMES, "files")
    public_key = _hex(package["public_key"], HEX_64, "public key")
    signature = _hex(package["signature"], HEX_128, "signature")
    payloads = [_decode(files[name]) for name in NAMES]
    for index, data in enumerate(payloads):
        descriptor = manifest["files"][index]
        if len(data) != descriptor["size"] or hashlib.sha256(data).hexdigest() != descriptor["sha256"]:
            _fail("file hash or size")
    frame = _frame(payloads[0])
    audio = _wav(payloads[1])
    _verify_signature(public_key, signature, manifest_bytes, openssl)
    return {"id": hashlib.sha256(manifest_bytes).hexdigest(), "manifest": manifest,
            "manifest_bytes": manifest_bytes, "frame": frame, "audio": audio,
            "files": dict(zip(NAMES, payloads)), "package": package,
            "package_bytes": raw}

