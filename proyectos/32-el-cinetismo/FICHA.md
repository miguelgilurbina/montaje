# 32 · El cinetismo

**Fecha:** 2026-11-23

## Idea

Después de los cuatro territorios del mapa, Miguel pidió: «Tu busca más por favor». La búsqueda trajo ocho
territorios nuevos, cada uno con sus fuentes (en el mapa y en `PROPUESTAS.md`, K8 a K15). Miguel eligió abrir los
cuatro recomendados y juzgarlos al final.

Éste es el primero: las técnicas del arte cinético venezolano llevadas al video, sin copiar obras. En el cinetismo, el
ojo pone el movimiento y el color. Las fuentes que se miraron:

- [MoMA, Soto](https://www.moma.org/collection/works/91773);
- [Centre Pompidou, Soto](https://www.centrepompidou.fr/es/ressources/oeuvre/cjz8dk);
- [Cruz-Diez](https://mymodernmet.com/es/carlos-cruz-diez/).

## Material

El banco del probador (La Añoranza). Todo en código.

## Lo que se hizo

**`py/montaje/cinetico.py`**, el aparato `cinetico` (perilla `tecnica`):

- `vibracion`: la imagen hecha de líneas verticales fijas, más gruesas en lo oscuro, en noche sobre hueso. Las
  líneas no se mueven y lo que se mueve detrás vibra en la trama.
- `moire`: esa trama y, encima, otra pareja, girada unos grados, que gira y corre despacio (`deriva`). Las ondas del
  moiré cruzan la imagen.
- `induccion`: dos franjas negras y claras según el brillo, y la tercera de color, de la paleta, según el tono de la
  imagen en ese lugar. Las de color corren despacio.

**Tres estilos:** `vibracion`, `moire` e `induccion-del-color`. No tienen sonido propio.

## Lo que midió Claude (que no oye)

- En la primera inducción, la franja de color salía marrón en lo oscuro: elegía el color más cercano también por su
  brillo. Ahora lo elige sólo por el tono, y en lo oscuro la franja también se apaga.
- Las pruebas (`test_buscados.py`):
  - la vibración usa sólo sus dos tintas, y lo oscuro lleva más línea;
  - el moiré cambia con el tiempo, y no cambia si no tiene `deriva`.

## Lo que dijo Miguel

- «Tu busca más por favor»
- En la tarjeta: los cuatro recomendados de lo que se encontró buscando. Se juzgan al final.
