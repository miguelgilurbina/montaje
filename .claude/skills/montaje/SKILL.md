---
name: montaje
description: Editar video junto a Miguel con el repo `montaje` (Remotion + Python + ffmpeg) — montajes de imágenes al ritmo de una canción, superposiciones, y más adelante voz en off, subtítulos y sonidos. Usar cuando se pida editar o montar un video, armar un video con imágenes (por ejemplo las de la galería de Curiana), analizar una canción para cortar al pulso, planificar o ajustar un timeline, renderizar un preview o el final, mirar un render en hojas de contacto, abrir el Studio, empezar un proyecto de video nuevo, escribir o traducir el guion de un video, elegir un estilo, o sumar uno al catálogo de estilos (la galería del panel).
---

# Montaje

El método para editar video entre los dos. Claude no ve un video correr ni
arrastra clips: **lee** (la música como números y espectrograma, las imágenes
como catálogo, el render como hojas de contacto) y **escribe** la edición en un
archivo de texto, `timeline.json`, que Remotion dibuja. Miguel corrige el mismo
archivo (o lo pide en el chat) y lo ve en el Studio.

## Dónde vive cada cosa

| Qué | Dónde | Por qué |
|---|---|---|
| Herramienta (código) | `~/OneDrive/Documents/Desarrollo/montaje` | repo propio; no vive en Curiana Radio ni en ningún proyecto |
| Cada experimento | `montaje/proyectos/NN-nombre/`: `proyecto.json`, `timeline.json`, `FICHA.md` | son la edición y su registro: van a git |
| Bitácora | `montaje/EXPERIMENTOS.md` | índice de experimentos con el veredicto de Miguel |
| Biblioteca | `~/Videos/montaje/<biblioteca>/` (`imagenes/ miniaturas/ audio/ analisis/catalogo.json`) | compartida por los experimentos que la nombran en `biblioteca`; **fuera de OneDrive** |
| Salidas | `~/Videos/montaje/NN-nombre/` (`analisis/musica.json render/ hojas/`) | propias de cada experimento: ninguno pisa a otro |
| Estilos | `montaje/estilos/<id>.json` (receta, uso, veredicto) | el catálogo para elegir según el guion: va a git |
| Muestras de estilos | `~/Videos/montaje/estilos/<id>.mp4` (segundos livianos) | lo que queda de un ejercicio cuando se borran sus salidas; **no van al repo** (es público) |
| Esta skill | `~/.claude/skills/montaje/` | disponible desde cualquier proyecto |

## Dirección: leerla antes de empezar

`direccion/` en el repo es la biblia de los videos: `TONO.md`, `PALETA.md`,
`MOTIVOS.md`, `REFERENCIAS.md`, `SONIDO.md` y `REGISTRO.md` (las palabras de
Miguel, en orden). **Leerla antes de planificar un experimento nuevo** y cuando
haya una duda de estilo. Lo que dice Miguel manda; lo marcado «Propuesta» espera
su visto bueno. Cuando Miguel dé una indicación de estilo, citarla en
`REGISTRO.md` y, si cambia una regla, actualizar el archivo que corresponda.

## Experimentos: registro obligatorio

Miguel quiere un registro de cada experimento. Por eso:

- **Una idea nueva es un experimento nuevo**: carpeta `proyectos/NN-nombre/` con
  el número siguiente. Nunca se re-planifica el timeline de otro experimento
  para probar algo distinto.
- Cada uno lleva su **`FICHA.md`**: fecha, commits, idea (con las palabras de
  Miguel), material (imágenes, música y sus derechos), qué renders salieron y
  dónde, **lo que dijo Miguel, citado**, y lo aprendido.
- Al cerrar una vuelta, actualizar la fila en **`EXPERIMENTOS.md`**.
- La música puede ser un tramo: `"tramo": [desde, hasta]` en segundos de la
  canción, `"fundido_audio": [entrada, salida]`. Si el tramo es corto, fijar
  `"fase_compas"` a mano (la detección del «uno» del compás falla con pocos datos).

Todo comando se corre desde la raíz del repo: `python montaje.py <comando> <proyecto>`.
`python montaje.py --help` lista los comandos; cada uno dice dónde dejó lo que hizo.

## Estilos y guion

`estilos/README.md` explica el catálogo entero; lo esencial:

