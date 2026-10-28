"""Frontera de registro local (AI Act art. 12), sin autoridad ni certificación.

Una tabla de traducción conserva etiquetas; no verifica firmas ni asigna color.
El techo se aplica al cuerpo serializado completo, antes de abrir el canal.
"""
import json
from pathlib import Path

MAX_BYTES = 1024

def _filas(origen):
    if not isinstance(origen, str):
        raise ValueError("origen inválido")
    try:
        with open(Path(__file__).parent / "data" / "aiact_art12_sellos.json", encoding='utf-8') as file:
            data = json.load(file)
        tabla = data['$defs'][origen]['oneOf']
        if not isinstance(tabla, list) or not tabla:
            raise ValueError("tabla de traducción u origen inválido")
        filas = []
        seen_consts = set()
        for item in tabla:
            if not isinstance(item, dict) or not item.keys() == {"const", "x-destino"}:
                raise ValueError("tabla de traducción u origen inválido")
            const = item.get("const")
            destino = item.get("x-destino")
            if not isinstance(const, str) or not const:
                raise ValueError("tabla de traducción u origen inválido")
            if const in seen_consts:
                raise ValueError("tabla de traducción u origen inválido")
            seen_consts.add(const)
            if destino is not None and (not isinstance(destino, str) or not destino):
                raise ValueError("tabla de traducción u origen inválido")
            filas.append(item)
        return filas
    except (OSError, KeyError, TypeError, json.JSONDecodeError, UnicodeError):
        raise ValueError


def serializar(cuerpo):
    if not isinstance(cuerpo, dict):
        raise ValueError("El cuerpo debe ser un diccionario")
    if set(cuerpo.keys()) != {"hilo", "texto", "rol", "sello", "maquina"}:
        raise ValueError("El cuerpo debe tener exactamente las claves: hilo, texto, rol, sello, maquina")
    if not isinstance(cuerpo["hilo"], str) or cuerpo["hilo"] not in ["app", "web", "lab", "orquesta"]:
        raise ValueError("El hilo debe ser una cadena en app/web/lab/orquesta")
    if not isinstance(cuerpo["texto"], str) or not cuerpo["texto"].strip():
        raise ValueError("El texto debe ser una cadena no vacía")
    if not isinstance(cuerpo["rol"], str) or len(cuerpo["rol"]) > 120:
        raise ValueError("El rol debe ser una cadena con longitud máxima de 120 caracteres")
    if not isinstance(cuerpo["maquina"], dict):
        raise ValueError("La maquina debe ser un diccionario")
    if not isinstance(cuerpo["sello"], str) or cuerpo["sello"] not in [f["const"] for f in _filas("canal")]:
        raise ValueError("El sello debe ser una cadena presente en las constantes de canal")
    try:
        crudo = json.dumps(cuerpo, ensure_ascii=False, sort_keys=True, allow_nan=False)
        if json.loads(crudo) != cuerpo:
            raise ValueError("El JSON no es reproducible")
        if len(crudo.encode("utf-8")) >= MAX_BYTES:
            raise ValueError("El cuerpo requiere menos de 1024 bytes UTF-8")
    except (TypeError, UnicodeError, RecursionError) as e:
        raise ValueError("cuerpo JSON o UTF-8 inválido") from None
    return crudo


def traducir(origen, sello, causa=None):
    if not isinstance(sello, str):
        raise ValueError('sello debe ser una cadena')
    if causa is not None and causa.strip() == '':
        raise ValueError('causa no puede ser blanca')

    fila = next((f for f in _filas(origen) if f['const'] == sello), None)
    if fila is None:
        raise ValueError('sello desconocido')

    destino = fila['x-destino']
    if destino is None:
        destino = 'NO_DATA'
        causa = 'equivalencia_no_aprobada'
    elif destino == 'NO_DATA' and causa is None:
        raise ValueError('falta causa')
    elif destino == 'STATIC' and causa is None:
        causa = 'etiqueta_textual_sin_color'

    resultado = {
        'origen': origen,
        'sello_original': sello,
        'sello': destino,
        'causa': causa,
        'autoridad': False
    }

    try:
        bruto = json.dumps(resultado, ensure_ascii=False, sort_keys=True, allow_nan=False).encode('utf-8')
    except UnicodeError:
        raise ValueError('texto UTF-8 inválido') from None

    if len(bruto) >= MAX_BYTES:
        raise ValueError('traducción fuera de tamaño')

    return resultado
