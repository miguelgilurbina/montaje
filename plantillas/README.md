# Plantillas de piezas

Un tipo de video ya pensado, que se le pone a un proyecto con su canción y su material y deja la pieza armada por
tramos. Miguel, el 2026-11-22: «También armar templates de trabajo para poder armar trabajo más adelante»; es uno de
los tres moldes que eligió (con las recetas guardadas, en `recetas/`, y el molde de experimento, en
`direccion/MOLDE.md`).

```
python montaje.py plantillas                                    # las lista y las valida
python montaje.py plantilla mi-cortina cortina-de-radio --crear # un proyecto nuevo con la plantilla
#  … la canción y los clips, `musica` y `clips` …
python montaje.py plantilla mi-cortina cortina-de-radio         # muestra la pieza en los segundos de la canción
python montaje.py plantilla mi-cortina cortina-de-radio --escribir
```

Con `--escribir` quedan los tramos y las capas en `proyecto.json` (`montaje.tramos`, `sintesis`) y una `PIEZA.md`
con lo que pasa en cada tramo, los textos que faltan escribir y los comandos de la mesa analógica para después del
render. Si el proyecto ya tiene tramos, no se pisan sin `--forzar`.

El guion (`python montaje.py guion`) elige solo, tramo por tramo, el primer estilo que sirve; una plantilla es una
decisión tomada de antemano, para una pieza que se hace seguido.

## Qué guarda una plantilla

`plantillas/<id>.json`:

| Campo | Qué es |
|---|---|
| `nombre`, `frase`, `para`, `dura` | cómo la llamamos, qué es, para qué sirve, cuánto dura |
| `material` | `clips`, `fotos` o `mixto` |
| `tono` | (opcional) el `tono` del proyecto: las lecciones de Miguel que valen para ese tono |
| `salida` | el lienzo: ancho, alto, cuadros por segundo, fondo |
| `formato` | (opcional) un estilo de formato (`reel-recortado`…): pone el lienzo y cómo se recorta |
| `montaje` | las perillas de todo el video (`modo: pulso`, el orden, el reparto) |
| `tramos` | la pieza: cada uno con `parte` ([desde, hasta] de 0 a 1 de la canción, seguidos), `estilos` (el primero de `pulso` arma el tramo; las capas que haya, van encima) y `pasa` |
| `capas` | estilos capa para todo el video |
| `textos` | lo que falta escribir: `estilo`, `parte` y `texto` (qué escribir) |
| `analogo` | la mesa, después del render, en ventanas: `cadena` (un estilo analógico o una receta) y `parte` |
| `pasos` | consejos que van a `PIEZA.md` |

Las partes de la canción se llevan al «uno» más cercano: un tramo vale por compases enteros. Lo analógico va sólo en
ventanas, y nunca sobre una imagen protagonista de la galería (la regla del tono).

## Lo que falta

- Una plantilla para el modo de fotos (collage, carrusel, secuencia), que no tiene tramos: hoy la plantilla es de
  `pulso`.
- El documental con voz (el modo `planos`, con la voz y los subtítulos) es otra forma de trabajo; su plantilla sería
  otra.
- Que la mesa analógica corra dentro del render (M9 en `PROPUESTAS.md`): hoy va después, con los comandos de
  `PIEZA.md`.
