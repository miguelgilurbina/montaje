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
  | {tipo: 'barrido'; ini: number; fin: number};

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
  modo?: 'superposicion' | 'actos' | 'collage';
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
  capas: Capa[];
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
