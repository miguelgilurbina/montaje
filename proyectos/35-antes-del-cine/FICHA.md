# 35 · Antes del cine

**Fecha:** 2026-11-23

## Idea

El cuarto de los territorios que se encontraron buscando (la historia está en la ficha del 32): los juguetes ópticos
que movían imágenes antes de la película. El zoótropo es el loop original («el reel se repite solo», dijo Miguel en
otro momento). Las fuentes que se miraron:

- [Zoetrope](https://en.wikipedia.org/wiki/Zoetrope);
- [Phenakistiscope](https://en.wikipedia.org/wiki/Phenakistoscope);
- [Chronophotography](https://en.wikipedia.org/wiki/Chronophotography);
- [Lenticular printing](https://en.wikipedia.org/wiki/Lenticular_printing).

## Material

El banco del probador (La Añoranza). Todo en código.

## Lo que se hizo

**`py/montaje/juguetes.py`**, el aparato `juguete` (perilla `modo`):

- `zootropo`: el tambor que gira, con la tira adentro, mirado por las ranuras que pasan, sobre su curva. Un loop de
  doce figuras a doce por segundo. La tira se llena en el primer segundo de cada `ciclo` y después se repite.
- `fenaquistiscopio`: el disco con las figuras en círculo, cada una en su sector. Gira un sector por figura: cada una
  se mueve en su lugar, como se ve por las ranuras.
- `libro`: el libro animado, con el doblez de cada hoja que pasa y el canto de las de abajo.
- `lenticular`: lo de ahora y lo de hace `separacion` segundos, cambiando al inclinar, con el fantasma de las dos y
  el brillo del plástico.
- `cronofotografia`: cada `intervalo` segundos, una pose más de lo claro sobre el negro; las últimas `poses`
  encimadas en una placa.

**El sonido** (`juguete` en `ruidos.py`, `sonido: mecanismo`):

- el tambor con el aleteo de las ranuras;
- el disco;
- las hojas;
- el obturador en cada pose.

**Cinco estilos:** `zootropo`, `fenaquistiscopio`, `libro-animado`, `postal-lenticular` y `cronofotografia`.

## Lo que midió Claude (que no oye)

- En la muestra de la cronofotografía, el brazo que saluda queda en varias poses encimadas, como en las placas del
  siglo XIX.
- En el espectrograma, las hojas del libro son un tableteo parejo. El tambor y el obturador quedan bajos, debajo de
  la canción.
- Las pruebas (`test_buscados.py`):
  - el zoótropo repite su loop;
  - cada pose de la cronofotografía deja su marca;
  - la lenticular muestra a ratos lo de ahora y a ratos lo de hace un segundo.

## Lo que dijo Miguel

- «Tu busca más por favor»
- En la tarjeta: «Antes del cine», con los otros tres. Se juzga al final.
