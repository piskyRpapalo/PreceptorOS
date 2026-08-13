#!/usr/bin/env python3
# M2 · cierre · la firma del manifiesto. Los cinco criterios del spec firmado.
# Escritos ANTES de manifest.py. Deben fallar todos antes de la implementacion.
# Solo biblioteca estandar. memory.py se importa del arbol del producto.
from __future__ import annotations

import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memory as M      # noqa: E402  del producto, no se copia
import manifest as MF   # noqa: E402


def tmp_ruta():
    return os.path.join(tempfile.mkdtemp(prefix="m2f_"), "memoria.db")


def con_recuerdos(n=2):
    ruta = tmp_ruta()
    M.crear(ruta)
    with M.abrir(ruta) as c:
        for i in range(n):
            M.escribir_engrama(c, what=f"recuerdo {i}",
                               why=None if i % 2 else f"porque {i}")
    return ruta


CASOS = []


def caso(nombre):
    def deco(fn):
        CASOS.append((nombre, fn))
        return fn
    return deco


# --- criterio 4 · el que importa. Va primero. ------------------------------

@caso("4 · firmar, anadir un recuerdo, verificar -> DEBE fallar")
def t4():
    ruta = con_recuerdos(2)
    with M.abrir(ruta) as c:
        texto = MF.firmar(MF.generar(c), nombre="quien sea")
        ok, motivo = MF.verificar(texto, c)
        assert ok, f"recien firmado deberia verificar: {motivo}"
        M.escribir_engrama(c, what="un recuerdo posterior a la firma")
        ok2, motivo2 = MF.verificar(texto, c)
    assert ok2 is False, "el manifiesto sigue cuadrando tras cambiar la memoria"
    assert motivo2 and motivo2 != "", "falla sin decir por que"
    assert "memor" in motivo2.lower() or "cambi" in motivo2.lower(), \
        f"el motivo no explica que la memoria cambio: {motivo2}"
    # Las cifras del motivo tienen que ser CIERTAS: 2 firmados, 3 ahora.
    # Un mensaje de error con numeros inventados es una medicion falsa.
    assert "2 recuerdos firmados, 3 ahora" in motivo2, \
        f"las cifras del motivo no son las reales: {motivo2}"


# --- criterio 1 · el hash es estable al firmar -----------------------------

@caso("1 · anadir la firma tras el marcador de fin NO cambia el hash")
def t1():
    ruta = con_recuerdos(3)
    with M.abrir(ruta) as c:
        sin_firma = MF.generar(c)
        h1 = MF.hash_cuerpo(sin_firma)
        firmado = MF.firmar(sin_firma, nombre="Nombre Con Acentos áéí")
        h2 = MF.hash_cuerpo(firmado)
    assert h1 == h2, "firmar cambio el hash del cuerpo"
    assert len(h1) == 64, f"el hash no es sha256 completo: {len(h1)}"
    declarado = re.search(r"^sha256\(body\):\s*([0-9a-f]{64})$", firmado, re.M)
    assert declarado, "el manifiesto no declara el hash del cuerpo"
    assert declarado.group(1) == h1, "el hash declarado no es el del cuerpo"
    i_fin = firmado.index(MF.MARCA_FIN)
    assert firmado.index("signed_by") > i_fin, "la firma esta DENTRO del cuerpo"
    assert firmado.index("sha256(body)") > i_fin, "el hash esta dentro del cuerpo"


# --- criterio 2 · firmar no muta la memoria --------------------------------

@caso("2 · firmar no muta ningun recuerdo ni su updated_at")
def t2():
    ruta = con_recuerdos(3)
    with M.abrir(ruta) as c:
        antes = [dict(r) for r in c.execute("select * from engrams order by id")]
        texto = MF.firmar(MF.generar(c), nombre="alguien")
        despues = [dict(r) for r in c.execute("select * from engrams order by id")]
    # Precondicion: este test no puede pasar por no hacer nada. Si el
    # manifiesto esta vacio, la comparacion de "antes y despues" es trivial.
    assert MF.MARCA_INICIO in texto and MF.MARCA_FIN in texto, \
        "no hay manifiesto que comparar: el test pasaria por vacio"
    assert len(MF.lineas_huella(texto)) == 3, \
        "el cuerpo no tiene las tres huellas de los tres recuerdos"
    assert antes == despues, "firmar modifico la memoria"
    fuente = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "manifest.py"), encoding="utf-8").read()
    escrituras = re.findall(r"\b(update|insert into|delete from)\s+engrams",
                            fuente, re.IGNORECASE)
    assert not escrituras, f"manifest.py escribe en engrams: {escrituras}"


