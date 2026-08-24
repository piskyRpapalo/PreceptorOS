#!/usr/bin/env python3
"""aurelius.py · el nombre viejo del punto de entrada. Sigue funcionando.

Mandato 1 renombró el producto: el punto de entrada es `preceptoros.py`. Este
fichero se queda porque `python3 aurelius.py` está escrito en sitios que este
repositorio no controla — el acceso directo de Android, un alias en el
`.bashrc`, el guion que alguien copió a su teléfono, la nota de un cuaderno.
Borrarlo de golpe no rompería el producto: rompería el arranque de otros, y el
síntoma sería «no existe el fichero», que no dice a dónde ir.

DOS CAMINOS, Y HACEN FALTA LOS DOS
----------------------------------
`python3 aurelius.py` ejecuta. `import aurelius` **NO ejecuta**: reexporta el
módulo nuevo, como haría cualquier alias.

La primera versión de este puente no distinguía los dos casos: corría el
producto también al importarlo. Lo cazó `test_idioma`, que hace justo eso —
`import aurelius as A` — y en vez de correr sus casos se quedó en una sesión
interactiva esperando a que alguien contestara si entraba en la Fuga del Museo.
Un alias que arranca un programa al mirarlo no es un alias: es una trampa.

Muere el mismo día que el puente de las variables de entorno: ver
`entorno.SOPORTE_NOMBRE_VIEJO_HASTA`.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import entorno as _entorno  # noqa: E402

_AVISO = (f"Aviso · `aurelius.py` pasó a llamarse `preceptoros.py`. El nombre "
          f"viejo funciona hasta el {_entorno.SOPORTE_NOMBRE_VIEJO_HASTA}; "
          f"después, no.")

if __name__ == "__main__":
    import runpy
    print(_AVISO, file=sys.stderr)
    # `run_path` con `__main__` y no un `import`: el nuevo decide qué hacer en
    # su propio bloque `if __name__ == "__main__"`, y los argumentos de la
    # línea de órdenes llegan intactos porque `sys.argv` no se toca.
    runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "preceptoros.py"), run_name="__main__")
else:
    # Importado: alias puro. Se reexporta el módulo nuevo entero, sin ejecutar
    # nada y sin copiar nombres a mano -- una lista de nombres se queda vieja en
    # cuanto el nuevo gane una función.
    from preceptoros import *              # noqa: F401,F403,E402
    import preceptoros as _nuevo           # noqa: E402
    for _n in dir(_nuevo):
        if _n not in globals():
            globals()[_n] = getattr(_nuevo, _n)