- **Técnica** (código) → **estilo** (`estilos/<id>.json`: la técnica con sus
  valores, `para`, `material`, `energia`, `estado`, las palabras de Miguel y
  `evitar`) → **guion** (`proyectos/<p>/GUION.md`).
- **El guion lo escribe Miguel en palabras.** Claude lo parte en tramos y, debajo,
  propone un estilo por tramo en una tabla (lo que tiene que pasar, material,
  estilo, por qué): primero los aprobados con ese `para` y ese `material`, nunca
  uno cuyo `evitar` describa el tramo. Sin estilo que sirva, el tramo es un
  ejercicio. Miguel corrige la tabla antes de armar el `proyecto.json`.
- **Del guion al video:** en `pulso`, `tramos` (dentro de `montaje`) cambia perillas
  entre dos segundos de la canción —`{"nombre", "desde", "hasta", …perillas}`— y
  `material` (palabras del nombre de los clips: `["campo"]`, `["lanchas"]`) dice qué
  clips entran en ese tramo, en ronda. Las capas de `sintesis` llevan `desde`/`hasta`.
  Así la tabla del guion se escribe tal cual: un estilo y un material por tramo.
  **El borde de un tramo corta la frase al compás más cercano** (un tramo vale por
  compases enteros): conviene poner `desde`/`hasta` en un «uno» —los que imprime
  `guion`— y usar esos mismos segundos en las capas de síntesis del tramo.
  Ejemplo completo: `proyectos/19-anoranza-con-guion/` (GUION.md + proyecto.json).
- **`guion <p>`** arma el esqueleto: la canción en tramos (sus secciones) con los
  estilos de la galería que sirven en cada uno, y deja en blanco lo que tiene que
  pasar y el material. No pisa un `GUION.md` que ya exista. Al final imprime **un
  primer armado**: los `tramos` con la receta del primer estilo que sirve en cada uno
  y sus capas de `sintesis` con sus segundos, más lo que cada estilo elegido pide
  evitar. Es para planificar y mirar, no una decisión: elige primero lo aprobado, así
  que mejora con cada veredicto. No escribe nada en proyecto.json.
- **Cada ejercicio** prueba una técnica en dos o tres versiones cortas; antes se
  pregunta qué se busca. Cada versión es un estilo con su muestra
  (`muestra <id> --de <render> --desde --hasta`). **`ejercicio <p>`** hace la
  vuelta entera: planifica cada versión, renderiza su tramo, saca su hoja y, con
  `--final --muestra`, corta la muestra. Cada versión dice cómo se prueba:
  `"prueba": [desde, hasta]`, `"estilo": "<id>"` (el archivo en `estilos/` se
  escribe antes) y `"muestra": [a, b]` dentro de ese render. Después, mirar las
  hojas: el comando no juzga. Ejemplo: `proyectos/21-laboratorio-de-la-manana/`.
- **Barrer una perilla:** `ejercicio <p> --version <base> --barrer
  fundido_golpes=0.5,1,2,4 --desde 30 --hasta 42` planifica y renderiza la misma
  base con cada valor y deja las variantes **lado a lado, sincronizadas y con su
  etiqueta**, en `render/barrido-<base>-<perilla>.mp4` (y su hoja). Sirve con
  números, palabras (`transicion=cortina,iris,empuje`) o sí/no. Los timelines de un
  barrido viven en las salidas (`barridos/`), no en el repo. Es la forma de afinar
  un valor con Miguel: se le manda el video y elige una celda.
- **`recorrido [--en <experimento>] [--estado …]`** junta unos segundos de cada
  muestra, con su nombre, en un video de menos de 28 MB para mandar por chat.
- **El veredicto se da en la galería** (`/estilos`): «sí», «a medias», «no» y unas
  palabras opcionales en cada tarjeta. Queda en el archivo del estilo (`estado`,
  `veredicto` y, si escribió, `miguel`) y las palabras, además, en
  `direccion/REGISTRO.md`. Lo que Miguel diga en el chat se anota con el mismo comando
  que usa la galería: `python montaje.py veredicto <id> aprobado|"a medias"|rechazado
  --cita "sus palabras"` (y `propuesta` para deshacer). Lo que haya que **evitar** a
  partir de un «no» se escribe después, a mano, en `evitar`. La elegida queda `aprobado`; las
  otras `rechazado` o `a medias`, con su porqué. Después del veredicto, los
  renders del ejercicio se pueden borrar: la receta y la muestra quedan.
