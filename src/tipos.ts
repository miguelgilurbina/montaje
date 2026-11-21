/**
 * La forma de timeline.json. Lo escribe py/montaje/planificar.py, lo puede
 * corregir Claude o Miguel a mano, y Remotion lo dibuja. Tiempos en cuadros;
 * posiciones y tamaños en píxeles del lienzo.
 */

export type Capa = {
  id: string;
  /** Ruta relativa a la carpeta de medios del proyecto. */
  img: string;
  ini: number;
  fin: number;
  /** Cuadros de fundido al entrar y al salir. */
  entrada: number;
  salida: number;
  /** Centro de la imagen en el lienzo. */
  x: number;
  y: number;
  ancho: number;
  alto: number;
  opacidad: number;
  /** Escala al entrar y al salir. */
  zoom: [number, number];
  /** Desplazamiento total (px) a lo largo de su vida. */
  deriva: [number, number];
  /** Modo de mezcla CSS: screen, lighten, normal… */
  mezcla: string;
  /** Difuminado de los bordes, como fracción del lado menor (0 = rectángulo duro). */
  borde?: number;
  seccion: number;
  /** Modo actos: desde el cuadro `desde` la imagen vuela a su pieza de la pared y llega en `fin`. */
  vuelo?: {desde: number; pieza: number};
  /** Si está, `img` es un clip (su copia de trabajo) y esto dice qué parte se ve. */
  video?: CapaVideo;
  /** La capa se ve sólo dentro de este rectángulo del lienzo (un díptico: cada clip en su mitad). */
  marco?: Rect;
  /** Sombra de la caja (0..1): un clip chico sobre un fondo, como una ventana. */
  sombra?: number;
  /**
   * Cómo entra sobre el clip que se va, durante sus `entrada` cuadros (sin esto, fundido):
   * cortina (un borde que barre), iris (un círculo que se abre desde `centro`), empuje
   * (entra corriendo al otro), destello (un fogonazo), zoom (llega desde cerca, desenfocado)
   * o persiana (franjas). `dir` es hacia dónde se mueve: [1, 0] = a la derecha.
   */
  transicion?: {tipo: 'cortina' | 'iris' | 'empuje' | 'destello' | 'zoom' | 'persiana'; dir: [number, number]; centro?: [number, number]};
  /** En sus últimos `cuadros`, el clip que entra con empuje la corre hacia `dir` hasta sacarla del cuadro. */
  empujada?: {cuadros: number; dir: [number, number]};
};

export type CapaVideo = {
  /** Segundo del clip en que empieza la capa. */
  desde: number;
  /** 1 = tiempo real; 0.8 = un poco lento. */
  velocidad: number;
  /** Tamaño del clip (px), para el relleno. */
  fuente: [number, number];
  /** `img` es una foto, no un clip: se dibuja quieta y el movimiento se lo dan el zoom y la deriva de la capa. */
  foto?: boolean;
  /** Detrás, el mismo clip agrandado, desenfocado y oscuro: para un vertical en un cuadro horizontal (o al revés). */
  relleno?: boolean;
  /** Volumen del sonido del clip (0 o ausente = mudo). */
  volumen?: number;
  /** Caleidoscopio: el centro del clip en espejo, 2 (izquierda | derecha) o 4 (los cuatro cuartos). */
  espejo?: 2 | 4;
  /** Mosaico de tiempo: el clip repetido en una cuadrícula, cada celda `desfase` s más atrás que la anterior (en diagonal). */
  rejilla?: {columnas: number; filas: number; desfase: number};
  /** La foto que despierta: los primeros `congelar` cuadros, quieto en `desde` y apagado; después corre desde ahí y toma color. */
  congelar?: number;
  /**
   * Los gestos de tiempo al pulso, en cuadros de la toma: `paso` (cada cuadro dura `paso`: 2 = a la mitad de
   * cuadros por segundo), `congelados` ([cuadro, cuántos]: la imagen quieta en el golpe) y `tartamudeos`
   * ([cuadro, largo, veces]: el pedacito que empieza en el golpe, repetido). Lo que se ve nunca va delante del
   * clip: después del gesto la toma sigue donde iba.
   */
  tiempo?: {paso?: number; congelados?: [number, number][]; tartamudeos?: [number, number, number][]};
};

