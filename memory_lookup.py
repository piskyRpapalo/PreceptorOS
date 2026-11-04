"""Bounded, read-only lexical evidence from the existing memory; no model calls."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3

import memory

SCHEMA = 'preceptoros.memory-search/1'


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


def unavailable(cause):
    return {'esquema': SCHEMA, 'estado': 'NO_DATA', 'causa': cause,
            'fuentes': [], 'fuera': 0, 'completo': False}


def buscar(consulta, database):
    """Return whole source fields and citations under the complete JSON byte ceiling.

    Completeness covers at most 50 FTS candidates, never the entire database.
    Hashes cover exactly the displayed text, not a second persisted copy.
    """
    if type(consulta) is not str or not consulta.strip() or len(consulta) > 600:
        return unavailable('query_invalid')
    try:
        if len(consulta.encode('utf-8')) >= 1024:
            return unavailable('query_too_large')
        db = Path(database)
        if not db.is_file() or db.is_symlink():
            return unavailable('memory_unavailable')
        with closing(sqlite3.connect(db.resolve().as_uri() + '?mode=ro', uri=True, timeout=1.0)) as con:
            con.row_factory = sqlite3.Row
            con.execute('pragma query_only=on')
            if not memory._tabla_existe(con, 'engrams_fts'):
                return unavailable('memory_index_unavailable')
            found = memory.recuperar(con, consulta, presupuesto=240, candidatos=50)
    except (OSError, sqlite3.Error, memory.BusquedaNoDisponible, ValueError, UnicodeError):
        return unavailable('memory_read_failed')
    out = {'esquema': SCHEMA, 'estado': 'MEASURED', 'fuentes': [],
           'fuera': found['fuera'], 'completo': found['completo'], 'limite_candidatos': 50}
    for row in found['engramas']:
        text = '\n'.join(k + ': ' + str(row.get(k) or '') for k in memory.CAMPOS_QUE_VIAJAN)
        source = {'id': row['id'], 'updated_at': row['updated_at'],
                  'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(), 'texto': text}
        out['fuentes'].append(source)
        # Reserve conservative counter/flag room before accepting a whole source.
        preview = dict(out, completo=False, fuera=50)
        if len(encoded(preview)) >= 1024:
            out['fuentes'].pop()
            out['fuera'] += 1
    out['completo'] = out['fuera'] == 0 and found['candidatos'] < 50
    if not out['fuentes']:
        result = unavailable('evidence_exceeds_budget' if found['candidatos'] else 'no_matches')
        result['fuera'] = found['candidatos']
        return result
    assert len(encoded(out)) < 1024
    return out
