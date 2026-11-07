"""Signed, chunked download of PWA files from GitHub with verify-before-install.

Extends lora_signed_download: no network or disk I/O until consent is True,
every chunk and the whole file are checked before os.replace. The manifest
carries no URLs; the origin is built here, so it cannot be injected.
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
from lora_signed_download import Refused, _unique, HEX

SCHEMA = 'preceptoros.descarga/1'
RECEIPT = 'preceptoros.descarga-recibo/1'
RAW = 'https://raw.githubusercontent.com/piskyRpapalo/PreceptorOS/'
RELEASE = 'https://github.com/piskyRpapalo/PreceptorOS/releases/download/'
RELEASE_HOST = 'release-assets.githubusercontent.com'
CHUNK_MAX = 16 * 1024 * 1024
SHA40 = re.compile(r'^[0-9a-f]{40}$')
TAG = re.compile(r'^v\d+(\.\d+){0,2}$')
SEGMENT = re.compile(r'^[A-Za-z0-9._-]+$')
BAD_EXT = ('.gguf', '.safetensors', '.bin', '.pt', '.onnx', '.jsonl')
BAD_WORDS = ('lora', 'adapter', 'dataset')


class Redirect(HTTPRedirectHandler):
    """Allow exactly one 302, release via only, https to the release host."""
    def __init__(self, via):
        self.via, self.used = via, False

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        u = urlsplit(newurl)
        if self.via != 'release' or self.used or code != 302 or u.scheme != 'https' or u.netloc != RELEASE_HOST:
            raise Refused('redirect_refused')
        self.used = True
        return Request(newurl)


def _check_path(name):
    if not isinstance(name, str) or not name or name.startswith('/') or '\\' in name:
        raise Refused('fichero_invalid')
    parts = name.split('/')
    if any(p.lower().endswith(BAD_EXT) or any(w in p.lower() for w in BAD_WORDS) for p in parts):
        raise Refused('model_data_never_leaves')
    if len(parts) < 2 or parts[0] != 'interface' or any(p in ('.', '..') or not SEGMENT.fullmatch(p) for p in parts):
        raise Refused('fichero_invalid')


def _is_sha(v):
    return isinstance(v, str) and bool(HEX.fullmatch(v))


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
    if not isinstance(obj, dict) or set(obj) != {'schema', 'ref', 'via', 'files'} or obj['schema'] != SCHEMA:
        raise Refused('manifest schema')
    ref, via, files = obj['ref'], obj['via'], obj['files']
    if via == 'edge':
        raise Refused('edge_route_not_published')
    if via not in ('raw', 'release'):
        raise Refused('via_invalid')
    if not isinstance(ref, str) or not (SHA40 if via == 'raw' else TAG).fullmatch(ref):
        raise Refused('ref_not_exact')
    if not isinstance(files, list) or not 0 < len(files) <= 256:
        raise Refused('files')
    seen = set()
    for e in files:
        if not isinstance(e, dict) or set(e) != {'fichero', 'bytes', 'sha256', 'chunks'}:
            raise Refused('file schema')
        _check_path(e['fichero'])
        if e['fichero'] in seen: raise Refused('duplicate fichero')
        seen.add(e['fichero'])
        if type(e['bytes']) is not int or e['bytes'] <= 0 or not _is_sha(e['sha256']):
            raise Refused('file metadata')
        ch = e['chunks']
        if not isinstance(ch, list) or not 0 < len(ch) <= 1024: raise Refused('chunks')
        total = 0
        for c in ch:
            if not isinstance(c, dict) or set(c) != {'bytes', 'sha256'} or type(c['bytes']) is not int or not 0 < c['bytes'] <= CHUNK_MAX or not _is_sha(c['sha256']):
                raise Refused('chunk metadata')
            total += c['bytes']
        if total != e['bytes']: raise Refused('chunk sizes')
    return obj


def url_for(manifest, entry):
    if manifest['via'] == 'raw':
        return f"{RAW}{manifest['ref']}/{entry['fichero']}"
    # Release assets are flat: only the basename is an asset name.
    return f"{RELEASE}{manifest['ref']}/{entry['fichero'].rsplit('/', 1)[-1]}"


def instalar(raw, signature, trusted_key, fichero, raiz_destino, consent=False, opener=None):
    if consent is not True: raise Refused('consent required')
    manifest = verify_manifest(raw, signature, trusted_key)
    entry = next((f for f in manifest['files'] if f['fichero'] == fichero), None)
    if entry is None: raise Refused('unknown fichero')
    root = Path(raiz_destino).resolve()
    dest = (root / fichero).resolve()
    if root not in dest.parents: raise Refused('destination_outside_root')
    opener = opener or build_opener(Redirect(manifest['via']))
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix='.descarga-', dir=dest.parent)
    chunks = []
    try:
        whole = hashlib.sha256()
        with os.fdopen(fd, 'wb') as out, opener.open(Request(url_for(manifest, entry)), timeout=30) as resp:
            if getattr(resp, 'status', 200) != 200: raise Refused('http_status')
            for n, c in enumerate(entry['chunks']):
                digest, left = hashlib.sha256(), c['bytes']
                while left:
                    block = resp.read(min(65536, left))
                    if not block: raise Refused('truncated')
                    left -= len(block); digest.update(block); whole.update(block); out.write(block)
                if digest.hexdigest() != c['sha256']: raise Refused('chunk_digest')
                chunks.append({'n': n, 'bytes': c['bytes'], 'sha256': c['sha256'], 'estado': 'OK'})
            if resp.read(1): raise Refused('size_mismatch')
            if whole.hexdigest() != entry['sha256']: raise Refused('file_digest')
            out.flush(); os.fsync(out.fileno())
        os.replace(temp, dest)
    finally:
        if os.path.exists(temp): os.unlink(temp)
    return {'esquema': RECEIPT, 'ref': manifest['ref'], 'via': manifest['via'], 'fichero': fichero,
            'bytes': entry['bytes'], 'sha256': entry['sha256'], 'chunks': chunks}
