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
| **Cámara lenta** | slow motion | El clip corre más despacio que la realidad. Repetir cuadros traba; inventar los que faltan (interpolación) la deja suave. | `velocidad` en `pulso`; `transformar --efecto lento` |
| **Temblor de cámara** | camera shake | El cuadro entero se sacude (la mano con el teléfono). Se mide para no elegir esos segundos. | la curva `temblor` de `clips` |
| **Temblor de proyector** | gate weave | El cuadro se mece apenas, como la película en el proyector. | `recuerdo.temblor` |

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
| **Tresillo** | triplet | El golpe partido en tres partes iguales en vez de dos o cuatro. Muchos tambores van así; cortar en corcheas o semicorcheas sobre un tresillo se siente a destiempo. | `subdivision: 3` en `sincronizar` |
| **Acelerando** | accelerando | Los cortes se apuran hacia un punto: de uno por golpe a uno por tresillo. | el `reloj` de `sincronizar` |
| **Anacrusa** | pickup, upbeat | Lo que entra justo antes del «uno» y lo anuncia. | `inicio` negativo en `sincronizar` |
| **Frase** (musical) | phrase | Un grupo de compases (cuatro, por lo general) que suena como una unidad. En `pulso` cada clip ocupa una frase. | `frase_compases` |
| **Salto** o **corte de salto** | jump cut | Corte entre dos momentos del mismo plano: el tiempo salta y el encuadre no. En `pulso`, al compás o al golpe. | `corte` en `pulso` |
| **Toma** | take, shot | Lo que se filmó de una vez, del botón al botón. Sus primeros y últimos instantes no se usan (el pulgar). | `BORDE_TOMA` en `clips.py` |
| **Copia de trabajo** | proxy | Una copia liviana del clip para editar (girada, en SDR, a cuadros parejos); el original no se toca. | `proxies/` de la biblioteca |
| **Volver a poner al pulso** | retime to the beat, beat-sync | Cambiar cuándo entra cada pieza de una ráfaga ya editada para que caiga en la rejilla de la canción, sin tocar el resto del video ni el audio. | comando `sincronizar` |
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
| **Fantasma** (nuestro nombre) | ghost, double exposure | Un clip transparente en `screen` sobre otro: el que viene se asoma antes (doble) o el que se va se queda un momento (estela). | `doble_golpes`, `estela_golpes` |
| **Relleno desenfocado** | blurred fill, blur pad | Un vertical en un cuadro horizontal: detrás, el mismo clip agrandado, desenfocado y oscuro, en vez de barras negras. | `encuadre: relleno` |
| **Barrido temporal** | slit-scan, time displacement | Cada fila de la imagen es de otro instante: lo que se mueve se estira y se dobla. | `transformar --efecto barrido` |
| **Estela de luz** | light trails, lagfun | Lo claro deja rastro y se apaga despacio, como una exposición larga. | `transformar --efecto estela` |

## La forma del video

