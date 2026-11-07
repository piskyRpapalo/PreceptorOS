# Lab real del rack desde la app

## Contrato

Al abrir el panel Lab, la app consulta una ruta local declarada. El servidor solo consulta la interfaz fija del laboratorio local, exige la autorización local existente, limita la lectura a 16 KiB, requiere HTTP 200 y `text/html`, y no sigue redirecciones. La interfaz muestra el enlace únicamente tras esa medida. En cualquier otro resultado muestra `NO_DATA` con causa y oculta el enlace.

No se consulta al iniciar la app ni se cargan iframes. La petición de comprobación es del mismo origen; la navegación al enlace local solo ocurre cuando la persona lo abre.

## Evidencia de implementación

- Panel: `interface/app.html`, ids `lab-rack-estado` y `lab-rack-enlace`.
- Carga diferida: `interface/app.js`, función `cargarLabRack`, llamada solo desde `mostrar()` al entrar en `lab`.
- Verificación local: `GET /api/lab-rack` en `bin/preceptoros-pwa`.
- Sabotajes: origen remoto denegado sin socket, timeout convertido a `NO_DATA`, redirección rechazada, contrato HTML medido antes de mostrar el enlace.

## Medida de referencia

El rack local respondió HTTP 200 con `text/html` en el puerto declarado por la implementación. La respuesta no se guarda ni se sirve desde caché.
