import {leerBiblioteca, nombreValido} from '@/lib/proyectos';

export const dynamic = 'force-dynamic';

export async function GET(_req: Request, {params}: {params: Promise<{nombre: string}>}) {
  const {nombre} = await params;
  if (!nombreValido(nombre)) return Response.json({error: 'nombre inválido'}, {status: 400});
  return Response.json(leerBiblioteca(nombre));
}
