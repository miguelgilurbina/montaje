# Propuestas para el motor

Lo que Claude propone para seguir, escrito el 2026-11-09 después del laboratorio de
la noche (15–20) y el de la mañana (21). Miguel pidió: «propone que más podemos
hacer para el motor», en sus dos frentes: **el entrenamiento** (cómo los ejercicios
se vuelven galería y criterio) y **la sintetización** (lo que el motor sabe dibujar
y montar).

Salvo lo tachado, nada de esto está hecho. Cada propuesta dice qué da, qué necesita de Miguel y si
hay que bajar algo (las descargas esperan su sí). El orden dentro de cada grupo es
el recomendado.

## Entrenamiento: que el motor aprenda de los veredictos

| # | Qué | Qué da | Qué necesita |
|---|---|---|---|
| E0 | **Juzgar la galería.** Hay 58 propuestas sin veredicto. `guion` ya arma un primer montaje con el primer estilo que sirve en cada tramo y prefiere lo aprobado: hoy elige casi a ciegas. | Cada «sí» o «no» mejora lo que el motor propone solo. | Media hora de Miguel en `/estilos` (o el recorrido en el teléfono y dictar). |
| E1 | **Leer los veredictos como datos.** Con la galería juzgada, un comando que compare las recetas aprobadas contra las rechazadas, perilla por perilla (largo de frase, fundidos, velocidad, capas), y diga lo que se repite: «lo que aprobaste va lento y con fundidos de dos golpes o más». | El criterio de Miguel deja de estar sólo en su cabeza y en las citas: los valores por defecto y el esqueleto del guion se inclinan hacia lo que eligió. | Los veredictos (ahora se dan con un clic en `/estilos`). Con menos de unos veinte, lo que salga es una pista, no una regla. |
| E2 | **Elegir entre dos.** En la galería, dos muestras lado a lado y una sola pregunta: ¿cuál? De muchas comparaciones sale un orden. | Juzgar sesenta tarjetas una por una cansa; comparar de a dos es rápido y da más información que sí/no. | Nada. Una tarde de trabajo en el panel. |
| E3 | ~~Barrer una perilla.~~ **Hecho el mismo 2026-11-09:** `ejercicio --barrer fundido_golpes=0.5,1,2,4` deja las variantes lado a lado, sincronizadas, en un video. | Afinar un valor mirando, sin escribir cuatro versiones a mano. Es la forma natural de un ejercicio: «¿cuánto fundido?». | Que Miguel elija la celda. |
| E4 | **Lo aprobado no se rompe.** La mitad ya está (2026-11-09): `py/pruebas/planes.py` planifica todas las versiones fuera del repo y dice cuáles cambian con un cambio al motor. Falta la otra mitad: guardar unos cuadros de referencia de cada estilo aprobado y compararlos, para lo que cambia en el dibujo (React) y no en el plan. | Un cambio al motor no altera un estilo aprobado sin que nadie lo note. | Nada; unos MB de cuadros en los medios. |
| E5 | **El ejercicio desde el panel.** El botón que corre la vuelta ya está (2026-11-09) y muestra la salida con las medidas; falta que el panel muestre las versiones y sus hojas una al lado de la otra. | Miguel puede lanzar y mirar un ejercicio sin Claude. | Nada. |

## Sintetización: lo que el motor todavía no sabe

