// Las sesiones de la consola: la fuente, la cadena con sus perillas, lo grabado y el MIDI, en los medios
// (consola/sesiones/<nombre>.json), fuera del repo.
import {guardarSesion, leerSesion} from '@/lib/consola';

export const dynamic = 'force-dynamic';

export async function GET(req: Request) {
  const nombre = new URL(req.url).searchParams.get('nombre') ?? '';
  const s = leerSesion(nombre);
  return s ? Response.json(s) : new Response('no existe', {status: 404});
}

export async function POST(req: Request) {
  const {nombre, sesion} = (await req.json()) as {nombre: string; sesion: unknown};
  if (!sesion || typeof sesion !== 'object') return new Response('falta la sesión', {status: 400});
  return guardarSesion(nombre, sesion) ? Response.json({ok: true}) : new Response('nombre inválido', {status: 400});
}
