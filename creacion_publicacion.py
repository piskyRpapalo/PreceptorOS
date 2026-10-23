"""Local publication helpers for author-signed creation packages."""
from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from creacion_import import CreationError

MAX_PACKAGE = 25 * 1024 * 1024
ASSET_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
}


def origen_local_valido(origin: str | None, host: str | None, port: int) -> bool:
    """Accept only an exact HTTP same-origin request addressed to loopback."""
    if not isinstance(origin, str) or not isinstance(host, str) or not origin or not host:
        return False
    try:
        parsed = urlsplit(origin)
        hostname = parsed.hostname
        if (parsed.scheme != "http" or parsed.username or parsed.password or parsed.path
                or parsed.query or parsed.fragment or parsed.netloc.casefold() != host.casefold()
                or parsed.port != port or not hostname):
            return False
        try:
            local = ipaddress.ip_address(hostname).is_loopback
        except ValueError:
            local = hostname.casefold() == "localhost"
        return local
    except ValueError:
        return False


def asset_manifest(root):
    path = Path(root) / "manifest.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        raise CreationError("NO_DATA · creation resources unavailable") from None
    if (not isinstance(data, dict) or set(data) != {"schema", "files"}
            or data["schema"] != "preceptoros.creation-view/1"
            or not isinstance(data["files"], dict)):
        raise CreationError("NO_DATA · creation resource manifest invalid")
    return data["files"]


def read_asset(root, name):
    """Read one pinned file by a closed relative name and verify its digest."""
    if not isinstance(name, str) or not name or name.startswith("/") or ".." in name.split("/"):
        raise CreationError("NO_DATA · creation resource name")
    manifest = asset_manifest(root)
    if name == "manifest.json":
        try:
            return (Path(root) / name).read_bytes(), "application/json; charset=utf-8"
        except OSError:
            raise CreationError("NO_DATA · creation resource manifest missing") from None
    descriptor = manifest.get(name)
    if (not isinstance(descriptor, dict) or set(descriptor) != {"sha256", "size"}
            or not isinstance(descriptor["sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", descriptor["sha256"])
            or isinstance(descriptor["size"], bool)
            or not isinstance(descriptor["size"], int) or descriptor["size"] < 0):
        raise CreationError("NO_DATA · creation resource is not pinned")
    path = Path(root).joinpath(*name.split("/"))
    try:
        resolved = path.resolve(strict=True)
        base = Path(root).resolve(strict=True)
        if base not in resolved.parents or not resolved.is_file():
            raise OSError("path outside distribution")
        data = resolved.read_bytes()
    except OSError:
        raise CreationError("NO_DATA · creation resource missing") from None
    if (len(data) != descriptor["size"]
            or hashlib.sha256(data).hexdigest() != descriptor["sha256"]):
        raise CreationError("NO_DATA · creation resource digest mismatch")
    media = ASSET_TYPES.get(resolved.suffix.lower())
    if media is None:
        raise CreationError("NO_DATA · creation resource type")
    return data, media
