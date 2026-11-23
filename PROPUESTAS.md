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
| E1 | **Hecho en parte el 2026-11-09:** `aprender` y `direccion/LECCIONES.json` (lo que Miguel dice, con cita, entra solo al primer armado de `guion`). Falta lo que no se sabe todavía: el porqué de los «no». **Leer los veredictos como datos.** Con la galería juzgada, un comando que compare las recetas aprobadas contra las rechazadas, perilla por perilla (largo de frase, fundidos, velocidad, capas), y diga lo que se repite: «lo que aprobaste va lento y con fundidos de dos golpes o más». | El criterio de Miguel deja de estar sólo en su cabeza y en las citas: los valores por defecto y el esqueleto del guion se inclinan hacia lo que eligió. | Los veredictos (ahora se dan con un clic en `/estilos`). Con menos de unos veinte, lo que salga es una pista, no una regla. |
| E2 | ~~Elegir entre dos.~~ **Hecho el 2026-11-10** sobre el probador: `/estilos/comparar` pone dos de la misma familia lado a lado, sincronizados, y anota la elección en `direccion/COMPARACIONES.json`; `guion` desempata con eso. Falta que Miguel elija: con pocas elecciones el orden es una pista. | Juzgar sesenta tarjetas una por una cansa; comparar de a dos es rápido y da más información que sí/no. | Unos minutos de Miguel en el panel. |
| E3 | ~~Barrer una perilla.~~ **Hecho el mismo 2026-11-09:** `ejercicio --barrer fundido_golpes=0.5,1,2,4` deja las variantes lado a lado, sincronizadas, en un video. | Afinar un valor mirando, sin escribir cuatro versiones a mano. Es la forma natural de un ejercicio: «¿cuánto fundido?». | Que Miguel elija la celda. |
| E4 | ~~Lo aprobado no se rompe.~~ **Hecho:** el plan, con `py/pruebas/planes.py` (2026-11-09); el dibujo, con los cuadros de referencia del probador (2026-11-10): `probar --todos` compara tres cuadros de cada estilo con los suyos. | Un cambio al motor no altera un estilo aprobado sin que nadie lo note. | Nada. |
| E5 | **El ejercicio desde el panel.** El botón que corre la vuelta ya está (2026-11-09) y muestra la salida con las medidas; falta que el panel muestre las versiones y sus hojas una al lado de la otra. | Miguel puede lanzar y mirar un ejercicio sin Claude. | Nada. |

## Las galerías de efectos, transiciones y filtros (2026-11-10)

Miguel preguntó «cómo podríamos seguir optimizando y expandiendo nuestras galerías de
efectos, transiciones y filtros» y eligió **el probador** (hecho, ver E2 y E4) y **sacar la
persiana de la ronda** (hecho: la ronda salta lo rechazado). Lo que se midió ese día: de los
estilos de la galería, casi todos se vieron en un solo experimento; las transiciones existen
sólo en `pulso`; para la calma sólo hay fundido; sus «a medias» de la cinta («está bueno pero
como transición») y de la doble exposición («igual en todos lados») apuntan a usarlas como
paso entre escenas. Lo que quedó para después, en el orden en que se propuso:

