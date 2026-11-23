# La consola de diales

Miguel, el 2026-11-23: «podríamos además de tener una galería, tener un espacio para hacer edición manual de vídeo.
Como modificación análoga de vídeo. Con diales manuales».

La galería elige y juzga cadenas ya armadas. La consola es lo otro: tocar. Es la página `/consola` del panel
(`npm run panel`, sólo en 127.0.0.1) y tiene cuatro piezas:

1. **La vista previa en vivo.** El video pasa por la cadena en la tarjeta de video (WebGL2), con un shader por
   aparato que se le parece. Al girar una perilla, la imagen responde al instante.
2. **Las perillas**, en pantalla o en un controlador MIDI.
3. **La grabación de los gestos.** Lo que se gira mientras el video corre queda como automatización: puntos
   `[segundo, valor]` por perilla.
4. **El render de verdad.** El botón le pasa la fuente, la cadena y lo grabado al motor
   (`python montaje.py analogo … --automatizacion`). El video que sale es el del motor, no el de la vista previa.

## Cómo se usa

1. Elegir una fuente: los clips de práctica y del banco, los renders de los proyectos, lo que ya salió de la consola.
2. Cargar una cadena de la galería como punto de partida, o sumar aparatos uno a uno.
3. Girar.
   - Arrastrar hacia arriba sube y hacia abajo baja. Con Shift, fino.
   - La rueda del mouse también gira.
   - Doble clic vuelve al valor de fábrica.
   - Con el foco en una perilla, las flechas suben y bajan, Re Pág y Av Pág dan saltos, e Inicio y Fin van a los
     extremos.
   - Las perillas de opciones (formato, emulsión, máscara) giran por pasos.
4. Grabar. Con **grabar** encendido y el video corriendo, la perilla que se toca escribe sobre lo que había
   mientras se la sostiene. Al soltarla, vuelve a leer lo grabado. Es el modo «touch» de REAPER y de Ableton.
5. Renderizar el tramo (todo, o entre las marcas de entrada y salida) al alto que se elija. Queda en
   `<medios>/consola/renders/`, con su receta al lado (`.json`: fuente, cadena, automatización, tramo) para repetirlo.

La sesión (fuente, cadena, lo grabado y el MIDI) se guarda en `<medios>/consola/sesiones/`. El navegador además
guarda la última sola, por si se cierra la pestaña.

El **boceto** graba lo que se ve en la vista previa mientras se toca, en tiempo real, con `MediaRecorder`. Sirve para
mostrar el gesto rápido. No es el render: es la aproximación y puede perder cuadros si la máquina no da abasto.

## Qué se ve en vivo

Tienen vista previa: `cinta`, `antena`, `pantalla`, `pelicula`, `tinte`, `imprenta`, `cinetico`, `lente`,
`consola`, `cruce`, `iman`, `realimentacion`, `colorizador`, `camara`, `sensor` y `compresion` (`lib/consola-gl.ts`).

**La barra** (`cruce`, en `py/montaje/consola.py`) es la T del mezclador: `cantidad` 1 deja salir lo que viene de la
cadena y 0 el cuadro como entró. Se pone donde termina lo que se mezcla (antes del tubo, que va siempre al final) y
se graba moviéndola, como cualquier perilla.

Los demás (`placa`, `copia`, `juguete`, `osciloscopio`, `radiofoto`, `hell`, `satelite`, `cascada`, `relieve`,
`proyector`, `tbc`, `osd` y los gestos) se pueden poner en la cadena y girar, pero en la vista previa pasan sin tocar
la imagen y llevan la marca «sólo en el render».

La vista previa **es una aproximación y lo dice**. El motor simula cada aparato en su señal con numpy, cuadro a
cuadro y con filtros exactos; el shader hace lo que se ve parecido, a 540 líneas. Lo que se mantiene igual:

- los nombres de las perillas, sus rangos y sus valores de fábrica, que la consola le pide al motor
  (`analogo --aparatos`), así que no hay dos listas que mantener;
- el tiempo: los puntos grabados van en segundos de la fuente (`video.currentTime`), los mismos que el motor usa
  en `ctx.t`;
- el orden de la cadena y lo que recuerda cada aparato del cuadro anterior (fósforo, estela, realimentación,
  estrobo).

## El formato de lo grabado

La cadena del motor suma `automatizacion`, una lista de pistas:

```json
{"aparatos": [{"aparato": "antena", "nieve": 0.06}, {"aparato": "pantalla"}],
 "automatizacion": [
   {"paso": 0, "perilla": "nieve", "puntos": [[0.0, 0.06], [2.5, 0.8], [4.0, 0.1]]},
   {"paso": 1, "perilla": "mascara", "puntos": [[0.0, "rejilla"], [3.0, "puntos"]], "curva": "escalon"}
 ]}
```

