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

/** [cuadro, centro x, centro y, escala] — qué punto de la pared queda al centro y cuántos px por unidad. */
export type ClaveCamara = [number, number, number, number];

export type Timeline = {
  version: number;
  modo?: 'superposicion' | 'actos';
  proyecto: string;
  ancho: number;
  alto: number;
  fps: number;
  fondo: string;
  duracion: number;
  audio: {src: string; desde: number} | null;
  meta?: Record<string, unknown>;
  actos?: Acto[];
  mural?: Mural;
  camara?: ClaveCamara[];
  ecos?: Eco[];
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
