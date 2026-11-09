// El vocabulario del montaje, en un solo lugar: cada perilla con su nombre en
// español y una frase que dice qué hace. El panel lo muestra; GLOSARIO.md lo
// explica largo. Los valores por defecto son los de POR_DEFECTO en Python.

export type Modo = 'collage' | 'secuencia' | 'cinta' | 'actos' | 'superposicion' | 'pulso';

export const MODOS: Record<Modo, {nombre: string; frase: string}> = {
  collage: {nombre: 'Collage infinito', frase: 'Papeles nítidos que caen uno sobre otro al pulso y se quedan; la cámara se aleja mientras el cuadro se llena.'},
  secuencia: {nombre: 'Secuencia (pantalla completa)', frase: 'Una imagen tras otra ocupando todo el cuadro, en cortes al pulso; ordenadas por parecido, así una serie de variaciones se lee como una imagen que se transforma.'},
  cinta: {nombre: 'Cinta (reel en loop)', frase: 'Una columna de imágenes que sube un paso por golpe; el último cuadro empalma con el primero.'},
  actos: {nombre: 'Actos', frase: 'De una imagen a la vez al caos: cada protagonista vuela a una pared que crece; ecos, respiros y coda.'},
  superposicion: {nombre: 'Superposición', frase: 'Doble exposición pareja: las imágenes entran al pulso, se mezclan y se van.'},
  pulso: {nombre: 'Pulso (clips)', frase: 'Para clips: cada uno ocupa una frase de la canción y salta al pulso entre sus mejores momentos; entre clips, fundido de recuerdo.'},
};

export type Parametro = {
  clave: string;
  nombre: string;
  frase: string;
  /** `numero`: un deslizador; `entero`: un número sin decimales; `par`/`trio`: dos o tres números; `bool`; `opcion`: una lista. */
  tipo: 'numero' | 'entero' | 'par' | 'trio' | 'bool' | 'opcion';
  min?: number;
  max?: number;
  paso?: number;
  opciones?: string[];
  /** Qué significa cada número de un par o trío. */
  partes?: string[];
  defecto: unknown;
};

const semilla: Parametro = {clave: 'semilla', nombre: 'Semilla', frase: 'El azar del montaje. Otra semilla, otro collage con las mismas reglas.', tipo: 'entero', min: 0, max: 9999, paso: 1, defecto: 11};

