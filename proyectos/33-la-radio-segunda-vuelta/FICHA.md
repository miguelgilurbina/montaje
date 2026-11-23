# 33 · La radio, segunda vuelta

**Fecha:** 2026-11-23

## Idea

El segundo de los cuatro territorios que se encontraron buscando (la historia está en la ficha del 32). Sigue a la
radio del 31: más imágenes que llegan por el aire, y la imagen escondida en el sonido. Las fuentes que se miraron:

- [la transmisión del satélite (APT)](https://en.wikipedia.org/wiki/Automatic_picture_transmission);
- [Hellschreiber](https://en.wikipedia.org/wiki/Hellschreiber);
- [pintar en la cascada](https://www.rtl-sdr.com/exploring-the-art-and-science-of-spectral-painting-with-sdr).

## Material

El banco del probador (La Añoranza). Todo en código.

## Lo que se hizo

**`py/montaje/aire.py`**, con tres aparatos. Su sonido va en el mismo módulo (`aire.sonido`).

**`satelite`: la imagen de los satélites meteorológicos (APT).**

- Dos imágenes lado a lado, la de luz y la infrarroja (lo frío, claro).
- Las barras de sincronismo y la cuña de grises de la telemetría, en las proporciones de la línea de 2 080 pixeles.
- Llega línea por línea.
- El sonido es el de la norma, a dos líneas por segundo: una portadora de 2 400 Hz modulada en amplitud por el brillo
  de la línea, con el sincronismo A (1 040 Hz, 7 ciclos) y el B (832 pulsos por segundo, 7 pulsos). Es el tic-tac.
- La imagen se dibuja acelerada; el tic-tac no.
- Según Wikipedia, el último satélite que mandaba APT se apagó el 19 de agosto de 2025.

**`hell`: el texto que llega por radio (Hellschreiber, 1929).**

- Una tira de papel que corre con el texto en puntos, impreso dos veces, inclinado si los relojes no calzan.
- El sonido es un tono de 980 Hz que se prende y se apaga punto por punto: cada columna se barre de abajo arriba.
- La letra de 5 × 7 puntos se dibujó aquí; no es la original.

**`cascada`: la pantalla de una radio por software.**

- La canción cae en las tintas de Curiana, de arriba abajo.
- Cada `dura` segundos, el cuadro de la entrada se dibuja en la cascada con el sonido mismo: 64 tonos entre 1 y
  4 kHz, de la última fila a la primera, para que caiga derecho.
- Las pinturas se leen de la entrada, no se recuerdan: los pedazos en paralelo dibujan igual las que siguen cayendo.

**Tres estilos:** `el-satelite-del-tiempo`, `el-texto-que-llega-por-radio` (con «CURIANA RADIO 88.8 FM») y
`la-imagen-en-la-cascada`.

## Lo que midió Claude (que no oye)

- El texto salió primero patas arriba: las filas se invertían al dibujarlas. Ahora se lee derecho en las dos copias.
- En el espectrograma del audio de la muestra de la cascada, la playa del video aparece dibujada, igual que en la
  imagen: la imagen está en el sonido.
- En el del satélite, la portadora de 2 400 Hz aparece justo en los segundos en que se dibuja cada imagen.
- Las pruebas (`test_buscados.py`):
  - el texto suena punto por punto: la I tiene tono en su columna llena y silencio en el espacio;
  - el satélite se repite cada medio segundo;
  - la pintura de una imagen con la mitad derecha clara suena en los tonos altos de su banda, y nada por encima de
    5 kHz.

## Lo que dijo Miguel

- «Tu busca más por favor»
- En la tarjeta: «La radio, segunda vuelta», con los otros tres. Se juzga al final.
