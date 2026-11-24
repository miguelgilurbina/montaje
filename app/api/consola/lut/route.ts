// Las tablas de color (el aparato `color`) para la vista previa: las escribe el motor (`montaje.py color --json`),
// así la consola usa las mismas tablas que el render. `?tabla=<nombre>` o `?archivo=<.cube dentro de los medios>`.
import {execFile} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import {MEDIOS, RAIZ} from '@/lib/proyectos';
import {PYTHON} from '@/lib/consola';

export const dynamic = 'force-dynamic';

const guardadas = new Map<string, {cuando: number; json: string}>();

export async function GET(req: Request) {
  const q = new URL(req.url).searchParams;
  let arg: string;
  let clave: string;
  const archivo = q.get('archivo');
  if (archivo) {
    const raiz = path.resolve(MEDIOS);
    const abs = path.resolve(raiz, archivo);
    if (!abs.toLowerCase().endsWith('.cube') || !abs.startsWith(raiz + path.sep) || !fs.existsSync(abs)) {
      return new Response('ese .cube no está en los medios', {status: 400});
    }
    arg = abs;
    clave = `${abs}@${fs.statSync(abs).mtimeMs}`;
  } else {
    const tabla = q.get('tabla') ?? '';
    if (!/^[\w-]+$/.test(tabla)) return new Response('tabla inválida', {status: 400});
    arg = tabla;
    clave = tabla;
  }
  const hay = guardadas.get(clave);
  if (hay) return new Response(hay.json, {headers: {'Content-Type': 'application/json'}});
  try {
    const json = await new Promise<string>((ok, mal) =>
      execFile(
        PYTHON,
        ['montaje.py', 'color', '--json', arg],
        {cwd: RAIZ, env: {...process.env, PYTHONIOENCODING: 'utf-8'}, maxBuffer: 64 * 1024 * 1024},
        (err, stdout, stderr) => (err ? mal(new Error(stderr || err.message)) : ok(stdout)),
      ),
    );
    guardadas.set(clave, {cuando: Date.now(), json});
    return new Response(json, {headers: {'Content-Type': 'application/json'}});
  } catch (e) {
    return new Response(`el motor no dio la tabla: ${(e as Error).message}`, {status: 500});
  }
}
