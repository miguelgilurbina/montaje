// El render de verdad: la fuente por la cadena del motor, con los movimientos de las perillas grabados en la consola.
// Deja en consola/renders/ el video y, al lado, la receta (fuente, cadena, automatización, tramo) para repetirlo.
// La salida del motor llega a medida que sale, como en /api/correr.
import {spawn} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import {MEDIOS, RAIZ} from '@/lib/proyectos';
import {PYTHON, RENDERS, conFecha, fuenteSegura} from '@/lib/consola';

export const dynamic = 'force-dynamic';

type Pedido = {
  fuente: string;
  nombre?: string;
  cadena: {aparatos: Record<string, unknown>[]; captura?: string; semilla?: number};
  automatizacion?: {paso: number; perilla: string; puntos: [number, unknown][]; curva?: string}[];
  desde?: number;
  hasta?: number;
  alto?: number;
};

const numero = (v: unknown) => (typeof v === 'number' && Number.isFinite(v) && v >= 0 ? v : null);

export async function POST(req: Request) {
  const p = (await req.json()) as Pedido;
  const fuente = fuenteSegura(p.fuente);
  if (!fuente) return new Response('esa fuente no está en los medios', {status: 400});
  if (!p.cadena || !Array.isArray(p.cadena.aparatos) || !p.cadena.aparatos.length) return new Response('la cadena está vacía', {status: 400});
  const auto = Array.isArray(p.automatizacion) ? p.automatizacion : [];

  fs.mkdirSync(RENDERS, {recursive: true});
  const base = conFecha(p.nombre ?? path.parse(fuente).name);
  const salida = path.join(RENDERS, `${base}.mp4`);
  const receta = path.join(RENDERS, `${base}.json`);
  const desde = numero(p.desde);
  const hasta = numero(p.hasta);
  const alto = numero(p.alto);
  fs.writeFileSync(
    receta,
    JSON.stringify({fuente: path.relative(MEDIOS, fuente).split(path.sep).join('/'), cadena: p.cadena, automatizacion: auto, desde, hasta, alto}, null, 2) + '\n',
    'utf-8',
  );

  // La cadena va como JSON en un argumento (sin shell: nada se interpreta); lo grabado, en la receta.
  const args = ['montaje.py', 'analogo', fuente, '--cadena', JSON.stringify(p.cadena), '--salida', salida];
  if (auto.length) args.push('--automatizacion', receta);
  if (desde !== null) args.push('--desde', String(desde));
  if (hasta !== null) args.push('--hasta', String(hasta));
  if (alto !== null && [360, 480, 540, 720, 1080].includes(alto)) args.push('--alto', String(alto));

  const hijo = spawn(PYTHON, args, {cwd: RAIZ, env: {...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUNBUFFERED: '1'}});
  const codificar = new TextEncoder();
  const cuerpo = new ReadableStream<Uint8Array>({
    start(ctl) {
      ctl.enqueue(codificar.encode(`→ ${path.relative(MEDIOS, salida).split(path.sep).join('/')}\n`));
      const pasar = (d: Buffer) => ctl.enqueue(new Uint8Array(d));
      hijo.stdout.on('data', pasar);
      hijo.stderr.on('data', pasar);
      hijo.on('error', (e) => {
        ctl.enqueue(codificar.encode(`\n[no pude correr ${PYTHON}: ${e.message}]\n`));
        ctl.close();
      });
      hijo.on('close', (codigo) => {
        ctl.enqueue(codificar.encode(`\n[fin: ${codigo === 0 ? 'ok' : `código ${codigo}`}]\n`));
        ctl.close();
      });
    },
    cancel() {
      hijo.kill();
    },
  });
  return new Response(cuerpo, {
    headers: {'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-cache', 'X-Content-Type-Options': 'nosniff'},
  });
}
