"""Integridad de semillas fijadas; el hash esperado no acredita firma humana."""
from pathlib import Path
import json
import hashlib
import re

def _archivo(raiz, relativo, sha):
    if not isinstance(sha, str) or not re.fullmatch('[0-9a-f]{64}', sha):
        raise ValueError("El resumen no es válido.")

    raiz_real = Path(raiz).absolute()
    destino = raiz_real / relativo

    if Path(relativo).is_absolute() or '..' in Path(relativo).parts:
        raise ValueError("La ruta relativa no es válida.")

    for actual in (destino, *destino.parents):
        if actual.is_symlink():
            raise ValueError("Se encontró un enlace simbólico.")

    if not destino.resolve().is_relative_to(raiz_real.resolve()):
        raise ValueError("La ruta no está dentro del directorio raíz.")

    if not destino.is_file():
        raise ValueError("El objetivo no es un archivo.")

    with destino.open('rb') as f:
        contenido = f.read(1025)

    if not 0 < len(contenido) <= 1024:
        raise ValueError("El archivo no tiene la longitud requerida.")

    if hashlib.sha256(contenido).hexdigest() != sha:
        raise ValueError("El resumen del archivo no coincide.")

    return contenido

def _objeto(raiz, relativo, sha, esquema):
    contenido = _archivo(raiz, relativo, sha)
    objeto = json.loads(contenido)
    if not isinstance(objeto, dict):
        raise ValueError("Contenido no es un diccionario")
    if objeto.get('esquema') != esquema:
        raise ValueError("Esquema no coincide")
    return objeto

def _semilla(raiz, identificador, sha):
    semilla = _objeto(raiz, f'{identificador}/semilla.json', sha, 'preceptoros.semilla/1')
    if not isinstance(semilla['origen'], str) or not semilla['origen']:
        raise ValueError("Origen debe ser una cadena no vacía")
    if type(semilla['bytes']) is not int or semilla['bytes'] <= 0:
        raise ValueError("Bytes debe ser un entero positivo")
    if not isinstance(semilla['sha256'], str) or len(semilla['sha256']) != 64 or not re.match(r'^[0-9a-f]{64}$', semilla['sha256']):
        raise ValueError("SHA256 debe ser una cadena hexadecimal de 64 caracteres")
    if not isinstance(semilla['grupos'], list) or not semilla['grupos']:
        raise ValueError("Grupos debe ser una lista no vacía de digests")

    acumulado = bytearray()
    contador = 0

    for i, sha_grupo in enumerate(semilla['grupos']):
        grupo = _objeto(raiz, f'{identificador}/grupo-{i:03}.json', sha_grupo, 'preceptoros.bloques/1')
        if not isinstance(grupo['bloques'], list) or not grupo['bloques'] or len(grupo['bloques']) > 6:
            raise ValueError("Bloques debe ser una lista no vacía de longitud <= 6")

        for sha_bloque in grupo['bloques']:
            bloque = _archivo(raiz, f'{identificador}/bloque-{contador:03}.bin', sha_bloque)
            acumulado.extend(bloque)
            contador += 1

    if len(acumulado) != semilla['bytes']:
        raise ValueError("La longitud del acumulado no coincide con el valor especificado en el semilla")
    if hashlib.sha256(acumulado).hexdigest() != semilla['sha256']:
        raise ValueError("El SHA256 del acumulado no coincide con el valor especificado en el semilla")

    return contador

def verificar(raiz, esperado):
    try:
        objeto = _objeto(raiz, 'indice.json', esperado, 'preceptoros.herencia/1')
        if objeto.get('revision') != '41826fceeefa632abe4accc628244ae7ceedaf90':
            raise ValueError("Revisión no coincide")
        semillas = objeto.get('semillas', {})
        if not isinstance(semillas, dict) or not semillas:
            raise ValueError("Semillas no es un diccionario no vacío")
        total = 0
        for key, sha in semillas.items():
            if not isinstance(key, str) or not re.fullmatch(r'[a-z][a-z0-9_-]*', key):
                raise ValueError("Clave de semilla no válida")
            total += _semilla(raiz, key, sha)
        return {'estado': 'MEDIDO', 'semillas': len(semillas), 'bloques': total}
    except Exception as error:
        return {'estado': 'NO_DATA', 'causa': 'herencia invalida: ' + type(error).__name__}
