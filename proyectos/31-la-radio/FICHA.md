# 31 · La radio

**Fecha:** 2026-11-22

## Idea

El cuarto de los territorios que Miguel eligió abrir en el mapa de la galería (la historia está en la ficha del 28).
Curiana es una radio («Transmisión cultural desde Abya Yala. 88.8 FM.»): imágenes que llegan por el aire, el dial del
88.8 y la canción que se ve. Junta dos motivos que estaban propuestos en `direccion/MOTIVOS.md`: el dial 88.8 y la
radio en el sonido.

## Material

El banco del probador (La Añoranza). Todo en código.

## Lo que se hizo

**`py/montaje/radio.py`**, con tres aparatos.

**`radiofoto`** (perilla `modo`): la foto que llega por un canal de sonido, línea por línea, de arriba abajo.

- `sstv`, la televisión de barrido lento de los radioaficionados: la foto chica en color (320 × 256), con el ruido de
  la banda y un poco inclinada.
- `fax`, el radiofacsímil del tiempo: en papel térmico, con la franja de fase.
- `telefoto`, la foto de prensa por cable: gris, con las rayas del tambor.

Cada `dura` segundos llega una: el encabezado, la imagen que se dibuja (el cuadro que había al empezar) y un rato
quieta.

Su sonido son los tonos que la dibujan (`sonido: tonos`): en cada línea, la altura del tono sigue el brillo, de
1 500 Hz el negro a 2 300 Hz el blanco, como en las de verdad. La sstv manda el sincronismo a 1 200 Hz y su
encabezado; el fax, un tic blanco al principio de cada línea; la telefoto va en amplitud sobre 1 800 Hz. Para tener
el cuadro que se manda, el sonido lee la entrada en ese segundo (los aparatos de sonido reciben ahora `_entrada`).
Está acelerado: una sstv de verdad tarda de 36 segundos a dos minutos, así que un programa de radioaficionado no
leería estos tonos.

**`dial`** (un gesto): alguien mueve el dial.

- La imagen se desgarra y se pierde en la estática mientras la aguja recorre la escala de FM, y vuelve cuando se
  asienta en el 88.8.
- La escala está dibujada con la letra del dato y la aguja en oro.
- En el sonido (`sonido: sintonia`), la canción se va en la estática con el silbido entre emisoras, y vuelve.
- La imagen y el sonido usan la misma cuenta (`desintonia`).

**`osciloscopio`**: la canción dibujada en la pantalla de un osciloscopio.

- Un canal contra el otro, corrido unos milisegundos para que una canción en mono también dibuje una figura.
- En verde (o en oro), con la retícula y el fósforo que dura.
- Lee el audio de la entrada: el contexto de cada cuadro ahora sabe cuál es (`ctx.entrada`).

**Seis estilos:**

- `la-foto-que-llega-por-radio`, `radiofacsimil` y `telefoto-de-agencia`;
- `el-dial-que-sintoniza` (gesto sobre el banco limpio, dos movimientos en la muestra) y su variante
  `el-dial-al-empezar`. La variante usa la perilla `inicio`: una sola vez, al empezar el video, ya perdida en la
  estática. La pide la plantilla de la cortina de radio;
- `la-cancion-en-el-osciloscopio`.

## Lo que midió Claude (que no oye)

**La imagen, en las muestras:**

- cada seis o siete segundos llega una foto, línea por línea;
- el dial se desgarra en sus dos movimientos (3,3 s y 14,7 s) y vuelve con la aguja en el 88.8;
- el osciloscopio abre la figura cuando entra la banda y la achica en la calma.

En el primer dial, la estática tapaba todo en blanco y negro duro. Ahora queda el fantasma de la emisora y la nieve
es más gris.

**El sonido, en los espectrogramas:**

- los tonos de la radiofoto aparecen en su banda justo en los segundos en que se dibuja cada foto, y la canción baja
  mientras tanto;
- la estática del dial cae exactamente donde se rompe la imagen.

**Las pruebas:**

- la radiofoto se dibuja de arriba abajo (lo que falta llegar es papel);
- el tono del blanco es 2 300 Hz y el del negro 1 500, con menos de 150 Hz de error contando cruces;
- el dial empieza y termina en sintonía, se pierde en el medio, y la canción vuelve igual después.

## Lo que dijo Miguel

- En la tarjeta: «La radio», junto con los otros tres territorios. Se juzga al final.
- En la mesa (2026-11-23): la foto que llega por radio, el dial que sintoniza, el dial al empezar y la canción en el osciloscopio, **sí**; del osciloscopio: «Me encantaría expandir esta función.» El radiofacsímil y la telefoto de agencia, **a medias** (sin decir por qué todavía).
