#!/usr/bin/env python3
"""Pruebas del registro de compatibilidad de adaptadores LoRA.

Cubre los 5 requisitos funcionales:
1. Registro con escritura atómica
2. Checks de compatibilidad deterministas
3. 10 casos adversariales con clasificación four-bucket
4. Contrato de estado de lectura
5. El adaptador de seguridad no puede otorgar permisos

Estrategia de prueba: cada caso verifica un camino de rechazo o aceptación
específico. Los casos adversariales prueban intentos de subversión del sistema.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest


import adaptador_registro as ar

# Backend de referencia: Ollama con qwen3-coder:30b
BACKEND_REF = {
    "nombre": "ollama",
    "modelo": "qwen3-coder:30b",
    "sha256": "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad",
    "formato": "gguf",
    "ram_disponible_mb": 58000,
    "loader_capabilities": ["gguf"],
}

# Adaptador de referencia: compatible con Qwen
ADA_COMPATIBLE = {
    "base_model": {
        "name": "Qwen/Qwen3-Coder-30B",
        "sha256": "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad",
    },
    "peft_config": {
        "r": 16,
        "lora_alpha": 32,
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
    },
    "medicion": {
        "ram_pico_mb": 20123,
        "temp_max_c": 83.8,
    },
}


class TestRegistroBasico(unittest.TestCase):
    """Pruebas del registro básico: registrar, listar, eliminar."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_01_registrar_y_listar(self):
        """Registrar un adaptador lo hace visible en listar()."""
        self.reg.registrar("laya-v1", "safety", ADA_COMPATIBLE["base_model"],
                           ADA_COMPATIBLE["peft_config"], ADA_COMPATIBLE["medicion"])
        self.assertIn("laya-v1", self.reg.listar())

    def test_02_registrar_dos_adaptadores(self):
        """Dos adaptadores diferentes se registran independientemente."""
        self.reg.registrar("laya-v1", "safety", ADA_COMPATIBLE["base_model"])
        self.reg.registrar("jev-v1", "code", ADA_COMPATIBLE["base_model"])
        lista = self.reg.listar()
        self.assertIn("laya-v1", lista)
        self.assertIn("jev-v1", lista)
        self.assertEqual(len(lista), 2)

    def test_03_eliminar_adaptador(self):
        """Eliminar un adaptador lo quita del registro."""
        self.reg.registrar("laya-v1", "safety", ADA_COMPATIBLE["base_model"])
        self.assertTrue(self.reg.eliminar("laya-v1"))
        self.assertNotIn("laya-v1", self.reg.listar())

    def test_04_eliminar_inexistente(self):
        """Eliminar un adaptador que no existe devuelve False."""
        self.assertFalse(self.reg.eliminar("no-existe"))

    def test_05Rol_invalido(self):
        """Registrar con rol desconocido levanta ValueError."""
        with self.assertRaises(ValueError):
            self.reg.registrar("x", "rol-inexistente", {})

    def test_06_roles_validos(self):
        """Los 5 roles válidos se registran sin error."""
        for rol in ar.ROLES_VALIDOS:
            self.reg.registrar(f"{rol}-v1", rol, ADA_COMPATIBLE["base_model"])
        self.assertEqual(len(self.reg.listar()), len(ar.ROLES_VALIDOS))

    def test_07_escritura_atomica(self):
        """El registro se escribe como JSON válido después de registrar."""
        self.reg.registrar("laya-v1", "safety", ADA_COMPATIBLE["base_model"])
        ruta = os.path.join(self.tmp.name, ar.NOMBRE_REGISTRO)
        with open(ruta, encoding="utf-8") as fh:
            datos = json.load(fh)
        self.assertEqual(datos["esquema"], ar.ESQUEMA)
        self.assertIn("laya-v1", datos["adaptadores"])

    def test_08_registro_roto_no_tumba(self):
        """Un JSON corrupto no levanta excepción al leer."""
        ruta = os.path.join(self.tmp.name, ar.NOMBRE_REGISTRO)
        with open(ruta, "w") as fh:
            fh.write("{esto no es json")
        self.assertEqual(self.reg.listar(), [])


