#!/usr/bin/env python3
"""
API Guia - Ecosistema Soberano
Endpoint: /api/guia
Modelo: el que diga MODELO, y solo ese. Hoy `preceptor-charla-web:v2`:
Mistral 7B Instruct v0.3 Q4_K_M con un adaptador LoRA de 27 MB (el de la charla
de la web). Esta linea decia «oficial-inventario:latest (Qwen3.8-27B-Uncensored)»
mientras la constante decia otra cosa: el docstring mentia. Y el Oficial ya no
se monta sobre el modelo sin censura -- ver `mente/decisiones` y capa1.py.

Entre el modelo y quien llama esta `capa1.py`: guardian determinista a la
entrada y a la salida (D38), y la salida va acotada por esquema con el
`format` de Ollama (D39): el modelo no puede devolver otras claves.
"""

import json
import re
from typing import Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

import capa1

app = FastAPI(
    title="API Guia - Ecosistema Soberano",
    description="Agente de inventario · capa 1 determinista en la frontera",
    version="1.0.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GuiaRequest(BaseModel):
    pregunta: str
    contexto: Optional[str] = None
    incluir_thinking: bool = False


class GuiaResponse(BaseModel):
    status: str
    comando: str
    explicacion: str
    servicio_afectado: str
    riesgo: str
    thinking_trace: Optional[str] = None
    timestamp: str
    modelo: str


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_TAGS = "http://127.0.0.1:11434/api/tags"
MODELO = "preceptor-charla-web:v2"

SYSTEM_PROMPT = """Eres el Oficial de Inventario del Ecosistema Soberano.
Responde SIEMPRE en JSON estricto, sin markdown, sin envoltorios, sin bloques de codigo.
Devuelve SOLO el JSON plano, nada mas.
Si no sabes un dato real, usa status='pending' o status='error', nunca inventes.
Schema obligatorio (exactamente estas claves):
{
  "status": "ok o error o pending",
  "comando": "comando bash exacto o vacio",
  "explicacion": "razonamiento tecnico breve",
  "servicio_afectado": "nombre del servicio o none",
  "riesgo": "none o low o medium o high o critical",
  "thinking_trace": "traza de razonamiento solo si fue complejo"
}"""

# La misma forma, como esquema: alimenta el `format` de Ollama (decoding acotado)
# y es lo que se valida al volver. Un fichero de verdad, dos consumidores.
ESQUEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["ok", "error", "pending"]},
        "comando": {"type": "string"},
        "explicacion": {"type": "string"},
        "servicio_afectado": {"type": "string"},
        "riesgo": {"type": "string", "enum": ["none", "low", "medium", "high", "critical"]},
        "thinking_trace": {"type": "string"},
    },
    "required": ["status", "comando", "explicacion", "servicio_afectado", "riesgo"],
}


def limpiar_respuesta(content: str) -> str:
    """Limpia residuos de , markdown y texto envolvente."""
    if not content:
        return ""
    # Eliminar bloques ...
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
    # Eliminar bloques de codigo markdown
    content = re.sub(r"```(?:json)?", "", content)
    content = content.replace("```", "")
    # Eliminar texto antes del primer { y despues del ultimo }
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        content = match.group(0)
    return content.strip()


@app.get("/")
def root():
    return {
        "servicio": "API Guia - Ecosistema Soberano",
        "modelo": MODELO,
        "endpoint": "/api/guia",
        "status": "activo",
        "version": "1.0.1",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/guia", response_model=GuiaResponse)
async def guia_endpoint(request: GuiaRequest):
    try:
        prompt = request.pregunta
        if request.contexto:
            prompt = f"CONTEXTO:\n{request.contexto}\n\nPREGUNTA:\n{request.pregunta}"

        cortes = capa1.inspecciona_entrada(request.pregunta + " " + (request.contexto or ""))
        if cortes:
            return GuiaResponse(**capa1.retirado(cortes, "entrada"), modelo=MODELO,
                                timestamp=datetime.now().isoformat())

        payload = {
            "model": MODELO,
            "format": ESQUEMA,
            "system": SYSTEM_PROMPT,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 2048
            }
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        response.raise_for_status()
        result = response.json()
        
        # IMPORTANTE: Qwen3 con template de thinking devuelve el contenido en 'thinking'
        content = result.get("response", "") or result.get("thinking", "") or ""
        
        if not content:
            raise ValueError("Respuesta vacia del modelo")

        # Limpiar y parsear
        content_limpio = limpiar_respuesta(content)

        try:
            guia_json = json.loads(content_limpio)
        except json.JSONDecodeError as e:
            # Intentar extraer JSON con regex
            match = re.search(r'\{[^{}]*"status"[^{}]*\}', content_limpio, re.DOTALL)
            if match:
                try:
                    guia_json = json.loads(match.group())
                except json.JSONDecodeError:
                    guia_json = None
            else:
                guia_json = None

            if guia_json is None:
                guia_json = {
                    "status": "error",
                    "comando": "parse_error",
                    "explicacion": f"JSON invalido: {str(e)}. Contenido: {content[:150]}",
                    "servicio_afectado": "none",
                    "riesgo": "medium",
                    "thinking_trace": ""
                }

        cortes = capa1.inspecciona_comando(str(guia_json.get("comando", "")))
        if cortes:
            guia_json = capa1.retirado(cortes, "salida")

        return GuiaResponse(
            status=guia_json.get("status", "error"),
            comando=guia_json.get("comando", ""),
            explicacion=guia_json.get("explicacion", ""),
            servicio_afectado=guia_json.get("servicio_afectado", "none"),
            riesgo=guia_json.get("riesgo", "medium"),
            thinking_trace=guia_json.get("thinking_trace", "") if request.incluir_thinking else None,
            timestamp=datetime.now().isoformat(),
            modelo=MODELO
        )

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Error Ollama: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@app.get("/health")
def health_check():
    try:
        response = requests.get(OLLAMA_TAGS, timeout=5)
        ollama_ok = response.status_code == 200
        models = response.json().get("models", []) if ollama_ok else []
        nombres = [m.get("name", "") for m in models]
        # Pertenencia REAL y nada mas. Antes habia un `or` con
        # `oficial-inventario` que aprobaba el chequeo aunque MODELO no
        # estuviese: el 2026-09-19 devolvia `modelo_disponible: true` para
        # `qwen38-limpio:latest`, que no existe, y listaba los 34 modelos sin
        # el al lado. El /api/generate habria dado 404.
        modelo_disponible = MODELO in nombres
        return {
            "status": "healthy" if modelo_disponible else "degraded",
            "ollama": "ok" if ollama_ok else "error",
            "modelo": MODELO,
            "modelo_disponible": modelo_disponible,
            "modelos_instalados": nombres,  # /api/tags lista lo instalado, no lo cargado
            "version": "1.0.1",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9001, log_level="info")