| Nombre | En inglés | Qué es | Aquí |
|---|---|---|---|
| **Arco** o **curva de intensidad** | arc, intensity curve | Cómo sube y baja la tensión a lo largo del video. | `caos` (`curva_caos`, `peso_energia`) |
| **Actos** | acts | Tramos con un tratamiento propio. | I, II, III, IV y coda |
| **Subida, clímax, respiro** | build-up, drop/climax, breakdown | Las partes de una canción electrónica que el montaje puede seguir. | las secciones de `musica.png` |
| **Cortina** o **interludio** | ident, bumper, interstitial | Pieza corta de identidad del canal que corta el programa con su propio sonido. Lo que Miguel llama «interludios estilo Locomotion». | `ensamblar` + `ensamblaje` |
| **Coda** | outro, coda | El cierre después del clímax. | `coda` |
| **Guion** | script, edit plan | El video en palabras, partido en tramos, cada uno con lo que tiene que pasar. Aquí lo escribe Miguel y Claude le pone un estilo a cada tramo. | `proyectos/<p>/GUION.md`; con clips, `tramos` y `material` en `pulso` |
| **Estilo** | look, treatment, preset | Una técnica con sus valores, un nombre y para qué sirve: lo que se elige para un tramo del guion. | `estilos/<id>.json`, galería en `/estilos` |
| **Técnica** | technique | Lo que el motor sabe hacer (un modo, un momento, un comando, una capa). De una técnica salen muchos estilos. | `py/montaje/` |
| **Síntesis** (de video) | generative video, procedural | Imagen hecha en código, cuadro a cuadro, sin material: como `componer` hace música. | `sintesis` en proyecto.json, `src/Sintesis.tsx` |
| **Grano** | film grain | El ruido fino de la película, nuevo en cada cuadro. | `recuerdo.grano` |
| **Viñeta** | vignette | Los bordes del cuadro más oscuros: la mirada va al centro. | `recuerdo.vineta` |
| **Halo** | halation, bloom | Las luces se abren y brillan un poco más allá de su borde. | `recuerdo.halo` |
| **Fuga de luz** | light leak | Una mancha de luz cálida que entra por un borde, como la película velada. | capa `fugas` |
| **Visualizador** | audio visualizer | La música dibujada: aquí, su espectro como un horizonte. | capa `partitura` |
| **Duotono** o **tinta** | duotone | La imagen a dos colores: uno para las sombras, otro para las luces. | capa `tinta` |
| **Calima** (aquí) | heat haze, heat shimmer | El aire caliente que hace ondular lo que está detrás. | capa `calima` |
| **Aberración cromática** | chromatic aberration, RGB split | Los canales de color corridos, como en un tubo viejo o un lente barato. | capa `tv` |
| **Líneas de barrido** | scanlines | Las líneas horizontales de un televisor de tubo. | capa `tv` |
| **Caleidoscopio** o **espejo** | kaleidoscope, mirror | La imagen repetida en espejo hasta volverse un patrón simétrico. | `espejo` en `pulso` |
| **Mosaico de tiempo** (nuestro nombre) | time grid, delay grid | El mismo clip en una cuadrícula, cada celda un poco atrasada. | `rejilla` en `pulso` |
| **Díptico** o **pantalla partida** | split screen, diptych | Dos imágenes a la vez, una junto a otra. | `dividir: 2` en `pulso` |
| **Imagen congelada** | freeze frame | El clip se detiene en un cuadro. «La foto que despierta»: entra congelado y arranca. | `congelar_golpes` |
| **Reversa** | reverse | El clip hacia atrás. | `transformar --efecto reversa` |
| **Ida y vuelta** | boomerang, ping-pong | Hacia adelante y de regreso, sin costura. | `transformar --efecto ida-y-vuelta` |
| **Interpolación de cuadros** | frame interpolation, optical flow | Inventar los cuadros que faltan entre dos reales; la cámara lenta deja de trabarse. | `clips_interpolar` |
| **Rampa de velocidad** | speed ramp | El clip acelera y frena dentro de la misma toma. | `velocidad` muy abierta en `pulso` |
| **Muro de recuerdos** (nuestro nombre) | video wall | Una cuadrícula de clips distintos corriendo a la vez; cada celda cambia a su golpe. | `muro` en `pulso` |
| **Reencuadre** | reframing | Llevar un video a otro formato (3:2 → 9:16): recortar, dejarlo entero con relleno o a medio camino, siguiendo al sujeto. | `encuadre`, `seguir` |
| **Cola de película** | film leader, countdown | La cuenta regresiva antes de la imagen, con el pitido del 2 («2-pop»). | capa `cuenta`, `proyector` |

## El sonido

| Nombre | En inglés | Qué es | Aquí |
|---|---|---|---|
| **Diseño sonoro** | sound design | Los sonidos que no son la música ni la voz y que le dan cuerpo a lo que pasa en la imagen. | `sonorizar` |
| **Efecto** | sound effect, SFX | Un sonido puntual amarrado a una acción. | `py/montaje/sonido.py` |
| **Impacto** | hit, impact | Golpe grave que marca una llegada. | destacados |
| **Soplo** | whoosh, swoosh | Aire que pasa: acompaña un movimiento rápido. | barridos, vuelos |
| **Subida** | riser | Sonido que crece y desemboca en algo. | antes de cada ráfaga |
| **Cama** | bed, ambience | Un fondo continuo y bajo debajo de lo demás. | la estática del salvapantallas |
| **Agachar** (la música) | ducking, sidechain | Bajar la música un instante para que un efecto o la voz se oiga. | `sonido.agachar` |
| **Mezcla** | mix | El balance de volúmenes entre música, efectos y voz. | `sonido.efectos` |
| **Masterización** | mastering | El último ajuste de volumen para entregar: cuánto suena en total y hasta dónde llegan los picos. | `paquete` |
| **LUFS** | loudness units | Cómo de fuerte se percibe un audio entero. Las redes nivelan alrededor de −14. | `lufs` en publicacion.json |
| **Pico real** | true peak (dBTP) | El punto más alto de la onda; sobre 0 se rompe. Se deja en −1 por seguridad. | `pico` en publicacion.json |
| **Firma sonora** | sonic logo, mnemonic | Un motivo corto que identifica a la marca. | por hacer |