| # | Qué | Qué da | Qué necesita |
|---|---|---|---|
| G1 | **Transiciones en todo.** En los modos de fotos (collage, secuencia, cinta) y entre tramos, no sólo entre clips de `pulso`. Nuevas: la cinta que pasa y agranda la imagen siguiente (idea de Miguel), la doble exposición pasajera, el fundido por luz (lo claro de la imagen nueva aparece primero) y el desenfoque que cruza, para la calma; el quemado de película para la familia del recuerdo; el barrido para la energía alta. | La calma deja de tener una sola forma de cambiar de imagen, y las fotos de la galería de Curiana tienen las mismas transiciones que los clips. | Nada; se prueban en el probador. |
| G2 | **Filtros con LUT.** El formato estándar de corrección de color (`.cube`); este ffmpeg ya trae `lut3d`. Se pueden escribir en código desde la paleta (`direccion/PALETA.md`), sin bajar nada. Junto con S3 (igualar el color entre clips). | Tintas más finas que el duotono, y cualquier corrección hecha en otro editor entra al motor. | Nada (una LUT de afuera, con su ok). |
| G3 | ~~Efectos de tiempo.~~ **Hecho el 2026-11-21** (experimento 25): en `pulso`, `congelar_golpe`, `tartamudeo` y `paso_de_cuadro`, colgados del uno de cada compás, de cada golpe o de los golpes de más energía (`_cada`); el render los aplica con `Freeze` sin gastar material. Estilos `golpe-congelado`, `tartamudeo`, `paso-de-cuadro`. | Más gestos al pulso sin cortar, y uno de película vieja que va con el recuerdo. | Los veredictos de Miguel. |
| G4 | **Lo que choca, para el motor.** Hoy los `evitar` lo dicen en prosa (el empuje sobre fantasmas, las manchas sobre rótulos chicos). Escrito como dato, `guion` avisa cuando un armado los junta. | El primer armado no propone combinaciones que ya se vio que no funcionan. | Nada. |
| G5 | **El probador con fotos de verdad.** El banco prueba sobre clips; sus fotos son fotogramas. Con unas fotos de la galería de Curiana y su catálogo de imágenes, entran los modos de fotos (collage, secuencia, cinta, actos, superposición) y los momentos. | Los estilos de fotos se comparan como los de clips. | Unas fotos de la galería de Curiana. |

## Lo que dejó el primer documental (2026-11-17)

Un video de cinco minutos con voz en off, contado plano a plano desde un guion ajeno (proyecto privado: su carpeta
no entra al repo). Salió en pocos días y quedó bien; nacieron el modo `planos` y `py/montaje/voz.py`. Lo que
funcionó: el guion como lista de planos; cada plano colgado de las palabras de la transcripción, de modo que
regrabar una voz entera o acelerarla reacomoda todo solo; revisar en el panel y renderizar sólo al final. Lo que
haría distinto, como propuestas:

| # | Qué | Qué da | Qué necesita |
|---|---|---|---|
| D1 | **Comprobar la voz limpia.** Volver a transcribir la voz después de `limpiar-voz` y `editar` y compararla palabra por palabra con la original: avisa si una palabra perdió una sílaba (pasó: la compuerta se comió el arranque de una palabra y lo encontró el oído de Miguel, no las medidas). | Lo que hoy depende de escuchar entero, el motor lo señala con el segundo exacto. | Nada. |
| D2 | **El reacomodo como comando.** `voz.editar` ya devuelve el mapa de tiempos (viejo → nuevo); el reacomodo de los planos de cada tramo (duración, cámara, efectos, textos, series) vivió en un script del proyecto. Como comando, cortar una frase o cambiar la velocidad es una línea en `proyecto.json`. | El límite de duración se ajusta sin escribir código. | Nada. |
| D3 | **Las mezclas viejas se borran.** Cada mezcla lleva su huella y ninguna se borraba: en una semana se juntaron 19 de cinco minutos (1,8 GB). `planificar` debería dejar sólo la mezcla y los derivados que el timeline usa; Remotion, además, deja una carpeta de temporales por render en `%TEMP%`. | El disco no se llena con versiones que nadie va a abrir. | Nada. |
| D4 | **El final, probado el primer día.** El render final se cayó dos veces al terminar: buscaba un catálogo de clips que el modo no tiene, y dos planos del mismo video 4K que se cruzaban pasaron la espera del compositor. Ya arreglado (los planos de video usan sólo su tramo, del tamaño que pide su encuadre); la lección es renderizar en calidad final el tramo más pesado apenas esté armado. | Las sorpresas salen al principio y no la noche de la entrega. | Nada. |
| D5 | **Los subtítulos a quien habla, antes del render.** `planificar` ya escribe el `.srt`: mandarlo a revisar apenas está la voz, porque una palabra dudosa termina incrustada. | Los subtítulos los corrige quien sabe qué dijo. | Que el autor lea el `.srt`. |

## La galería de textos (2026-11-17)

