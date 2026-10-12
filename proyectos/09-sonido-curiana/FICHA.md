# 09 · Sonido sobre el collage Curiana (3:2)

**Fecha:** 2026-10-12

## Idea

Después de revisar cómo otros hacen películas con Claude (2026-10-08), Miguel dijo
«Vale» a empezar por dos cosas: la biblia de dirección (`direccion/`) y **la capa
de sonido**, que estaba pendiente desde el principio («Me gustaría complementar
con audios, estilo sonidos y música»).

Primera prueba: el **render del 05**, sin tocar la imagen, con efectos que
subrayan cada momento. La canción sigue mandando; los efectos aparecen sólo
cuando la imagen hace algo distinto.

## La partitura de sonido

| Tiempo | Momento | Sonido |
|---|---|---|
| 8,3 s | destacado de marca | **impacto** grave (la canción baja 3 dB un instante) |
| 10,6 s | la imagen vuelve a su lugar | **soplo** suave |
| 15,2 s | antes de la ráfaga de retratos | **subida** de un golpe |
| 15,9–18,3 s | ráfaga de 8 retratos | **obturador** en cada corte |
| 23,9–34,5 s | silencio con salvapantallas | **estática** de radio AM con silbido de sintonía; **rebotes** cada vez que el logo toca un borde |
| 34,2 s | barrido | **soplo** que cruza de derecha a izquierda, como se mueve la imagen |
| 42,6 s | destacado de marca | impacto |
| 45,0 s | vuelve a su lugar | soplo suave |
| 50,0 s | antes del carrusel | subida |
| 50,7–53,4 s | carrusel de 16 imágenes de marca | obturador por corte |
| 58,8 s | firma | impacto + **campana** |

Tonalidad estimada del tramo: **mi menor**. El impacto cae en mi grave; la
campana, en mi; los rebotes en los costados suenan si (la quinta), arriba y
abajo mi, y en una esquina el acorde.

## Técnica nueva: sonorizar

`python montaje.py sonorizar <p>` (`py/montaje/sonido.py`): lee los momentos y el
logo del timeline, sintetiza cada efecto en código (numpy, sin muestras),
lo afina a la tónica, lo mezcla sobre el audio del render y copia el video sin
re-renderizar (unos 15 s). Deja también la pista de efectos sola
(`sonido/efectos.wav`) y un dibujo de la mezcla (`analisis/sonido.png`) para
mirarla. Los niveles se corrigen en `sonido.efectos` (dB por efecto).

Y en `paquete`: masterización a **−14 LUFS, pico real −1 dBTP** (el reel 06 pasó
de −11,3 a −14,0 LUFS con ganancia pareja).

## Material

- **Imagen y canción:** `05-collage-curiana/render/curiana-3x2.mp4` (−10,9 LUFS).
- **Efectos:** sintetizados; sin derechos de terceros.

## Lo que salió

En `~/Videos/montaje/09-sonido-curiana/`:
`render/curiana-3x2-sonido.mp4` (1620×1080, 1:01; −10,9 LUFS, pico −0,7 dBTP) y
`render/curiana-3x2-sonido-compartir.mp4` (27 MB).

Cuánto suena cada efecto frente a la canción (RMS en sus 100 ms más fuertes):
impacto ≈ a la par, campana +2 dB, soplo del barrido −6, subida −10, estática −10,
rebotes −5 a −10, soplo de vuelta −13, obturador −20 (un clic: se oye por su pico,
no por su RMS).

**Claude no puede oír la mezcla**: los niveles están medidos, no escuchados. El
oído de Miguel decide.

## Lo que dijo Miguel

(pendiente)
