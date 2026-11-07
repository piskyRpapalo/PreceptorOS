# Plan de accesibilidad completo (decreto: una vez la app dada por buena)

> Base legal: EN 301 549 (canon de estética ya nombrado), contraste A11Y medido como en la web, cero telemetría.

## Joyas medidas en la casa

- Botones de 44 px táctiles (web, 13-oct) · zoom de pellizco/rueda (#58).
- Reduced-motion nativo: sting, transición, gusano. Ninguna animación obligatoria.
- Doctrina sin teclado: voz + joystick (ideas14oct); audio SIEMPRE voluntario, nunca suena solo.
- 8 lenguas (textos_lenguas) · formas infantiles (#64) · lenguaje llano con NO_DATA honesto.
- Color nunca solo: siempre con texto y sentido (ley Acho) · tabla semántica (hue/flujo/pulso/escala/feedback) · glifo semántico accesible.
- La voz del ecosistema: FM del sting (220 Hz del canon, 110 Hz de la vozDe, tensión dirimida) con envolvente A11Y y settle-motion (joya akella firmada).
- role="status" ya medido en app.html.
- accesibilidad-doctrina existe en web como propuesta (cimiento, draft): heredar a la app.

## NO_DATA a medir antes del plan

Cobertura ARIA de los 9 paneles · orden de foco al cambiar de pestaña · contraste medido de app.css · prueba real con lector de pantalla.

Agent: preceptor-orquestador-github · Model: GLM (Vibe) · Run: NO_DATA