Miguel: «hacer una galería de textos con fonts, con estilos, de forma que tengamos algo base propio para la galería,
para usar como de repente como títulos». En el documental se inventaron cinco estilos sobre la marcha (portada, frase
blanca con borde negro, cita, rótulo, subtítulo en caja) y quedaron enterrados en el código.

| # | Qué | Qué da | Qué necesita |
|---|---|---|---|
| T1 | ~~Tipografías libres dentro del repo.~~ **Hecho el 2026-11-17** (elección de Miguel, con su ok para la descarga): once familias en `fuentes/` con su licencia, registradas en `fuentes/fuentes.json`; incluye las de la marca (S8). | Lo que se escribe en un video deja de depender de qué hay instalado. | — |
| T2 | ~~Cada texto, una receta.~~ **Hecho el mismo día:** `textos/<id>.json` (ver `textos/README.md`), 23 letreros en cuatro familias, en vivo en `/textos` del panel con el veredicto ahí mismo; `planos` los usa con `"letrero"`. Falta: los veredictos, y que `pulso` y los `rotulos` también los usen. | Los textos se piden por nombre. | Los veredictos de Miguel. |
| T3 | ~~Curiana Cartel.~~ **Hecho el 2026-11-19** (elección de Miguel): Archivo Black apretada al 0,82 hecha tipografía con `montaje.py tipografia apretar` (dibujo, anchos, kerning y acentos; sin hinting; OFL, con el aviso de la original). Medida: cada glifo a menos de media unidad de 1000 del 0,82 exacto. El cartel y la firma de la galería ya la usan. | El «type 3c» sirve fuera del motor (Canva, Figma, el sitio). | — |
| T4 | ~~Texto en movimiento.~~ **Hecho el mismo día** (elección de Miguel), siete letreros en la familia `movimiento`: la **ventana** (la imagen o el video dentro de las letras, con dos capas de mezcla) y **atravesar** una letra al salir; el **karaoke** (cada palabra se enciende cuando se dice; en `planos`, `subtitulos.letrero` lo pone en los subtítulos con los tiempos de la transcripción); el **latido** con el tempo del proyecto (medido: +6,5 % en el golpe, cada 0,6 s a 100 bpm); las letras que se **arman** y la **ola**; la máquina con **cursor**. | Los títulos y las frases se mueven con la imagen, la voz y la música. | Los veredictos de Miguel. |

Lo que quedó para después, de lo que se propuso el 2026-11-19 (Miguel eligió T3 y T4 primero):

| # | Qué | Qué necesita |
|---|---|---|
| T5 | **Letra de dial de radio:** matriz de puntos o siete segmentos, dibujada en código desde una grilla (100 % propia), para «el dato teclea». | Nada. |
| T6 | **La letra a mano de Miguel:** una plantilla con las letras, tildes, ñ y ¿¡«», fotografiada, vectorizada y armada como tipografía. | Que Miguel llene la plantilla; **descarga con ok:** potrace para vectorizar. |
| G6 | **Gráficos que se dibujan:** el círculo y la flecha a mano, el subrayado que se traza, la ruta que avanza en un mapa, el número que cuenta, barras y línea de tiempo (lo que pedía el documental). | Nada. |
| G7 | ~~Imprenta.~~ **Hecho el 2026-11-22** (experimento 30, elección de Miguel en el mapa de la galería): el aparato `imprenta`, con serigrafía, risografía, el tramado del diario y la fotocopia. | Los veredictos de Miguel. |
| G8 | ~~Luz y óptica.~~ **Hecho el 2026-11-21** en la mesa: el aparato `lente` (aberración, barril, destello, raya anamórfica, niebla, suciedad, foco al pulso, viñeta). Las luces que se cuelan ya estaban (`fugas`). | Nada. |
| G9 | **Señal rota:** píxeles ordenados por brillo (amplía `senal`). El lado analógico (cinta, antena, sincronismo perdido) se hizo el 2026-11-20 en la mesa analógica, y el datamosh el 2026-11-21 (el códec de `digital.py` con `residuo` bajo: estilo `se-derrite`). | Nada. |
| G10 | **Recorte y collage:** la persona recortada como sticker, fotos que caen sobre una mesa. | **Descarga con ok:** un modelo que separe a la persona del fondo. |
| G11 | **Profundidad 2.5D:** una foto que se mueve en capas, como si tuviera volumen. | **Descarga con ok:** un modelo de profundidad (~100 MB). |