- `python montaje.py estilos` valida el catálogo (vocabulario cerrado, experimentos
  que existen, veredictos con cita) y lo lista; la galería está en `/estilos` del panel.

## El flujo

1. **Proyecto.** `proyectos/<p>/proyecto.json`: idea, fuentes de imágenes,
   canción (`musica`, relativa a los medios), lienzo (`salida`) y parámetros del
   montaje (`montaje`; los que falten salen de `POR_DEFECTO` en
   `py/montaje/planificar.py`). Copiar `proyectos/ejemplo/` como plantilla.
   Fuentes: `{"tipo": "carpeta", "ruta": …}` (cualquier carpeta de imágenes, con
   `descripciones.json` opcional al lado) o `{"tipo": "galeria-curiana",
   "manifest": …}` (la galería de Curiana, en Vercel Blob).
2. **Catálogo.** `catalogo <p>` → `analisis/catalogo.json`: cada imagen con
   proporción, familia, color dominante, luz, tono, título, alt y concepto. Se
   decide sobre esto; no hace falta abrir 800 imágenes para ordenarlas.
3. **Imágenes en disco.** `imagenes <p> --medir` dice cuánto pesa bajarlas.
   **Bajar (`--bajar`) necesita el ok de Miguel con el peso a la vista.**
   `--prueba` genera rellenos con la proporción y el color reales para probar
   sin bajar nada (`--bajar` los reemplaza solo).
4. **Música.** `musica <p>` → `analisis/musica.json` (BPM, golpes, primeros
   tiempos, energía por golpe, secciones) y `analisis/musica.png`. **Mirar el
   PNG con Read** antes de opinar sobre la canción: es lo más cerca de oírla.
   Sin canción todavía: `pista-prueba <p>` y `musica <p> --archivo audio/prueba.wav`.
5. **Planificar.** `planificar <p>` → `proyectos/<p>/timeline.json` y un resumen
   por sección (imágenes, capas a la vez, vida típica). Leer el resumen: si el
   ritmo medio pasa de ~3 imágenes nuevas por segundo, el montaje es parpadeo;
   decirlo, no esconderlo.
6. **Preview de un tramo.** `render <p> --preview --desde 20 --hasta 50`
   (mitad de resolución). Un tramo de 30 s tarda alrededor de un minuto.
7. **Mirar.** `hoja <p> <archivo.mp4> --cada 1` → `hojas/*.png`, y **leerlas
   con Read**. Ningún juicio sobre cómo se ve algo sin haber mirado la hoja.
   **Y medir:** `revisar <p> <archivo.mp4>` lee el render entero y cuenta lo que
   una hoja no muestra: segundos de negro, imagen quieta, cuadros repetidos (la
   cámara lenta que tironea), cortes por minuto, **destellos por segundo** (más de
   tres no se publica: es el límite de accesibilidad por fotosensibilidad) y la
   sonoridad. Avisa lo que conviene mirar; no reemplaza la hoja.
8. **Iterar** sobre `proyecto.json` (parámetros) y volver a 5, o tocar capas
   sueltas en `timeline.json` (ver abajo).
9. **Final** (`render <p>` sin `--preview`) sólo cuando Miguel lo pida: a 1080p
   y con el archivo completo tarda.
10. **Sonido** (`sonorizar <p>`, `py/montaje/sonido.py`): sobre un render
    cerrado, efectos sintetizados en código y afinados a la tónica del tramo,
    uno por momento (impacto, soplo, subida, obturador, estática, rebotes,
    campana); copia el video sin re-renderizar (~15 s). Con `base` usa el render
    de otro experimento. Mirar `analisis/sonido.png` y la tabla de niveles que
    imprime. **Claude no oye la mezcla: los niveles se miden, el oído es de Miguel.**
    **Proyector** (`proyector <p> [--version v] [--render x.mp4]`,
    `py/montaje/proyector.py`): el traqueteo de la película mientras hay `pelicula`
    o `cuenta`, el pop del 2 y un clac de diapositiva en cada capa con `congelar`;
    lee el inicio del tramo del nombre del render («-final-44-60»).
11. **Señal** (`senal <p>`, `py/montaje/senal.py`): fallas de transmisión
    (glitch) sólo en las transiciones (salvapantallas, barridos, firma, videos),
    con su sonido; nunca sobre una imagen protagonista. `geq` no recorta: cada
    canal va con `clip(…, 0, 255)`. Mirar las hojas de cada ventana (`hoja
    --desde --hasta --cada 0.0667`).
