// El catálogo de estilos, leído del disco: las recetas en estilos/*.json (el repo)
// y sus muestras en <medios>/estilos/<id>.mp4. Lo valida `python montaje.py estilos`;
// aquí sólo se lee. Sólo del lado del servidor.
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
