"""Genera el filtro de la web DESDE el filtro del producto.

Se genera y no se transcribe a mano por una razon concreta: si la web dice
«saneado» con reglas distintas a las que usa el producto, eso es una mentira
peligrosa — la persona confia en un filtro que no es el que se probo. Aqui la
desviacion es imposible por construccion: la fuente unica es `guardrails.py`,
y este script vuelca sus patrones a JavaScript.

Se ejecuta a mano y el resultado se commitea, no se construye en el navegador:
la web no puede depender de Python para arrancar.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import guardrails as G   # noqa: E402

DESTINO = Path.home() / "preceptoros-web" / "public" / "assets" / "sanitize.js"


def a_js(patron):
    """Traduce un patron de Python a uno de JavaScript.

    Solo hay una diferencia real que tratar: Python admite `(?i)` dentro del
    patron y JavaScript no — alli la insensibilidad es una BANDERA. Se saca al
    frente y se declara. Si algun dia aparece una construccion que JS no tiene
    (por ejemplo, grupos condicionales), este script debe PARAR, no traducir a
    ojo: un patron mal traducido es peor que no tener patron.
    """
    flags = "g"
    if "(?i)" in patron:
        patron = patron.replace("(?i)", "")
        flags += "i"
    for imposible in ("(?P<", "(?(", r"\A", r"\Z", "(?#"):
        if imposible in patron:
            raise SystemExit(f"PARADO: {imposible!r} no existe en JavaScript. "
                             "Traducir a ojo seria peor que no tener el patron.")
    return patron, flags


def main():
    patrones = dict(G.PATRONES_CORE)
    for nombre, p in G.PATRONES_CUSTOM.items():
        if nombre != "NODE_PATH":     # NODE_PATH nace vacia: la pone quien la usa
            patrones[nombre] = p
    orden = [n for n in G.ORDEN if n in patrones]
    reglas = []
    for nombre in orden:
        cuerpo, flags = a_js(patrones[nombre])
        reglas.append(f"  {{ name: {json.dumps(nombre)}, re: new RegExp({json.dumps(cuerpo)}, {json.dumps(flags)}) }}")
    js = '''/* preceptoros.org · el mismo filtro que el producto, en el navegador.
   GENERADO por herramientas/generar_sanitize.py desde `guardrails.py`. No se
   edita a mano: si la web sanea con reglas distintas a las del producto, quien
   pega el resultado confia en un filtro que no es el que se probo.

   Aqui NO hay NODE_PATH: los nombres de maquina los declara cada persona en su
   instalacion, y esta pagina no los conoce. Es un hueco declarado mas.

   El orden es el del producto: lo mas especifico primero, para que una
   politica ancha no se coma lo que otra iba a marcar mejor. */
window.SANITIZE_RULES = [
''' + ",\n".join(reglas) + '''
];
window.sanitize = function (texto) {
  var hallazgos = {};
  window.SANITIZE_RULES.forEach(function (r) {
    texto = texto.replace(r.re, function () {
      hallazgos[r.name] = (hallazgos[r.name] || 0) + 1;
      return "[REDACTED:" + r.name + "]";
    });
  });
  return { texto: texto, hallazgos: hallazgos };
};
'''
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(js, encoding="utf-8")
    print(f"[generar] {DESTINO} · {DESTINO.stat().st_size} B · {len(reglas)} politicas: {orden}")


if __name__ == "__main__":
    main()
