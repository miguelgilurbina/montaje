# 25 · Más aparatos: la película, lo digital, la casetera, la consola y el tiempo

**Fecha:** 2026-11-21

## Idea

Miguel, al volver de dormir y antes de juzgar las quince cadenas de la mesa analógica: «acumulemos más efectos antes
de evaluar lo que ya hiciste. Que más podemos hacer ?». De un menú de nueve (cuatro aparatos de la mesa, cuatro
familias fuera de ella y los efectos de tiempo al pulso) dijo «Dale» a lo recomendado: **la película**, **lo
digital temprano** y **el tiempo al pulso**. Lo demás quedó en `PROPUESTAS.md` (M2–M7).

El criterio es el de la mesa: no pintar el efecto sino simular lo que lo producía. La película se simula en la
emulsión; lo digital, en un sensor chico y un códec escrito aquí. Las referencias, con sus fuentes y lo que no se
pudo verificar, están en [`direccion/ANALOGO.md`](../../direccion/ANALOGO.md) («La película», «Lo digital
temprano», «Los gestos de tiempo»).

Con eso hecho y mandado (el recorrido y el video de los gestos de tiempo), siguió lo que había dicho que venía si
no me frenaba: **la casetera** y **la consola de mezcla de los 90** (M2 y M3). Con los 25 commiteados y subidos
(con su ok), Miguel eligió en tarjetas **«Seguir acumulando»**: el proyector en la pared, el 35 mm de las fotos, el
sonido de la película y la consola al pulso (M4, M5, M6, M8).

## Material

El banco del probador (ocho clips de La Añoranza y 21 s de la canción) para las muestras, y el banco a 1080 del
experimento 24 para las hojas y para medir. Nada se bajó.

## Lo que se hizo

- **La mesa con dos mundos.** Hasta ayer todos los aparatos trabajaban en la señal NTSC (480 líneas de 760
  muestras). Ahora hay también aparatos que trabajan en la imagen, en sus módulos; `procesar_cuadro` pasa la imagen
  a la señal cuando le toca a un aparato de señal y la devuelve cuando le toca a uno de imagen. Así se encadenan:
  `[pelicula, cinta]` es el Super 8 que alguien pasó a cassette.
- **`py/montaje/pelicula.py`**, el aparato `pelicula`: Super 8, 8 mm y 16 mm. La luz (el filtro 85 olvidado, el
  parpadeo), el quemado del arranque y el velo del rollo, el halo rojo, lo blando del formato, la curva de la
  reversible (Kodachrome, Ektachrome, blanco y negro), el grano en la densidad y nuevo en cada cuadro de película,
  los tintes que se destiñen, polvo, rayas, el pelo en la ventanilla, el vaivén, los 18 cuadros por segundo, la
  ventanilla o el escaneo con la tira y su perforación, y la fecha naranja en siete segmentos.
- **`py/montaje/digital.py`**, los aparatos `sensor` (pocos pixeles, pocas capturas y algunas perdidas, ruido, el
  balance que se equivoca, la exposición que persigue, la mancha del CCD, el borde morado, el obturador rodante,
  los serruchos de la lectura salteada, y el micrófono) y `compresion` (un códec en bloques de 8×8: `jpeg`, `dv`
  con su color 4:1:1, y `mpeg` con cuadro clave, búsqueda de movimiento y zona muerta; los errores que se
  arrastran hasta el próximo cuadro clave; el datamosh con `residuo` bajo).
- **Los gestos de tiempo** en `pulso` (`tiempo_de_toma` → `video.tiempo` → `cuadroVisto` en `Montaje.tsx`): la
  imagen congelada en el golpe, el tartamudeo, el paso de cuadro.
- **`py/montaje/casetera.py`**, el aparato `casetera` (de señal; la mesa ahora suma también aparatos de señal de
  otros módulos): la pausa de un campo con su barra de ruido y su ‖, rebobinar (la imagen de antes, hacia atrás,
  entre dos barras que suben, con el ◀◀), el arranque en la pantalla azul con ▶ PLAY y el tracking, y el
  entrelazado. El rebobinado guarda los cuadros de antes livianos (luma a la mitad, color a un cuarto, 8 bits).
- **`py/montaje/consola.py`**, el aparato `consola` (de imagen): mosaico, estrobo, multi (la pantalla en 4, 9 o
  16), pintura, negativo y llave, `siempre` o `a ratos`; lo que tiene memoria se actualiza aunque el efecto esté
  apagado, para que los pedazos no dejen costura.