## La mesa analógica (2026-11-20)

Miguel, antes de dormir: «Busca referencias para alteración de vídeo análogo y trabaja en implementar eso en el
proyecto. Sigue tu intuición». **Hecho esa noche:** `py/montaje/analogo.py` simula la señal NTSC aparato por
aparato (cámara, letreros del aparato, cinta VHS, antena, TBC, colorizador, imán, relieve Rutt/Etra,
realimentación, televisor de tubo), con quince cadenas en la galería (`propuesta`, experimento 24) y sus
referencias en `direccion/ANALOGO.md`. Amplía G9 por el lado analógico (el datamosh y los píxeles ordenados son
digitales y siguen pendientes). Lo que queda, en el orden en que lo haría:

| # | Qué | Qué da | Qué necesita |
|---|---|---|---|
| A1 | **Juzgar las quince** en `/estilos` (filtro «en 24-mesa-analogica») o en el recorrido a 1080. | Saber cuáles son de Curiana y cuáles sobran; los «a medias» dicen qué perilla mover. | Unos minutos de Miguel. |
| A2 | ~~El sonido de la cinta.~~ **Hecho la misma noche** (`cinta.sonido`: `lineal` o `hifi`). | Imagen y sonido pasan por la misma cinta. | El oído de Miguel. |
| A3 | ~~Película.~~ **Hecho el 2026-11-21** (experimento 25): el aparato `pelicula` (Super 8, 8 mm, 16 mm), con siete estilos; y lo digital temprano (`sensor`, `compresion`), con seis. | El archivo familiar en película, no sólo en video. | Los veredictos de Miguel. |
| A4 | **Ventanas desde el guion.** Hoy las ventanas se dan a mano (`--ventana`); que una capa del guion diga «este tramo, en la cinta de la casa» y `render` pase sólo esos segundos por la cadena. | El analógico como un estilo más del guion, sin comandos aparte. | Nada. |
| A5 | **Entrelazado y pausa.** Los dos campos de cada cuadro (el peinado cuando algo se mueve) y la pausa del VCR (un campo repetido con su barra de ruido). | Dos gestos más de la cinta; la pausa sirve al pulso, como congelar en el golpe (G3). | Nada. |
| A6 | **Más rápido.** La pantalla a 1080 es lo que más pesa (~0,3 s por cuadro). En la tarjeta de video (un shader) sería tiempo real. | Previews de 1080 con tubo en segundos. | Nada para probar; quizá una biblioteca (con ok). |
| A7 | **Una captura de verdad.** Si Miguel tiene una cinta, un VCR o un televisor de tubo: grabar unos segundos (la cinta reproducida, la pantalla filmada) y ajustar las perillas contra eso. | La mejor referencia posible; lo que las fuentes no dicen (ver «Lo que no se pudo verificar» en `direccion/ANALOGO.md`). | El aparato y unos minutos. |

## Más aparatos (2026-11-21)

Miguel, al volver: «acumulemos más efectos antes de evaluar lo que ya hiciste. Que más podemos hacer?». De un menú
de nueve dijo «Dale» a lo recomendado: la película, lo digital temprano y el tiempo al pulso; después siguieron la
casetera y la consola de mezcla, y con «Seguir acumulando» el proyector, el 35 mm, el sonido de la película y la
consola al pulso, y con «Luz y óptica» la lente (hecho, experimento 25: treinta y ocho estilos en `propuesta`).
Lo que quedó del menú, y lo que apareció haciendo:

