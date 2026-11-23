// Lo que la consola del panel sabe del disco: los aparatos y sus perillas (los dice el motor), las fuentes que se
// pueden tocar, las sesiones guardadas y los renders. Sólo del lado del servidor.
import {execFile} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import {MEDIOS, RAIZ, nombreValido} from '@/lib/proyectos';

export const CONSOLA = path.join(MEDIOS, 'consola');
export const SESIONES = path.join(CONSOLA, 'sesiones');
export const RENDERS = path.join(CONSOLA, 'renders');
export const BOCETOS = path.join(CONSOLA, 'bocetos');

export const PYTHON = process.platform === 'win32' ? 'python' : 'python3';

export type Perilla = {defecto: unknown; rango: unknown[] | null};
export type Aparato = {tipo: 'imagen' | 'señal'; gesto: boolean; modulo: string; doc: string; perillas: Record<string, Perilla>};
export type CadenaGaleria = {id: string; frase: string; estado: string; aparatos: Record<string, unknown>[]; captura: string; semilla: number};
export type Catalogo = {aparatos: Record<string, Aparato>; cadenas: CadenaGaleria[]};
export type Fuente = {ruta: string; carpeta: string; nombre: string; bytes: number};

let catalogo: {cuando: number; datos: Catalogo} | null = null;

/** Los aparatos de la mesa y las cadenas de la galería, como los dice el motor (`analogo --aparatos`). Se guarda en
 * memoria un rato: preguntarle a Python tarda un par de segundos. */
export async function leerCatalogo(fresco = false): Promise<Catalogo> {
  if (catalogo && !fresco && Date.now() - catalogo.cuando < 5 * 60_000) return catalogo.datos;
  const salida = await new Promise<string>((ok, mal) =>
    execFile(
      PYTHON,
      ['montaje.py', 'analogo', '--aparatos'],
      {cwd: RAIZ, env: {...process.env, PYTHONIOENCODING: 'utf-8'}, maxBuffer: 16 * 1024 * 1024},
      (err, stdout, stderr) => (err ? mal(new Error(stderr || err.message)) : ok(stdout)),
    ),
  );
  const datos = JSON.parse(salida) as Catalogo;
  catalogo = {cuando: Date.now(), datos};
  return datos;
}

const VIDEO = /\.(mp4|mov|m4v|webm)$/i;
// Dónde hay material para tocar: los clips de práctica y del banco, los renders de los proyectos, lo que ya salió de
// la consola. Nada de las muestras de la galería, las copias de trabajo ni lo que no es de la biblioteca.
const FUERA = /(^|[\\/])(estilos|proxies|transformados|borradores|seleccion|modelos|transcripciones|marca|23-[^\\/]*)([\\/]|$)/i;

/** Los videos de la biblioteca que la consola puede tocar, agrupados por carpeta. */
export function listarFuentes(): Fuente[] {
  const sale: Fuente[] = [];
  const recorrer = (dir: string, hondo: number) => {
    let entradas: fs.Dirent[];
    try {
      entradas = fs.readdirSync(dir, {withFileTypes: true});
    } catch {
      return;
    }
    for (const e of entradas) {
      if (e.name.startsWith('.')) continue;
      const abs = path.join(dir, e.name);
      const rel = path.relative(MEDIOS, abs);
      if (FUERA.test(rel)) continue;
      if (e.isDirectory() && hondo < 3) recorrer(abs, hondo + 1);
      else if (e.isFile() && VIDEO.test(e.name)) {
        const st = fs.statSync(abs);
        sale.push({ruta: rel.split(path.sep).join('/'), carpeta: path.dirname(rel).split(path.sep).join('/'), nombre: e.name, bytes: st.size});
      }
    }
  };
  recorrer(MEDIOS, 0);
  return sale.sort((a, b) => a.carpeta.localeCompare(b.carpeta) || a.nombre.localeCompare(b.nombre));
}

/** Una ruta relativa a los medios que de verdad está dentro de ellos y existe. */
export function fuenteSegura(rel: unknown): string | null {
  if (typeof rel !== 'string' || !VIDEO.test(rel)) return null;
  const raiz = path.resolve(MEDIOS);
  const abs = path.resolve(raiz, rel);
  if (!abs.startsWith(raiz + path.sep) || FUERA.test(path.relative(raiz, abs))) return null;
  return fs.existsSync(abs) && fs.statSync(abs).isFile() ? abs : null;
}

export function listarSesiones(): {nombre: string; cuando: number}[] {
  if (!fs.existsSync(SESIONES)) return [];
  return fs
    .readdirSync(SESIONES)
    .filter((n) => n.endsWith('.json'))
    .map((n) => ({nombre: n.slice(0, -5), cuando: fs.statSync(path.join(SESIONES, n)).mtimeMs}))
    .sort((a, b) => b.cuando - a.cuando);
}

export function leerSesion(nombre: string): unknown | null {
  if (!nombreValido(nombre)) return null;
  const ruta = path.join(SESIONES, `${nombre}.json`);
  return fs.existsSync(ruta) ? JSON.parse(fs.readFileSync(ruta, 'utf-8')) : null;
}

export function guardarSesion(nombre: string, sesion: unknown): boolean {
  if (!nombreValido(nombre)) return false;
  fs.mkdirSync(SESIONES, {recursive: true});
  fs.writeFileSync(path.join(SESIONES, `${nombre}.json`), JSON.stringify(sesion, null, 2) + '\n', 'utf-8');
  return true;
}

/** Lo que ya salió de la consola: los renders del motor y los bocetos grabados en el navegador. */
export function listarSalidas(): {ruta: string; tipo: 'render' | 'boceto'; cuando: number}[] {
  const sale: {ruta: string; tipo: 'render' | 'boceto'; cuando: number}[] = [];
  for (const [dir, tipo] of [
    [RENDERS, 'render'],
    [BOCETOS, 'boceto'],
  ] as const) {
    if (!fs.existsSync(dir)) continue;
    for (const n of fs.readdirSync(dir)) {
      if (!VIDEO.test(n)) continue;
      sale.push({ruta: path.relative(MEDIOS, path.join(dir, n)).split(path.sep).join('/'), tipo, cuando: fs.statSync(path.join(dir, n)).mtimeMs});
    }
  }
  return sale.sort((a, b) => b.cuando - a.cuando);
}

/** Un nombre de archivo con la fecha delante: `2026-11-23-2210-<nombre>`. */
export function conFecha(nombre: string): string {
  const d = new Date();
  const dos = (n: number) => String(n).padStart(2, '0');
  const limpio = nombre.normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^\w-]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 48) || 'toma';
  return `${d.getFullYear()}-${dos(d.getMonth() + 1)}-${dos(d.getDate())}-${dos(d.getHours())}${dos(d.getMinutes())}-${limpio}`;
}
