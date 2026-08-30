#!/usr/bin/env python3
"""frontera.py — la frontera Wasmtime del Preceptor (misión LAS TRES JOYAS).

DOCTRINA: El silicio propone DENTRO de esta celda; el carbono firma FUERA.
Este sandbox no relaja IronClaw — es su brazo de contención en G3. Nada
ejecutado aquí toca el rack sin firma del carbono.

La celda de cuarentena queda instanciada y lista (``CELDA``), pero este
módulo NO ejecuta nada por sí mismo: solo cuando una misión con mandato
llame a ``proponer()`` correrá código WASM — y siempre dentro de la jaula:

- **Memoria acotada** (64 MiB por defecto) vía ``Store.set_limits``.
- **CPU acotada** por combustible determinista (``consume_fuel``): un bucle
  infinito muere por trampa de fuel, no cuelga el nodo.
- **Sin FS ni red**: cero WASI enlazado. Un módulo que importe cualquier
  cosa del anfitrión no llega ni a instanciarse.
- **Una Store fresca por propuesta**: ningún estado sobrevive entre
  propuestas — la celda se demuele y se reconstruye cada vez.

Requiere ``wasmtime`` (ver ``requirements.txt``; en soberano vive en el
venv de usuario ``~/.venvs/p0x``, sin sudo).
"""

from __future__ import annotations

from dataclasses import dataclass

import wasmtime

MEMORIA_MAX_BYTES: int = 64 * 2**20   # 64 MiB: propuesta, no proceso
COMBUSTIBLE_POR_PROPUESTA: int = 100_000_000  # ~instrucciones; determinista


@dataclass(frozen=True)
class ResultadoAislado:
    """Lo único que sale de la celda: dato inerte, jamás efectos.

    Attributes:
        exito: la propuesta corrió y terminó dentro de los límites.
        valor: retorno numérico de la función exportada, si lo hubo.
        error: trampa/violación declarada tal cual, o ``None``.
        combustible_consumido: instrucciones de fuel gastadas, si medibles.
    """

    exito: bool
    valor: int | float | None
    error: str | None
    combustible_consumido: int | None


class FronteraWasmtime:
    """La jaula: un ``Engine`` vacío y celdas ``Store`` de un solo uso.

    El engine se configura una vez (fuel activo); cada llamada a
    ``proponer`` construye su propia ``Store`` con límites de memoria y
    combustible, instancia el módulo SIN imports del anfitrión y llama a la
    función exportada. Nada de lo que pase dentro toca el rack.
    """

    def __init__(self,
                 memoria_max_bytes: int = MEMORIA_MAX_BYTES,
                 combustible: int = COMBUSTIBLE_POR_PROPUESTA) -> None:
        """Instancia el engine de la jaula (vacío, listo para G3).

        Args:
            memoria_max_bytes: techo duro de memoria lineal por propuesta.
            combustible: presupuesto determinista de ejecución por propuesta.
        """
        config = wasmtime.Config()
        config.consume_fuel = True
        self.engine: wasmtime.Engine = wasmtime.Engine(config)
        self.memoria_max_bytes: int = memoria_max_bytes
        self.combustible: int = combustible
        # La celda en espera: demuestra que la jaula está viva sin ejecutar
        # nada. Cada propuesta real usará una Store fresca, no esta.
        self.celda_en_espera: wasmtime.Store = self._celda_nueva()

    def _celda_nueva(self) -> wasmtime.Store:
        """Construye una ``Store`` con los límites de la jaula ya puestos."""
        celda = wasmtime.Store(self.engine)
        celda.set_limits(memory_size=self.memoria_max_bytes)
        celda.set_fuel(self.combustible)
        return celda

    def proponer(self, codigo_wasm: bytes,
                 funcion: str = "proponer") -> ResultadoAislado:
        """Corre una propuesta WASM DENTRO de la jaula y rinde dato inerte.

        Args:
            codigo_wasm: binario ``.wasm`` (o texto ``.wat`` en bytes — se
                traduce con ``wat2wasm`` si no empieza por la magia WASM).
            funcion: nombre del export a invocar (sin argumentos).

        Returns:
            ``ResultadoAislado``. Toda violación de la jaula (import del
            anfitrión, memoria, fuel agotado, trampa) es ``exito=False``
            con el error declarado tal cual — jamás una excepción que
            escape de la frontera.
        """
        celda = self._celda_nueva()
        try:
            if not codigo_wasm.startswith(b"\0asm"):
                codigo_wasm = wasmtime.wat2wasm(codigo_wasm)
            modulo = wasmtime.Module(self.engine, codigo_wasm)
            if modulo.imports:
                pedidos = ", ".join(
                    f"{i.module}.{i.name}" for i in modulo.imports)
                return ResultadoAislado(
                    exito=False, valor=None,
                    error=f"veto de frontera: el modulo exige imports del "
                          f"anfitrion ({pedidos}) — sin WASI, sin FS, sin red",
                    combustible_consumido=None)
            instancia = wasmtime.Instance(celda, modulo, [])
            export = instancia.exports(celda).get(funcion)
            if not isinstance(export, wasmtime.Func):
                return ResultadoAislado(
                    exito=False, valor=None,
                    error=f"sin dato: el modulo no exporta la funcion "
                          f"'{funcion}'",
                    combustible_consumido=self._gastado(celda))
            crudo = export(celda)
            valor = crudo if isinstance(crudo, (int, float)) else None
            return ResultadoAislado(exito=True, valor=valor, error=None,
                                    combustible_consumido=self._gastado(celda))
        except (wasmtime.Trap, wasmtime.WasmtimeError) as trampa:
            # Trap NO hereda de WasmtimeError en wasmtime-py 46 (verificado
            # aquí: el fuel agotado escapaba de la jaula) — se cazan ambas.
            return ResultadoAislado(exito=False, valor=None,
                                    error=str(trampa),
                                    combustible_consumido=self._gastado(celda))

    def _gastado(self, celda: wasmtime.Store) -> int | None:
        """Combustible consumido por la celda, o ``None`` si no es medible."""
        try:
            return self.combustible - celda.get_fuel()
        except wasmtime.WasmtimeError:
            return None


# La celda de cuarentena, instanciada y lista. Importar este módulo no
# ejecuta ninguna propuesta: solo levanta la jaula.
CELDA: FronteraWasmtime = FronteraWasmtime()