- `paso` es el lugar del aparato en la cadena (desde 0); `perilla`, su nombre.
- Los `puntos` van en orden de tiempo, con los valores dentro del rango de la perilla. Entre dos puntos, el valor
  se mueve en línea recta (`lineal`, por defecto) o salta (`escalon`). Las opciones y los sí/no siempre saltan.
- Antes del primer punto vale el primero y después del último, el último.
- Lo que suena (el ruido de los aparatos) lee el primer valor: no sigue a la perilla.
- `analogo.errores` revisa todo: el paso, que la perilla exista, el orden y el rango.

Se puede escribir a mano y pasar con `--automatizacion ARCHIVO` (una lista de pistas, o un objeto con
`automatizacion`). El video sale con `-a-mano` en el nombre.

Dos cosas que conviene saber al automatizar:

- **Perillas pesadas.** La geometría del tubo (`curva`, `vineta`, `mascara`, `mascara_fuerza`) y la de la lente
  (`barril`, `aberracion`, `vineta`, `suciedad`) se calculan una vez y se guardan. Si se mueven, se recalculan en
  cada cuadro: sale bien, pero más lento.
- **Lo que recuerda** (realimentación, estela, fósforo, película) se renderiza en orden. Por eso el motor calienta
  cada pedazo con los cuadros de antes.

## MIDI

Botón **MIDI**: el navegador pide permiso (Chrome desde la 124; Firefox desde la 108 con un complemento de permiso
que genera solo; Safari no lo tiene). Después:

1. **aprender**, clic en una perilla de la pantalla y mover una del controlador: quedan atadas (entrada, canal, CC);
2. las perillas absolutas (0 a 127) entran **sin salto**: la de pantalla no se mueve hasta que la física pasa por su
   valor (el «pickup» o «soft takeover»; sin esto, la imagen salta al primer roce);
3. las opciones se reparten en el recorrido de la perilla física.

El mapa viaja en la sesión.

## Licencias de lo que se estudió

Los shaders de `lib/consola-gl.ts` están escritos desde cero para este repo, con la idea de cada aparato y no con
código ajeno.

**Se puede copiar o portar** (con su aviso):

