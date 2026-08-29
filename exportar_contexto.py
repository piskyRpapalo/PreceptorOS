"""Puerta de Enlace de Privacidad · el contexto sale saneado o no sale.

QUÉ RESUELVE. Quien trabaja en local y pide ayuda a una IA de la nube tiene que
pegarle su contexto: rutas, IPs, nombres de máquina, a veces una clave. Ese
pegado es la fuga. Aquí el contexto se prepara ANTES de salir, y lo prepara
Python, no un modelo: el filtro es determinista y auditable, así que su
comportamiento no depende de que un modelo esté teniendo un buen día.

LO QUE **NO** GARANTIZA, y va escrito en el propio fichero exportado. Esto no es
una garantía matemática de que no quede nada privado: es un filtro con huecos
DECLARADOS. `corpus/muestras.json` los enumera uno a uno —URLs de gancho con
credencial en la ruta, rutas de Windows y de macOS, correos— y el export los
copia en su cabecera. Un filtro que promete cubrirlo todo es más peligroso que
uno que dice dónde no llega, porque el primero apaga la vigilancia de quien lo
usa.

FALLA CERRADO. Si la memoria no abre, si el filtro no carga o si algo no se
puede sanear, no se escribe un fichero a medias: se para y se dice por qué.
Un export parcial es peor que ninguno — nadie revisa lo que ya cree limpio.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import casa as _casa
import guardrails as G
import memory as M

CORPUS = Path(__file__).resolve().parent / "corpus" / "muestras.json"


class NoSePuedeExportar(Exception):
    """Algo impide garantizar el saneado. No se escribe nada."""


def roles_declarados():
    """Nombres de máquina -> rol genérico.

    Los NOMBRES los declara `policies.json`, que es de guardrails. Los ROLES
    viven en un fichero aparte, `roles.json`, que es de esta pasarela. La
    frontera no es burocracia: el validador de políticas rechaza cualquier
    campo que no reconoce —falla cerrado, y hace bien—, y ensancharlo desde
    aquí seria que una función de comodidad tocase el esquema de un módulo de
    seguridad. Guardrails decide qué es secreto; la pasarela decide cómo se
    describe lo que ya sabe que hay que tapar.

    Sustituir antes de redactar es deliberado: «la-torre» convertido en «nodo
    edge con CUDA» le sirve a la IA externa para razonar, mientras que
    [REDACTED:NODE_PATH] solo le dice que ahí había algo. Se gana privacidad y
    utilidad a la vez, que no suele pasar.
    """
    try:
        ruta_pol = Path(G.ruta_politicas())
        cfg = json.loads(ruta_pol.read_text(encoding="utf-8"))
    except Exception as e:                      # noqa: BLE001
        raise NoSePuedeExportar(f"no se pudieron leer las políticas: {e}") from None
    nombres = list(cfg.get("NODE_PATH", {}).get("nombres", []))
    roles = {}
    ruta_roles = ruta_pol.parent / "roles.json"
    if ruta_roles.is_file():
        try:
            roles = dict(json.loads(ruta_roles.read_text(encoding="utf-8")))
        except Exception as e:                  # noqa: BLE001
            raise NoSePuedeExportar(f"roles.json ilegible: {e}") from None
    # Un nombre declarado sin rol NO se queda al descubierto: se le da uno
    # genérico. El descuido de no describirlo no puede costar una fuga.
    for n in nombres:
        roles.setdefault(n, "otro nodo del equipo")
    return roles, nombres


def huecos_declarados():
    """Lo que el filtro NO caza hoy, dicho por el propio corpus."""
    try:
        d = json.loads(CORPUS.read_text(encoding="utf-8"))
    except Exception:                           # noqa: BLE001
        return []                                # sin corpus se dice que no se sabe
    return [(l["id"], l["motivo"]) for l in d.get("limites_declarados", [])]


# Formas de los huecos DECLARADOS. No redactan: señalan. La diferencia importa
# —redactar por sospecha destroza el texto y entrena a ignorar los avisos— pero
# un aviso genérico («hay huecos») tampoco sirve si el hueco está en la línea 40
# y nadie lo relaciona. Esto convierte «hay huecos» en «mira esta línea».
PISTAS = (
    ("correo", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    ("ruta-windows", r"[A-Za-z]:\\\\[^\s]+"),
    ("ruta-usuarios-mac", r"/Users/[^\s/]+"),
    ("token-con-rotulo-humano", r"(?i)\btoken\b[^\n:=]{0,20}[:=]\s*[A-Za-z0-9._\-]{12,}"),
    ("webhook-entrante", r"https?://[^\s]+/[A-Za-z0-9]{8,}"),
)


def pistas(texto):
    """Líneas que TAL VEZ lleven algo de lo que el filtro no cubre."""
    encontradas = []
    for n, linea in enumerate(texto.splitlines(), 1):
        for ident, patron in PISTAS:
            if re.search(patron, linea):
                encontradas.append((n, ident, linea.strip()[:90]))
                break
    return encontradas


def sustituir_roles(texto, roles):
    for nombre, rol in sorted(roles.items(), key=lambda kv: -len(kv[0])):
        texto = texto.replace(nombre, f"«{rol}»")
    return texto


def recoger(ruta_db, tema, limite):
    with M.abrir(ruta_db) as c:
        try:
            filas = M.buscar(c, tema, limite=limite)
        except Exception as e:                   # noqa: BLE001
            raise NoSePuedeExportar(f"la memoria no se pudo consultar: {e}") from None
    return filas


def componer(tema, filas, roles, hallazgos_acc):
    partes = []
    for f in filas:
        d = dict(f)
        crudo = "\n".join(str(d.get(k) or "") for k in ("what", "why", "learned"))
        crudo = sustituir_roles(crudo, roles)
        limpio, hallazgos = G.redactar_salida(crudo)
        for h in hallazgos:
            hallazgos_acc[h["policy"]] = hallazgos_acc.get(h["policy"], 0) + h["count"]
        partes.append((d.get("id"), limpio.strip()))
    return partes


def render(tema, partes, hallazgos, roles, nombres):
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    L = []
    L.append(f"# Contexto seguro · {tema}")
    L.append("")
    L.append(f"Generado por PreceptorOS el {ahora}. Puedes pegar esto en una IA externa.")
    L.append("")
    L.append("## Qué se ha quitado de aquí")
    if hallazgos:
        for pol, n in sorted(hallazgos.items()):
            L.append(f"- `{pol}` · {n} " + ("coincidencia" if n == 1 else "coincidencias"))
    else:
        L.append("- Nada. El filtro corrió y no encontró nada que redactar.")
    if roles:
        L.append("")
        L.append("Nombres de máquina sustituidos por su papel:")
        for nombre, rol in roles.items():
            L.append(f"- un nodo → «{rol}»")
    L.append("")
    L.append("## Qué NO garantiza este filtro")
    L.append("Es determinista y auditable, no infalible. Estos huecos están declarados:")
    for ident, motivo in huecos_declarados():
        L.append(f"- **{ident}** — {motivo}")
    L.append("")
    L.append("Revisa el texto antes de pegarlo. El filtro reduce el trabajo; no lo sustituye.")
    L.append("")
    L.append("## El contexto")
    if not partes:
        L.append("")
        L.append("NO_DATA — no hay recuerdos que casen con ese tema.")
    for ident, texto in partes:
        if not texto:
            continue
        L.append("")
        L.append(f"### recuerdo {ident}")
        L.append("")
        L.append(texto)
    return "\n".join(L) + "\n"


def exportar(tema, ruta_db=None, limite=40):
    roles, nombres = roles_declarados()
    db = Path(ruta_db) if ruta_db else Path(_casa.raiz()) / "memory.db"
    if not db.is_file():
        raise NoSePuedeExportar(f"no hay memoria en {db}")
    filas = recoger(db, tema, limite)
    hallazgos = {}
    partes = componer(tema, filas, roles, hallazgos)
    texto = render(tema, partes, hallazgos, roles, nombres)
    # Última pasada sobre el documento ENTERO, cabecera incluida: si el propio
    # tema o un título colase algo, aquí se caza. Barato y cierra el círculo.
    texto, extra = G.redactar_salida(texto)
    # Las pistas se calculan sobre el documento FINAL: lo que se mira es lo que
    # se va a pegar, no un borrador anterior.
    marcas = pistas(texto.split("## El contexto", 1)[-1])
    if marcas:
        aviso = ["", "## Revisa estas líneas antes de pegar", "",
                 "El filtro no cubre estas formas y aquí puede haber alguna. "
                 "No se han tocado: señalar no es redactar."]
        for n, ident, muestra in marcas:
            aviso.append(f"- línea {n} del contexto · posible **{ident}** · `{muestra}`")
        cabeza, _, cuerpo = texto.partition("## El contexto")
        texto = cabeza + "\n".join(aviso) + "\n\n## El contexto" + cuerpo
    return texto, hallazgos, extra


def main(argv=None):
    ap = argparse.ArgumentParser(description="Exporta contexto saneado para una IA externa")
    ap.add_argument("tema")
    ap.add_argument("--db", default=None)
    ap.add_argument("--salida", default="contexto_seguro.md")
    ap.add_argument("--limite", type=int, default=40)
    a = ap.parse_args(argv)
    try:
        texto, hallazgos, extra = exportar(a.tema, a.db, a.limite)
    except NoSePuedeExportar as e:
        print(f"[exportar] PARADO: {e}")
        print("[exportar] no se escribe nada: un export a medias es peor que ninguno")
        return 1
    Path(a.salida).write_text(texto, encoding="utf-8")
    total = sum(hallazgos.values()) + sum(h["count"] for h in extra)
    print(f"[exportar] escrito {a.salida} · {len(texto)} B")
    print(f"[exportar] redactado: {total} coincidencia(s) · {sorted(hallazgos) or 'ninguna política'}")
    print("[exportar] huecos declarados incluidos en la cabecera del fichero")
    return 0


if __name__ == "__main__":
    sys.exit(main())
