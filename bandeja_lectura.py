"""Read the versioned local tray, without creating or modifying it."""
import json
import os
from pathlib import Path

LIMIT = 65536


def leer(raiz):
    resultado = {}
    for nombre in ('huecos', 'coberturas'):
        path = Path(raiz) / 'data' / 'bandeja' / (nombre + '.jsonl')
        try:
            if path.is_symlink() or path.parent.is_symlink():
                raise ValueError('unsafe_path')
            with open(path, 'rb') as stream:
                raw = stream.read(LIMIT + 1)
            if len(raw) > LIMIT:
                raise ValueError('too_large')
            rows = [json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()]
            if any(type(row) is not dict for row in rows):
                raise ValueError('invalid_row')
            resultado[nombre] = {'estado': 'MEASURED', 'filas': rows}
        except (OSError, UnicodeError, ValueError):
            resultado[nombre] = {'estado': 'NO_DATA', 'causa': 'bandeja_ausente_o_invalida'}
    return resultado