export const PARAMETROS: Record<Modo, Parametro[]> = {
  collage: [
    semilla,
    {clave: 'umbrales', nombre: 'Umbrales de ritmo', frase: 'A qué caos el ritmo pasa de una imagen por compás a una por golpe, por corchea y por semicorchea.', tipo: 'trio', min: 0, max: 1, paso: 0.01, partes: ['golpe', 'corchea', 'semicorchea'], defecto: [0.12, 0.32, 0.6]},
    {clave: 'respiro', nombre: 'Respiro', frase: 'Si un compás cae esto o más en energía respecto del anterior, el ritmo baja dos niveles.', tipo: 'numero', min: 0, max: 0.5, paso: 0.01, defecto: 0.1},
    {clave: 'silencio', nombre: 'Silencio', frase: 'Un compás con menos energía que esto no recibe imágenes: el collage se queda quieto. 0 = nunca.', tipo: 'numero', min: 0, max: 1, paso: 0.01, defecto: 0},
    {clave: 'alto', nombre: 'Tamaño de cada imagen', frase: 'Alto de una imagen nueva, como fracción del cuadro: al inicio y al final del video.', tipo: 'par', min: 0.05, max: 1, paso: 0.01, partes: ['inicio', 'final'], defecto: [0.8, 0.36]},
    {clave: 'acento', nombre: 'Acento del primer tiempo', frase: 'Las imágenes que caen en el «uno» del compás, cuánto más grandes.', tipo: 'numero', min: 1, max: 2, paso: 0.05, defecto: 1.25},
    {clave: 'zoom_final', nombre: 'Alejamiento final', frase: 'Escala de la cámara al terminar. 1 = no se aleja; 0.4 = se ve dos veces y media más collage.', tipo: 'numero', min: 0.1, max: 1, paso: 0.01, defecto: 0.42},
    {clave: 'giro', nombre: 'Giro', frase: 'Rotación máxima de cada papel, en grados.', tipo: 'numero', min: 0, max: 15, paso: 0.5, defecto: 2},
    {clave: 'sombra', nombre: 'Sombra', frase: 'Cuánta sombra proyecta cada papel sobre el de abajo.', tipo: 'numero', min: 0, max: 1, paso: 0.05, defecto: 0.55},
    {clave: 'entrada_cuadros', nombre: 'Golpe de entrada', frase: 'Cuadros que tarda una imagen en caer: en la calma y en el pico.', tipo: 'par', min: 1, max: 20, paso: 1, partes: ['calma', 'pico'], defecto: [6, 2]},
    {clave: 'candidatos', nombre: 'Candidatos', frase: 'Cuántos lugares prueba cada imagen antes de elegir el que lleva más tiempo sin cubrirse.', tipo: 'entero', min: 1, max: 100, paso: 1, defecto: 28},
    {clave: 'una_por_generacion', nombre: 'Una por generación', frase: 'No repetir variantes de la misma imagen (las que Midjourney hizo juntas).', tipo: 'bool', defecto: true},
  ],
  secuencia: [
    {clave: 'contraste', nombre: 'Contraste de ritmo', frase: 'Cuánto más rápido corta lo fuerte que lo suave: 1 = parejo; más = la calma lenta y el pico vertiginoso.', tipo: 'numero', min: 0.5, max: 4, paso: 0.1, defecto: 2},
    {clave: 'max_por_golpe', nombre: 'Cortes máximos por golpe', frase: 'El tope de velocidad: 4 = semicorcheas; 2 = corcheas.', tipo: 'entero', min: 1, max: 4, paso: 1, defecto: 4},
    {clave: 'umbral_calma', nombre: 'Umbral de calma', frase: 'Bajo esta energía, un corte por compás y con fundido encadenado.', tipo: 'numero', min: 0, max: 1, paso: 0.05, defecto: 0.3},
    {clave: 'fundido_calma', nombre: 'Fundido en la calma', frase: 'Segundos del fundido encadenado entre imágenes cuando la canción está tranquila.', tipo: 'numero', min: 0, max: 2, paso: 0.05, defecto: 0.4},
    {clave: 'original_golpes', nombre: 'Duración de la original', frase: 'Golpes que se queda la original cada vez que vuelve (en la calma se queda el compás entero).', tipo: 'entero', min: 1, max: 4, paso: 1, defecto: 1},
    {clave: 'cierre_golpes', nombre: 'Cierre', frase: 'Golpes finales con la original al frente. 0 = sin cierre.', tipo: 'entero', min: 0, max: 16, paso: 1, defecto: 4},
  ],
  cinta: [
    {...semilla, defecto: 21},
    {clave: 'ancho', nombre: 'Ancho de la cinta', frase: 'Ancho de las imágenes, como fracción del cuadro.', tipo: 'numero', min: 0.3, max: 1, paso: 0.01, defecto: 0.84},
    {clave: 'alto_max', nombre: 'Alto máximo', frase: 'Las verticales se achican a esto para que entren varias en pantalla.', tipo: 'numero', min: 0.2, max: 1, paso: 0.01, defecto: 0.62},
    {clave: 'hueco', nombre: 'Hueco', frase: 'Espacio entre una imagen y la siguiente, como fracción del alto del cuadro.', tipo: 'numero', min: 0, max: 0.2, paso: 0.005, defecto: 0.025},
    {clave: 'paso_cuadros', nombre: 'Duración del paso', frase: 'Cuadros que tarda la cinta en subir un lugar.', tipo: 'entero', min: 1, max: 30, paso: 1, defecto: 7},
    {clave: 'sombra', nombre: 'Sombra', frase: 'Cuánta sombra lleva cada imagen.', tipo: 'numero', min: 0, max: 1, paso: 0.05, defecto: 0.5},
  ],
  actos: [
    {...semilla, defecto: 7},
    {clave: 'capas_max', nombre: 'Protagonistas a la vez', frase: 'Cuántas imágenes al frente al mismo tiempo con el caos al máximo.', tipo: 'entero', min: 1, max: 12, paso: 1, defecto: 5},
    {clave: 'curva_caos', nombre: 'Curva del caos', frase: 'Cómo crece el caos con el avance: 1 = parejo; más = tarda en despegar y luego sube rápido.', tipo: 'numero', min: 0.5, max: 3, paso: 0.1, defecto: 1.3},
    {clave: 'peso_energia', nombre: 'Peso de la energía', frase: 'Cuánto modula la energía de la canción al caos.', tipo: 'numero', min: 0, max: 1, paso: 0.05, defecto: 0.25},
    {clave: 'coda', nombre: 'Coda', frase: 'Fracción final sin entradas: la cámara se aleja hasta mostrar todo.', tipo: 'numero', min: 0, max: 0.3, paso: 0.01, defecto: 0.07},
    {clave: 'vida_golpes', nombre: 'Vida de la protagonista', frase: 'Golpes que dura al frente antes de volar a la pared: mínimo, y máximo en calma.', tipo: 'par', min: 0.5, max: 32, paso: 0.5, partes: ['mínimo', 'en calma'], defecto: [1, 16]},
    {clave: 'alto', nombre: 'Tamaño de la protagonista', frase: 'Alto como fracción del cuadro: en calma y en caos.', tipo: 'par', min: 0.1, max: 1, paso: 0.01, partes: ['calma', 'caos'], defecto: [0.92, 0.4]},
    {clave: 'vuelo_golpes', nombre: 'Duración del vuelo', frase: 'Golpes que tarda en llegar a la pared: en calma y en caos.', tipo: 'par', min: 0.25, max: 8, paso: 0.25, partes: ['calma', 'caos'], defecto: [2, 0.5]},
    {clave: 'borde', nombre: 'Calado', frase: 'Difuminado del borde de la protagonista, como fracción del lado menor.', tipo: 'numero', min: 0, max: 0.5, paso: 0.01, defecto: 0.12},
    {clave: 'borde_pared', nombre: 'Calado de la pared', frase: 'Difuminado de las piezas de la pared.', tipo: 'numero', min: 0, max: 0.5, paso: 0.01, defecto: 0.06},
    {clave: 'encuadre', nombre: 'Encuadre de la pared', frase: 'Cuántos cuadros ocupa la pared: al inicio, en el caos y al final.', tipo: 'trio', min: 0.2, max: 3, paso: 0.05, partes: ['inicio', 'caos', 'final'], defecto: [0.75, 1.35, 0.92]},
    {clave: 'luz_pared', nombre: 'Luz de la pared', frase: 'Opacidad de la pared: en calma y en caos.', tipo: 'par', min: 0, max: 1, paso: 0.05, partes: ['calma', 'caos'], defecto: [0.95, 0.55]},
    {clave: 'ecos', nombre: 'Ecos', frase: 'Caos a partir del cual aparecen uno, dos y tres ecos de la pared (montaje sobre montaje).', tipo: 'trio', min: 0, max: 1, paso: 0.05, partes: ['1', '2', '3'], defecto: [0.45, 0.65, 0.85]},
    {clave: 'golpe_camara', nombre: 'Golpe de cámara', frase: 'Empujón de zoom en cada primer tiempo, con el caos al máximo.', tipo: 'numero', min: 0, max: 0.2, paso: 0.005, defecto: 0.035},
    {clave: 'umbral_silencio', nombre: 'Umbral de respiro', frase: 'Una sección con menos energía que esto es un respiro: sin entradas.', tipo: 'numero', min: 0, max: 1, paso: 0.05, defecto: 0.35},
    {clave: 'compases_calma', nombre: 'Acto I métrico', frase: 'En la calma, las entradas caen parejas en los primeros tiempos.', tipo: 'bool', defecto: true},
  ],
  pulso: [
    {clave: 'corte', nombre: 'Saltos dentro del clip', frase: 'Cada cuánto salta a otro momento del mismo clip: nunca (una toma por frase), en cada compás, en cada golpe, o según la energía (la calma no salta, el pico más).', tipo: 'opcion', opciones: ['energia', 'frase', 'compas', 'golpe'], defecto: 'energia'},
    {clave: 'frase_compases', nombre: 'Compases por frase', frase: 'Cuántos compases dura un clip antes de pasar al siguiente (se reinicia en cada sección de la canción).', tipo: 'entero', min: 1, max: 16, paso: 1, defecto: 4},
    {clave: 'umbral_calma', nombre: 'Umbral de calma', frase: 'Bajo esta energía la frase es calma: una toma larga, más lenta, con fundidos largos.', tipo: 'numero', min: 0, max: 1, paso: 0.05, defecto: 0.35},
    {clave: 'umbral_pico', nombre: 'Umbral de pico', frase: 'Desde esta energía, varios saltos por compás.', tipo: 'numero', min: 0, max: 1, paso: 0.05, defecto: 0.7},
    {clave: 'pico_por_compas', nombre: 'Saltos por compás en el pico', frase: '2 = cada dos golpes; 4 = en cada golpe.', tipo: 'entero', min: 1, max: 8, paso: 1, defecto: 2},
    {clave: 'fundido_golpes', nombre: 'Fundido entre clips', frase: 'Golpes que dura el paso de un clip al siguiente. 0 = corte seco.', tipo: 'numero', min: 0, max: 8, paso: 0.25, defecto: 1},
    {clave: 'fundido_calma_golpes', nombre: 'Fundido en la calma', frase: 'Golpes del paso entre clips cuando una de las dos frases es calma.', tipo: 'numero', min: 0, max: 16, paso: 0.25, defecto: 3},
    {clave: 'fundido_dentro_golpes', nombre: 'Fundido entre momentos', frase: 'Golpes del paso entre dos momentos del mismo clip. 0 = salto seco.', tipo: 'numero', min: 0, max: 4, paso: 0.25, defecto: 0},
    {clave: 'transicion', nombre: 'Transición entre clips', frase: 'Cómo entra un clip sobre el que se va, en lo que dura el fundido: fundido, cortina (un borde que barre), iris (un círculo que se abre desde el sujeto), empuje (lo corre), destello (un fogonazo), zoom (llega desde cerca) o persiana. Ronda las recorre todas.', tipo: 'opcion', opciones: ['fundido', 'cortina', 'iris', 'empuje', 'destello', 'zoom', 'persiana', 'ronda'], defecto: 'fundido'},
    {clave: 'transicion_dir', nombre: 'Hacia dónde', frase: 'La dirección de la cortina, el empuje y la persiana. Alterna va a la derecha y a la izquierda.', tipo: 'opcion', opciones: ['alterna', 'derecha', 'izquierda', 'arriba', 'abajo'], defecto: 'alterna'},
    {clave: 'mezclar_fotos', nombre: 'Mezclar fotos', frase: 'Las fotos del proyecto entran al mismo reparto que los clips, cada una con un acercamiento lento.', tipo: 'bool', defecto: false},
    {clave: 'zoom_foto', nombre: 'Acercamiento de las fotos', frase: 'Cuánto se acerca (o se aleja) cada foto mientras está en pantalla.', tipo: 'numero', min: 0, max: 0.3, paso: 0.01, defecto: 0.08},
    {clave: 'doble_golpes', nombre: 'Doble exposición', frase: 'En la calma, el clip que viene aparece transparente estos golpes antes de llegar. 0 = sin doble.', tipo: 'numero', min: 0, max: 16, paso: 0.5, defecto: 0},
    {clave: 'doble_opacidad', nombre: 'Opacidad de la doble', frase: 'Cuánto se ve el clip que viene.', tipo: 'numero', min: 0, max: 1, paso: 0.05, defecto: 0.45},
    {clave: 'estela_golpes', nombre: 'Estela', frase: 'El clip que se va se queda como un brillo que se apaga, estos golpes. 0 = sin estela.', tipo: 'numero', min: 0, max: 8, paso: 0.25, defecto: 0},
    {clave: 'estela_opacidad', nombre: 'Opacidad de la estela', frase: 'Cuánto se ve el clip que se va.', tipo: 'numero', min: 0, max: 1, paso: 0.05, defecto: 0.35},
    {clave: 'velocidad', nombre: 'Velocidad', frase: 'Velocidad de los clips en la calma y en el pico (1 = tiempo real). Si un clip no alcanza, va más lento.', tipo: 'par', min: 0.25, max: 2, paso: 0.05, partes: ['calma', 'pico'], defecto: [0.8, 1]},
    {clave: 'orden', nombre: 'Orden', frase: 'Por fecha (la del teléfono), por nombre de archivo, o del más quieto al más movido.', tipo: 'opcion', opciones: ['fecha', 'nombre', 'movimiento'], defecto: 'fecha'},
    {clave: 'encuadre', nombre: 'Encuadre', frase: 'Cubrir recorta para llenar el cuadro; contener lo deja entero con bordes; relleno pone detrás el mismo clip desenfocado; medio queda a mitad de camino (con relleno); auto elige según la forma.', tipo: 'opcion', opciones: ['auto', 'cubrir', 'contener', 'relleno', 'medio'], defecto: 'auto'},
    {clave: 'zoom', nombre: 'Acercamiento', frase: 'Cuánto se acerca lentamente cada toma larga.', tipo: 'numero', min: 0, max: 0.2, paso: 0.005, defecto: 0.03},
    {clave: 'frase_compases_calma', nombre: 'Compases por frase en la calma', frase: 'Frases más largas donde la música descansa. 0 = igual que el resto.', tipo: 'entero', min: 0, max: 16, paso: 1, defecto: 0},
    {clave: 'reparto', nombre: 'Reparto', frase: 'Seguido: cada clip ocupa sus frases juntas. Ronda: los clips vuelven en orden, cada vuelta con otros momentos.', tipo: 'opcion', opciones: ['seguido', 'ronda'], defecto: 'seguido'},
    {clave: 'borde_toma', nombre: 'Borde de la toma', frase: 'Segundos del arranque y del final de cada clip que no se usan (el pulgar en el botón). Clips hechos con IA: 0.1.', tipo: 'numero', min: 0, max: 1, paso: 0.05, defecto: 0.35},
    {clave: 'congelar_golpes', nombre: 'Foto que despierta', frase: 'Golpes que cada clip entra congelado y apagado, antes de moverse y tomar color. 0 = no.', tipo: 'numero', min: 0, max: 8, paso: 0.5, defecto: 0},
    {clave: 'doble_en', nombre: 'Doble exposición en', frase: 'Sólo en la calma, o en todos los cambios de clip.', tipo: 'opcion', opciones: ['calma', 'todo'], defecto: 'calma'},
    {clave: 'dividir', nombre: 'Díptico', frase: '2 = dos clips a la vez, cada uno en su mitad (lado a lado; uno sobre otro en vertical). 1 = uno.', tipo: 'entero', min: 1, max: 2, paso: 1, defecto: 1},
    {clave: 'escala', nombre: 'Ventana', frase: 'Tamaño del clip en el cuadro; menos de 1 lo deja como una ventana sobre el fondo (con síntesis «campo» detrás).', tipo: 'numero', min: 0.3, max: 1, paso: 0.01, defecto: 1},
    {clave: 'sombra', nombre: 'Sombra', frase: 'Sombra del clip cuando es una ventana.', tipo: 'numero', min: 0, max: 1, paso: 0.05, defecto: 0},
    {clave: 'espejo', nombre: 'Caleidoscopio', frase: 'El centro del clip en espejo: 2 mitades o 4 cuartos. 0 = no.', tipo: 'entero', min: 0, max: 4, paso: 2, defecto: 0},
    {clave: 'transformados', nombre: 'Clips transformados', frase: 'Usar la variante transformada de cada clip (estela, eco, barrido, reversa…) en la calma o siempre.', tipo: 'opcion', opciones: ['no', 'calma', 'todo'], defecto: 'no'},
  ],
  superposicion: [
    {...semilla, defecto: 7},
    {clave: 'capas_max', nombre: 'Capas a la vez', frase: 'Cuántas imágenes se ven superpuestas en el pico.', tipo: 'entero', min: 1, max: 10, paso: 1, defecto: 4},
    {clave: 'mezcla', nombre: 'Modo de fusión', frase: 'Cómo se combinan: trama suma luces, aclarar se queda con lo más claro, normal tapa.', tipo: 'opcion', opciones: ['screen', 'lighten', 'normal', 'multiply', 'difference'], defecto: 'screen'},
    {clave: 'piso_densidad', nombre: 'Densidad mínima', frase: 'Entradas en la calma, relativas al pico.', tipo: 'numero', min: 0, max: 1, paso: 0.05, defecto: 0.15},
    {clave: 'curva', nombre: 'Curva', frase: 'Cómo sigue la densidad a la energía: 1 = lineal; más = sólo en los picos.', tipo: 'numero', min: 0.5, max: 3, paso: 0.1, defecto: 1.5},
    {clave: 'vida_golpes', nombre: 'Vida', frase: 'Golpes que dura cada imagen: en el pico y en la calma.', tipo: 'par', min: 0.5, max: 32, paso: 0.5, partes: ['pico', 'calma'], defecto: [1.5, 16]},
    {clave: 'alto', nombre: 'Tamaño', frase: 'Alto como fracción del cuadro: mínimo y máximo.', tipo: 'par', min: 0.1, max: 1, paso: 0.01, partes: ['mín', 'máx'], defecto: [0.5, 0.95]},
    {clave: 'opacidad', nombre: 'Opacidad', frase: 'Mínima y máxima.', tipo: 'par', min: 0, max: 1, paso: 0.05, partes: ['mín', 'máx'], defecto: [0.7, 1]},
    {clave: 'zoom', nombre: 'Ken Burns', frase: 'Zoom lento de cada imagen durante su vida: mínimo y máximo.', tipo: 'par', min: 0, max: 0.3, paso: 0.01, partes: ['mín', 'máx'], defecto: [0.02, 0.08]},
    {clave: 'deriva', nombre: 'Deriva', frase: 'Cuánto se desplaza cada imagen mientras vive, como fracción del cuadro.', tipo: 'numero', min: 0, max: 0.2, paso: 0.005, defecto: 0.02},
    {clave: 'borde', nombre: 'Calado', frase: 'Difuminado del borde.', tipo: 'numero', min: 0, max: 0.5, paso: 0.01, defecto: 0.12},
    {clave: 'orden', nombre: 'Orden', frase: 'Cómo se encadenan: por luz y tono (montaje tonal) o al azar.', tipo: 'opcion', opciones: ['luz-y-tono', 'azar'], defecto: 'luz-y-tono'},
  ],
};

