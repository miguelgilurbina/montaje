# 01 · Superposición

**Fecha:** 2026-10-04 · **Commit:** 241d895 (el timeline de esa versión es el de esta carpeta)

## Idea

Las 821 imágenes de la galería de Curiana Radio superpuestas en **doble
exposición** (mezcla `screen`) al pulso de la música. Cada imagen entra completa,
en su proporción, con **calado** de bordes; la cantidad de capas a la vez sigue a
la energía (1 en la calma, 4 en el pico). Orden **tonal**: las oscuras a la
calma, las claras a los picos, y por tono dentro de cada sección.

## Material

- **Imágenes:** las 821 de la galería (biblioteca `galeria-curiana`).
- **Música:** pista sintética de prueba de 3 min (`audio/prueba.wav`); la canción
  todavía no había llegado.

## Lo que salió

En `~/Videos/montaje/01-superposicion/render/`:

| Archivo | Qué es |
|---|---|
| `preview-20-50.0.mp4` | primera prueba con rellenos de color (sin imágenes reales) |
| `real-20-50.mp4` | con las imágenes reales, bordes duros |
| `borde-20-50.mp4` | con calado de bordes: la versión que quedó |

## Lo que dijo Miguel

> «hasta ahora me gusta la prueba que hiciste»

> «encontré monótona la edición, es igual en todos lados»

## Aprendido

- El **calado** cambia todo: sin él se ven rectángulos apilados.
- En `screen`, **lo blanco quema**: las imágenes de fondo claro lavan el cuadro.
- Una superposición pareja de principio a fin es **textura, no estructura**: sirve
  para un tramo, no para un video entero. De ahí salió el 02.
