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
  /** La muestra del probador (el mismo banco para todos) y lo que midió, o por qué no se probó. */
  probador: Probado | null;
  noSePrueba?: string;
  falla?: string;
  /** Cuánto gana cuando Miguel lo elige entre dos. */
  elecciones?: Puntaje;
  familia: Familia;
  /** Si casi no se distingue de otro estilo, vive dentro de él en la galería (2026-11-22): su id y lo que los separa. */
  variante_de?: string;
  diferencia?: string;
  /** Las del principal: cada una con lo que la separa y su muestra del probador. */
  variantes?: Variante[];
};

export type Variante = {id: string; nombre: string; diferencia: string; estado: Estado; probador: string | null};

export type Probado = {
  url: string;
  mb: number;
  fecha: string;
  lienzo: string;
  /** Segundos que tardó en dibujarse y cuántas veces lo que tarda el banco solo. */
  dibujo_s: number | null;
  costo: number | null;
  /** El parecido de sus cuadros con los de referencia (1 = idéntico); null si la referencia es nueva. */
  parecido: number[] | null;
  cambio: boolean;
};

export type Puntaje = {ganadas: number; jugadas: number; puntaje: number};

/** Para elegir entre dos se comparan estilos de la misma familia: dos transiciones, dos filtros. */
export type Familia = 'transiciones' | 'efectos de tiempo' | 'filtros y texturas' | 'gestos' | 'textos y gráficos' | 'formatos' | 'montajes';
export const FAMILIAS: Familia[] = ['transiciones', 'efectos de tiempo', 'filtros y texturas', 'gestos', 'textos y gráficos', 'formatos', 'montajes'];

const TEXTOS = new Set(['titulo', 'rotulos', 'credito', 'cuenta', 'partitura']);

export function familiaDe(t: Record<string, unknown>, para: string[]): Familia {
  // Un gesto (la pausa del VHS, el estrobo de la consola) va encima de una base: se compara con otro gesto.
  if (t.gesto === true) return 'gestos';
  // Una transición es el estilo entero, no una perilla de paso: «fotos y clips» lleva cortina y es un montaje.
  if (typeof t.transicion === 'string' && t.transicion !== 'fundido' && para.includes('transición')) return 'transiciones';
  if (t.comando === 'transformar') return 'efectos de tiempo';
  if (typeof t.capa === 'string') return TEXTOS.has(t.capa) ? 'textos y gráficos' : 'filtros y texturas';
  if (typeof t.salida === 'string') return 'formatos';
  return 'montajes';
}

/** Las mismas constantes que py/montaje/probador.py: el estilo que es el banco solo y desde cuánto un cuadro es el mismo. */
const BASE = 'toma-por-frase';
const IGUAL = 0.98;
const PROBADOR = path.join(MEDIOS, 'estilos', 'probador');

type Registro = Record<string, {fecha: string; lienzo?: string; dibujo_s?: number | null; parecido?: number[] | null; motivo?: string; falla?: string}>;

function leerJson<T>(archivo: string, vacio: T): T {
  try {
    return JSON.parse(fs.readFileSync(archivo, 'utf-8')) as T;
  } catch {
    return vacio;
  }
}

/** Como `estilos.puntajes` en Python: (ganadas + 1) / (jugadas + 2), para que dos elecciones no hagan un orden. */
export function puntajes(): Record<string, Puntaje> {
  const lista = leerJson<{a: string; b: string; gana: string}[]>(path.join(RAIZ, 'direccion', 'COMPARACIONES.json'), []);
  const tabla: Record<string, Puntaje> = {};
  for (const c of lista) {
    for (const x of [c.a, c.b]) {
      const t = (tabla[x] ??= {ganadas: 0, jugadas: 0, puntaje: 0.5});
      t.jugadas += 1;
      t.ganadas += c.gana === x ? 1 : c.gana === 'igual' ? 0.5 : 0;
    }
  }
  for (const t of Object.values(tabla)) t.puntaje = Math.round(((t.ganadas + 1) / (t.jugadas + 2)) * 1000) / 1000;
  return tabla;
}

export function cuantasComparaciones(): number {
  return leerJson<unknown[]>(path.join(RAIZ, 'direccion', 'COMPARACIONES.json'), []).length;
}

function probado(id: string, registro: Registro): Probado | null {
  const archivo = path.join(PROBADOR, `${id}.mp4`);
  const r = registro[id];
  if (!r || !fs.existsSync(archivo) || r.motivo) return null;
  const st = fs.statSync(archivo);
  const base = registro[BASE]?.dibujo_s;
  return {
    url: `/medios/estilos/probador/${id}.mp4?v=${Math.round(st.mtimeMs)}`,
    mb: st.size / 1e6,
    fecha: r.fecha,
    lienzo: r.lienzo ?? '',
    dibujo_s: r.dibujo_s ?? null,
    costo: r.dibujo_s && base ? Math.round((r.dibujo_s / base) * 10) / 10 : null,
    parecido: r.parecido ?? null,
    cambio: Boolean(r.parecido && Math.min(...r.parecido) < IGUAL),
  };
}