| # | Qué | Qué da | Qué necesita |
|---|---|---|---|
| M1 | **Juzgar las treinta y ocho** junto con las quince de la mesa (A1): `/estilos`, filtros «en 25-mas-aparatos» y «en 24-mesa-analogica». | Saber qué se queda antes de seguir sumando. | Unos minutos de Miguel. |
| M2 | ~~La casetera~~ (y A5). **Hecho el mismo día**: `casetera` con pausa, rebobinar, el arranque en azul con PLAY y el entrelazado; estilos `pausa-del-vhs`, `rebobinar`, `vhs-que-arranca`. Falta el sonido de la pausa y del rebobinado. | Gestos de la cinta que sirven al pulso. | Los veredictos de Miguel. |
| M3 | ~~La consola de mezcla de los 90.~~ **Hecho el mismo día**: `consola` con mosaico, estrobo, multi, pintura, negativo y llave, siempre o a ratos; seis estilos, entre ellos `video-de-boda` (cámara, consola, fecha, cinta y casetera). Las cortinillas con borde de color quedan para `pulso` (son transiciones). | Efectos y transiciones a la vez, de la época del VHS. | Los veredictos de Miguel. |
| M8 | ~~La consola al pulso.~~ **Hecho**: `cuando: "al pulso"` con `golpes_cada` y `dura_golpes`; la mesa recibe los golpes con `--golpes <proyecto>` (el probador pasa los del banco); estilo `consola-al-pulso`. Lo siguiente sería lo mismo para la casetera (la pausa en el golpe). | Los efectos de la consola en el tiempo de la canción. | Los veredictos de Miguel. |
| M9 | **La mesa dentro del guion** (amplía A4): hoy la mesa corre sobre un render ya hecho; que un tramo del guion diga «aquí, la película en la pared» y `render` lo pase sólo por esos segundos, con los golpes de su canción. | El analógico como un estilo más del guion. | Nada. |
| M4 | ~~El proyector en la pared.~~ **Hecho el mismo día** (Miguel: «Seguir acumulando»): el aparato `proyector` (la mancha de luz, el trapecio, la pared o la sábana, el foco, el latido, el cuarto oscuro); estilos `pelicula-en-la-pared`, `pelicula-en-la-sabana`. | El Super 8 visto como se veía en la casa. | Los veredictos de Miguel. |
| M5 | ~~El 35 mm de las fotos.~~ **Hecho**: `formato: 35mm` y los negativos `kodak-gold` y `fuji-superia`; estilos `foto-de-laboratorio`, `foto-de-laboratorio-fuji`, y `foto-con-fecha` pasó al 35 mm. Falta probarlos con fotos de verdad (el banco es de clips: G5). | Las fotos de la galería en papel de laboratorio. | Unas fotos de la galería de Curiana. |
| M6 | ~~El sonido de la película.~~ **Hecho**: `pelicula.sonido` (`magnetico`, `proyector`); estilo `super-8-sonoro`, y las dos películas proyectadas llevan el traqueteo. | Imagen y sonido de la misma máquina. | El oído de Miguel. |
| M7 | Lo que no entró del menú: ~~luz y óptica~~ (G8, **hecho el mismo día** con su elección: el aparato `lente` y siete estilos), ~~imprenta~~ (G7, **hecho el 2026-11-22**), **píxeles ordenados** (G9). | — | Nada. |

## El mapa de la galería (2026-11-22)

Miguel: «Me gustaría revisar todo lo que tenemos hasta ahora y mapear que otra cosa podemos hacer para expander nuestra
galería de efectos y filtros». El repaso (el catálogo por mundos con sus veredictos, lo que dicen los veredictos y lo
pendiente) y once territorios quedaron en una página privada, el «Mapa de la galería» (su dirección no va al repo). La
página tiene además un cuadro donde Miguel anota ideas desde el teléfono: se guardan en la colección `ideas` de su base
y Claude las lee para volverlas territorios.

Eligió abrir cuatro (y juzgarlos todos al final, «Al final juzgo todos»): los gestos de la película (28), la
fotografía de antes (29), la imprenta (30) y la radio (31). Los otros siete siguen en el mapa:

