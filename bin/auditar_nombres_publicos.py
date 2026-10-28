#!/usr/bin/env python3
"""Inventario cerrado de rutas y rótulos de identidad servidos por la PWA."""
from __future__ import annotations

import json
import os
import re
from html.parser import HTMLParser
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "docs/naming/app-public-names-allowlist.json"
RUTAS = RAIZ / "bin/preceptoros-pwa"


class Rotulos(HTMLParser):
    """Recoge títulos, nombres accesibles y encabezados; no prosa ni traducciones."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.activos: list[str] = []
        self.valores: set[str] = set()

    def handle_starttag(self, etiqueta, atributos):
        attrs = dict(atributos)
        if etiqueta in {"title", "h1", "h2", "h3", "h4", "button", "summary", "label"}:
            self.activos.append(etiqueta)
        for clave in ("aria-label", "alt", "title", "placeholder"):
            valor = attrs.get(clave, "").strip()
            if valor:
                self.valores.add(valor)

    def handle_endtag(self, etiqueta):
        if etiqueta in self.activos:
            self.activos.remove(etiqueta)

    def handle_data(self, dato):
        valor = " ".join(dato.split())
        if valor and self.activos:
            self.valores.add(valor)


def rutas_servidas():
    loader = SourceFileLoader("pwa_nombres", str(RUTAS))
    spec = spec_from_loader("pwa_nombres", loader)
    modulo = module_from_spec(spec)
    loader.exec_module(modulo)
    salida = {}
    for ruta, (fichero, mime) in sorted(modulo.ESTATICOS.items()):
        local = Path(fichero)
        if local.is_absolute():
            local = local.resolve().relative_to(RAIZ)
        else:
            local = Path("interface") / local
        salida[ruta] = local.as_posix()
    return salida


def nombres_servidos():
    fuentes = sorted({fuente for fuente in rutas_servidas().values() if fuente.endswith(".html")})
    valores = {}
    for fuente in fuentes:
        parser = Rotulos()
        parser.feed((RAIZ / fuente).read_text(encoding="utf-8"))
        valores[fuente] = sorted(parser.valores, key=str.casefold)
    manifiesto = json.loads((RAIZ / "interface/manifest.json").read_text(encoding="utf-8"))
    valores["interface/manifest.json"] = sorted(
        (x for x in (manifiesto.get("name"), manifiesto.get("short_name")) if x), key=str.casefold)
    return dict(sorted(valores.items()))


def observado():
    texto_rutas = RUTAS.read_text(encoding="utf-8")
    api_routes = sorted(set(re.findall(r"['\"](/api/[a-z0-9/_-]+/?)[\"]", texto_rutas)))
    commands = sorted(p.name for p in (RAIZ / "bin").iterdir() if p.is_file() and os.access(p, os.X_OK))
    return {
        "routes": rutas_servidas(),
        "api_routes": api_routes,
        "commands": commands,
        "names_by_source": nombres_servidos(),
    }


def coincide(esperado, actual):
    return esperado == actual


def main():
    actual = observado()
    esperado = json.loads(CATALOGO.read_text(encoding="utf-8"))
    if not coincide(esperado, actual):
        print("RED · la superficie pública cambió; clasifica cada ruta o nombre nuevo en el catálogo")
        return 1
    count = sum(len(v) for v in actual["names_by_source"].values())
    print(f"PASS · {len(actual['routes'])} routes · {count} source-bound name entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