/** Una pieza de la pared, en unidades de pared (centro y tamaño). Aparece en el cuadro `llega`. */
export type Pieza = {
  id: string;
  img: string;
  mini: string;
  x: number;
  y: number;
  ancho: number;
  alto: number;
  llega: number;
};

export type Mural = {
  borde: number;
  /** Opacidad de la pared en el tiempo: [cuadro, opacidad]. */
  luz: [number, number][];
  /** Ordenadas por `llega`. */
  piezas: Pieza[];
};

/** Una copia de la pared sobre la pared: montaje sobre montaje. */
export type Eco = {
  tipo: string;
  ini: number;
  fin: number;
  entrada: number;
  salida: number;
  /** Cuadros hacia atrás: el eco muestra la pared como estaba entonces. */
  desfase: number;
  escala: [number, number];
  rot: [number, number];
  dx: [number, number];
  dy: [number, number];
  opacidad: number;
  mezcla: string;
};

export type Acto = {nombre: string; ini: number; fin: number};

/** Una imagen del collage, en unidades de mundo (la cámara las proyecta). Entra en `ini` y se queda. */
export type PiezaCollage = {
  id: string;
  img: string;
  ini: number;
  /** Cuadros que dura el golpe de entrada. */
  entrada: number;
  x: number;
  y: number;
  ancho: number;
  alto: number;
  /** Grados. */
  rot: number;
  /** Cuadro desde el que otras piezas la cubren entera: ya no se dibuja. */
  tapada?: number;
};

/** Un rectángulo en pantalla (centro y tamaño, px). */
export type Rect = {x: number; y: number; ancho: number; alto: number};

/** Un compás donde cambia el estilo: una imagen al frente, una ráfaga a pantalla completa o un barrido de cámara. */
export type Momento =
  | {
      tipo: 'destacado';
      ini: number;
      /** Cuadro en que termina: aterriza en su pieza del collage, vuelve a su lugar o (firma) se queda. */
      fin: number;
      entrada: number;
      /** Cuadros del final: vuelo a su pieza o regreso a `desde`. */
      salida: number;
      /** Cuánto se oscurece lo de atrás. */
      oscuro: number;
      id: string;
      img: string;
      /** Tamaño en pantalla (px), centrada. */
      ancho: number;
      alto: number;
      /** Pieza del collage donde aterriza; -1 si no aterriza. */
      pieza: number;
      /** Si sale de un lugar de la pantalla (la cinta), crece desde ahí y vuelve ahí. */
      desde?: Rect;
    }
  | {
      tipo: 'rafaga';
      ini: number;
      fin: number;
      imagenes: {id: string; img: string; ini: number; ancho: number; alto: number}[];
    }
  | {tipo: 'barrido'; ini: number; fin: number}
  | {
      tipo: 'video';
      ini: number;
      fin: number;
      /** Ruta relativa a la biblioteca. */
      src: string;
      /** Parte del video que se muestra: [x, y, ancho, alto] en píxeles del video. */
      recorte: [number, number, number, number];
      /** Tamaño del video original (px). */
      fuente: [number, number];
      /** Tamaño en pantalla (px), centrado. */
      ancho: number;
      alto: number;
      /** Velocidad de reproducción, para que dure justo sus compases. */
      velocidad: number;
      volumen: number;
    };

/**
 * Cinta: imágenes en columna que suben un paso por golpe, como un feed. Es cíclica:
 * al final del video la cinta avanzó exactamente su largo y el cuadro vuelve a ser
 * el primero (loop sin costura).
 */