**Harness** (arnés) es el nombre que Miguel le dio al conjunto: el repo `montaje`
(lo que fabrica el video; en inglés también *rig*) más cómo trabaja Claude dentro
de él (la skill, la dirección y las vueltas de revisión). **Glitch** o **falla de
señal**: la imagen que se rompe como una cinta o una transmisión dañada
(separación RGB, desgarro horizontal, ruido); **TBC** (*time base corrector*): el
aparato que vuelve a estabilizar una señal de video analógica.

Las palabras de Miguel y su traducción: **«carrusel»** = ráfaga a pantalla completa (imágenes una tras otra en cortes secos al pulso); **«montaje sobre montaje»** = puesta en
abismo con ecos; **«composición infinita en el fondo»** = mosaico acumulativo
con cámara virtual; **«más caótico»** = la curva de caos. **«reel rápido de imágenes mientras un video corre»** = ráfaga sobre un video que sigue corriendo debajo; **«sincronización de video»** = volver a poner al pulso (`sincronizar`).

## Lo del laboratorio de la mañana (2026-11-09)

| En español | En inglés | Qué es | Dónde se mueve |
|---|---|---|---|
| transición | transition | cómo entra un clip sobre el que se va | `transicion` en `pulso` |
| cortina | wipe | un borde que barre el cuadro y descubre el clip nuevo | `transicion: cortina` |
| iris | iris wipe | un círculo que se abre (aquí, desde el sujeto) | `transicion: iris` |
| empuje | push | el clip que entra corre al que se va | `transicion: empuje` |
| destello | flash cut / dip to white | un fogonazo tapa el cambio | `transicion: destello` |
| persiana | blinds | franjas que se ensanchan hasta cerrarse | `transicion: persiana` |
| rótulo | caption / lower third | una frase en pantalla, al pulso | `sintesis: rotulos` |
| barras de cine | letterbox | franjas negras arriba y abajo (cinemascope 2,39:1) | `sintesis: barras` |
| rayones, manchas | scratches, dust and dirt | el daño de una película gastada | `sintesis: rayas` |
| la luz sigue a la canción | audio-reactive grade | brillo y color según la energía | `sintesis: luz` |
| ejercicio | — | una vuelta de versiones: plan, render, hoja, muestra | `python montaje.py ejercicio` |
| barrido de una perilla | parameter sweep | la misma base con un valor distinto en cada celda, lado a lado | `ejercicio --barrer` |
| borrador | proxy sin interpolar | la copia de trabajo rápida con la que se hacen los previews | `clips` (carpeta `borradores/`) |
| preview por tramos | render caching | guardar cada tramo dibujado para que corregir uno rehaga sólo ese | `render --preview` |
| lista de tomas | shot list | lo que hay que producir para un guion, toma por toma | `python montaje.py tomas` |
| mesa de selección | selects / logging | elegir a mano los clips antes de editar | `python montaje.py seleccion` |
| transcribir | transcription | de un audio al texto, con el segundo de cada palabra | `python montaje.py transcribir` |
| recorrido | showreel | la galería de corrido en un video | `python montaje.py recorrido` |
| esqueleto del guion | — | la canción en tramos con los estilos que sirven | `python montaje.py guion` |
| veredicto | — | sí, a medias o no, dado en la galería | `/estilos` del panel |
| fotos y clips juntos | mixed media | las fotos entran al reparto de `pulso` como clips quietos | `"fotos"` en el proyecto + `mezclar_fotos` |
| acercamiento lento de una foto | Ken Burns effect | la foto se acerca (o se aleja) y se desliza mientras está en pantalla | `zoom_foto` |
| revisar | QC (quality control) | medir un render: negro, cuadros repetidos, destellos, sonoridad | `python montaje.py revisar` |
| destellos por segundo | flash rate | fogonazos en un segundo; más de tres no se publica | lo cuenta `revisar` |

