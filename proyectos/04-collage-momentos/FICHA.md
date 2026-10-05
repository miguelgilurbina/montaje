# 04 · Collage con momentos

**Fecha:** 2026-10-05

## Idea

Sale de lo que dijo Miguel del 03: «Siento que tienen que haber momentos donde
cambiamos el tempo o el estilo de mostrar imágenes, como que deberían haber
animaciones que especializan a alguna imagen.»

El collage del 03, igual, con **momentos** puestos en compases concretos (se
declaran en `proyecto.json` → `momentos`, y se mueven cambiando el número de
compás):

| Momento | Qué pasa | Por qué |
|---|---|---|
| **Destacado** | el collage se oscurece y **se detiene**; una imagen sube al frente, grande y nítida (nunca más que su tamaño nativo), con un acercamiento lento; al final **vuela** a su lugar en el collage | «especializar» una imagen; el collage que se detiene es el cambio de tempo |
| **Ráfaga** | el collage desaparece y las imágenes pasan **a pantalla completa en cortes secos** al pulso (8 o 16 por compás); luego vuelve el collage | cambio de estilo: del collage al montaje métrico |
| **Barrido** | la cámara salta de golpe a una zona vacía y el collage empieza a llenarse de nuevo | una página nueva; renueva el cuadro |

## La partitura (24 compases del tramo 0:10.7–1:15.4)

| Compás | Tiempo | Qué |
|---|---|---|
| 0–1 | 0:00 | intro: una imagen sola |
| 2–5 | 0:05 | entra la batería: collage por golpe |
| **6** | 0:16 | **destacado** |
| 7–9 | 0:19 | collage, golpe → corchea |
| **10** | 0:27 | **ráfaga** de 8 (corcheas) |
| 11–12 | 0:30 | collage por corchea |
| **13** | 0:35 | **barrido** |
| 14–17 | 0:38 | collage, corchea → semicorchea |
| **18** | 0:49 | **ráfaga** de 16 (semicorcheas) |
| **19** | 0:51 | **barrido** |
| 20–21 | 0:54 | collage por semicorchea |
| **22** | 0:59 | **destacado** en el compás que respira antes del golpe final |
| 23 | 1:02 | el golpe final: collage por semicorchea hasta el corte |

Las imágenes de los destacados las elige el plan (la panorámica más saturada y
de luz media que no se haya usado) salvo que el momento diga `"img": "<slug>"`.
Las de cada ráfaga son una familia de color. Ninguna se repite con el collage.

## Material

- **Imágenes:** biblioteca `galeria-curiana`; 182 en el collage, 2 destacadas,
  24 en ráfagas.
- **Música:** el mismo tramo de la Tonada que el 03.

## Lo que salió

En `~/Videos/montaje/04-collage-momentos/render/`: `momentos-1080.mp4` (render en 4 min) y `momentos-1080-compartir.mp4` (27 MB, para el chat).

## Lo que dijo Miguel

(pendiente)