12. **Música propia y videos de afuera:** `componer <p>` escribe una canción
    neutra en código (afinada, al tempo, sin derechos); `musicalizar <p>` le pone
    una pista a un video que ya existe sin tocar la imagen (compone primero si
    hace falta, con la duración exacta del video; `original` = cuánto queda del
    audio de origen). Mirar el espectrograma de la pista antes de entregar.
13. **Un video que ya viene editado** (un preeditado, una colaboración):
    primero leerlo entero sin canción ni capas aparte, con hojas cada 0,5 s y la
    sonoridad de cada cuadro, cortes con `select='gt(scene,0.25)'`, espectrograma
    y pulso; después, el tramo sospechoso cuadro a cuadro. Si una ráfaga corre a
    su propio reloj, **`sincronizar <p>`** (`py/montaje/sincronizar.py`) la vuelve
    a poner al pulso: rescata cada pieza del propio video (su cuadro más nítido,
    recortado del rectángulo) y la pega en el mismo lugar según un `reloj` en
    subdivisiones desde un **ancla** (un «uno» seguro). Sólo cambia ese
    rectángulo en esa ventana; el audio se copia sin tocar. Mirar si la música va
    en **tresillo** (autocorrelación de los ataques) antes de elegir la rejilla.
    **Antes de tocar nada: preguntarle a Miguel qué le molesta de ese tramo, y
    comprobar si cada pieza se mueve.** Lo que parece imagen en una hoja de contacto
    puede ser un clip; `sincronizar` pega un solo cuadro, así que sirve sólo para
    piezas fijas y se detiene si alguna se mueve. Lo que se rechazó y por qué:
    `proyectos/14-caliz-rafaga/FICHA.md`.
14. **Entrega:** `ensamblar` (cortinas) y `paquete` (por red, masterizado a
    −14 LUFS y pico real −1 dBTP).

### Clips (videos en vez de imágenes)

1. `"clips": "clips"` en proyecto.json (carpeta de la biblioteca; puede ser una
   lista). `clips <p>` hace las **copias de trabajo** (`proxies/`: H.264 a 1080 como
   mucho, giradas como en el teléfono, HDR→SDR, 30 o 60 cps parejos, un cuadro clave
   cada medio segundo) y lee cada clip como curvas (movimiento sin la cámara,
   cámara, temblor, nitidez, luz, cortes) → `analisis/clips.json`, y la hoja
   `hojas/clips.png` (ocho cuadros por clip con sus curvas). **Mirar la hoja con
   Read antes de planificar.** Los originales no se tocan.
2. `modo: pulso` y `planificar`. `clips.mejor_tramo` elige los segundos: nítidos,
   sin temblor, lejos del arranque y el final de la toma, con el movimiento que pide
   la energía (quietos en la calma).
3. **Versiones** para comparar sin pisarse: `"versiones": {"a": {…}, "b": {…}}` en
   proyecto.json; `planificar <p> --version a` escribe `timeline-a.json` y `render
   <p> --version a` deja `a-preview.mp4`. En el panel, las versiones son botones
   arriba del reproductor (`/p/<p>?v=a`): se ve su timeline; el formulario sigue
   trabajando sobre la base.
4. El render con clips arma `.publico/` en las salidas con **vínculos duros** de lo
   que el timeline usa (Remotion copia la carpeta pública entera en cada render; los
   enlaces simbólicos no los sirve) y limita la caché de cuadros del compositor
   (sin tope se quedó sin memoria a los 53 s).
5. `transformar <p> --efecto estela|eco|barrido|lento|reversa|ida-y-vuelta [--clip …]
   [--fuerza …]`: clips nuevos en `transformados/` (estela de luz, eco, barrido
   temporal, cámara lenta suave, reversa, boomerang); la fuerza va en segundos, así
   vale igual a 24 que a 72 cps. Para usarlos: `"clips": ["clips", "transformados"]`,
   `clips <p>` y `"transformados": "calma"` (o `"todo"`) en el montaje: cada clip usa
   su variante en vez del original. Sin eso, los transformados no entran.
6. **Cámara lenta sin trabas:** `"clips_interpolar": 3` hace las copias con cuadros
   inventados (`minterpolate`): con 24 cps de origen, a 72. Hace falta cuando los
   clips son más cortos que la canción (en el 15 iban a 0,33×: con 48 cps se repetía
   uno de cada cinco cuadros; con 72, ninguno). El video sale a la cadencia del
   material (`salida.fps: 24`): pasar 24 a 30 tironea.
