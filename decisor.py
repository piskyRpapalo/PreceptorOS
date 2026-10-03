#!/usr/bin/env python3
"""decisor.py · el tier 1: elegir de una tabla cerrada o decir NO_DATA.

**Solo biblioteca estándar. Sin socket. Solo LEE su tabla de reglas.**

POR QUÉ EXISTE
--------------
Buena parte de lo que parece trabajo de un modelo generativo es clasificación
disfrazada: «¿qué compañero contesta este mensaje?» tiene ocho respuestas
posibles, no infinitas. Para eso no hace falta un modelo que pueda alucinar:
hace falta una tabla de reglas explícitas que elige de la lista o se abstiene.
Esto es la capa determinista de la cascada (tier 1 → tier 2 → tier 3 →
carbono): cuesta microsegundos, no gasta token de frontera y no inventa.

EL CONTRATO, Y POR QUÉ CADA LÍMITE
---------------------------------
* La salida tiene la forma de `hexelion.eleccion.tier2/1` con `arnes.tier=1`.
* `choice` es SIEMPRE una de las opciones de entrada o `NO_DATA`. Una regla
  que apunta fuera de la tabla no puede ganar: la tabla manda sobre la regla.
* Sin regla que case, o con EMPATE en el peso máximo → `noul=true`,
  `choice=NO_DATA` con causa. **Un empate jamás se desempata por el orden de
  la lista**: el orden en que alguien escribió las opciones no es un dato
  sobre el mensaje, y desempatar con él sería decidir a escondidas.
* Más de 20 opciones → NO_DATA (el «cliff» del esquema).
* `score=null` y `probs=[]`, con su causa en `no_data`. El peso de una regla
  es un voto entero, no una probabilidad; el esquema prohíbe inventar
  confianza, y un tier determinista que dijera «95 %» estaría inventándola.
* Cada conjunto de reglas lleva su sha256 dentro. Sin sha256, o si no cuadra
  con el contenido, el conjunto NO se carga: una regla tocada a mano sin
  volver a sellar es otro decisor que dice ser este.
* La decisión es un dato tipado. El personaje que la cuente (`narrar`) la lee
  y devuelve una frase; no la toca. El personaje narra, no decide.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
SCHEMA_V = "hexelion.eleccion.tier2/1"
ESQUEMA_REGLAS = "preceptoros.reglas-decisor/1"
NO_DATA = "NO_DATA"
MAX_OPCIONES = 20
REGLAS_COMPANEROS = os.path.join(AQUI, "reglas", "companeros.json")
_CONTENT_V = re.compile(r"^sha256:[0-9a-f]{64}$")
CAUSA_SIN_PROB = ("tier 1 determinista: el peso de una regla no es una "
                  "probabilidad (prohibido inventar confianza)")


class ReglasInvalidas(ValueError):
    """El conjunto de reglas no se puede usar. Nunca se usa a medias."""


def _canon(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def sha_de(obj):
    return "sha256:" + hashlib.sha256(_canon(obj)).hexdigest()


def sellar(conjunto):
    """El sha256 de un conjunto es el de todo lo demás. Se usa al escribirlo."""
    cuerpo = {k: v for k, v in conjunto.items() if k != "sha256"}
    return sha_de(cuerpo)


def normalizar(texto):
    """Minúsculas y sin tildes: «Tradúceme» y «traduceme» son la misma petición."""
    t = unicodedata.normalize("NFKD", str(texto or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def cargar(ruta=REGLAS_COMPANEROS):
    """Lee y valida un conjunto. Cualquier duda es ReglasInvalidas."""
    try:
        with open(ruta, "r", encoding="utf-8") as fh:
            conjunto = json.load(fh)
    except (OSError, ValueError) as e:
        raise ReglasInvalidas(f"no se pudo leer ({type(e).__name__})") from None
    return validar(conjunto)


def validar(conjunto):
    if not isinstance(conjunto, dict) or conjunto.get("esquema") != ESQUEMA_REGLAS:
        raise ReglasInvalidas(f"esquema distinto de {ESQUEMA_REGLAS}")
    sello = conjunto.get("sha256")
    if not isinstance(sello, str) or not _CONTENT_V.match(sello):
        raise ReglasInvalidas("el conjunto no lleva sha256")
    if sello != sellar(conjunto):
        raise ReglasInvalidas("el sha256 no cuadra con las reglas: se tocaron sin sellar")
    tabla = conjunto.get("opciones")
    if not (isinstance(tabla, list) and tabla and all(isinstance(o, str) for o in tabla)
            and len(set(tabla)) == len(tabla)):
        raise ReglasInvalidas("`opciones` debe ser una lista de textos sin repetir")
    vistos = set()
    for r in conjunto.get("reglas") or []:
        if not isinstance(r, dict) or set(r) != {"id", "patron", "opcion", "peso"}:
            raise ReglasInvalidas("cada regla es {id, patron, opcion, peso}")
        if r["id"] in vistos:
            raise ReglasInvalidas(f"regla repetida: {r['id']}")
        vistos.add(r["id"])
        if r["opcion"] not in tabla:
            raise ReglasInvalidas(f"la regla {r['id']} apunta fuera de la tabla")
        if isinstance(r["peso"], bool) or not isinstance(r["peso"], int) or r["peso"] < 1:
            raise ReglasInvalidas(f"la regla {r['id']} no tiene un peso entero positivo")
        try:
            re.compile(r["patron"])
        except re.error:
            raise ReglasInvalidas(f"la regla {r['id']} tiene un patrón roto") from None
    return conjunto


def _plan_hash(conjunto_sha, opciones):
    with open(os.path.abspath(__file__), "rb") as fh:
        codigo = hashlib.sha256(fh.read()).hexdigest()
    return sha_de({"decisor": codigo, "reglas": conjunto_sha, "opciones": list(opciones)})


def _salida(content_v, choice, noul, plan_hash, no_data, regla, modelo):
    return {
        "schema_v": SCHEMA_V, "content_v": content_v, "choice": choice,
        "score": None, "noul": noul, "probs": [],
        "judge": {"veredicto": NO_DATA, "contra": "sin juez", "regla": regla},
        "arnes": {"tier": 1, "donde": "local-rack", "modelo": modelo,
                  "modo": "reglas"},
        "plan_hash": plan_hash, "no_data": no_data,
    }


def decidir(estado, opciones, content_v=None, conjunto=None, ruta=REGLAS_COMPANEROS):
    """Elige de `opciones` según las reglas, o se abstiene con causa.

    `estado` es {"texto": ...}. `content_v` es la huella del caso; si no llega
    se calcula del estado (la misma entrada da siempre la misma huella).
    """
    if content_v is None:
        content_v = sha_de(estado if isinstance(estado, (dict, list, str)) else str(estado))
    base_nd = [{"campo": "score", "causa": CAUSA_SIN_PROB},
               {"campo": "probs", "causa": CAUSA_SIN_PROB}]
    if not isinstance(content_v, str) or not _CONTENT_V.match(content_v):
        content_v = sha_de(str(content_v))
        base_nd.append({"campo": "content_v", "causa": "la huella de entrada no tenía forma sha256; se recalculó"})

    try:
        conjunto = validar(conjunto) if conjunto is not None else cargar(ruta)
    except ReglasInvalidas as e:
        return _salida(content_v, NO_DATA, True, sha_de({"reglas": None}),
                       base_nd + [{"campo": "choice", "causa": f"reglas inválidas: {e}"}],
                       "", "reglas:NO_DATA")
    modelo = f"reglas:{conjunto.get('tarea', '?')}@{conjunto['sha256']}"

    if not isinstance(opciones, list) or not all(isinstance(o, str) for o in opciones) \
            or len(set(opciones)) != len(opciones):
        return _salida(content_v, NO_DATA, True, _plan_hash(conjunto["sha256"], []),
                       base_nd + [{"campo": "choice", "causa": "opciones no son una lista cerrada de textos únicos"}],
                       "", modelo)
    plan = _plan_hash(conjunto["sha256"], opciones)
    if len(opciones) > MAX_OPCIONES or not opciones:
        return _salida(content_v, NO_DATA, True, plan,
                       base_nd + [{"campo": "choice", "causa": f"{len(opciones)} opciones: fuera de 1..{MAX_OPCIONES} (cliff)"}],
                       "", modelo)

    texto = normalizar((estado or {}).get("texto") if isinstance(estado, dict) else estado)
    pesos, casadas = {}, []
    for r in conjunto.get("reglas") or []:
        if r["opcion"] not in opciones:
            continue                    # la tabla de esta llamada manda
        if re.search(r["patron"], texto):
            pesos[r["opcion"]] = pesos.get(r["opcion"], 0) + r["peso"]
            casadas.append(r["id"])
    rastro = ",".join(casadas)
    if not pesos:
        return _salida(content_v, NO_DATA, True, plan,
                       base_nd + [{"campo": "choice", "causa": "ninguna regla casa: el tier 1 no sabe, escala"}],
                       rastro, modelo)
    tope = max(pesos.values())
    ganadoras = sorted(o for o, p in pesos.items() if p == tope)
    if len(ganadoras) > 1:
        return _salida(content_v, NO_DATA, True, plan,
                       base_nd + [{"campo": "choice", "causa": "empate entre " + " y ".join(ganadoras)
                                   + f" (peso {tope}): no se desempata por orden de lista, escala"}],
                       rastro, modelo)
    return _salida(content_v, ganadoras[0], False, plan, base_nd, rastro, modelo)


def valida_salida(s, opciones):
    """Validador stdlib de la forma (sin jsonschema). Lista de fallos, vacía si vale."""
    fallos = []
    claves = {"schema_v", "content_v", "choice", "score", "noul", "probs", "judge",
              "arnes", "plan_hash", "no_data"}
    if set(s) != claves:
        fallos.append(f"claves: {sorted(set(s) ^ claves)}")
    if s.get("schema_v") != SCHEMA_V:
        fallos.append("schema_v")
    for k in ("content_v", "plan_hash"):
        if not (isinstance(s.get(k), str) and _CONTENT_V.match(s[k])):
            fallos.append(k)
    if s.get("choice") != NO_DATA and s.get("choice") not in opciones:
        fallos.append("choice fuera de la tabla")
    if s.get("noul") is not (s.get("choice") == NO_DATA):
        fallos.append("noul y choice no concuerdan")
    if s.get("score") is not None or s.get("probs") != []:
        fallos.append("el tier 1 no inventa probabilidad")
    a = s.get("arnes") or {}
    if a.get("tier") != 1 or a.get("modo") != "reglas":
        fallos.append("arnes")
    if not isinstance(s.get("no_data"), list) or not all(
            isinstance(x, dict) and set(x) == {"campo", "causa"} for x in s["no_data"]):
        fallos.append("no_data")
    return fallos


def narrar(decision, fichas):
    """La frase del personaje sobre una decisión. LEE la decisión; no la toca.

    Trabaja sobre una copia: aunque mañana alguien escriba aquí una línea que
    asigne, la decisión que vuelve al llamador es la que entró.
    """
    d = copy.deepcopy(decision)
    if d.get("noul") or d.get("choice") == NO_DATA:
        causa = next((x["causa"] for x in d.get("no_data", []) if x.get("campo") == "choice"),
                     "sin causa")
        return f"El tier 1 no sabe: escala. ({causa})"
    nombre = next((f.get("nombre") for f in fichas if f.get("id") == d["choice"]), d["choice"])
    return f"El tier 1 sugiere a {nombre}. Eliges tú."


def leer_golden(ruta):
    with open(ruta, "r", encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def replay(conjunto, golden):
    """El gate de una regla nueva: ¿empeora ALGUNA decisión pasada?

    Devuelve la lista de casos que empeoran (vacía = la regla puede entrar).
    Empeorar es: un caso que acertaba deja de acertar, o cualquier caso pasa
    a una opción que no es la esperada. Pasar de NO_DATA a acertar es mejorar;
    pasar de NO_DATA a equivocarse, no.
    """
    validar(conjunto)
    peor = []
    for c in golden:
        d = decidir({"texto": c["texto"]}, list(conjunto["opciones"]), conjunto=conjunto)
        mal = d["choice"] not in (c.get("esperado"), NO_DATA)
        perdido = c.get("acierta") and d["choice"] != c.get("esperado")
        if mal or perdido:
            peor.append({"texto": c["texto"], "esperado": c.get("esperado"),
                         "antes": c.get("tier1"), "ahora": d["choice"]})
    return peor
