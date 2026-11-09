# 21 · Laboratorio de la mañana

**Fecha:** 2026-11-09 (de 6:13 a 7:59, antes de que Miguel empezara el día)

## Idea

Miguel, al despertar y ver lo de la noche: «aún tenemos tiempo de hacer algo más.
Revisa lo que tenemos hasta ahora y mejora lo más posible hasta las 7:59 am. Le
interesa que el motor tanto en entrenamiento como en sinterización de videos y
además propone que más podemos hacer para el motor».

Mismo material y canción que el 15 (los 20 clips de `practica`, «La Añoranza de
Natalia»). Dos frentes:

- **Sintetización:** lo que al motor le faltaba para editar clips —cómo pasar de
  uno a otro sin que sea siempre un fundido— y cuatro capas hechas en código.
- **Entrenamiento:** que una vuelta de ejercicios cueste un comando y que el
  veredicto se dé en la galería, sin dictarlo.

Cada versión es una prueba corta y un estilo `propuesta` con su muestra (filtro
«en 21-laboratorio-de-la-manana» en `/estilos`).

## Lo que se probó

| Versión | Qué | Lo que salió (mirado en hojas) |
|---|---|---|
| `cortina` | un borde blando barre el cuadro; alterna derecha e izquierda | limpio; el borde blando evita la raya dura |
| `iris` | un círculo se abre desde el **centro de interés** del clip que llega | en el cementerio se abre desde la persona que camina, no desde el centro del cuadro |
| `empuje` | el clip que entra corre al que se va | los dos se mueven en los mismos cuadros, sin hueco |
| `destello` | un fogonazo cálido tapa el cambio | en la primera versión el clip nuevo aparecía de golpe *antes* de la luz; ahora aparece debajo, en el tope del fogonazo (mirado cuadro a cuadro) |
| `zoom` | el clip nuevo llega agrandado y desenfocado y se asienta | |
| `persiana` | franjas verticales que se ensanchan | con palmeras o rejas se confunde con la imagen |
| `ronda` | las seis, una por cambio | sirve de catálogo, no de estilo |
| `rotulos` | frases del guion abajo, en itálica, palabra por palabra a la corchea | se leen; la letra va según el lado menor del cuadro para que sirva en vertical |
| `rotulos-cartel` | dos o tres palabras grandes al centro, una por golpe | con cinco palabras la última casi no se alcanzaba a leer: ahora cada frase se queda dos golpes después de completarse |
| `luz` | brillo y color siguen la energía de la canción | en 2:18, cuando la canción se apaga, la imagen se oscurece y se destiñe |
| `barras` | franjas de cinemascope que se cierran en cuatro golpes | |
| `rayas` | rayones que duran un rato, manchas de un cuadro, con grano | sutil; a tamaño de teléfono los rayones casi no se ven |
| `mixto` | **fotos y clips juntos**: los clips del mar intercalados con fotos del campo, con cortina | la primera prueba (cada clip seguido de sus propios fotogramas) no se leía: era la misma escena quieta quince segundos. Intercalando clip y foto de escenas distintas, sí |

Las frases de los rótulos son de práctica, escritas por Claude (del `GUION.md` del
19 y de los nombres de los clips). **No son la letra de la canción.**

## Técnica nueva (motor)

- `pulso`: **`transicion`** (`fundido`, `cortina`, `iris`, `empuje`, `destello`,
  `zoom`, `persiana`, o `ronda`) y `transicion_dir`. Dura lo que el fundido entre
  clips; el primero del video siempre sale del negro; dentro de un `tramo` del
  guion se puede cambiar. En el timeline: `transicion` en la capa que entra y
  `empujada` en la que sale.
- Síntesis: **`rotulos`** (con `tiempos` por palabra queda lista para los
  subtítulos de una voz en off), **`luz`** (filtro), **`barras`** y **`rayas`**.
- **Fotos y clips en el mismo montaje:** `"fotos": "<carpeta>"` en el proyecto y
  `"mezclar_fotos": true` en el montaje. La foto entra al catálogo de clips como un
  clip quieto y `pulso` le da el movimiento (acercamiento lento, una sí y una no se
  aleja). En `material`, `foto:` y `clip:` eligen sólo unas u otros. Las únicas
  fotos de la biblioteca de práctica son los fotogramas del 17, sacados de los
  mismos clips: falta probarlo con fotos de verdad (la galería de Curiana).