7. Más perillas de `pulso`: `congelar_golpes` (la foto que despierta: cada clip entra
   quieto y en sepia y arranca en el golpe), `dividir: 2` (díptico: cada clip con su
   pareja de la otra mitad del catálogo, lado a lado), `escala` + `sombra` (ventana:
   el clip chico sobre un `campo`), `espejo: 2|4` (caleidoscopio), `rejilla:
   [columnas, filas, segundos]` (mosaico de tiempo), `doble_en: "todo"`, `muro: [3, 3]`
   + `muro_golpes` (muro de recuerdos: nueve clips distintos a la vez, cada celda
   cambia a su golpe, en ola; se planifica aparte de las frases).
   **`transicion`**: cómo entra un clip sobre el que se va, en lo que dura el fundido
   entre clips: `fundido`, `cortina` (un borde blando que barre), `iris` (se abre
   desde el centro de interés del clip que llega), `empuje` (lo corre), `destello`
   (un fogonazo que tapa el cambio), `zoom` (llega desde cerca), `persiana`, o
   `ronda` (todas, una por cambio); `transicion_dir`: `derecha`, `izquierda`,
   `arriba`, `abajo` o `alterna`. El primer clip siempre sale del negro. Para juzgar
   una transición la hoja tiene que ir cuadro a cuadro (`hoja --cada 0.0834`): a un
   cuadro por segundo no se ve.
   El catálogo de clips es **uno por biblioteca**; cada experimento ve sólo lo de
   sus carpetas (`"clips"`), así sumar transformados en uno no le cambia el reparto
   a los demás.
   **Fotos y clips juntos:** `"fotos": "<carpeta>"` en proyecto.json (al lado de
   `clips`) y `clips <p>` las suma al catálogo como clips quietos (sin copia de
   trabajo: Remotion dibuja la imagen). Entran al reparto sólo si el montaje dice
   `"mezclar_fotos": true`, intercaladas (un clip, una foto), cada una con un
   acercamiento lento (`zoom_foto`) y un deslizamiento que nunca destapa el fondo;
   comparten transiciones, díptico, muro y fantasmas con los clips. En el `material`
   de un tramo, `"foto:campo"` pide sólo fotos con esa palabra y `"clip:playa"` sólo
   clips.
8. **Una versión es una prueba completa:** además de perillas del montaje puede traer
   su `salida` (el mismo tramo en 9:16, 1:1, 4:5…) y su `sintesis`. Ojo: las
   versiones heredan del `montaje` base; si la base cambia (en el 15 la base pasó a
   ser la c para el panel y la a heredó sus fantasmas), cada versión tiene que fijar
   lo suyo. Para probar sin gastar: `render <p> --version v --desde 40 --hasta 52`.

### Síntesis: capas hechas en código

`"sintesis": [{"tipo": …}, …]` en proyecto.json; `planificar` las suma al timeline
con los golpes, «uno», energía y espectro de la canción (`py/montaje/sintesis.py`;
se dibujan en `src/Sintesis.tsx`). Van encima de cualquier modo; `campo` va de fondo.
`desde`/`hasta` (s) para un tramo.

- `recuerdo`: `grano`, `vineta`, `calidez`, `parpadeo`, `temblor` (px), `halo`.
- `fugas`: fugas de luz cálidas en el «uno» cada `cada_compases`.
- `polvo`: `motas` que flotan y brillan en los golpes.
- `partitura`: el espectro de la canción como un horizonte (`y`, `alto`); el
  espectro se calcula una vez en `analisis/espectro-*.json` de la biblioteca.
- `campo`: manchas de la paleta que derivan y crecen con la energía; sin material
  (con `"modo": "solo-sintesis"` el video es sólo eso y la canción).
- `tinta` (`oscuro`, `claro`, `fuerza`), `calima` (`fuerza`, `golpe` en px) y `tv`
  (`lineas`, `corrimiento`, `curva`) son **filtros**: no van encima, el contenido
  entero pasa por un filtro SVG (`filtroDe` en Sintesis.tsx).
