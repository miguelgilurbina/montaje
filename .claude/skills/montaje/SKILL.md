---
name: montaje
description: Editar video junto a Miguel con el repo `montaje` (Remotion + Python + ffmpeg) — montajes de imágenes al ritmo de una canción, superposiciones, y más adelante voz en off, subtítulos y sonidos. Usar cuando se pida editar o montar un video, armar un video con imágenes (por ejemplo las de la galería de Curiana), analizar una canción para cortar al pulso, planificar o ajustar un timeline, renderizar un preview o el final, mirar un render en hojas de contacto, abrir el Studio, o empezar un proyecto de video nuevo.
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
11. **Señal** (`senal <p>`, `py/montaje/senal.py`): fallas de transmisión
    (glitch) sólo en las transiciones (salvapantallas, barridos, firma, videos),
    con su sonido; nunca sobre una imagen protagonista. `geq` no recorta: cada
    canal va con `clip(…, 0, 255)`. Mirar las hojas de cada ventana (`hoja
    --desde --hasta --cada 0.0667`).
12. **Entrega:** `ensamblar` (cortinas) y `paquete` (por red, masterizado a
    −14 LUFS y pico real −1 dBTP).

Miguel mira y ajusta en **el panel**: `python montaje.py panel <p>` (Next, puerto
3310, `app/` + `components/` + `lib/`): el video sin renderizar (Remotion Player
con el mismo `Montaje.tsx`), la tira de la canción con compases y momentos,
los momentos se editan en la tira (clic en un compás vacío, arrastrar, Supr) con
su ficha, el resto de `proyecto.json` es un formulario (`components/Formulario`;
las perillas con nombre y frase viven en `lib/vocabulario.ts`: si se agrega un
parámetro en Python, agregarlo ahí); cada cambio replanifica solo (600 ms) y hay
deshacer. Botones para música, render, sonorizar y señal mostrando su salida. Los medios los sirve
`app/medios` desde `~/Videos/montaje` (el timeline lleva `base` para eso).
También está Remotion Studio: `python montaje.py studio <p>` (puerto 3300).
Lanzar cualquiera con `run_in_terminal` (pestaña del panel Terminal de Miguel),
no como proceso de fondo: esos mueren a las 2 horas. `preview_start` no sirve
aquí: lee el launch.json de Curiana. Ambos recargan solos al cambiar el timeline.

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

## Reglas

- **Lo original no se toca.** Todo lo que sale va a `render/`, `hojas/`, `analisis/`.
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

- Voz en off: grabación de Miguel → Whisper (faster-whisper en la RTX 3060)
  marca el tiempo de cada palabra; el texto de los subtítulos sale del guion,
  no de lo que Whisper oye.
- Subtítulos con la tipografía y las tintas del proyecto.
- Ambientes que sigan a las familias de imágenes (agua, desierto, ojos…) según
  sus descripciones, y una firma sonora propia de Curiana Radio.
- Reescalado con IA (Real-ESRGAN) si las imágenes se ven blandas a 1080p.
