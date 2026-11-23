# 29 · Fotografía de antes

**Fecha:** 2026-11-22

## Idea

El segundo de los cuatro territorios que Miguel eligió abrir en el mapa de la galería (la historia está en la ficha
del 28). La película ya cubría el rollo y la copia de laboratorio. Esto va más atrás, a los procesos del siglo XIX, y
más al costado, a la foto como objeto de la casa.

## Material

El banco del probador (La Añoranza). El banco es de clips: las copias (la instantánea, el fotomatón, la tarjeta) se
pensaron también para fotos, y quedan por probar con fotos de verdad (G5 en `PROPUESTAS.md`).

## Lo que se hizo

**`py/montaje/fotografia.py`**, con dos aparatos de imagen.

`placa` (perilla `proceso`):

- `cianotipo`: el azul de Prusia, las pinceladas de la emulsión en el borde, la fibra del papel.
- `colodion` (el ferrotipo):
  - sensible casi sólo al azul, así que el cielo sale blanco y lo rojo, negro;
  - el lente de la época, nítido al centro y arremolinado en los bordes;
  - el borde donde corrió el colodión y la esquina del dedo;
  - las manchas de plata;
  - con `exposicion`, lo que se mueve se borra, como en las exposiciones largas.
- `daguerrotipo`: la plata como espejo, que se ve positiva o negativa según cómo se mueve la placa (`angulo`), con el
  velo de colores del óxido en el borde. Con `marco: estuche`, el paspartú de bronce.
- `linterna`: la placa de vidrio pintada a mano y proyectada, en su máscara redonda.

`copia` (perilla `forma`):

- `instantanea`: el marco blanco con el borde de abajo ancho. Con `revelado`, la imagen aparece desde el gris
  verdoso: primero la luz, después el color.
- `fotomaton`: la tira de cuatro, acostada. El cuadro que viene se ve en vivo, cada flash lo congela, y la tira se
  llena y empieza otra vez.
- `estereo`: las dos fotos a la albúmina, la de la derecha un poco corrida, con las puntas redondeadas, sobre el
  cartón ocre con sus manchas.

**El sonido** (`copia` en `ruidos.py`, `sonido: camara`):

- la instantánea: el obturador y el motor que la expulsa, al principio;
- el fotomatón: el flash y la carga que silba, en los mismos segundos en que la imagen dispara.

**Siete estilos:** `cianotipo`, `ferrotipo`, `daguerrotipo`, `linterna-magica`, `la-instantanea`, `fotomaton` y
`tarjeta-estereoscopica`.

## Lo que midió Claude (que no oye)

**Ajustes antes de las muestras.**

- El primer cianotipo tenía la fibra del papel tan fuerte que parecía lluvia sobre la imagen, y el borde del pincel
  salía como una nube. La fibra bajó a un 1 %, el borde quedó casi derecho y los trazos sólo aparecen donde la
  emulsión se acaba.
- A la linterna casi no se le veía la pintura: los colores subieron y quedaron en pocos tonos, como la paleta de un
  pintor.

**El fotomatón.** Recuerda los cuadros que congeló en la vuelta. Con cinco intervalos se pasaba del tope de memoria
(242 cuadros a 30 por segundo, el tope es 240): ahora cuenta desde el primer flash (cuatro intervalos y medio) y el
`intervalo` llega hasta 1,7 s.

**En las muestras se ve:**

- la instantánea que se revela entre los 0 y los 6 s;
- el fotomatón que se llena flash por flash, con el silbido de cada carga en el espectrograma;
- el daguerrotipo que pasa a negativo;
- el ferrotipo que borra el brazo que saluda.

**Las pruebas:**

- cada proceso da una imagen del tamaño de la salida;
- el cianotipo es azul;
- la instantánea aparece de a poco;
- el fotomatón suena donde dispara.

## Lo que dijo Miguel

- En la tarjeta: «Fotografía de antes», junto con los otros tres territorios. Se juzga al final.
- En la mesa (2026-11-23): el cianotipo, el ferrotipo, la linterna mágica, la instantánea, el fotomatón y la tarjeta estereoscópica, **sí**; el daguerrotipo, **a medias** (sin decir por qué todavía).
