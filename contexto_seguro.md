# Contexto seguro · Ollama

Generado por PreceptorOS el 2026-08-30 09:47 UTC. Puedes pegar esto en una IA externa.

## Qué se ha quitado de aquí
- `PRIVATE_IP` · 1 coincidencia

## Qué NO garantiza este filtro
Es determinista y auditable, no infalible. Estos huecos están declarados:
- **ip-publica** — IP pública: no es dato privado de la máquina
- **version-con-puntos** — cuatro números no son una IP
- **ruta-tmp** — exclusión firmada de /tmp por falsos positivos
- **ruta-relativa** — una ruta relativa no revela dónde vive nadie
- **ruta-usuarios-mac** — hueco declarado: entra cuando tenga su test explícito
- **ruta-windows** — hueco declarado: necesita su propio caso de escapado
- **prosa-contrasena** — prosa sin asignación: redactarla degrada el texto sin proteger nada
- **prosa-sin-contrasena** — palabra pegada, no es una asignación
- **identificador-uuid** — un UUID de traza no identifica a una persona ni a una máquina
- **hash-git** — un hash de commit no es una credencial
- **webhook-entrante** — URL de gancho con credencial en la ruta: NO cubierto hoy, ni se declara cubierto
- **correo** — el correo es dato personal, no secreto de máquina: fuera del alcance declarado
- **token-con-rotulo-humano** — «token» con un nombre propio delante NO se caza, ni suelto («Token del broker: mqtt_...») ni asignado («MQTT_TOKEN=mqtt_...»). MEDIDO, no supuesto: la primera version de esta nota decia que la forma asignada si entraba, y era falsa. Solo entra cuando el nombre se construye sobre api_key, access_token, auth_token, secret_key o bearer. Cubrir «token» a secas exigiria una regla sobre la palabra suelta, y en ESTE producto token es vocabulario del temario —uno de los cinco engramas del arranque explica que es—, asi que esa regla redactaria el propio material didactico. Se declara el hueco en vez de pagar ese precio.

Revisa el texto antes de pegarlo. El filtro reduce el trabajo; no lo sustituye.

## El contexto

### recuerdo 2

Ollama de este nodo escucha en http://[REDACTED:PRIVATE_IP]:11434, no en localhost
Trampa de configuracion: un `ollama list` pelado falla con «could not connect» y parece que el servicio esta caido. Esta vivo.
OLLAMA_HOST vive en ~/.config/environment.d/50-p0x.conf, no en .bashrc (que las shells no interactivas no leen). Medido: 8 modelos, 6.02 ms, backend vulkan (OLLAMA_IGPU_ENABLE=1 en la unidad).

### recuerdo 4

LoRA v7 servido en Ollama: preceptor-v7-linea-b:latest, preceptor-v7:latest
Son las dos lineas (A y B) entrenadas sobre sft_cot_v7.jsonl, 109 lineas, en CPU.
La forja vive en ~/.venvs/aurelius-forja y su torch es +cpu: no hay ruta GPU en este nodo. Entrenar v8 exige decidir si va aqui en CPU o en la-torre, que tiene CUDA pero no peft ni trl.
