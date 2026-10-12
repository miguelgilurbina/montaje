# 10 · Señal: fallas de transmisión sobre el 09

**Fecha:** 2026-10-12

## Idea

Miguel propuso integrar al harness un flujo **«Video Glitch» (Carena + JVC)**: un
aparato que rompe la señal (Carena MVP-4000) y otro que la estabiliza (JVC
KM-250, como un TBC). No tiene los aparatos («no los tengo»), así que se hace en
digital, con ffmpeg, sobre el render del 09 (imagen del 05 + su capa de sonido).

Decisiones:

- **No se averían las imágenes en sí** (la opción A de su documento): el glitch
  quedaría pegado en el archivo, igual en cada cuadro, y choca con la regla de
  que las imágenes se vean al 100 %. Las imágenes protagonistas (destacados,
  carrusel) quedan limpias.
- **Fallas acotadas en el tiempo** (su opción B, pero no sobre todo el video):
  sólo donde el video cambia de estado, y cada una vuelve limpia en el golpe.
  La señal ya era un motivo en el sonido (la estática del 09); ahora se rompe
  también la imagen.

| Tiempo | Dónde | Falla |
|---|---|---|
| 23,3–24,4 s | entra el salvapantallas, la canción cae en su corte | la grande: canales de color separados, filas desgarradas, nieve, la imagen rueda en vertical; el logo aparece en medio de la interferencia y engancha limpio |
| 34,2–34,8 s | sale el salvapantallas (con el barrido) | la señal vuelve |
| 58,8–59,3 s | la firma | el logo llega averiado y se estabiliza: el TBC que engancha |

El sonido de cada falla tiene la misma envolvente que la imagen: zumbido de
cabezal a 59,94 Hz, ráfagas de ruido que se abren cuadro a cuadro y la canción
cortada un cuadro aquí y allá.

## Técnica nueva: señal

`python montaje.py senal <p>` (`py/montaje/senal.py`): calcula las fallas a
partir del timeline (el primero de la cadena de `base` que lo tenga: 10 → 09 →
05), arma un filtro `geq` de ffmpeg por falla, encendido sólo en su ventana
(`enable`), y mezcla el sonido. Fuera de las ventanas el video no se toca.
Tarda un minuto. Se ajusta con `senal.intensidad`, `senal.no` (dónde no poner
fallas) y `senal.extra` (fallas a mano).

Un tropiezo útil: `geq` **no recorta** los valores fuera de 0–255; un negativo
da la vuelta y sale blanco (la primera versión pintaba las ventanas de negro y
la nieve salía verde). Cada canal va con `clip(…, 0, 255)`: el `np.clip` que el
documento de Miguel le pedía al JVC resultó necesario, aunque no por el TBC sino
para que la imagen siempre sea legible.

## Lo que salió

En `~/Videos/montaje/10-senal-curiana/`: `render/curiana-3x2-senal.mp4`
(1620×1080, 1:01, −10,9 LUFS), `render/curiana-3x2-senal-compartir.mp4` (27 MB),
`senal/fallas.json` y las hojas `hojas/falla-salva.png`, `falla-vuelta.png`,
`falla-firma.png` (un cuadro cada 2).

## Lo que dijo Miguel

(pendiente)
