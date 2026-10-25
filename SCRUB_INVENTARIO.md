# Recibo de inventario y scrub del árbol PreceptorOS

Base medida: `02e7673` (`main` remoto), 540 archivos rastreados. El recuento distingue el valor A y el valor B; los valores nunca se copian a este documento. El barrido se hizo sin distinguir mayúsculas.

## Inventario de contenido por fichero

El valor A tuvo **0 coincidencias** en contenido y nombres de ruta. El valor B tuvo **245 coincidencias de contenido en 63 ficheros y 232 líneas**; otras **8 coincidencias** estaban en nombres de ruta. Tabla completa del contenido:

| Fichero de base (segmento privado sustituido por marcador) | Líneas base | Ocurrencias de contenido |
|---|---:|---:|
| `.gitignore` | 54–55, 58, 60 | 4 |
| `ASSETS.md` | 31, 37, 46 | 3 |
| `CHANGELOG.md` | 70–73, 93 | 7 |
| `CIERRE_M3.md` | 83, 206, 273 | 3 |
| `EXCEPCIONES.md` | 22 | 1 |
| `El_Temple.md` | 3, 14, 27 | 3 |
| `LORE.md` | 36, 98 | 2 |
| `MANIFIESTO.md` | 18 | 1 |
| `MARCA.md` | 76 | 1 |
| `README.md` | 179–180 | 3 |
| `RELEASE_v1.0.md` | 1, 3, 10, 25–27 | 6 |
| `RELEASE_v1.1.md` | 13, 20, 30–33 | 7 |
| `SECURITY.md` | 66, 164 | 2 |
| `TECHNICAL.md` | 200 | 1 |
| `<PRIVADO_2>.py` | 2, 5, 13, 18, 32 | 6 |
| `bin/crear-acceso-directo-android` | 25, 32 | 2 |
| `bin/instalar-android` | 49–50, 54 | 3 |
| `bin/instalar-pc` | 23 | 1 |
| `bin/preceptoros-puente` | 48–49 | 2 |
| `bin/preceptoros-pwa` | 65–66 | 2 |
| `bin/preceptoros-servicio` | 27, 32, 35, 45, 61, 65, 83, 95 | 8 |
| `bin/pruebas` | 53, 55 | 2 |
| `cara.py` | 39, 442–443, 508, 647, 649, 936 | 7 |
| `casa.py` | 8, 31 | 2 |
| `compass.py` | 785 | 1 |
| `contexto_seguro.md` | 38 | 1 |
| `conversacion.py` | 156, 225, 593 | 4 |
| `corredor.py` | 2 | 1 |
| `descarga.py` | 30, 174–179 | 7 |
| `docs/COMPASS.md` | 194 | 1 |
| `entorno.py` | 39, 61 | 2 |
| `fuga.py` | 42–43, 200, 882 | 4 |
| `herramientas/medir_tokens.py` | 11, 25, 74 | 3 |
| `importar.py` | 471 | 1 |
| `interface/dashboard.js` | 1744, 1748 | 2 |
| `interface/sw.js` | 30 | 1 |
| `interprete.py` | 3 | 1 |
| `laminas/LEEME.md` | 13 | 1 |
| `laminas/recortar.py` | 144 | 1 |
| `manifest.py` | 199 | 1 |
| `memory.py` | 1364 | 1 |
| `mente/misiones/ESPEC_CAHIER.md` | 141, 190 | 2 |
| `preceptoros.py` | 51 | 1 |
| `pyproject.toml` | 41 | 1 |
| `silencio.py` | 16, 19 | 2 |
| `test_app_una_pestana.py` | 80 | 1 |
| `test_cara.py` | 58, 62, 195, 364–365, 586, 773 | 8 |
| `test_compass.py` | 38 | 2 |
| `test_conversacion.py` | 355, 404, 473, 475, 488–489, 500, 502, 517, 520, 537, 539, 554, 560–561, 563–564, 602, 651, 655, 661, 674–675, 677, 692, 699, 708, 713, 731, 733, 773, 775 | 32 |
| `test_entorno.py` | 33, 38, 56, 74, 82, 94, 150, 157, 163 | 9 |
| `test_fuga.py` | 19, 42–43, 882, 933 | 5 |
| `test_idioma.py` | 6, 12, 54, 69, 76, 79–80, 105, 345, 361, 402 | 11 |
| `test_interprete.py` | 69, 72, 82–83, 85–86, 104–105 | 11 |
| `test_leitmotivs.py` | 12, 46, 52 | 3 |
| `test_path.py` | 216–217, 224–225 | 4 |
| `test_puente.py` | 46–47, 180 | 3 |
| `test_pwa.py` | 550, 1085 | 2 |
| `test_restaurar.py` | 17, 42, 48, 53, 58, 67, 76, 81, 85 | 9 |
| `test_silencio.py` | 105 | 1 |
| `test_tono.py` | 14, 48 | 2 |
| `test_voz_cyber.py` | 2, 19, 70, 82, 93, 104, 109, 114, 131, 195–196, 204, 206, 231 | 16 |
| `tono.py` | 14, 29 | 2 |
| `voz.py` | 2, 29–30, 51, 184, 225 | 6 |

