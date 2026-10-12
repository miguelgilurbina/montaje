// Lo que el panel sabe de los proyectos, leído del disco. Sólo del lado del servidor.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {formatear} from '@/lib/json';
import type {Timeline} from '@/src/tipos';

/** `next dev` corre desde la raíz del repo: la misma que usa montaje.py. */
export const RAIZ = process.cwd();
export const PROYECTOS = path.join(RAIZ, 'proyectos');
/** Mismo valor por defecto que `rutas.py`. */
export const MEDIOS = process.env.MONTAJE_MEDIOS ?? path.join(os.homedir(), 'Videos', 'montaje');

export type Musica = {
  archivo: string;
  tramo?: [number, number];
  duracion: number;
  bpm: number;
  beats: number[];
  energia: number[];
  fase_compas: number;
  primeros_tiempos: number[];
  secciones: {ini: number; fin: number; energia: number}[];
};

export type Resumen = {nombre: string; titulo: string; tieneTimeline: boolean};

export type Proyecto = {
  nombre: string;
  biblioteca: string;
  cfg: Record<string, unknown>;
  timeline: Timeline | null;
  musica: Musica | null;
};

export function nombreValido(nombre: string): boolean {
  return /^[\w.-]+$/.test(nombre) && !nombre.includes('..');
}

function leerJson<T>(ruta: string): T | null {
  if (!fs.existsSync(ruta)) return null;
  return JSON.parse(fs.readFileSync(ruta, 'utf-8')) as T;
}

export function listar(): Resumen[] {
  if (!fs.existsSync(PROYECTOS)) return [];
  return fs
    .readdirSync(PROYECTOS)
    .filter((n) => fs.existsSync(path.join(PROYECTOS, n, 'proyecto.json')))
    .sort()
    .map((nombre) => {
      const cfg = leerJson<{titulo?: string}>(path.join(PROYECTOS, nombre, 'proyecto.json')) ?? {};
      return {nombre, titulo: cfg.titulo ?? nombre, tieneTimeline: fs.existsSync(path.join(PROYECTOS, nombre, 'timeline.json'))};
    });
}

export function leerProyecto(nombre: string): Proyecto | null {
  if (!nombreValido(nombre)) return null;
  const cfg = leerJson<Record<string, unknown>>(path.join(PROYECTOS, nombre, 'proyecto.json'));
  if (!cfg) return null;
  const biblioteca = typeof cfg.biblioteca === 'string' ? cfg.biblioteca : nombre;
  const timeline = leerJson<Timeline>(path.join(PROYECTOS, nombre, 'timeline.json'));
  // Las salidas (análisis, renders) son propias del experimento; la biblioteca, compartida.
  const musica = leerJson<Musica>(path.join(MEDIOS, nombre, 'analisis', 'musica.json'));
  return {
    nombre,
    biblioteca,
    cfg,
    timeline: timeline ? {...timeline, base: `/medios/${biblioteca}/`} : null,
    musica,
  };
}

export function escribirProyecto(nombre: string, cfg: Record<string, unknown>): void {
  if (!nombreValido(nombre)) throw new Error('nombre inválido');
  fs.writeFileSync(path.join(PROYECTOS, nombre, 'proyecto.json'), formatear(cfg) + '\n', 'utf-8');
}
