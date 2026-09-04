#!/usr/bin/env python3
"""M2 · el idioma de la sesion, y la gramatica de las preguntas numeradas.

sistema: MVP · solo biblioteca estandar.

Estos casos son de CAJA NEGRA: arrancan `aurelius.py` como un proceso y le
hablan por la entrada estandar, igual que una persona. Se hace asi a
proposito. Un test que importara las funciones y llamara al dict de textos
comprobaria que el diccionario tiene claves, no que la sesion habla el idioma
que la persona eligio — y lo segundo es lo unico que le importa a nadie.

Ninguna prueba toca ~/.aurelius/. Cada caso trabaja en una base temporal que
se crea y se tira; si un dia una de estas lineas apunta al directorio real,
el caso 0 lo dice antes de que se escriba nada.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import memory as M                          # noqa: E402

CASOS = []


def caso(nombre):
    def envoltorio(fn):
        CASOS.append((nombre, fn))
        return fn
    return envoltorio


# --- cadenas que el producto tiene que decir ------------------------------
# Se declaran aqui, arriba y a la vista. Si manana cambian, este bloque es el
# unico sitio que hay que tocar, y el cambio se ve en el diff.

IDIOMA_EN = "English"
IDIOMA_ES = "Español"
CREAR_EN = "Create my memory now?"
CREAR_ES = "¿Creo mi memoria ahora?"
GUIA_EN = "1"
GUIA_ES = "2"

TEMPORALES = []


def tmp_dir():
    d = tempfile.mkdtemp(prefix="aurelius_idioma_")
    TEMPORALES.append(d)
    return d


def tmp_ruta():
    return os.path.join(tmp_dir(), "memory.db")


def correr(entradas, ruta=None, extra=()):
    """Corre una sesion completa alimentando stdin. Devuelve (salida, ruta).

    El ritmo va a 0: una suite que espera a que el tono termine de escribir se
    deja de correr, y un mecanismo que no se corre no protege nada.

    AURELIUS_TEST=1 no es un interruptor de conveniencia: `arranque()` (D75) se
    ejecuta ANTES de `sesion()` y pregunta por el cerebro y por la voz. Sin la
    bandera, esas dos preguntas se comen las dos primeras lineas del guion —
    la sesion recibe el guion desplazado y el idioma nunca se contesta. Este
    fichero prueba la SESION, no el arranque: el arranque tiene su suite en
    test_descarga.py y test_estado.py. Y ademas cierra el caso 0: sin la
    bandera, `arranque()` llama a `casa.asegurar()`, que escribe estado.json
    en el ~/.aurelius de la persona.
    """
    ruta = ruta or tmp_ruta()
    entorno = dict(os.environ, AURELIUS_RITMO="0", PYTHONIOENCODING="utf-8",
                   AURELIUS_TEST="1")
    proc = subprocess.run(
        [sys.executable, "preceptoros.py", "--db", ruta, *extra],
        input="\n".join(entradas) + "\n", cwd=AQUI, env=entorno,
        capture_output=True, text=True, timeout=60)
    return proc.stdout + proc.stderr, ruta


def bloque_hasta_primer_prompt(salida):
    """Todo lo que se dice ANTES de que se espere la primera respuesta."""
    corte = salida.find("  > ")
    return salida if corte < 0 else salida[:corte]


# --- caso 0 · la salvaguarda ----------------------------------------------

@caso("0 · ninguna prueba escribe en la memoria real de la persona")
def t0():
    # Dos cierres, y hacen falta los dos. El primero es estructural: TODA
    # sesion de prueba pasa por `correr`, y `correr` pasa siempre --db. El
    # segundo es empirico, por si alguna vez el primero deja de ser cierto.
    import inspect
    fuente = inspect.getsource(correr)
    assert '"--db", ruta' in fuente, \
        "correr() dejo de fijar la base: una prueba podria ir a la memoria real"
    real = os.path.expanduser("~/.aurelius")

    # La foto mira LA MEMORIA, no la carpeta entera, y es la misma correccion
    # que `test_cara.py` recibio para su caso 8 -- alli en dos pasos, aqui de
    # una vez, porque el motivo ya estaba medido cuando se llego a este:
    #
    #   * el directorio entero incluye la bitacora del servicio, el diario de
    #     `loops.db` y el cache de prompts, que son de OTROS subsistemas y se
    #     mueven solos mientras la tanda corre;
    #   * `memory.db-shm` es el indice en memoria compartida de SQLite y lo
    #     tocan tambien los LECTORES: con el servicio vivo cambia cada pocos
    #     segundos sin que nadie escriba nada. Medido el 2026-09-04: tres
    #     cambios en veinte segundos, `memory.db` y `-wal` quietos.
    #
    # Se queda el `-wal` porque es donde una escritura de verdad aparece
    # PRIMERO: en modo WAL `memory.db` no se entera hasta el checkpoint. Se
    # quita el ruido, no la alarma.
    def foto():
        if not os.path.isdir(real):
            return None
        suyos = [n for n in os.listdir(real)
                 if n.startswith("memory.db") and not n.endswith("-shm")]
        return sorted((n, os.stat(os.path.join(real, n)).st_mtime_ns)
                      for n in suyos)

    antes = foto()
    correr(["1", "2"])                  # una sesion entera, ingles, sin crear
    assert foto() == antes, "la suite toco la memoria real de la persona"


# --- los cuatro que pidio el Soberano -------------------------------------

@caso("1 · la primera pregunta de la sesion es el idioma")
def t1():
    salida, _ = correr(["1", "2"])
    primero = bloque_hasta_primer_prompt(salida)
    assert IDIOMA_EN in primero and IDIOMA_ES in primero, \
        f"la primera pregunta no ofrece los dos idiomas:\n{primero[-400:]}"
    # Y va ANTES de la de crear: preguntar en un idioma que la persona no ha
    # elegido es elegirlo por ella.
    i_idioma = salida.find(IDIOMA_ES)
    i_crear = min(x for x in (salida.find(CREAR_EN), salida.find(CREAR_ES))
                  if x >= 0)
    assert i_idioma < i_crear, "se pregunta por crear antes que por el idioma"


@caso("2 · el idioma elegido se guarda en el perfil")
def t2():
    salida, ruta = correr(["2", "1"])          # 2 = español, 1 = crear
    assert os.path.exists(ruta), f"la sesion no creo la base:\n{salida[-400:]}"
    with M.abrir(ruta) as c:
        assert M.leer_perfil(c, "language") == "es", \
            f"el perfil guarda language={M.leer_perfil(c, 'language')!r}"


@caso("3 · la sesion continua en el idioma elegido, en los dos sentidos")
def t3():
    es, _ = correr(["2", "1"])
    assert CREAR_ES in es, f"se eligio español y la segunda pregunta no lo esta:\n{es[:900]}"
    assert CREAR_EN not in es, "se eligio español y la sesion siguio en ingles"
    en, _ = correr(["1", "1"])
    assert CREAR_EN in en, f"se eligio ingles y la segunda pregunta no lo esta:\n{en[:900]}"
    assert CREAR_ES not in en, "se eligio ingles y la sesion siguio en español"


@caso("4 · 'yes' en una pregunta numerada se rechaza diciendo que numeros hay")
def t4():
    salida, _ = correr(["yes", "1", "2"])
    # El mensaje tiene que nombrar los numeros que SI valen. "no es una de las
    # opciones" no vale: describe el error sin decir como salir de el, que es
    # exactamente el sitio donde la persona se quedo atascada.
    rechazo = [l for l in salida.splitlines() if "yes" in l.lower()
               and l.strip().startswith(("'", "\"", "·", "-", "yes"))
               or ("yes" in l.lower() and re.search(r"\b1\b.*\b2\b", l))]
    assert rechazo, f"escribir 'yes' no produjo ningun rechazo visible:\n{salida[:900]}"
    texto = "\n".join(rechazo)
    assert re.search(r"\b1\b", texto) and re.search(r"\b2\b", texto), \
        f"el rechazo no dice que numeros valen: {texto!r}"
    assert re.search(r"n[uú]mero|number", texto, re.I), \
        f"el rechazo no dice que se espera un numero: {texto!r}"
    # Y la pregunta se repite: rechazar sin volver a preguntar es colgar.
    assert salida.count(IDIOMA_ES) >= 2, "tras el rechazo no se repitio la pregunta"


# --- lo que la decision del Soberano implica y nadie pidio probar ---------

@caso("5 · no elegir es NO_DATA, y el idioma por defecto es el ingles")
def t5():
    ruta = tmp_ruta()
    M.crear(ruta)                     # base ya existente: la sesion no la crea
    salida, _ = correr([], ruta=ruta)  # EOF inmediato: nadie elige
    with M.abrir(ruta) as c:
        assert M.leer_perfil(c, "language") == M.AUSENTE, \
            "no contestar dejo algo distinto de NO_DATA en el perfil"
    assert CREAR_ES not in salida, "sin elegir, la sesion no arranco en ingles"


@caso("6 · el idioma se ve en el perfil, al lado de device y name")
def t6():
    assert "language" in M.CLAVES_PERFIL, \
        f"language no es una clave del perfil: {M.CLAVES_PERFIL}"
    ruta = tmp_ruta()
    M.crear(ruta)
    with M.abrir(ruta) as c:
        vista = M.vista_perfil(c)
        assert "language" in vista, f"la cabecera no muestra el idioma: {vista}"
        assert f"language: {M.AUSENTE}" in vista, \
            "el idioma sin contestar no se declara ausente en la cabecera"
        M.escribir_perfil(c, "language", "es")
        M.escribir_perfil(c, "device", "el portatil de la cocina")
        vista = M.vista_perfil(c)
    for trozo in ("language: es", "device: el portatil de la cocina", "name"):
        assert trozo in vista, f"la cabecera pierde {trozo!r}: {vista}"


@caso("7 · un idioma ya contestado no se vuelve a preguntar")
def t7():
    ruta = tmp_ruta()
    M.crear(ruta)
    with M.abrir(ruta) as c:
        M.escribir_perfil(c, "language", "es")
    salida, _ = correr([], ruta=ruta)
    primero = bloque_hasta_primer_prompt(salida)
    assert IDIOMA_EN not in primero or IDIOMA_ES not in primero, \
        "se volvio a preguntar un idioma que ya estaba contestado"


@caso("8 · ninguna pregunta de la sesion mezcla las dos gramaticas")
def t8():
    # El bug que reporto el carbono: opciones numeradas y [y/N] a la vez, o
    # numeradas cuyo texto no dice que se espera un numero.
    salida, _ = correr(["1", "1"])
    for linea in salida.splitlines():
        assert "[y/N]" not in linea, \
            f"queda una pregunta con la gramatica vieja: {linea!r}"


@caso("9 · el idioma no es un recuerdo: elegirlo no escribe en engrams")
def t9():
    salida, ruta = correr(["2", "1"])
    with M.abrir(ruta) as c:
        n = c.execute("select count(*) from engrams").fetchone()[0]
    assert n == 0, f"elegir idioma y crear la base dejo {n} recuerdos"


@caso("10 · el texto de los dos idiomas cubre las mismas claves")
def t10():
    import textos as X
    idiomas = sorted(X.TEXTOS)
    assert set(idiomas) == {"en", "es"}, f"idiomas declarados: {idiomas}"
    claves = {i: set(X.TEXTOS[i]) for i in idiomas}
    falta_es = claves["en"] - claves["es"]
    falta_en = claves["es"] - claves["en"]
    assert not falta_es, f"al español le faltan claves: {sorted(falta_es)}"
    assert not falta_en, f"al ingles le faltan claves: {sorted(falta_en)}"
    # Y los huecos de formato tienen que coincidir: una traduccion que pierde
    # un {campo} revienta en tiempo de ejecucion, no en tiempo de revision.
    for k in claves["en"]:
        h_en = set(re.findall(r"{(\w+)}", str(X.TEXTOS["en"][k])))
        h_es = set(re.findall(r"{(\w+)}", str(X.TEXTOS["es"][k])))
        assert h_en == h_es, f"la clave {k} no lleva los mismos huecos: {h_en} vs {h_es}"


@caso("11 · un solo recuerdo no se cuenta en plural, en ninguno de los dos")
def t11():
    guion = ["", "", "un recuerdo cualquiera", "", "", "", "2"]
    es, _ = correr(["2", "1"] + guion)
    assert "1 recuerdo." in es and "1 recuerdos" not in es, \
        "el español cuenta un recuerdo en plural"
    en, _ = correr(["1", "1"] + guion)
    assert "1 memory." in en and "1 memories" not in en, \
        "el ingles cuenta un recuerdo en plural"


# --- sabotaje -------------------------------------------------------------

SABOTAJES = (
    ("la sesion no pregunta el idioma",
     "preceptoros.py",
     "    idioma = paso_idioma(ruta)",
     "    idioma = TX.DEFECTO"),
    ("el idioma elegido no se guarda en el perfil",
     "preceptoros.py",
     '        M.escribir_perfil(c, "language", idioma)',
     "        pass"),
    ("la sesion ignora el idioma y habla siempre en ingles",
     "preceptoros.py",
     "def tx(idioma, clave, **kw):\n    return TX.texto(idioma, clave, **kw)",
     'def tx(idioma, clave, **kw):\n    return TX.texto("en", clave, **kw)'),
    ("la pregunta numerada vuelve a tragarse cualquier cosa",
     "preceptoros.py",
     "        if linea.isdigit() and 1 <= int(linea) <= len(opciones):",
     "        if True:"),
)


def _sha(ruta):
    import hashlib
    return hashlib.sha256(open(ruta, "rb").read()).hexdigest()


def main_sabotaje():
    print("── M2 · IDIOMA · MODO SABOTAJE · se EXIGE rojo " + "─" * 20)
    sha_antes = {f: _sha(os.path.join(AQUI, f))
                 for f in ("preceptoros.py", "textos.py", "memory.py")}
    no_detectados = []
    for nombre, fichero, ancla, sustitucion in SABOTAJES:
        destino = os.path.join(tempfile.mkdtemp(prefix="sab_idioma_"), "arbol")
        shutil.copytree(AQUI, destino, ignore=shutil.ignore_patterns(
            "__pycache__", ".git"))
        ruta = os.path.join(destino, fichero)
        s = open(ruta, encoding="utf-8").read()
        if ancla not in s:
            print(f"  AVISO · {nombre}: ancla perdida")
            no_detectados.append(nombre + " (ancla perdida)")
            continue
        open(ruta, "w", encoding="utf-8").write(s.replace(ancla, sustitucion, 1))
        r = subprocess.run([sys.executable, "test_idioma.py"], cwd=destino,
                           capture_output=True, text=True, timeout=300)
        if r.returncode == 0:
            print(f"  VERDE · {nombre} · NO DETECTADO")
            no_detectados.append(nombre)
        else:
            fallo = next((l for l in r.stdout.splitlines()
                          if l.strip().startswith(("FALLO", "ERROR"))), "")
            print(f"  roja  · {nombre}\n          {fallo.strip()[:86]}")
    mutados = [f for f, h in sha_antes.items()
               if _sha(os.path.join(AQUI, f)) != h]
    if mutados:
        print(f"  CRITICO: el sabotaje escribio en el arbol original: {mutados}")
        no_detectados.append("original mutado")
    else:
        print("\nARBOL ORIGINAL INTACTO (aurelius.py, textos.py, memory.py)")
    total = len(SABOTAJES)
    print(f"\nRESULTADO SABOTAJE: {total - len(no_detectados)}/{total} detectadas")
    return 1 if no_detectados else 0



@caso("13 · el ritual pregunta el idioma ANTES que nada, y no lleva español fijo")
def t13():
    """El primer contacto del producto, medido en un teléfono el 2026-08-19.

    Abría con `tx(idioma, "final")` — el texto de CIERRE de la sesión — así que
    lo primero que leía alguien en su primer arranque era «Misión M2 completa:».
    Y pedía el nombre en castellano fijo, en un producto que habla dos idiomas.
    """
    import inspect
    import aurelius as A
    import textos as TX

    # Se mira el CODIGO, no la documentación: el docstring cita el fallo que
    # esta prueba vigila, y un test que lee comentarios se caza a sí mismo.
    fuente = inspect.getsource(A.ritual)
    fuente = fuente.split('"""')[0] + '"""'.join(fuente.split('"""')[2:])

    # Nada visible se escribe a mano: todo pasa por textos.py.
    for suelta in ("¿Cómo te llamas", "Ritmo de respuesta", "Ritual completado",
                   "Idioma / Language", "Escribe 1 o 2"):
        assert suelta not in fuente, \
            f"el ritual lleva una cadena visible sin pasar por textos.py: {suelta!r}"

    # Y el texto de cierre no puede usarse como saludo.
    assert '"final"' not in fuente, \
        "el ritual abre con el texto de CIERRE de la sesión"

    # El idioma va primero: antes que el nombre y antes que el ritmo.
    pos_idioma = fuente.index("PREGUNTA_IDIOMA")
    for despues in ("ritual_nombre", "ritual_ritmo", "ritual_hecho"):
        assert pos_idioma < fuente.index(despues), \
            f"{despues} se pregunta antes que el idioma: eso ya es elegirlo"

    # Las cuatro claves existen en los dos idiomas, o el ritual habla a medias.
    for clave in ("ritual_saludo", "ritual_nombre", "ritual_ritmo", "ritual_hecho"):
        for lengua in ("es", "en"):
            assert clave in TX.TEXTOS[lengua], f"falta {clave} en {lengua}"



