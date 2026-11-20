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
- **Película** (Super 8, 16 mm: grano según la luz, *gate weave*, halo rojo, el cian que se va primero): la
  galería ya tiene `recuerdo`, `rayas` y `pelicula`; lo que aporta la referencia está anotado en
  `PROPUESTAS.md` (A3).

## Lo que no se pudo verificar

La amplitud de los fantasmas, el SNR del VHS en dB, el largo y la frecuencia reales de los dropouts, las barras
de la pausa y del avance rápido, el estilo de los letreros de cada marca de VCR, el *weave* del Super 8, el
pitch de la máscara y los tiempos del P22. Los valores del motor para eso son puntos de partida ajustados
mirando las hojas: si Miguel tiene una cinta, un VCR o un televisor de tubo, una captura de verdad es la mejor
referencia que podemos tener.