- `rotulos`: las frases del guion en pantalla. `lineas: [{"t": 28, "texto": "…"}]`;
  cada una entra en el golpe más cercano a su `t`, palabra por palabra (`cada`:
  `golpe`, `medio` o `todo`), en `voz` `oraculo`, `cartel` o `dato`, `lugar` abajo,
  centro o arriba. Con `tiempos` (un segundo por palabra) no usa los golpes: por ahí
  van a entrar los subtítulos de la voz en off. No es para la letra de una canción ajena.
- `luz` (filtro): `brillo` y `color` [calma, pico] siguen la energía suavizada, con
  un latido (`golpe`) en cada golpe. `barras`: las franjas del cine (`formato`,
  `abre_golpes`). `rayas`: rayones y manchas de película gastada (`rayones`, `manchas`).
- **El grano no se comprime:** a CRF 16, 3 min con `recuerdo` pesaron 1,9 GB. Con
  grano el render final va a tasa fija (12 Mb/s, ~270 MB por 3 min).

Miguel mira y ajusta en **el panel**: `python montaje.py panel <p>` (Next, puerto
3310, `app/` + `components/` + `lib/`): el video sin renderizar (Remotion Player
con el mismo `Montaje.tsx`), la tira de la canción con compases y momentos,
los momentos se editan en la tira (clic en un compás vacío, arrastrar, Supr) con
su ficha, el resto de `proyecto.json` es un formulario (`components/Formulario`;
las perillas con nombre y frase viven en `lib/vocabulario.ts`: si se agrega un
parámetro en Python, agregarlo ahí); cada cambio replanifica solo (600 ms) y hay
deshacer. Botones para música, render, sonorizar y señal mostrando su salida; también
«Esqueleto del guion» y, si el proyecto tiene versiones, «Correr todas las versiones»
(`ejercicio` a media resolución). Los medios los sirve
`app/medios` desde `~/Videos/montaje` (el timeline lleva `base` para eso).
También está Remotion Studio: `python montaje.py studio <p>` (puerto 3300).
Lanzar cualquiera con `run_in_terminal` (pestaña del panel Terminal de Miguel),
no como proceso de fondo: esos mueren a las 2 horas. `preview_start` no sirve
aquí (lee el launch.json de Curiana); para mirarlo, `navigate` del navegador
integrado a `http://localhost:3310` con el panel ya corriendo. Ambos recargan solos al cambiar el timeline.

## Modos de montaje (`montaje.modo` en proyecto.json)

- **`superposicion`** — sobreimpresión pareja de principio a fin: las imágenes
  entran al pulso, conviven en doble exposición y se van. Miguel la encontró
  monótona como video entero; sirve como textura o para un tramo.
- **`collage`** (`py/montaje/collage.py`) — papeles opacos y nítidos que caen uno
  sobre otro y se quedan; la cámara se aleja (collage infinito) y el ritmo de
  entradas va por compases (compás → golpe → corchea → semicorchea). Cada imagen
  **al 100 %**: sin mezcla ni calado y nunca más grande que su tamaño nativo.
  Es lo que Miguel entiende por «superpuesto». Admite **`momentos`** en
  proyecto.json (por número de compás): `destacado` (una imagen al frente, el
  collage se oscurece y se detiene, luego ella vuela a su lugar; `"img"` fija
  cuál), `rafaga` (`por_compas` imágenes a pantalla completa en cortes secos) y
  `barrido` (la cámara salta a una zona vacía). Miguel pidió contraste en el
  tiempo: un solo tratamiento parejo, aunque acelere, se siente plano.
- **`cinta`** (`py/montaje/cinta.py`) — feed vertical para reels: las imágenes
  suben en columna un paso por golpe; `compases` dice pasos por compás (4, 8 =
  doble tiempo) o un momento (`destacado`, `rafaga`). Cíclica: el último cuadro
  empalma con el primero (loop sin costura) y el orden recorre el círculo de color.
- **Marca y logo** (`py/montaje/marca.py`, `curaduria/<biblioteca>.json`): Miguel
  pidió que **las imágenes donde se lee Curiana Radio destaquen** (`"img": "marca"`)
  y el logo **intercalado**: `"logo": {"sello": …, "salvapantallas": [{compas,
  compases}], "en_cinta": [k]}`; el logo como destacado/firma: `"img":
  "logo:lockup_claro", "firma": true`. El catálogo trae `tipos` (retrato,
  paisaje, ciudad, cartel, abstracto, ciencia-ficcion) para ráfagas temáticas
  (`"de": "retrato"`).