## Coincidencias en nombres de ruta

Las ocho coincidencias de ruta correspondían a un módulo de compatibilidad, cuatro symlinks de `bin/` y tres assets. Los symlinks eran alias directos, no implementaciones:

| Ruta de base | Conteo de ruta | Bytes del symlink / tipo | Destino medido | Decisión |
|---|---:|---:|---|---|
| `<PRIVADO_2>.py` | 1 | módulo Python | reenviaba al módulo canónico | eliminado; callers pasan al módulo canónico |
| `bin/<PRIVADO_2>-puente` | 1 | 18 B | `preceptoros-puente` | eliminado; alias duplicado |
| `bin/<PRIVADO_2>-pwa` | 1 | 15 B | `preceptoros-pwa` | eliminado; alias duplicado |
| `bin/<PRIVADO_2>-servicio` | 1 | 20 B | `preceptoros-servicio` | eliminado; alias duplicado |
| `bin/<PRIVADO_2>-servicio-pc` | 1 | 23 B | `preceptoros-servicio-pc` | eliminado; alias duplicado |
| `assets/<PRIVADO_2>-talks.png` | 1 | binario | asset renombrado | renombrado a prefijo canónico |
| `assets/<PRIVADO_2>-up.png` | 1 | binario | asset renombrado | renombrado a prefijo canónico |
| `assets/titulo-<PRIVADO_2>.png` | 1 | binario | asset renombrado | renombrado a prefijo canónico |

El campo de caché del worker pasó a `preceptoros-armazon-v101`. La clave `/app.js?v=4` se conserva alineada en el precache y en `interface/app.html`; la prueba lee ambos lugares. El inventario `L3_P1_INVENTARIO.md` tuvo **0 coincidencias** de ambos valores en la base, así que no se cambió; se conservan su recuento de siete timers y sus causas.

## Dependencias medidas

| Consumidor | Medición | Acción de este PR | Seguimiento rack |
|---|---|---|---|
| Tests y documentación del repo | Subprocesos, imports, ejemplos de CLI, configuración de empaquetado y pruebas de rutas usaban el módulo de compatibilidad; `bin/preceptoros-servicio` aceptaba ambos patrones de proceso. | Imports y ejemplos quedan en el punto de entrada canónico; se elimina el módulo y se simplifica el patrón del servicio. | Ninguna escritura al rack. |
| Unidades de aplicación locales | `user config/preceptoros-pwa.service:9-11` documenta los dos puntos de entrada; `user config/10-motor-vulkan.conf:3-8,14` cita el nombre anterior de la unidad y del override. | No se editan unidades locales. | La mano del Soberano debe revisar esos comentarios/rutas tras el merge. |
| Permisos de unidades del rack | `afinador.service:16`, `curador.service:15-16`, `director.service:23-25`, `guardian.service:19` contienen rutas del directorio de datos anterior. | No se editan unidades. | Revisar permisos y migración manual de datos después del merge. |
| Timers y scripts privados del rack | La configuración de usuario tiene un service/timer y un symlink de activación; hay dos plantillas de despliegue. La configuración de sistema tiene un service/timer, un drop-in y un symlink. `<private-ref>/consejo.py` `sha256=NO_DATA scope_not_signed`:2,4-7,34,77 y su prueba mantienen referencias privadas; `<private-ref>/reconcilia_contratos.py` `sha256=NO_DATA scope_not_signed`:10 consulta una ruta API privada. | No se toca el rack ni se copia ese identificador al PR. | La mano del Soberano actualiza esas unidades y scripts después del merge. |
| Instalación y permisos del rack | `<private-ref>/instalar-ganchos` `sha256=NO_DATA scope_not_signed`:7,13 y `<private-ref>/renombrar-empaquetado.py` `sha256=NO_DATA scope_not_signed`:2,10,16,34-41,46,50-64,99,102,105,112,116 conservan rutas/identificadores. Unidades de usuario: `afinador.service:16`, `curador.service:15-16`, `director.service:23-25`, `guardian.service:19`; la unidad PWA y el drop-in local documentan entradas anteriores en líneas citadas arriba. | Sin cambios fuera de este repo. | Revisar permisos de directorios y referencias una vez fusionado; no ejecutar antes. |

## Guardián y CI

`test_privacidad_arbol.py` lee una lista JSON desde `PRECEPTOROS_PRIVATE_SCAN_TOKENS`, revisa nombres y bytes de los archivos rastreados y no ignorados, y nunca imprime los valores. Sin la variable, marca el caso `NO_DATA` y lo salta. El rojo local se ejecutó con lista ad hoc; después del scrub pasó con cero coincidencias.

Para activar el gate en GitHub Actions, el Soberano debe crear en **Settings → Secrets and variables → Actions** el secreto de repositorio `PRECEPTOROS_PRIVATE_SCAN_TOKENS` con una lista JSON de los dos valores. El workflow solo inyecta ese secreto al entorno; el secreto no entra al árbol.

## Historial

El historial no se reescribe. Los objetos anteriores quedan cerrados con causa; este cambio solo limpia el árbol vigente.