@caso("14 · el idioma no se pregunta dos veces en un primer arranque")
def t14():
    """Medido en un clon fresco el 2026-08-20: el desconocido elegía idioma,
    el ritual lo guardaba, y treinta segundos después se lo volvían a preguntar.

    La causa: `paso_idioma` consultaba `estado()`, que dice SIN_ESQUEMA mientras
    falten los engramas — y el ritual escribe el perfil ANTES de que existan.
    Una memoria a medio nacer ya sabe en qué idioma le hablan.
    """
    import sqlite3
    import aurelius as A
    import memory as M

    ruta = os.path.join(tempfile.mkdtemp(), "memory.db")

    # Una memoria como la deja el ritual: perfil con idioma, sin engramas.
    con = sqlite3.connect(ruta)
    con.executescript(M.ESQUEMA_PERFIL)
    con.execute("insert into profile (key, value) values ('language', 'es')")
    con.commit()
    con.close()

    assert M.estado(ruta)[0] == "SIN_ESQUEMA", \
        "el escenario que se quiere probar es justo ese: sin engramas"
    assert A._idioma_firmado(ruta) == "es", \
        "el idioma estaba guardado y no se ve: se volverá a preguntar"



# --- la cara, no la sesion -------------------------------------------------
# Los casos de arriba prueban la SESION de terminal. Estos prueban las dos
# CARAS web, que es donde se escapo el idioma de verdad: tres etiquetas del
# panel de memoria estaban escritas a mano en el HTML y se quedaban en
# castellano con el perfil en English. Nadie lo vio porque nada lo miraba.

