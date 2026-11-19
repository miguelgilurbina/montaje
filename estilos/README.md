# Estilos

El catálogo de ediciones con nombre. Sirve para dos cosas: **recordar** cada
edición que probamos (cómo se hizo, para qué sirve y lo que dijo Miguel) y
**elegir** según el guion de un video qué estilo va en cada tramo.

Se ve en el panel, en **`/estilos`** (`python montaje.py panel <p>` y el enlace
«estilos» de la portada): cada estilo con su muestra, sus filtros por estado, uso,
material y experimento (`en`: lo que salió de un ejercicio o de una noche). Desde la consola: `python montaje.py estilos [--para abrir]
[--material clips] [--estado aprobado]`, que además valida todos los archivos.

## Tres capas

| Capa | Qué es | Dónde vive |
|---|---|---|
| **Técnica** | lo que el motor sabe hacer: un modo (`collage`, `secuencia`, `pulso`…), un momento (`rafaga`, `destacado`…), un comando (`sincronizar`, `transformar`…) o una capa hecha en código (`recuerdo`, `fugas`…) | el código, `py/montaje/` |
| **Estilo** | una técnica con sus valores, un nombre, para qué sirve, con qué material, y el veredicto de Miguel | aquí, un archivo por estilo |
| **Guion** | el video partido en tramos, cada uno con lo que tiene que pasar y su estilo | el proyecto de cada video (`GUION.md`) |

De una técnica salen muchos estilos: el carrusel y el «acelerando» son la misma
ráfaga con valores y material distintos.

## Qué guarda un estilo

`estilos/<id>.json`; el `id` es el nombre del archivo.

| Campo | Qué es |
|---|---|
| `nombre` | cómo lo llamamos al hablar |
| `frase` | qué se ve, en una o dos líneas |
| `para` | para qué sirve en un guion (lista; vocabulario abajo) |
| `material` | con qué funciona: `fotos`, `clips`, `mixto`, `serie` (variaciones de una misma imagen), `cualquiera` (una capa que va encima de lo que sea) o `ninguno` (sale entero del código) |
| `energia` | qué le hace al ritmo: `calma`, `media`, `alta`, `sube` (de lento a rápido) o `sigue` (acelera y frena con la canción) |
| `dura` | cuánto ocupa, en palabras («un compás», «un tramo de la canción») |
| `tecnica` | la receta: exactamente uno de `modo`, `momento`, `comando` o `capa`, con los valores que la distinguen. Se copia a `montaje`, a `momentos` o a `sintesis` de un `proyecto.json` |
| `estado` | `aprobado`, `a medias`, `pedido`, `propuesta` o `rechazado` |
| `miguel` | lo que dijo Miguel, **con sus palabras**. Obligatorio si está aprobado, a medias o rechazado |
| `visto_en` | los experimentos donde se usó (su `FICHA.md` cuenta la historia completa) |
| `evitar` | dónde no va, y por qué. Un rechazo se guarda aquí para no repetirlo |
| `muestra` | (lo escribe `muestra`) de qué render y qué segundos salió la muestra |
| `veredicto` | (lo escribe la galería) el último veredicto dado con un clic: `estado`, `fecha`, `via`. Vale como las palabras de Miguel para validar un aprobado, a medias o rechazado |

### Vocabulario de `para`

`abrir` · `cerrar` · `transición` · `presentar la marca` · `mostrar el archivo` ·
`destacar` · `subir la energía` · `respirar` · `loop`

Es cerrado a propósito: el guion habla con estas palabras. Una nueva se agrega en
`PARA` de `py/montaje/estilos.py` y aquí, cuando un estilo de verdad la necesite.

## Las muestras

Unos segundos de un render, livianos (540 px de alto, H.264 CRF 30, audio a 96
kb/s: entre medio y dos MB), en `~/Videos/montaje/estilos/<id>.mp4`:

```
python montaje.py muestra <id> --de 13-variaciones/render/final.mp4 --desde 24.6 --hasta 32.6
```

**No van al repo**: el repo es público y las muestras usan material de Curiana y
de colaboraciones. Tampoco se borran al limpiar: lo que se borra después de
publicar son los renders, los análisis y las hojas de cada experimento. **La
receta y la muestra son lo que queda**: con eso alcanza para recordar y repetir
un estilo, y el disco no se llena con ejercicios.

Los estilos de los experimentos 01 a 11 no tienen muestra porque sus renders ya
se borraron; se corta la suya del próximo render que los use.

## El probador: el mismo banco para todos (2026-11-10)