## Lo del probador (2026-11-10)

| En español | En inglés | Qué es | Dónde se mueve |
|---|---|---|---|
| probador, banco de pruebas | test bench | el mismo material para todos los estilos, para que las muestras se comparen | `python montaje.py probar` |
| cuadro de referencia | golden frame, reference frame | un cuadro guardado con el que se compara el de mañana para saber si algo cambió | `ref/` del probador |
| parecido (SSIM) | structural similarity | cuánto se parecen dos imágenes en forma y luz, de 0 a 1 | lo mide `probar` |
| elegir entre dos | pairwise comparison, A/B | mostrar dos y preguntar cuál; de muchas elecciones sale un orden | `/estilos/comparar` |
| prueba de regresión visual | visual regression test | volver a dibujar lo aprobado y comparar, para que un cambio no lo rompa sin aviso | `probar --todos` |

## La mesa analógica (2026-11-20)

| En español | En inglés | Qué es | Dónde se mueve |
|---|---|---|---|
| señal compuesta | composite video, CVBS | luma y color en un solo cable: el color montado en una subportadora de 3,58 MHz | entre aparatos de `analogo` |
| puntos que caminan | dot crawl | el color que se cuela en la luma: un damero que se mueve por los bordes de color | sale de `codificar`/`decodificar` |
| arcoíris, color falso | rainbow, cross-color | el detalle fino de luma que el televisor lee como color | ídem |
| filtro de muesca / de peine | notch / comb filter | cómo el televisor separa el color de la luma: el barato corta una banda; el fino resta la línea anterior | `pantalla.decodificador`, `captura` |
| color rebajado | color-under | el VHS graba el color en una banda angosta y baja: por eso se corre | `cinta` |
| cambio de cabezal | head switching noise | la costura abajo, donde un cabezal le pasa la cinta al otro | `cinta.cabezal` |
| tracking | tracking error | los cabezales fuera de la pista: una franja de ruido | `cinta.tracking` |
| base de tiempo | time base error, jitter, flagging, skew | las líneas que tiemblan y se tuercen porque la cinta no corre pareja | `cinta.temblor` |
| dropout | dropout | una raya blanca donde a la cinta le falta óxido | `cinta.desgaste` |
| generación | generation loss | copia de una copia: cada pasada suma ruido y quita detalle | `cinta.generaciones` |
| corrector de base de tiempo | TBC | el aparato que endereza las líneas | `tbc` |
| fantasma | ghosting, multipath | la señal rebotada que llega después: la imagen repetida, corrida a la derecha | `antena.fantasma` |
| nieve | snow | el ruido de una señal débil; con la señal muy baja, el color se apaga | `antena.nieve` |
| barra del zumbido | hum bar | la red eléctrica (60 Hz) contra los 59,94 campos: una barra que sube despacio | `antena.zumbido` |
| máscara de fósforos | aperture grille, shadow mask, slot mask | las franjas o puntos de color del vidrio del televisor | `pantalla.mascara` |
| colorizador | colorizer | el brillo convertido en colores, como en los sintetizadores de video | `colorizador` |
| relieve de barrido | Rutt/Etra scan processor | cada línea levantada según su brillo | `relieve` |
| wobbulator | wobbulator | bobinas que hacen ondular el barrido (Paik y Abe) | `iman.ondas` |
| realimentación | video feedback | la cámara que mira su propio monitor | `realimentacion` |
| cola de cometa | comet tail, image lag | lo claro que deja estela en una cámara de tubo | `camara.estela` |

## La película y lo digital (2026-11-21)

