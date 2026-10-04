# EXCEPCIONES

Registro de los pragmas que apagan una guardia automática. Una fila por pragma.

Existe porque una excepción sin registro es una excepción que nadie vuelve a
mirar: la guardia pasa a verde, el motivo se queda en la cabeza de quien la
escribió, y dentro de un año la línea parece parte del diseño. Aquí el motivo
está escrito, fechado y al lado del siguiente, que es la única forma de notar
que van siendo demasiados.

**Este fichero vive en la raíz, no en `docs/`.** `docs/` está en `.gitignore`
(línea 7) por un motivo que está escrito dentro y es correcto — los entregables
internos llevan léxico propio y no entran en la historia de un repo público.
Pero eso significa que un fichero puesto ahí no entraría en git: `git ls-files
docs/` da 0. Un registro de excepciones que no está versionado no es un
registro. El `.gitignore` no se toca; el fichero se pone donde sí se guarda.

## Pragmas vigentes

| Fichero | Línea | Pragma | Motivo | Fecha |
|---|---|---|---|---|
| `voz.py` | 43 | `guardia:permitir` | `/opt/homebrew/share/espeak-ng-data` es un prefijo de sistema de macOS, no la carpeta personal de nadie. La guardia de higiene marca rutas absolutas porque el repo es público y una ruta bajo el home describe a quien compiló Piper a mano — exactamente lo que `guardrails` redacta al exportar. Un prefijo de gestor de paquetes es igual en cualquier máquina, así que no describe a nadie. Quien tenga espeak bajo su home lo declara por entorno (`AURELIUS_ESPEAK_DATA`), que es la vía que existe para eso. | 2026-08-16 |

Total: **1**.

## Reglas

- **Una fila o no hay pragma.** Un `guardia:` sin fila aquí es un fallo de la
  misma clase que el que la guardia detecta: se apagó una comprobación y no
  quedó constancia.
- **El motivo dice por qué esta línea concreta es segura**, no por qué la
  guardia es molesta. «La guardia da un falso positivo» no es un motivo: es la
  conclusión. El motivo es lo que hace que sea falso.
- **La fecha es la del commit que introdujo el pragma**, no la de esta anotación.
- **El número de línea se mueve.** Es una referencia de lectura, no la
  identidad de la fila: la identidad es fichero + pragma + motivo. Para
  recalcularlas:

      git grep -niE "guardia:[a-z]+" -- .

  Si esa orden devuelve un pragma que no está en la tabla, o la tabla tiene uno
  que la orden no devuelve, la tabla está mal y se arregla la tabla.

## Excepciones de promesa (capacidades firmadas)

Otra clase de excepción: no apaga una guardia del código, **acota una promesa pública**. Se
registra aquí para que la promesa y su excepción se lean juntas.

### Voz en web y app por motor de terceros · PENDIENTE (frase de estado del Soberano, sin firma criptográfica)

- **Firma:** Soberano, frase espontánea en sesión («acepto la voz en app y web, con nube de tercero declarada y killswitch»). DECLARADO: no es firma ed25519.
- **Alcance:** reconocimiento de habla **por pulsación**, revocable, en `voz-web` y `voz-app`. Nunca escucha continua.
- **Riesgo:** cuando el aparato no puede reconocer en local, el motor del navegador puede enviar el audio a un tercero (en Chrome, Google) que PreceptorOS no controla.
- **Mitigación (ya en `preceptoros-web/public/assets/voice.js` desde el 2026-09-05):** primero en local (`processLocally`), sin preguntar, porque nada sale. La nube solo después de aceptar el trato dicho entero. El permiso dura **una sesión** (`sessionStorage`).
- **Pendiente para cerrarla** (sin esto la excepción sigue PROPUESTA en esas partes):
  - registro del sí con alcance, TTL, hash y fecha;
  - indicador **sonoro** de micrófono abierto y cerrado;
  - killswitch que **verifica** que el reconocimiento terminó, o declara el fallo;
  - sabotajes en rojo: micrófono sin firma, killswitch que afirma sin verificar, página que promete «cero nube» usando el motor del tercero.
- **Promesa reformulada:** «La página no hace peticiones externas al cargar. El micrófono web, si lo firmas, puede usar el motor del navegador y enviar audio a un tercero para transcribir. PreceptorOS no guarda tu audio salvo el texto que tú firmes.»
- **Caducidad:** la del permiso, que es la sesión. La excepción se revisa si cambia el motor del navegador.