export type Cinta = {
  /** Centro vertical de cada imagen en la cinta (px, la primera en 0) y su tamaño. */
  items: {id: string; img: string; y: number; ancho: number; alto: number}[];
  /** Largo total de un ciclo (px). */
  largo: number;
  /** Cuánto avanzó la cinta en el tiempo: [cuadro, px]. */
  desplazamiento: [number, number][];
  sombra: number;
};

/** El logo de Curiana Radio sobre el video. */
export type Logo = {
  /** Sello fijo en una esquina; late en los primeros tiempos. */
  sello?: {img: string; x: number; y: number; alto: number; ancho: number; opacidad: number; pulsos: number[]; ocultar: [number, number][]};
  /** El logo suelto, rebotando por el cuadro como el salvapantallas del DVD. */
  salvapantallas?: {
    ini: number;
    fin: number;
    imgs: string[];
    ancho: number;
    alto: number;
    /** Posición inicial (esquina superior izquierda, px) y velocidad (px por cuadro). */
    x0: number;
    y0: number;
    vx: number;
    vy: number;
    oscuro: number;
  }[];
};

/**
 * Capas hechas en código (src/Sintesis.tsx), encima del montaje salvo `campo`, que va
 * de fondo. `fundido`: cuadros en que aparecen y se van. Las arma py/montaje/sintesis.py.
 */
