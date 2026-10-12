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
                                  sonorizar (efectos) · senal (glitch) · ensamblar (cortinas) · paquete (redes)
```

## Qué sabe hacer

- **Modos de montaje:** `collage` (papeles nítidos que se acumulan, cámara que
  se aleja), `cinta` (feed vertical en loop para reels), `actos` (de una imagen
  a la vez al caos, con pared, ecos y coda), `superposicion` (doble exposición).
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

## Requisitos

- Node.js 22 o más nuevo, y `npm`.
- Python 3.11 o más nuevo.
- `ffmpeg` y `ffprobe` en el PATH.
- Una GPU ayuda a renderizar, pero no hace falta.

```bash
npm install
python -m pip install --user -r requirements.txt
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
python montaje.py studio mi-video                # verlo antes de renderizar (puerto 3300)
python montaje.py render mi-video --preview --desde 0 --hasta 20
python montaje.py hoja mi-video preview-0-20.mp4 --cada 1
python montaje.py render mi-video                # el final
```

Cada comando dice dónde dejó lo que hizo; `python montaje.py --help` los lista.
Los parámetros del montaje están en `proyecto.json` (los que faltan salen de
`POR_DEFECTO` en `py/montaje/planificar.py` y en cada modo).

Junto a una carpeta de imágenes puede haber un `descripciones.json`
(`{"archivo.jpg": {"titulo": …, "alt": …, "concepto": …}}`): con eso el montaje
sabe qué muestra cada imagen y puede pedir «una ráfaga de retratos».

## Dónde vive cada cosa

| Qué | Dónde | Por qué |
|---|---|---|
| Código, experimentos (`proyecto.json`, `timeline.json`, `FICHA.md`) y dirección | este repo | son decisiones: van a git |
| Imágenes, audio, análisis, renders, hojas | `~/Videos/montaje/<proyecto>/` (se cambia con `MONTAJE_MEDIOS`) | pesado o regenerable: fuera del repo |

Una **biblioteca** (`biblioteca` en `proyecto.json`) puede compartirse entre
varios experimentos; las salidas de cada uno van en su propia carpeta.

## El método

- **`direccion/`** — la biblia: tono, paleta, motivos, referencias, sonido y el
  registro de lo que dijo la persona que dirige, con sus palabras. El agente la
  lee antes de cada experimento.
- **`proyectos/NN-nombre/FICHA.md`** — cada experimento con su idea, material,
  renders y el veredicto. **`EXPERIMENTOS.md`** es el índice.
- **`GLOSARIO.md`** — el vocabulario de montaje en español e inglés, con el
  parámetro que mueve cada cosa.
- **`PUBLICACIONES.md`** — qué se preparó para qué red. Nada se publica sin el sí
  de la persona.
- La skill de Claude Code con el flujo paso a paso (`montaje`) explica cómo
  trabaja el agente: mirar las hojas antes de opinar, registrar cada
  experimento, no tocar los originales, pedir ok antes de bajar nada.

Los experimentos 01–10 son los de Curiana Radio: sirven de ejemplo de cómo se
itera (y de qué dijo quien dirige en cada vuelta). Sus imágenes y su música no
están en el repo.

## Estructura

- `montaje.py` — punto de entrada: `python montaje.py <comando> <proyecto>`.
- `py/montaje/` — catálogo, análisis de música, planificador y modos (`collage`,
  `cinta`, `actos`), marca y logo, sonido, señal, ensamblado, publicación.
- `src/` — la composición de Remotion (`Montaje.tsx`) y los tipos del timeline
  (`tipos.ts`).
- `proyectos/<p>/` — cada experimento. `curaduria/` — listas de imágenes de marca
  por biblioteca.

## Licencias

El código de este repo: ver `LICENSE`. Remotion tiene [su propia
licencia](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md): gratis
para personas y empresas chicas, con licencia de empresa a partir de cierto
tamaño; quien use esto en una organización debe revisarla. Las imágenes y la
música de los experimentos son de sus autores y no se distribuyen aquí.

Hecho entre Miguel Gil (Curiana Radio) y Claude.
