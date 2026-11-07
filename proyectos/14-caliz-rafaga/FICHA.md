# 14 · Caliz: la ráfaga de retratos al pulso

**Fecha:** 2026-11-03

**Resultado: rechazado.** La versión congeló los personajes que se movían y Miguel
prefiere el original (ver «Lo que salió mal»). El diagnóstico de abajo queda como
se escribió, con su error.

## Idea

Primer experimento sobre un video **que ya viene editado**. Miguel: «es una
video que ya está preeditado, pero que hay que mejorar […] vamos a ver si tú
puedes encontrar el lugar que tenemos que editar». Es una colaboración: «media
que creamos nosotros con un estudio de edición y creación de ia. Caliz Estudio».

El lugar, en sus palabras: «una parte entre medio donde se ve que hay un reel
rapido de imagenes mientras un video corre». Y la condición: «Pensemos que esto
es lo que tenemos, no quiero pedirme más cosas a caliz».

Al mismo tiempo pidió sumarle al motor «poder crear como sincronización de
video. Para poder generar modificación de video»: este experimento estrena el
comando `sincronizar`.

## Material

- `~/Videos/montaje/calizEstudio/WhatsApp Video 2025-08-08 at 20.30.34.mp4`: la
  copia de WhatsApp del preeditado (960×544, 29,97 cps, 2:02, H.264 Baseline a
  ~2 Mb/s, AAC estéreo). Es todo lo que hay: ni máster, ni capas, ni la canción
  aparte. La biblioteca del proyecto es esa carpeta (`biblioteca: calizEstudio`).
- La música es la del video, sin archivo propio: el audio se copia tal cual.

## Cómo se leyó el video

Sin canción aparte ni capas, todo sale del archivo:

- hojas de contacto cada 0,5 s con la sonoridad de cada cuadro; cortes con el
  detector de escena de ffmpeg (`select='gt(scene,0.25)'`); espectrograma;
- barrido cuadro a cuadro (vacíos, negros, congelados, presencia del marco
  crema) y el pulso con librosa;
- el tramo sospechoso cuadro a cuadro (tira a 10 cps) y, dentro de él, la
  diferencia sólo en la franja central para fechar cada retrato al cuadro.

## El diagnóstico

En 1:13.5–1:17.5 hay 15 retratos verticales, **todos en el mismo rectángulo**
(288×434 en x 336, y 55, dentro de la ventana del marco crema). El primero entra
solo; luego viene la ráfaga, primero sobre el crema y desde 1:15.64 sobre el
video de la puerta turquesa, que sigue corriendo debajo. El último retrato se
queda hasta 1:17.505 y el video sigue solo.

- **Reloj propio:** 13 retratos de **3 cuadros exactos** (0,100 s) cada uno, 10
  caras por segundo: más de tres veces lo que se alcanza a leer.
- **La canción va en tresillo:** el golpe (~0,46 s, ~131 BPM) se parte en tres
  (~0,1525 s). Lo confirman los ataques y su autocorrelación en todo el tema
  (picos en 0,151 y 0,453 s; corchea y semicorchea dan negativo). Un reloj de
  0,100 s no existe en la canción: la ráfaga se desliza contra el tambor.
- **Lo que sí estaba bien puesto:** la canción corta el bajo durante un compás
  (1:13.80–1:15.64) y el video de la puerta entra justo cuando vuelve (1:15.64).
  La entrada del primer retrato (1:13.501) cae exacta 14 tresillos antes de ese
  «uno»: la rejilla anclada ahí calza con los ataques a 19 ms medianos.

## Técnica nueva: `sincronizar`

`py/montaje/sincronizar.py` (`python montaje.py sincronizar <p>`):

1. Mide el período de la subdivisión en los ataques alrededor de la ráfaga, con
   la fase fija en un **ancla** (un «uno» seguro).
2. Rescata cada pieza del propio video: entre los cuadros en que aparece en el
   original, el de su rectángulo más nítido (varianza del laplaciano).
3. Reescribe **sólo la ventana del original y sólo el rectángulo**: cada cuadro
   lleva la pieza que le toca según el `reloj`. Fuera de eso, el video no cambia.
