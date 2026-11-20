# 24 · La mesa analógica

**Fecha:** 2026-11-20 (de noche, mientras Miguel dormía)

## Idea

Miguel, antes de dormir: «Busca referencias para alteración de vídeo análogo y trabaja en implementar eso en el
proyecto. Yo voy a dormir. Sigue tu intuición».

La intuición: no hacer otro «filtro VHS» (ruido, líneas y un «PLAY» encima), sino **simular la señal**. Su idea
del 2026-10-12, el flujo «Video Glitch» (un aparato que rompe la señal y un TBC que la estabiliza), ya pedía
pensar en aparatos. La imagen se vuelve la señal NTSC-M que era (la norma de la televisión de Venezuela) y pasa
por una cadena de aparatos simulados; los defectos salen solos de esa física. Las referencias (simuladores de
código abierto, el AV Artifact Atlas, la norma, el video arte de Paik, Rutt/Etra y Sandin) están en
[`direccion/ANALOGO.md`](../../direccion/ANALOGO.md), con sus fuentes.

## Material

El banco del probador (ocho clips de Miguel de La Añoranza y el paso de la calma a la banda de la canción, 21 s)
para las muestras de la galería, y un clip del banco (`natalia-02`, `natalia-06`) para las pruebas de un cuadro.
Nada se bajó: las referencias se leyeron en la web, el motor se escribió desde su descripción (el código de los
simuladores es GPL o de linaje GPL, y este repo es MIT).

## Lo que se hizo

- **`py/montaje/analogo.py`**: la señal (480 líneas de 760 muestras, filtros en el espectro de cada línea, la
  subportadora de color con su fase que se invierte por línea y por cuadro) y diez aparatos: `camara`, `osd`,
  `cinta`, `antena`, `tbc`, `colorizador`, `iman`, `relieve`, `realimentacion` y `pantalla`. El video se procesa
  en pedazos en paralelo; todo lo aleatorio sale de la semilla y del número de cuadro, así que no hay costura, y lo
  que tiene memoria (la estela del tubo de la cámara, la realimentación, el fósforo) se calienta antes de cada
  pedazo.
- **El sonido de la cinta** (`cinta.sonido`: `lineal` o `hifi`; por defecto la música queda intacta).
- **El comando** `python montaje.py analogo` (con `--ventana`, `--comparar`, `--recorrido`, `--cadenas`), el
  comando `analogo` en la galería (validado) y en el probador.
- **Quince cadenas** en `estilos/` (estado `propuesta`), con su muestra del probador.
- `py/pruebas/test_analogo.py`: 22 pruebas de la física (el color liso vuelve igual, el arcoíris en las rayas
  finas, los puntos que caminan, el color corrido y arrastrado por la cinta, el ancho de banda de la luma por
  formato, el TBC que endereza, el cabezal que sólo toca abajo, sin costura entre pedazos, la pantalla que
  conserva el brillo, el sonido de la cinta, un video de punta a punta con su audio).

## Errores que aparecieron (y quedaron como pruebas)

- El pasabanda del color tenía 13 % de respuesta en la continua: le robaba brillo a todo lo liso (un gris de 0,55
  salía 0,48). Ahora lleva un pasaaltos que lo deja en cero abajo.
- El realce de bordes tenía ganancia en la continua: aclaraba un 2,8 %. Ahora afila sin aclarar.
- El fantasma sumaba energía y la antena quemaba los cielos; el control automático de ganancia del televisor lo
  compensa, y ahora el motor también.
- La pantalla tardaba 750 ms por cuadro a 1620×1080: numpy recorría tríos de colores con pesos estirados. En
  planos, muestreando la grilla chica de la señal con la curva ya dentro de las coordenadas, y con la gamma en una
  tabla, quedó en ~280 ms.

## La segunda mirada

Un agente que sólo leyó y probó (sin tocar el repo) revisó el motor esa misma noche y reprodujo cada hallazgo con
un video corto. Lo que encontró, ya arreglado y con su prueba:

- **El fósforo quemaba la imagen**: la persistencia guardaba el cuadro antes de una multiplicación en su lugar; desde
  el segundo cuadro, todo blanco. Ninguna cadena de la galería la usa (el fósforo P22 casi no deja rastro), por eso
  no se vio en las muestras.
- **Las ventanas con memoria dependían de los pedazos**: fuera de una ventana la realimentación no andaba, y al
  abrirla su memoria dependía de dónde había caído la costura (y del número de procesos del computador). Ahora lo
  que tiene memoria sigue andando fuera de las ventanas.
- **Rodar invertía el color** con corrimientos impares (la fase de la subportadora se invierte en cada línea).
- **La realimentación no se apagaba** si mezcla × contraste llegaba a 1: ahora se rechaza desde 0,97.
- **Videos girados y fotos con EXIF** salían aplastados o de lado.
- **El largo salía del contenedor, no del video**: un audio más largo dejaba pedazos sin cuadros; un video que
  empieza después del audio salía corrido.
