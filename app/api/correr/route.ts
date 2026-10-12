// Corre un comando de montaje.py y devuelve su salida a medida que sale.
// Sólo los comandos de la lista, con argumentos armados aquí: nada del cliente
// llega a la línea de comandos tal cual.
import {spawn} from 'node:child_process';
import {RAIZ, leerProyecto, nombreValido} from '@/lib/proyectos';

export const dynamic = 'force-dynamic';

type Opciones = Record<string, unknown>;

const numero = (v: unknown): string | null => (typeof v === 'number' && Number.isFinite(v) ? String(v) : null);

const COMANDOS: Record<string, (o: Opciones) => string[]> = {
  planificar: () => [],
  musica: () => [],
  catalogo: () => [],
  sonorizar: () => [],
  senal: () => [],
  render: (o) => {
    const args: string[] = [];
    if (o.preview) args.push('--preview');
    const desde = numero(o.desde);
    const hasta = numero(o.hasta);
    if (desde !== null) args.push('--desde', desde);
    if (hasta !== null) args.push('--hasta', hasta);
    if (typeof o.salida === 'string' && /^[\w-]+$/.test(o.salida)) args.push('--salida', o.salida);
    return args;
  },
};

export async function POST(req: Request) {
  const {nombre, comando, opciones = {}} = (await req.json()) as {nombre: string; comando: string; opciones?: Opciones};
  if (!nombreValido(nombre) || !leerProyecto(nombre)) return new Response('proyecto inválido', {status: 404});
  const armar = COMANDOS[comando];
  if (!armar) return new Response(`comando no permitido: ${comando}`, {status: 400});

  const python = process.platform === 'win32' ? 'python' : 'python3';
  const hijo = spawn(python, ['montaje.py', comando, nombre, ...armar(opciones)], {
    cwd: RAIZ,
    env: {...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUNBUFFERED: '1'},
  });
  const codificar = new TextEncoder();
  const cuerpo = new ReadableStream<Uint8Array>({
    start(ctl) {
      const pasar = (d: Buffer) => ctl.enqueue(new Uint8Array(d));
      hijo.stdout.on('data', pasar);
      hijo.stderr.on('data', pasar);
      hijo.on('error', (e) => {
        ctl.enqueue(codificar.encode(`\n[no pude correr ${python}: ${e.message}]\n`));
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
