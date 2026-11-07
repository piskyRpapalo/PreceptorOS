# Insertor anclado y carril de ayuda (decreto del Soberano)

## LA PUERTA ÚNICA DE PREGUNTAS

- El insertor de texto del chat se **ANCLA a la base de la app, siempre visible** desde cualquier panel: una sola puerta de preguntas, desde donde sea.
- **RUTA DETERMINÍSTICA POR TAGS**: preguntar desde cualquier panel rutea con un tag (@lab, @mando, ...) hacia el chatbot, y el tag genera un **CONJUNTO DE INFO BASE** del panel activo para que el cerebro designado ofrezca ayuda contextual. Tag desconocido → fallback honesto, jamás adivinado (fail-closed, NO_DATA con causa).
- **CARRIL DE AYUDA SEPARADO**: la ayuda NO entra en el historial principal de talk. Carril propio, **efímero por defecto**. Ley del Cuaderno: capturado no es consentido; salvar solo a voluntad explícita.
- **CEREBRO DESIGNADO por tag**: ayuda → mini orquestador (rápido); conversación profunda → hexelion:latest con citas verificadas. La flechita de modelos muestra siempre quién responde.
- **LORA ESPECIALIZADO (fase 2, no bloquea la fase 1)**: las preguntas de ayuda medidas SON el corpus de entrenamiento; el LoRA se entrena cuando haya datos medidos, no antes. La fábrica se alimenta a sí misma. Precedente de la casa: los adaptadores Laya publicados con .sha256.

## REPARTO DE CARRILES

- La CARA (posición, estilo del insertor, visibilidad) = plan de Claude (R-ESTILO-ÚNICO, modo plan).
- La FUNCIÓN (rutas por tag, conjunto base medido, carril separado, cerebro designado) = cirugía de codex, modelo barato, tras el Lab V2. Estética cero: la pinta Claude sobre el mismo contrato.

Agent: preceptor-orquestador-github · Model: GLM (Vibe) · Run: NO_DATA