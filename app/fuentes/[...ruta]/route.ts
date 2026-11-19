// Sirve las tipografías del repo (fuentes/) al panel: Letrero.tsx las pide a /fuentes/<carpeta>/<archivo>.ttf.
// En el render salen de la carpeta pública, adonde las copia montaje.py.
import {readFileSync, statSync} from 'node:fs';
import path from 'node:path';
import {RAIZ} from '@/lib/proyectos';

export const dynamic = 'force-dynamic';

const TIPOS: Record<string, string> = {'.ttf': 'font/ttf', '.otf': 'font/otf', '.woff2': 'font/woff2', '.json': 'application/json'};

export async function GET(_req: Request, {params}: {params: Promise<{ruta: string[]}>}) {
  const {ruta} = await params;
  const raiz = path.resolve(RAIZ, 'fuentes');
  const archivo = path.resolve(raiz, ...ruta.map(decodeURIComponent));
  const tipo = TIPOS[path.extname(archivo).toLowerCase()];
  if (!archivo.startsWith(raiz + path.sep) || !tipo) return new Response('no es una tipografía', {status: 403});
  try {
    if (!statSync(archivo).isFile()) throw new Error();
  } catch {
    return new Response('no existe', {status: 404});
  }
  return new Response(readFileSync(archivo), {headers: {'Content-Type': tipo, 'Cache-Control': 'no-cache'}});
}
