#!/usr/bin/env python3
"""firmas_pendientes.py · the open fronts that wait for the Sovereign. **Stdlib only, pure.**

The scraper (bin/firmas-scraper) feeds it the open PRs of each repo and the comments of
buzon#30; it returns `preceptoros.firmas-pendientes/1`, which the Command tab paints.

A signature is counted exactly as the fence counts it (web `atlas/hitl_fence.py:31`,
`decide`): a comment that carries «FIRMA SOBERANO» and one line
`HITL: <sha40> <slug> <YYYY-MM-DD>` for the exact head, dated between the head and today.
This module only reads and proposes the text; it never writes the signature. Signing is
the Sovereign's act (AGENTS.md: the HITL line is never written by silicon).
"""

import re

ESQUEMA = "preceptoros.firmas-pendientes/1"
CABECERA = "FIRMA SOBERANO"
LINEA = re.compile(r"^HITL: ([0-9a-f]{40}) ([A-Za-z0-9#._-]+) (\d{4}-\d{2}-\d{2})$")
SHA = re.compile(r"^[0-9a-f]{40}$")
MAX_FILAS = 40
# The hitl check is the signature itself; it is red until the Sovereign signs, so it never
# decides whether the rest of the CI is green.
CHEQUEOS_DE_FIRMA = {"hitl"}
ORDEN = {"retarget": 0, "sign": 1, "merge": 2, "running": 3, "red": 4, "wait_base": 5, "no_data": 6}


def lineas_firmadas(comentarios):
    """{sha40: [date, ...]} from buzon#30 comments, the fence's rules."""
    firmadas = {}
    for c in comentarios or []:
        cuerpo = (c.get("body") if isinstance(c, dict) else None) or ""
        if CABECERA not in cuerpo:
            continue
        for linea in cuerpo.splitlines():
            m = LINEA.match(linea.strip())
            if m:
                firmadas.setdefault(m.group(1), []).append(m.group(3))
    return firmadas


def estado_chequeos(rollup):
    """green / red / running / no_data over every check except the signature check."""
    if not isinstance(rollup, list):
        return "no_data"
    vistos = []
    for ch in rollup:
        if not isinstance(ch, dict):
            continue
        nombre = (ch.get("name") or ch.get("context") or "").lower()
        if nombre in CHEQUEOS_DE_FIRMA:
            continue
        estado = (ch.get("conclusion") or ch.get("state") or ch.get("status") or "").upper()
        vistos.append(estado)
    if not vistos:
        return "no_data"
    if any(e in ("FAILURE", "ERROR", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED") for e in vistos):
        return "red"
    if all(e in ("SUCCESS", "NEUTRAL", "SKIPPED") for e in vistos):
        return "green"
    return "running"


def slug(rama):
    """Piece slug from the branch: last path part, without the trailing date."""
    base = (rama or "").rsplit("/", 1)[-1]
    base = re.sub(r"-20\d{6}$", "", base)
    base = re.sub(r"[^A-Za-z0-9#._-]", "-", base).strip("-")
    return base or "piece"


def texto_firma(sha, rama, hoy):
    """The exact comment body the fence accepts. The Sovereign posts it; nothing here does."""
    return CABECERA + "\nHITL: " + sha + " " + slug(rama) + " " + hoy


def fila(repo, pr, firmadas, hoy, ramas_abiertas=frozenset()):
    """One open PR → one card. Never raises: a bad PR gives a no_data card.

    A PR stacked on a branch that no open PR carries any more has a dead base: merging it
    lands nowhere (measured 2026-11-07: #218 merged into the already merged #213 branch).
    """
    try:
        n, sha = int(pr["number"]), pr.get("headRefOid") or ""
        base, rama = pr.get("baseRefName") or "", pr.get("headRefName") or ""
        checks = estado_chequeos(pr.get("statusCheckRollup"))
        fechas = firmadas.get(sha, []) if SHA.match(sha) else []
        # A line names the exact head, so it cannot predate that commit; the date must not be future.
        firmada = any(f <= hoy for f in fechas)
        apilada = base not in ("main", "master")
        if not SHA.match(sha):
            accion, causa = "no_data", "head_not_sha40"
        elif apilada and base not in ramas_abiertas:
            accion, causa = "retarget", "base_branch_not_open"
        elif apilada:
            accion, causa = "wait_base", "stacked_on_" + base
        elif checks == "red":
            accion, causa = "red", "checks_red"
        elif checks in ("running", "no_data"):
            accion, causa = "running", "checks_" + checks
        elif firmada:
            accion, causa = "merge", "signed_exact_head"
        else:
            accion, causa = "sign", "green_unsigned"
        r = {"repo": repo, "n": n, "title": (pr.get("title") or "")[:120], "url": pr.get("url") or "",
             "head": sha[:12], "base": base, "draft": bool(pr.get("isDraft")), "checks": checks,
             "signed": firmada, "action": accion, "cause": causa}
        if accion == "sign":
            r["signature"] = texto_firma(sha, rama, hoy)
        if accion == "retarget":
            r["retarget"] = "gh pr edit %d -R %s --base main" % (n, repo)
        if accion in ("sign", "merge"):
            r["merge"] = "gh pr ready %d -R %s; gh pr merge %d -R %s --merge" % (n, repo, n, repo)
        return r
    except (KeyError, TypeError, ValueError, AttributeError):
        return {"repo": repo, "n": None, "title": "", "action": "no_data", "cause": "malformed_pr",
                "checks": "no_data", "signed": False}


def documento(prs_por_repo, comentarios, hoy, medido, causas=None):
    """{repo: [pr...]}, buzon#30 comments, today (YYYY-MM-DD) and the scrape time, both passed in."""
    firmadas = lineas_firmadas(comentarios)
    filas = []
    for repo, prs in sorted((prs_por_repo or {}).items()):
        abiertas = frozenset(pr.get("headRefName") for pr in (prs or []) if isinstance(pr, dict))
        filas += [fila(repo, pr, firmadas, hoy, abiertas) for pr in (prs or [])]
    filas.sort(key=lambda f: (ORDEN.get(f["action"], 9), f["repo"], f["n"] or 0))
    cuenta = {}
    for f in filas:
        cuenta[f["action"]] = cuenta.get(f["action"], 0) + 1
    no_data = [{"campo": k, "causa": v} for k, v in sorted((causas or {}).items())]
    if len(filas) > MAX_FILAS:
        no_data.append({"campo": "rows", "causa": "over_%d_trimmed" % MAX_FILAS})
        filas = filas[:MAX_FILAS]
    return {"esquema": ESQUEMA, "medido": medido, "hoy": hoy, "cuenta": cuenta, "filas": filas,
            "no_data": no_data}