- **`ejercicio <p>`**: planifica cada versión, renderiza su tramo de prueba, saca
  su hoja y, con `--muestra`, corta la muestra de su estilo. Cada versión dice cómo
  se prueba: `"prueba": [desde, hasta]`, `"estilo": "<id>"`, `"muestra": [a, b]`.
  Todo este experimento se corrió así.
- **`ejercicio --barrer perilla=valor,valor,…`**: la misma base con una perilla en
  cada valor, lado a lado y sincronizadas en un solo video. Probado con
  `fundido_golpes=0.5,1,2,4` sobre `cortina`: en el mismo cuadro, la cortina de
  medio golpe ya terminó, la de uno va por la mitad y las de dos y cuatro recién
  empiezan (`render/barrido-cortina-fundido_golpes.mp4`).
- **`revisar <p> <video>`**: mide un render entero —negro, imagen quieta, cuadros
  repetidos, cortes, destellos por segundo, sonoridad— y avisa lo que conviene
  mirar. `ejercicio` lo corre sobre cada versión. El `destello` mide un fogonazo
  por segundo, bajo el límite de tres.
- **`recorrido`**: la galería de corrido en un video liviano, desde las muestras
  (sirve aunque los renders ya no estén).
- **`guion <p>`**: el esqueleto del guion —la canción en tramos, con los estilos de
  la galería que sirven en cada uno—; lo que tiene que pasar lo escribe Miguel. Además
  imprime un primer armado planificable (la receta del primer estilo que sirve en cada
  tramo, sus capas y sus «ojo»): hoy elige casi todo entre propuestas; con veredictos,
  elige lo aprobado.
- **En el panel:** botones «Esqueleto del guion» y «Correr todas las versiones»
  (el ejercicio, a media resolución), además del veredicto.
- **El veredicto en la galería:** cada tarjeta de `/estilos` tiene «sí», «a
  medias», «no» y un lugar para escribir. Se guarda en el archivo del estilo; con
  palabras, también en `direccion/REGISTRO.md`. Lo mismo desde la consola, para lo
  que Miguel diga en el chat: `python montaje.py veredicto <id> aprobado --cita "…"`.
- Pruebas nuevas para todo lo anterior (`python -m pytest py/pruebas -q`).

## La revisión del motor

Mientras se escribía lo nuevo, otra sesión de Claude revisó a ciegas el código de la
noche buscando defectos (sin tocar nada). Encontró quince comprobados y varios probables; se arreglaron
midiendo la planificación de las 53 versiones antes y después:

| Qué pasaba | Medido antes → después |
|---|---|
| **El doble no empalmaba:** el fantasma del clip que viene iba por otro segundo del clip que la toma de verdad, y al entrar la imagen saltaba. Con clips cortos la toma arranca al principio del clip y antes no hay material: ahora el fantasma va más lento para llegar justo. | salto de hasta 1,69 s → 0,18 s como mucho (16 `doble-siempre`: 26 de 27 sin empalmar → 8, todos bajo 0,2 s) |
| **Las estelas se perdían sin aviso** cuando al clip no le quedaba material. Ahora van más lentas en vez de no salir. | 15 `b`: 32 estelas en 54 cambios → 54; `c`: 6 de 27 → 27 |
| **Un tramo del guion valía recién desde la primera frase que empezaba dentro de él.** Ahora el borde de un tramo corta la frase (al compás más cercano), y avisa si un tramo no alcanza a tener un compás propio. | 19: «el silencio» empezaba 3,9 s tarde → 1,3 s antes de su segundo (el «uno» más cercano) |
| El recorte que sigue al sujeto miraba dónde iba la toma *antes* de acomodarla en su clip. | 16 `reel-recorte`: 11 de 20 tomas con el recorte corrido (hasta 130 px) → 0 |
| El muro podía pasar del final de un clip; `muro_golpes: 0` rompía. | 7 capas pasadas → 0 |
| La cuenta regresiva usaba un golpe promedio. | el «1» llegaba 5 cuadros tarde → cada número en su golpe |
| Las copias de los clips transformados se interpolaban dos veces (72 → 60 → 120 cps). | rehechas a 72 cps |
| `transformar` sin `--clip` transformaba también lo ya transformado. | sólo los originales |
| `render --hasta` rendía un cuadro de más; `"fundido": 0` en un título tumbaba el render; el fogonazo del destello se pintaba sobre los títulos; entre un clip y su variante transformada no había fundido; con poco material una toma podía ir *más rápido* de lo pedido; el fundido final podía ser más largo que la última toma. | arreglados, con prueba donde se pudo |
| Los fantasmas (doble y estela) iban siempre a pantalla completa y al centro: con un recorte que sigue al sujeto, una ventana o un díptico quedaban corridos respecto de su clip. Ahora copian el lugar, el tamaño y el acercamiento de la capa de verdad. | 20 en 9:16: las 6 estelas, corridas → sobre su clip |
| El catálogo de clips es uno por biblioteca: sumar una carpeta en un experimento le cambiaba el reparto a los demás. | cada experimento ve sólo sus carpetas |

