# 06 · Reel en cinta (9:16, loop)

**Fecha:** 2026-10-05

## Idea

Pedido de Miguel: «hagamos una vertical para reels… puede ser más en loop para
que el reel sea interminable y muy repetible», con estilos distintos y los
momentos entre medio.

Un estilo nuevo, **cinta** (`py/montaje/cinta.py`): las imágenes van en columna,
como un feed, y la cinta **sube un paso por golpe** (aterriza en el golpe). Cada
compás dice cuántos pasos da o qué momento ocupa su lugar:

| Compás | Qué |
|---|---|
| 0–1 | por golpe |
| 2 | **doble tiempo** (por corchea) |
| 3 | **destacado de marca**: la imagen del centro sale al frente y vuelve |
| 4 | por golpe |
| 5 | doble tiempo |
| 6 | **ráfaga de 16 imágenes de marca** a pantalla completa |
| 7 | por golpe, y la última llegada es la primera imagen: **loop** |

- **Loop sin costura:** la cinta es cíclica (32 imágenes, 32 pasos). En el último
  cuadro está llegando la primera imagen; el primer cuadro la muestra quieta.
- **Loop de color:** las imágenes recorren el **círculo de color** en orden, así
  que también el color vuelve a donde empezó.
- **Logo:** sello arriba a la izquierda que late en cada compás, y el logotipo
  como una «tarjeta» más de la cinta (lugar 16).
- **Música:** 8 compases de la sección pareja después del corte (3:32.3–3:53.9),
  que empiezan y terminan dentro de la misma sección: el audio también empalma.

## Lo que salió

En `~/Videos/montaje/06-reel-cinta/render/`: `reel.mp4` (1080×1920, 21,6 s, render en 46 s) y `reel-compartir.mp4` (24 MB).

## Lo que dijo Miguel

(pendiente)
