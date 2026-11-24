# 39 · Transiciones en todo

**Fecha:** 2026-11-23

## Idea

Más formas de pasar de una imagen a otra, y en más lugares: entre fotos (no sólo entre clips) y al empezar cada tramo
del guion. Era G1/K1 en `PROPUESTAS.md`; volvió al mirar el catálogo de transiciones de OpenMontage. Escrito desde
cero, sin mirar su código.

## Material

El banco del probador (La Añoranza) para las muestras; para las fotos, una prueba aparte con cuadros de los clips de
práctica (borrada después).

## Lo que se hizo

- Nueve transiciones nuevas en `src/Montaje.tsx` (`transicionNueva`): **luz** (lo claro de la nueva primero, en
  «aclarar»), **desenfoque**, **doble** (doble exposición pasajera, en «trama»), **quemado** (la película que se quema
  desde un borde), **sacudon**, **separacion** (los colores corridos, con un filtro SVG), **pixeles** (por bloques,
  con una máscara), **latigazo** (el paneo rápido, desenfocado en su dirección) y **cinta** (la idea de Miguel del
  2026-11-09: «la imagen siguiente se agranda»).
- `py/montaje/transiciones.py`: las elige para todos los modos. La **ronda no cambia** (recorre las seis de antes):
  si las nuevas entraran solas, cambiaría lo ya juzgado (el 21). La luz y la doble apagan a la que se va al final de
  la entrada (si no, al terminar la mezcla la imagen saltaría); el latigazo la empuja, como el empuje.
- `pulso`: `transicion_tramo`, cómo entra el primer clip de cada tramo del guion (un cambio de parte que se nota
  distinto de un cambio de clip).
- `secuencia`: `transicion`, `transicion_golpes` y `transicion_dir`. Sin `transicion` (o con «corte») el plan es el
  de siempre.
- Las fotos (`CapaImagen`) dibujan las transiciones medidas en su caja, no en el cuadro: una foto que cubre el cuadro
  puede ser más grande que él.
- Nueve estilos `propuesta` (`transicion-<tipo>`) con su muestra en el probador; el vocabulario del panel las nombra.

## Lo que midió Claude (que no oye)

- `planes.py`: las 57 planificaciones de los experimentos con clips, antes y después: **57 iguales, 0 distintos**.
- Las muestras: separación y bloques mirados cuadro a cuadro a través del cambio; después de la transición, el cuadro
  es el mismo que con la cortina (no queda corrimiento).
- Fotos: un proyecto de prueba con `secuencia` y seis versiones (cinta, luz, bloques, quemado, latigazo, doble),
  renderizado con Remotion: las seis se dibujan. Sin `transicion` y con «corte» las capas salen idénticas.
- `test_transiciones.py` (4) y `test_motor.py` al día con la ronda.
- El collage y la cinta (los modos de fotos que se acumulan o corren) no tienen transiciones todavía: sus capas no
  ocupan el cuadro y el iris o el empuje habría que pensarlos para eso.

## Lo que dijo Miguel

- «y podríamos sacar nosotros algo de ahí pero hacerlo nosotros mismos?» (de OpenMontage); eligió el etalonaje con
  LUT, las transiciones en todo y la medida de monotonía.

## Veredicto

Por juzgar.
