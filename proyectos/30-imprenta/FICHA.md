# 30 · Imprenta

**Fecha:** 2026-11-22

## Idea

El tercero de los cuatro territorios que Miguel eligió abrir en el mapa de la galería (la historia está en la ficha del
28). Estaba anotado como G7 en `PROPUESTAS.md`: «la voz serigráfica de las tintas del arte». Las tintas por defecto
son las del arte de Curiana, sobre el hueso (`direccion/PALETA.md`).

## Material

El banco del probador (La Añoranza). Todo en código.

## Lo que se hizo

**`py/montaje/imprenta.py`**, el aparato `imprenta` (perilla `tecnica`):

- `serigrafia`: tres tintas planas y opacas, oro, rojo e índigo, una encima de otra. Cada una tiene su registro un
  poco corrido y la tinta no cubre pareja.
- `riso`: dos tintas transparentes, eléctrico y rojo, en trama gruesa y cada una en su ángulo. Donde se pisan se
  oscurecen. El grano es del máster (fijo) y el registro baila más.
- `trama`: el diario. Cian, magenta, amarillo y negro en puntos, cada color con su trama girada (15°, 75°, 0°, 45°),
  sobre el papel gris.
- `fotocopia`: blanco y negro quemado, con:
  - el tóner que mancha y salpica;
  - las rayas del tambor, siempre en el mismo lugar;
  - la sombra de la tapa abierta;
  - con `copias`, la copia de la copia.

**Cada impresión es un cuadro.** Con `cuadros` (8 por segundo), el registro y la tinta cambian a saltos, como una
animación impresa. Con 0 cambian en cada cuadro del video.

**El sonido** (`imprenta` en `ruidos.py`, `sonido: maquina`) es la máquina andando a su propio ritmo, debajo de la
canción:

- la fotocopiadora: la luz que barre y el clic de cada copia;
- la riso y la rotativa: el golpe del tambor y la hoja que sale;
- la serigrafía: la rasqueta.

**Cuatro estilos:** `serigrafia`, `risografia`, `tramado-del-diario` y `fotocopia`.

## Lo que midió Claude (que no oye)

**La riso costó tres vueltas:**

1. El grano al azar en cada pixel se leía como estática de video.
2. Con el grano fijo y más grueso se perdían las formas.
3. Quedó como trama de puntos, una por tinta en su ángulo, y ahí se lee como una risografía a dos tintas.

La fotocopia tenía el negro demasiado ruidoso: el tóner bajó a un 7 % de desparejo y la salpicadura a un tercio.

**La trama.** Los puntos cubren lo que dice el tono: con 10 %, 30 % y 60 %, la tinta cubre lo mismo con menos de 4
puntos de diferencia (es una prueba).

**Las pruebas:**

- una impresión dura lo que dicen sus `cuadros`;
- la fotocopia es blanco y negro.

**El sonido** queda bajo: entre 21 y 30 dB bajo la canción, la máquina «debajo». Si no se oye, se sube.

## Lo que dijo Miguel

- En la tarjeta: «Imprenta», junto con los otros tres territorios. Se juzga al final.
