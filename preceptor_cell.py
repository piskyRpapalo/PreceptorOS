import argparse
import json
import os
import platform
import sys
from pathlib import Path

import casa
import entorno
import medidas
import memory


def check():
    return {"estado": "READY", "python": platform.python_version(), "configuracion_local": "present" if entorno.leer("MOTOR") else "NO_DATA"}


def initialize(root=None):
    home = Path(root) if root else Path(casa.raiz())
    home.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(home, 0o700)
    database = home / "memory.db"
    memory.crear(str(database))
    return {"estado": "READY", "almacen": "~/.preceptoros/memory.db", "tamano": database.stat().st_size,
            "hardware": {"cpu": medidas.maquina(), "ram": {"estado": "NO_DATA", "causa": "safe unit check does not collect RAM"},
                         "gpu": {"estado": "NO_DATA", "causa": "safe unit check does not identify a GPU"}},
            "listener": {"estado": "NO_DATA", "causa": "D68 prohibits opening a socket in this build"}}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--init", action="store_true")
    args = parser.parse_args(argv)
    result = check() if args.check else initialize()
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0 if result.get("estado") == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
