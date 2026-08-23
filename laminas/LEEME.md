# Láminas fuente

Los originales del concept art, tal y como llegaron: 1664×928, sin canal alfa
(la transparencia venía pintada como damero casi blanco).

Viven **fuera de `assets/`** a propósito. `assets/` se sirve por la red y se
empaqueta en el ejecutable; estas cinco pesan 13 MB entre ellas y no se piden
nunca desde la interfaz. Aquí quedan como fuente de verdad para poder rehacer
un recorte sin volver a pedir el dibujo.

| Fichero | Qué es | Derivados en `assets/` |
|---|---|---|
| `1787443886.png` | Las letras «Aurelius» con engranajes | `titulo-aurelius.png` |
| `1787443916.png` | Fondo violeta de circuitos | *(sin uso desde que el tablero es de mármol)* |
| `1787444210.png` | La pizarra de mármol con marco de bronce | `marco-marmol.png`, `fondo-marmol.jpg` |
| `1787444220.png` | Tira de los cinco iconos | `icono-{memoria,frontera,camino,perfil,proyectos}.png` |
| `1787444225.png` | Placa de bronce con el micrófono | `boton-hablar.png` |

El recorte no se hace por color global: el mármol del marco es casi blanco y un
filtro de claros lo borraría entero. Se inunda desde los bordes exigiendo
*claro **y** sin color*, que es lo que separa el damero del bronce.
