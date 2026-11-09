# 19 · Añoranza con guion

**Fecha:** 2026-11-09 (laboratorio de la noche)

## Idea

El flujo entero que Miguel busca con los entrenamientos («poder elegir distintos
tipos de edición para videos específicos segun guión»), probado con lo que salió
de la noche: un guion en palabras —de práctica, escrito por Claude; los de verdad
los escribe Miguel— partido en siete tramos por las secciones de la canción, con
un estilo y un material de la galería por tramo. Ver `GUION.md`.

## Técnica nueva

- `tramos` en el montaje de `pulso`: cada tramo (`desde`, `hasta`) pone sus
  perillas encima de las del montaje (largo de frase, fundidos, velocidad,
  ventana, doble exposición, congelado, transformados…).
- `material` en cada tramo: palabras del nombre de los clips que entran (en ronda
  dentro del tramo; un material que vuelve sigue donde quedó).
- Las capas de síntesis con `desde`/`hasta` hacen el resto (cuenta, título, golpe
  de zoom sólo en la banda, campo detrás de la ventana, tinta de postal y fugas en
  la salida, crédito a los 2:40).

## Render

`~/Videos/montaje/19-anoranza-con-guion/render/final.mp4` (3:01, 1620×1080, 24 cps;
16 min de render). La hoja (`hojas/final-01.png`) muestra los siete tramos en su
lugar: la cuenta (0:00), el título sobre el pesquero (0:06), la foto que despierta
en el restaurante (0:12), un clip por compás (0:27–1:13), el ciclista en una
ventana sobre el campo de color (1:15–1:21), el campo en doble exposición
(1:24–2:18), la pareja con estela en el silencio (2:24) y el mar como postal con
«sonando ahora» (2:39).

Con sonido: `final-proyector.mp4` (`proyector`: el traqueteo durante la cuenta, el pop
del 2 y un clac de diapositiva en cada foto que despierta), 16 dB bajo la canción.

## Arreglos del motor (2026-11-09)

La revisión del motor (ver la ficha del 21) cambia esta pieza en tres cosas:

- **Los tramos del guion empiezan donde dicen.** Antes un tramo valía recién desde la primera
  frase que arrancaba dentro de él: «el silencio que se borra» (2:18) empezaba a los 2:22 y «vuelve
  el mar» (2:28), a los 2:30. Ahora el borde de un tramo corta la frase en el «uno» más cercano
  (2:16,9 y 2:27,3).
- **La doble exposición empalma:** de 11 dobles, 10 mostraban el clip que venía entre 0,35 y 1,63 s
  adelantado respecto de donde entraba de verdad, y la imagen saltaba al entrar.
- **La cuenta regresiva** cae en los golpes (el «1» llegaba cinco cuadros tarde).
- Renders con el motor arreglado: `final-arreglado.mp4`, `final-arreglado-proyector.mp4` (los de la noche quedan al lado para comparar).

## Lo que dijo Miguel

(pendiente)
