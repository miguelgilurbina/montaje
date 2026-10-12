# Sonido

## La música

- **La canción de la serie:** «Tonada de Luna Llena (Basic Need Remix)», Simón
  Díaz × Basic Need (Wonderwheel Recordings), versión de 4:53. 89,1 BPM; el tramo
  2:30–3:32 está en **mi menor** (estimado por `sonorizar`). Hay un corte casi en
  silencio en 2:57–3:04. **Los derechos los resolvió Miguel.**
- **Para qué está:** Miguel: «algo que nos de el tempo de edición de las fotos».
  La música es la que corta: el montaje cae en sus golpes y compases.
- **Cómo se elige un tramo:** Miguel: «secciones con claros ups and downs», «de
  más lento a más alto». Un tramo que construye, cae en un corte y vuelve.
- En pantalla, la canción va acreditada en el texto del posteo y, cuando exista,
  en el «sonando ahora» (ver MOTIVOS.md).

## Los efectos (propuesta, experimento 09)

**El sonido subraya, no compite.** La canción es la protagonista; los efectos
sólo aparecen donde la imagen hace algo distinto (un momento) y desaparecen.

- **Hechos en código** (`py/montaje/sonido.py`), sin muestras grabadas: no hay
  derechos que pedir, y se pueden afinar.
- **Afinados a la canción:** lo que tiene altura (el impacto, la campana, los
  rebotes) se afina a la tónica del tramo.
- **Después del montaje:** `sonorizar` toma un render cerrado y le suma la capa
  en segundos, sin volver a renderizar la imagen.

| Momento | Efecto | Nivel de pico | Frente a la canción |
|---|---|---|---|
| destacado | **impacto** grave (la canción baja 3 dB un instante) | −9 dBFS | a la par |
| destacado, al volver a su lugar | **soplo** suave | −11 | −13 dB |
| firma | impacto + **campana** en la tónica | −12 | a la par |
| ráfaga / carrusel | **subida** de un golpe y un **obturador** por corte | −8 / −11 | −10 / −20 dB |
| barrido | **soplo** que cruza en el sentido en que se mueve la imagen | −9 | −6 dB |
| salvapantallas | **estática** de radio AM con silbido de sintonía (cama) y **rebotes** afinados en cada borde (esquina: acorde) | −38 RMS / −16 | −10 / −9 dB |

Los niveles se corrigen por proyecto (`sonido.efectos` en proyecto.json, en dB,
o `false` para apagar uno).

## Masterización

`paquete` entrega el audio a **−14 LUFS integrados, pico real −1 dBTP**, con
ganancia pareja (se mide primero, `loudnorm` lineal en dos pasadas). YouTube baja
a −14 lo que llega más fuerte, así que entregar ahí no pierde nada; el pico de
−1 evita que la compresión de la red recorte. Los renders quedan al nivel de la
canción (−10,9 LUFS en el 05).

Las cortinas (`ensamblar`) se nivelan al programa antes de unirse.

## Por hacer

- **Voz en off:** la voz de Miguel; antes de grabar, una voz sintética de prueba
  para medir tiempos (la de Windows, sin claves); Whisper marca el tiempo de
  cada palabra para cortar sobre ellas. El texto de los subtítulos sale del
  guion, no de lo que Whisper oye.
- **Ambientes por familia de imágenes** (agua, desierto, ciudad…), muy bajos,
  según las descripciones del catálogo.
- **Firma sonora de Curiana Radio:** un motivo corto propio (escrito en código)
  para cortinas y cierres.