# --- criterio 3 · sin nombre sigue siendo firma ----------------------------

@caso("3 · sin nombre en el perfil, signed_by NO_DATA y la firma es valida")
def t3():
    ruta = con_recuerdos(1)
    with M.abrir(ruta) as c:
        texto = MF.firmar(MF.generar(c), nombre=None)
        assert f"signed_by: {M.AUSENTE}" in texto, \
            "sin nombre no escribe NO_DATA visible"
        ok, motivo = MF.verificar(texto, c)
    assert ok, f"una firma anonima deberia ser valida: {motivo}"


# --- criterio 5 · memoria vacia ------------------------------------------

@caso("5 · firmar una memoria vacia es legitimo: se firma que no hay nada")
def t5():
    ruta = tmp_ruta()
    M.crear(ruta)
    with M.abrir(ruta) as c:
        texto = MF.firmar(MF.generar(c), nombre=None)
        assert MF.lineas_huella(texto) == [], \
            f"memoria vacia con huellas: {MF.lineas_huella(texto)}"
        assert "memories: 0" in texto, "no declara cero recuerdos"
        ok, motivo = MF.verificar(texto, c)
    assert ok, f"un manifiesto de memoria vacia deberia verificar: {motivo}"


# --- extras que el spec implica -------------------------------------------

@caso("6 · manipular el cuerpo a mano rompe la integridad")
def t6():
    ruta = con_recuerdos(2)
    with M.abrir(ruta) as c:
        texto = MF.firmar(MF.generar(c))
        # Alteracion DETERMINISTA y dentro de la region firmada: se cambia el
        # recuento declarado. Nada de ramas if/else: un test que altera un
        # sitio distinto segun el contenido no prueba lo que dice probar.
        assert "memories: 2" in MF.cuerpo(texto), "el cuerpo no declara el recuento"
        alterado = texto.replace("memories: 2", "memories: 99", 1)
        ok, motivo = MF.verificar(alterado, c)
    assert ok is False, "un cuerpo alterado a mano sigue verificando"
    assert "integr" in motivo.lower() or "hash" in motivo.lower(), \
        f"el motivo no habla de integridad: {motivo}"


@caso("7 · archivar un recuerdo invalida el manifiesto y lo dice")
def t7():
    ruta = con_recuerdos(2)
    with M.abrir(ruta) as c:
        texto = MF.firmar(MF.generar(c))
        i = c.execute("select id from engrams order by id").fetchone()[0]
        M.archivar(c, i)
        ok, motivo = MF.verificar(texto, c)
    assert ok is False, "archivar no invalido el manifiesto"


@caso("8 · el manifiesto no contiene el texto de los recuerdos, solo huellas")
def t8():
    ruta = tmp_ruta()
    M.crear(ruta)
    secreto = "esto no deberia aparecer en el manifiesto"
    with M.abrir(ruta) as c:
        M.escribir_engrama(c, what=secreto)
        texto = MF.firmar(MF.generar(c))
    # Precondicion: sin manifiesto real, "el secreto no aparece" es trivial.
    lineas = MF.lineas_huella(texto)
    assert len(lineas) == 1, "el cuerpo no tiene la huella del unico recuerdo"
    assert re.search(r"[0-9a-f]{16}", lineas[0]), \
        "la linea del cuerpo no contiene una huella hexadecimal"
    assert secreto not in texto, \
        "el manifiesto transcribe el recuerdo: es una fuga por la puerta de atras"


# --- modo sabotaje --------------------------------------------------------

SABOTAJES = (
    ("hash que cubre la firma",
     "manifest.py",
     'def hash_cuerpo(texto):\n    return _sha256(cuerpo(texto))',
     'def hash_cuerpo(texto):\n    return _sha256(texto)'),
    ("firmar toca updated_at",
     "manifest.py",
     "    return texto + linea_firma",
     "    _c_global.execute(\"update engrams set updated_at=datetime('now')\")\n"
     "    return texto + linea_firma"),
    ("la verificacion ignora la vigencia",
     "manifest.py",
     "    if cuerpo_actual != cuerpo_firmado:",
     "    if False:"),
)


