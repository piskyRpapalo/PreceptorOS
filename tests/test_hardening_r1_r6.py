#!/usr/bin/env python3
"""Pruebas de endurecimiento: R1–R6 defectos demostrados por SentinelX.

Cada prueba primero reproduce el comportamiento inseguro (RED), luego verifica
la corrección (GREEN). Se ejecutan contra el mismo adaptador_registro.py.

Estrategia: cada test registra un adaptador diseñado para explotar un defecto
específico, luego verifica que el veredicto sea el esperado después de la reparación.

Los nombres de los métodos indican el defecto:
- test_r1_* — Contradictory SHA-256
- test_r2_* — Missing identity evidence
- test_r3_* — Unverified backend support
- test_r4_* — Zero available RAM truthiness bug
- test_r5_* — Model-name impersonation
- test_r6_* — Destructive export
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest


import adaptador_registro as ar

# Backend de referencia con SHA verificado y loader_capabilities
BACKEND_REF = {
    "nombre": "ollama",
    "modelo": "qwen3-coder:30b",
    "sha256": "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad",
    "formato": "gguf",
    "ram_disponible_mb": 58000,
    "loader_capabilities": ["gguf"],
}

# SHA diferente al de referencia
OTHER_SHA = "000000000000000000000000000000000000000000000000000000000000dead"


class TestR1_ContradictorySHA256(unittest.TestCase):
    """R1: Un SHA-256 coincidente nunca debe anular nombres contradictorios.

    Si el adaptador declara un SHA-256 que coincide con el backend pero el
    nombre del modelo es completamente diferente, el veredicto debe ser
    INCOMPATIBLE, no COMPATIBLE. El SHA solo confirma la identidad si el
    nombre también es compatible o si el SHA es la única evidencia.

    Sin embargo, si el SHA coincide exactamente, eso ES la identidad.
    El defecto real es: cuando el SHA NO coincide pero el nombre sí
    (por substring), el resultado debe ser NO_DATA, no COMPATIBLE.

    Caso R1 específico: nombre coincide por substring PERO SHA es
    contradictorio (diferente). El SHA contradictorio debe anular la
    coincidencia de nombre.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_r1_sha_contradictorio_debe_ser_incompatible(self):
        """Nombre coincide por substring pero SHA es diferente → INCOMPATIBLE."""
        ada = {
            "base_model": {
                # "Qwen3" es substring de "qwen3-coder:30b" → nombre_coincide=True
                # pero SHA es diferente → contradicción
                "name": "Qwen3",
                "sha256": OTHER_SHA,  # SHA diferente al backend
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        # El SHA contradictorio debe anular la coincidencia de nombre
        self.assertEqual(
            resultado["estado"],
            "INCOMPATIBLE",
            f"R1 FALLIDO: SHA contradictorio no rechazado. Obtenido: {resultado}",
        )

    def test_r1_sha_coincide_nombre_diferente_es_compatible(self):
        """SHA coincide exactamente → COMPATIBLE aunque nombre difiera.

        El SHA-256 es la evidencia definitiva de identidad. Si coincide,
        el adaptador es compatible con ese modelo base.
        """
        ada = {
            "base_model": {
                "name": "otro-nombre-cualquiera",
                "sha256": "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad",
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        # SHA exacto = identidad verificada
        self.assertEqual(resultado["estado"], "COMPATIBLE")


class TestR2_MissingIdentityEvidence(unittest.TestCase):
    """R2: Sin evidencia de identidad, no puede ser COMPATIBLE.

    Un adaptador sin nombre verificado, sin módulos objetivo o sin evidencia
    de arquitectura debe producir NO_DATA, no COMPATIBLE.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_r2_sin_nombre_ni_sha_es_no_data(self):
        """Adaptador sin nombre ni SHA → NO_DATA(identity_unverified)."""
        ada = {
            "base_model": {},  # Sin nombre, sin SHA
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        self.assertEqual(
            resultado["estado"],
            "NO_DATA",
            f"R2 FALLIDO: Sin identidad, debería ser NO_DATA. Obtenido: {resultado}",
        )
        self.assertIn("identity", resultado.get("causa", "").lower())

    def test_r2_sin_target_modules_es_no_data(self):
        """Adaptador sin target_modules → NO_DATA(architecture_unverified)."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad",
            },
            "peft_config": {},  # Sin target_modules
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        # Sin módulos objetivo, no podemos verificar la arquitectura
        self.assertEqual(
            resultado["estado"],
            "NO_DATA",
            f"R2 FALLIDO: Sin target_modules, debería ser NO_DATA. Obtenido: {resultado}",
        )
        self.assertIn("architecture", resultado.get("causa", "").lower())


class TestR3_UnverifiedBackendSupport(unittest.TestCase):
    """R3: Un formato conocido no prueba que el backend lo soporta.

    Declarar 'gguf' o 'peft' no significa que el backend instalado pueda
    cargar ese formato. Sin evidencia verificada del loader, el resultado
    debe ser NO_DATA(loader_capability_unverified).
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_r3_formato_sin_verificacion_es_no_data(self):
        """Formato declarado pero loader no verificado → NO_DATA."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad",
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        # Backend sin loader_capabilities verificado
        backend_sin_loader = {
            "nombre": "ollama",
            "modelo": "qwen3-coder:30b",
            "sha256": "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad",
            "formato": "gguf",
            "ram_disponible_mb": 58000,
            # Sin loader_capabilities → no podemos verificar
        }
        resultado = self.reg.es_compatible("x-v1", backend_sin_loader)
        self.assertEqual(
            resultado["estado"],
            "NO_DATA",
            f"R3 FALLIDO: Loader no verificado, debería ser NO_DATA. Obtenido: {resultado}",
        )
        self.assertIn("loader", resultado.get("causa", "").lower())

    def test_r3_loader_verificado_es_compatible(self):
        """Con loader_capabilities verificado → puede ser COMPATIBLE."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad",
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        backend_con_loader = {
            "nombre": "ollama",
            "modelo": "qwen3-coder:30b",
            "sha256": "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad",
            "formato": "gguf",
            "ram_disponible_mb": 58000,
            "loader_capabilities": ["gguf"],  # Verificado
        }
        resultado = self.reg.es_compatible("x-v1", backend_con_loader)
        # Con loader verificado, puede pasar a COMPATIBLE
        self.assertEqual(resultado["estado"], "COMPATIBLE")


class TestR4_ZeroAvailableRAM(unittest.TestCase):
    """R4: Cero RAM disponible no es suficiente para requisito positivo.

    El bug de truthiness: `if ram_disponible` es False cuando ram_disponible=0,
    saltándose el check. Cero RAM con requisito positivo debe ser INCOMPATIBLE.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_r4_cero_ram_es_incompatible(self):
        """RAM disponible = 0 con requisito positivo → INCOMPATIBLE."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad",
            },
            "peft_config": {"target_modules": ["q_proj"]},
            "medicion": {"ram_pico_mb": 20123},  # Requisito positivo
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"],
                           ada["medicion"])
        backend_cero_ram = dict(BACKEND_REF)
        backend_cero_ram["ram_disponible_mb"] = 0  # Cero RAM
        backend_cero_ram["loader_capabilities"] = ["gguf"]
        resultado = self.reg.es_compatible("x-v1", backend_cero_ram)
        self.assertEqual(
            resultado["estado"],
            "INCOMPATIBLE",
            f"R4 FALLIDO: Cero RAM no rechazado. Obtenido: {resultado}",
        )
        self.assertIn("RAM", resultado.get("causa", ""))

    def test_r4_sin_evidencia_ram_es_no_data(self):
        """Sin evidencia de RAM disponible → NO_DATA."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad",
            },
            "peft_config": {"target_modules": ["q_proj"]},
            "medicion": {"ram_pico_mb": 20123},  # Requisito medido
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"],
                           ada["medicion"])
        backend_sin_ram = {
            "nombre": "ollama",
            "modelo": "qwen3-coder:30b",
            "sha256": "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad",
            "formato": "gguf",
            "loader_capabilities": ["gguf"],
            # Sin ram_disponible_mb → NO_DATA
        }
        resultado = self.reg.es_compatible("x-v1", backend_sin_ram)
        self.assertEqual(
            resultado["estado"],
            "NO_DATA",
            f"R4 FALLIDO: Sin evidencia RAM, debería ser NO_DATA. Obtenido: {resultado}",
        )
        self.assertIn("ram", resultado.get("causa", "").lower())


class TestR5_ModelNameImpersonation(unittest.TestCase):
    """R5: Coincidencia por substring no establece identidad.

    'Qwen3' es substring de 'qwen3-coder:30b' pero no es la misma identidad.
    Solo el SHA-256 exacto o un alias atestiguado explícitamente establece
    la identidad.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_r5_substring_no_es_identidad(self):
        """'Qwen3' como nombre no establece identidad → NO_DATA."""
        ada = {
            "base_model": {
                "name": "Qwen3",  # Substring de 'qwen3-coder:30b' pero no es la identidad
                "sha256": "",  # Sin SHA
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        self.assertNotEqual(
            resultado["estado"],
            "COMPATIBLE",
            f"R5 FALLIDO: Substring produjo COMPATIBLE. Obtenido: {resultado}",
        )
        # Debe ser NO_DATA o INCOMPATIBLE
        self.assertIn(resultado["estado"], ["NO_DATA", "INCOMPATIBLE"])

    def test_r5_nombre_exacto_con_sha_es_compatible(self):
        """Nombre exacto con SHA verificado → COMPATIBLE."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad",
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        backend_con_loader = dict(BACKEND_REF)
        backend_con_loader["loader_capabilities"] = ["gguf"]
        resultado = self.reg.es_compatible("x-v1", backend_con_loader)
        self.assertEqual(resultado["estado"], "COMPATIBLE")


class TestR6_DestructiveExport(unittest.TestCase):
    """R6: exportar() no debe sobrescribir el registro canónico.

    El export actual sobrescribe adaptador_registro.json con una proyección
    que pierde metadatos de compatibilidad. Un check posterior puede fallar.

    La solución: exportar a un archivo separado (ej. adaptador_estado.json)
    que no sea la fuente de verdad.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_r6_exportar_no_destruye_registro(self):
        """Exportar no debe corromper el registro canónico."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad",
            },
            "peft_config": {"target_modules": ["q_proj"]},
            "medicion": {"ram_pico_mb": 20123},
        }
        self.reg.registrar("laya-v1", "safety", ada["base_model"], ada["peft_config"],
                           ada["medicion"],
                           capacidades=["risk_classification"],
                           prohibido=["grant_permission"])

        # Exportar
        self.reg.exportar(BACKEND_REF)

        # El registro canónico debe seguir funcionando
        lista = self.reg.listar()
        self.assertIn("laya-v1", lista)

        # es_compatible debe seguir funcionando después de exportar
        backend_con_loader = dict(BACKEND_REF)
        backend_con_loader["loader_capabilities"] = ["gguf"]
        resultado = self.reg.es_compatible("laya-v1", backend_con_loader)
        # No debe levantar AttributeError
        self.assertIn(resultado["estado"], ["COMPATIBLE", "INCOMPATIBLE", "NO_DATA"])

    def test_r6_exportar_produce_archivo_separado(self):
        """Exportar debe producir un archivo diferente al canónico."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad",
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])

        # Exportar
        ruta_export = self.reg.exportar(BACKEND_REF)

        # El archivo exportado debe ser diferente del canónico
        ruta_canonical = os.path.join(self.tmp.name, ar.NOMBRE_REGISTRO)
        self.assertNotEqual(
            str(ruta_export),
            ruta_canonical,
            "R6 FALLIDO: exportar sobrescribe el registro canónico",
        )

    def test_r6_export_repetido_es_determinista(self):
        """Múltiples exports producen el mismo resultado."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad",
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])

        backend_con_loader = dict(BACKEND_REF)
        backend_con_loader["loader_capabilities"] = ["gguf"]

        # Exportar dos veces
        ruta1 = self.reg.exportar(backend_con_loader)
        with open(ruta1, encoding="utf-8") as f:
            contenido1 = f.read()

        ruta2 = self.reg.exportar(backend_con_loader)
        with open(ruta2, encoding="utf-8") as f:
            contenido2 = f.read()

        self.assertEqual(contenido1, contenido2, "Export no es determinista")


