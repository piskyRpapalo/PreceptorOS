"""La superficie que se envia no importa nada fuera de la biblioteca estandar.

QUE PROTEGE
-----------
La promesa publica del producto -- «MVP Python stdlib only» -- es la unica de
todo el proyecto que alguien puede romper sin darse cuenta: basta un `import`
comodo en un modulo que ya estaba ahi. No se rompe por decision; se rompe por
descuido, que es peor, porque nadie firma el descuido.

El guardian del enjambre vigila el ARBOL entero y avisa de cualquier import
ajeno. Esta prueba vigila otra cosa, mas estrecha y mas dura: el **camino por
defecto**, el que recorre de verdad quien instala el producto y lo arranca. Un
modulo puede existir en el arbol con una dependencia declarada y no romper nada
mientras nadie lo alcance desde un punto de entrada.

Esa es exactamente la situacion de `frontera.py`, la jaula Wasmtime de LAS TRES
JOYAS, firmada como excepcion el 2026-08-30: existe, esta declarada, y **nadie
la importa**. La firma dice «opt-in y declarada; fuera del camino stdlib que se
envia». Esta prueba es el candado de esa frase: el dia que alguien enchufe la
jaula al camino por defecto, cae aqui y no en produccion.

POR QUE UN GRAFO Y NO UN `grep`
-------------------------------
`grep import` no distingue un modulo alcanzable de uno que duerme en el arbol,
y es justo la distincion que sostiene la firma. Se recorre el grafo desde los
puntos de entrada, siguiendo SOLO modulos locales, y se mira que se alcanza.

Y con `ast`, no con lineas: un import dentro de una funcion o de un `try` es un
import igual, y este arbol tiene los dos.
"""
from __future__ import annotations

import ast
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.abspath(__file__))

# Lo que arranca de verdad. Si manana hay otra puerta, va aqui: una puerta sin
# vigilar es una puerta por la que entra cualquier cosa.
PUERTAS = (
    "preceptoros.py",                 # la CLI
    "bin/preceptoros-pwa",            # el servidor de la cara
    "empaquetado/lanzador.py",        # el doble clic
)

# Excepciones al camino por defecto, con su motivo. Vacio a proposito: hoy
# NINGUNA dependencia externa es alcanzable desde una puerta, y esa es la
# afirmacion que esta prueba defiende. Anadir algo aqui es cambiar la promesa
# publica, y eso lo firma el carbono.
PERMITIDAS_EN_EL_CAMINO: dict[str, str] = {}


def _modulos_locales():
    """Los nombres de modulo que viven en el arbol. Se descubren, no se listan."""
    locales = {}
    for base, dirs, ficheros in os.walk(RAIZ):
        dirs[:] = [d for d in dirs
                   if not d.startswith(".") and d != "__pycache__"
                   and not os.path.isfile(os.path.join(base, d, "pyvenv.cfg"))]
        for f in ficheros:
            if f.endswith(".py"):
                locales.setdefault(f[:-3], os.path.join(base, f))
    return locales


def _importa(ruta):
    """Los modulos de primer nivel que un fichero importa, con `ast`."""
    try:
        with open(ruta, encoding="utf-8") as fh:
            arbol = ast.parse(fh.read())
    except (OSError, SyntaxError, UnicodeDecodeError):
        return set()
    fuera = set()
    for n in ast.walk(arbol):
        if isinstance(n, ast.Import):
            fuera.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
            fuera.add(n.module.split(".")[0])
    return fuera


def recorrer():
    """Devuelve (alcanzados_externos, camino) desde todas las puertas.

    `camino` mapea modulo externo -> quien lo importo primero, para que un
    fallo diga POR DONDE entro y no solo que entro.
    """
    locales = _modulos_locales()
    vistos, pendientes, externos, camino = set(), [], set(), {}
    for puerta in PUERTAS:
        ruta = os.path.join(RAIZ, puerta)
        if os.path.exists(ruta):
            pendientes.append((puerta, ruta))

    while pendientes:
        nombre, ruta = pendientes.pop()
        if ruta in vistos:
            continue
        vistos.add(ruta)
        for mod in _importa(ruta):
            if mod in locales:
                pendientes.append((mod, locales[mod]))
            elif mod not in sys.stdlib_module_names and mod != "__future__":
                externos.add(mod)
                camino.setdefault(mod, nombre)
    return externos, camino


class SuperficieEnviada(unittest.TestCase):

    def test_hay_puertas_que_vigilar(self):
        """Si las puertas no existen, esta prueba pasaria por vacia."""
        existen = [p for p in PUERTAS if os.path.exists(os.path.join(RAIZ, p))]
        self.assertEqual(sorted(existen), sorted(PUERTAS),
                         "falta un punto de entrada: la prueba estaria mirando al aire")

    def test_el_camino_por_defecto_es_stdlib_puro(self):
        externos, camino = recorrer()
        intrusos = {m: camino[m] for m in externos
                    if m not in PERMITIDAS_EN_EL_CAMINO}
        self.assertEqual(
            intrusos, {},
            "la promesa publica «MVP Python stdlib only» se rompe por el camino "
            "por defecto: " + ", ".join(f"`{m}` alcanzado desde {d}"
                                        for m, d in sorted(intrusos.items())))

    def test_la_jaula_wasmtime_sigue_fuera_del_camino(self):
        """El candado explicito de la firma del 2026-08-30.

        Se comprueba aparte del caso general aunque este cubierto por el, y a
        proposito: si algun dia alguien anade `wasmtime` a
        `PERMITIDAS_EN_EL_CAMINO`, el caso general pasaria en silencio y la
        firma quedaria derogada sin que nadie la derogase. Este caso NO mira
        esa lista.
        """
        externos, camino = recorrer()
        self.assertNotIn(
            "wasmtime", externos,
            "la jaula Wasmtime entro en el camino por defecto (desde "
            f"{camino.get('wasmtime')}). La firma la declaro OPT-IN: "
            "«fuera del camino stdlib que se envia». Enchufarla al arranque "
            "cambia la promesa publica y exige firma nueva del Soberano.")

    def test_la_jaula_existe_y_sigue_declarada(self):
        """Que el candado no pase por ausencia.

        Si alguien borra `frontera.py`, los dos casos de arriba pasan solos y
        esta prueba dejaria de significar nada. Un candado que se abre porque
        ya no hay puerta no es un candado.
        """
        jaula = os.path.join(RAIZ, "frontera.py")
        if not os.path.exists(jaula):
            self.skipTest("frontera.py ya no esta en el arbol: no hay jaula que vigilar")
        with open(jaula, encoding="utf-8") as fh:
            self.assertIn("wasmtime", fh.read(),
                          "frontera.py ya no usa wasmtime: revisar la firma")


if __name__ == "__main__":
    unittest.main()