def main_sabotaje():
    import shutil
    import subprocess
    print("── M2 · CIERRE · MODO SABOTAJE · se EXIGE rojo " + "─" * 20)
    aqui = os.path.dirname(os.path.abspath(__file__))
    original = os.path.join(aqui, "manifest.py")
    sha_antes = _sha_fichero(original)
    no_detectados = []
    for nombre, fichero, ancla, sustitucion in SABOTAJES:
        destino = os.path.join(tempfile.mkdtemp(prefix="sab_m2f_"), "arbol")
        shutil.copytree(aqui, destino)
        ruta = os.path.join(destino, fichero)
        s = open(ruta, encoding="utf-8").read()
        if ancla not in s:
            print(f"  AVISO · {nombre}: el ancla ya no existe en el codigo")
            no_detectados.append(nombre + " (ancla perdida)")
            continue
        open(ruta, "w", encoding="utf-8").write(s.replace(ancla, sustitucion, 1))
        r = subprocess.run([sys.executable, "test_manifest.py"], cwd=destino,
                           capture_output=True, text=True)
        fallos = [l for l in r.stdout.splitlines()
                  if l.strip().startswith(("FALLO", "ERROR"))]
        if r.returncode == 0:
            print(f"  VERDE · {nombre} · LA SUITE NO LO DETECTO")
            no_detectados.append(nombre)
        else:
            print(f"  roja  · {nombre}")
            if fallos:
                print(f"          {fallos[0].strip()[:88]}")
    if _sha_fichero(original) != sha_antes:
        print("  CRITICO: el sabotaje escribio en el arbol original")
        no_detectados.append("arbol original mutado")
    else:
        print(f"\nMODULO ORIGINAL INTACTO (sha256 {sha_antes[:16]}…)")
    total = len(SABOTAJES)
    print(f"\nRESULTADO SABOTAJE: {total - len(no_detectados)}/{total} detectadas")
    return 1 if no_detectados else 0


@caso("9 · el sello firma con el nombre del perfil, no como anonimo")
def t9():
    # M-D64. `manifest --sign` leia la clave de perfil "called_you", que es como
    # se llamaba en la propuesta y que NADIE escribe: M-D60 la nombro "name". La
    # lectura no fallaba, devolvia NO_DATA — asi que quien habia dado su nombre
    # veia su sello firmado como anonimo y no habia forma de notarlo desde el
    # producto. Un nombre mal escrito no rompe: miente en silencio.
    ruta = con_recuerdos(1)
    with M.abrir(ruta) as c:
        M.escribir_perfil(c, "name", "David")
    destino = os.path.join(os.path.dirname(ruta), "manifest-firmado.txt")
    codigo = MF.main(["--db", ruta, "--sign", "--out", destino])
    assert codigo == 0, f"firmar devolvio codigo {codigo}"
    texto = open(destino, encoding="utf-8").read()
    assert MF.firmante(texto) == "David", \
        (f"signed_by es {MF.firmante(texto)!r} y la persona dio su nombre: "
         "el sello se firma con una clave de perfil que nadie escribe")

    # Y la clase entera del fallo, no solo su instancia: toda clave que
    # manifest.py pida al perfil tiene que ser una clave que el perfil tenga.
    fuente = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "manifest.py"), encoding="utf-8").read()
    pedidas = set(re.findall(r"leer_perfil\(\s*\w+\s*,\s*[\"'](\w+)[\"']", fuente))
    fantasmas = pedidas - set(M.CLAVES_PERFIL)
    assert not fantasmas, \
        f"manifest.py lee claves de perfil que nadie escribe: {sorted(fantasmas)}"


def _sha_fichero(ruta):
    import hashlib
    return hashlib.sha256(open(ruta, "rb").read()).hexdigest()


def main():
    fallos = 0
    print("── M2 · CIERRE · FIRMA DEL MANIFIESTO " + "─" * 28)
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
    total = len(CASOS)
    print(f"\nRESULTADO: {total - fallos}/{total} correctos, {fallos} fallo(s)")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main_sabotaje() if "--sabotaje" in sys.argv[1:] else main())
