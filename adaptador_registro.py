#!/usr/bin/env python3
"""Registro de compatibilidad de adaptadores LoRA. **Solo biblioteca estándar.**

Módulo nativo de PreceptorOS APP que declara qué adaptadores son compatibles
con el backend de inferencia actual, sin activarlos. Sigue los patrones de
`afinado.py` (escritura atómica, huellas medidas) y `lab.py` (NO_DATA con
causa, estados declarados).

CONTRATO
--------
* El registro escribe; la APP lee. No se importa este módulo desde la APP:
  se lee el JSON producido.
* Un adaptador es compatible si su modelo base coincide, su arquitectura es
  soportada y el formato es conocido. La precisión de entrenamiento (bf16)
  vs cuantización de inferencia (Q4_K_M) **no** es motivo de rechazo.
* Cada veredicto lleva causa: sin causa no hay auditoría.
* Escritura atómica: `.parcial` → `os.replace`, como `afinado.py`.
* La identidad del modelo base se verifica por SHA-256 exacto, no por
  coincidencia de nombre. El nombre es solo una pista humana.
* El export produce un archivo separado; nunca sobrescribe el registro canónico.

ROLES CONOCIDOS
---------------
* **safety** (Laya) — inspección de contexto, clasificación de riesgo,
  propuestas de rechazo. Nunca otorga permisos.
* **code** (Jev) — comprensión de código, diffs, propuestas de refactor.
  Nunca fusiona ni firma.
* **guide** (Guide) — explicaciones claras, lenguaje accesible.
* **memory** (Memory) — referencias de contexto con evidencia.
* **measurement** (Measurement) — explicación de benchmarks, detección de
  evidencia faltante. Nunca fabrica mediciones.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

ESQUEMA = "preceptoros.adaptador-registro/1"
NOMBRE_REGISTRO = "adaptador_registro.json"
NOMBRE_EXPORT = "adaptador_estado.json"
TROZO = 1024 * 1024

ROLES_VALIDOS = ("safety", "code", "guide", "memory", "measurement")

# Módulos que un backend típico (transformers/Qwen) soporta como target
# para LoRA. Si el adaptador apunta a módulos fuera de esta lista, la
# arquitectura no coincide.
MODULOS_ARQUITECTURA_QWEN = {
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
    "embed_tokens", "lm_head",
}

# Formatos que el backend puede cargar (después de conversión si es necesario)
FORMATOS_SOPORTADOS = ("peft", "gguf")

# SHA-256 hex digest must be exactly 64 lowercase hex characters
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

# Maximum age for telemetry to be considered current (30 days)
TELEMETRY_MAX_AGE_DAYS = 30


def nd(causa):
    """NO_DATA con causa. Mismo patrón que `lab.py::nd`."""
    return {"estado": "NO_DATA", "causa": causa}


def huella_fichero(ruta):
    """SHA-256 del fichero, por trozos. Mismo patrón que `afinado.py`."""
    h = hashlib.sha256()
    try:
        with open(ruta, "rb") as fh:
            for bloque in iter(lambda: fh.read(TROZO), b""):
                h.update(bloque)
    except OSError:
        return None
    return h.hexdigest()


def _leer_reg(raiz):
    """Lee el registro JSON o devuelve vacío si no existe o está roto.

    - Si el archivo no existe: devuelve {} (registro nuevo, normal).
    - Si el archivo existe pero es JSON inválido: devuelve {"_corrupto": True}.
    - Si el archivo existe y es válido: devuelve los datos.
    """
    ruta = Path(raiz) / NOMBRE_REGISTRO
    if not ruta.exists():
        return {}
    try:
        with open(ruta, encoding="utf-8") as fh:
            datos = json.load(fh)
        if not isinstance(datos, dict):
            return {"_corrupto": True}
        return datos
    except json.JSONDecodeError:
        return {"_corrupto": True}


def _escribir_reg(raiz, datos):
    """Escritura atómica: `.parcial` → `os.replace`. Mismo patrón que `afinado.py`."""
    raiz = Path(raiz)
    raiz.mkdir(parents=True, exist_ok=True)
    destino = raiz / NOMBRE_REGISTRO
    tmp = raiz / (NOMBRE_REGISTRO + ".parcial")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(datos, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, destino)
    return destino


def _escribir_export(raiz, datos):
    """Escritura atómica del archivo de export separado.

    Nunca sobrescribe el registro canónico. Produce un archivo distinto
    que la APP lee como proyección de solo lectura.
    """
    raiz = Path(raiz)
    raiz.mkdir(parents=True, exist_ok=True)
    destino = raiz / NOMBRE_EXPORT
    tmp = raiz / (NOMBRE_EXPORT + ".parcial")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(datos, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, destino)
    return destino


# ---------------------------------------------------------------------------
# Registro público
# ---------------------------------------------------------------------------

class Registro:
    """Registro de adaptadores con escritura atómica.

    Uso típico:
        reg = Registro("/ruta/a/preceptor-runtime")
        reg.registrar("laya-v1", "safety", base_model, peft_config, medida)
        resultado = reg.es_compatible("laya-v1", backend_info)
        estado = reg.estado("laya-v1")
    """

    def __init__(self, raiz):
        self.raiz = Path(raiz)

    def registrar(self, adapter_id, rol, base_model, peft_config=None,
                  medida=None, capacidades=None, prohibido=None):
        """Registra un adaptador en el catálogo.

        Args:
            adapter_id: identificador único (ej. "laya-v1")
            rol: uno de ROLES_VALIDOS
            base_model: dict con "name" y opcionalmente "sha256"
            peft_config: dict con config PEFT (rank, alpha, target_modules, etc.)
            medida: dict con mediciones de entrenamiento (ram_pico_mb, temp_max_c, etc.)
            capacidades: lista de capacidades del adaptador
            prohibido: lista de acciones prohibidas para este rol

        Raises:
            ValueError: si el rol no es válido o el ID ya existe.
        """
        if rol not in ROLES_VALIDOS:
            raise ValueError(f"rol '{rol}' no conocido; usa uno de {ROLES_VALIDOS}")

        reg = _leer_reg(self.raiz)
        if reg.get("_corrupto"):
            raise ValueError("registro canónico corrupto; no se puede registrar")

        adaptadores = reg.setdefault("adaptadores", {})

        # R9: IDs duplicados no sobrescriben silenciosamente
        if adapter_id in adaptadores:
            raise ValueError(
                f"adaptador '{adapter_id}' ya registrado; no se sobrescribe"
            )

        entrada = {
            "rol": rol,
            "base_model": base_model,
        }
        if peft_config:
            entrada["peft_config"] = peft_config
        if medida:
            entrada["medicion"] = medida
        if capacidades:
            entrada["capacidades"] = capacidades
        if prohibido:
            entrada["prohibido"] = prohibido

        adaptadores[adapter_id] = entrada
        reg["esquema"] = ESQUEMA
        _escribir_reg(self.raiz, reg)
        return adapter_id

    def eliminar(self, adapter_id):
        """Elimina un adaptador del registro."""
        reg = _leer_reg(self.raiz)
        if reg.get("_corrupto"):
            return False
        adaptadores = reg.get("adaptadores", {})
        if adapter_id not in adaptadores:
            return False
        del adaptadores[adapter_id]
        _escribir_reg(self.raiz, reg)
        return True

    def listar(self):
        """Devuelve los IDs de adaptadores registrados."""
        reg = _leer_reg(self.raiz)
        if reg.get("_corrupto"):
            return []
        return list(reg.get("adaptadores", {}).keys())

    def es_compatible(self, adapter_id, backend_info):
        """Verifica compatibilidad determinista de un adaptador con un backend.

        Args:
            adapter_id: identificador del adaptador
            backend_info: dict con info del backend:
                - "nombre": nombre del backend (ej. "ollama")
                - "modelo": nombre del modelo base (ej. "qwen3-coder:30b")
                - "sha256": SHA-256 del blob del modelo (opcional)
                - "formato": formato del modelo (ej. "gguf")
                - "ram_disponible_mb": RAM disponible en MB (opcional)
                - "loader_capabilities": lista de formatos que el backend
                  puede cargar (opcional, pero requerido para COMPATIBLE)

        Returns:
            dict con "estado" (COMPATIBLE, INCOMPATIBLE, NO_DATA) y "causa".
        """
        reg = _leer_reg(self.raiz)
        if reg.get("_corrupto"):
            return nd("registro canónico corrupto")

        adaptadores = reg.get("adaptadores", {})

        if adapter_id not in adaptadores:
            return nd(f"adaptador '{adapter_id}' no registrado")

        ada = adaptadores[adapter_id]
        causas_incompatible = []
        causas_no_data = []

        # ------------------------------------------------------------------
        # 1. Identidad del modelo base (R1, R2, R5, P7)
        # ------------------------------------------------------------------
        base_model = ada.get("base_model") or {}
        # P7: base_model puede ser una cadena u otro tipo no-dict en JSON roto
        if not isinstance(base_model, dict):
            causas_no_data.append("base_model_malformed")
        backend_modelo = backend_info.get("modelo", "")
        backend_sha = backend_info.get("sha256", "")

        base_name = base_model.get("name", "") if isinstance(base_model, dict) else ""
        base_sha = base_model.get("sha256", "") if isinstance(base_model, dict) else ""

        # R5: Sin substring matching. Solo SHA-256 exacto establece identidad.
        # El nombre es solo una pista humana, no una verificación.
        # Defect 1 fix: validate SHA format before trusting it
        def _sha_valid(s):
            """Return True only if s is a well-formed SHA-256 hex string."""
            return bool(s and SHA256_PATTERN.match(s))

        base_sha_valid = _sha_valid(base_sha)
        backend_sha_valid = _sha_valid(backend_sha)

        sha_coincide = bool(
            base_sha and backend_sha and base_sha == backend_sha
        )

        if sha_coincide and base_sha_valid and backend_sha_valid:
            # SHA exacto y bien formado = identidad verificada
            identidad_ok = True
        elif sha_coincide and (not base_sha_valid or not backend_sha_valid):
            # Matching but malformed SHA — cannot trust as identity evidence
            causas_no_data.append("sha256_malformed")
            identidad_ok = None
        elif base_sha and backend_sha:
            # R1: Ambos SHA presentes pero diferentes → INCOMPATIBLE
            causas_incompatible.append(
                f"SHA-256 contradictorio: adaptador declara "
                f"{base_sha[:12]}…, backend tiene {backend_sha[:12]}…"
            )
            identidad_ok = False
        elif not base_sha and not base_name:
            # R2: Sin evidencia de identidad → NO_DATA
            causas_no_data.append("identity_unverified")
            identidad_ok = None  # NO_DATA
        elif not base_sha:
            # R2, R5: Solo nombre sin SHA → NO_DATA(identity_unverified)
            # El nombre solo es una pista, no una verificación
            causas_no_data.append("identity_unverified")
            identidad_ok = None  # NO_DATA
        else:
            # base_sha presente, backend_sha ausente → NO_DATA
            causas_no_data.append("backend_sha_missing")
            identidad_ok = None  # NO_DATA

        # ------------------------------------------------------------------
        # 2. Arquitectura — módulos objetivo (R2, P8)
        # ------------------------------------------------------------------
        peft = ada.get("peft_config") or {}
        # P8: peft_config puede ser una cadena u otro tipo no-dict en JSON roto
        if not isinstance(peft, dict):
            causas_no_data.append("peft_config_malformed")
        raw_target_modules = peft.get("target_modules") if isinstance(peft, dict) else None

        # Defect 5 fix: target_modules must be a list, not int/string/dict
        if not isinstance(raw_target_modules, (list, tuple)):
            causas_no_data.append("target_modules_malformed")
            target_modules = []
        else:
            target_modules = list(raw_target_modules) if raw_target_modules else []

        if not target_modules:
            # R2: Sin target_modules → NO_DATA(architecture_unverified)
            causas_no_data.append("architecture_unverified")
        else:
            desconocidos = set(target_modules) - MODULOS_ARQUITECTURA_QWEN
            if desconocidos:
                causas_incompatible.append(
                    f"módulos objetivo no reconocidos en arquitectura: "
                    f"{sorted(desconocidos)}"
                )

        # ------------------------------------------------------------------
        # 3. Loader capability del backend (R3)
        # ------------------------------------------------------------------
        loader_caps = backend_info.get("loader_capabilities")
        if not loader_caps:
            # R3: Sin loader_capabilities verificado → NO_DATA
            causas_no_data.append("loader_capability_unverified")
        else:
            # Defect 2 fix: only accept known formats as valid loader capabilities
            # A caller-supplied list is NOT proof — must contain at least one known format
            known_caps = set(loader_caps) & set(FORMATOS_SOPORTADOS)
            if not known_caps:
                causas_no_data.append("loader_capability_unverified")

        # ------------------------------------------------------------------
        # 4. Recursos — RAM disponible (R4)
        # ------------------------------------------------------------------
        medida = ada.get("medicion") or {}
        ram_pico = medida.get("ram_pico_mb")
        # R4: Usar 'in' para detectar presencia, no truthiness
        ram_disponible_presente = "ram_disponible_mb" in backend_info
        ram_disponible = backend_info.get("ram_disponible_mb")

        # Defect 4 fix: reject negative RAM measurements as corrupted data
        if ram_pico is not None and isinstance(ram_pico, (int, float)) and ram_pico < 0:
            causas_no_data.append("negative_ram_pico")
        if ram_disponible_presente and isinstance(ram_disponible, (int, float)) and ram_disponible < 0:
            causas_no_data.append("negative_ram_disponible")

        if ram_pico is not None and ram_disponible_presente:
            # R4: ram_disponible puede ser 0 — no usar truthiness
            if ram_pico > ram_disponible:
                causas_incompatible.append(
                    f"RAM pico del adaptador ({ram_pico} MB) > "
                    f"RAM disponible ({ram_disponible} MB)"
                )
        elif ram_pico is not None and not ram_disponible_presente:
            # Sin evidencia de RAM disponible → NO_DATA
            causas_no_data.append("ram_evidence_missing")

        # Defect 3 fix: stale telemetry check
        # If medición has a timestamp, verify it's not too old
        if isinstance(medida, dict) and "timestamp" in medida:
            ts_str = medida["timestamp"]
            try:
                # Parse ISO 8601 timestamp
                ts_str_clean = str(ts_str).replace("Z", "+00:00")
                ts = datetime.fromisoformat(ts_str_clean)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                age = now - ts
                if age > timedelta(days=TELEMETRY_MAX_AGE_DAYS):
                    causas_no_data.append("stale_telemetry")
            except (ValueError, TypeError):
                # Unparseable timestamp — treat as no timestamp (don't reject)
                pass

        # NOTA: La precisión de entrenamiento (bf16/fp32) vs cuantización
        # de inferencia (Q4_K_M) NO es motivo de rechazo. Es una decisión
        # del backend, no del registro.

        # ------------------------------------------------------------------
        # Veredicto final
        # ------------------------------------------------------------------
        if causas_no_data:
            return nd("; ".join(causas_no_data))

        if causas_incompatible:
            return {"estado": "INCOMPATIBLE", "causa": "; ".join(causas_incompatible)}

        return {"estado": "COMPATIBLE", "causa": "todos los checks pasaron"}

    def estado(self, adapter_id, backend_info=None):
        """Estado de lectura para un adaptador.

        Args:
            adapter_id: identificador del adaptador
            backend_info: opcional, dict con info del backend para incluir
                          el resultado de compatibilidad

        Returns:
            dict con el estado completo del adaptador para consumo de la APP.
        """
        reg = _leer_reg(self.raiz)
        if reg.get("_corrupto"):
            return nd("registro canónico corrupto")

        adaptadores = reg.get("adaptadores", {})

        if adapter_id not in adaptadores:
            return nd(f"adaptador '{adapter_id}' no registrado")

        ada = adaptadores[adapter_id]
        resultado = {
            "rol": ada.get("rol"),
            "base_model": ada.get("base_model", {}),
            "peft_config": ada.get("peft_config"),
            "medicion": ada.get("medicion"),
            "capacidades": ada.get("capacidades"),
            "prohibido": ada.get("prohibido"),
        }

        if backend_info:
            resultado["compatibilidad"] = self.es_compatible(adapter_id, backend_info)

        return resultado

    def estado_todos(self, backend_info=None):
        """Estado completo del registro para consumo de la APP.

        Args:
            backend_info: opcional, dict con info del backend

        Returns:
            dict con el esquema completo listo para ser leído por la APP.
        """
        reg = _leer_reg(self.raiz)
        if reg.get("_corrupto"):
            return {"esquema": ESQUEMA, "adaptadores": {}, "_corrupto": True}

        adaptadores = reg.get("adaptadores", {})

        resultado = {
            "esquema": ESQUEMA,
            "adaptadores": {},
        }

        for adapter_id in sorted(adaptadores.keys()):
            ada = adaptadores[adapter_id]
            entrada = {
                "rol": ada.get("rol"),
                "base_model": ada.get("base_model", {}),
                "capacidades": ada.get("capacidades"),
                "prohibido": ada.get("prohibido"),
                "medicion": ada.get("medicion"),
            }

            if backend_info:
                compat = self.es_compatible(adapter_id, backend_info)
                entrada["estado"] = compat["estado"]
                entrada["causa"] = compat.get("causa")

            resultado["adaptadores"][adapter_id] = entrada

        if backend_info:
            resultado["backend"] = {
                "nombre": backend_info.get("nombre"),
                "modelo": backend_info.get("modelo"),
                "sha256": backend_info.get("sha256"),
            }

        return resultado

    def exportar(self, backend_info=None):
        """Exporta el estado completo a JSON atómico en archivo separado.

        Produce `adaptador_estado.json` (no el registro canónico) que la APP
        lee sin importar este módulo. El registro canónico no se modifica.

        Args:
            backend_info: opcional, dict con info del backend

        Returns:
            Path al archivo exportado.
        """
        estado = self.estado_todos(backend_info)
        _escribir_export(self.raiz, estado)
        return self.raiz / NOMBRE_EXPORT
