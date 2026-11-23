# 27 · El sonido de los aparatos

**Fecha:** 2026-11-22

## Idea

Mientras se cerraba el 26, Miguel: «Otra cosa, hay efectos que deberían ir acompañados de audios característicos».

Medido en el catálogo: de los 53 estilos de 24 y 25, sólo 8 sonaban distinto (la cinta lineal, el micrófono del
celular, de la webcam y de la cámara de bolsillo, el proyector y la banda magnética), y en todos el aparato sólo
cambiaba cómo suena la canción. Ninguno sonaba **en su momento**: la pausa no hacía clac, el rebobinado no corría,
la antena no tenía estática. Se le propusieron cuatro grupos en una tarjeta y **eligió los cuatro**: la casetera,
la antena y el televisor, la película y las cámaras con la videollamada.

## Material

El banco del probador (La Añoranza). Los sonidos se sintetizan en código, como los de `sonido.py`: nada se grabó ni
se bajó.

## Lo que se hizo

- **`py/montaje/ruidos.py`**: un ruido por aparato, en la perilla `sonido` que ya usaban la cinta, el sensor y la
  película. La casetera (`mecanica`), la antena (`aire`), la pantalla (`parlante`), la cámara (`microfono`) y la
  compresión (`llamada`). Qué suena en cada uno, y por qué, está en el encabezado del archivo y en
  `direccion/ANALOGO.md` («Los ruidos de los aparatos»).
- **Donde se ve, suena.** La pausa y el rebobinado de la casetera son eventos al azar con semilla: `eventos_en`
  recorre las mismas ranuras que la imagen y da los mismos (`analogo._audio_de_aparatos` le pasa a cada aparato su
  lugar en la cadena, `_paso`, que es parte de la semilla). El arranque usa los mismos segundos que la pantalla
  azul y el letrero de PLAY. La llamada pierde el audio en algunas de las capturas donde el códec rompe la imagen.
- **Los estilos que suenan ahora** (17): la pausa, rebobinar y el arranque; la antena lejana, el canal con
  interferencia y la señal que se pierde (antena y parlante); el VHS en el televisor, el televisor solo y el imán
  (parlante); la cámara de los 90, la de tubo y el video de boda (micrófono); la videollamada (llamada); el Super 8
  de la familia, el del filtro puesto, el 8 mm en blanco y negro y la película desteñida (el proyector, que ya
  existía).
- `sonido: "ninguno"` es lo de fábrica: un estilo que no lo pide suena como antes (lo prueba
  `test_sin_sonido_el_audio_pasa_igual`).

## Lo que midió Claude (que no oye)

Con una canción de prueba (un tono y ruido), en `py/pruebas/test_ruidos.py` y antes de tocar los estilos:

- Los eventos del sonido coinciden con los de la imagen en cada centésima de 30 s (cero desacuerdos).
- En la pausa, la canción baja más de 15 dB y entra el clac; el arranque calla la canción hasta el PLAY y después
  la deja entera.
- La antena sisea más con más nieve; el parlante del televisor deja pasar 1 kHz casi igual, resuena cerca de
  400 Hz y corta los graves (60 Hz) y el brillo (9 kHz) más de 10 dB.

Después, sobre las 17 muestras del probador (todas salieron, ninguna falló): un espectrograma de cada una con, debajo,
cuánto cambia la imagen cuadro a cuadro. En la pausa del VHS la canción desaparece en dos bandas que terminan justo
donde la imagen salta al soltarse la pausa; en rebobinar, dos bloques de ruido con el chirrido que sube, en los
mismos segundos en que corre la imagen; en el arranque, silencio y mecánica hasta los 2 s y la canción entra con la
imagen. El proyector suena unos 17 dB bajo la canción. La señal que se pierde es la más ruidosa: el siseo tapa buena
parte de la canción (como la imagen, que es casi toda nieve), y la videollamada se corta seguido: los dos quedan para
el oído de Miguel.

Las muestras con sonido están en la mesa (versión 9), en «por juzgar», cada una con lo que suena.

## Lo que dijo Miguel

- «Otra cosa, hay efectos que deberían ir acompañados de audios característicos»
- En la tarjeta: los cuatro grupos (casetera, antena y televisor, película, cámaras y videollamada).
- En la mesa: **los diecisiete sí**, la señal que se pierde y la videollamada incluidas.
