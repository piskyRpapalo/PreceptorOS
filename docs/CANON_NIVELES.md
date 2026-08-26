# CANON · los cuatro niveles · definición cerrada

**Firmado:** 2026-08-26 · **Estado:** CANON. No es propuesta.

## Por qué existe este fichero

El Nivel 1 llegó definido de dos formas incompatibles el mismo día:

| Fuente | Decía |
|---|---|
| Despertar §2 | «NIVEL 1 · ARNÉS / CEREBRO EXTERNO — puede consultar APIs externas (Claude, Gemini) **como herramienta**» |
| Parte 2 §A | «MODO 1 · ARNÉS (Cerebro **Local**) — inferencia 100 % local. Zero-cloud» |

Se implementó la segunda. Este fichero la cierra para que la contradicción no
viva en dos prompts, donde la próxima sesión la reabriría — y donde no hay
forma de saber cuál manda.

## La definición que manda

| Nivel | Nombre | Qué concede | Qué NO concede |
|---|---|---|---|
| **0** | Santuario | Biblioteca estándar, disco local, lógica determinista. Es el suelo y el valor por defecto. | Abrir un socket, de cualquier clase, a donde sea. |
| **1** | Arnés · **cerebro local** | Ejecutar un fichero de modelo que vive **en esta máquina**. La inferencia es 100 % local. | **Salir de la máquina. Nada de APIs externas en el nivel 1.** |
| **2** | Expansión · consentimientos | Todo lo que cruza el borde de la máquina: APIs externas, transcripción en la nube, OCR, descargas, sincronización cifrada. Cada uno se consiente por separado. | Consentir una vez para todo. |
| **3** | Ecosistema | Hardware, procesos y dispositivos locales. Vive **fuera** del build del núcleo y se engancha como complemento. | Cambiar lo que hacen los niveles 0-2. Si el complemento muere, el núcleo sigue entero. |

## La frase que zanja el choque

> **El nivel 1 no sale de la máquina.** Un cerebro que consulta una API está
> fuera, y estar fuera es el nivel 2 — se llame cerebro, herramienta o consejo.
> Lo que define el escalón no es para qué se sale: es que se sale.

## Dónde está escrito en el código

`soberania.CAPACIDADES` es la tabla ejecutable de esta página, y
`test_soberania.py` la comprueba capacidad por capacidad y nivel por nivel:

```
inferencia_local    → 1
recursos_externos   → 2
sincronizacion      → 2
complementos        → 3
hardware_local      → 3
```

El nivel 0 no aparece, y no es un olvido: lo que el santuario ya hace no pide
permiso. Meterlo en la tabla lo volvería condicional, y el suelo dejaría de ser
suelo.

Doctrina completa de las capas: [SOBERANIA.md](SOBERANIA.md).

## Licencia

CC BY-SA 4.0 — [LICENSE-PROSE](../LICENSE-PROSE).
