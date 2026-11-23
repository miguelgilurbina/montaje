# El teaser de la alfa

Miguel, el 2026-11-23: «Tenemos que pensar además en un vídeo interesante de teaser. Para publicarlo como open
source».

El teaser se hace con montaje mismo y su receta se publica como ejemplo: es la mejor prueba de que la herramienta
sirve (Remotion lanzó con un video hecho con Remotion). El borrador es el experimento 37
(`proyectos/37-el-teaser-de-la-alfa/`).

## Lo que funciona en un teaser de herramienta

- **Los dos primeros segundos.** Mostrar el producto ahí rinde mucho más que mostrarlo después; también el nombre al
  principio. [Las cifras vienen de un resumen de prensa de 2022 de un estudio de Meta con Analytic Partners, no de la
  fuente primaria.]
- **Corto.** Menos de un minuto; la gente se va hacia la mitad.
- **El resultado primero, la interfaz después.** La interfaz prueba que es de verdad, pero lo que engancha es la
  imagen. FFglitch perdió en Hacker News porque la página no decía qué hacía.
- **Se entiende sin sonido**, con rótulos. Aquí el sonido es contenido (los aparatos suenan), así que se rotula para
  quien mira callado y se cuida para quien escucha.
- **Dos formatos desde el mismo timeline**: 16:9 (README, Hacker News, YouTube) y 9:16 (Shorts, Reels). Hacer los dos
  desde un `timeline.json` ya es una demo.

Referencias: el antes y después de ntsc-rs; las demos de LZX que muestran sólo la salida del parche; el EYESY de
Critter & Guitari que responde al audio; *Oscilloscope Music* de Jerobeam Fenderson y Hansi Raber (el canal izquierdo
mueve x, el derecho y: la música y el dibujo se componen juntos); *Global Groove* de Paik y Godfrey (1973), el zapping
como forma.

## Tres conceptos

### 1. Una imagen, todos los aparatos (unos 45 s)

- **0 a 3 s:** una foto se enciende en un televisor de tubo. Rótulo: «una imagen».
- **3 a 24 s:** siete aparatos, tres segundos cada uno, cortados al pulso: antena, VHS, Super 8, imprenta,
  fotografía del XIX, zoótropo, consola de los 90. Cada uno con su nombre.
- **24 a 32 s:** dieciséis estilos de la galería, medio segundo cada uno, con su veredicto.
- **32 a 40 s:** pantalla partida: el pedido a Claude Code en español y el `timeline.json` cambiando.
- **40 a 45 s:** cartón final y la dirección.
- **Sonido:** los ruidos de la mesa hacen la banda, sobre una pista sintetizada; medio segundo de silencio antes
  del cartón.

### 2. 88.8 (unos 40 s)

- **0 a 3 s:** estática; el dial corre y se clava en 88.8, y aparece la imagen. Se entiende sin sonido.
- **3 a 15 s:** cuatro estaciones de tres segundos, cada frecuencia un estilo, con estática entre una y otra.
- **15 a 25 s:** la consola: se giran los diales y la imagen responde. Rótulo: «a mano».
- **25 a 33 s:** el pedido al agente, el diff y el render. Rótulo: «o se lo pides».
- **33 a 40 s:** vuelta a 88.8, la identificación de la estación y la dirección.
- **Sonido:** el barrido de la radio, la estática y la música de cada estación.

### 3. La marca la dibuja el sonido (unos 30 s; sirve de loop para el README y en vertical)

- **0 a 3 s:** la retícula verde y un punto; entra un zumbido y el punto se vuelve línea. Rótulo: «este sonido…».
- **3 a 9 s:** el trazo dibuja la marca. Rótulo: «…dibuja esto».
- **9 a 18 s:** la marca pasa por el tubo, el VHS, la imprenta y el Super 8, dos segundos cada uno, al pulso del
  zumbido.
- **18 a 24 s:** se abre la galería; alguien gira «persistencia» en la consola.
- **24 a 30 s:** la marca se queda quieta en un tono limpio y entra el cartón.
- **Sonido:** sólo el audio del dibujo, sin música encima, para que la relación se pueda comprobar; normalizado,
  porque es áspero.

**La recomendación:** el 3 como gancho corto y loop del README; el 1 para el Show HN; el 2 para quien llega desde la
radio. El borrador del 37 mezcla el 2 (la sintonía) y el 1 (los aparatos) y cierra con la marca del 3, para mirar las
piezas antes de elegir.

## El borrador (experimento 37)

`python proyectos/37-el-teaser-de-la-alfa/armar.py` → `<medios>/37-el-teaser-de-la-alfa/borrador.mp4`, 28 s:
sintonía con el dial (3,5 s), los aparatos (16 s), MONTAJE en el osciloscopio (5 s) y el cartón por el tubo (3,5 s).
Todo con el material de prueba. Lo que se ve y lo que está flojo, en su ficha.

## Lo que decide Miguel

1. **El concepto** (o la mezcla).
2. **El material**: el de prueba (se puede mostrar en cualquier parte), sus clips de Midjourney o imágenes de Curiana.
   Lo que no es de él no entra.
3. **La música**: compuesta para esto, para no depender de derechos; o sólo los sonidos de la mesa.
4. **El nombre que dibuja el haz**: MONTAJE con las letras de la marca (como en el borrador), o la espiral y CURIANA
   (la espiral vive fuera de este repo público).
5. **La toma de la consola**: la grabación de la pantalla girando los diales la hace él (con su mano y su controlador,
   si tiene uno); el boceto de la consola graba sólo la imagen, no la interfaz.
6. **Rótulos**: en español en la imagen y una versión en inglés aparte.
