# montaje

Un harness para editar video **con** un agente de IA (Claude Code), no a pesar
de él. La edición vive en un archivo de texto, `timeline.json`, que la persona
y el agente leen y escriben; [Remotion](https://www.remotion.dev) lo dibuja y lo
renderiza; Python escucha la música y planifica los cortes; ffmpeg hace la
postproducción. El agente no ve el video correr: lee la canción como números,
las imágenes como catálogo y el render como hojas de contacto, y escribe la
edición. La persona mira, opina y corrige.

Nació para los videos de [Curiana Radio](https://curianaradio.com): montajes de
cientos de imágenes al pulso de una canción. Está escrito en español, de
principio a fin, a propósito.

> *English:* a text-first video editing harness for working with an AI coding
> agent. The edit is a `timeline.json`; Remotion renders it; Python analyses the
> music (beats, bars, energy, key) and plans the cuts; ffmpeg does sound design,
> glitches, idents and mastering. The agent reads contact sheets instead of
> watching video. Docs and code are in Spanish.

```
imágenes ──catalogo──▶ catalogo.json ─┐
canción ───musica────▶ musica.json   ├─planificar─▶ timeline.json ──render──▶ render/*.mp4
           (pulso, compases, energía) ┘                   ▲                        │
                                              Studio / chat / a mano          hoja ▼  (lo que mira el agente)
                                                                             hojas/*.png
                                                                                  │
                                  sonorizar (efectos) · senal (glitch) · analogo (cinta, antena, tubo) · ensamblar (cortinas) · paquete (redes)
```

## Qué sabe hacer

- **Modos de montaje:** `collage` (papeles nítidos que se acumulan, cámara que
  se aleja), `cinta` (feed vertical en loop para reels), `actos` (de una imagen
  a la vez al caos, con pared, ecos y coda), `superposicion` (doble exposición),
  `secuencia` (una tras otra a pantalla completa) y `pulso` (**clips**: cada uno
  en su frase de la canción, saltando entre sus mejores momentos, con fundidos
  o transiciones (cortina, iris, empuje, destello, zoom, persiana; y luz, desenfoque,
  doble exposición, quemado de película, sacudón, colores corridos, bloques, latigazo
  y la cinta que agranda, también entre fotos y al empezar cada tramo), fantasmas,
  díptico, ventana, caleidoscopio, muro… y un estilo por tramo del guion; las
  fotos del proyecto pueden entrar al mismo reparto, con un acercamiento lento).
- **Clips:** copias de trabajo (giradas, HDR→SDR, cámara lenta interpolada), lectura
  de cada clip como curvas (movimiento, cámara, temblor, nitidez, centro de
  interés) y clips transformados (`transformar`: estela, eco, barrido temporal,
  reversa, ida y vuelta).
- **Síntesis:** capas hechas en código al pulso de la canción (grano y recuerdo,
  fugas de luz, polvo, la canción dibujada, campos de color, tintas, calima,
  televisor, onda, foco, golpe de zoom, títulos, «sonando ahora», cuenta
  regresiva, tira de película, rótulos al pulso, la luz que sigue a la canción,
  barras de cine, película gastada) y el sonido del proyector (`proyector`).
- **Estilos:** el catálogo de recetas con su muestra y el veredicto, que se da en
  la galería del panel (`/estilos`).
- **Ejercicios:** `ejercicio` corre todas las versiones de un experimento (plan,
  render, hoja, medidas y muestra) o barre una perilla y pone los valores lado a
  lado (`--barrer fundido_golpes=0.5,1,2,4`), `revisar` mide un render (negro, cuadros
  repetidos, destellos por segundo, sonoridad, y cinco señales de monotonía: planos del
  mismo largo, planos que vuelven, poco movimiento, energía pareja, misma luz), `recorrido` junta la galería en un
  video y `guion` propone los estilos que sirven en cada tramo de la canción.
- **Al pulso:** la canción se analiza (BPM, golpes, compases, energía por golpe,
  secciones, tonalidad) y el ritmo de entradas la sigue: compás → golpe →
  corchea → semicorchea.
- **Momentos** por número de compás: destacado (una imagen al frente), ráfaga
  (cortes secos a pantalla completa), barrido (salto de cámara), video.
- **Marca:** imágenes curadas que destacan, logo como sello que late en una
  esquina, salvapantallas tipo DVD en los silencios, firma al final.
- **Postproducción sin re-renderizar:** efectos de sonido sintetizados en código y
  afinados a la tónica (`sonorizar`), fallas de transmisión en las transiciones
  (`senal`), cortinas con su propio audio (`ensamblar`), paquete por red social
  masterizado a −14 LUFS (`paquete`).
- **Mesa analógica** (`analogo`): un video o una foto pasado por aparatos simulados en su señal
  NTSC: la cámara de video, la cinta VHS (formatos, copias de copias, tracking, desgaste, con su
  sonido), la antena (nieve, fantasmas, interferencia, sincronismo perdido), el corrector de base
  de tiempo, el video arte (colorizador, imán de Paik, relieve Rutt/Etra, realimentación) y el
  televisor de tubo. Los defectos salen de cómo se codificaba el color y de lo que cada aparato
  le hacía; las referencias, en `direccion/ANALOGO.md`. En la misma mesa, la película (Super 8,
  8 mm, 16 mm, simulada en la emulsión), lo digital temprano (el celular, la webcam, la MiniDV:
  un sensor chico y un códec en bloques, con su datamosh), la casetera (pausa, rebobinar, la
  pantalla azul con PLAY), la consola de mezcla de los 90 (mosaico, estrobo, multi; también al
  pulso de la canción), el proyector en la pared o en la sábana, y la lente (aberración, ojo de
  pez, destello, raya anamórfica, niebla). Y el etalonaje (`color`): tablas de color escritas en
  código (la paleta de la marca, noche americana, infrarroja, blanqueo saltado, proceso cruzado) o
  cualquier `.cube` de otro editor; `python montaje.py color --exportar` las lleva a otro editor.
- **Consola de diales** (`/consola` en el panel): la mesa a mano. El video pasa por la cadena de
  aparatos en la tarjeta de video, en vivo, y cada perilla se gira con el mouse, el teclado o un
  controlador MIDI. Lo que se gira con el video corriendo queda grabado (puntos por perilla, como
  la automatización de un programa de música) y el motor lo renderiza igual. Ver
  `direccion/CONSOLA.md`.
- **Gestos de tiempo al pulso:** la imagen congelada en el golpe, el tartamudeo y el paso de cuadro.

## Requisitos

- Node.js 22 o más nuevo, y `npm`.
- Python 3.11 o más nuevo.
- `ffmpeg` y `ffprobe` en el PATH.
- Una GPU ayuda a renderizar, pero no hace falta.

```bash
npm install
python -m pip install --user -r requirements.txt
```

## Probar sin material propio

```bash
python montaje.py demo        # cinco clips hechos con código, CC0 → ~/Videos/montaje/demo/clips/
npm run panel                 # el panel en http://127.0.0.1:3310 → «consola»
```

En la consola: elige `demo/clips/cielo-con-sol.mp4`, parte de una cadena de la galería (por
ejemplo `destello-de-sol` o `cinta-gastada`) y gira. Con **grabar** encendido y el video
corriendo, lo que giras queda escrito; **renderizar con el motor** saca el video de verdad a
`~/Videos/montaje/consola/renders/`, con su receta al lado.

Desde la línea de comandos, lo mismo sin el panel:

```bash
python montaje.py analogo demo/clips/carta-que-se-mueve.mp4 --cadena cinta-gastada
python montaje.py analogo --cadenas          # las cadenas de la galería
```

## Empezar con tus imágenes

1. Copia `proyectos/ejemplo/` con otro nombre (`proyectos/mi-video/`) y edita su
   `proyecto.json`: `fuentes` apunta a una carpeta con imágenes (jpg, png,
   webp); `musica` es un archivo dentro de `~/Videos/montaje/mi-video/audio/`.
   Si todavía no tienes canción, `pista-prueba` sintetiza una con pulso.
2. Corre el flujo:

```bash
python montaje.py catalogo mi-video              # mide y describe las imágenes
python montaje.py imagenes mi-video --bajar      # las copia a la biblioteca
python montaje.py imagenes mi-video --miniaturas
python montaje.py pista-prueba mi-video          # (si no hay canción)
python montaje.py musica mi-video --archivo audio/prueba.wav
python montaje.py planificar mi-video            # → proyectos/mi-video/timeline.json
python montaje.py panel mi-video                 # el panel: verlo sin renderizar, editar y correr todo (puerto 3310)
python montaje.py render mi-video --preview --desde 0 --hasta 20
python montaje.py hoja mi-video preview-0-20.mp4 --cada 1
python montaje.py render mi-video                # el final
```

Cada comando dice dónde dejó lo que hizo; `python montaje.py --help` los lista.

**El panel** (`panel`, Next.js en el mismo paquete) es la mesa de trabajo: el
video dibujado en el navegador por el mismo código que lo renderiza; la **tira**
de la canción (energía por golpe, compases numerados) donde los momentos se
ponen con un clic, se arrastran de compás y se ajustan en su ficha; las
decisiones de `proyecto.json` como **formulario** (la canción, el formato, el
montaje con cada perilla explicada, la marca) y el JSON plegado para lo demás.
Cada cambio replanifica solo y el video se actualiza; hay deshacer. Botones para
analizar la música, renderizar un tramo o el final, sonorizar y poner la señal,
con la salida de cada comando a la vista. El vocabulario de las perillas está en
`lib/vocabulario.ts`. Remotion Studio (`studio`, puerto 3300) sigue disponible
para inspeccionar cuadro a cuadro.
Los parámetros del montaje están en `proyecto.json` (los que faltan salen de
`POR_DEFECTO` en `py/montaje/planificar.py` y en cada modo).

Junto a una carpeta de imágenes puede haber un `descripciones.json`
(`{"archivo.jpg": {"titulo": …, "alt": …, "concepto": …}}`): con eso el montaje
sabe qué muestra cada imagen y puede pedir «una ráfaga de retratos».

## Todo trabaja en tu máquina

Nada del flujo necesita la nube: el análisis, la planificación, el render, el
sonido, la señal y el panel corren en local y leen y escriben archivos locales.
Las imágenes, el audio y los renders viven fuera del repo y nunca se suben (git
ignora todos los formatos de medios). El repo en GitHub guarda sólo el código y
las decisiones (`proyecto.json`, timelines, fichas). El panel no carga nada de
internet, escucha sólo en tu computador (127.0.0.1, no en la red de la casa) y
la telemetría de Next va apagada. Lo único que sale a la red es lo
que tú pides: bajar imágenes de una fuente remota o instalar dependencias.

## Dónde vive cada cosa

| Qué | Dónde | Por qué |
|---|---|---|
| Código, experimentos (`proyecto.json`, `timeline.json`, `FICHA.md`) y dirección | este repo | son decisiones: van a git |
| Imágenes, audio, análisis, renders, hojas | `~/Videos/montaje/<proyecto>/` (se cambia con `MONTAJE_MEDIOS`) | pesado o regenerable: fuera del repo |

Una **biblioteca** (`biblioteca` en `proyecto.json`) puede compartirse entre
varios experimentos; las salidas de cada uno van en su propia carpeta.

## El método

- **`direccion/`**: la biblia: tono, paleta, motivos, referencias, sonido y el
  registro de lo que dijo la persona que dirige, con sus palabras. El agente la
  lee antes de cada experimento.
- **`proyectos/NN-nombre/FICHA.md`**: cada experimento con su idea, material,
  renders y el veredicto. **`EXPERIMENTOS.md`** es el índice.
- **`GLOSARIO.md`**: el vocabulario de montaje en español e inglés, con el
  parámetro que mueve cada cosa.
- **`PUBLICACIONES.md`**: qué se preparó para qué red. Nada se publica sin el sí
  de la persona.
- **`.claude/skills/montaje/SKILL.md`**: la skill de Claude Code con el flujo
  paso a paso: cómo trabaja el agente (mirar las hojas antes de opinar,
  registrar cada experimento, no tocar los originales, pedir ok antes de bajar
  nada). Al abrir el repo con Claude Code se carga sola.

Los experimentos 01–10 son los de Curiana Radio: sirven de ejemplo de cómo se
itera (y de qué dijo quien dirige en cada vuelta). Sus imágenes y su música no
están en el repo.

## Estructura

- `montaje.py`: punto de entrada: `python montaje.py <comando> <proyecto>`.
- `py/montaje/`: catálogo, análisis de música, planificador y modos (`collage`,
  `cinta`, `actos`), marca y logo, sonido, señal, ensamblado, publicación.
- `src/`: la composición de Remotion (`Montaje.tsx`) y los tipos del timeline
  (`tipos.ts`).
- `app/`, `components/`, `lib/`: el panel (Next): páginas, reproductor, tira,
  servidor de medios con rangos, los comandos como API y la consola de diales
  (`components/Consola.tsx`; los shaders de la vista previa en `lib/consola-gl.ts`).
- `proyectos/<p>/`: cada experimento. `curaduria/`: listas de imágenes de marca
  por biblioteca. `estilos/`: el catálogo de estilos.
- `py/pruebas/`: pruebas del motor: `python -m pytest py/pruebas -q` (las que
  necesitan medios se saltan si no están).

## Licencias

El código de este repo es libre bajo la licencia MIT (`LICENSE`). Remotion tiene [su propia
licencia](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md): gratis
para personas y empresas chicas, con licencia de empresa a partir de cierto
tamaño; quien use esto en una organización debe revisarla. Las imágenes y la
música de los experimentos son de sus autores y no se distribuyen aquí. El material de prueba
(`demo`) lo genera el código y es CC0. Los shaders de la consola están escritos para este repo;
lo que se estudió de otros proyectos y bajo qué licencia está en `direccion/CONSOLA.md`.

Hecho entre Miguel Gil (Curiana Radio) y Claude.
