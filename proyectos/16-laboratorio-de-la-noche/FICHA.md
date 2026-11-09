# 16 · Laboratorio de la noche

**Fecha:** 2026-11-08/09 (de noche, mientras Miguel dormía)

## Idea

Miguel, al irse a dormir: «le saques el jugo. No tienen que ser tramos completos
de la canción de 3 min. Puedes iterar y probar todos los formatos posibles. La
idea es que mañana tengamos una galería surtida y nutrida. Y experiencia».

Mismo material y canción que el 15 (los 20 clips de `practica`, «La Añoranza de
Natalia»). Cada versión es una prueba corta (10 a 24 s) para la galería, casi
todas sobre la base de «una toma por frase», la que Miguel aprobó del 15. Cada
una es un estilo `propuesta` con su muestra en `/estilos` (filtro «en
16-laboratorio-de-la-noche»).

## Lo que se probó

| Versión | Qué | Lo que salió |
|---|---|---|
| `reel-relleno` | 9:16 con el 3:2 entero y relleno desenfocado | el clip queda en un tercio del alto: chico en el teléfono |
| `reel-recorte` | 9:16 recortado, **siguiendo al sujeto** | mejor que centrado (comparado: `reel-recorte-centro-final`); falla con dos sujetos separados |
| `cuadrado` | 1:1 recortado | a estos 3:2 les queda bien |
| `retrato-4-5` | 4:5 con relleno | el vertical más equilibrado |
| `panoramico-16-9` | 16:9 recortado | pierde 11 % del alto, sin problema |
| `diptico` | dos clips lado a lado (el mar con el campo) | funciona; con el recorte que sigue al sujeto el pesquero queda entero |
| `foto-que-despierta` | cada clip entra congelado y en sepia, arranca en el golpe | con 2 golpes de congelado (= el fundido) no se notaba; con 4 sí (medido: quieta 0,23, despierta 2,17) |
| `ventana` | el clip al 62 % con sombra sobre un `campo` | elegante; buena para abrir o cerrar |
| `rampa` | velocidad de 0,3× a 1,4× según la energía | |
| `doble-siempre` | doble exposición en cada cambio | |
| `salto-al-golpe` | un salto dentro del clip en cada golpe | con clips de 5 s repite momentos |
| `transformados` | cada clip usa su variante (barrido, reversa, ida y vuelta, eco, estela) | |
| `tinta-*`, `postal`, `calima-recuerdo`, `partitura-sobre-clips` | combinaciones de síntesis | la tinta eléctrico/ácido enferma la imagen: a lo sumo un golpe |
| `titulos`, `cuenta-y-pelicula` | título al pulso, «sonando ahora», cuenta regresiva, tira de película | funcionan; las letras de la marca no están instaladas (Bahnschrift y Georgia de reemplazo) |
| `onda`, `foco`, `golpe-de-zoom` | efectos al golpe | la onda salía en serrucho: se suavizó; el foco cansa en un video entero |

## Técnica nueva (motor)

- `pulso`: `congelar_golpes`, `dividir: 2`, `escala` + `sombra`, `doble_en`,
  `transformados`, `seguir` (el recorte sigue al centro de interés de cada clip,
  `cx`/`cy` en el catálogo) y `tramos` (ver el 19).
- Una versión puede traer su `salida` y su `sintesis`.
- Síntesis: `titulo`, `credito`, `cuenta`, `pelicula`, `onda`, `foco`, `golpe`
  (además de las del 15).
- `transformar`: `reversa`, `ida-y-vuelta`; la fuerza de `estela` y `eco` en
  segundos.

## Renders

`~/Videos/montaje/16-laboratorio-de-la-noche/render/` (tramos de 10 a 24 s).

## Arreglos del motor (2026-11-09)

La revisión del motor (ver la ficha del 21) cambia ocho versiones: `reel-recorte`, `cuadrado`,
`panoramico-16-9` y `diptico` (el recorte que sigue al sujeto miraba la toma antes de acomodarla:
en `reel-recorte`, 11 de 20 tomas corridas hasta 130 px), `doble-siempre` (26 de 27 dobles sin
empalmar; 6 estelas de 27), `muro` (7 tomas pasaban del final de su clip), `transformados` (copias
de trabajo interpoladas dos veces) y `cuenta-y-pelicula` (la cuenta fuera del golpe). Los tramos se
volvieron a renderizar y **sus muestras de la galería se rehicieron** con los mismos segundos. El
resto de las versiones planifica idéntico.

## Lo que dijo Miguel

(pendiente)
