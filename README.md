# montaje

Edición de video entre Miguel y Claude. La edición vive en un archivo de texto,
`proyectos/<p>/timeline.json`, que los dos leemos y escribimos; Remotion lo
dibuja y lo renderiza. El método completo (para Claude y para quien lo lea) está
en la skill `~/.claude/skills/montaje/SKILL.md`.

```
fuentes de imágenes ──catalogo──▶ analisis/catalogo.json ─┐
canción ──────────────musica────▶ analisis/musica.json    ├─planificar─▶ timeline.json ──render──▶ render/*.mp4
                                  analisis/musica.png  ───┘                    ▲                     │
                                                                  Studio / chat / a mano        hoja ▼
                                                                                              hojas/*.png
```

## Instalar

```bash
npm install
python -m pip install --user -r requirements.txt
```

Hace falta `ffmpeg` en el PATH (para las hojas de contacto).

## Usar

```bash
python montaje.py --help
python montaje.py catalogo archivo-completo
python montaje.py musica archivo-completo
python montaje.py planificar archivo-completo
python montaje.py render archivo-completo --preview --desde 20 --hasta 50
python montaje.py hoja archivo-completo preview-20-50.mp4 --cada 1
python montaje.py studio archivo-completo
```

Después del render, la postproducción no vuelve a renderizar la imagen:

```bash
python montaje.py sonorizar 09-sonido-curiana        # capa de efectos sobre un render
python montaje.py ensamblar 08-programa-interludios  # programa + cortinas
python montaje.py paquete 06-reel-cinta --red instagram-reel youtube-short  # masterizado, listo para subir
```

Los medios (imágenes, audio, análisis, renders) van en `~/Videos/montaje/<p>/`,
fuera del repo y fuera de OneDrive. `MONTAJE_MEDIOS` cambia esa raíz.

## Estructura

- `montaje.py` — punto de entrada.
- `py/montaje/` — catálogo, análisis de música, planificador, comandos.
- `src/` — la composición de Remotion (`Montaje.tsx`) y los tipos del timeline.
- `proyectos/<p>/` — `proyecto.json` (la idea y los parámetros) y `timeline.json` (la edición).
- `direccion/` — la biblia: tono, paleta, motivos, referencias, sonido y lo que dijo Miguel. Se lee antes de cada experimento.
- `EXPERIMENTOS.md`, `GLOSARIO.md`, `PUBLICACIONES.md` — bitácora, vocabulario y registro de publicaciones.

## Proyectos

- **archivo-completo** — las 821 imágenes de la galería de Curiana Radio en un
  solo video, superpuestas en doble exposición al pulso de una canción.
