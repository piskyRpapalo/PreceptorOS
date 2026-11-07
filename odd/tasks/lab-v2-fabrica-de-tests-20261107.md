# Lab V2 · la fábrica de tests nativa (decreto §62)

> El Lab pasa de «canales recientes» a la fábrica visible: experimentos, telemetría de agentes, reportes de estado y enlaces entre paneles.

Concepto medido: «agentic software factory» (Sonar, 2-nov-2026) y el marco loop/harness/fábrica de Osmani. La casa ya es una fábrica luz: comisiones = cola, cerca = vallas, CI + sabotajes = análisis independiente, FIRMO = puerta humana jamás delegada. El Lab es su andon.

## Comisión (para el preceptor que la tome)

1) MIDE primero qué consume hoy el Lab y qué señales medibles existen (harness, timers del rack, recibos públicos, commits, CI). Sin señal medible, nada se pinta.
2) EXPERIMENTOS: lista de títulos que el Soberano nombra (el objetivo es suyo, independiente del flujo de agentes).
3) TELEMETRÍA DE AGENTES: iconos encendido/apagado por agente, SOLO de fuentes medidas; sin señal = NO_DATA con causa; edad del dato visible.
4) REPORTE DE ESTADO: icono por experimento que despliega «últimas novedades» en ventana CERRABLE de ≤100 caracteres: cómo va el objetivo. Solo hechos medidos (último recibo/commit/CI), jamás inferido.
5) ENLACES ENTRE PANELES: Lab↔Hablar (preguntar a Hexelion del experimento), Lab↔Modelos, Lab↔Web, Lab↔Cuaderno.
6) Ley: fail-closed; sello sube; tests + sabotajes (sin red, señal mentirosa, reporte >100 caracteres, ventana que no cierra); rama desde main, PR draft; si se apila: etiqueta STACKED + base declarada.

## Contrato fábrica/1 (propuesto)

`{ id, título, estado, novedades ≤100 chars, agentes[] con encendido/apagado, edad del dato }`

## META de la Mesa

LAB-1 censo y contrato · LAB-2 la cara (este doc) · LAB-3 enlace vivo harness→app · LAB-4 ciclo cerrado (F2: hexelion redacta sus propios reportes).

Agent: preceptor-orquestador-github · Model: GLM (Vibe) · Run: NO_DATA