- **La máscara recortaba los blancos**: a 1080 (con máscara) el blanco salía 12 % más oscuro que en la muestra del
  probador (sin máscara). Ahora va después de la gamma y más leve en lo claro.
- Menores: la gamma en 16 bits (las sombras iban en escalones), la saturación de la pista lineal subía 3,6 dB lo
  suave, la primera línea perdía el color con el peine, los corrimientos grandes traían el otro lado de la línea,
  una entrada chica se agrandaba como vecino más cercano (y daba arcoíris), las fotos grandes salían a su tamaño
  completo, bt2020 se leía como bt601, dos cintas en la misma cadena temblaban en fase, el `osd` escribía sobre la
  memoria de otro aparato y el probador escondía si el motor analógico se volvía más lento.

Queda sin arreglar, anotado: durante el fundido de una ventana con sonido de cinta se mezcla el audio limpio con el
que tiembla, y eso hace un leve efecto de peine en ese medio segundo.

## Lo que salió (mirado en hojas)

Las quince en el probador (21 s del banco cada una), sin fallas; dibujarlas cuesta de 1 a 5,6 veces lo que el banco
solo (la copia de copia, con tres pasadas de cinta, es la más cara). Mirado en dos cuadros de cada muestra (la
calma del mar y la mujer de la cocina con la banda):

| Cadena | Lo que se ve |
|---|---|
| `vhs-de-la-casa` | la que más se parece a una cinta de verdad: el color corrido, el halo claro en los bordes, vetas de color en lo oscuro; no grita |
| `copia-de-copia` | más ruido y el color despegado de la forma; la cara todavía se reconoce |
| `cinta-gastada` | ruido fuerte y la franja del tracking abajo; para ventanas cortas |
| `cinta-con-tbc` | la misma cinta con las líneas derechas: se nota la diferencia en los bordes verticales (el tronco, el marco de la ventana) |
| `camara-de-los-90` | la fecha y la hora abajo a la derecha (la hora corre); el blanco del delantal y la ventana se queman |
| `camara-de-tubo` | más cálida y pálida; la cola de cometa sólo aparece donde algo claro se mueve |
| `antena-lejana` | casi siempre en blanco y negro: con esa nieve el televisor apaga el color, y vuelve a ratos |
| `canal-con-interferencia` | dos fantasmas a la derecha; las rayas diagonales casi no se ven a 540 |
| `se-pierde-la-senal` | la imagen rueda y se desgarra en diagonal, con las barras negras del borrado: un golpe, no un estado |
| `televisor-de-tubo`, `vhs-en-el-televisor` | el vidrio curvo, las esquinas y la viñeta; a 540 sin líneas (a propósito), a 1080 con ellas |
| `iman-en-el-televisor` | una mancha amarillo verdosa que se pasea y tuerce lo que toca |
| `relieve-de-barrido` | el mar y la cocina como relieve de líneas doradas sobre la noche: lo más distinto de la mesa |
| `tunel-de-video` | sutil: los ecos de las ollas bajan en diagonal; con poco movimiento casi no se ve |
| `colorizador-de-tintas` | las tintas de Curiana en bandas planas: el mar oro sobre índigo, la cocina en ocre y azul |

**El sonido** de `copia-de-copia` y `cinta-gastada` (las dos con la pista lineal) medido en sus muestras contra la
de `vhs-de-la-casa` (que deja la canción intacta): la energía sobre 6 kHz baja de 0,49 % a 0,25–0,29 % y el nivel,
1 dB. Claude no oye: el oído es de Miguel.

## Renders

En `~/Videos/montaje/24-mesa-analogica/render/`: `banco-1080.mp4` (el banco del probador a calidad final, la base) y
`recorrido-1080.mp4` (las quince, 6 s cada una sobre el mismo tramo, con su nombre; primero, tal cual). Las
muestras de la galería, en `~/Videos/montaje/estilos/probador/`.

## Lo que dijo Miguel

—

## Lo aprendido

- Medido: un proceso hace ~2 cuadros por segundo con cinta + pantalla a 1620×1080 y ~7 con la cinta sola; en
  paralelo no pasa de ~5 en este computador (8 núcleos que bajan de frecuencia cuando trabajan todos).
- Lejos, el tubo no se ve: con pocos pixeles por línea las líneas y la máscara hacen muaré; el motor las apaga bajo
  ~1,25 pixeles por línea y ~1100 de ancho. Las muestras de la galería (540 de alto) muestran el tubo sin líneas;
  para juzgarlo hay que mirarlo a 1080 (el recorrido).