export type Sintesis =
  | {
      tipo: 'recuerdo';
      ini: number;
      fin: number;
      fundido?: number;
      /** 0..1 cada uno; `temblor` en px. */
      grano: number;
      vineta: number;
      calidez: number;
      parpadeo: number;
      temblor: number;
      halo: number;
      semilla: number;
    }
  | {
      tipo: 'fugas';
      ini: number;
      fin: number;
      fundido?: number;
      /** Cada fuga: posición y deriva como fracción del cuadro, radio como fracción del ancho. */
      destellos: {ini: number; fin: number; x: number; y: number; dx: number; dy: number; radio: number; giro: number; color: string; fuerza: number}[];
    }
  | {tipo: 'polvo'; ini: number; fin: number; fundido?: number; motas: number; golpes: number[]; brillo: number; semilla: number}
  | {
      tipo: 'partitura';
      ini: number;
      fin: number;
      fundido?: number;
      /** JSON de la biblioteca con el espectro de la canción, cuadro a cuadro. */
      espectro: string;
      /** Segundo de la canción en que empieza el video (el tramo). */
      desde: number;
      color: string;
      /** Línea de base y altura máxima, como fracción del alto. */
      y: number;
      alto: number;
      opacidad: number;
    }
  | {
      tipo: 'campo';
      ini: number;
      fin: number;
      fundido?: number;
      colores: string[];
      /** [cuadro, energía 0..1]. */
      energia: [number, number][];
      /** Cuadros de los «uno». */
      golpes: number[];
      opacidad: number;
      mezcla: string;
      semilla: number;
    }
  | {
      /** Los clips teñidos a dos tintas: las sombras de `oscuro`, las luces de `claro`. Filtro sobre el contenido. */
      tipo: 'tinta';
      ini: number;
      fin: number;
      fundido?: number;
      oscuro: string;
      claro: string;
      /** 0 = el original … 1 = sólo las dos tintas. */
      fuerza: number;
    }
  | {
      /** El aire caliente: la imagen ondula hacia arriba y se agita en los golpes. Filtro sobre el contenido. */
      tipo: 'calima';
      ini: number;
      fin: number;
      fundido?: number;
      /** Desplazamiento en px: el de siempre y el empujón de cada golpe. */
      fuerza: number;
      golpe: number;
      golpes: number[];
      semilla: number;
    }
  | {
      /** Televisor viejo: líneas de barrido, colores corridos, una franja de luz que baja y la pantalla redondeada. */
      tipo: 'tv';
      ini: number;
      fin: number;
      fundido?: number;
      lineas: number;
      /** Corrimiento del rojo y el azul, en px. */
      corrimiento: number;
      curva: number;
      semilla: number;
    }
  | {
      /** Un texto que aparece letra por letra al pulso y se va con un fundido. */
      tipo: 'titulo';
      ini: number;
      fin: number;
      fundido?: number;
      texto: string;
      /** cartel (condensada, mayúsculas), oraculo (itálica serif), dato (mono). */
      voz: 'cartel' | 'oraculo' | 'dato';
      /** Alto de la letra, como fracción del alto del cuadro. */
      tam: number;
      /** Posición del texto (fracciones del cuadro) y alineación. */
      x: number;
      y: number;
      alinear: 'centro' | 'izquierda';
      color: string;
      /** Cuadro en que aparece cada letra (los espacios cuentan). */
      letras: number[];
    }
  | {
      /** «Sonando ahora»: el crédito de la canción como en una emisora, abajo a la izquierda. */
      tipo: 'credito';
      ini: number;
      fin: number;
      fundido?: number;
      lineas: [string, string];
      color: string;
    }
  | {
      /**
       * Rótulos: las frases del guion en pantalla. Cada una entra palabra por palabra
       * (cada palabra en su cuadro, al pulso) y se va con un fundido antes de la siguiente.
       */
      tipo: 'rotulos';
      ini: number;
      fin: number;
      fundido?: number;
      voz: 'cartel' | 'oraculo' | 'dato';
      /** Alto de la letra, como fracción del lado menor del cuadro. */
      tam: number;
      lugar: 'abajo' | 'centro' | 'arriba';
      color: string;
      /** Oscuridad de la mancha que va detrás para que se lea sobre cualquier imagen (0 = sin mancha). */
      sombra: number;
      lineas: {ini: number; fin: number; palabras: [string, number][]}[];
    }
  | {
      /** La cuenta regresiva de la cola de una película (4, 3, 2, 1), un número por golpe; tapa el cuadro. */
      tipo: 'cuenta';
      ini: number;
      fin: number;
      fundido?: number;
      /** Cuadro en que empieza cada número. */
      numeros: [number, number][];
      semilla: number;
    }
  | {
      /** La tira de película: bandas negras a los lados con sus perforaciones, que corren. */
      tipo: 'pelicula';
      ini: number;
      fin: number;
      fundido?: number;
      /** Ancho de cada banda, como fracción del ancho del cuadro. */
      borde: number;
      /** Perforaciones que pasan por segundo. */
      velocidad: number;
    }
  | {
      /** Una piedra en el agua: en cada golpe pedido, un anillo de distorsión se abre desde el centro. Filtro. */
      tipo: 'onda';
      ini: number;
      fin: number;
      fundido?: number;
      golpes: number[];
      /** Desplazamiento máximo (px) y cuadros que tarda el anillo en salir del cuadro. */
      fuerza: number;
      dura: number;
    }
  | {
      /** El foco respira: desenfocado entre golpes, nítido en cada golpe. Filtro. */
      tipo: 'foco';
      ini: number;
      fin: number;
      fundido?: number;
      golpes: number[];
      /** Desenfoque máximo (px). */
      fuerza: number;
    }
  | {
      /** Un empujón de zoom en cada golpe pedido, que vuelve enseguida. */
      tipo: 'golpe';
      ini: number;
      fin: number;
      fundido?: number;
      golpes: number[];
      /** Cuánto empuja (0.03 = 3 %). */
      fuerza: number;
    }
  | {
      /** La luz sigue a la canción: brillo y color del contenido según la energía, con un latido en cada golpe. Filtro. */
      tipo: 'luz';
      ini: number;
      fin: number;
      fundido?: number;
      /** La energía suavizada: [cuadro, 0..1] por golpe. */
      energia: [number, number][];
      golpes: number[];
      /** Brillo y saturación en la calma y en el pico (1 = sin cambio). */
      brillo: [number, number];
      color: [number, number];
      /** Cuánto sube el brillo en cada golpe. */
      golpe: number;
    }
  | {
      /** Las franjas negras del cine: se cierran en `abre` cuadros al entrar y se abren al salir. */
      tipo: 'barras';
      ini: number;
      fin: number;
      fundido?: number;
      /** Proporción del cuadro que queda a la vista (2.39 = cinemascope). */
      formato: number;
      abre: number;
      color: string;
    }
  | {
      /** La película gastada: rayones verticales que duran un rato y manchas de un cuadro. */
      tipo: 'rayas';
      ini: number;
      fin: number;
      fundido?: number;
      /** Cuántos rayones y manchas (0..1). */
      rayones: number;
      manchas: number;
      semilla: number;
    };

