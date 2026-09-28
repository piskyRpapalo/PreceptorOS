#!/usr/bin/env python3
"""El runner de theGame: tu IA local juega, sin conversar, y se mide contra la regla fija.

sistema: MVP · solo biblioteca estandar (mas `node` para el motor, que es el de la web).

    python3 atlas_runner.py --modelo RUTA.gguf [--decisiones 20] [--cada 25] [--guardar]
    python3 atlas_runner.py --motor regla        # la tuberia entera, sin cargar ningun modelo

QUE HACE. Abre el motor puro de theGame por una TUBERIA (`atlas/corre.mjs`, D68: ni un socket) y
juega `decisiones` veces, cada `cada` ciclos. En cada decision le da al modelo local la
instantanea (`atlas.instantanea/1`) y la lista de acciones LEGALES en ese momento, y le pide UNA
sola `atlas.accion/1` en JSON. Nada de charla: lo que no es una accion legal cuenta como fallo y se
juega `esperar`. Al final, la misma ley y el mismo calendario los juega la regla fija, y el
criterio del juez de la web (nucleo > fase > integridad minima > xp) dice si el modelo mejora,
empeora o empata. El resultado es `atlas.corrida/1`: medido, con sus latencias, sus fallos y cada
lectura termica, o NO_DATA con su causa.

LO QUE NO HACE. No entrena, no sustituye a la regla (`reemplaza` es siempre False: eso exige
ganar en el arnes y la firma del Soberano), no invoca ni gasta (el enum no incluye `invocar`), no
sale a la red y no escribe en `memory.db`: la memoria guarda las palabras de la persona, y una
corrida es una medida de la maquina. Va a su carpeta, `<casa>/atlas/corridas/`.

EL ESCUDO TERMICO. Antes de cada decision se lee la temperatura: la CPU por el sensor honesto
(`k10temp`, el mismo que `metricas.py`) o la bateria de un telefono (`power_supply/battery/temp`).
Por encima del techo se espera a que baje, y si no baja en el tiempo maximo la corrida se PARA y lo
dice. Sin sensor, NO_DATA, y se descansa tanto como tardo la ultima decision: un telefono sin
termometro no se castiga a ciegas. Los techos son NORMA provisional (85 C CPU, 40 C bateria),
pendientes de firma, y se pueden cambiar por entorno.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CORRE = AQUI / "atlas" / "corre.mjs"
LEY = {"nd": False, "integridad_max": 117, "dano": 1}
TECHO_CPU = float(os.environ.get("PRECEPTOROS_TECHO_CPU_C", "85"))
TECHO_BATERIA = float(os.environ.get("PRECEPTOROS_TECHO_BATERIA_C", "40"))
ESPERA_MAX_S = float(os.environ.get("PRECEPTOROS_ESPERA_TERMICA_S", "600"))
BATERIA = Path("/sys/class/power_supply/battery/temp")


# --- el motor por tuberia --------------------------------------------------------------------
class SinMotor(RuntimeError):
    """No hay node, no hay motor o no casa su huella. Lleva la causa."""


class Motor:
    def __init__(self, node="node", corre=CORRE):
        try:
            self.p = subprocess.Popen([node, str(corre)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=subprocess.DEVNULL, text=True, bufsize=1)
        except OSError as e:
            raise SinMotor(f"NO_DATA · no se puede lanzar node: {e}") from e
        hola = self._lee()
        if not hola.get("ok"):
            self.cierra()
            raise SinMotor(f"{hola.get('estado', 'NO_DATA')} · {hola.get('motivo')}")
        self.contenido_v, self.web_commit = hola.get("contenido_v"), hola.get("web_commit")

    def _lee(self):
        linea = self.p.stdout.readline()
        if not linea:
            raise SinMotor("NO_DATA · el motor se cerro sin contestar")
        return json.loads(linea)

    def orden(self, **o):
        self.p.stdin.write(json.dumps(o) + "\n")
        self.p.stdin.flush()
        return self._lee()

    def cierra(self):
        try:
            self.p.stdin.close()
            self.p.wait(timeout=5)
        except Exception:
            self.p.kill()
        finally:
            self.p.stdout.close()


# --- el escudo termico ------------------------------------------------------------------------
def leer_temperatura():
    """(fuente, grados) o (None, causa). Nunca un cero de relleno."""
    try:
        import metricas
        t = metricas._temperatura()
        if t.get("estado") == "MEDIDO":
            return "cpu", float(t["valor"])
    except Exception:
        pass
    try:
        return "bateria", int(BATERIA.read_text().strip()) / 10.0
    except (OSError, ValueError):
        return None, "ni k10temp ni power_supply/battery/temp en este aparato"


class Escudo:
    def __init__(self, sensor=leer_temperatura, dormir=time.sleep, reloj=time.monotonic):
        self.sensor, self.dormir, self.reloj = sensor, dormir, reloj
        self.lecturas, self.parado = [], None

    def antes(self, ultima_s):
        """True si se puede decidir; False si la corrida debe pararse por calor."""
        fuente, v = self.sensor()
        if fuente is None:
            self.lecturas.append({"estado": "NO_DATA", "causa": v, "descanso_s": round(ultima_s, 2)})
            if ultima_s > 0:
                self.dormir(ultima_s)
            return True
        techo = TECHO_CPU if fuente == "cpu" else TECHO_BATERIA
        t0 = self.reloj()
        while v >= techo:
            self.lecturas.append({"estado": "MEDIDO", "fuente": fuente, "c": v, "techo": techo, "espera": True})
            if self.reloj() - t0 >= ESPERA_MAX_S:
                self.parado = f"{fuente} a {v} C sobre el techo de {techo} C durante {int(ESPERA_MAX_S)} s"
                return False
            self.dormir(30)
            fuente, v = self.sensor()
            if fuente is None:
                break
        self.lecturas.append({"estado": "MEDIDO" if fuente else "NO_DATA", "fuente": fuente, "c": v if fuente else None,
                              "techo": techo})
        return True


# --- el modelo, sin conversar -----------------------------------------------------------------
def pregunta(ins, legales):
    """Lo que ve el modelo: la instantanea y las acciones legales. Nada mas."""
    return ("You play theGame. Reply with ONLY one JSON object, copied exactly from the LEGAL list. "
            "No other text.\nSTATE: " + json.dumps(ins, separators=(",", ":"), sort_keys=True) +
            "\nLEGAL: " + json.dumps(legales, separators=(",", ":")) + "\nANSWER:")


def extrae(texto, legales):
    """(accion, None) si el texto trae una accion LEGAL ahora; (None, causa) si no."""
    if not texto:
        return None, "el modelo no contesto"
    dec = json.JSONDecoder()
    for m in re.finditer(r"\{", texto):
        try:
            o, _ = dec.raw_decode(texto[m.start():])
        except ValueError:
            continue
        if not isinstance(o, dict):
            continue
        a = {"accion": o.get("accion")}
        if o.get("banda") is not None:
            a["banda"] = o.get("banda")
        if a in legales:
            return a, None
        return None, f"no es legal ahora: {json.dumps(a)[:80]}"
    return None, "sin JSON en la respuesta"


def correr(pensar, decisiones=20, cada=25, ley=LEY, escudo=None, nombre="NO_DATA", modelo_sha256=None,
           reloj=time.monotonic, corre=CORRE):
    """Juega y mide. `pensar(prompt) -> texto | None`. Devuelve `atlas.corrida/1`."""
    escudo = escudo or Escudo()
    try:
        mo = Motor(corre=corre)
    except SinMotor as e:
        if callable(getattr(pensar, "cierra", None)):
            pensar.cierra()
        return {"esquema": "atlas.corrida/1", "estado": "NO_DATA", "causa": str(e)}
    pasos, ultima = [], 0.0
    try:
        mo.orden(op="inicial", ley=ley)
        for n in range(decisiones):
            if not escudo.antes(ultima):
                break
            ins = mo.orden(op="ciclos", n=0)["ins"]
            leg = mo.orden(op="legales")["legales"]
            t0 = reloj()
            try:
                texto = pensar(pregunta(ins, leg))
            except Exception as e:           # un modelo que revienta es un fallo medido, no un cuelgue
                texto = None
                causa_motor = f"{type(e).__name__}"
            else:
                causa_motor = None
            ultima = reloj() - t0
            accion, causa = extrae(texto, leg)
            r = mo.orden(op="aplica", accion=accion or {"accion": "esperar"})
            pasos.append({"n": n, "ciclo": ins["ciclo"], "propuesta": accion, "valida": accion is not None,
                          "causa": causa_motor or causa, "cambio": r.get("cambio"), "ms": round(ultima * 1000)})
            mo.orden(op="ciclos", n=cada)
        final = mo.orden(op="final")["final"]
        base = mo.orden(op="base", ley=ley, cada=cada, decisiones=len(pasos))["base"]
        g = mo.orden(op="gana", p=base, h=final)["gana"]
        contenido_v, web = mo.contenido_v, mo.web_commit
    finally:
        mo.cierra()
        # Si quien piensa tiene su propio proceso (la regla fija como motor), tambien se cierra aqui.
        if callable(getattr(pensar, "cierra", None)):
            pensar.cierra()
    ms = [p["ms"] for p in pasos]
    validas = sum(p["valida"] for p in pasos)
    return {
        "esquema": "atlas.corrida/1", "estado": "PARADO_POR_CALOR" if escudo.parado else "OK",
        "parado": escudo.parado, "contenido_v": contenido_v, "web_commit": web,
        "motor": {"nombre": nombre, "sha256": modelo_sha256 or None,
                  "causa_sha256": None if modelo_sha256 else "no calculado en esta corrida"},
        "ley": ley, "plan": {"decisiones": decisiones, "cada": cada, "jugadas": len(pasos)},
        "medidas": {"validas": validas, "invalidas": len(pasos) - validas,
                    "ms_media": round(sum(ms) / len(ms)) if ms else None, "ms_max": max(ms) if ms else None},
        "final": final, "base": base,
        "veredicto": {"humano": "mejora", "piloto": "empeora"}.get(g, "empate"),
        "reemplaza": False,
        "causa_reemplazo": "sustituir la regla fija exige ganar en el arnes del piloto y la firma del Soberano",
        "termico": escudo.lecturas, "pasos": pasos,
    }


def guardar(res):
    """En la casa de la persona, 0600, con nombre por su contenido. Nunca junto al programa."""
    import casa
    carpeta = Path(casa.asegurar()) / "atlas" / "corridas"
    carpeta.mkdir(parents=True, exist_ok=True)
    os.chmod(carpeta, 0o700)
    cuerpo = json.dumps(res, sort_keys=True, ensure_ascii=False, indent=1) + "\n"
    ruta = carpeta / (hashlib.sha256(cuerpo.encode("utf-8")).hexdigest()[:16] + ".json")
    ruta.write_text(cuerpo, encoding="utf-8")
    os.chmod(ruta, 0o600)
    return ruta


def main(argv=None):
    ap = argparse.ArgumentParser(description="theGame runner: your local model plays, measured against the fixed rule")
    ap.add_argument("--modelo", help="path to a .gguf (uses the same llama binary as the conversation)")
    ap.add_argument("--motor", choices=["regla"], help="'regla': the fixed rule, to test the pipeline without a model")
    ap.add_argument("--decisiones", type=int, default=20)
    ap.add_argument("--cada", type=int, default=25)
    ap.add_argument("--guardar", action="store_true", help="write the run under <home>/atlas/corridas/ (0600)")
    a = ap.parse_args(argv)
    if a.motor == "regla":
        pensar = _pensar_regla(a.cada)
        nombre = "regla-fija (no es un modelo)"
    elif a.modelo:
        import conversacion
        pensar = conversacion.motor_llama(a.modelo)
        if pensar is None:
            print(json.dumps({"estado": "NO_DATA", "causa": "no hay binario llama o no existe el modelo"}))
            return 0
        nombre = os.path.basename(a.modelo)
    else:
        print(json.dumps({"estado": "NO_DATA", "causa": "sin --modelo ni --motor: no hay quien juegue"}))
        return 0
    res = correr(pensar, a.decisiones, a.cada, nombre=nombre)
    if a.guardar and res.get("estado") != "NO_DATA":
        res["guardada"] = str(guardar(res))
    resumen = {k: res.get(k) for k in ("estado", "parado", "veredicto", "medidas", "final", "base", "guardada", "causa")}
    print(json.dumps(resumen, ensure_ascii=False, indent=1))
    return 0


def _pensar_regla(cada, corre=None):
    """La regla fija como «motor», para probar la tuberia sin cargar un modelo, y dice lo que es.
    Un segundo motor juega su PROPIA partida al mismo ritmo (la instantanea no es el estado entero y
    no se puede reconstruir desde ella): si la tuberia es fiel, empata EXACTO con la base."""
    mo = Motor(corre=corre) if corre else Motor()
    mo.orden(op="inicial", ley=LEY)
    estado = {"n": 0}

    def pensar(prompt):
        if estado["n"]:
            mo.orden(op="ciclos", n=cada)
        estado["n"] += 1
        a = mo.orden(op="piloto")["accion"]
        mo.orden(op="aplica", accion=a)
        return json.dumps(a)
    pensar.cierra = mo.cierra
    return pensar


if __name__ == "__main__":
    sys.exit(main())
