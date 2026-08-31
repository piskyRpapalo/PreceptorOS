#!/usr/bin/env python3
"""Las once metricas de METRICAS_NORMA, medidas o declaradas. **Solo stdlib.**

LO QUE ESTE MODULO HACE DE VERDAD ES NEGARSE
--------------------------------------------
Un panel de metricas es el sitio donde un cero decorativo se cuela mas facil:
quien lo mira espera numeros, asi que un `0` en VRAM pasa por dato sin que
nadie lo mire dos veces. Aqui no hay ceros de relleno. Cada campo sale MEDIDO
con su fuente, NORMA si es una condicion declarada, o NO_DATA con su causa.

TRES ESTADOS, Y EL DEL MEDIO ES EL QUE FALTABA
----------------------------------------------
* **MEDIDO** — se leyo de algun sitio, y ese sitio se nombra en `como`.
* **NORMA**  — no se mide: se DECIDE antes de correr. Son `ventana_contexto` y
  `tokens_sesion`, las dos condiciones sin las cuales dos paquetes no son
  comparables aunque ambos midan bien.
* **NO_DATA** — no se pudo, o no existe la magnitud. Siempre con causa.

EL SENSOR DE TEMPERATURA SE BUSCA POR NOMBRE
--------------------------------------------
En este nodo el sensor honesto es `k10temp`. El que NO sirve es `acpitz`, que
marca 20 grados constantes: un sensor de portabilidad que en este hardware
esta muerto y lo parece vivo, asi que la zona termica generica queda
descartada por doctrina.

Y el hwmon se busca por su fichero `name`, jamas por su numero. La numeracion
depende del orden en que se registran los drivers y no es estable entre
arranques: leer un indice a ciegas da una cifra, y es de otro sensor.
"""
from __future__ import annotations

import glob
import os
import subprocess

CAMPOS = {
    "modelo_nombre", "modelo_base", "modelo_tamano_gb", "consumo_ram_mb",
    "tokens_sesion", "ventana_contexto", "tokens_por_segundo",
    "latencia_primer_token_ms", "temp_cpu_c", "vram_mb", "duracion_ms",
}

# La ventana medida en este nodo el 2026-08-25: `-c 32768` con `-ngl 99` carga
# y responde. Por encima no hay medida, asi que no hay norma.
VENTANA_MEDIDA = 32768


def medido(clave, valor, unidad, como):
    return {"clave": clave, "estado": "MEDIDO", "valor": valor,
            "unidad": unidad, "como": como}


def norma(clave, valor, unidad, como):
    return {"clave": clave, "estado": "NORMA", "valor": valor,
            "unidad": unidad, "como": como}


def sin_dato(clave, causa, unidad, detalle=""):
    d = {"clave": clave, "estado": "NO_DATA", "valor": None,
         "unidad": unidad, "causa": causa}
    if detalle:
        d["detalle"] = detalle
    return d


def campo(paquete, clave):
    """El campo por su nombre, o KeyError. Que falte es un defecto, no un caso."""
    for m in paquete["metricas"]:
        if m["clave"] == clave:
            return m
    raise KeyError(clave)


def _hwmon_por_nombre(nombre="k10temp"):
    """La carpeta hwmon cuyo `name` coincide. None si no esta."""
    for n in sorted(glob.glob("/sys/class/hwmon/hwmon*/name")):
        try:
            if open(n, encoding="utf-8").read().strip() == nombre:
                return os.path.dirname(n)
        except OSError:
            continue
    return None


def _temperatura():
    h = _hwmon_por_nombre()
    if not h:
        return sin_dato("temp_cpu_c",
                        "no hay ningun hwmon que se llame k10temp en esta "
                        "maquina; la zona termica generica no se usa porque "
                        "en este nodo es acpitz y marca un valor fijo",
                        "grados C")
    try:
        crudo = int(open(os.path.join(h, "temp1_input"), encoding="utf-8").read())
    except (OSError, ValueError) as e:
        return sin_dato("temp_cpu_c", f"k10temp presente pero ilegible: {e}",
                        "grados C")
    return medido("temp_cpu_c", round(crudo / 1000.0, 1), "grados C",
                  "temp1_input del hwmon cuyo name es k10temp, en milesimas")


def _modelos_cargados():
    """Que modelos hay CARGADOS ahora mismo, segun quien lo sabe.

    Se le pregunta a `ollama ps` en vez de adivinarlo por el nombre de los
    procesos. La primera version de esto buscaba «llama» en el nombre y
    casaba con el propio demonio `ollama` en reposo: publicaba sus 39 MB como
    si fueran los 2,5 GB del modelo. Una cifra plausible del orden de
    magnitud equivocado es peor que un hueco declarado, porque nadie la mira
    dos veces.
    """
    try:
        r = subprocess.run(["ollama", "ps"], capture_output=True, text=True,
                           timeout=10)
    except (OSError, subprocess.SubprocessError):
        return []
    if r.returncode != 0:
        return []
    filas = [l for l in r.stdout.splitlines()[1:] if l.strip()]
    return [l.split()[0] for l in filas]