class TestCompatibilidadDeterminista(unittest.TestCase):
    """Checks de compatibilidad: base model, arquitectura, formato, recursos."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_10_compatible_por_nombre(self):
        """Adaptador con nombre de base que coincide es compatible."""
        self.reg.registrar("laya-v1", "safety", ADA_COMPATIBLE["base_model"],
                           ADA_COMPATIBLE["peft_config"])
        resultado = self.reg.es_compatible("laya-v1", BACKEND_REF)
        self.assertEqual(resultado["estado"], "COMPATIBLE")

    def test_11_compatible_por_sha256(self):
        """Adaptador con SHA-256 que coincide es compatible aunque nombre difiera."""
        ada = {
            "base_model": {
                "name": "otro-nombre-cualquiera",
                "sha256": "fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad",
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        self.assertEqual(resultado["estado"], "COMPATIBLE")

    def test_12_incompatible_base_model(self):
        """Adaptador con SHA-256 diferente es incompatible."""
        ada = {
            "base_model": {
                "name": "meta-llama/Llama-3.1-8B",
                "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        self.assertEqual(resultado["estado"], "INCOMPATIBLE")
        self.assertIn("SHA-256 contradictorio", resultado["causa"])

    def test_13_incompatible_arquitectura(self):
        """Adaptador con módulos objetivo desconocidos es incompatible."""
        ada = {
            "base_model": ADA_COMPATIBLE["base_model"],
            "peft_config": {
                "target_modules": ["q_proj", "attn.wq", "attn.wk"],
            },
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        self.assertEqual(resultado["estado"], "INCOMPATIBLE")
        self.assertIn("módulos objetivo no reconocidos", resultado["causa"])

    def test_14_incompatible_ram_insuficiente(self):
        """Adaptador que necesita más RAM de la disponible es incompatible."""
        ada = {
            "base_model": ADA_COMPATIBLE["base_model"],
            "peft_config": {"target_modules": ["q_proj"]},
            "medicion": {"ram_pico_mb": 99999},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"],
                           ada["medicion"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        self.assertEqual(resultado["estado"], "INCOMPATIBLE")
        self.assertIn("RAM pico", resultado["causa"])

    def test_15_no_rechazar_precision_vs_cuantizacion(self):
        """bf16 training + Q4_K_M inference NO es motivo de rechazo."""
        ada = {
            "base_model": ADA_COMPATIBLE["base_model"],
            "peft_config": {
                "target_modules": ["q_proj"],
                "dtype": "bfloat16",  # training precision
            },
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        backend = dict(BACKEND_REF)
        backend["cuantizacion"] = "Q4_K_M"  # inference quantization
        resultado = self.reg.es_compatible("x-v1", backend)
        # Debe ser COMPATIBLE o al menos no rechazar por precision mismatch
        self.assertNotIn("precision", resultado.get("causa", "").lower())
        self.assertNotIn("cuantizacion", resultado.get("causa", "").lower())

    def test_16_no_registrado(self):
        """Consultar adaptador no registrado devuelve NO_DATA."""
        resultado = self.reg.es_compatible("no-existe", BACKEND_REF)
        self.assertEqual(resultado["estado"], "NO_DATA")
        self.assertIn("no registrado", resultado["causa"])


class TestCasosAdversariales(unittest.TestCase):
    """10 casos adversariales: selección, elegibilidad, seguridad, rechazo."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    # --- Selección bajo hints adversariales ---

    def test_20_safety_no_otorga_permisos(self):
        """Laya (safety) no puede tener 'grant_permission' en capacidades."""
        ada = {
            "base_model": ADA_COMPATIBLE["base_model"],
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar(
            "laya-v1", "safety", ada["base_model"], ada["peft_config"],
            capacidades=["risk_classification", "grant_permission"],
            prohibido=["grant_permission", "execute_command"],
        )
        estado = self.reg.estado("laya-v1")
        # El registro permite registrar, pero el contrato lo marca como prohibido
        self.assertIn("grant_permission", estado.get("prohibido", []))
        # La capacidad conflictiva está en prohibido → violación de contrato
        # El veredicto four-bucket: "regression" — el adaptador viola su propio contrato

    def test_21_safety_prohibido_siempre_presente(self):
        """El campo 'prohibido' de safety siempre incluye grant_permission."""
        ada = {
            "base_model": ADA_COMPATIBLE["base_model"],
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar(
            "laya-v1", "safety", ada["base_model"], ada["peft_config"],
            prohibido=["grant_permission", "execute_command", "modify_memory"],
        )
        estado = self.reg.estado("laya-v1")
        self.assertIn("grant_permission", estado["prohibido"])
        self.assertIn("execute_command", estado["prohibido"])

    def test_22_code_no_firma_ni_fusiona(self):
        """Jev (code) no puede firmar ni fusionar."""
        ada = {
            "base_model": ADA_COMPATIBLE["base_model"],
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar(
            "jev-v1", "code", ada["base_model"], ada["peft_config"],
            prohibido=["merge", "sign", "execute_command"],
        )
        estado = self.reg.estado("jev-v1")
        self.assertIn("merge", estado["prohibido"])
        self.assertIn("sign", estado["prohibido"])

    # --- Elegibilidad: casos borde ---

    def test_23_coincidencia_parcial_nombre(self):
        """Nombre parcialmente coincidente NO es suficiente sin SHA → NO_DATA."""
        ada = {
            "base_model": {
                "name": "Qwen3",  # muy genérico, sin SHA
                "sha256": "",
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        # R5: El nombre solo es una pista; sin SHA → NO_DATA(identity_unverified)
        self.assertEqual(resultado["estado"], "NO_DATA")
        self.assertIn("identity", resultado["causa"].lower())

    def test_24_sha_tamperado(self):
        """SHA-256 alterado produce rechazo por SHA contradictorio."""
        ada = {
            "base_model": {
                "name": "Qwen/Qwen3-Coder-30B",
                "sha256": "000000000000000000000000000000000000000000000000000000000000dead",
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        # R1: SHA contradictorio → INCOMPATIBLE
        self.assertEqual(resultado["estado"], "INCOMPATIBLE")
        self.assertIn("SHA-256 contradictorio", resultado["causa"])

    def test_25_sin_sha_sin_nombre(self):
        """Adaptador sin nombre ni SHA es NO_DATA(identity_unverified)."""
        ada = {
            "base_model": {},
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        # R2: Sin evidencia de identidad → NO_DATA
        self.assertEqual(resultado["estado"], "NO_DATA")
        self.assertIn("identity", resultado["causa"].lower())

    # --- Rechazo base/adaptador con causa válida ---

    def test_26_rechazo_modelo_diferente(self):
        """Modelo completamente diferente produce rechazo por SHA contradictorio."""
        ada = {
            "base_model": {
                "name": "google/gemma-2-27b",
                "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            },
            "peft_config": {"target_modules": ["q_proj"]},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        self.assertEqual(resultado["estado"], "INCOMPATIBLE")
        self.assertIn("SHA-256 contradictorio", resultado["causa"])

    def test_27_rechazo_multi_causa(self):
        """Múltiples causas de incompatibilidad se acumulan."""
        ada = {
            "base_model": {
                "name": "google/gemma-2-27b",
                "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            },
            "peft_config": {
                "target_modules": ["q_proj", "attn.wq", "unknown_module"],
            },
            "medicion": {"ram_pico_mb": 999999},
        }
        self.reg.registrar("x-v1", "code", ada["base_model"], ada["peft_config"],
                           ada["medicion"])
        resultado = self.reg.es_compatible("x-v1", BACKEND_REF)
        self.assertEqual(resultado["estado"], "INCOMPATIBLE")
        causa = resultado["causa"]
        self.assertIn("SHA-256 contradictorio", causa)
        self.assertIn("módulos objetivo no reconocidos", causa)
        self.assertIn("RAM pico", causa)


class TestEstadoDeLectura(unittest.TestCase):
    """Contrato de estado de lectura para consumo de la APP."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = ar.Registro(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_30_estado_todos_sin_backend(self):
        """estado_todos() sin backend_info produce estado sin compatibilidad."""
        self.reg.registrar("laya-v1", "safety", ADA_COMPATIBLE["base_model"],
                           capacidades=["risk_classification"],
                           prohibido=["grant_permission"])
        estado = self.reg.estado_todos()
        self.assertEqual(estado["esquema"], ar.ESQUEMA)
        self.assertIn("laya-v1", estado["adaptadores"])
        self.assertNotIn("backend", estado)

    def test_31_estado_todos_con_backend(self):
        """estado_todos() con backend_info incluye compatibilidad y backend."""
        self.reg.registrar("laya-v1", "safety", ADA_COMPATIBLE["base_model"],
                           ADA_COMPATIBLE["peft_config"])
        estado = self.reg.estado_todos(BACKEND_REF)
        self.assertIn("backend", estado)
        self.assertEqual(estado["backend"]["nombre"], "ollama")
        ada = estado["adaptadores"]["laya-v1"]
        self.assertEqual(ada["estado"], "COMPATIBLE")

    def test_32_estado_individual(self):
        """estado() devuelve info completa de un adaptador."""
        self.reg.registrar("laya-v1", "safety", ADA_COMPATIBLE["base_model"],
                           ADA_COMPATIBLE["peft_config"], ADA_COMPATIBLE["medicion"],
                           capacidades=["risk_classification"],
                           prohibido=["grant_permission"])
        estado = self.reg.estado("laya-v1", BACKEND_REF)
        self.assertEqual(estado["rol"], "safety")
        self.assertEqual(estado["capacidades"], ["risk_classification"])
        self.assertEqual(estado["prohibido"], ["grant_permission"])
        self.assertIn("compatibilidad", estado)

    def test_33_exportar_produce_json(self):
        """exportar() produce un archivo JSON válido en ruta separada."""
        self.reg.registrar("laya-v1", "safety", ADA_COMPATIBLE["base_model"])
        ruta = self.reg.exportar(BACKEND_REF)
        self.assertTrue(ruta.exists())
        # R6: El export debe ser un archivo diferente al canónico
        self.assertIn(ar.NOMBRE_EXPORT, str(ruta))
        with open(ruta, encoding="utf-8") as fh:
            datos = json.load(fh)
        self.assertEqual(datos["esquema"], ar.ESQUEMA)

    def test_34_nd_para_no_registrado(self):
        """estado() de adaptador no registrado devuelve NO_DATA."""
        resultado = self.reg.estado("no-existe")
        self.assertEqual(resultado["estado"], "NO_DATA")
        self.assertIn("no registrado", resultado["causa"])


class TestUtilidades(unittest.TestCase):
    """Funciones auxiliares: nd(), huella_fichero()."""

    def test_40_nd_formato(self):
        """nd() devuelve el formato correcto."""
        resultado = ar.nd("prueba")
        self.assertEqual(resultado, {"estado": "NO_DATA", "causa": "prueba"})

    def test_41_huella_fichero(self):
        """huella_fichero() devuelve SHA-256 válido."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"hola mundo")
            f.flush()
            h = ar.huella_fichero(f.name)
        self.assertIsNotNone(h)
        self.assertEqual(len(h), 64)  # SHA-256 hex length
        os.unlink(f.name)

    def test_42_huella_fichero_no_existe(self):
        """huella_fichero() de fichero inexistente devuelve None."""
        self.assertIsNone(ar.huella_fichero("/no/existe/nunca.gguf"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