| # | Qué | Qué da | Qué necesita |
|---|---|---|---|
| S1 | **Voz en off y subtítulos.** Miguel graba; Whisper marca el segundo de cada palabra; el texto sale del guion, no de lo que Whisper oye. Los `rotulos` ya aceptan un tiempo por palabra: falta el oído. | El primer video con la voz de Miguel. Es lo que más cambia lo que el motor puede hacer. | **Descarga con ok:** faster-whisper y un modelo (alrededor de 1,5 GB el mediano). Una grabación de prueba. |
| S2 | ~~Fotos y clips en el mismo montaje.~~ **Hecho el mismo 2026-11-09** (`"fotos"` + `mezclar_fotos`; ver la ficha del 21). Falta probarlo con fotos de verdad: en la práctica sólo había fotogramas de los mismos clips. | El material real de Curiana es mixto: la galería de imágenes más lo que Miguel graba. | Un puñado de fotos de la galería junto a los clips. |
| S3 | **Igualar el color entre clips.** Llevar todos los clips hacia uno de referencia (o hacia la paleta), antes de montar. | Veinte clips de días y luces distintas se ven como una sola película. | Elegir el clip de referencia. Sin descargas (este ffmpeg ya trae lo necesario). |
| S4 | **Cortar en el movimiento.** Elegir el punto de corte donde lo que se mueve en el clip que se va y en el que llega van hacia el mismo lado o están en el mismo lugar del cuadro (ya se mide el centro de interés y el movimiento de cada clip). | El corte se siente continuo en vez de casual: es lo que distingue un montaje de una sucesión. | Nada. Hay que probarlo con clips que tengan movimiento claro. |
| S5 | **Saber dónde hay una cara.** El recorte a vertical hoy sigue «lo que se mueve y tiene detalle»; con un detector de caras y personas, sigue a la persona y nunca la corta, y los rótulos no caen encima. | Los verticales para redes salen bien sin mirar clip por clip. | **Descarga con ok:** un detector liviano (decenas de MB). |
| S6 | **Estabilizar lo que tiembla.** Este ffmpeg ya trae `vidstab`. Los clips que pasen de un umbral de temblor se estabilizan al hacer la copia de trabajo. | Los clips del teléfono caminando dejan de marear en cámara lenta. | Clips que tiemblen: los veinte de la práctica casi no tiemblan (medido), así que no hay con qué probarlo. |
| S7 | **El sonido de los clips.** Dejar el mar o el viento del clip por debajo de la canción, bajando cuando la canción sube. | El video respira: no es sólo imagen con música encima. | Clips con sonido que valga. Claude no oye: los niveles se miden y el oído es de Miguel. |
| S8 | **Las letras de la marca.** Archivo Black y Lora no están instaladas; títulos y rótulos salen con reemplazos (Bahnschrift, Georgia). | Los textos se ven como Curiana. | **Descarga con ok:** las dos fuentes de Google Fonts (licencia abierta, menos de 1 MB). |
| S9 | **Zonas seguras por red.** Mostrar en el panel dónde Instagram y TikTok tapan el cuadro (nombre, botones, descripción) y avisar si un rótulo o un sujeto cae ahí. | Lo que se publica no queda tapado por la interfaz de la red. | Nada. |

## Lo que quedó anotado de las revisiones del motor

Dos revisiones independientes del código (2026-11-09) encontraron 24 defectos; se arreglaron
casi todos (ver la ficha del 21). Quedan, sin urgencia:

- El **muro de recuerdos** ignora `zoom`, `encuadre` y los fundidos de inicio y final: termina sin fundido.
- `revisar` mide los **destellos** por la luz media del cuadro entero; la pauta de accesibilidad
  también mira el área que parpadea y el rojo saturado. Sirve de alarma, no de certificado.
- Los **rótulos** se dibujan con las letras de reemplazo (ver S8) y no saben de zonas seguras (S9).
- Si la **partitura** no logra leer el espectro de la canción, esa pestaña del render se queda sin dibujarla y no avisa.
- Los bordes de los **tramos** del guion van al compás: las capas de síntesis de un tramo conviene
  escribirlas con los mismos segundos que imprime `guion`.

## El panel

| # | Qué | Qué da |
|---|---|---|
| P1 | **El guion en la tira de la canción.** Los tramos como bloques que se arrastran sobre la canción, cada uno con su estilo elegido de la galería y su material. | Miguel arma el video entero sin tocar `proyecto.json`. |
| P2 | **Comparar versiones.** Dos reproductores sincronizados. | Hoy se cambia de una a otra con los botones y hay que acordarse. |

## Por dónde empezar

1. **Los veredictos** de la galería (lo hace Miguel, con el clic): sin eso E1 no tiene datos y el motor sigue eligiendo a ciegas entre propuestas.
2. **Un ejercicio con material mixto de verdad** (clips de Miguel más fotos de la galería): S2 ya está hecho y sólo se probó con fotogramas.
3. **S1, la voz:** es el cambio más grande; necesita el sí para la descarga y una grabación.
