# 12 · Abstract (1:1)

**Fecha:** 2026-10-21

## Idea

Un video nuevo con material nuevo: 276 imágenes **cuadradas** de Midjourney
(1024×1024; 71 generaciones de 4 variantes) que Miguel dejó en
`~/Videos/montaje/abstract/`: patrones en *trompe-l'œil*, selva amazónica,
pirámides mayas, ciudades, mazmorras medievales, lava, colonias espaciales. La
canción: «Broken Like An Angel» de Dollybraid (4:24, 112 BPM).

Lo que pidió Miguel:

- «tiene que ser máximo de 1 min o 1 min y medio»;
- «tenemos que conseguir la parte de la canción que mejor nos funcione»;
- formato cuadrado.

## Elegir el tramo

La canción se analizó entera: va en frases de 8 compases (~17 s). Se le
propusieron tres tramos cortados en bordes de frase, con su clip para escuchar
y un gráfico de la energía (`~/Videos/montaje/12-abstract/candidatos/`):

| | Tramo | Dura | |
|---|---|---|---|
| A · De cero | 0:06–1:05 | 1:00 | desde casi silencio hasta el primer pico |
| B · La subida | 0:31–1:56 | 1:25 | dos subidas hasta el punto más alto; corta antes de la caída |
| **C · El final** | **2:47–4:08** | **1:20** | pausa corta, la sección más fuerte y el cierre real de la canción |

Miguel eligió **C**. (Claude había recomendado A.) El análisis del tramo solo
detectó mal el «uno» del compás (fase 3); se fijó `fase_compas: 0` desde el
análisis de la canción entera, que alinea las frases con las secciones.

## La partitura

Collage 1080×1080, semilla 12, `silencio: 0.5`.

| Compás | Qué |
|---|---|
| 0–7 | collage por golpe (la pausa y la subida) |
| **8** | **ráfaga de 8 paisajes**: entra la sección fuerte (cuadradas en cuadro: el carrusel ocupa todo) |
| **12** | **barrido** |
| 13–15 | corcheas |
| **16** | **destacado** (un patrón geométrico) |
| 17–23 | corcheas |
| **24** | **ráfaga de 16 abstractas** (el clímax) |
| 25–27 | semicorcheas |
| **28** | **destacado** (una ciudad en trompe-l'œil) |
| 29–33 | semicorcheas, que bajan con la canción |
| **34** | **firma**: una imagen (el sol geométrico) se queda al frente mientras la canción se apaga; el collage queda quieto |

## Técnica nueva

- La fuente `carpeta` usa las imágenes **donde están** si la carpeta está dentro
  de los medios (no duplica 528 MB).
- Lee los **nombres de Midjourney**: el título es el prompt sin parámetros y el
  slug conserva la generación, para no repetir variantes seguidas.
- `TIPOS` también en inglés; el destacado sin imagen elegida ya no exige panorámicas.

## Lo que salió

`~/Videos/montaje/12-abstract/render/preview.mp4` (540×540, 1:20, render en
5 min 42 s). 228 imágenes en el collage.

Para revisar: en el barrido (0:25) la cámara salta a una zona vacía y el cuadro
queda **negro ~0,4 s** hasta que cae la imagen siguiente.

## Lo que dijo Miguel

- «la C», «formato cuadrado».
- Sobre el borrador: «no me gusta que usemos collage, la idea es que usemos todas en seguidillas […] podríamos intercalar la "original" de vez en cuando. Ahora que lo pienso me gusta más la versión de la canción A.» → experimento 13 (secuencia a pantalla completa).
