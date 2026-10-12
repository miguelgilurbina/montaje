import {escribirProyecto, leerProyecto, nombreValido} from '@/lib/proyectos';

export const dynamic = 'force-dynamic';

export async function GET(_req: Request, {params}: {params: Promise<{nombre: string}>}) {
  const {nombre} = await params;
  const p = leerProyecto(nombre);
  if (!p) return Response.json({error: `no existe el proyecto ${nombre}`}, {status: 404});
  return Response.json(p);
}

/** Guarda proyecto.json. El cuerpo es el objeto entero: lo que no venga, se pierde. */
export async function PUT(req: Request, {params}: {params: Promise<{nombre: string}>}) {
  const {nombre} = await params;
  if (!nombreValido(nombre) || !leerProyecto(nombre)) return Response.json({error: 'proyecto inválido'}, {status: 404});
  const cfg = (await req.json()) as Record<string, unknown>;
  if (!cfg || typeof cfg !== 'object' || Array.isArray(cfg)) return Response.json({error: 'el cuerpo debe ser un objeto'}, {status: 400});
  escribirProyecto(nombre, cfg);
  return Response.json({ok: true});
}
