// Sirve los medios (imágenes, audio, video) desde ~/Videos/montaje, con rangos:
// sin `Range`, el reproductor no puede saltar dentro del audio ni del video.
import {createReadStream, statSync} from 'node:fs';
import path from 'node:path';
import {Readable} from 'node:stream';
import {MEDIOS} from '@/lib/proyectos';

export const dynamic = 'force-dynamic';

const TIPOS: Record<string, string> = {
  '.webp': 'image/webp',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.mp3': 'audio/mpeg',
  '.wav': 'audio/wav',
  '.mp4': 'video/mp4',
  '.json': 'application/json',
};

export async function GET(req: Request, {params}: {params: Promise<{ruta: string[]}>}) {
  const {ruta} = await params;
  const raiz = path.resolve(MEDIOS);
  const archivo = path.resolve(raiz, ...ruta.map(decodeURIComponent));
  if (!archivo.startsWith(raiz + path.sep)) return new Response('fuera de los medios', {status: 403});
  let st;
  try {
    st = statSync(archivo);
  } catch {
    return new Response('no existe', {status: 404});
  }
  if (!st.isFile()) return new Response('no es un archivo', {status: 404});

  let inicio = 0;
  let fin = st.size - 1;
  let status = 200;
  const rango = /bytes=(\d*)-(\d*)/.exec(req.headers.get('range') ?? '');
  if (rango) {
    if (rango[1]) inicio = Number(rango[1]);
    if (rango[2]) fin = Math.min(Number(rango[2]), st.size - 1);
    if (!rango[1] && rango[2]) inicio = Math.max(0, st.size - Number(rango[2]));
    if (inicio > fin || inicio >= st.size) {
      return new Response('rango fuera del archivo', {status: 416, headers: {'Content-Range': `bytes */${st.size}`}});
    }
    status = 206;
  }
  const cuerpo = Readable.toWeb(createReadStream(archivo, {start: inicio, end: fin})) as ReadableStream;
  const headers: Record<string, string> = {
    'Content-Type': TIPOS[path.extname(archivo).toLowerCase()] ?? 'application/octet-stream',
    'Content-Length': String(fin - inicio + 1),
    'Accept-Ranges': 'bytes',
    'Cache-Control': 'no-cache',
  };
  if (status === 206) headers['Content-Range'] = `bytes ${inicio}-${fin}/${st.size}`;
  return new Response(cuerpo, {status, headers});
}