| En español | En inglés | Qué es | Dónde se mueve |
|---|---|---|---|
| película reversible | reversal film (Kodachrome, Ektachrome) | la que sale en positivo, sin copia: la de las películas caseras | `pelicula.emulsion` |
| paso a saltitos | 18 fps cadence, judder | 18 cuadros de película en 30 del video: cada uno dura dos o uno | `pelicula.cuadros` |
| vaivén | gate weave | el cuadro que baila en la ventanilla (el Super 8 no tiene uña de registro) | `pelicula.vaiven` |
| halo rojo | halation | la luz fuerte que rebota en la base y vuelve a la capa del rojo | `pelicula.halo` |
| desteñido | dye fading | los tintes que se van con los años: en la copia de color, el cian primero (queda rojo) | `pelicula.desvanecido` |
| densidad | density | lo que la película frena la luz (−log₁₀ de lo que deja pasar): ahí viven el grano y los tintes | `_en_la_densidad` |
| velo, quemado | fogging, flash frames | la luz que se cuela al principio y al final del rollo; los cuadros sobreexpuestos al arrancar | `pelicula.quemado` |
| filtro 85 | Wratten 85 | el naranja de la cámara para usar de día la película de luz artificial | `pelicula.balance` |
| escaneo con la tira | overscan, full-gate scan | el cuadro con su perforación y los vecinos, como sale del escáner | `pelicula.marco` |
| QCIF | QCIF | 176 × 144: el video de los celulares | `sensor.resolucion` |
| obturador rodante | rolling shutter | el sensor que lee línea por línea: lo que se mueve sale inclinado | `sensor.rodar` |
| mancha vertical | CCD smear | la columna clara que deja una luz fuerte en un CCD | `sensor.mancha` |
| borde morado | purple fringing | el morado alrededor de lo que se quema | `sensor.franja` |
| cuadro clave, GOP | keyframe, I-frame, GOP | el cuadro que el códec guarda entero; entre dos, sólo lo que cambió | `compresion.gop` |
| bloques | blocking, macroblocks | la imagen en cuadraditos cuando faltan bits | `compresion.calidad` |
| datamosh | datamosh | sin cuadro clave, el códec mueve la imagen vieja con el movimiento de la nueva | `compresion.residuo` |
| dropout digital | DV dropout | rectángulos con colores equivocados o con un pedazo del cuadro de al lado | `compresion.errores` (`dv`) |
| campo, entrelazado | field, interlace, combing | cada cuadro de video eran dos campos (las líneas pares y las impares) de instantes distintos: lo que se mueve se peina | `casetera.entrelazado` |
| pausa de un campo | field still | la pausa de la casetera: la mitad de las líneas, repetidas, con la barra de ruido | `casetera.pausa` |
| memoria de cuadro | frame store, frame synchronizer | lo que guardaba la consola de mezcla para sus efectos | `consola` |
| estrobo | strobe | la imagen retenida que salta a golpes | `consola.efecto` |
| multi | multi-picture | la pantalla partida en 4, 9 o 16 que se llena con momentos distintos | `consola.efecto` |
| posterizado | paint, posterization | cada color en pocos escalones, como un afiche | `consola.efecto` (`pintura`) |
| llave de luma | luma key | donde la imagen es oscura (o clara), se ve otra | `consola.efecto` (`llave`) |
| mancha de luz | hot spot | el centro de la imagen proyectada, más claro que los bordes | `proyector.mancha` |
| trapecio | keystone | la imagen proyectada más ancha arriba, con el proyector inclinado | `proyector.trapecio` |
| negativo de color, copia de laboratorio | color negative, minilab print | el rollo de fotos revelado y copiado en papel: menos contraste, el negro del papel | `pelicula.emulsion` (`kodak-gold`, `fuji-superia`) |
| banda magnética | magnetic stripe | el sonido grabado en una tira de óxido al borde de la película | `pelicula.sonido` |
| aberración cromática lateral | lateral (transverse) chromatic aberration | cada color sale a otra escala: bordes rojos y azules hacia las esquinas | `lente.aberracion` |
| barril, ojo de pez | barrel distortion, fisheye | las rectas se curvan hacia afuera | `lente.barril` |
| destello, fantasmas | lens flare, ghosts | la luz que rebota entre los vidrios, en la línea que pasa por el centro | `lente.destello` |
| raya anamórfica | anamorphic streak | el destello estirado de lado, azulado | `lente.raya` |
| difusión, niebla | diffusion, veiling glare | lo claro que se derrama y los negros que suben | `lente.niebla` |
| golpe congelado | freeze frame | la imagen quieta en el golpe | `pulso.congelar_golpe` |
| tartamudeo | stutter edit | el pedacito del golpe repetido | `pulso.tartamudeo` |
| paso de cuadro | step printing, frame step | cada cuadro dura dos: el movimiento a saltos | `pulso.paso_de_cuadro` |