Las muestras de arriba salieron de renders distintos, con otro material y otra canción:
no se comparan una al lado de la otra. Por eso Miguel eligió el **probador**: un banco fijo
(`proyectos/probador/proyecto.json`; hoy, ocho clips, cuatro fotos y 8 compases de La Añoranza)
donde cada estilo hace **otra** muestra, en `~/Videos/montaje/estilos/probador/<id>.mp4`.

```
python montaje.py probar --armar          # el banco
python montaje.py probar --todos          # la galería entera (lo que no cambió no se redibuja)
python montaje.py probar transicion-iris  # uno
```

En la galería cada tarjeta muestra las dos («en el probador» y «en su video») y una línea
con lo que dijo el probador: cuánto tarda en dibujarse contra el banco solo, si se parece
a su referencia y cuántas veces lo eligió Miguel entre dos. Las de un estilo que el banco
todavía no sabe probar dicen por qué. **Elegir entre dos** (`/estilos/comparar`) pone dos
de la misma familia lado a lado, sincronizados, y anota la elección en
`direccion/COMPARACIONES.json`.

El probador prueba **la receta**: si una muestra del probador no se parece a la de su
video, a la receta le falta algo que el video tenía, y conviene escribirlo en `tecnica`.

## El guion, en palabras

Miguel escribe el guion como un guion normal, en `proyectos/<p>/GUION.md`:

> Abre lento con el logo. Después los personajes, rápido, que se note que son
> muchos. En el puente respira con una sola imagen grande. Cierra con la firma.

Claude lo parte en tramos y propone un estilo para cada uno, debajo, en el mismo
archivo:

| Tramo | Lo que tiene que pasar | Material | Estilo | Por qué |
|---|---|---|---|---|
| 1 | abrir: el logo aparece | fotos de marca | `actos-pared` | aprobado como intro |
| 2 | los personajes, rápido | clips | — | no hay estilo aprobado de ráfaga con clips: ejercicio |
| … | | | | |

Para elegir: los que tienen el `para` y el `material` del tramo; primero los
aprobados; nunca uno cuyo `evitar` describa el tramo. Si no hay ninguno, el tramo
es un ejercicio (abajo). Miguel corrige la tabla; recién entonces se arma el
`proyecto.json`: con clips, cada fila de la tabla es un tramo de `tramos` en el
montaje (`desde`, `hasta`, las perillas del estilo y el `material`), y las capas
de síntesis llevan su `desde`/`hasta`. Ejemplo: `proyectos/19-anoranza-con-guion/`.

## Cómo crece: los ejercicios

Cada ejercicio de práctica es un experimento con número (como siempre) que
prueba **una técnica** en dos o tres versiones cortas. Antes, Claude pregunta
qué se busca; después, Miguel elige y dice por qué.

- Cada versión es un estilo: un archivo aquí, con su muestra.
- La elegida queda `aprobado`, con las palabras de Miguel en `miguel`.
- Las otras quedan `rechazado` (o `a medias`), con su porqué en `miguel` y en
  `evitar`. Lo que no queremos también se recuerda.
- Después del veredicto, los renders del ejercicio se pueden borrar.

## El veredicto, la vuelta de ejercicio y el recorrido (2026-11-09)

- **Veredicto desde la consola:** `python montaje.py veredicto <id> <estado> --cita
  "…"`. Es el mismo que usa la galería: una sola forma de escribir un estilo.
- **Veredicto en la galería.** Cada tarjeta de `/estilos` tiene «sí» (`aprobado`),
  «a medias» y «no» (`rechazado`), y un lugar para escribir qué le pareció. El clic
  cambia `estado` y deja `veredicto`; si Miguel escribió, sus palabras van a
  `miguel` y a `direccion/REGISTRO.md` con la fecha. «deshacer» lo devuelve a
  `propuesta` (las palabras ya anotadas quedan). Lo que haya que **evitar** a
  partir de un «no» lo escribe Claude después, leyendo esas palabras.
- **`python montaje.py ejercicio <p> [--final --muestra]`** corre todas las
  versiones de un experimento y corta la muestra de cada una en su estilo.
- **`python montaje.py recorrido [--en <experimento>] [--estado propuesta]`** arma
  un video con unos segundos de cada muestra y su nombre, en
  `<medios>/estilos/recorridos/`.
- **`python montaje.py guion <p>`** propone, para cada sección de la canción, los
  estilos de este catálogo que sirven (por `para`, `energia` y `material`; los
  aprobados primero, los rechazados nunca).