- Formatos: 3:2 = 1620×1080; reel = 1080×1920. Referencia de Miguel hecha con
  Gemini/Veo: `~/Downloads/Video_Animado_Estilo_s.mp4` (portada «CURIANA», marco de
  espirales, glitch VHS, destello).
- Para mandarle un video por chat (límite 30 MB): reencodar a 1080p en dos
  pasadas (`-b:v` ≈ 28 MB × 8 / duración) y revisar un cuadro antes de enviar.
- **`secuencia`** (`py/montaje/secuencia.py`) — una imagen tras otra a pantalla
  completa, en cortes al pulso, **sin collage**. Para series que comparten forma
  (variaciones del editor de Midjourney): ordenadas por parecido, el corte rápido
  se lee como metamorfosis. La `original` vuelve en `original_en` (el «uno» de
  cada frase) y cierra; se usan todas, una vez, escalando los cortes por compás a
  la energía (`contraste`, `max_por_golpe`). Calma con fundido, ritmo con corte seco.
- **`pulso`** (`py/montaje/pulso.py`) — **para clips**. Cada clip ocupa una o más
  frases de la canción (grupos de `frase_compases`, que se reinician en cada
  sección) y dentro de su frase **salta** entre sus mejores momentos, siempre hacia
  adelante, según `corte`: `frase` (una toma), `compas`, `golpe` o `energia` (la
  calma no salta, el pico salta `pico_por_compas` veces). Entre clips, fundido
  (`fundido_golpes`, más largo en la calma). Fantasmas opcionales en `screen`:
  `doble_golpes` (el que viene se asoma antes) y `estela_golpes` (el que se va se
  queda). En la calma va más lento (`velocidad` [calma, pico]); si a un clip no le
  alcanza el material, más lento todavía. `encuadre: auto` pone **relleno
  desenfocado** detrás de un vertical en cuadro horizontal (y al revés). Sin
  `salida`, el lienzo sigue a la mayoría de los clips (vertical → reel).
- **`actos`** (`py/montaje/actos.py`) — de una imagen a la vez al caos. Abre con
  las de mayor formato (panorámicas), una a una; cada protagonista **vuela** a
  su lugar en una **pared** (mosaico acumulativo que crece en elipse) y la
  cámara se aleja hasta que la pared desborda el cuadro; con el caos alto
  aparecen **ecos** (copias de la pared, escaladas, giradas y desfasadas en el
  tiempo: montaje sobre montaje); la **coda** se aleja hasta mostrar el archivo
  entero. Una sola curva, `caos(t)` (avance × energía), gobierna todo.

## Vocabulario

`GLOSARIO.md` en el repo: cada técnica con su nombre en español y en inglés y
el parámetro que la mueve. Hablar con esas palabras; si Miguel usa una propia
(«montaje sobre montaje», «composición infinita»), anotarla ahí con su traducción.

## Tiempos reales (RTX 3060, 16 hilos, preview a mitad de resolución)

- `planificar`: menos de 1 s. Cambiar orden, ritmo o actos es instantáneo.
- Render de un tramo de 30 s: ~20 s en la calma, ~70 s en el acto III, y en el
  pico del caos ~15 s por cada segundo de video (cientos de piezas + ecos).
- Para decidir, renderizar tramos; el video completo, en segundo plano.

## timeline.json

Una cabecera (`ancho`, `alto`, `fps`, `fondo`, `duracion` en cuadros, `audio`,
`meta`) y `capas`, **una por línea** para que el diff diga qué imagen cambió.
Cada capa: `img` (relativa a los medios), `ini`/`fin` (cuadros), `entrada`/`salida`
(cuadros de fundido), `x`/`y` (centro, px), `ancho`/`alto` (px), `opacidad`,
`zoom` [al entrar, al salir], `deriva` [dx, dy] px a lo largo de su vida,
`mezcla` (modo CSS: `screen`, `lighten`, `normal`…), `borde` (difuminado como
fracción del lado menor; 0 = rectángulo duro), `seccion`.
En modo `actos` además: `actos` (tramos con nombre), `mural` (`piezas` de la
pared en unidades de pared con el cuadro en que `llega` cada una, `luz` = su
opacidad en el tiempo, `borde`), `camara` (claves `[cuadro, cx, cy, escala]`),
`ecos` (`desfase`, `escala`, `rot`, `dx`, `dy`, `mezcla`) y, en cada capa,
`vuelo` (`desde`, `pieza`).
Los tipos están en `src/tipos.ts`; el dibujo, en `src/Montaje.tsx`.
Las piezas de la pared usan `miniaturas/` (`imagenes <p> --miniaturas`) salvo
cuando la cámara las acerca.

