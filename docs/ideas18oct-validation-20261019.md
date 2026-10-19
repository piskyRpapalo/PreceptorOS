# Recibo de validación ideas18oct · APP · 2026-10-19

Máquina/runtime: Linux 7.0.0-38-generic x86_64; Python 3.14.4.

## Gate del repositorio

- Comando exacto: `./bin/pruebas`.
- Resultado: dos ejecuciones completas consecutivas de 1.033/1.033 pruebas
  verdes en 72 suites y 6 corredores.
- Saltos: 11 en cada ejecución. El escaneo privado queda `NO_DATA` porque
  `PRECEPTOROS_PRIVATE_SCAN_TOKENS` no está disponible; no se contó como verde.
- Sabotajes, cada ejecución: idioma 4/4, fuga 6/6, consola 15/15, decisor 6/6,
  canales 6/6 y lab 8/8 detectados (45/45).
- Rojo antes de verde: la primera ejecución encontró que la nueva suite no
  estaba en la lista de `bin/pruebas`; se añadió a `UNITTEST`. Las dos
  ejecuciones completas posteriores terminaron `VERDE · 1033/1033`.
- CI remoto: `NO_DATA`, causa: no configurado en el repositorio.

## Pruebas dirigidas

- Comando exacto: `python3 -m unittest -v test_ideas18oct_contracts.py`.
- Resultado: 7 pruebas, 0 fallos. Incluye rechazo entero por encima de
  1.024 B, seis sellos, claves JSON duplicadas, UTC RFC3339 y transición
  exacta de `LIVE` a `STALE` en 604.800 segundos.

## Límites

Las pruebas no ejercitan render de navegador, service worker ni dispositivo
físico. Esas rutas siguen `NO_DATA` salvo los recibos live expresos del LAB.