| # | Territorio | Qué | Qué necesita |
|---|---|---|---|
| K1 | **Transiciones** (G1) | la cinta que pasa y agranda la imagen siguiente (idea de Miguel), el quemado de película, el fundido por luz, el desenfoque que cruza, las cortinillas de la consola; también en los modos de fotos | Nada. |
| K2 | **Pantallas** | la cámara de vigilancia, el cartel de luces, el teletexto, la pantalla de cuatro verdes, la imagen en letras, el muro de televisores de una tienda | Nada. |
| K3 | **Color** (G2, S3) | LUT escritas desde la paleta: noche americana, película infrarroja, blanqueo saltado, proceso cruzado; e igualar los clips entre sí | Nada (una LUT de afuera, con su ok). |
| K4 | **Señal rota digital** (G9) | píxeles ordenados, el JPEG gastado, el escáner que se mueve, el archivo que se lee mal | Nada. |
| K5 | **Óptica y aire** | miniatura, la luz del fondo del mar, la sombra de las hojas, la lluvia en el vidrio, la cámara en mano | Nada. |
| K6 | **Grabado** | el grabado en cobre (como el mapa a lo De Bry de Kaketiana), la xilografía, el aguafuerte, el picado | Nada; el más difícil: que las líneas no tiemblen. |
| K7 | **Con un modelo** (G10, G11, S5) | el recorte de la persona, la foto en capas con profundidad, las caras | **Descarga con ok** de cada modelo. |

Pidió también moldes de trabajo para armar trabajo más adelante, y en la tarjeta eligió los tres:

- **las plantillas de piezas** (`plantillas/`, `python montaje.py plantilla <p> <id>`): el archivo de familia, el reel
  vertical y la cortina de radio. Cada una deja los tramos con sus estilos, las capas, los textos que faltan y la
  mesa analógica para después del render (`PIEZA.md`);
- **las recetas guardadas** (`recetas/`, `--cadena <receta>`): una base analógica con sus gestos, con nombre;
- **el molde de experimento** (`direccion/MOLDE.md`, `python montaje.py experimento <NN-nombre>`): la carpeta, la
  ficha y la fila de la bitácora, y los pasos de siempre.

Lo que falta de los moldes:

- la plantilla para el modo de fotos (collage, carrusel, secuencia: sin tramos);
- la del documental con voz (el modo `planos`);
- que la mesa corra dentro del render (M9).

## Sintetización: lo que el motor todavía no sabe

| # | Qué | Qué da | Qué necesita |
|---|---|---|---|
| S1 | ~~Voz en off y subtítulos.~~ **Hecho el 2026-11-17** con el primer documental (ver abajo): el modo `planos`, `limpiar-voz`, `voz.editar` y los subtítulos desde la transcripción. Falta el video con la voz de Miguel. | Es lo que más cambió lo que el motor puede hacer. | — |
| S2 | ~~Fotos y clips en el mismo montaje.~~ **Hecho el mismo 2026-11-09** (`"fotos"` + `mezclar_fotos`; ver la ficha del 21). Falta probarlo con fotos de verdad: en la práctica sólo había fotogramas de los mismos clips. | El material real de Curiana es mixto: la galería de imágenes más lo que Miguel graba. | Un puñado de fotos de la galería junto a los clips. |
| S3 | **Igualar el color entre clips.** Llevar todos los clips hacia uno de referencia (o hacia la paleta), antes de montar. | Veinte clips de días y luces distintas se ven como una sola película. | Elegir el clip de referencia. Sin descargas (este ffmpeg ya trae lo necesario). |
| S4 | **Cortar en el movimiento.** Elegir el punto de corte donde lo que se mueve en el clip que se va y en el que llega van hacia el mismo lado o están en el mismo lugar del cuadro (ya se mide el centro de interés y el movimiento de cada clip). | El corte se siente continuo en vez de casual: es lo que distingue un montaje de una sucesión. | Nada. Hay que probarlo con clips que tengan movimiento claro. |
| S5 | **Saber dónde hay una cara.** El recorte a vertical hoy sigue «lo que se mueve y tiene detalle»; con un detector de caras y personas, sigue a la persona y nunca la corta, y los rótulos no caen encima. | Los verticales para redes salen bien sin mirar clip por clip. | **Descarga con ok:** un detector liviano (decenas de MB). |
| S6 | **Estabilizar lo que tiembla.** Este ffmpeg ya trae `vidstab`. Los clips que pasen de un umbral de temblor se estabilizan al hacer la copia de trabajo. | Los clips del teléfono caminando dejan de marear en cámara lenta. | Clips que tiemblen: los veinte de la práctica casi no tiemblan (medido), así que no hay con qué probarlo. |
| S7 | **El sonido de los clips.** Dejar el mar o el viento del clip por debajo de la canción, bajando cuando la canción sube. | El video respira: no es sólo imagen con música encima. | Clips con sonido que valga. Claude no oye: los niveles se miden y el oído es de Miguel. |
| S8 | **Las letras de la marca.** Archivo Black y Lora no están instaladas; títulos y rótulos salen con reemplazos (Bahnschrift, Georgia). Pasa a la galería de textos (T1): las dos van en ese juego. | Los textos se ven como Curiana. | Ver T1. |
| S9 | **Zonas seguras por red.** Mostrar en el panel dónde Instagram y TikTok tapan el cuadro (nombre, botones, descripción) y avisar si un rótulo o un sujeto cae ahí. | Lo que se publica no queda tapado por la interfaz de la red. | Nada. |

