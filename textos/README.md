# La galería de textos

Letreros con nombre para títulos, frases, rótulos, subtítulos y créditos. Cada uno es un archivo
`textos/<id>.json` con su tipografía, su forma, su lugar y cómo entra y sale. Pedida por Miguel el
2026-11-17, después del primer documental: «algo base propio para la galería, para usar como de
repente como títulos».

- **Verlos:** en el panel, `/textos`. Se dibujan en vivo con el mismo componente que los pone en el
  video (`src/Letrero.tsx`): no hay muestras guardadas que ocupen disco. Arriba se puede escribir un
  texto propio, cambiar el fondo de todas y dejarlas quietas en el cuadro donde ya entraron.
- **Juzgarlos:** ahí mismo, sí / a medias / no, con o sin palabras; se anota con
  `python montaje.py veredicto <id> <estado>`, igual que los estilos.
- **Validarlos:** `python montaje.py textos` (y las pruebas del motor).
- **Usarlos** en el modo `planos`, por su nombre:

```json
"textos": [{"texto": "Nombre Apellido", "secundario": "quien habla", "letrero": "nombre-y-cargo", "desde": 0.1, "hasta": 0.9}]
```

`planificar` pone la forma del letrero en el timeline y la lista de tipografías que usa; el render
las copia a su carpeta pública.

## Las tipografías

Viven en `fuentes/`, una carpeta por familia con su licencia al lado (OFL o Apache 2.0), y se
registran en `fuentes/fuentes.json` con su voz, su licencia y el rango de pesos de cada archivo. Las
bajó Claude el 2026-11-17 del repositorio de Google Fonts, con el ok de Miguel. Una tipografía nueva
se agrega ahí (archivo + licencia + entrada en el registro), con su ok si hay que bajarla.

Las tres voces de la marca (`direccion/PALETA.md`) son la columna: **el cartel grita** (Archivo
Black en mayúsculas, apretada a 0,82), **el oráculo susurra** (Lora cursiva) y **el dato teclea**
(IBM Plex Mono).

## Los campos

Los tamaños van en fracción del **alto** del cuadro (0,1 = una letra de 108 px en 1080) y los
espacios en **em**: el mismo letrero se ve igual en 16:9, 9:16 o 1:1.

| Campo | Qué es |
|---|---|
| `nombre`, `frase` | cómo se llama y qué es, en palabras |
| `familia` | `titulos` · `frases` · `rotulos` · `subtitulos` |
| `para` | para qué sirve (lista libre: «abrir», «quien habla», «subtítulos»…) |
| `fuente`, `peso`, `cursiva` | una familia de `fuentes/fuentes.json`; el peso dentro de su rango |
| `variacion` | ejes de la tipografía variable (`{"SOFT": 100, "WONK": 1, "opsz": 144}` en Fraunces) |
| `tamano`, `interlineado`, `espaciado`, `mayusculas` | la forma de la letra |
| `compresion` | la aprieta a lo ancho (0,82 = el «type 3c» del cartel de Curiana) |
| `color` | `#rrggbb` o `#rrggbbaa` |
| `contorno` | `{color, ancho}`: el borde va detrás del relleno, la letra no adelgaza |
| `sombra` | `{color, desenfoque, y}` |
| `caja` | `{color, relleno, radio, bloque}`: una caja por fila (los subtítulos); con `bloque: true`, un solo papel para todo el texto (el post-it) |
| `resaltado` | `{color}`: plumón detrás de la parte baja de cada fila |
| `barra` | `{color, ancho}`: barra a la izquierda, como en los rótulos de noticiero |
| `lugar` | `centro` · `arriba` · `abajo` · `tercio-inferior` · `arriba-izquierda` · `abajo-izquierda` · `abajo-derecha` |
| `alineado`, `ancho`, `giro` | alineación, ancho máximo (fracción del cuadro) y giro en grados |
| `entrada` | `{tipo, dura}`: `fundido` · `subir` · `acercar` · `desenfoque` · `maquina` (letra a letra) · `palabras` · `barrido` · `ninguna` |
| `salida` | `{tipo, dura}`: `fundido` · `bajar` · `ninguna` |
| `secundario` | la segunda línea, con su propia letra (`arriba: true` la pone encima) |
| `rodillo` | créditos que suben; cada fila es una línea y `rol \| nombre` va en dos letras |
| `ejemplo` | `{texto, secundario}`: lo que muestra la galería |
| `fondo` | el de la muestra: `oscuro` · `claro` · `imagen` · `mapa` |
| `estado`, `miguel`, `veredicto` | como en los estilos |
| `origen` | de dónde salió (opcional) |

Una palabra nueva del vocabulario se agrega a la vez en `py/montaje/textos.py`, `src/tipos.ts` y
aquí.
