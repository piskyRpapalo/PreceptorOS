"""VT11: supervisión local del motor (AI Act art. 14), sin autoridad.

No certifica cumplimiento legal. Carga explícita, hash fijado y fusible:
un fallo exige otra activación humana. No descarga ni escribe memoria.
"""
import http.client
import json
import re
import shlex
import threading
from pathlib import Path

import consola
import orquestador

CAUSAS = frozenset({
    "motor_no_activado", "configuracion_invalida", "motor_no_disponible",
    "modelo_no_coincide", "blob_no_verificado", "gguf_invalido",
    "daemon_modelo_distinto", "motor_http_rechazado", "motor_respuesta_excesiva",
    "carga_incompleta", "datos_invalidos", "prompt_fuera_de_molde",
    "salida_fuera_de_molde", "motor_no_residente",
})


class MotorNoDisponible(RuntimeError):
    def __init__(self, causa):
        self.causa = causa if causa in CAUSAS else "motor_no_disponible"
        super().__init__(self.causa)


def _peticion(ruta, cuerpo=None):
    if ruta not in ('/api/show', '/api/generate', '/api/ps'):
        raise ValueError('ruta de motor no permitida')
    conn = http.client.HTTPConnection('127.0.0.1', 11434, timeout=60)
    try:
        method = 'GET' if cuerpo is None else 'POST'
        headers = {'Content-Type': 'application/json'}
        data = json.dumps(cuerpo, allow_nan=False, ensure_ascii=False).encode('utf-8') if cuerpo is not None else None
        conn.request(method, ruta, body=data, headers=headers)
        response = conn.getresponse()
        if response.status != 200:
            raise MotorNoDisponible('motor_http_rechazado')
        contenido = response.read(65537)
        if len(contenido) > 65536:
            raise MotorNoDisponible('motor_respuesta_excesiva')
        resultado = json.loads(contenido.decode('utf-8', errors='strict'),
                               object_pairs_hook=orquestador._json_unico,
                               parse_constant=lambda _: (_ for _ in ()).throw(ValueError('JSON no finito')))
        if type(resultado) is not dict:
            raise ValueError('respuesta JSON no es objeto')
        return resultado
    finally:
        conn.close()


def _verificar(modelo, sha256, raiz, peticion):
    modelos = consola.modelos_pc(raiz)['modelos']
    fichas = [m for m in modelos if m['id'] == modelo]
    if len(fichas) != 1 or fichas[0]['sha256'] != sha256:
        raise MotorNoDisponible('modelo_no_coincide')
    if fichas[0].get('adaptador') is not None:
        raise MotorNoDisponible('modelo_no_coincide')

    verificacion = consola.verificar_blob(sha256, raiz)
    if verificacion['estado'] != 'MEDIDO':
        raise MotorNoDisponible('blob_no_verificado')

    blob_path = Path(raiz) / 'blobs' / ('sha256-' + sha256)
    with blob_path.open('rb') as f:
        lee4 = f.read(4)
    if lee4 != b'GGUF':
        raise MotorNoDisponible('gguf_invalido')

    remoto = peticion('/api/show', {'model': modelo})
    modelfile = remoto.get('modelfile')
    if not isinstance(modelfile, str):
        raise MotorNoDisponible('daemon_modelo_distinto')

    lineas = [line.strip() for line in modelfile.splitlines() if line.strip()]
    if any(line.startswith('ADAPTER ') for line in lineas):
        raise MotorNoDisponible('daemon_modelo_distinto')
    from_lineas = [line for line in lineas if line.startswith('FROM ')]
    if not from_lineas:
        raise MotorNoDisponible('daemon_modelo_distinto')

    parsed = [shlex.split(line) for line in from_lineas]
    esperado = [['FROM', str(blob_path)]]
    if parsed != esperado:
        raise MotorNoDisponible('daemon_modelo_distinto')

    return verificacion['bytes']


class MotorLocal:
    def __init__(self, modelo, sha256, *, raiz=None, peticion=None):
        self.modelo = modelo
        self.sha256 = sha256
        self.raiz = (Path(raiz) if raiz is not None else consola.raiz_ollama()).resolve()
        self._peticion = peticion if peticion is not None else _peticion
        self._cerrojo = threading.RLock()
        self._activo = False
        self._causa = "motor_no_activado"
        self._bytes_residentes = None
        self._bytes_vram = None
        if (type(modelo) is not str or not re.fullmatch(r"[a-zA-Z0-9_./:-]{1,120}", modelo)
                or type(sha256) is not str or not re.fullmatch(r"[0-9a-f]{64}", sha256)):
            raise MotorNoDisponible("configuracion_invalida")

    def _generacion(self, prompt):
        return {"model": self.modelo, "prompt": prompt, "stream": False,
                "think": False, "keep_alive": "5m",
                "options": {"temperature": 0, "seed": 17, "num_ctx": 4096,
                            "num_predict": 96}}

    def _cerrar(self, exc):
        self._activo = False
        self._causa = exc.causa if isinstance(exc, MotorNoDisponible) else "motor_no_disponible"
        self._bytes_residentes = None
        self._bytes_vram = None

    def estado(self):
        with self._cerrojo:
            return {"estado": "MEDIDO" if self._activo else "NO_DATA",
                    "causa": self._causa, "modelo": self.modelo, "sha256": self.sha256,
                    "bytes_residentes": self._bytes_residentes, "bytes_vram": self._bytes_vram,
                    "fuente": "ollama.api.ps:activacion", "autoridad": False}

    def activar(self):
        with self._cerrojo:
            try:
                _verificar(self.modelo, self.sha256, self.raiz, self._peticion)
                r = self._peticion('/api/generate', self._generacion(''))
                if not (r.get('done') is True and r.get('model') == self.modelo):
                    raise MotorNoDisponible('carga_incompleta')
                ps = self._peticion('/api/ps')
                residentes = [r for r in ps.get('models', []) if r.get('name') == self.modelo]
                if not (len(residentes) == 1 and type(residentes[0].get('size')) is int and residentes[0].get('size') > 0 and type(residentes[0].get('size_vram')) is int and residentes[0].get('size_vram') >= 0):
                    raise MotorNoDisponible('datos_invalidos')
                self._bytes_residentes = residentes[0].get('size')
                self._bytes_vram = residentes[0].get('size_vram')
                self._activo = True
                self._causa = None
            except Exception as exc:
                self._cerrar(exc)
            return self.estado()

    def __call__(self, prompt):
        with self._cerrojo:
            if not self._activo:
                raise MotorNoDisponible(self._causa)
            try:
                if not isinstance(prompt, str) or not prompt.strip() or len(prompt.encode('utf-8')) > 3072:
                    raise MotorNoDisponible('prompt_fuera_de_molde')
                _verificar(self.modelo, self.sha256, self.raiz, self._peticion)
                ps = self._peticion('/api/ps')
                if not any(r.get('name') == self.modelo for r in ps.get('models', [])):
                    raise MotorNoDisponible('motor_no_residente')
                r = self._peticion('/api/generate', self._generacion(prompt))
                if not (r.get('done') is True and r.get('model') == self.modelo and r.get('done_reason') != 'length'):
                    raise MotorNoDisponible('salida_fuera_de_molde')
                salida = r.get('response')
                if not isinstance(salida, str) or not salida.strip() or len(salida.encode('utf-8')) >= 600:
                    raise MotorNoDisponible('salida_fuera_de_molde')
                _verificar(self.modelo, self.sha256, self.raiz, self._peticion)
                return salida.strip()
            except Exception as exc:
                self._cerrar(exc)
                raise MotorNoDisponible(self._causa) from None