## Lo que quedó anotado de las revisiones del motor

Dos revisiones independientes del código (2026-11-09) encontraron 24 defectos; se arreglaron
casi todos (ver la ficha del 21). Quedan, sin urgencia:

- El **muro de recuerdos** ignora `zoom`, `encuadre` y los fundidos de inicio y final: termina sin fundido.
- `revisar` mide los **destellos** por la luz media del cuadro entero; la pauta de accesibilidad
  también mira el área que parpadea y el rojo saturado. Sirve de alarma, no de certificado.
- Los **rótulos** se dibujan con las letras de reemplazo (ver S8) y no saben de zonas seguras (S9).
- Si la **partitura** no logra leer el espectro de la canción, esa pestaña del render se queda sin dibujarla y no avisa.
- **`hoja --cada`** no toma el cuadro del segundo que escribe en cada celda: con `--desde 4.5 --cada 6` sobre un
  video cosido de piezas de 6 s, las celdas cayeron al comienzo de cada pieza (visto el 2026-11-20 en el recorrido
  de la mesa analógica; con `ffmpeg -ss` directo, los cuadros caen donde deben). Usa el filtro `fps=1/cada`; habría
  que sacar cada cuadro por su segundo.
- Los bordes de los **tramos** del guion van al compás: las capas de síntesis de un tramo conviene
  escribirlas con los mismos segundos que imprime `guion`.

## Velocidad

Medido el 2026-11-09. Hecho: copiar sólo lo elegido, 8 a la vez, previews sin interpolar y con la tarjeta de video, y el
preview guardado por tramos.

| Qué | Por qué | Cuánto cuesta |
|---|---|---|
| **RIFE para inventar los cuadros.** Con la tarjeta de video en vez de `minterpolate`. Sin medir aquí. | El final interpola en el procesador (unos 110 s por clip de 1620×1080, 27 s por uno de 768×512, y 8 a la vez rinden 2,8 veces una sola). Suele deformar menos. | **Descarga con ok** (de GitHub). Miguel decidió dejarlo para más adelante: se prueba cuando moleste la calidad de la cámara lenta. |

Lo que no sirvió, para no volver a probarlo: comprimir con la tarjeta o más rápido (el tiempo no está ahí), interpolar en
un modo menos fino, dibujar 16 cuadros a la vez y bajar a un tercio de resolución.

## El panel

| # | Qué | Qué da |
|---|---|---|
| P1 | **El guion en la tira de la canción.** Los tramos como bloques que se arrastran sobre la canción, cada uno con su estilo elegido de la galería y su material. | Miguel arma el video entero sin tocar `proyecto.json`. |
| P2 | **Comparar versiones.** Dos reproductores sincronizados. | Hoy se cambia de una a otra con los botones y hay que acordarse. |

## Por dónde empezar

1. **Los veredictos** de la galería (lo hace Miguel, con el clic): sin eso E1 no tiene datos y el motor sigue eligiendo a ciegas entre propuestas.
2. **Un ejercicio con material mixto de verdad** (clips de Miguel más fotos de la galería): S2 ya está hecho y sólo se probó con fotogramas.
3. **La galería de textos** (T1, T2): lo que Miguel pidió después del primer documental.
