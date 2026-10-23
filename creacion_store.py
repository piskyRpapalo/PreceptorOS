"""Atomic, content-addressed storage for already verified creations."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile

from creacion_import import MAX_PACKAGE, validate, CreationError


class CreationStore:
    def __init__(self, root, openssl="openssl"):
        self.root = Path(root)
        self.openssl = openssl

    def _path(self, identifier):
        if not isinstance(identifier, str) or len(identifier) != 64 or any(
                c not in "0123456789abcdef" for c in identifier):
            raise CreationError("NO_DATA · creation identifier")
        return self.root / (identifier + ".json")

    def put(self, raw):
        checked = validate(raw, self.openssl)
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        destination = self._path(checked["id"])
        if destination.exists():
            previous = destination.read_bytes()
            old = validate(previous, self.openssl)
            if old["manifest_bytes"] != checked["manifest_bytes"]:
                raise CreationError("NO_DATA · creation identifier conflict")
            if old["files"] != checked["files"]:
                raise CreationError("NO_DATA · creation content conflict")
            return checked["id"], False

        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="wb", dir=self.root, prefix=".pending-",
                                             delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            # Re-read and verify bytes that will become visible.
            validate(temporary.read_bytes(), self.openssl)
            try:
                os.link(temporary, destination)
            except FileExistsError:
                existing = validate(destination.read_bytes(), self.openssl)
                if existing["id"] != checked["id"] or existing["files"] != checked["files"]:
                    raise CreationError("NO_DATA · creation identifier conflict")
                return checked["id"], False
            finally:
                temporary.unlink(missing_ok=True)
                temporary = None
            directory = os.open(self.root, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
            return checked["id"], True
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def get(self, identifier):
        path = self._path(identifier)
        try:
            raw = path.read_bytes()
        except OSError:
            return None
        checked = validate(raw, self.openssl)
        if checked["id"] != identifier:
            raise CreationError("NO_DATA · stored creation identifier mismatch")
        return checked
