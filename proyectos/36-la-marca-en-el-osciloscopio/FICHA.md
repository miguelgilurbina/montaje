# 36 · La marca en el osciloscopio

**Fecha:** 2026-11-23

## Idea

En la mesa, Miguel aprobó «La canción en el osciloscopio» (31) y escribió: «Me encantaría expandir esta función». Se le
propusieron tres caminos en una tarjeta y eligió el recomendado: la marca en el osciloscopio. Es un sonido que, mirado
en un osciloscopio, dibuja la marca, como la imagen escondida en la cascada del 33.

## Material

El banco del probador (La Añoranza), y dos piezas de la marca:

- la espiral del isotipo: el trazo vectorial del sitio, `espiral.svg`, copiado a la biblioteca de medios
  (`~/Videos/montaje/marca/`) para no ponerlo en este repo público;
- la letra Curiana Cartel, que ya está en `fuentes/` con su licencia.

## Lo que se hizo

**En `py/montaje/radio.py`, el osciloscopio tiene nuevas perillas:**

- `dibujo`: `cancion`, que es lo de antes, o `espiral`, `nombre` o `espiral-y-nombre`;
- `cada` y `dura`: cada `cada` segundos, durante `dura`, la canción se aparta (queda un 6 %) y el haz dibuja la
  marca, que se mece un poco de lado;
- `texto`: el nombre, «CURIANA» por defecto, leído de los contornos de la letra con fontTools.

**Cómo se dibuja.** La figura es un solo recorrido del haz, de 2 400 puntos repartidos por largo, que se repite 50
veces por segundo. La espiral va de ida y de vuelta, sin salto. Entre letra y letra, el haz salta rápido y el salto
casi no deja traza.

**Cómo suena** (`sonido: marca`): el canal izquierdo es la x y el derecho la y. Lo que se oye es el dibujo mismo, un
zumbido grave con sus armónicos. Mirado en un osciloscopio de verdad, el audio de la salida dibuja la marca. La imagen
y el sonido usan la misma cuenta (`marca_xy`, `marca_ganancia`).

**Tres estilos:** `la-marca-en-el-osciloscopio` (la espiral y el nombre) y sus variantes
`la-espiral-en-el-osciloscopio` y `el-nombre-en-el-osciloscopio`.

## Lo que midió Claude (que no oye)

- En la hoja, la espiral y «CURIANA» se leen claros en el verde del fósforo, y en los segundos de canción vuelve la
  figura de la música.
- Con la canción al 15 % debajo de la marca, el dibujo temblaba donde la canción es fuerte (la segunda y la tercera
  vez). Ahora queda al 6 %.
- El audio de la muestra, puesto en X e Y como lo vería un osciloscopio, dibuja la espiral y la franja del nombre,
  borrosas porque la muestra va comprimida (96 kb/s). En el render final, con más calidad, se lee mejor.
- Las pruebas (`test_buscados.py`):
  - los dos canales del audio, uno contra el otro, son la figura: correlación de más de 0,95 con el recorrido;
  - pasada la marca, la canción vuelve tal cual;
  - el nombre tiene sus letras.

## Lo que dijo Miguel

- Del osciloscopio, en la mesa: «Me encantaría expandir esta función.»
- En la tarjeta: «La marca en el osciloscopio».