- **Dieciséis estilos** en `propuesta`, con su muestra del probador: siete de película (`super-8-de-la-familia`,
  `super-8-escaneado`, `pelicula-destenida`, `ocho-milimetros-en-blanco-y-negro`, `super-8-con-el-filtro-puesto`,
  `super-8-pasado-a-vhs`, `foto-con-fecha`), seis digitales (`celular-de-2006`, `webcam`, `camara-de-bolsillo`,
  `minidv-con-dropouts`, `videollamada-que-se-corta`, `se-derrite`) y tres de tiempo (`golpe-congelado`,
  `tartamudeo`, `paso-de-cuadro`). Después, **nueve más**: tres de la casetera (`pausa-del-vhs`, `rebobinar`,
  `vhs-que-arranca`) y seis de la consola (`mosaico-de-la-consola`, `estrobo-de-la-consola`,
  `multi-de-la-consola`, `pintura-de-la-consola`, `llave-de-la-consola` y `video-de-boda`, que junta la cámara con
  su fecha, el mosaico y el estrobo a ratos, la cinta y el entrelazado). Y con «Seguir acumulando», **seis más**:
  `pelicula-en-la-pared`, `pelicula-en-la-sabana`, `super-8-sonoro`, `foto-de-laboratorio`,
  `foto-de-laboratorio-fuji` y `consola-al-pulso`; `foto-con-fecha` pasó al 35 mm de laboratorio.
- **`py/montaje/proyeccion.py`**, el aparato `proyector`: la imagen en la pared (o en la sábana, o en una
  pantalla), con la mancha de luz, el trapecio, el foco, el latido del obturador y el cuarto oscuro. Lo que no
  cambia de un cuadro a otro (dónde cae cada pixel, la textura, los pliegues) se calcula una vez.
- **La película** suma el `formato: 35mm` y dos negativos de laboratorio (`kodak-gold`, `fuji-superia`), y
  `sonido` (`magnetico`, `proyector`, con el sintetizador del comando `proyector`).
- **La consola al pulso**: la mesa recibe los golpes de la canción (`musica_de`, `--golpes <proyecto>`; el
  probador pasa los del banco) y la consola prende sus efectos en el uno de cada compás, en cada golpe o en los
  picos. Sin golpes, la cadena se detiene y dice qué falta.
- **`py/pruebas/test_pelicula_digital.py`**: la cadencia de 18 cuadros, el cuadro repetido con su grano, el gris
  medio en su lugar, la copia desteñida que tira al rojo, el halo rojo, la ventanilla, el blanco y negro, la
  película y lo digital sin costura entre pedazos, las capturas perdidas, el celular con barras, la calidad del
  códec, el datamosh en un corte, el error que dura hasta el cuadro clave, el micrófono del celular, la película
  pasada a VHS y los gestos de tiempo en los golpes.

## Errores que aparecieron (y quedaron como pruebas)

- **Una semilla negativa.** Las rayas, el pelo y el velo se identifican por su ranura en el tiempo; cerca del
  segundo cero la ranura anterior es −1, y numpy no acepta semillas negativas: el aparato se caía. La prueba sin
  costura lo encontró.
- **El micrófono del celular dejaba pasar los agudos.** El control automático de ganancia devolvía al nivel lo
  poco que el filtro dejaba a 6 kHz. Un celular tiene, antes de muestrear a 8 kHz, un filtro empinado: ahora
  también (octavo orden).
- **Pruebas mal planteadas, no el motor:** el ruido de colores al azar no mide un códec (lo que pierde ahí es el
  color achicado, no la cuantización), y un corrimiento que la búsqueda de movimiento encuentra entero no se
  derrite. Las pruebas usan ahora ruido gris y un corte de verdad.

- **El tartamudeo no tartamudeaba en el banco.** «En los golpes fuertes» se medía contra el `umbral_pico` del
  proyecto, y en el banco ningún golpe llega (el más fuerte, 0,78 contra 0,8): la muestra salió igual al banco.
  Ahora el pico es relativo a la canción, el cuarto de golpes de más energía.

## La segunda mirada

Como la noche anterior, un agente que sólo leyó y probó (sin tocar el repo) revisó todo lo nuevo y reprodujo cada
hallazgo. Lo que encontró, ya arreglado y con su prueba:

- **El sensor irregular se caía en el primer cuadro**: si se perdía la captura 0 o la 1, la que se mostraba era
  la −1 (y una semilla negativa). Ahora la primera nunca se pierde.
- **El escaneo se caía en una salida vertical o cuadrada**: la tira se medía sólo por el alto. Ahora manda el
  ancho cuando la salida es angosta, y en una salida alta se ven más cuadros de la tira.
- **El tope del calentamiento rompía la costura sin aviso**: con un `gop` largo y un sensor de pocos cuadros, el
  cuadro clave quedaba a más de 240 cuadros. Ahora la cadena se rechaza y dice qué bajar.
- **Con capturas perdidas el calentamiento no alcanzaba** (el obturador rodante y el cuadro clave pueden quedar
  una captura más atrás), y **los dropouts de la MiniDV tenían memoria sin fin** (tapaban con el cuadro anterior
  ya tapado). Ahora se calienta lo que hace falta, y se tapa con el cuadro anterior tal como salió del códec.
- **La foto que despierta con los gestos de tiempo saltaba hacia atrás**, y el gesto en el primer cuadro de una
  toma caía mientras entraba (con el doble de la anterior todavía moviéndose). Ahora los gestos empiezan después
  de la entrada y de la foto que despierta, y nunca muestran un cuadro anterior a ella.
