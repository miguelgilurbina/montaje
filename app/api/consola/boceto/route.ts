// El boceto: lo que se vio en la vista previa, grabado en el navegador mientras se tocaba (la aproximación, no el
// motor). Llega el archivo tal cual y queda en consola/bocetos/.
import fs from 'node:fs';
import path from 'node:path';
import {BOCETOS, conFecha} from '@/lib/consola';
import {MEDIOS} from '@/lib/proyectos';

export const dynamic = 'force-dynamic';

const TOPE = 400 * 1024 * 1024;

export async function POST(req: Request) {
  const tipo = req.headers.get('content-type') ?? '';
  const ext = tipo.includes('mp4') ? 'mp4' : tipo.includes('webm') ? 'webm' : null;
  if (!ext) return new Response('un boceto es webm o mp4', {status: 400});
  const datos = Buffer.from(await req.arrayBuffer());
  if (!datos.length || datos.length > TOPE) return new Response('boceto vacío o demasiado grande', {status: 400});
  fs.mkdirSync(BOCETOS, {recursive: true});
  const nombre = new URL(req.url).searchParams.get('nombre') ?? 'boceto';
  const destino = path.join(BOCETOS, `${conFecha(nombre)}.${ext}`);
  fs.writeFileSync(destino, datos);
  return Response.json({ruta: path.relative(MEDIOS, destino).split(path.sep).join('/')});
}
