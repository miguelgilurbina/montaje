# 13 · Variaciones (1:1)

**Fecha:** 2026-10-21

## Idea

Sobre el 12 (collage), Miguel: «no me gusta que usemos collage, la idea es que
usemos todas en seguidillas, piensa que todas tienen el mismo formato, las cree
en base a midjourney-editor-1792552364848 en la página de edits de midjourney,
por lo que siguen un patrón, y más bien, podríamos intercalar la "original" de
vez en cuando. Ahora que lo pienso me gusta más la versión de la canción A.
[…] todas estas imágenes deben ir una encima de la otra, ocupando 100% del
viewport 1:1».

Las 275 imágenes son **variaciones de una sola**: la original es una S
serpenteante (río azul y fachadas amarillas) y casi todas conservan esa forma,
vuelta selva, pirámide, mazmorra, lava o patrón geométrico. Puestas una tras
otra a pantalla completa, en los cortes rápidos la imagen parece transformarse:
**animación por variaciones**.

## Técnica nueva: el modo `secuencia`

`py/montaje/secuencia.py`:

- **Orden por parecido:** cada imagen va seguida de la más parecida (forma y
  color en miniaturas de 16×16) entre las que quedan, pulido con 2-opt; arranca
  en la más parecida a la original. El recorrido termina, además, cerca de ella.
- **La original vuelve** en el «uno» de los compases pedidos (`original_en`): el
  inicio de cada frase de 8 compases. En la calma se queda el compás entero; con
  ritmo, un golpe. Y cierra el video (`cierre_golpes`), respirando un poco
  mientras la canción se apaga.
- **Se usan todas, una vez cada una:** los cortes por compás siguen a la energía
  (con `contraste`) y se escalan para que entren las 275. Caen en la rejilla del
  golpe (hasta 4 por golpe = semicorcheas); dentro de un compás, más cortes
  hacia el final.
- **Calma con fundido, ritmo con corte seco.**

Para eso, `Montaje.tsx` ahora hace corte seco de verdad cuando `entrada` es 0
(antes la imagen tardaba un cuadro en aparecer).

## Música

Tramo **A** de «Broken Like An Angel» (Dollybraid): 0:05.83–1:05.25 (59,4 s),
`fase_compas` 0 (coincide con el análisis de la canción entera), fundidos 0,3 /
1,4 s.

| Compases | Tiempo | Qué |
|---|---|---|
| 0 | 0:00 | la original, quieta, en el silencio |
| 1–2 | 0:02 | dos variaciones con fundido encadenado |
| 3–7 | 0:06 | entra el pulso: una por golpe; la original en el compás 4 |
| 8–14 | 0:17 | corcheas a semicorcheas; la original en el 12 |
| 15–25 | 0:32 | semicorcheas (8 por segundo); la original en el 20 |
| cierre | 0:56 | la original hasta el final |

280 cortes (275 variaciones + 5 veces la original); la más breve dura 3 cuadros.

## Lo que salió

`~/Videos/montaje/13-variaciones/render/preview.mp4` (540×540, 1:00; render en
51 s).

## Lo que dijo Miguel

(pendiente)
