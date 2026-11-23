// La consola pregunta qué hay: los aparatos con sus perillas, las cadenas de la galería, las fuentes, las sesiones y
// lo que ya salió. `?fresco=1` le vuelve a preguntar al motor (si se tocó un aparato).
import {leerCatalogo, listarFuentes, listarSalidas, listarSesiones} from '@/lib/consola';

export const dynamic = 'force-dynamic';

export async function GET(req: Request) {
  const fresco = new URL(req.url).searchParams.get('fresco') === '1';
  try {
    const catalogo = await leerCatalogo(fresco);
    return Response.json({...catalogo, fuentes: listarFuentes(), sesiones: listarSesiones(), salidas: listarSalidas()});
  } catch (e) {
    return new Response(`el motor no contestó: ${(e as Error).message}`, {status: 500});
  }
}