- **La fecha salía amarilla**: la luz empujaba el rojo y el verde al hombro de la curva a la vez. Ahora es
  rojo anaranjada (tono entre 10 y 42°, medido).
- Menores: el códec antes de un sensor veía la captura del cuadro anterior; `busqueda` con decimales y una
  `semilla` negativa pasaban la validación; las perillas nuevas de `pulso` no se validaban.

## La tercera mirada

Otra revisión independiente, sobre la casetera, la consola, el proyector, el 35 mm, el sonido de la película y la
consola al pulso. Lo que encontró, ya arreglado y con su prueba:

- **Las memorias encadenadas dejaban costura** (la grave): el calentamiento tomaba la mayor de las memorias de la
  cadena, pero encadenadas se suman. Con el estrobo de la consola antes de la pausa de la casetera, la pausa
  guardaba un cuadro que el estrobo, todavía frío, había hecho distinto: en un video de verdad, la costura se veía
  en el primer cuadro de un pedazo. Ahora el calentamiento suma, aparato por aparato.
- **Un multi grande pasaba la validación y después el render se detenía** con un consejo que no venía al caso, y
  el rebobinado por defecto no andaba en videos de 50 o 60 cuadros por segundo. Ahora la cadena se rechaza al
  validarla, con el consejo del aparato que se pasa (cada módulo tiene el suyo), y en 50/60 el final de un
  rebobinado largo se queda en lo más viejo que se puede recordar.
- **El traqueteo del proyector no seguía a la película**: con `cuadros: 0` la imagen iba a 30 y el traqueteo a 18.
  Ahora suena a los cuadros que se ven.
- Menores: la pantalla azul de la casetera contaba desde el segundo de la entrada y no desde donde empieza la
  salida (con `--desde`, no aparecía), y unas pocas muestras de audio por la cinta salían a un volumen absurdo.

Los recorridos que se mandaron antes de estos arreglos pueden tener esa costura en algún cuadro suelto; las
muestras del probador se redibujaron.

## Lo que salió (mirado en hojas)

- **La película** (hojas a 540 y recortes al 100 % a 1080): el Kodachrome contrastado y saturado, el Ektachrome
  más frío; la ventanilla con sus esquinas; el escaneo con la tira, la perforación y los vecinos; la copia
  desteñida en rojo magenta; el blanco y negro con la fecha (en blanco y negro la fecha sale blanca: la luz de
  los diodos aclara la reversible). A 1080 el grano se ve como grano, no como ruido.
- **Lo digital:** el celular chico con barras, en bloques que se arrastran; la webcam con mucho ruido; la cámara
  de bolsillo con el borde morado; la MiniDV con los rectángulos de colores del dropout. El datamosh hace lo que
  hace el de verdad: después del corte del banco, la playa se derrite con el movimiento de la cocina.
- **La casetera y la consola** (hoja a 540 con los eventos forzados): la pausa con el ‖ y su barra; el rebobinado
  que vuelve a la playa desde la cocina, con el ◀◀ y sus dos barras; la pantalla azul, el ▶ PLAY y la imagen que
  entra con el tracking; el mosaico, el multi en nueve. La pintura salía gris (escalonar la luz y el color por
  separado lo apagaba): ahora escalona cada canal, con el color un poco subido. La llave casi no se ve en el banco,
  porque la memoria guarda la misma escena: se nota cuando la escena cambia (lo dice su frase).
- **El proyector y el 35 mm** (hoja a 540): la película en trapecio, más clara al centro y cálida, en la pared
  de revoque o en la sábana (los pliegues se notan en los bordes torcidos más que en la sombra, sobre una imagen
  oscura); el cuarto salía gris claro y ahora queda casi negro, con un poco de luz rebotada cerca de la imagen. El
  Kodak Gold cálido con la fecha naranja, el Fuji más verde.
- **Velocidad**, a 1620×1080 en este computador: Super 8 ~5 cuadros/s, el escaneo ~6,5, el celular ~11, la
  MiniDV ~11, el Super 8 pasado a VHS y visto en el tubo ~2,6.

## Renders

En `~/Videos/montaje/25-mas-aparatos/`: `hojas/` (las hojas de comparación) y `velocidad/` (cuatro segundos del
banco a 1080 por cadena). Las muestras de la galería, en `~/Videos/montaje/estilos/probador/`.

## Lo que dijo Miguel

—

## Lo aprendido

- Un aparato que repite cuadros (la película a 18, el sensor a 15) guarda el cuadro hecho y lo devuelve tal cual:
  es más barato y es lo correcto (el telecine repite el mismo cuadro, grano incluido).
- El códec propio se calienta desde su cuadro clave: con un `gop` largo, cada pedazo procesa muchos cuadros antes
  de empezar; por eso los pedazos se alargan cuando el calentamiento es largo.
- Lo que tiene memoria se prueba también encadenado: cada aparato solo no dejaba costura, y juntos sí. La
  prueba de la costura va con dos aparatos con memoria, uno detrás del otro.
- Una segunda y una tercera mirada (agentes que sólo leen y prueban) encontraron 12 defectos reales en un día de
  trabajo; ninguno se veía en las hojas.