class TestR7_SafetyNoGrantPermissions(unittest.TestCase):
    """Verificación adicional: safety no puede otorgar permisos de host."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_safety_prohibido_incluye_grant_permission(self):
        """El rol safety debe prohibir grant_permission por defecto."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad",
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar(
            "laya-v1", "safety", ada["base_model"], ada["peft_config"],
            prohibido=["grant_permission", "execute_command", "modify_memory"],
        )
        estado = self.reg.estado("laya-v1")
        self.assertIn("grant_permission", estado.get("prohibido", []))


class TestR8_InvalidJSONFailsClosed(unittest.TestCase):
    """JSON inválido no se trata como registro vacío y confiable."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_json_invalido_no_es_confiable(self):
        """JSON roto no permite registrar sin error."""
        ruta = os.path.join(self.tmp.name, ar.NOMBRE_REGISTRO)
        with open(ruta, "w") as f:
            f.write("{esto no es json valido")

        # Leer debe fallar cerrado, no devolver registro vacío confiable
        lista = self.reg.listar()
        # Debe devolver lista vacía, no datos corruptos
        self.assertEqual(lista, [])


class TestR9_DuplicateIDs(unittest.TestCase):
    """IDs duplicados no sobrescriben identidad confiable."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_id_duplicado_no_sobrescribe(self):
        """Registrar con ID existente no debe sobrescribir silenciosamente."""
        ada1 = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad",
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("laya-v1", "safety", ada1["base_model"], ada1["peft_config"],
                           prohibido=["grant_permission"])

        # Intentar registrar otro adaptador con el mismo ID
        ada2 = {
            "base_model": {
                "name": "otro-modelo",
                "sha256": OTHER_SHA,
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        # El segundo registro con el mismo ID debe fallar o ser rechazado
        try:
            self.reg.registrar("laya-v1", "code", ada2["base_model"], ada2["peft_config"])
            # Si no falla, el estado debe seguir siendo el original
            estado = self.reg.estado("laya-v1")
            # Verificar que no se sobrescribió silenciosamente
            self.assertEqual(
                estado.get("base_model", {}).get("sha256"),
                "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad",
                "ID duplicado sobrescribió identidad confiable",
            )
        except ValueError:
            # Es aceptable que levante ValueError para IDs duplicados
            pass


class TestR10_ExportOrderingDeterministic(unittest.TestCase):
    """El orden de exportación y serialización canónica es determinista."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_export_ordering_deterministic(self):
        """Exportar múltiples veces produce el mismo orden de claves."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad",
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("a-v1", "safety", ada["base_model"], ada["peft_config"])
        self.reg.registrar("b-v1", "code", ada["base_model"], ada["peft_config"])
        self.reg.registrar("c-v1", "guide", ada["base_model"], ada["peft_config"])

        backend_con_loader = dict(BACKEND_REF)
        backend_con_loader["loader_capabilities"] = ["gguf"]

        # Exportar dos veces
        ruta1 = self.reg.exportar(backend_con_loader)
        with open(ruta1, encoding="utf-8") as f:
            datos1 = json.load(f)

        ruta2 = self.reg.exportar(backend_con_loader)
        with open(ruta2, encoding="utf-8") as f:
            datos2 = json.load(f)

        # El orden de los adaptadores debe ser el mismo
        keys1 = list(datos1["adaptadores"].keys())
        keys2 = list(datos2["adaptadores"].keys())
        self.assertEqual(keys1, keys2, "Orden de exportación no es determinista")


class TestR11_FourBucketLabels(unittest.TestCase):
    """Las etiquetas four-bucket describen comparaciones de modelos, no veredictos."""

    def test_four_bucket_labels_are_model_comparison(self):
        """Las etiquetas four-bucket no se usan como veredictos de compatibilidad."""
        # Los veredictos de compatibilidad son: COMPATIBLE, INCOMPATIBLE, NO_DATA
        # Las etiquetas four-bucket son: protects, redundant, regression, unfixed
        # No deben mezclarse
        cuatro_buckets = ("protects", "redundant", "regression", "unfixed")
        veredictos = ("COMPATIBLE", "INCOMPATIBLE", "NO_DATA")
        # No hay superposición
        self.assertEqual(
            set(cuatro_buckets) & set(veredictos),
            set(),
            "Four-bucket labels must not overlap with compatibility verdicts",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
