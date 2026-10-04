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
};

export type Timeline = {
  version: number;
  proyecto: string;
  ancho: number;
  alto: number;
  fps: number;
  fondo: string;
  duracion: number;
  audio: {src: string; desde: number} | null;
  meta?: Record<string, unknown>;
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
