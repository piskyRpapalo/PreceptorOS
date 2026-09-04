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
import json
import os
import subprocess
import urllib.error
import urllib.request

CAMPOS = {
    "modelo_nombre", "modelo_base", "modelo_tamano_gb", "consumo_ram_mb",
    "tokens_sesion", "ventana_contexto", "tokens_por_segundo",
    "latencia_primer_token_ms", "temp_cpu_c", "vram_mb", "duracion_ms",
}

# La ventana medida en este nodo el 2026-08-25: `-c 32768` con `-ngl 99` carga
# y responde. Por encima no hay medida, asi que no hay norma.
VENTANA_MEDIDA = 32768

# El enchufe medidor del rack (Nous A1T con Tasmota). Se deja en una constante
# y no incrustado en la funcion porque es una direccion de LAN: el dia que
# cambie de IP se cambia aqui, y quien corra esto en otra red la sobreescribe
# sin editar el codigo.
ENCHUFE = os.environ.get("P0X_ENCHUFE", "http://192.168.50.162")
# Solo la parte que un humano reconoce, para la frase del hueco: «no responde
# en http://192.168.50.162» se lee peor que «no responde en 192.168.50.162».
ENCHUFE_IP = ENCHUFE.split("//")[-1].rstrip("/")


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


def _consumo_w():
    """Los vatios que el rack esta chupando AHORA, leidos del enchufe.

    ES LA UNICA METRICA DE ESTE MODULO QUE SALE DE LA MAQUINA
    ---------------------------------------------------------
    Las otras once se leen de /sys, de /proc o de un subproceso local. Esta
    cruza la LAN hasta el Nous A1T, y por eso lleva `timeout=2`: un panel que
    se cuelga esperando a un enchufe es peor panel que uno que declara
    NO_DATA en dos segundos. La causa viaja en el hueco -- si el enchufe se
    apaga, quien mire tiene que poder distinguirlo de un consumo de cero.

    Y no entra en `paquete()`: METRICAS_NORMA compara PAQUETES DE MODELO entre
    maquinas, y el vatiaje de un enchufe describe el rack, no el modelo. Ver
    la nota de `paquete()`.
    """
    url = f"{ENCHUFE}/cm?cmnd=Status+8"
    try:
        with urllib.request.urlopen(url, timeout=2) as r:
            datos = json.loads(r.read().decode("utf-8"))
        w = datos["StatusSNS"]["ENERGY"]["Power"]
    except (urllib.error.URLError, OSError, ValueError) as e:
        # La causa es la frase fija que el Soberano quiere leer en el panel; el
        # TIPO de averia va en `detalle`, porque «tardo mas de 2 s» y «me
        # cerraron el puerto» se arreglan de forma distinta y perderlo seria
        # cambiar un hueco con causa por un hueco con excusa.
        return sin_dato("consumo_w", f"Nous A1T no responde en {ENCHUFE_IP}",
                        "W", f"{type(e).__name__} pidiendo {url}")
    except (KeyError, TypeError) as e:
        # Contesto, pero no con lo que se le pidio. Es una averia distinta
        # --firmware cambiado, otro aparato en esa IP-- y se dice distinta.
        return sin_dato("consumo_w",
                        f"Nous A1T responde en {ENCHUFE_IP} pero sin "
                        "StatusSNS.ENERGY.Power", "W", f"{type(e).__name__}: {e}")
    return medido("consumo_w", w, "W", "Nous A1T por HTTP local")


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


# Nombres de los procesos que sirven un modelo en este arbol. `ps -eo comm`
# corta a quince caracteres, asi que se comparan por PREFIJO y las entradas se
# escriben ya cortadas cuando el nombre real es mas largo.
SERVIDORES = ("llama-server", "llama-cli", "llama-completio",
              "ollama_llama_s", "ollama")

# Un servidor con el modelo dentro pesa gigas. El suelo existe por la cicatriz
# de agosto: la primera version casaba «llama» por nombre y publicaba los 39 MB
# del demonio `ollama` en reposo como si fueran los 2,5 GB del modelo.
SUELO_RUNNER = 512 * 1024          # KiB, que es lo que da `ps -eo rss`


