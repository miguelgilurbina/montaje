# Glosario de montaje

Los nombres que usamos para hablar de la edición, con su equivalente en inglés
(así aparecen en tutoriales y programas) y **dónde vive cada cosa en nuestro
sistema**: el parámetro de `proyecto.json` o el campo de `timeline.json` que la
controla. Si dices la palabra, ya sé qué perilla mover.

## Cómo se junta una imagen con otra

| Nombre | En inglés | Qué es | Aquí |
|---|---|---|---|
| **Corte seco** | hard cut | De una imagen a otra sin transición. | `entrada` de 1 cuadro |
| **Fundido** (de entrada / de salida) | fade in / fade out | La imagen aparece desde el fondo o se pierde en él. | `entrada`, `salida` |
| **Fundido encadenado** o **disolvencia** | cross-dissolve | Una se va mientras la otra llega. | el relevo del acto I |
| **Sobreimpresión** | superimposition | Dos imágenes visibles a la vez, una a través de la otra. | modo `superposicion` |
| **Doble exposición** | double exposure | Sobreimpresión donde se suman las luces: lo claro de una se ve sobre lo oscuro de la otra. | `mezcla: "screen"` |
| **Modo de fusión** | blend mode | La regla con que se combinan dos capas. *Trama* (screen) suma luces, *Multiplicar* (multiply) suma sombras, *Aclarar* (lighten) se queda con lo más claro, *Diferencia* invierte. | `mezcla` |
| **Calado** o **difuminado de bordes** | feather | El borde de la imagen se funde con el fondo en vez de cortar en seco. | `borde`, `borde_pared` |
| **Máscara** | mask | Lo que decide qué parte de una imagen se ve. El calado es una máscara. | — |

## Cómo se mueve la imagen

| Nombre | En inglés | Qué es | Aquí |
|---|---|---|---|
| **Efecto Ken Burns** | Ken Burns effect | Zoom lento y deriva sobre una foto fija, para darle vida. | `zoom`, `deriva` |
| **Cámara virtual** | virtual camera | Mirar un lienzo más grande que el cuadro, como si una cámara lo recorriera. | `camara` |
| **Acercamiento / alejamiento** | push-in / pull-back | La cámara se acerca o se aleja (aquí, de la pared). | `encuadre` |
| **Paneo** | pan | La cámara se desplaza de lado. | la cámara siguiendo la pieza nueva |
| **Golpe de zoom** | zoom punch, beat zoom | Un empujón breve de zoom en el pulso. | `golpe_camara` |
| **Barrido** o **paneo rápido** | whip pan, swish pan | La cámara salta de lado tan rápido que el cuadro se vuelve otro. | `momentos` de tipo `barrido` |
| **Vuelo** (nuestro nombre) | — | La protagonista viaja a su lugar en la pared. | `vuelo`, `vuelo_golpes` |

## Cómo se ordena en el tiempo

| Nombre | En inglés | Qué es | Aquí |
|---|---|---|---|
| **Corte al pulso** | cutting on the beat | Los cambios caen en los golpes de la música. | la rejilla de golpes y semicorcheas |
| **Montaje métrico** | metric montage | Cortes de duración fija, como un metrónomo, sin mirar el contenido. (Eisenstein) | — |
| **Montaje rítmico** | rhythmic montage | El ritmo de cortes sigue al movimiento o la energía. | la densidad sigue a la energía |
| **Montaje tonal** | tonal montage | Se encadena por tono: luz, color, forma. | `orden: luz-y-tono`, la continuidad de color |
| **Montaje intelectual** | intellectual montage | Dos imágenes juntas crean una idea que ninguna tiene sola. | lo que buscamos en los cruces |
| **Efecto Kuleshov** | Kuleshov effect | Una imagen cambia de sentido según la que tiene al lado. | — |
| **Raccord** o **corte por coincidencia** | match cut | Pasar a otra imagen que comparte forma, color o posición. | la elección por tono de `_elegir` |
| **Montaje acumulativo** | accumulative montage | Las imágenes se suman en vez de reemplazarse. | la pared |
| **Parpadeo** o **montaje estroboscópico** | flicker, strobe montage | Imágenes tan breves que casi no se leen: se perciben como textura. | el acto IV (15 por segundo) |
| **Cambio de tempo** | tempo change | El ritmo de cortes cambia de golpe: se detiene, se duplica, se parte a la mitad. | el collage que se detiene en un destacado |
| **Medio tiempo / doble tiempo** | half-time / double-time | Cortar la mitad o el doble de seguido que el pulso. | los niveles: compás, golpe, corchea, semicorchea |
| **Ráfaga** o **montaje de destellos** | flash cut, rapid montage | Una serie de imágenes a pantalla completa en cortes secos muy cortos. | `momentos` de tipo `rafaga` |
| **Destacado** o **plano de detalle** (aquí, «héroe») | spotlight, hero shot | Una imagen se aísla del resto y ocupa el cuadro un momento. | `momentos` de tipo `destacado` |

## Cómo se compone el cuadro

| Nombre | En inglés | Qué es | Aquí |
|---|---|---|---|
| **Fotomontaje** o **collage** | photomontage, collage | Varias imágenes en un mismo cuadro. | todo el modo `actos` |
| **Mosaico** o **retícula** | mosaic, grid | Imágenes ordenadas en filas o celdas. | la pared: `fila`, `hueco` |
| **Pantalla dividida** | split screen | El cuadro partido en zonas con imágenes distintas. | — |
| **Puesta en abismo** o **efecto Droste** | mise en abyme, Droste effect | Una imagen que se contiene a sí misma. Tu «montaje sobre montaje». | los `ecos` de tipo `lejos` |
| **Eco** o **estela** | echo, trails | Una copia de la imagen retrasada en el tiempo, superpuesta a la actual. | `ecos`, `desfase` |
| **Retroalimentación de video** | video feedback | La cámara filmando su propia pantalla: copias dentro de copias. | pariente de los `ecos` |

## La forma del video

| Nombre | En inglés | Qué es | Aquí |
|---|---|---|---|
| **Arco** o **curva de intensidad** | arc, intensity curve | Cómo sube y baja la tensión a lo largo del video. | `caos` (`curva_caos`, `peso_energia`) |
| **Actos** | acts | Tramos con un tratamiento propio. | I, II, III, IV y coda |
| **Subida, clímax, respiro** | build-up, drop/climax, breakdown | Las partes de una canción electrónica que el montaje puede seguir. | las secciones de `musica.png` |
| **Coda** | outro, coda | El cierre después del clímax. | `coda` |

Las palabras de Miguel y su traducción: **«montaje sobre montaje»** = puesta en
abismo con ecos; **«composición infinita en el fondo»** = mosaico acumulativo
con cámara virtual; **«más caótico»** = la curva de caos.