HTML_CARAS = ("interface/dashboard.html", "interface/app.html")

# Enganches validos: si un texto vive dentro de uno de estos, el JS lo traduce.
ENGANCHES = ("data-rotulo", "data-i18n", "data-volver", "data-cajon", "id=")

# Lo que puede quedarse literal: nombres propios, marcas, simbolos y lore.
BLANCA = {
    "PreceptorOS", "Preceptor", "Preceptor", "M0", "M1", "M2", "M3", "M4",
    "M5", "M6", "M7", "The Path", "Detail", "—", "·", "…", "⌂",
    # Los nombres de idioma se escriben en SU idioma: un selector que dice
    # «Spanish» en ingles obliga a saber ingles para elegir castellano.
    "Español", "English", "Português",
}


def _textos_sueltos(ruta):
    """Texto visible que NO cuelga de un enganche de traduccion."""
    import html as _html
    crudo = open(os.path.join(AQUI, ruta), encoding="utf-8").read()
    # Fuera lo que no se ve.
    crudo = re.sub(r"<(script|style)\b.*?</\1>", " ", crudo, flags=re.S | re.I)
    sueltos = []
    for m in re.finditer(r"<([a-zA-Z0-9]+)([^>]*)>([^<>]+)</\1>", crudo):
        atributos, texto = m.group(2), _html.unescape(m.group(3)).strip()
        if len(texto) < 3 or texto in BLANCA:
            continue
        if any(e in atributos for e in ENGANCHES):
            continue
        sueltos.append((ruta, texto[:60]))
    return sueltos


