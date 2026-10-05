# 03 · Collage infinito

**Fecha:** 2026-10-04/05

## Idea

Pedido de Miguel después del 02: «uno más corto… de más lento a más alto»,
«una muestra más rápida pero a la vez más nítida: las fotos deben aparecer al
100 % con su detalle, ya que cada una es el producto de Curiana Radio», «cuando
digo superpuestos es literal superpuestos, estilo collage, y que la imagen se
vaya llenando con un collage infinito, y que vaya más rápido ya que iría con el
tempo más fino de la canción. 1 min.»

- **Collage literal:** cada imagen cae encima como un papel con sombra y se
  queda. Opaca, sin mezcla ni calado, **nunca más grande que su tamaño nativo**.
- **Infinito:** la cámara se aleja todo el tiempo (de 1 a 0,42); lo viejo se
  achica debajo, lo nuevo llega grande arriba. Cada imagen busca el lugar que
  lleva más tiempo sin cubrirse: el cuadro se llena parejo.
- **Tempo fino:** densidad por compás según avance y energía — 1 por compás en
  la intro, 1 por golpe al entrar la batería, corcheas, semicorcheas; el compás
  bajo antes del final respira (por golpe) y el último explota.
- **Selección:** 214 de las 821, una por generación de Midjourney (sin
  variantes repetidas), de oscuras a claras con la subida y encadenadas por tono.

## Material

- **Imágenes:** biblioteca `galeria-curiana`.
- **Música:** la Tonada (Basic Need Remix), tramo **0:10.7–1:15.4** (64,7 s,
  24 compases): 2 compases de intro, la batería entra con anacrusa, sube de 0,45
  a 0,95 y cierra en el golpe más fuerte. Mismos derechos que en el 02.

## Técnica nueva

- **Tramos de canción** (`tramo`, `fundido_audio`, `fase_compas`).
- **Imágenes tapadas:** se calcula cuándo cada papel queda cubierto entero y deja
  de dibujarse; el render del tramo denso pasó de 3,4 s a 0,4 s por cuadro.

## Lo que salió

En `~/Videos/montaje/03-collage/render/`: `collage-1080.mp4` (1080p),
`medir-58-60.mp4` (tramo de medición); `hojas/cuadro-59s.png` (un cuadro a
resolución completa).

También `collage-1080-compartir.mp4`: la misma a 1080p en dos pasadas a 3,2 Mb/s
(27 MB), para mandar por chat (límite de 30 MB).

## Lo que dijo Miguel

> «Excelente.»

> «Siento que tienen que haber momentos donde cambiamos el tempo o el estilo de
> mostrar imágenes, como que deberían haber animaciones que especializan a
> alguna imagen.»

## Aprendido

- Es lo que Miguel buscaba con «superpuesto»: collage nítido, cada imagen legible.
- Le falta **contraste en el tiempo**: un solo tratamiento durante todo el minuto,
  aunque acelere, se siente parejo. De ahí sale el 04.