**`planificar` reescribe el timeline entero.** Si Miguel (o Claude) tocó capas
a mano, mirar `git diff` del timeline antes de volver a planificar y preguntar;
lo hecho a mano se pierde.

## Cambiar el motor sin romper lo aprobado

Un cambio en `pulso.py` o `clips.py` puede cambiar la planificación de versiones ya
renderizadas y juzgadas, sin que ninguna prueba lo note. La red es
`py/pruebas/planes.py`: planifica todas las versiones de los experimentos con clips
**fuera del repo** y las compara.

    python py/pruebas/planes.py foto <carpeta-antes>      # antes de tocar el motor
    python py/pruebas/planes.py foto <carpeta-despues>    # después
    python py/pruebas/planes.py comparar <carpeta-antes> <carpeta-despues>
    python py/pruebas/planes.py repo <carpeta-despues>    # ¿los timelines del repo son los del motor de hoy?

Lo que cambie se dice con medidas, se replanifica en el repo y se vuelve a renderizar
con otro nombre (`-arreglado`); lo aprobado no puede cambiar sin que Miguel lo sepa.
Si una versión que no tenía que cambiar aparece en la lista, el arreglo está mal (el
2026-11-09 pasó: unir frases sueltas cambiaba la pieza del 20, y se deshizo). Si
cambia el plan de una versión cuya muestra está en la galería, la muestra se rehace
con su mismo tramo y sus mismos segundos (están en `muestra` del estilo).

Una segunda mirada independiente al código (un agente que sólo lee y prueba, sin
tocar nada) encontró quince defectos en la tanda de la noche y nueve en la de la
mañana que las hojas no mostraban: vale la pena después de cada tanda larga.

## Pruebas

`python -m pytest py/pruebas -q` antes de dar por cerrado un cambio al motor: las
funciones puras (encuadres, tramos de clip, títulos, cuenta, rótulos, transiciones,
el esqueleto del guion), la validez del catálogo de estilos y, si están los medios,
que ninguna toma pida más segundos de los que tiene su clip, que el muro no repita
clips a la vez y que a cada clip que entra empujando le corresponda uno que sale.

## Reglas

- **Lo original no se toca.** Todo lo que sale va a `render/`, `hojas/`, `analisis/`.
- **Las salidas no duran.** Miguel borra lo de `~/Videos/montaje` después de publicar
  para no acumular: no dar por hecho que un render o una biblioteca vieja sigue ahí
  (ni buscarlos); el registro que queda es la FICHA.
- **Los rellenos no son las imágenes.** Son más claros y planos que las reales:
  no se ajustan opacidad, mezcla ni exposición mirando rellenos.
- **En `screen`, lo blanco quema.** Las imágenes de fondo claro (pocas en la
  galería, pero existen) se comen las capas de debajo. Si molestan, bajarles la
  opacidad o mandarlas a los picos, no apagar la mezcla para todas.
- **La música llega como archivo.** De Spotify u otro streaming no se baja (DRM y
  términos de uso); el archivo lo consigue Miguel (compra, el artista, su propia
  música) y lo deja en `~/Videos/montaje/<p>/audio/`. Publicar el video con una
  canción ajena necesita permiso de sus dueños; para el experimento privado no.
- **Descargas con ok.** Imágenes, audio o modelos: decir qué, de dónde y cuánto
  pesa, y esperar el sí.
- **Secretos fuera de OneDrive.** Si alguna vez hace falta una clave (voz
  sintética, etc.), va en una variable de entorno de usuario, nunca en el repo.

## Lo que todavía no existe (siguiente en la lista)

La lista larga, con lo que cuesta cada cosa y lo que necesita de Miguel, está en
`PROPUESTAS.md`. Lo primero:

- Voz en off: grabación de Miguel → Whisper (faster-whisper en la RTX 3060)
  marca el tiempo de cada palabra; el texto de los subtítulos sale del guion,
  no de lo que Whisper oye.
- Subtítulos con la tipografía y las tintas del proyecto.
- Ambientes que sigan a las familias de imágenes (agua, desierto, ojos…) según
  sus descripciones, y una firma sonora propia de Curiana Radio.
- Reescalado con IA (Real-ESRGAN) si las imágenes se ven blandas a 1080p.