@caso("la cara no lleva texto suelto sin enganche de traduccion")
def t_cara_sin_texto_suelto():
    sueltos = []
    for ruta in HTML_CARAS:
        sueltos += _textos_sueltos(ruta)
    assert not sueltos, (
        "texto visible sin forma de traducirse (engancharlo con data-rotulo o "
        "data-i18n, o anadirlo a BLANCA si es nombre propio):\n  " +
        "\n  ".join(f"{r}: {t!r}" for r, t in sueltos))


@caso("toda clave que la cara USA esta declarada en los diccionarios")
def t_claves_usadas_existen():
    """Un `t("algo")` sin entrada en el diccionario no falla: pinta vacio.

    Ese es el problema. Se vio el 2026-09-04 con `elige_idioma`: la pantalla de
    eleccion de idioma salio con las tres cajas y SIN titulo, porque la clave se
    uso en el codigo y nunca llego al diccionario. Ninguna prueba lo vio -- la
    de simetria compara los idiomas ENTRE ELLOS, y los tres carecian de ella por
    igual, asi que estaban perfectamente simetricos en su hueco.

    La web ya tenia esta comprobacion desde hace tiempo (`claves_que_usa` en
    `test_web.py`); la cara del MVP no. Aqui se le pone.
    """
    for fichero in ("interface/dashboard.js", "interface/app.js"):
        crudo = open(os.path.join(AQUI, fichero), encoding="utf-8").read()
        sin_comentarios = re.sub(r"/\*.*?\*/", "", crudo, flags=re.S)
        sin_comentarios = re.sub(r"(?m)//.*$", "", sin_comentarios)
        usadas = set(re.findall(r'\bt\("([a-z_0-9]+)"\)', sin_comentarios))
        if not usadas:
            continue
        m = re.search(r"\n\s{2,4}es:\s*\{", crudo)
        if not m:
            continue
        trozo, prof = "", 0
        for ch in crudo[m.end() - 1:]:
            trozo += ch
            prof += (ch == "{") - (ch == "}")
            if prof == 0:
                break
        declaradas = set(re.findall(r"[\n,{]\s*([a-z_0-9]+)\s*:", trozo))
        faltan = usadas - declaradas
        assert not faltan, (
            f"{fichero} usa claves que no estan en el diccionario: "
            f"{sorted(faltan)} -- saldran vacias en pantalla")