export type Collage = {
  /** Opacidad de la sombra de cada papel (0 = sin sombra). */
  sombra: number;
  /** Ordenadas por `ini`: la última queda arriba. */
  piezas: PiezaCollage[];
};

/** [cuadro, centro x, centro y, escala] — qué punto de la pared queda al centro y cuántos px por unidad. */
export type ClaveCamara = [number, number, number, number];

export type Timeline = {
  version: number;
  /** Prefijo de URL para los archivos de la biblioteca cuando lo dibuja el panel (no el render). */
  base?: string;
  modo?: 'superposicion' | 'actos' | 'collage' | 'cinta' | 'secuencia' | 'pulso' | 'solo-sintesis' | 'planos';
  proyecto: string;
  ancho: number;
  alto: number;
  fps: number;
  fondo: string;
  duracion: number;
  /** Tramo de la canción (segundos de la canción) y fundidos de entrada/salida (segundos). */
  audio: {src: string; desde: number; hasta?: number; fundido?: [number, number]} | null;
  meta?: Record<string, unknown>;
  actos?: Acto[];
  mural?: Mural;
  camara?: ClaveCamara[];
  ecos?: Eco[];
  collage?: Collage;
  cinta?: Cinta;
  momentos?: Momento[];
  logo?: Logo;
  sintesis?: Sintesis[];
  /** Modo planos: el video contado plano a plano, como un guion de documental (ver Planos.tsx). */
  planos?: Plano[];
  /** Textos que cruzan varios planos (los de una serie de fotos): en cuadros del video. */
  textos?: TextoPlano[];
  /**
   * Los subtítulos de la voz, en cuadros del video (una o dos filas, separadas por \n). `palabras`: cuándo se dice cada
   * palabra del texto ([ini, fin] en cuadros del video), para el karaoke.
   */
  subtitulos?: {ini: number; fin: number; texto: string; palabras?: [number, number][]}[];
  /** Con esto, los subtítulos se dibujan con un letrero de la galería de textos (p. ej. el karaoke) en vez de la caja de siempre. */
  subtitulos_letrero?: EstiloTexto;
  /** Las tipografías de fuentes/ que usan sus letreros (rutas dentro de fuentes/): el render las pone en la carpeta pública. */
  fuentes?: string[];
  capas: Capa[];
};

/**
 * Cómo entra un letrero: de a poco, subiendo, acercándose, enfocándose, letra a letra, palabra a palabra, barrido, con
 * las letras que se arman desde todas partes o en una ola.
 */
export type EntradaLetrero = 'fundido' | 'subir' | 'acercar' | 'desenfoque' | 'maquina' | 'palabras' | 'barrido' | 'armar' | 'ola' | 'ninguna';
export type LugarLetrero = 'centro' | 'arriba' | 'abajo' | 'tercio-inferior' | 'arriba-izquierda' | 'abajo-izquierda' | 'abajo-derecha';