- ntsc-rs: el crate `ntscrs` es `MIT OR ISC OR Apache-2.0`
  (https://github.com/valadaptive/ntsc-rs). Su modelo de la señal es el camino más corto para acercar la cinta y la
  antena del navegador a las del motor.
- crt-lottes, de la colección de libretro: dominio público según su cabecera.
- ISF (la especificación y la colección ISF-Files): MIT.
- gl-transitions: MIT, salvo dos que son BSD.
- glsl-film-grain: MIT. glsl-halftone: dominio público.
- Mediabunny (WebCodecs): MPL-2.0, se puede usar como dependencia.
- moderngl: MIT.

**Sólo se estudia** (no se copia código a un repo MIT):

- crt-royale, crt-geom y crt-guest-advanced: GPL-2.0 o posterior.
- El filtro NTSC de blargg: LGPL-2.1.
- Shadertoy: CC BY-NC-SA 3.0 salvo que el autor diga otra cosa [sin verificar: shadertoy.com no contestó; el dato
  viene de una fuente secundaria].
- Hydra y hydra-synth: AGPL-3.0.
- La cadena de ntsc-rs viene de composite-video-simulator (GPL-2.0) a través de zhuker/ntsc y ntscqt (Apache-2.0).
  [sin verificar: cómo se pasó de GPL a Apache en esa cadena.]

## Referencias

### Aparatos para tocar video

- **LZX Vidiot** (manual en PDF): cada parámetro tiene una perilla de valor, una de cuánto entra la modulación y un
  interruptor para invertirla. Los grupos son Patrones, Luma y Colorizador.
- **Sleepy Circuits Hypno**: dos lados espejados y lo global al centro. La perilla de realimentación aclara hacia un
  lado y pasa a negativo hacia el otro, con muesca en el cero. De ahí las perillas **bipolares** de la consola.
- **Critter & Guitari EYESY**: pocas perillas fijas cuyo sentido cambia según el modo.
- **Erogenous Tones Structure**: un joystick que graba el gesto y lo repite en bucle [sin verificar: sólo tiendas].
- **Sandin Image Processor**: módulos sueltos con planos publicados libres («copy-it-right»). Es el antecedente de
  un proyecto abierto de video.
- **Experimental Television Center, *Image Processing Manual* (1986)**: el colorizador de seis canales, el keyer de
  luma y el secuenciador, las piezas mínimas de un estudio.
- **Paik/Abe** y **Rutt/Etra** (de este último sale el aparato `relieve`).
- **Panasonic WJ-MX50**: el joystick de color centrado, CHROMA como perilla centrada, Still/Strobe/Multi/Trail como
  botones y una sola perilla de ritmo («Effect Interval», de 0,03 a 2,1 s), y AV Synchro, que dispara los efectos
  con el sonido. Es el aparato `consola` y su `al pulso`.
- **Videonics MX-1**: la barra de transición. Las reseñas de sus sucesores se quejan de que respondía lento: el
  cruce tiene que responder sin demora.
- **Sony SEG-2550**: 63 efectos en memorias numeradas.
- **El proc amp**: brillo, contraste, color y tinte, que cada fabricante nombra distinto. La consola nombra por lo
  que hace la perilla.
- **Circuit bending** (Tachyons+, la WJ-AVE5 intervenida de BPMC, Karl Klomp): aparatos de consumo con perillas de
  «error» agregadas.

### Programas

- **ntsc-rs**: los grupos (head switching, tracking, ringing, croma, VHS) tienen su casilla para encenderlos y se
  pliegan; los presets se copian como JSON. De ahí, cada aparato con su interruptor.
- **Lumen**: arrastrar hacia arriba sube, con modificadores más lento; el doble clic vuelve al valor de fábrica;
  un pad XY funde entre variaciones guardadas.
- **Resolume** anima cada parámetro en bucle, al BPM o con el análisis del audio. **VDMX** tiene un «Detect» por
  control y LFOs como fuentes. **TouchDesigner** graba canales con un Record CHOP y advierte que, al reabrir, los
  valores saltan si las perillas físicas se movieron.
- **RetroArch**: cada shader declara sus parámetros (etiqueta, defecto, mínimo, máximo, paso) y el menú se arma
  solo. Aquí lo mismo sale de `POR_DEFECTO` y `RANGOS`.
- **Hydra** tipa cada función según cómo toca la imagen (genera, mueve coordenadas, cambia el color, mezcla) y
  compone la cadena en un solo shader. Lo que sirve: fundir las etapas de color seguidas en una pasada y abrir otra
  sólo donde hace falta mirar a los vecinos o tener memoria.
- **ISF**: un encabezado JSON con las entradas (tipo, defecto, mínimo, máximo) y pasadas persistentes. Es el mejor
  modelo para que un aparato declare su shader.

### Grabar los gestos

- **REAPER**: read, touch, latch, write y trim; tramos lineales, en escalón, en S o Bézier.
- **Ableton**: tocar una perilla grabada suspende lo grabado sin borrarlo; con el mouse graba como touch y con MIDI
  como latch; «Simplify Envelope» reduce los puntos.
- **darktable** (un editor de imagen con MIDI): devuelve el valor a los anillos de LED del controlador, y Ctrl
  divide la velocidad por diez.

### En el navegador

- WebGL2 está en Chrome, Firefox y Safari; WebGPU todavía no llega a todos (Firefox en Linux, sólo en Nightly).
- `requestVideoFrameCallback` da el tiempo del cuadro mostrado, pero es de mejor esfuerzo: la grabación se fecha
  con el tiempo del video, no con el reloj.
- `MediaRecorder` sobre `canvas.captureStream()` graba en tiempo real y pierde cuadros si no da abasto; el códec
  cambia según el navegador.
- El patrón slider de WAI-ARIA: `role="slider"`, `aria-valuenow`, `aria-valuetext` («nieve 0,30»), flechas,
  Re Pág, Av Pág, Inicio y Fin.

### Obras

- Nam June Paik, *Magnet TV* (1965): el imán sobre el tubo que el público podía mover. Es el aparato `iman`.
- Steina Vasulka, *Violin Power* (1970-78): el sonido del violín mueve la imagen.
- El videoarte en Venezuela: *Arte de video* en el MACC (1975); Claudio Perna, *Sonata para un cisne* (1975);
  Carlos Castillo, *Hecho en Venezuela* (1977); el Super 8 de Diego Rísquez.
- Gilles Charalambos (Colombia): el ruido y la distorsión como estilo.

## Lo que sigue

- **Fuentes de movimiento**: un LFO o el pulso de la canción moviendo una perilla, además de la mano.
- **Instantáneas**: guardar variaciones y fundir entre ellas.
- **Acercar la vista previa al motor**: portar la cinta y la antena de ntsc-rs, usar el mismo ruido determinista
  (un hash entero igual en GLSL y en numpy) y comparar cuadros de los dos con un umbral (PSNR o SSIM).
- **Un solo shader para los dos**: que el render final corra el mismo GLSL con moderngl, sin ventana. Así la vista
  previa coincidiría con el final salvo la precisión. Es una decisión de diseño, porque cambia el motor.