export type TipoMomento = 'destacado' | 'rafaga' | 'barrido' | 'video' | 'salvapantallas';

export const MOMENTOS: Record<TipoMomento, {nombre: string; letra: string; frase: string; color: string}> = {
  destacado: {nombre: 'Destacado', letra: 'D', frase: 'El collage se detiene y oscurece; una imagen ocupa el cuadro, respira y vuelve a su lugar.', color: '#b64924'},
  rafaga: {nombre: 'Ráfaga (carrusel)', letra: 'R', frase: 'Imágenes a pantalla completa, una tras otra, en cortes secos al pulso.', color: '#c36712'},
  barrido: {nombre: 'Barrido', letra: 'B', frase: 'La cámara salta de golpe a una zona vacía del collage.', color: '#2154c5'},
  video: {nombre: 'Video', letra: 'V', frase: 'Un video de la biblioteca (una cortina) dentro del montaje, ajustado a sus compases.', color: '#26396a'},
  salvapantallas: {nombre: 'Salvapantallas', letra: 'S', frase: 'El collage se vela y el logo rebota por el cuadro como el del DVD; en cada borde cambia de versión.', color: '#7e93aa'},
};

export const TIPOS_IMAGEN: Record<string, string> = {
  marca: 'de marca (se lee Curiana Radio)',
  retrato: 'retratos',
  paisaje: 'paisajes',
  ciudad: 'ciudad',
  cartel: 'carteles y letras',
  abstracto: 'abstractas',
  'ciencia-ficcion': 'ciencia ficción',
};

export const FORMATOS: {nombre: string; ancho: number; alto: number}[] = [
  {nombre: '16:9', ancho: 1920, alto: 1080},
  {nombre: '3:2', ancho: 1620, alto: 1080},
  {nombre: 'Reel 9:16', ancho: 1080, alto: 1920},
  {nombre: '4:5', ancho: 1080, alto: 1350},
  {nombre: 'Cuadrado', ancho: 1080, alto: 1080},
];

export const ESQUINAS = ['arriba-izquierda', 'arriba-derecha', 'abajo-izquierda', 'abajo-derecha'] as const;

export const VERSIONES_LOGO: Record<string, string> = {
  isotipo_claro: 'isotipo claro (hueso)',
  isotipo_oscuro: 'isotipo oscuro (espiral)',
  lockup_claro: 'logotipo claro',
  lockup_oscuro: 'logotipo oscuro',
};
