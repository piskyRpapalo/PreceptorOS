#!/usr/bin/env python3
"""consola.py · la consola soberana: qué hay en esta máquina, en una sola vista.

**Solo biblioteca estándar. SOLO LECTURA. Ni un socket (D68).**

POR QUÉ EXISTE
--------------
El tablero sabía con qué cerebro hablaba (`/api/cerebro`), pero no qué más hay
en el aparato: los modelos que Ollama guarda en el disco, los compañeros que la
web anuncia, el motor de theGame que ya vive en `atlas/`, el estado del rack.
Cada pieza existía; ninguna se veía desde el home. Esto las junta en un dict
con esquema `preceptoros.consola/1` que `GET /api/consola` sirve tal cual.

LAS TRES REGLAS QUE GOBIERNAN EL FICHERO
----------------------------------------
1. **Se lee, no se escribe.** Ninguna función de aquí abre un fichero para
   escribir, ni borra, ni renombra. La orden de parada (el centinela de
   `estado.py`) se DESCRIBE -- qué fichero crear y dónde --, no se ejecuta. Un
   panel que pudiera parar el rack por sí solo sería un interruptor sin firma.
2. **Ni un socket.** Saber qué modelo está residente en Ollama, o si el
   servidor de juego contesta, exigiría hablarle por la red local. D68 lo
   prohíbe en el producto: esas casillas salen NO_DATA con su causa, nunca a
   cero y nunca adivinadas.
3. **Lo no medido lleva sello y causa.** Cada valor dice si es MEDIDO (lo
   comprobó esta función ahora), DECLARADO (lo dice un fichero que esta función
   no puede verificar) o PROPUESTA (un contrato que nadie ha firmado). Un
   número sin sello es un rumor con decimales.

Toda ruta que sale de aquí pasa por la regla de `_ruta_visible` (la misma que
usa `bin/preceptoros-pwa`): dice dónde, nunca de quién.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import pathlib

import estado as _estado
import guardrails as G

ESQUEMA = "preceptoros.consola/1"
AQUI = os.path.dirname(os.path.abspath(__file__))

# La instantánea del rack la escribe el laboratorio (timer de 5 min). Pasados
# 15 min ya no describe el rack de ahora: se trata como ausente.
RACK_ESQUEMA = "hexelion.rack-instantanea/1"
RACK_RELATIVA = ("laboratorio", "rack.json")
RACK_RANCIA_S = 15 * 60
RACK_FUTURO_S = 2 * 60          # un reloj adelantado tampoco es un dato
RACK_TOPE_B = 64 * 1024         # un JSON de estado no pesa más; si pesa, no se lee
RACK_ESTADOS = ("ONLINE", "OFFLINE", "CRITICO", "NO_DATA")
RACK_BACKENDS = ("GPU", "CPU", "MIXTO")

COMPANEROS = "companeros.json"
# Lista BLANCA de lo que una ficha de compañero puede llevar. El personaje
# narra, no decide: cualquier campo fuera de aquí -- `decide`, `aprueba`,
# `autoriza`, `ejecuta`, o el que se invente mañana -- tumba la ficha entera.
# Es lista blanca y no negra porque un nombre de campo nuevo no avisa.
CAMPOS_FICHA = ("id", "nombre", "rol", "modelo_base", "adaptador", "permisos",
                "herramientas", "paralelo", "requiere_firma")

PROCEDENCIAS = ("humano", "piloto_base", "denso", "lora", "sintetico", "emulado")
CICLO_LORA = ("PROPUESTA", "EN_CANARIO", "ACTIVO", "CUARENTENA", "REVERTIDO")

CAUSA_RESIDENTE = ("saberlo exige la API de Ollama por socket y D68 lo "
                   "prohíbe en el producto")
CAUSA_USABLE = ("el chat del producto usa su cerebro base/afinado; usar otro "
                "exige arrancar el servidor con esa ruta (PROPUESTA)")
CAUSA_TOKS = "sin medición registrada; una velocidad no se supone"
SELLO_SHA = ("DECLARADO: nombre del blob, que Ollama verifica al descargarlo o "
             "crearlo; esta consola no lo re-hashea")


def nd(causa):
    """Un NO_DATA siempre lleva su causa. Sin causa es un hueco, no un dato."""
    return {"estado": "NO_DATA", "causa": causa}


# --- rutas que se pueden enseñar ---------------------------------------------
def ruta_visible(ruta):
    """La MISMA regla que `_ruta_visible` de `bin/preceptoros-pwa`.

    La PWA pasa la suya a `vista()` y es la que manda; esta es el respaldo para
    quien llame sin servidor (las pruebas cruzan las dos y exigen igualdad).
    """
    if not ruta:
        return None
    ruta = str(ruta)
    casa = os.path.expanduser("~")
    if ruta.startswith(casa):
        visible = "~" + ruta[len(casa):]
    else:
        trozos = ruta.strip("/").split("/")
        visible = "…/" + "/".join(trozos[-2:])
    tachado, hallazgos = G.redactar_salida(visible)
    if hallazgos:
        visible = tachado
    return visible


def _sanear(valor, casa):
    """Última pasada sobre TODA la salida: ningún texto lleva la casa entera.

    Los ficheros que se leen (la instantánea del rack, sobre todo) los escribe
    otro proceso. Que prometa no llevar rutas no basta: se comprueba aquí.
    """
    if isinstance(valor, str):
        if casa and casa != "/" and casa in valor:
            valor = valor.replace(casa, "~")
        if "/home/" in valor:
            tachado, _h = G.redactar_salida(valor)
            valor = tachado if "/home/" not in tachado else \
                valor.replace("/home/", "/…/")
        return valor
    if isinstance(valor, dict):
        return {k: _sanear(v, casa) for k, v in valor.items()}
    if isinstance(valor, list):
        return [_sanear(v, casa) for v in valor]
    return valor


def _leer_json(ruta, tope=RACK_TOPE_B):
    """(datos, causa). Lectura acotada: nunca se carga un fichero sin techo."""
    try:
        if os.path.getsize(ruta) > tope:
            return None, f"pesa más de {tope} B; no se lee"
        with open(ruta, "r", encoding="utf-8") as fh:
            return json.load(fh), None
    except FileNotFoundError:
        return None, "no existe"
    except (OSError, ValueError) as e:
        return None, f"no se pudo leer ({type(e).__name__})"


def _sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as fh:
        for trozo in iter(lambda: fh.read(1 << 20), b""):
            h.update(trozo)
    return h.hexdigest()


# --- modelos -----------------------------------------------------------------
def raiz_ollama():
    """Donde Ollama guarda sus modelos. `OLLAMA_MODELS` manda si está puesta."""
    return pathlib.Path(os.environ.get("OLLAMA_MODELS")
                        or os.path.join(os.path.expanduser("~"), ".ollama", "models"))


def _blob(raiz, digest):
    if not isinstance(digest, str) or not digest.startswith("sha256:"):
        return None
    return raiz / "blobs" / digest.replace(":", "-", 1)


def modelos_pc(raiz=None, visible=ruta_visible):
    """Los modelos que Ollama tiene EN DISCO, leídos de sus manifiestos.

    No pregunta a Ollama (eso sería un socket): mira los ficheros que Ollama
    escribe. Lo que solo sabe Ollama en marcha -- qué está residente, a qué
    velocidad genera -- sale NO_DATA con causa.
    """
    raiz = pathlib.Path(raiz) if raiz else raiz_ollama()
    manif = raiz / "manifests"
    if not manif.is_dir():
        return {"estado": "NO_DATA", "causa": "no hay manifiestos de Ollama en "
                + str(visible(str(manif))), "raiz": visible(str(raiz)),
                "modelos": []}
    modelos = []
    for registro in sorted(p for p in manif.iterdir() if p.is_dir()):
        for ruta in sorted(registro.rglob("*")):
            if not ruta.is_file():
                continue
            partes = ruta.relative_to(registro).parts
            if len(partes) < 2:
                continue
            nombre, tag = "/".join(partes[:-1]), partes[-1]
            if registro.name != "registry.ollama.ai":
                nombre = registro.name + "/" + nombre
            elif nombre.startswith("library/"):
                nombre = nombre[len("library/"):]
            modelos.append(_ficha_modelo(raiz, ruta, nombre, tag))
    modelos.sort(key=lambda m: m["id"])
    return {"estado": "MEDIDO", "fuente": "manifiestos de Ollama en disco",
            "raiz": visible(str(raiz)), "total": len(modelos),
            "con_riesgo": sum(1 for m in modelos if m["riesgos"]),
            "modelos": modelos}


def _ficha_modelo(raiz, ruta, nombre, tag):
    ficha = {
        "id": f"{nombre}:{tag}", "nombre": nombre, "tag": tag,
        "familia": nd("sin config legible"), "parametros": nd("sin config legible"),
        "cuantizacion": nd("sin config legible"),
        "bytes": None, "sha256": None, "sello_sha256": SELLO_SHA,
        "blob_presente": False, "adaptador": None,
        # `latest` es un tag movedizo: hoy apunta a una cosa y mañana a otra,
        # y en esta casa ya apuntó a variantes Thinking. Nunca canon.
        "riesgos": (["tag_latest"] if tag == "latest" else []),
        "residente": nd(CAUSA_RESIDENTE),
        "tok_s": nd(CAUSA_TOKS),
        "usable_en_chat": False, "causa_usable": CAUSA_USABLE,
    }
    datos, causa = _leer_json(ruta)
    if not isinstance(datos, dict):
        ficha["error"] = causa or "manifiesto no es un objeto"
        return ficha
    capas = datos.get("layers") if isinstance(datos.get("layers"), list) else []
    for capa in capas:
        if not isinstance(capa, dict):
            continue
        tipo = capa.get("mediaType")
        if tipo == "application/vnd.ollama.image.model":
            ficha["sha256"] = str(capa.get("digest", ""))[len("sha256:"):] or None
            ficha["bytes"] = capa.get("size") if isinstance(capa.get("size"), int) else None
            blob = _blob(raiz, capa.get("digest"))
            try:
                ficha["blob_presente"] = bool(blob and blob.is_file()
                                              and blob.stat().st_size == ficha["bytes"])
            except OSError:
                ficha["blob_presente"] = False
        elif tipo == "application/vnd.ollama.image.adapter":
            # Un adaptador va AL LADO de la base, como capa propia del
            # manifiesto. Se enseña que existe y cuánto pesa; no se mezcla.
            ficha["adaptador"] = {"bytes": capa.get("size"),
                                  "sha256": str(capa.get("digest", ""))[7:] or None,
                                  "sello": "MEDIDO en el manifiesto"}
    cfg = (datos.get("config") or {}) if isinstance(datos.get("config"), dict) else {}
    blob_cfg = _blob(raiz, cfg.get("digest"))
    if blob_cfg:
        conf, causa = _leer_json(blob_cfg)
        if isinstance(conf, dict):
            for campo, clave in (("familia", "model_family"),
                                 ("parametros", "model_type"),
                                 ("cuantizacion", "file_type")):
                v = conf.get(clave)
                ficha[campo] = v if isinstance(v, str) and v else nd(
                    f"la config de Ollama no trae `{clave}`")
    return ficha


def modelos_producto(paquete):
    """Lo que `_cerebro_paquete` ya decidió. Se copia, no se recalcula."""
    if not isinstance(paquete, dict):
        return nd("el paquete del cerebro no llegó")
    opciones = []
    for op in paquete.get("opciones") or []:
        o = dict(op)
        o["usable_en_chat"] = bool(op.get("disponible"))
        opciones.append(o)
    return {"estado": "MEDIDO", "fuente": "/api/cerebro (afinado.elegir)",
            "en_uso": paquete.get("en_uso"), "opciones": opciones}


# --- compañeros --------------------------------------------------------------
def ficha_valida(ficha):
    """(True, None) o (False, causa). Lista blanca: lo que no está, sobra."""
    if not isinstance(ficha, dict):
        return False, "la ficha no es un objeto"
    sobran = sorted(set(ficha) - set(CAMPOS_FICHA))
    if sobran:
        return False, ("campos fuera de la lista blanca (el personaje narra, "
                       "no decide): " + ", ".join(sobran))
    for campo in ("permisos", "herramientas"):
        if not isinstance(ficha.get(campo), list):
            return False, f"`{campo}` debe ser una lista"
    firma = ficha.get("requiere_firma")
    if not (isinstance(firma, dict) and firma.get("salida_externa") is True):
        return False, "toda salida externa requiere firma y la ficha no lo dice"
    return True, None


def companeros(raiz_repo=AQUI):
    datos, causa = _leer_json(os.path.join(raiz_repo, COMPANEROS))
    if not isinstance(datos, dict):
        return {**nd(f"{COMPANEROS}: {causa or 'no es un objeto'}"), "fichas": []}
    fichas, rechazadas = [], []
    for f in datos.get("companeros") or []:
        ok, porque = ficha_valida(f)
        if ok:
            fichas.append(f)
        else:
            rechazadas.append({"id": (f or {}).get("id") if isinstance(f, dict) else None,
                               "causa": porque})
    return {"estado": datos.get("estado", "PROPUESTA"), "fuente": datos.get("fuente"),
            "nota": datos.get("nota"), "fichas": fichas, "rechazadas": rechazadas}


# --- theGame -----------------------------------------------------------------
def thegame(raiz_repo=AQUI):
    atlas = os.path.join(raiz_repo, "atlas")
    man, causa = _leer_json(os.path.join(atlas, "MANIFIESTO.json"))
    esperado = (man or {}).get("ficheros") if isinstance(man, dict) else None
    esperado = esperado if isinstance(esperado, dict) else {}
    ficheros = []
    try:
        nombres = sorted(n for n in os.listdir(atlas)
                         if n.endswith((".js", ".mjs")))
    except OSError:
        nombres = []
    for n in nombres:
        sha = _sha256(os.path.join(atlas, n))
        dec = esperado.get(n)
        ficheros.append({"fichero": n, "sha256": sha, "sello": "MEDIDO",
                         "integridad": ("NO_DECLARADO" if dec is None else
                                        "CUADRA" if dec == sha else "NO_CUADRA")})
    return {
        "estado": "MEDIDO" if ficheros else "NO_DATA",
        "causa": None if ficheros else "no hay motor en atlas/",
        "motor": ficheros,
        "manifiesto": ({"web_commit": man.get("web_commit"),
                        "contenido_v": man.get("contenido_v")}
                       if isinstance(man, dict) else nd(f"MANIFIESTO.json: {causa}")),
        "idiomas": {"en": {"estado": "MEDIDO", "nota": "la lengua del motor"},
                    "resto": nd("pendiente de revisión humana y medición")},
        "servidor_local": {
            **nd("el producto no sondea puertos (D68); el enlace se prueba al pulsarlo"),
            "enlace": "http://127.0.0.1:8000/",
            "sello_enlace": "DECLARADO por el README de la web (servidor local)"},
        "como_juega_la_ia": "atlas/corre.mjs por tubería (D68), sin socket",
    }


# --- juez de media -----------------------------------------------------------
def juez_media():
    return {
        "estado": "NO_DATA", "causa": "sin flujo firmado",
        "contrato": {
            "sello": "PROPUESTA",
            "campos": {
                "modalidad": ["audio", "video"],
                "origen": ["local", "rack", "externa", "EMULADO"],
                "coste": "número con unidad, o NO_DATA",
                "ttl": "segundos de vida del veredicto",
                "alcance": "qué puede tocar el veredicto",
                "requiere_firma": "true siempre que origen sea externa",
                "salida_hash": "sha256 de la salida juzgada",
            },
        },
    }


# --- rack --------------------------------------------------------------------
def _ahora():
    return _dt.datetime.now(_dt.timezone.utc)


def instantanea(raiz_casa, ahora=None, visible=ruta_visible):
    """La foto del rack que deja el laboratorio. Rancia o rota = NO_DATA entera.

    No se pinta ni un campo de una instantánea que no pasa: medio dato viejo al
    lado de medio dato nuevo se lee como un estado que nunca existió.
    """
    ruta = pathlib.Path(raiz_casa).joinpath(*RACK_RELATIVA)
    donde = visible(str(ruta))
    datos, causa = _leer_json(ruta)
    if datos is None:
        return {**nd(f"rack.json {causa}"), "fichero": donde}
    if not isinstance(datos, dict) or datos.get("esquema") != RACK_ESQUEMA:
        return {**nd(f"esquema distinto de {RACK_ESQUEMA}"), "fichero": donde}
    try:
        generado = _dt.datetime.fromisoformat(str(datos.get("generado")))
    except ValueError:
        return {**nd("`generado` no es una fecha ISO-8601"), "fichero": donde}
    if generado.tzinfo is None:
        return {**nd("`generado` no lleva zona horaria; sin zona no hay edad"),
                "fichero": donde}
    edad = ((ahora or _ahora()) - generado).total_seconds()
    if edad > RACK_RANCIA_S:
        return {**nd(f"rancia: {int(edad // 60)} min (> {RACK_RANCIA_S // 60} min)"),
                "fichero": donde, "edad_s": int(edad)}
    if edad < -RACK_FUTURO_S:
        return {**nd("`generado` está en el futuro; reloj desajustado"),
                "fichero": donde}
    nodos = []
    for n in datos.get("nodos") or []:
        if not isinstance(n, dict):
            continue
        est = n.get("estado") if n.get("estado") in RACK_ESTADOS else "NO_DATA"
        nodos.append({"nodo": str(n.get("nodo") or "?"), "estado": est,
                      "nota": G.redactar_salida(str(n.get("nota") or ""))[0]})
    ol = datos.get("ollama") if isinstance(datos.get("ollama"), dict) else {}
    residentes = [{"modelo": str(r.get("modelo")),
                   "backend": r.get("backend") if r.get("backend") in RACK_BACKENDS else None}
                  for r in (ol.get("residentes") or []) if isinstance(r, dict)]
    nivel = datos.get("nivel") if isinstance(datos.get("nivel"), dict) else None
    no_data = [{"campo": str(x.get("campo")), "causa": str(x.get("causa"))}
               for x in (datos.get("no_data") or []) if isinstance(x, dict)]
    return {"estado": "MEDIDO", "sello": "MEDIDO por el laboratorio; leído aquí",
            "fichero": donde, "edad_s": int(edad), "generado": datos.get("generado"),
            "fuente": datos.get("fuente"), "nodos": nodos,
            "ollama": {"residentes": residentes,
                       "backend": ol.get("backend") if ol.get("backend") in RACK_BACKENDS else None},
            "nivel": nivel, "no_data": no_data}


def rack(raiz_casa, ahora=None, visible=ruta_visible):
    base = pathlib.Path(raiz_casa)
    forzado = _estado.santuario_forzado(base)
    plan, causa_plan = _leer_json(base / "plan_ventanas.json")
    if isinstance(plan, dict):
        momento = plan.get("momento")
        edad = (int((ahora or _ahora()).timestamp() - momento)
                if isinstance(momento, (int, float)) else None)
        plan_vigente = {"estado": "DECLARADO", "fuente": visible(str(base / "plan_ventanas.json")),
                        "edad_s": edad, "cola": plan.get("cola"),
                        "pospuestos": plan.get("pospuestos"),
                        "ventana_pesados": plan.get("ventana_pesados")}
    else:
        plan_vigente = nd(f"plan_ventanas.json {causa_plan}")
    inter, causa_int = _leer_json(base / "interruptores.json")
    interruptores = ({"estado": "DECLARADO", "datos": inter} if inter is not None
                     else nd(f"interruptores.json {causa_int}; esta consola no los crea"))
    return {
        "nivel_instalacion": {
            "estado": "MEDIDO", "fuente": "estado.py",
            "en_vigor": _estado.nivel(base),
            "declarado": _estado.leer(base)[_estado.NIVEL],
            "maximo": _estado.NIVEL_MAXIMO,
            "centinela_puesto": forzado,
        },
        "orden_de_parada": {
            "que": f"crear el fichero vacío {_estado.CENTINELA} en la casa",
            "donde": visible(str(_estado.ruta_centinela(base))),
            "efecto": "el nivel en vigor baja a SANTUARIO (0) sin reescribir estado.json",
            "deshacer": f"borrar {_estado.CENTINELA}",
            "la_consola_lo_hace": False,
            "causa": "solo lectura: la parada es un gesto de la persona, no del panel",
        },
        "plan_vigente": plan_vigente,
        "interruptores": interruptores,
        "instantanea": instantanea(base, ahora, visible),
    }


# --- LoRAs -------------------------------------------------------------------
def loras(paquete):
    afinado = None
    if isinstance(paquete, dict):
        for op in paquete.get("opciones") or []:
            if op.get("cual") == "afinado":
                afinado = op
    return {
        "ciclo": list(CICLO_LORA), "sello_ciclo": "PROPUESTA",
        "procedencias": list(PROCEDENCIAS),
        "afinado_actual": afinado if afinado else nd("sin paquete de cerebro"),
        "regla": "un adaptador va al lado de su base, nunca encima; "
                 "promover o revertir no se hace desde la consola",
    }


# --- la vista entera -----------------------------------------------------------
def vista(cerebro_paquete, raiz_casa, raiz_ollama=None, ahora=None,
          visible=None, raiz_repo=AQUI):
    """El dict `preceptoros.consola/1`. Cada sección falla sola, nunca la vista."""
    visible = visible or ruta_visible
    secciones = {
        "modelos": lambda: {"producto": modelos_producto(cerebro_paquete),
                            "pc": modelos_pc(raiz_ollama, visible)},
        "companeros": lambda: companeros(raiz_repo),
        "thegame": lambda: thegame(raiz_repo),
        "juez_media": juez_media,
        "rack": lambda: rack(raiz_casa, ahora, visible),
        "loras": lambda: loras(cerebro_paquete),
    }
    salida = {"esquema": ESQUEMA, "solo_lectura": True,
              "generado": (ahora or _ahora()).isoformat(timespec="seconds")}
    for nombre, hacer in secciones.items():
        try:
            salida[nombre] = hacer()
        except Exception as e:                      # una sección rota no tumba el home
            salida[nombre] = nd(f"la sección falló ({type(e).__name__})")
    return _sanear(salida, os.path.expanduser("~"))
