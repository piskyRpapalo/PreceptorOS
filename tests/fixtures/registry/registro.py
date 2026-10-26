"""In-repository adapter fixture for the app's append-only registry contract.

This is a test double, not a copy of an external registry implementation.
External source parity remains NO_DATA because T1 did not return that source.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3

TIPOS_EVENTO = ("mensaje",)
PRIVADO = [
    (re.compile(r"\b100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b"), "IP de la tailnet"),
    (re.compile(r"/home/[A-Za-z0-9_.-]+"), "ruta /home/<usuario>"),
    (re.compile(r"ssh-(ed25519|rsa|ecdsa)\S*\s+AAAA"), "clave SSH"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "clave privada"),
    (re.compile(r"ed25519:[1-9A-HJ-NP-Za-km-z]{40,}"), "clave NEAR"),
]


class Registro:
    """Append one event to the database created by the app adapter."""

    def __init__(self, root):
        self.root = Path(root)

    def anexar_evento(self, tipo, actor, cuerpo):
        path = self.root / "eventos.db"
        body = json.dumps(cuerpo, ensure_ascii=False, sort_keys=True)
        with sqlite3.connect(path, timeout=30) as con:
            cur = con.execute(
                "INSERT INTO eventos "
                "(ts, maquina, tipo, actor, cuerpo_json, no_data_json, bloquea_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "local test fixture", tipo, actor, body, "[]", "[]"),
            )
            return {"estado": "OK", "n": cur.lastrowid}