@caso("todos los diccionarios de la cara tienen las MISMAS claves")
def t_diccionarios_simetricos():
    """Una clave que existe en un idioma y no en el otro es una fuga con fecha."""
    import json as _json
    for fichero in ("interface/dashboard.js", "interface/app.js"):
        crudo = open(os.path.join(AQUI, fichero), encoding="utf-8").read()
        claves = {}
        # Los idiomas se DESCUBREN del fichero, no se listan aqui. Con la
        # lista escrita a mano, anadir un idioma y olvidarse de esta linea
        # dejaba el nuevo sin comprobar -- y un idioma sin comprobar es
        # exactamente donde vive una clave que falta. Firmado 2026-09-04, al
        # entrar el portugues.
        presentes = re.findall(r"\n\s{2,4}([a-z]{2}):\s*\{", crudo)
        for idioma in presentes:
            m = re.search(rf"\n\s{{2,4}}{idioma}:\s*\{{", crudo)
            if not m:
                continue
            trozo, prof = "", 0
            for ch in crudo[m.end() - 1:]:
                trozo += ch
                prof += (ch == "{") - (ch == "}")
                if prof == 0:
                    break
            claves[idioma] = set(re.findall(r"[\n,{]\s*([a-z_0-9]+)\s*:", trozo))
        # El castellano es la referencia: es donde se escribe primero. Cada
        # idioma se compara contra el, en los dos sentidos -- una clave que
        # sobra es texto muerto, y una que falta es un hueco en pantalla.
        if len(claves) >= 2 and "es" in claves:
            for idioma, suyas in sorted(claves.items()):
                if idioma == "es":
                    continue
                faltan = claves["es"] - suyas
                sobran = suyas - claves["es"]
                assert not faltan and not sobran, (
                    f"{fichero} · {idioma}: claves asimetricas contra es · "
                    f"faltan={sorted(faltan)} · sobran={sorted(sobran)}")

def main():
    fallos = 0
    print("── M2 · IDIOMA DE LA SESION " + "─" * 38)
    for nombre, fn in CASOS:
        try:
            fn()
            print(f"  ok    · {nombre}")
        except AssertionError as e:
            fallos += 1
            print(f"  FALLO · {nombre}\n          -> {e}")
        except Exception as e:
            fallos += 1
            print(f"  ERROR · {nombre}\n          -> {type(e).__name__}: {e}")
    for d in TEMPORALES:
        shutil.rmtree(d, ignore_errors=True)
    total = len(CASOS)
    print(f"\nRESULTADO: {total - fallos}/{total} correctos, {fallos} fallo(s)")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main_sabotaje() if "--sabotaje" in sys.argv[1:] else main())