**Segunda revisión, sobre el código de esta misma mañana** (otra sesión, doce minutos, sólo lectura): nueve defectos comprobados.

| Qué pasaba | Cómo quedó |
|---|---|
| **`revisar` contaba mal los destellos**, en los dos sentidos: tres fogonazos (lo permitido) daban cinco, y un estrobo en rampa daba cero porque sólo miraba saltos entre cuadros seguidos. | sigue la luz de extremo a extremo y cuenta idas y vueltas: tres son tres, la rampa se ve, un corte a una escena clara no cuenta |
| **La cita del veredicto se podía dañar**: quitaba comillas de cada punta por separado («lento» al entrar… perdía la primera), y un salto de línea podía escribir un título falso en el registro. Además, guardar desde el navegador cambiaba el formato de los números del archivo. | el veredicto lo escribe Python (`montaje.py veredicto`, el mismo que escribe todos los estilos): una línea, comillas de adentro intactas, el archivo cambia sólo en lo que cambió |
| **Los rótulos perdían palabras sin avisar**: dos frases en el mismo golpe (desaparecía la primera) o una frase que no terminaba de escribirse antes de la siguiente. | la segunda se corre al golpe siguiente; las palabras se apuran para caber y quedar completas un golpe, con aviso |
| El doble, cuando tenía que asomarse lento para empalmar, seguía lento después del cambio y se iba quedando atrás de la toma. | va en dos tramos: lento hasta el cambio y, desde ahí, pegado a la toma de verdad |
| En `ronda`, cada transición salía siempre hacia el mismo lado; con `empuje` y tomas muy cortas, la que salía se arrastraba más cuadros que la que entraba; `zoom_foto` negativo destapaba el fondo; una versión mal escrita cortaba todo el ejercicio. | arreglados, con prueba |

Y uno que encontré yo mirando la hoja de la pieza del guion ya arreglada: el borde de un
tramo a un compás de un cambio de sección dejaba entre los dos un clip de un solo compás
(a los 2:28 aparecía el mar y ya se estaba yendo). El primer remedio —unir las frases
sueltas— cambiaba también la pieza del 20, que no tenía nada que ver; se deshizo. Quedó
así: si el borde de un tramo cae a un compás de un cambio de sección, el corte es uno
solo, el del tramo.

**La versión `a` del 15 (la aprobada) y todas sus variantes planifican idéntico.**
Cambian `b`, `c`, el 19, el 20 y cuatro versiones del 16: sus timelines del repo ya
están replanificados y los renders nuevos llevan `-arreglado` en el nombre (los de la
noche quedan al lado para comparar).

Lo que la revisión encontró y **no** se arregló (queda anotado):

- El muro ignora `zoom`, `encuadre` y los fundidos de inicio y final.
- El color de `partitura` no acepta los nombres de la paleta.
- Los bordes de los tramos se ajustan al compás: si el guion pone un borde a mitad
  de compás, las capas de síntesis (que van por segundos) entran hasta un compás y
  medio corridas respecto del primer clip. `guion` ya propone los bordes en el «uno».

## Renders

`~/Videos/montaje/21-laboratorio-de-la-manana/render/` (tramos de 14 a 35 s) y
`~/Videos/montaje/estilos/recorridos/` (el recorrido).

## Lo que dijo Miguel

(pendiente)
