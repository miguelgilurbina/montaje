# 34 · El color del cine mudo

**Fecha:** 2026-11-23

## Idea

El tercero de los cuatro territorios que se encontraron buscando (la historia está en la ficha del 32): cómo se le
daba color a la película antes del color. Las fuentes que se miraron:

- [Film tinting](https://en.wikipedia.org/wiki/Film_tinting);
- [The Bioscope](https://thebioscope.net/2008/07/05/colourful-stories-no-12-tinting-and-toning/);
- [George Eastman Museum](https://www.eastman.org/technicolor/technology/two-color-process).

Las convenciones del tintado no eran fijas, y las fuentes no coinciden: el azul para la noche y el rojo para el fuego
sí se repiten; el ámbar o el amarillo para los interiores, no.

## Material

El banco del probador (La Añoranza). Todo en código.

## Lo que se hizo

**`py/montaje/cinemudo.py`**, el aparato `tinte` (perilla `modo`). Va después de la película:

- `tintado`: lo claro toma el color y lo negro queda negro.
  - Con `tinta: auto`, el color sale de la escena: el azul para lo oscuro, el ámbar para lo cálido, el rojo para lo
    que arde, el verde para el campo, y el sepia para lo demás.
  - Recuerda unos cuadros para no titilar.
  - Lo elige mirando el cuadro como entró a la cadena (`ctx.original`, nuevo), porque la copia que le llega ya es en
    blanco y negro.
- `virado`: lo oscuro toma el color (sepia, azul, verde, rojo) y lo claro queda limpio.
- `dos-colores`: los dos tintes de los años 20, sin azules de verdad.
- `kinemacolor`: el rojo de este cuadro y el verde del anterior: lo que se mueve deja dos franjas.

**Cuatro estilos**, todos sobre película de 16 mm con el proyector:

- `pelicula-tintada`;
- `pelicula-virada`;
- `pelicula-de-dos-colores`;
- `dos-colores-que-se-corren`.

## Lo que midió Claude (que no oye)

- En la muestra, la playa de noche sale azul y la escena del jardín, verde: el tintado automático cambia de color con
  la escena.
- Las pruebas (`test_buscados.py`):
  - el tintado deja el negro negro y tiñe lo claro;
  - el automático elige azul para la noche y ámbar para la lámpara, aunque la copia sea gris;
  - el virado y los dos colores, sin azul;
  - la barra que se mueve deja dos franjas, y la quieta no.

## Lo que dijo Miguel

- «Tu busca más por favor»
- En la tarjeta: «El color del cine mudo», con los otros tres. Se juzga al final.