def _rss_del_runner():
    """RSS del proceso que sirve el modelo, y solo si hay uno cargado.

    Un modelo en disco no consume nada: lo que se quiere saber es lo que
    ocupa cuando esta servido. Sin modelo cargado no hay cifra, y el tamano
    del fichero NO la sustituye.
    """
    cargados = _modelos_cargados()
    if not cargados:
        return sin_dato("consumo_ram_mb",
                        "no hay ningun modelo cargado ahora mismo (ollama ps "
                        "vacio). El tamano del fichero en disco NO es esta "
                        "cifra y no se sustituye por el", "MiB")
    try:
        salida = subprocess.run(["ps", "-eo", "pid,rss,comm"],
                                capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError) as e:
        return sin_dato("consumo_ram_mb", f"no se pudo listar procesos: {e}", "MiB")
    mejor = None
    for linea in salida.splitlines()[1:]:
        partes = linea.split(None, 2)
        if len(partes) < 3:
            continue
        pid, rss, comm = partes
        try:
            rss = int(rss)
        except ValueError:
            continue
        # El runner es el proceso GRANDE. Se elige por tamano y no por nombre:
        # los nombres cambian entre versiones de ollama, el orden de magnitud
        # no. Y se exige un minimo, para que el demonio en reposo nunca gane.
        if rss > 512 * 1024 and (mejor is None or rss > mejor[1]):
            mejor = (pid, rss, comm)
    if not mejor:
        return sin_dato("consumo_ram_mb",
                        f"ollama declara {len(cargados)} modelo(s) cargado(s) "
                        "pero no se encontro ningun proceso por encima de 512 "
                        "MiB que pueda ser su runner", "MiB")
    pid, rss, comm = mejor
    return medido("consumo_ram_mb", round(rss / 1024), "MiB",
                  f"RSS de {comm} (pid {pid}), el mayor proceso residente con "
                  f"{cargados[0]} cargado")


def _modelo(cerebro):
    """Los tres campos del modelo. `cerebro` es lo que sirve /api/estado."""
    c = cerebro or {}
    nombre, bytes_ = c.get("nombre"), c.get("bytes")
    out = []
    out.append(medido("modelo_nombre", nombre, "texto",
                      "el cerebro declarado por /api/estado")
               if nombre else
               sin_dato("modelo_nombre", "no hay cerebro declarado", "texto"))
    out.append(medido("modelo_tamano_gb", round(bytes_ / 1e9, 2), "GB",
                      "tamano del fichero del modelo declarado")
               if bytes_ else
               sin_dato("modelo_tamano_gb", "el cerebro no declara tamano", "GB"))
    # modelo_base es OBLIGATORIO en la norma: sin el, comparar un adaptador con
    # otro entrenado sobre otra base es comparar dos cosas y llamarlas la misma.
    base = c.get("base")
    out.append(medido("modelo_base", base, "texto",
                      "FROM del Modelfile del adaptador")
               if base else
               sin_dato("modelo_base",
                        "el cerebro no declara de que base sale. Mientras falte, "
                        "este paquete NO es comparable con otro: es el campo que "
                        "hace comparables dos medidas", "texto"))
    return out


def _del_turno(turno):
    """Lo que el ultimo turno dejo medido. Sin turno, tres NO_DATA."""
    t = turno or {}
    out = []
    ms, tok, ttft = t.get("ms"), t.get("tokens"), t.get("ttft")
    out.append(medido("duracion_ms", round(ms), "ms", "reloj del turno")
               if ms else sin_dato("duracion_ms", "todavia no hubo turno", "ms"))
    # tok/s solo si el motor DECLARO tokens. Contar trozos y llamarlos tokens
    # seria decorar una cifra.
    out.append(medido("tokens_por_segundo", round(tok / (ms / 1000.0), 2),
                      "tokens/s", "tokens declarados por el motor / duracion")
               if tok and ms else
               sin_dato("tokens_por_segundo",
                        "el motor no declaro tokens en el ultimo turno; contar "
                        "trozos y llamarlos tokens seria inventar la cifra",
                        "tokens/s"))
    out.append(medido("latencia_primer_token_ms", round(ttft), "ms",
                      "reloj hasta el primer trozo")
               if ttft is not None else
               sin_dato("latencia_primer_token_ms",
                        "no llego ningun trozo, asi que no hay primer token que "
                        "cronometrar. No es cero: es que no lo hubo", "ms"))
    return out


def paquete(cerebro=None, turno=None, tokens_sesion=0, ventana=VENTANA_MEDIDA):
    """El paquete entero, listo para pintar o para firmar."""
    m = []
    m += _modelo(cerebro)
    m.append(_rss_del_runner())
    m += [
        norma("tokens_sesion", tokens_sesion, "tokens",
              "contador acumulado de la sesion; se declara, no se descubre"),
        norma("ventana_contexto", ventana, "tokens",
              f"num_ctx pasado al runtime. {VENTANA_MEDIDA} es lo medido en este "
              "nodo; por encima no hay medida y por tanto no hay norma"),
    ]
    m += _del_turno(turno)
    m.append(_temperatura())
    # El unico campo que NUNCA sale con cifra en este hardware, y por eso el
    # hueco existe: para que el dia que haya una GPU con memoria propia nadie
    # tenga que inventarle nombre ni unidad.
    m.append(sin_dato(
        "vram_mb",
        "esta maquina no tiene VRAM que medir",
        "MiB",
        "la Radeon 780M es una iGPU: comparte la DDR5 con la CPU y no tiene "
        "memoria propia. Lo que en otra maquina seria VRAM aqui ya esta "
        "contado en consumo_ram_mb. Un 0 aqui no seria un dato bajo, seria "
        "una magnitud que no existe"))
    return {
        "esquema": 1,
        "norma": {"tokens_sesion": tokens_sesion, "ventana_contexto": ventana,
                  "nota": "solo son comparables entre si los paquetes que "
                          "declaran los mismos dos valores"},
        "metricas": m,
    }
