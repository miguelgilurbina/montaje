# 08 · Programa con interludios (3:2)

**Fecha:** 2026-10-05

## Idea

Miguel, sobre sus videos de Curiana Radio hechos con Gemini: «tenían audio, esos
videos los pensé tipo para que sean como "interludios" estilo las propaganda de
Locomotion». En el 07 se usaron mudos, como parte de la canción: no era eso.

Ahora son **cortinas** (en TV: *idents* o *bumpers*): cortan el programa con su
propio sonido y la canción se detiene mientras pasan.

| Tramo | Qué |
|---|---|
| 0:00–0:08 | **cortina de apertura**: la portada CURIANA (`intro-gemini`) |
| 0:08–0:32 | **programa**: el collage del 05, compases 0–8 |
| 0:32–0:40 | **cortina** con el logo y destellos (`logo-destellos`), justo donde la canción cae en su corte: la «tanda» reemplaza los tres compases de silencio |
| 0:40–1:07 | **programa**: compases 12–21; vuelve con el logo rebotando un compás y la música explota |
| 1:07–1:15 | **cortina de cierre**: el logo que se arma desde partículas (`logo-particulas`) |

## Técnica nueva: ensamblar

`python montaje.py ensamblar <p>` (`py/montaje/ensamblar.py`): toma el render de
otro experimento como programa, lo corta en compases y le intercala interludios.
No re-renderiza nada (54 s). Los interludios se recortan (cuadrado central, sin la
marca «Veo»), se agrandan al alto del cuadro y su audio se **nivela al del
programa** (`loudnorm`, de −12,9 a −10,9 LUFS); cada empalme lleva un fundido de
audio de 40 ms.

## Material

- **Programa:** `05-collage-curiana/render/curiana-3x2.mp4`.
- **Cortinas:** los tres videos de Miguel en `galeria-curiana/video/`.

## Lo que salió

En `~/Videos/montaje/08-programa-interludios/render/`:
`programa-interludios-3x2.mp4` (1620×1080, 1:15) y `programa-interludios-compartir.mp4` (27 MB).

## Lo que dijo Miguel

(pendiente)