def _procesos():
    """(pid, rss_kib, comm) de todo lo que corre. Lista vacia si no se puede."""
    try:
        salida = subprocess.run(["ps", "-eo", "pid,rss,comm"],
                                capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    fuera = []
    for linea in salida.splitlines()[1:]:
        partes = linea.split(None, 2)
        if len(partes) < 3:
            continue
        try:
            fuera.append((partes[0], int(partes[1]), partes[2].strip()))
        except ValueError:
            continue
    return fuera


def _servidor_vivo(procesos):
    """El proceso servidor mas grande, elegido POR NOMBRE y con suelo."""
    hallados = [p for p in procesos
                if p[1] > SUELO_RUNNER and p[2].startswith(SERVIDORES)]
    return max(hallados, key=lambda p: p[1]) if hallados else None


def _rss_del_runner():
    """RSS del proceso que sirve el modelo, y solo si hay uno cargado.

    Un modelo en disco no consume nada: lo que se quiere saber es lo que
    ocupa cuando esta servido. Sin modelo cargado no hay cifra, y el tamano
    del fichero NO la sustituye.

    DOS AUTORIDADES, Y HACEN FALTA LAS DOS. Medido el 2026-09-04 entrando en
    el producto como usuario: este panel declaraba «no hay ningun modelo
    cargado (ollama ps vacio)» mientras un `llama-server` con 7,6 GB
    residentes llevaba casi ocho horas contestando. No era un hueco honesto:
    era una ausencia inventada, que es peor que una cifra mal puesta porque
    parece rigor. El MVP no sirve por Ollama -- sirve por `llama-server`
    directo-- y a la unica autoridad que se preguntaba no le constaba.

    Y AL ARREGLARLO SE VIO OTRO. Con Ollama cargado, la version anterior
    elegia «el mayor proceso residente» de TODA la maquina. En un escritorio
    eso es el navegador: aqui Chrome pesa 1,7 GB y la impresora 1,68. Bastaba
    un runner mas pequeno que el navegador para publicar la memoria de Chrome
    como si fuera la del modelo -- otra cifra plausible del orden de magnitud
    equivocado, que es exactamente lo que la cicatriz de agosto vino a matar.
    Ahora el servidor se elige POR NOMBRE, con el mismo suelo de 512 MiB que
    protege del demonio en reposo. El tamano solo desempata entre servidores.
    """
    procesos = _procesos()
    if not procesos:
        return sin_dato("consumo_ram_mb", "no se pudo listar los procesos", "MiB")
    cargados = _modelos_cargados()
    servidor = _servidor_vivo(procesos)

    if servidor is None:
        if cargados:
            return sin_dato("consumo_ram_mb",
                            f"ollama declara {len(cargados)} modelo(s) cargado(s) "
                            "pero no hay ningun proceso servidor por encima de "
                            "512 MiB que pueda estar sirviendolos", "MiB")
        return sin_dato("consumo_ram_mb",
                        "no hay ningun modelo cargado ahora mismo: ni ollama "
                        "declara ninguno ni corre un servidor con el modelo "
                        "dentro. El tamano del fichero en disco NO es esta "
                        "cifra y no se sustituye por el", "MiB")

    pid, rss, comm = servidor
    quien = cargados[0] if cargados else "un modelo que ollama no declara"
    return medido("consumo_ram_mb", round(rss / 1024), "MiB",
                  f"RSS de {comm} (pid {pid}), el mayor proceso servidor "
                  f"residente · sirviendo {quien}")


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
    """El paquete entero, listo para pintar o para firmar.

    `consumo_w` NO esta aqui a proposito. Este paquete es la unidad de
    comparacion entre maquinas: once campos, los mismos siempre. El vatiaje
    del enchufe mide el RACK, no el modelo, y meterlo dentro romperia la
    comparabilidad con cualquier paquete que venga de una maquina sin enchufe.
    Se pide aparte, con `_consumo_w()`, y lo consume el Ojo.
    """
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