/** Una línea de letra: la tipografía y su forma (los tamaños, en fracción del alto del cuadro; los espacios, en em). */
export type LetraLetrero = {
  /** Una familia de fuentes/fuentes.json (o del sistema, si no está ahí). */
  fuente: string;
  peso?: number;
  cursiva?: boolean;
  /** Ejes de la tipografía variable, p. ej. {SOFT: 100, WONK: 1} en Fraunces. */
  variacion?: Record<string, number>;
  tamano: number;
  mayusculas?: boolean;
  espaciado?: number;
  interlineado?: number;
  color: string;
  /** Aprieta la letra a lo ancho (0,82 = el «type 3c» del cartel de Curiana: la compresión es la identidad). */
  compresion?: number;
};

/**
 * Un estilo de la galería de textos (textos/<id>.json), tal como lo dibuja Letrero.tsx: la letra, su
 * contorno, sombra, caja o resaltado, dónde va y cómo entra y sale.
 */
export type EstiloTexto = LetraLetrero & {
  id: string;
  /** Borde de la letra (ancho en em), por detrás del relleno: la letra no adelgaza. */
  contorno?: {color: string; ancho: number};
  sombra?: {color: string; desenfoque: number; y?: number};
  /** Una caja detrás de cada fila (relleno en em; el color puede traer transparencia, #000000b3); con `bloque`, una sola caja para todo el texto (un papel). */
  caja?: {color: string; relleno: number; radio?: number; bloque?: boolean};
  /** Plumón detrás de la parte baja de cada fila. */
  resaltado?: {color: string};
  /** Una barra vertical a la izquierda del bloque (ancho en em), como en los rótulos de noticiero. */
  barra?: {color: string; ancho: number};
  alineado?: 'izquierda' | 'centro' | 'derecha';
  lugar: LugarLetrero;
  /** Ancho máximo del bloque, en fracción del ancho del cuadro. */
  ancho?: number;
  /** El bloque, girado (grados): lo escrito a mano o pegado no queda derecho. */
  giro?: number;
  entrada?: {tipo: EntradaLetrero; dura: number};
  /** atravesar: el letrero crece hasta que la cámara pasa por dentro de una letra (con `ventana`, se abre a la imagen). */
  salida?: {tipo: 'fundido' | 'bajar' | 'atravesar' | 'ninguna'; dura: number};
  /** La segunda línea (el cargo bajo el nombre, el rol sobre el nombre en los créditos). */
  secundario?: LetraLetrero & {arriba?: boolean};
  /** Créditos que suben: cada fila del texto es una línea; «rol | nombre» pone el rol con la letra secundaria. */
  rodillo?: boolean;
  /** La imagen (o el video) de abajo se ve sólo dentro de las letras; afuera, el color `fuera`. */
  ventana?: {fuera: string};
  /** Cada palabra se enciende cuando se dice: `activa` la que suena, `futura` las que vienen, `dicha` las que ya pasaron. */
  karaoke?: {activa: string; futura?: string; dicha?: string};
  /** Late con el golpe: crece un poco en cada pulso (`bpm`, o «cancion» para el tempo del proyecto) y vuelve. */
  latido?: {bpm: number | 'cancion'; fuerza: number; fase?: number};
  /** Con la entrada a máquina, el cursor que escribe y después parpadea. */
  cursor?: boolean;
};

/**
 * Un encuadre de la cámara sobre una imagen, en fracciones de la imagen: el centro (x, y) y el
 * ancho que ocupa la pantalla. `null` = la imagen entera, sin recortar (contenida).
 */
export type Encuadre = [number, number, number] | null;

/** Un rectángulo de la imagen en fracciones: [x0, y0, x1, y1]. */
export type Zona = [number, number, number, number];

