# 26 · Los parecidos: uno por grupo, los momentos como gestos y la lente que se vea

**Fecha:** 2026-11-22

## Idea

Miguel juzgó desde el teléfono, en la mesa de montaje, 49 de los 53 estilos de 24 y 25 (36 sí, 10 a medias y 3
no); los otros cuatro ya los había juzgado en el chat. Después dijo: «Hay muchos que son muy parecidos entre si».

No hacía falta adivinar cuáles: las muestras del probador salen todas del mismo banco y empiezan sincronizadas, así
que se pueden comparar cuadro a cuadro. Con la medida y las hojas lado a lado, se le propusieron tres arreglos en
tarjetas y **eligió los tres recomendados**:

1. **Uno por grupo** (Repetidos): queda un estilo por grupo; lo que separaba a los demás pasa a ser una variante
   dentro de él. No se borra nada.
2. **Como gestos aparte** (Momentos): la pausa, el rebobinado, el arranque, el estrobo, la llave, la pintura, el
   mosaico y el multi dejan de ser estilos y pasan a ser gestos que se ponen sobre cualquier base.
3. **Subirlos hasta que se vean** (Lente): el lente barato y el foco al pulso, con más fuerza, para volver a
   juzgarlos.

## Material

Las muestras del probador (`~/Videos/montaje/estilos/probador/`: 810×540, 24 cuadros, el banco de La Añoranza).
Nada se bajó.

## La medida

Fuera del repo (un script en la carpeta de trabajo de la sesión), sobre los primeros 20 s de cada muestra a 8 cuadros
por segundo y 270×180:

- **el aspecto**: cada cuadro bajado a 30×20 en color, comparado con el mismo cuadro de la otra muestra (encuadre,
  color, forma);
- **la textura**: lo fino que queda al restar un desenfoque de 3×3 (grano, ruido, nitidez), la saturación, el brillo,
  el contraste, el parpadeo y la dominante de color;
- **el movimiento**: cuánto cambia cada cuadro respecto del anterior, a 45×30.

Cada parte se divide por su mediana entre todos los pares y se suman. La mediana de todos los pares del probador
quedó en 3,3; el 5 % más parecido, debajo de 0,86. Entre los nuevos, los más cercanos:

| par | distancia |
|---|---|
| estrobo de la consola · VHS de la casa | 0,24 |
| foto con fecha · foto de laboratorio | 0,25 |
| cámara de los 90 · VHS de la casa | 0,30 |
| película en la pared · en la sábana | 0,31 |
| pausa del VHS · VHS de la casa | 0,31 |
| televisor de tubo · VHS en el televisor | 0,38 |
| foto de laboratorio · la Fuji | 0,55 |
| super 8 sonoro · pasado a VHS | 0,76 |

Las hojas (cuatro momentos de cada muestra, una fila por estilo) lo confirmaron, y mostraron lo que la medida no
ve bien: el Super 8 de la familia, el sonoro y el pasado a VHS son la misma imagen aunque el vaivén de la
película los separe en la medida.

Tres cosas que la medida enseñó:

- **Un momento se diluye.** Los de la consola y la casetera «a ratos» son el VHS de la casa la mayor parte del
  tiempo (el estrobo, seis veces por minuto durante dos segundos: cuatro quintos del tiempo es la base): el estrobo
  de la consola fue el par más parecido de todos los nuevos. Por eso se leían iguales.
- **Lo sutil de la lente no se mide ni se ve.** El lente barato y el foco al pulso quedaron a 1,1 y 0,75 del banco
  limpio; el ojo de pez, que sí se ve, a 1,8.
- **Los gestos de tiempo** (golpe congelado, tartamudeo, paso de cuadro) también miden casi igual que el banco
  limpio, pero a propósito: lo suyo es el movimiento en el golpe.

## Lo que se hizo

- **Variantes** (`variante_de` y `diferencia` en el estilo): el Super 8 de la familia con el sonoro y el pasado a
  VHS; la película en la pared con la de la sábana; la foto de laboratorio con la Fuji y la de la fecha; el VHS en
  el televisor con el televisor solo; y, en una segunda tarjeta («Sí, variantes»), el VHS de la casa con la cámara
  de los 90, la cámara de tubo y la cinta con TBC. El principal se eligió por ser el más general (el Super 8 de la familia, la
  pared, la foto de laboratorio) o el aprobado (el VHS en el televisor; el televisor solo había quedado a medias).
  `estilos` las valida, `guion` no las propone aparte (las nombra junto al principal) y la galería del panel las
  muestra dentro de su principal.
- **Gestos** (`"gesto": true`, la cadena sólo con los aparatos del gesto y `sobre`, la base de su muestra):
  `componer` en `analogo.py` pone la consola antes de la primera cinta (mezcla lo que se graba) y la casetera
  después de la última (reproduce lo grabado); sin cinta, al final, antes de la pantalla. `--gesto <id>` suma
  uno o más a cualquier `--cadena`. La base de cada gesto es la misma cinta de antes, así que su muestra no cambia
  (lo prueba `test_un_gesto_de_la_galeria_dibuja_la_misma_cadena_que_antes_de_ser_gesto` y lo midió el probador).
  En la galería son su propia familia, «gestos», para elegir entre dos.
- **La lente:** el lente barato pasó de aberración 2, viñeta 0,7, foco 0,8 y barril 0,2 a 3, 1, 2 y 0,45; el foco
  al pulso, de 2 a 5. Medidos de nuevo contra el banco limpio, el lente barato pasó de 1,10 a 1,51 y el foco al
  pulso de 0,75 a 1,47 (el ojo de pez, que se ve, está en 1,77). Volvieron a la mesa para juzgarlos.

## Lo que dijo el probador

Los ocho gestos, dibujados con su base y su gesto por separado, salieron **iguales a su referencia** (parecido
1,000 en los tres cuadros): la muestra que Miguel juzgó es la misma. El lente barato y el foco al pulso, con la
receta nueva, tienen referencia nueva.

## Lo que dijo Miguel

- «Hay muchos que son muy parecidos entre si»
- En tarjetas: «Uno por grupo», «Como gestos aparte», «Subirlos hasta que se vean» (las tres recomendadas), y
  «Sí, variantes» para la cámara de los 90, la cámara de tubo y la cinta con TBC.

## Lo aprendido

- Antes de sumar un estilo, preguntarse si es una variante de otro (cambia un detalle) o un gesto (la misma base con
  un momento encima). Quedó en `estilos/README.md` y en la skill.
- Un efecto que pasa «a ratos» necesita que su muestra lo muestre: en 21 s con un evento cada diez, el que juzga ve
  la base.
