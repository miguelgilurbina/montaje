# Video analógico: las referencias

Lo que sostiene a la mesa analógica (`py/montaje/analogo.py`, experimento 24). Miguel, el 2026-11-20: «Busca
referencias para alteración de vídeo análogo y trabaja en implementar eso en el proyecto. Sigue tu intuición».
Las referencias las juntó un agente de Claude esa noche, leyendo páginas (sin bajar nada); cada dato lleva su
fuente. Lo marcado **[sin verificar]** no se pudo confirmar en una fuente leída: se usó como punto de partida y
se ajustó mirando las hojas.

**Propuesta:** el criterio de la mesa es **simular la señal, no pintar el efecto**. Un «filtro VHS» de los que
abundan pone ruido, líneas y un «PLAY» encima de la imagen; aquí la imagen se vuelve la señal que era (NTSC-M,
la norma de la televisión de Venezuela) y pasa por los aparatos que la estropeaban. El color corrido, los puntos
que caminan por los bordes, el arcoíris en las rayas finas y la nieve de colores no se dibujan: salen de cómo se
codificaba el color y de lo que cada aparato le hacía.

## La señal: NTSC-M

- El color va montado en una **subportadora de 3,579545 MHz**; hay 227,5 ciclos por línea, así que la fase se
  invierte de una línea a la siguiente y de un cuadro al siguiente. Por eso los puntos del color que se cuela en
  la luma «caminan» (*dot crawl*) y el detalle fino de luma se lee como color falso (*rainbow*, cross-color).
  Los televisores viejos separaban el color con un filtro de muesca; los peines de tres líneas llegaron en los
  90 y ninguno lo elimina del todo.
  [Wikipedia: NTSC](https://en.wikipedia.org/wiki/NTSC) · [Wikipedia: Dot crawl](https://en.wikipedia.org/wiki/Dot_crawl) ·
  [NTSC-CRT, crt_ntsc.h](https://raw.githubusercontent.com/LMP88959/NTSC-CRT/main/crt_ntsc.h)
- **YIQ:** la luma ocupa 4,2 MHz; I se limita a 1,3 MHz y Q a 0,4. ≈80 líneas de TV por MHz: a 4,2 MHz, unas
  336 líneas por alto de imagen. [Wikipedia: YIQ](https://en.wikipedia.org/wiki/YIQ) ·
  [TV Technology](https://www.tvtechnology.com/miscellaneous/horizontal-resolution-pixels-or-lines)
- La línea visible dura unos 52,7 µs de los 63,6 de la línea entera (el resto es el borrado horizontal, que se
  ve cruzar en diagonal cuando se pierde el sincronismo).

**En el motor:** 480 líneas de 760 muestras (lo que toman los digitalizadores «4fsc»); cada línea es una señal en
el tiempo y los filtros van en su espectro, con los anchos de banda en MHz. El codificador limita I y Q como la
norma; el decodificador separa el color con **muesca** (el televisor barato) o con **peine** (resta la línea
anterior, más fino). PAL (576 líneas, 4,43 MHz, la fase de V que se alterna) no está: Venezuela era NTSC.

## La cinta: VHS

| Lo que se ve | Por qué | En el motor (`cinta`) |
|---|---|---|
| Imagen blanda | la luma va en FM con ~3 MHz de banda (≈240 líneas; S-VHS 400) | `formato`: SP, LP y EP bajan el corte como los simuladores (2,4 / 1,9 / 1,4 MHz en ntsc-rs y composite-video-simulator; aquí 2,8 / 2,2 / 1,7) |
| El color corrido a la derecha | el color se graba «rebajado» (*color-under*, 629 kHz) en ~0,3 MHz; un filtro de verdad arrastra lo que borra hacia adelante, y el color llega tarde | pasabajos causal de dos polos a 0,28–0,32 MHz y un retraso de 4–6 muestras (ntsc-rs) |
| Vetas de color en lo liso | el ruido de croma es de banda angosta: vetas horizontales largas, más visibles en lo oscuro y saturado | ruido de croma de 0,25 MHz, promediado entre dos líneas como el peine del VCR |
| Halo claro en los bordes | el «peaking» del VCR afila y deja su anillo | `realce`: una loma en el espectro de la luma |
| Las líneas que tiemblan, la bandera arriba | la base de tiempo: tensión de la cinta, cabrestante, cinta estirada (*flagging* arriba, *skew*) | `temblor`: ondas lentas a lo alto del cuadro, temblor de línea a línea y las primeras líneas torcidas |
| La costura de abajo | el cambio de cabezal unas líneas antes del sincronismo vertical; la mayoría de los VCR muestra ~8 líneas | `cabezal`, `cabezal_lineas`: las últimas líneas corridas con un perfil ^1,5 (ntsc-rs), con ruido y sin color |
| La barra de tracking | los cabezales no siguen la pista: bandas de ruido que van y vienen | `tracking`: una franja abajo que a ratos sube, con ondas, chispas y sin color |
| Rayas blancas | *dropouts*: falta óxido o hay suciedad, el cabezal no lee; transitorios de 8 a 64 px | `desgaste`: rayas que se apagan hacia la derecha |
| Copia de copia | cada generación suma ruido (una sexta, ~6 veces) y encadena los filtros | `generaciones`: la cinta se aplica de nuevo, pasando por compuesta entre VCR y VCR |

Fuentes: [Wikipedia: VHS](https://en.wikipedia.org/wiki/VHS) · [AV Artifact Atlas](https://avartifactatlas.com/artifacts/head_switching_noise.html)
(cambio de cabezal, [tracking](https://avartifactatlas.com/artifacts/tracking_error.html),
[base de tiempo](https://avartifactatlas.com/artifacts/time_base_error.html),
[skew](https://avartifactatlas.com/artifacts/skew_error.html),
[dropouts](https://avartifactatlas.com/artifacts/video_dropout.html),
[ruido de croma](https://avartifactatlas.com/artifacts/chrominance_noise.html),
[ringing](https://avartifactatlas.com/artifacts/ringing.html)) ·
[videohelp: líneas del cambio de cabezal](https://forum.videohelp.com/threads/395625-How-to-capture-with-no-head-switching-noise-(certain-VCRs)) ·
[Videomaker: generaciones](https://www.videomaker.com/article/f6/7113-clean-copies-one-generation-to-the-next/) ·
[ntsc-rs: valores por defecto](https://raw.githubusercontent.com/ntsc-rs/ntsc-rs/main/crates/ntscrs/src/settings/standard.rs).

Una advertencia de composite-video-simulator que vale como criterio: el «look VHS» de internet (estática,
«PLAY», contador) no es fiel; una cinta de los 80 suele mostrar, a lo más, una barra de tracking abajo
([README](https://raw.githubusercontent.com/joncampbell123/composite-video-simulator/master/README)). Por eso
la cinta de la casa no lleva letreros; el `osd` existe aparte, para cuando el guion lo pida.

**El sonido de la cinta** (`cinta.sonido`; por defecto la música queda intacta). La pista lineal del VHS va en el
borde de la cinta, a la velocidad de la cinta: banda angosta (más en EP), casi mono, con silbido; la HiFi va en el
tambor, en FM, y es casi limpia. Las cifras de banda por formato son de catálogo de época **[sin verificar]** en una
fuente leída. Medido en el motor (2026-11-20) con un tono de 1 kHz, ruido y silencio: la pista lineal en SP tiembla
±0,35 % de pico (0,18 % RMS) y corta en unos 90 Hz–8 kHz con un silbido de −50 dBFS; en EP gastada, 111 Hz–4,4 kHz y
−42 dBFS; la HiFi tiembla 0,09 % RMS. Las arrugas hunden el sonido en los mismos instantes en que saltan la imagen.
**Claude no oye: esto se midió; el oído es de Miguel.**

**El TBC** (el JVC de la idea de Miguel) corrige la base de tiempo línea por línea: endereza el temblor y la
bandera, y deja el ruido y el color corrido. En el motor, un `tbc` después de una cinta le quita su temblor; trae
además los controles de un procesador (brillo, contraste, color, tono). [Wikipedia: Dropout compensator](https://en.wikipedia.org/wiki/Dropout_compensator)

## La antena y el televisor

- **Señal débil:** nieve; sin el *burst* el televisor apaga el color y la imagen queda en blanco y negro (si
  falla, la nieve trae «confeti» de color). [Wikipedia: Colour killer](https://en.wikipedia.org/wiki/Colour_killer)
- **Fantasmas:** la señal rebotada llega después (de −4 a +45 µs; el 90 % entre −4 y 26). Un fantasma a la
  izquierda es un pre-eco. La amplitud típica **[sin verificar]**. El control automático de ganancia del
  televisor devuelve el nivel: el eco no aclara la imagen.
  [Wikipedia: Ghosting](https://en.wikipedia.org/wiki/Ghosting_(television)) · [US5335009A](https://patents.google.com/patent/US5335009A/en)
- **Sincronismo perdido:** sin el vertical la imagen rueda y se ve la barra del borrado (~8 % del alto); sin el
  horizontal se desgarra en diagonal (~17 % de la línea). [Wikipedia: Analog television](https://en.wikipedia.org/wiki/Analog_television)
- **La barra del zumbido:** 60 Hz de la red contra 59,94 campos por segundo deja una barra que sube despacio
  (unos 17 s por vuelta). Es una cuenta, no una medida: **[sin verificar]** en una fuente.

**El tubo** (`pantalla`): el haz es una campana que engorda con el brillo (las líneas claras se ven más anchas,
entre las oscuras se ve el negro); máscara de rejilla (Trinitron), de puntos o de ranuras; gamma del tubo 2,4
contra 2,2 de la pantalla de hoy, como crt-geom; el resplandor del vidrio; la curva con sus esquinas; el blanco
azulado de 9300 K de muchos televisores **[sin verificar]** como cifra de una fuente. La persistencia del fósforo
P22 es de milisegundos (**[sin verificar]**, leída en un extracto): en un campo casi no queda rastro. Las colas de
cometa de lo que se mueve son del **tubo de la cámara** (vidicón), no del televisor: por eso viven en `camara`
(`estela`). [AV Artifact Atlas: image lag](https://avartifactatlas.com/artifacts/image_lag.html) ·
[crt-geom](https://raw.githubusercontent.com/libretro/slang-shaders/master/crt/shaders/crt-geom.slang) ·
[crt-lottes](https://raw.githubusercontent.com/libretro/slang-shaders/master/crt/shaders/crt-lottes.slang) ·
[crt-royale](https://github.com/libretro/slang-shaders/blob/master/crt/shaders/crt-royale/README.TXT) ·
[Wikipedia: Shadow mask](https://en.wikipedia.org/wiki/Shadow_mask)

Lejos, las líneas y la máscara no se distinguen: el motor las apaga cuando hay pocos pixeles por línea (bajo unos
1,25 por línea) o por tríada (bajo unos 1100 px de ancho), en vez de dejar muaré. Las muestras del probador (540
de alto) muestran el tubo sin líneas; se ve de verdad a 1080.

## El video arte

| Referencia | Qué hace | En el motor |
|---|---|---|
| Nam June Paik, *Magnet TV* (1965) | un imán sobre el televisor deforma la imagen, y cambia al moverlo ([Whitney](https://whitney.org/collection/works/6139)) | `iman`: la imagen se tuerce alrededor de un punto que se pasea; el color se corre de tono (la pureza) |
| Paik/Abe, *wobbulator* | bobinas de deflexión extra alimentadas por osciladores: el barrido ondula ([Rhizome](https://rhizome.org/editorial/2010/nov/22/paik-raster-manipulation-unit-or-wobbulator/)) | `iman` con `ondas` |
| Rutt/Etra | la luminancia levanta las líneas: «un mapa topográfico del brillo» ([Vasulka](https://vasulka.org/Kitchen/essays_furlong/K_Furlong_13.html)) | `relieve` |
| Sandin Image Processor | sumadores, comparadores, bordes, rebanado de luma y codificador de color ([Wikipedia](https://en.wikipedia.org/wiki/Sandin_Image_Processor)) | `colorizador` (el rebanado y el falso color) |
| Realimentación | una cámara apuntada a su monitor: anidamiento y formas casi fractales ([Wikipedia](https://en.wikipedia.org/wiki/Video_feedback)) | `realimentacion` |
| LZX (Vidiot, Chromagnon) | procesador de luma, colorizador, llaves ([Perfect Circuit](https://www.perfectcircuit.com/lzx-chromagnon.html)) | `colorizador` |

## Lo que no se usó, y por qué

- **El código de los simuladores.** composite-video-simulator es GPL-2.0 y es la raíz del linaje (ntscQT y ntsc
  son ports en Apache-2.0 de ese código); el núcleo de ntsc-rs es MIT/ISC/Apache, su interfaz GPL-3.0; los
  shaders crt-royale, crt-geom y guest son GPL-2.0 o posterior (crt-lottes es dominio público). Este repo es MIT:
  el motor está escrito desde la descripción de lo que hacen, no copiado.
- **El filtro `noise` de ffmpeg** repite una tabla fija y no tiene correlación a lo largo de la línea: no sirve
  para ruido de cinta. El ruido se genera en numpy, con su espectro.
- **Los códecs de verdad** (ffmpeg trae H.263, MJPEG y DV): pasar la imagen por ellos daría artefactos
  auténticos, pero no se pueden encadenar con los demás aparatos ni procesar en pedazos sin costura, y el
  datamosh y los errores que se arrastran piden tocar el códec por dentro. El de `digital.py` es propio y chico
  (ver abajo).

## La película (2026-11-21)

Miguel, el 2026-11-21: «acumulemos más efectos antes de evaluar lo que ya hiciste». La película estaba en la
galería sólo como capas pintadas encima (`recuerdo`, `rayas`, `pelicula`); el aparato `pelicula`
(`py/montaje/pelicula.py`, experimento 25) la simula en la emulsión, con el mismo criterio de la mesa.

| Lo que se ve | Por qué | En el motor (`pelicula`) |
|---|---|---|
| El paso a saltitos | el Super 8 casero se filmaba a **18 cuadros por segundo** (la velocidad de fábrica; 24, 25 y 36 eran las otras): a 30 del video, cada cuadro de película dura dos o uno (2, 2, 1…) | `cuadros` (18 por defecto); cada cuadro de película se repite tal cual, grano incluido |
| Todo naranja (o azul) | la película de luz artificial («tipo A», tungsteno) se usaba de día con el **filtro 85** naranja de la cámara, que se quita adentro: si no, todo sale naranja | `balance`: `naranja` (el filtro olvidado adentro), `azul` (la de tungsteno de día sin filtro) |
| Un halo rojo alrededor de las luces | la luz más fuerte atraviesa la emulsión, rebota en la base y vuelve a la capa de más abajo, la sensible al rojo; la capa antihalo no alcanza a frenarla | `halo`: el exceso de lo claro, desenfocado ancho, sobre todo al rojo |
| La copia que se pone roja | en las copias de color Eastmancolor envejecidas se va primero el cian, después el amarillo; el magenta es el más estable: queda rojo magenta, y con menos contraste. El Kodachrome, en cambio, casi no se destiñe a oscuras | `desvanecido`: la densidad de cada tinte baja con su propia velocidad |
| El cuadro que baila | el Super 8 no tiene uña de registro y la placa de presión del cartucho sujeta poco: el cuadro se mueve en la ventanilla | `vaiven` [sin verificar la medida: no se encontró en píxeles; es un punto de partida mirado en las hojas] |
| La tira en el escaneo | el cuadro de cámara del Super 8 mide **5,69 × 4,22 mm**, el paso entre cuadros 4,234 mm (0,1667″); la perforación, 0,91 × 1,14 mm (0,036 × 0,045″), con el cuadro centrado en ella; la tira, 7,976 mm | `marco: escaneo` (las medidas de la tira); `ventanilla` (sólo el cuadro, con esquinas redondas) |
| Los primeros cuadros quemados | al cargar un cartucho quedan expuestos unos 7 cuadros; que la cámara queme el arranque de cada toma (el motor todavía no llega a su velocidad) es lo que cuenta quien filma, [sin verificar] en una fuente | `quemado`: arranques sobreexpuestos y velos naranjas que entran por un borde |

Además: el **grano** va en la densidad, del tamaño que le toca al formato (un grumo de ~14 µm [sin verificar] se ve
más grande en un cuadro chico) y con la ley de Selwyn para el desvío; la **curva** de la reversible es
contrastada, hunde los negros y dobla las luces sin recortarlas; el **polvo** es negro en la reversible proyectada
(y claros los rasguños de la emulsión); el **pelo** está en la ventanilla y no baila con la imagen; la **fecha**
naranja en siete segmentos es la de las cámaras de rollo de bolsillo (para las fotos). Las granularidades de cada
emulsión y el tamaño del grumo son puntos de partida [sin verificar].

[Wikipedia: Super 8 film](https://en.wikipedia.org/wiki/Super_8_film) ·
[Kodak Super 8 Camera, guía](https://www.kodak.com/content/pdfs/KODAK-SUPER-8-Camera-getting-started-guide-EN.pdf) ·
[Rewind Photo Lab: filtro 85 y película tungsteno](https://help.rewindphotolab.com.au/en-US/super-8-filters-and-cartridge-notches-1948336) ·
[Wikipedia: Anti-halation backing](https://en.wikipedia.org/wiki/Anti-halation_backing) ·
[Dehancer: la halación](https://blog.dehancer.com/articles/halation/) ·
[Brian Pritchard: el desteñido de la película](https://brianpritchard.com/wp/british-motion-picture-laboratories/fading-of-motion-picture-film/) ·
[National Film Preservation Foundation](https://www.filmpreservation.org/preservation-basics/color-dye-fading) ·
[filmkorn: normas del Super 8](https://www.filmkorn.org/super8data/database/articles_list/super8_fotmat_standards.htm) ·
[Wikipedia: Film perforations](https://en.wikipedia.org/wiki/Film_perforations) ·
[bolex repair: el vaivén del 8 mm](https://bolexrepair.blogspot.com/2011/07/bolex-pressure-plate-mod.html)

## Lo digital temprano (2026-11-21)

Después del VHS vino lo digital barato. Dos aparatos en `py/montaje/digital.py`: el `sensor` (la cámara) y la
`compresion` (el códec), escritos aquí: los códecs de la época eran transformadas del coseno en bloques de 8×8,
y uno chico en numpy alcanza para que los artefactos salgan de verdad.

| Lo que se ve | Por qué | En el motor |
|---|---|---|
| El celular: chico y a saltos | los celulares con cámara grababan **3GP**: H.263 o MPEG-4 a 176 × 144 (QCIF), unos **15 cuadros por segundo** y decenas de kb/s (H.263 nivel 10: hasta 15 cuadros y 64 kb/s), con audio **AMR-NB** de 4,75 a 12,2 kb/s; las cifras de un aparato real son anecdóticas | `sensor` (`resolucion`, `cuadros`, `irregular`) y `compresion: mpeg` con poca `calidad` |
| Bloques que se arrastran | entre cuadros clave el códec manda sólo lo que cambió; con pocos bits, lo chico se vuelve cero y el bloque viejo se queda; en el cuadro clave la imagen «revienta» de nuevo | el cuantizador de zona muerta de los códecs de movimiento; `gop` |
| Manchas de colores que se arrastran | un paquete perdido deja basura en la referencia, y el error viaja con el movimiento hasta el próximo cuadro clave | `compresion.errores` en `mpeg` |
| El datamosh | si se quita el cuadro clave (en un corte), el códec mueve la imagen vieja con el movimiento de la nueva | `residuo` bajo |
| La MiniDV que se pliega | los **dropouts** de DV son rectángulos de unos **32 píxeles** de ancho con colores equivocados que no copian nada del cuadro, o lo que el reproductor puso del cuadro de al lado; vienen en una zona; los causan pliegues y daños de la cinta | `compresion: dv` (color 4:1:1, macrobloques de 32 × 8) con `errores` |
| La columna clara, el borde morado | el CCD rebalsa en una columna con una luz fuerte; el borde morado de lo quemado era el de las cámaras de bolsillo [sin verificar en una fuente leída] | `sensor.mancha`, `sensor.franja` |

[Wikipedia: 3GP and 3G2](https://en.wikipedia.org/wiki/3GP_and_3G2) ·
[Wikipedia: H.263](https://en.wikipedia.org/wiki/H.263) ·
[ffmpeg: muestras de 3GP de teléfonos](https://samples.ffmpeg.org/mobileVideo_3gp/) ·
[Adam Wilt: defectos de DV por la cinta](https://adamwilt.com/pix-defects.html) ·
[AV Artifact Atlas: DV dropout](https://www.avartifactatlas.com/artifacts/dv_dropout.html) ·
[DV Rescue: artefactos](https://mipops.github.io/dvrescue/sections/artifacts.html) ·
las tablas de cuantización son las del anexo K de la norma JPEG.

**El sonido:** el micrófono del celular deja la banda del habla telefónica (300–3400 Hz; AMR-NB muestrea a 8 kHz),
el control automático de ganancia sube el ruido en los silencios, y la ley μ en 8 bits pone el grano; la webcam
suma el zumbido de la tierra del USB. La ley μ es un parecido, no el AMR: [sin verificar] cuánto se le parece al
oído. Claude no oye: se mide, el oído es de Miguel.

## La casetera y la consola de mezcla (2026-11-21)

Dos aparatos más, de la sala de la casa y de la sala de edición:

- **La casetera** (`casetera`, `py/montaje/casetera.py`, de señal): la **pausa** (la imagen quieta de un solo
  campo, con los bordes en serrucho, temblando, con la barra de ruido donde los cabezales leen entre pistas),
  **rebobinar** (la imagen hacia atrás entre barras que suben, el color que se va), **el arranque** (la pantalla
  azul de la casetera sin señal, ▶ PLAY y la imagen que entra con el tracking) y el **entrelazado** (dos campos de
  instantes distintos: lo que se mueve se peina). Ya estaba anotado como sin verificar: las barras de la pausa y
  del avance, el azul de cada marca y sus letreros; los letreros van en inglés, como en las de la época.
- **La consola de mezcla de los 90** (`consola`, `py/montaje/consola.py`, de imagen: era digital por dentro). El
  Panasonic WJ-MX50 de los videos de boda y los canales locales tenía memoria de cuadro y botones para estrobo,
  cuadro quieto, mosaico, negativo, pintura (posterizado), mono, **multi** (la pantalla en 1/4, 1/9 o 1/16), estela,
  y una sincronía que disparaba los efectos con la música. En el motor: `mosaico`, `estrobo`, `multi`, `pintura`,
  `negativo` y `llave` (lo oscuro muestra lo que la memoria guardó hace unos segundos), `siempre` o `a ratos`.
  [Manual del WJ-MX50](https://www.manualsdir.com/manuals/652668/panasonic-wj-mx50.html) ·
  [Studio 1 Productions: preguntas sobre el MX50](https://studio1productions.com/Articles/MX50QA.htm)

La sincronía con la música del MX50 es lo mismo que el modo `pulso` hace con los golpes: la consola al pulso
quedó como propuesta (M8 en `PROPUESTAS.md`).

## Los gestos de tiempo al pulso (2026-11-21)

No son aparatos sino del modo `pulso` (G3 en `PROPUESTAS.md`): la imagen quieta medio golpe en el uno de cada
compás, el pedacito del golpe repetido (el tartamudeo de los videos de música) y el paso de cuadro (cada cuadro
dura dos: el movimiento a saltos de la película vieja y del stop motion). Se calculan en `pulso.tiempo_de_toma`
desde los golpes de la canción y el render los aplica con `Freeze` de Remotion, sin gastar material del clip.

## Lo que no se pudo verificar

La amplitud de los fantasmas, el SNR del VHS en dB, el largo y la frecuencia reales de los dropouts, las barras
de la pausa y del avance rápido, el estilo de los letreros de cada marca de VCR, el *weave* del Super 8, el
pitch de la máscara y los tiempos del P22; de la película, cuánto baila el cuadro, el tamaño del grumo de grano y
la granularidad de cada emulsión; de lo digital, el borde morado de las cámaras de bolsillo y cuánto se parece al
AMR la voz del celular. Los valores del motor para eso son puntos de partida ajustados
mirando las hojas: si Miguel tiene una cinta, un VCR o un televisor de tubo, una captura de verdad es la mejor
referencia que podemos tener.
