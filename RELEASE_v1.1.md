# v1.1 · PreceptorOS

**Fecha:** 2026-08-25 · **Anterior:** [v1.0.0](RELEASE_v1.0.md)

Esta versión establece PreceptorOS, sus rutas canónicas y mejoras de velocidad.
La aplicación usa `~/.preceptoros/` para datos personales y no adopta rutas
anteriores. Si aún conservas datos locales en otra carpeta, no la borres:
migra su contenido manualmente antes de iniciar esta versión.

## Cambios

- Búsqueda de texto completo sobre recuerdos con FTS5, sin dependencias nuevas.
- Caminos de aprendizaje disponibles sin modelo ni red.
- Latencia por turno medida; lo que no se midió conserva su causa.
- Los alias, rutas y etiquetas retirados ya no forman parte del árbol público.

El historial Git no se reescribe. Las referencias históricas quedan cerradas;
esta guía describe únicamente el árbol vigente.
