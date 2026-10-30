"""Opt-in, signed manifest and bounded verified adapter download.

The caller supplies an independently trusted Ed25519 public key. This module
performs no network or filesystem operation until consent is explicitly True.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

from creacion_import import _verify_signature

ORIGIN = 'downloads.preceptoros.org'
LIMIT = 16 * 1024 * 1024
HEX = re.compile(r'^[0-9a-f]{64}$')
NAME = re.compile(r'^preceptor-[a-z0-9-]+\.gguf$')

class Refused(ValueError):
    pass

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise Refused('redirect refused')

def verify_manifest(raw, signature, trusted_key):
    if not isinstance(raw, bytes) or len(raw) > 65536:
        raise Refused('manifest size')
    if not isinstance(signature, bytes) or len(signature) != 64 or not isinstance(trusted_key, bytes) or len(trusted_key) != 32:
        raise Refused('missing signature or trusted key')
    try:
        _verify_signature(trusted_key, signature, raw)
        obj = json.loads(raw, object_pairs_hook=_unique)
    except Exception as exc:
        raise Refused('signature or manifest invalid') from exc
    if not isinstance(obj, dict) or set(obj) != {'schema', 'adapters'} or obj['schema'] != 'preceptoros.lora-download/1' or not isinstance(obj['adapters'], list) or len(obj['adapters']) != 5:
        raise Refused('manifest schema')
    names = set()
    for item in obj['adapters']:
        if not isinstance(item, dict) or set(item) != {'name', 'url', 'size', 'sha256', 'chunks'}:
            raise Refused('adapter schema')
        name, url, size, digest, chunks = (item[k] for k in ('name', 'url', 'size', 'sha256', 'chunks'))
        if not isinstance(name, str) or not NAME.fullmatch(name) or name in names: raise Refused('adapter name')
        names.add(name)
        if not isinstance(url, str): raise Refused('adapter url')
        u = urlsplit(url)
        if u.scheme != 'https' or u.netloc != ORIGIN or u.path != '/downloads/' + name or u.query or u.fragment:
            raise Refused('adapter origin')
        if type(size) is not int or size <= 0 or size > 2**31 or not isinstance(digest, str) or not HEX.fullmatch(digest):
            raise Refused('adapter metadata')
        if not isinstance(chunks, list) or not chunks or len(chunks) > 1024: raise Refused('chunks')
        total = 0
        for c in chunks:
            if not isinstance(c, dict) or set(c) != {'size', 'sha256'} or type(c['size']) is not int or not 0 < c['size'] <= LIMIT or not isinstance(c['sha256'], str) or not HEX.fullmatch(c['sha256']):
                raise Refused('chunk metadata')
            total += c['size']
        if total != size: raise Refused('chunk sizes')
    return obj

def _unique(pairs):
    out = {}
    for k, v in pairs:
        if k in out: raise Refused('duplicate key')
        out[k] = v
    return out

def download(raw, signature, trusted_key, name, destination, consent=False, opener=None):
    if consent is not True: raise Refused('consent required')
    manifest = verify_manifest(raw, signature, trusted_key)
    adapter = next((a for a in manifest['adapters'] if a['name'] == name), None)
    if adapter is None: raise Refused('unknown adapter')
    destination = Path(destination)
    if destination.name != name: raise Refused('destination name')
    opener = opener or build_opener(NoRedirect())
    fd, temp = tempfile.mkstemp(prefix='.lora-', dir=destination.parent)
    try:
        whole = hashlib.sha256()
        with os.fdopen(fd, 'wb') as out, opener.open(Request(adapter['url']), timeout=30) as response:
            for chunk in adapter['chunks']:
                digest, remaining = hashlib.sha256(), chunk['size']
                while remaining:
                    block = response.read(min(65536, remaining))
                    if not block: raise Refused('truncated download')
                    remaining -= len(block); digest.update(block); whole.update(block); out.write(block)
                if digest.hexdigest() != chunk['sha256']: raise Refused('chunk digest')
            if response.read(1) or whole.hexdigest() != adapter['sha256']: raise Refused('file digest or size')
            out.flush(); os.fsync(out.fileno())
        os.replace(temp, destination)
    finally:
        if os.path.exists(temp): os.unlink(temp)
    return destination
