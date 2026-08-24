# v1.1 · PreceptorOS

**Fecha:** 2026-08-25 · **Anterior:** [v1.0.0](RELEASE_v1.0.md)

Dos cosas en esta versión: el producto cambia de nombre, y responde entre cinco
y doce veces más rápido. Nada de lo tuyo se mueve.

---

## Se llama PreceptorOS

El producto pasa a llamarse **PreceptorOS**. **El personaje sigue siendo
Aurelius**, y su nombre sigue honrando a Marco Aurelio: son dos cosas distintas
y este renombrado no las confunde. El sprite, el saludo, el carácter y el Lore
no han cambiado ni un byte.

### Lo tuyo no se mueve

Si ya lo tenías instalado, **tu carpeta se queda donde está**. La casa nueva es
`~/.preceptoros/`, pero si existe `~/.aurelius/` se adopta en su sitio y todo
sigue funcionando: tu memoria, tu perfil, tu voz y los modelos que descargaste.

No se mueve nada porque mover gigabytes es una decisión tuya, y a medio camino
—en un teléfono con la batería al 12 %— es una forma nueva de perderlo todo.

### Los nombres viejos siguen funcionando hasta el 2026-11-23

| Lo viejo | Lo nuevo | Estado |
|---|---|---|
| `python3 aurelius.py` | `python3 preceptoros.py` | funciona, avisa una vez |
| `import aurelius` | `import preceptoros` | funciona, es un alias puro |
| `AURELIUS_MOTOR`, `AURELIUS_ESPERA`… | `PRECEPTOROS_*` | funciona, avisa una vez |
| `bin/aurelius-servicio`, `-pwa`, `-puente` | `bin/preceptoros-*` | funciona, son enlaces |

Si están puestos los dos nombres de una variable, **gana el nuevo**: quien ya
migró no debe salir perdiendo.

La fecha no es decorativa. Una compatibilidad sin fecha se queda para siempre y
dentro de tres años nadie sabe si se puede quitar. El **2026-11-23** el puente
se retira.

---

## Va mucho más rápido

El modelo ya no vuelve a leerse su hoja de personaje entera en cada turno. Con
`--prompt-cache`, medido el 2026-08-24 con el prompt real:

| | primer token | turno completo |
|---|---|---|
| Escritorio (Ryzen 7, solo CPU) | 17,7 s → **2,4 s** | 20,3 s → **5,8 s** |
| Teléfono (Android, 8 núcleos) | 337,7 s → **7,3 s** | 408,6 s → **32,8 s** |

En el teléfono, de casi seis minutos por turno a treinta y tres segundos.

El caché ocupa ~252 MiB, vive al lado de tu memoria, guarda tensores —**no tus
palabras**— y es un fichero, no un servidor: no abre ningún puerto. Bórralo
cuando quieras; se rehace solo. Para no tenerlo: `PRECEPTOROS_SIN_CACHE=1`.

---

## Y ahora busca

Búsqueda por texto completo sobre tus recuerdos, con el buscador que ya viene
dentro de SQLite. **Cero dependencias nuevas.** Busca *palabras*, no
significado: encontrar lo que querías decir exigiría un modelo de embeddings, y
eso rompería la promesa de que la biblioteca estándar es el único requisito.

El índice no duplica tu texto —hay una prueba que lo vigila— y lo archivado no
reaparece por la puerta de atrás de la búsqueda.

---

## Además

- **Caminos de aprendizaje** (`~/.preceptoros/path/`): secuencias de pasos que
  eliges tú. Se leen sin modelo y sin red. Vienen dos de fábrica.
- **Cada turno se cronometra**, y lo que no se midió dice `NO_DATA` en vez de
  cero: un cero se promedia y mentiría en la media.

---

## Cómo actualizar

```bash
git pull
python3 preceptoros.py
```

No hay migración que ejecutar. Si algo de lo viejo deja de funcionar antes del
2026-11-23, es un fallo — cuéntalo.

---

**447 pruebas en 33 suites, todas en verde.** Sin dependencias fuera de la
biblioteca estándar.
