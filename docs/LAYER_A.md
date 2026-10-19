# LAYER A · 1 APP = 1 NODO · propuesta REQUIERE_FIRMA

Una instancia de PreceptorOS opera como un nodo local con su memoria, identidad y modelo/ruta locales. El modelo pequeño consume recibos y evidencia del LAB; no escribe leyes ni se evalúa a sí mismo.

| Poder | Ruta del APP | Función de frontera |
|---|---|---|
| Legislativo | `aiact_art14_game_policy.json` y contratos firmados | El carbono define ley, límites y condiciones; la IA solo propone. |
| Ejecutivo | `nodo_app.py`, `nodo_export.py`, `eleccion_tier2.py`, `aiact_art14_node_decide.py` | La puerta local verifica credenciales; exportación solo ocurre tras acción humana; el selector valida forma y la decisión produce una propuesta acotada. |
| Judicial | `decision_evento.py`, `canal_event.py`, esquemas de `data/` y arneses `test_*.py` | Validación determinista, evento completo o rechazo completo, y recibo con hash; no concede autoridad. |
| Entrada/salida | `oido.py`, `tono.py`, `herencia_web.py` | Adaptación local de señales y herencia de contenido. Ninguna ruta cambia leyes, firma ni el registro por sí sola. |

Rutas confirmadas por lectura de los archivos en el árbol remoto del APP el 2026-10-19: `nodo_app.py`, `nodo_export.py`, `eleccion_tier2.py`, `decision_evento.py`, `aiact_art14_node_decide.py`, `oido.py`, `tono.py` y `herencia_web.py`. La configuración física y los sensores live se consultan por la vía separada descrita en LAB; no se copian al payload del modelo.

Alcance: contrato y mapa de rutas. No habilita sincronización, telemetría, ejecución remota, entrenamiento de LoRA ni escritura en un registro compartido. Los LoRA esperan tráfico real y solo feedback firmado por el rack.
