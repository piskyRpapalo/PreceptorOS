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
ORIGEN_HECHOS = "rack: facts (live, from main)"
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
    """Content words only, OR-joined. Function words («how», «which», «the») and bracketed tags made every
    chunk a match and let a third-party corpus outrank the house (probe 2026-11-12)."""
    palabras = _palabras(consulta)
    # A long word is searched by its 5-letter root («waiting» answers «waits»); the re-rank below keeps precision.
    return " OR ".join(('"%s"*' % w[:5]) if len(w) >= 6 else '"%s"' % w for w in palabras)


def _palabras(texto):
    """Content words of a question: 3+ letters, or a 2-letter acronym such as «PR»; no function words."""
    import memory_lookup
    out = [w.replace('"', "") for w in re.findall(r"[\w#.-]+", memory_lookup.contenido(texto), re.UNICODE)
           if len(w) > 2 or (len(w) == 2 and w.isupper())]
    return list(dict.fromkeys(out))[:12]


def _raices(texto):
    import unicodedata
    plano = "".join(ch for ch in unicodedata.normalize("NFKD", texto.lower()) if not unicodedata.combining(ch))
    return {w[:5] for w in re.findall(r"\w+", plano)}


def _cubre(texto, raices):
    """How many distinct roots of the question a chunk holds."""
    return len(raices & _raices(texto))


def hechos(app_sw, app_html, web_sw, prs, medido):
    """Live facts of the house as plain sentences Hexelion can quote exactly. Each value is read from main by
    the builder; a value that cannot be read is said as NO_DATA with its cause, never guessed.
    prs: [(repo, number, title, head_sha)] of open pull requests."""
    def uno(patron, texto, causa):
        m = re.search(patron, texto or "")
        return m.group(1) if m else "NO_DATA (%s)" % causa
    lineas = [
        "Measured from main at %s." % medido,
        "The current app cache version on main is %s (interface/sw.js)." % uno(r'const Cache = "([^"]+)"', app_sw, "app sw.js unreadable"),
        "The current app script version on main is app.js?v=%s and notebook.js?v=%s (interface/app.html)." % (
            uno(r"app\.js\?v=(\d+)", app_html, "app.html unreadable"), uno(r"notebook\.js\?v=(\d+)", app_html, "app.html unreadable")),
        "The current web service worker version on main is %s (public/sw.js)." % uno(r"const VERSION = '([^']+)'", web_sw, "web sw.js unreadable"),
        "To run the app gate: bin/pruebas --rapido for the fast gate, bin/pruebas for the full gate (AGENTS.md).",
        "To run the web gate: python3 test_web.py, then node atlas/version_sw_gate.mjs (preceptoros-web).",
    ]
    hitl = [(r, n, t, h) for r, n, t, h in prs if str(t).startswith("HITL")]
    if hitl:
        lineas.append("Each open PR that waits for signature (HITL) now: " + "; ".join(
            "%s #%d %s at head %s" % (r, n, str(t)[7:90], str(h)[:8]) for r, n, t, h in hitl) + ".")
    else:
        lineas.append("Each open PR that waits for signature (HITL) now: none.")
    return "\n\n".join(lineas)


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
                                " order by bm25(trozos, 4.0, 2.0, 1.0) limit ?", (q, int(limite) * 12)).fetchall()
        # Re-rank: the chunk that holds MORE distinct words of the question comes first; bm25 breaks ties (stable
        # sort). Plain bm25 let a PR body that repeats one word beat the one line that holds all of them.
        raices = {w.lower()[:5] for w in _palabras(consulta)}
        # At equal coverage a live fact measured from main beats a document that talks about the same value.
        filas = sorted(filas, key=lambda f: (-_cubre(f[1], raices), not f[1].startswith(ORIGEN_HECHOS)))[:int(limite)]
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
