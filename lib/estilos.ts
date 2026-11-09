// El catálogo de estilos, leído del disco: las recetas en estilos/*.json (el repo)
// y sus muestras en <medios>/estilos/<id>.mp4. Lo valida `python montaje.py estilos`;
// aquí se lee y, desde la galería, se anota el veredicto de Miguel. Sólo del lado del servidor.
import {spawnSync} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import {MEDIOS, RAIZ} from '@/lib/proyectos';

export const ESTILOS = path.join(RAIZ, 'estilos');

export type Estado = 'aprobado' | 'a medias' | 'pedido' | 'propuesta' | 'rechazado';

/** El orden en que se muestran: lo que se puede usar primero, lo que no, al final. */
export const ESTADOS: Estado[] = ['aprobado', 'a medias', 'pedido', 'propuesta', 'rechazado'];

export type Estilo = {
  id: string;
  nombre: string;
  frase: string;
  para: string[];
  material: string;
  energia: string;
  dura: string;
  tecnica: Record<string, unknown>;
  estado: Estado;
  miguel: string[];
  visto_en: string[];
  evitar: string[];
  muestra?: {de: string; desde: number; hasta: number};
  /** El último veredicto dado desde la galería (el clic de Miguel vale como veredicto aunque no escriba nada). */
  veredicto?: {estado: Estado; fecha: string; via: 'galeria'};
  /** Si la muestra está en disco: su URL en el panel y su peso. */
  video: {url: string; mb: number} | null;
};

export function leerEstilos(): Estilo[] {
  if (!fs.existsSync(ESTILOS)) return [];
  return fs
    .readdirSync(ESTILOS)
    .filter((n) => n.endsWith('.json'))
    .map((n) => {
      const id = n.slice(0, -5);
      const e = JSON.parse(fs.readFileSync(path.join(ESTILOS, n), 'utf-8')) as Omit<Estilo, 'id' | 'video'>;
      const archivo = path.join(MEDIOS, 'estilos', `${id}.mp4`);
      const st = fs.existsSync(archivo) ? fs.statSync(archivo) : null;
      // El mtime en la URL: una muestra nueva no se queda en la caché del navegador.
      const video = st ? {url: `/medios/estilos/${id}.mp4?v=${Math.round(st.mtimeMs)}`, mb: st.size / 1e6} : null;
      return {...e, id, video};
    })
    .sort((a, b) => ESTADOS.indexOf(a.estado) - ESTADOS.indexOf(b.estado) || a.nombre.localeCompare(b.nombre, 'es'));
}

/**
 * Anota el veredicto de un estilo. Lo escribe `python montaje.py veredicto`, el mismo que
 * escribe todos los estilos: así el archivo conserva su formato (los números, los saltos de
 * línea) y la cita de Miguel se limpia en un solo lugar. Los argumentos van como lista, sin
 * pasar por un intérprete de comandos. Devuelve el estado y las palabras como quedaron, o
 * null si el estilo no existe.
 */
export function guardarVeredicto(id: string, estado: Estado, cita: string): {estado: Estado; miguel: string[]} | null {
  if (!/^[a-z0-9][a-z0-9-]*$/.test(id) || !fs.existsSync(path.join(ESTILOS, `${id}.json`))) return null;
  const python = process.platform === 'win32' ? 'python' : 'python3';
  const r = spawnSync(python, ['montaje.py', 'veredicto', id, estado, `--cita=${cita.slice(0, 2000)}`, '--via', 'galeria'], {
    cwd: RAIZ,
    encoding: 'utf-8',
    env: {...process.env, PYTHONIOENCODING: 'utf-8'},
  });
  if (r.status !== 0) throw new Error((r.stderr || r.stdout || 'no pude anotar el veredicto').trim().split('\n').pop());
  return JSON.parse(r.stdout.trim().split('\n').pop() as string) as {estado: Estado; miguel: string[]};
}
