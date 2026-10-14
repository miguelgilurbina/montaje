# 11 · Aviso de venta con canción neutra

**Fecha:** 2026-10-13

## Idea

Miguel mandó un video hecho afuera (un aviso inmobiliario armado en CapCut:
«Oportunidad de venta», 476×848, 24,6 s, con una pista de música de fondo) y
pidió: «acá este video pero pongámosle una canción que sea neutro».

«Neutro» se tomó en los dos sentidos: **sin derechos de nadie** y **sin
protagonismo**. La canción se **escribe en código** (`componer`): una cama
limpia, afinada y al tempo, hecha en local con numpy, así que es nuestra. Y
reemplaza por completo al audio original, que era sólo música (sin voz: lo
confirmó el espectrograma).

## La canción

Re mayor, 100 BPM, 11 compases, progresión I–V–vi–IV. Capas: pad (acorde por
compás, entrada lenta), arpegio en corcheas con timbre de cuerda pulsada y eco a
corchea con puntillo, bajo en la fundamental, percusión suave (bombo en 1 y 3,
un toque en 2 y 4, charles, maraca a contratiempo). Forma: el primer compás
sólo pad y arpegio, el segundo suma el bajo, del tercero entra la percusión, el
último se queda en la tónica y se apaga con el video. A propósito no tiene una
melodía que se recuerde.

## Técnica nueva

- `python montaje.py componer <p>` (`py/montaje/componer.py`): la canción en
  código; `componer` en proyecto.json (bpm, tonalidad, progresión, semilla).
- `python montaje.py musicalizar <p>` (`py/montaje/musicalizar.py`): le pone una
  pista a un video que ya existe sin tocar la imagen (compone primero si la
  música es la compuesta, con la duración exacta del video); `original` dice
  cuánto queda del audio original; masteriza a −14 LUFS.

## Material

- **Video:** `11-aviso-venta/video/aviso-venta.mp4` (copia del de WhatsApp).
- **Música:** `audio/compuesta.wav`, nuestra.

## Lo que salió

`~/Videos/montaje/11-aviso-venta/render/aviso-venta-cancion.mp4` (−13,9 LUFS,
pico −1,6 dBFS, 24,6 s). Claude no oye la mezcla: la revisó en el espectrograma
(estructura, entradas de cada capa) y por medidas.

## Lo que dijo Miguel

(pendiente)
