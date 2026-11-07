#!/usr/bin/env python3
"""indice_rack.py · Hexelion's second shelf: the rack and GitHub, as exact quotes. **Stdlib only.**

The memory (memory.db) holds the person's turns. This index holds the house: the docs of p0x,
PreceptorOS and the web as they stand on main, the signature book, open and recent PRs, and the
mailboxes. bin/indice-rack builds it from a user timer; the chat only reads it (mode=ro).

Contract: `buscar()` returns the same `preceptoros.memory-search/1` shape that hexelion_book
validates, so the evidence rule never changes: exact quotes or NO_DATA. Each source text starts
with its origin line («rack: p0x/mente/x.md» or «github: owner/repo#12»), so a citation always
says where it came from. Ids live above 1e9, never colliding with memory engram ids.
Lines that look like secrets are dropped before indexing; they never reach a prompt.
"""

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path

SCHEMA = "preceptoros.memory-search/1"
ID_BASE = 1_000_000_000
CHUNK_B = 340          # one chunk; two of them fit the 768 B source budget with memory beside
MAX_DOC_B = 65536      # a file larger than this is read only up to here
SECRETO = re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd|private key|BEGIN [A-Z ]*PRIVATE|"
                     r"\bsk-[A-Za-z0-9]{8,}|gh[pousr]_|github_pat_|mstrl_|xox[abp]-|AKIA[0-9A-Z]{12,})")
RUTA_SECRETA = re.compile(r"(?i)secret|credential|\.env\b|password|token")


def limpio(texto):
    """Drop every line that looks like a secret; collapse blank runs."""
    lineas = [l.rstrip() for l in (texto or "").splitlines() if not SECRETO.search(l)]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lineas)).strip()


def trozos(origen, texto):
    """Paragraph chunks ≤ CHUNK_B bytes, each starting with its origin line."""
    cabeza = origen + "\n"
    cupo = CHUNK_B - len(cabeza.encode("utf-8"))
    out, actual = [], ""
    for par in re.split(r"\n\s*\n", limpio(texto)):
        par = par.strip()
        while par:
            pieza = par.encode("utf-8")[:cupo].decode("utf-8", "ignore")
            if len(pieza) < len(par):              # cut at the last space inside the budget
                corte = pieza.rfind(" ")
                pieza = pieza[:corte] if corte > cupo // 3 else pieza
            par = par[len(pieza):].strip()
            if actual and len((actual + "\n" + pieza).encode("utf-8")) > cupo:
                out.append(cabeza + actual)
                actual = pieza
            else:
                actual = (actual + "\n" + pieza).strip()
    if actual:
        out.append(cabeza + actual)
    return out


def construir(db, documentos):
    """documentos: iterable of (origen, titulo, texto, actualizado). Writes a fresh FTS5 index."""
    db = Path(db)
    db.parent.mkdir(parents=True, exist_ok=True)
    tmp = db.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    n = 0
    with closing(sqlite3.connect(tmp)) as con:
        con.execute("create virtual table trozos using fts5(origen, titulo, texto, actualizado unindexed,"
                    " tokenize='unicode61 remove_diacritics 2')")
        for origen, titulo, texto, actualizado in documentos:
            if RUTA_SECRETA.search(origen or ""):
                continue
            for t in trozos(origen, texto[:MAX_DOC_B] if isinstance(texto, str) else ""):
                con.execute("insert into trozos values (?,?,?,?)", (origen, titulo or "", t, actualizado or ""))
                n += 1
        con.commit()
    tmp.replace(db)
    return n


def _consulta_fts(consulta):
    palabras = [w for w in re.findall(r"[\w#.-]+", consulta, re.UNICODE) if len(w) > 2][:12]
    return " OR ".join('"' + w.replace('"', "") + '"' for w in palabras)


def no_data(causa):
    return {"esquema": SCHEMA, "estado": "NO_DATA", "causa": causa, "fuentes": [], "fuera": 0, "completo": False}


def buscar(consulta, db, limite=4):
    """Ranked exact chunks for a question, in the memory-search contract. Never raises."""
    if type(consulta) is not str or not consulta.strip() or len(consulta.encode("utf-8")) >= 1024:
        return no_data("query_invalid")
    q = _consulta_fts(consulta)
    if not q:
        return no_data("query_has_no_words")
    try:
        db = Path(db)
        if not db.is_file() or db.is_symlink():
            return no_data("rack_index_not_built")
        with closing(sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True, timeout=1.0)) as con:
            con.execute("pragma query_only=on")
            filas = con.execute("select rowid, texto, actualizado from trozos where trozos match ?"
                                " order by bm25(trozos, 4.0, 2.0, 1.0) limit ?", (q, int(limite))).fetchall()
    except (OSError, sqlite3.Error, ValueError):
        return no_data("rack_index_read_failed")
    if not filas:
        return no_data("rack_no_match")
    fuentes = [{"id": ID_BASE + rid, "updated_at": act or "unknown",
                "sha256": hashlib.sha256(txt.encode("utf-8")).hexdigest(), "texto": txt}
               for rid, txt, act in filas]
    return {"esquema": SCHEMA, "estado": "MEASURED", "fuentes": fuentes, "fuera": 0, "completo": True,
            "limite_candidatos": int(limite)}


def unir(memoria, rack, presupuesto=768, maximo=3):
    """Interleave memory and rack sources (memory first) under the book's byte and count budget."""
    listas = [e.get("fuentes") or [] for e in (memoria, rack)
              if isinstance(e, dict) and e.get("estado") == "MEASURED"]
    if not listas:
        causas = [e.get("causa") for e in (memoria, rack) if isinstance(e, dict) and e.get("causa")]
        return no_data(causas[0] if causas else "no_evidence")   # memory first: its cause leads
    elegidas, usados, i = [], 0, 0
    while len(elegidas) < maximo and any(i < len(l) for l in listas):
        for l in listas:
            if i < len(l) and len(elegidas) < maximo:
                b = len(l[i]["texto"].encode("utf-8"))
                if usados + b <= presupuesto:
                    elegidas.append(l[i]); usados += b
        i += 1
    if not elegidas:
        return no_data("evidence_over_budget")
    return {"esquema": SCHEMA, "estado": "MEASURED", "fuentes": elegidas, "fuera": 0, "completo": False,
            "limite_candidatos": 50}


if __name__ == "__main__":
    import sys
    print(json.dumps(buscar(" ".join(sys.argv[2:]), sys.argv[1]), ensure_ascii=False, indent=1))