4. Una sola recodificación (CRF 14) y el audio copiado sin tocar.
5. Deja un clip de comparación (original arriba, nuevo abajo) para mirar y
   mandar por chat.

Límite: lo que el original tapaba no se puede destapar antes de tiempo. La última
pieza se queda hasta `fin`.

## El reloj elegido: «Acelerando»

Miguel eligió entre tres (acelerando, al tresillo igual que ahora, uno por golpe)
la recomendada:

| Retratos | Entra | Dura | Qué |
|---|---|---|---|
| 1 | 1:13.502 | 2 tresillos | la anacrusa: entra antes del corte del bajo |
| 2–5 | 1:13.807 | un golpe cada uno | el compás sin bajo, sobre el crema: las caras se leen |
| 6–14 | 1:15.637 | un tresillo cada uno | vuelve el bajo, entra el video y los retratos corren con el tambor |
| 15 | 1:17.009 | hasta 1:17.505 | cae en el golpe y se queda hasta que el video sigue solo |

## Lo que salió

`~/Videos/montaje/14-caliz-rafaga/render/`:

- `caliz-rafaga-acelerando.mp4`: el video completo (2:02, 51 MB).
- `caliz-rafaga-acelerando-comparar-1.mp4`: 1:11–1:20, original arriba y nuevo
  abajo (9,6 s, 4,4 MB).

Verificado: el audio es idéntico al original (mismo MD5 de la pista); los 3.668
cuadros caen en los mismos tiempos; fuera del rectángulo, PSNR medio 42 dB contra
el original (la recodificación no se nota); los bordes del rectángulo no dejan
asomar los retratos viejos (la franja oscura junto al borde izquierdo es del
video de la puerta, está también en sus cuadros limpios).

## Visto y no tocado

- 0:36.0–0:36.7: la imagen desaparece 24 cuadros (sólo el crema), y 4 más en
  0:38.2. Coincide con el primer corte de la canción; los siguientes no lo repiten.
- El cierre: el audio se corta seco en 2:02.0, en pleno nivel, mientras la imagen
  se funde a negro; no hay firma.
- En general los cortes no caen en el pulso (27 de 97 a menos de 60 ms de un
  golpe, lo que daría el azar), y los más rápidos están en la parte más calma.

## Lo que dijo Miguel

- Ofreció más material: «también puedo pasarte más fotos, o videos para que
  agregues si gustas». Le dije que no hacía falta: fue un error, los clips eran
  justo lo que faltaba.
- Veredicto: «no me gustó la modificación, porque no sé si te diste cuenta, pero
  tomaste un reel que se ataba a movimiento, donde en el mismo formato habían
  videos con estos personajes moviendose. Que le brindó una capa extra de
  movimiento, no siento que sea mejor a lo que ya estaba.»

## Lo que salió mal

Traté los 15 retratos como imágenes fijas, y no lo eran todos. Medido después en
su rectángulo (diferencia media, de 0 a 255, entre el primer y el último cuadro):

| Retrato | Cuadros | Cambio | Qué pasa |
|---|---|---|---|
| 1 | 52 | 20 | video: cierra los ojos y gira la cabeza |
| 2–14 | 3 cada uno | hasta 2 | casi idénticos en sus 3 cuadros |
| 15 | 29 | 36 | video: parpadea y se mueve |

- El reel va de personaje en movimiento a destellos en el mismo formato, y de
  vuelta a un personaje en movimiento. Esa continuidad es lo que le da la capa
  de movimiento, no sólo el ritmo de los cortes.
- Mi versión dejó el 1 en 9 cuadros quietos (eran 52 en movimiento) y el 15 en 15
  quietos, y llenó el corte del bajo con caras fijas. Quedó un pase de diapositivas.
- El giro de cabeza del retrato 1 se veía en las hojas. Me anoté comprobar si las
  piezas se movían y no lo hice; medí el ritmo y no el contenido.
- Nunca le pregunté a Miguel qué le molestaba de ese tramo: asumí que era el reloj.

`sincronizar` ahora mide esto y se detiene si una pieza se mueve, así que este
proyecto.json ya no corre tal cual: es lo que debe pasar. Los archivos de
`render/` son este intento rechazado.
