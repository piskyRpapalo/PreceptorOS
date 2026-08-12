# Guardrails

Redacta claves, tokens, IPs privadas y rutas locales de un texto **antes** de que
salga de tu máquina hacia un modelo externo. Un fichero, un interruptor, sin
dependencias fuera de la librería estándar de Python.

## Qué hace

Recibe texto y devuelve dos cosas: el texto ya redactado y un contador de qué
clases apareció y cuántas veces.

```python
from guardrails import redactar_salida

texto, hallazgos = redactar_salida('export API_KEY=sk-live-9aB7cD5eF3gH1iJ2kL4')
# texto      -> 'export [REDACTED:API_KEY]'
# hallazgos  -> [{'policy': 'API_KEY', 'count': 1}]
```

El contador nunca lleva el texto encontrado: solo **clase y cantidad**. Es lo que
se puede enseñar en pantalla sin volver a exponer aquello que acabas de tapar.

### Políticas duras (Core) — siempre activas

| Policy | Qué tapa |
|---|---|
| `API_KEY` | Tokens de API por forma conocida (`sk-…`, `ghp_…`, `xox…`, `AKIA…`, `AIza…`) y por asignación (`…_API_KEY=`, `Bearer …`) |
| `PRIVATE_KEY` | Bloques `-----BEGIN … PRIVATE KEY-----` completos |
| `SSH_PUBLIC_KEY` | Claves públicas SSH con su comentario final |
| `ASSIGNED_SECRET` | Contraseñas y secretos asignados (`…_password=`, `client_secret:`), credenciales en URL (`esquema://usuario:clave@`) y JWT |

No se apagan desde la configuración. Un fichero `policies.json` que intente
tocarlas es un fichero inválido, y un fichero inválido bloquea el envío.

### Políticas blandas (Custom) — se ajustan en `policies.json`

| Policy | Qué tapa |
|---|---|
| `PRIVATE_IP` | Rangos privados y de enlace local (10/8, 172.16/12, 192.168/16, 100.64/10, 169.254/16, ULA y link-local de IPv6) |
| `HOME_PATH` | Rutas absolutas bajo `/home` `/mnt` `/srv` `/opt` `/var` `/media` |
| `NODE_PATH` | Los nombres de máquina **que tú declares**. Nace vacía: sin nombres declarados no busca nada |

```json
{
  "PRIVATE_IP": { "activa": true },
  "HOME_PATH":  { "activa": true },
  "NODE_PATH":  { "activa": true, "nombres": ["mi-portatil", "servidor-casa"] }
}
```

## Qué NO hace

- **No es un detector de PII de propósito general.** No busca nombres de persona,
  correos, teléfonos, tarjetas ni números de identidad.
- **No entiende el texto.** Son expresiones regulares sobre formas conocidas. Un
  secreto con forma inédita pasa; un token que no parece token, pasa.
- **No hay exención por directorio.** Ninguna ruta compra una excepción: si un
  secreto aparece, se tapa, viva donde viva.
- **No cifra, no anonimiza de forma reversible, no guarda un mapa.** Lo redactado
  se sustituye por una máscara y no se puede recuperar desde la salida.
- **No intercepta nada por su cuenta.** No es un proxy ni un hook: es una función
  que tienes que llamar tú antes de enviar.
- **No cubre `/Users` ni rutas de Windows** todavía. Ver más abajo.
- **No es una garantía.** Reduce la superficie de fuga; no la elimina.

## Uso mínimo

```python
from guardrails import preparar_envio, EnvioBloqueado

try:
    respuesta = preparar_envio(prompt_del_usuario)
except EnvioBloqueado:
    ...  # no se envía nada: ni el original, ni un "por si acaso"

enviar_al_modelo(respuesta["texto"])
mostrar_contador(respuesta["hallazgos"])   # [{'policy': …, 'count': …}]
```

`preparar_envio` devuelve `{estado, texto, hallazgos, policy_hash}`. Ese contador
es el valor de retorno: la interfaz lo muestra, no lo recalcula.

**Fail-closed.** Si el motor falla, o `policies.json` falta o está corrupto,
`preparar_envio` lanza `EnvioBloqueado` y no devuelve texto. Un fallo del filtro
nunca se interpreta como «no había nada que redactar».

**`POLICY_HASH`** es la huella del conjunto de patrones de las políticas duras.
Sirve para comparar dos instalaciones. Cubre solo las duras a propósito: si
cubriera las blandas, cambiaría en cuanto alguien personalizase su configuración
y dejaría de significar nada.

Tests (sin dependencias):

```
python3 -m unittest -v test_guardrails
```

## El corpus

`corpus/muestras.json` son **36 muestras** con la forma que tienen de verdad los
ficheros de configuración, los logs y las trazas — `.env`, `docker-compose.yml`,
manifiestos, `.netrc`, `.npmrc`, trazas de Python y de Node, salidas de `mount` y
`journalctl` — más **12 límites declarados**: textos que hoy **no** se redactan,
con el motivo escrito al lado.

Todo su contenido es inventado. Un test comprueba que el corpus no contenga
nada de la máquina donde corre.

Los límites se prueban igual que los casos: si uno empieza a dispararse, el test
cae y alguien tiene que mover la línea a mano. Una cobertura que crece sin que
nadie se entere no es cobertura, es azar.

Un detalle que el corpus fijó: `password caducó ayer` **no** se redacta. Cuando
entre la palabra clave y el valor solo hay un espacio, el valor tiene que
parecer un secreto — llevar un dígito, un signo, o pasar de doce letras. Con
`:` o `=` de por medio no hace falta: ahí la asignación es explícita. Un filtro
que muerde la prosa acaba apagado, y un filtro apagado no protege nada.

## Estado real

**Fase 0.** Es una función y su suite de tests, y nada más. No hay servidor, no
hay endpoint, no hay interruptor en pantalla, no hay paquete instalable, no hay
integración con ningún cliente. Lo que existe está probado; lo que no aparece en
la tabla de políticas, no existe.

Huecos declarados, no olvidados:

- `/Users` (macOS) y `C:\` (Windows) **no** están cubiertos. Entran cuando tengan
  su test explícito, y `C:\` con su propio caso de escapado de la barra invertida.
  Hay un test que hoy fija esa ausencia: caerá el día que se cubran, que es
  justo lo que se quiere de él.
- La configuración se relee en cada llamada. Es correcto y es lento; con textos
  grandes o en bucle, hay que medirlo antes de usarlo en caliente.

## Por qué `/tmp` queda fuera

`HOME_PATH` cubre seis prefijos (`/home` `/mnt` `/srv` `/opt` `/var` `/media`) y
deja `/tmp` fuera **por decisión firmada**, no por descuido.

`/tmp` es el sitio donde todo el mundo —el sistema, el editor, el navegador, el
propio intérprete— deja ficheros de paso con nombres generados. Casi ninguno dice
nada de quien los escribió. Incluirlo llenaría el contador de hallazgos que no
son hallazgos, y un contador que siempre marca alto es un contador que se deja
de mirar: el coste no es el ruido, es que la señal deje de creerse.

La decisión se revisa con datos, no con opiniones: hace falta medir en uso real
qué proporción de rutas `/tmp` contienen algo identificable. Hasta que ese dato
exista, `/tmp` no entra.