export type EfectoPlano =
  /** Todo en gris menos `zona` (una elipse inscrita en ella), desde `ini` (cuadros del plano). */
  | {tipo: 'gris_fuera'; zona: Zona; ini: number; dura: number}
  /** La imagen entera en gris. */
  | {tipo: 'gris'; ini: number; dura: number}
  /** Un marcador amarillo que barre `zona` de izquierda a derecha. */
  | {tipo: 'resaltar'; zona: Zona; ini: number; dura: number; color?: string}
  /** Una línea que tacha `zona`. */
  | {tipo: 'tachar'; zona: Zona; ini: number; dura: number}
  /** Islas que no están: contornos punteados con su pregunta, una tras otra. */
  | {tipo: 'islas_fantasma'; islas: {x: number; y: number; ancho: number; texto: string}[]; ini: number; cada: number}
  /** El contorno de una silueta humana, sin rasgos. */
  | {tipo: 'silueta'; x: number; y: number; alto: number; ini: number; dura: number}
  /** Una isla nueva, dibujada a mano: el trazo avanza y después se rellena. */
  | {tipo: 'isla_nueva'; x: number; y: number; ancho: number; ini: number; dura: number; semilla?: number};

export type TextoPlano = {
  texto: string;
  /** titulo: grande al centro · rotulo: abajo a la izquierda, como las etiquetas del mapa · cita: la fuente, abajo a la derecha · frase: al centro, en cursiva · aviso: lo que falta (sólo en un borrador). */
  estilo: 'portada' | 'titulo' | 'rotulo' | 'cita' | 'frase' | 'aviso';
  /** Cuadros desde el comienzo del plano. */
  ini: number;
  fin: number;
  /** oscuro: letra oscura (sobre el mapa claro) · claro: letra clara (sobre fotos o negro). */
  tono?: 'oscuro' | 'claro' | 'contorno';
  /** arriba: arriba a la izquierda (sobre un video que ya trae subtítulos abajo y su logo arriba a la derecha). */
  lugar?: 'arriba';
  /** Un estilo de la galería de textos, ya resuelto por planificar (con él, `estilo`, `tono` y `lugar` no cuentan). */
  letrero?: EstiloTexto;
  /** La segunda línea del letrero (el cargo, la fecha, el rol). */
  secundario?: string;
};

export type Plano = {
  id: string;
  /** El número del plano en el guion. */
  n: number | string;
  ini: number;
  fin: number;
  /** Cuadros del fundido de entrada (0 = corte). El plano anterior sigue debajo hasta que éste termina de entrar. */
  entrada: number;
  /** La imagen (o el clip, con `video`); sin imagen, un fondo liso de `color`. */
  img?: string;
  fuente?: [number, number];
  color?: string;
  video?: {desde: number; volumen?: number};
  /** Un velo negro encima de la imagen (0 a 1): para que un título se lea sobre un video. */
  velo?: number;
  /**
   * Cómo entra sobre el plano anterior, en sus `entrada` cuadros (sin esto, fundido): las mismas transiciones de la
   * galería que en `pulso` (cortina, iris, empuje, destello, zoom). `dir`: hacia dónde avanza; `centro`: el del iris,
   * en fracciones de la pantalla.
   */
  transicion?: {tipo: 'cortina' | 'iris' | 'empuje' | 'destello' | 'zoom'; dir: [number, number]; centro?: [number, number]};
  /** En sus últimos `cuadros`, el plano que entra con empuje lo corre hacia `dir` hasta sacarlo. */
  empujada?: {cuadros: number; dir: [number, number]};
  /** La cámara: encuadres en cuadros del plano; entre uno y otro se mueve suave. */
  camara: {t: number; e: Encuadre}[];
  efectos?: EfectoPlano[];
  textos?: TextoPlano[];
  /** Créditos que suben de abajo hacia arriba durante todo el plano. */
  rodillo?: string[];
};

export const TIMELINE_VACIO: Timeline = {
  version: 1,
  proyecto: '(sin timeline: pasa --props=proyectos/<p>/timeline.json)',
  ancho: 1920,
  alto: 1080,
  fps: 30,
  fondo: '#08080a',
  duracion: 30,
  audio: null,
  capas: [],
};