export function leerEstilos(): Estilo[] {
  if (!fs.existsSync(ESTILOS)) return [];
  const registro = leerJson<Registro>(path.join(PROBADOR, 'registro.json'), {});
  const gana = puntajes();
  const todos: Estilo[] = fs
    .readdirSync(ESTILOS)
    .filter((n) => n.endsWith('.json'))
    .map((n) => {
      const id = n.slice(0, -5);
      const e = JSON.parse(fs.readFileSync(path.join(ESTILOS, n), 'utf-8')) as Omit<Estilo, 'id' | 'video' | 'probador' | 'familia'>;
      const archivo = path.join(MEDIOS, 'estilos', `${id}.mp4`);
      const st = fs.existsSync(archivo) ? fs.statSync(archivo) : null;
      // El mtime en la URL: una muestra nueva no se queda en la caché del navegador.
      const video = st ? {url: `/medios/estilos/${id}.mp4?v=${Math.round(st.mtimeMs)}`, mb: st.size / 1e6} : null;
      const r = registro[id];
      return {
        ...e,
        id,
        video,
        probador: probado(id, registro),
        noSePrueba: r?.motivo,
        falla: r?.falla,
        elecciones: gana[id],
        familia: familiaDe(e.tecnica, e.para),
      };
    })
    .sort((a, b) => ESTADOS.indexOf(a.estado) - ESTADOS.indexOf(b.estado) || a.nombre.localeCompare(b.nombre, 'es'));
  // Cada principal lleva sus variantes (las valida `python montaje.py estilos`).
  for (const v of todos) {
    const principal = v.variante_de ? todos.find((e) => e.id === v.variante_de) : undefined;
    if (!principal) continue;
    (principal.variantes ??= []).push({id: v.id, nombre: v.nombre, diferencia: v.diferencia ?? '', estado: v.estado, probador: v.probador?.url ?? null});
  }
  return todos;
}

/**
 * Anota el veredicto de un estilo. Lo escribe `python montaje.py veredicto`, el mismo que
 * escribe todos los estilos: así el archivo conserva su formato (los números, los saltos de
 * línea) y la cita de Miguel se limpia en un solo lugar. Los argumentos van como lista, sin
 * pasar por un intérprete de comandos. Devuelve el estado y las palabras como quedaron, o
 * null si el estilo no existe.
 */
export function guardarVeredicto(id: string, estado: Estado, cita: string): {estado: Estado; miguel: string[]} | null {
  // Un estilo (estilos/) o un letrero de la galería de textos (textos/): el mismo veredicto, lo escribe Python.
  const existe = ['estilos', 'textos'].some((d) => fs.existsSync(path.join(RAIZ, d, `${id}.json`)));
  if (!/^[a-z0-9][a-z0-9-]*$/.test(id) || !existe) return null;
  const python = process.platform === 'win32' ? 'python' : 'python3';
  const r = spawnSync(python, ['montaje.py', 'veredicto', id, estado, `--cita=${cita.slice(0, 2000)}`, '--via', 'galeria'], {
    cwd: RAIZ,
    encoding: 'utf-8',
    env: {...process.env, PYTHONIOENCODING: 'utf-8'},
  });
  if (r.status !== 0) throw new Error((r.stderr || r.stdout || 'no pude anotar el veredicto').trim().split('\n').pop());
  return JSON.parse(r.stdout.trim().split('\n').pop() as string) as {estado: Estado; miguel: string[]};
}

/** Anota cuál de dos estilos eligió Miguel. Lo escribe `python montaje.py comparar`, como el veredicto. */
export function guardarComparacion(a: string, b: string, gana: string): void {
  const id = /^[a-z0-9][a-z0-9-]*$/;
  if (![a, b].every((x) => id.test(x) && fs.existsSync(path.join(ESTILOS, `${x}.json`)))) throw new Error('no existe ese estilo');
  if (gana !== a && gana !== b && gana !== 'igual') throw new Error('gana uno de los dos, o igual');
  const python = process.platform === 'win32' ? 'python' : 'python3';
  const r = spawnSync(python, ['montaje.py', 'comparar', a, b, '--gana', gana, '--via', 'galeria'], {
    cwd: RAIZ,
    encoding: 'utf-8',
    env: {...process.env, PYTHONIOENCODING: 'utf-8'},
  });
  if (r.status !== 0) throw new Error((r.stderr || r.stdout || 'no pude anotar la elección').trim().split('\n').pop());
}
