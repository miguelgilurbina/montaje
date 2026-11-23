# 28 · Gestos de la película

**Fecha:** 2026-11-22

## Idea

Miguel pidió revisar todo lo que había en la galería y mapear qué más se podía hacer. El repaso y el mapa quedaron en
una página aparte (el «Mapa de la galería»), con once territorios. En las tarjetas eligió abrir cuatro: los gestos de
la película, la fotografía de antes, la imprenta y la radio. Pidió juzgarlos todos juntos al final («Al final juzgo
todos»), y además un lugar para anotar sus ideas y moldes de trabajo.

Éste es el primero. La casetera ya tenía sus gestos (la pausa, el rebobinado, el arranque) desde el 26; la película no
tenía ninguno. Aquí van los suyos: lo que le pasaba a la película dentro del proyector, como un momento encima de
cualquier base.

## Material

El banco del probador (La Añoranza). Todo se dibuja y se sintetiza en código: nada se grabó ni se bajó.

## Lo que se hizo

- **`py/montaje/rollo.py`**, el aparato `rollo`, con cinco perillas que son cinco gestos:
  - `quema`: el cuadro se traba, la lámpara lo calienta y se abre un agujero desde un punto, con el borde ampollado y
    tostado, hasta que no queda imagen;
  - `corrido`: el lazo se pierde y la línea entre cuadros recorre la pantalla, con la perforación clara;
  - `cambio`: las dos marcas de cambio de rollo arriba a la derecha, cuatro cuadros cada una, siete segundos entre las
    dos;
  - `empalme`: el salto, la cinta lechosa con su borde y sus burbujas, el destello;
  - `cola`: los últimos segundos del video. Primero la punta velada (naranja), después la cola transparente con su
    mugre, y al final la punta suelta que golpea.
- **El rollo es un gesto** (`GESTOS` en `analogo.py`). Va justo después de la última película de la base, antes del
  proyector: lo que se quema es la película, y la pared lo muestra.
- **La cola necesita saber dónde termina el video.** El contexto de cada cuadro ahora lo sabe (`ctx.fin`), y el
  sonido también (`_fin`).
- **El sonido** (`rollo` en `ruidos.py`, `sonido: proyector`):
  - la quema: el mecanismo que se traba, el motor que se ahoga y la película que crepita;
  - el cuadro que se corre: la uña que salta las perforaciones;
  - el empalme: un chasquido;
  - la cola: la punta suelta golpeando cada vez más lento.

  Los eventos son los mismos que los de la imagen: la misma semilla y las mismas ranuras.
- **Cinco estilos**, todos gestos:
  - `la-pelicula-que-se-quema` y `el-cuadro-que-se-corre`, sobre la película en la pared;
  - `cambio-de-rollo`, sobre un 16 mm en pantalla;
  - `el-empalme` y `se-acaba-el-rollo`, sobre el Super 8 de la familia.

  Cada uno con su semilla elegida para que el gesto caiga dentro de la muestra.

## Lo que midió Claude (que no oye)

En hojas de cuadros sueltos y en las muestras del probador:

- **La quema:** en el primer intento salía en islas sueltas y ya estaba toda blanca a la mitad. Ahora es una burbuja
  que se abre con el borde continuo y termina en la luz hacia el 85 % del gesto.
- **El cuadro que se corre:** da dos vueltas en la muestra, en los segundos que dice la cuenta.
- **El cambio de rollo:** las dos marcas aparecen a los 5,9 s y a los 12,9 s.
- **El empalme:** tres empalmes en los segundos previstos.
- **La cola:** el último cuadro de la muestra cae en la punta suelta.

En los espectrogramas, el traqueteo del proyector de la base tapa casi todo. Por eso el chasquido del empalme subió a
6 dB bajo el nivel de la canción (estaba 13 dB abajo y casi no se oía), y el golpe y el crepitar de la quema y la punta
de la cola también subieron. El traqueteo rápido del cuadro que se corre sí se ve en sus dos tramos.

Las pruebas están en `py/pruebas/test_territorios.py`:

- el rollo cae en su lugar de la cadena;
- sin gestos no toca la imagen;
- la quema sale del cuadro trabado y termina en la luz;
- la cola sólo aparece al final;
- el empalme suena donde salta.

## Lo que dijo Miguel

- «Me gustaría revisar todo lo que tenemos hasta ahora y mapear que otra cosa podemos hacer para expander nuestra
  galería de efectos y filtros.»
- En las tarjetas eligió los cuatro territorios: Gestos de la película, Fotografía de antes, Imprenta y La radio.
- «Al final juzgo todos.»
- En la mesa (2026-11-23): la película que se quema, el cambio de rollo, el empalme y se acaba el rollo, **sí**; el cuadro que se corre, **a medias** (sin decir por qué todavía).
