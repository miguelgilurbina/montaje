import {guardarComparacion} from '@/lib/estilos';

export const dynamic = 'force-dynamic';

/** Cuál de dos estilos eligió Miguel en el probador. Cuerpo: `{a, b, gana}` (gana: a, b o «igual»). */
export async function POST(req: Request) {
  // Como el veredicto: que otra página abierta en el navegador no pueda mandar elecciones.
  const origen = req.headers.get('origin');
  if (origen && new URL(origen).host !== req.headers.get('host')) {
    return Response.json({error: 'se elige desde el panel'}, {status: 403});
  }
  const cuerpo = (await req.json().catch(() => null)) as {a?: string; b?: string; gana?: string} | null;
  if (!cuerpo?.a || !cuerpo.b || !cuerpo.gana) return Response.json({error: 'faltan a, b o gana'}, {status: 400});
  try {
    guardarComparacion(cuerpo.a, cuerpo.b, cuerpo.gana);
    return Response.json({ok: true});
  } catch (e) {
    return Response.json({error: e instanceof Error ? e.message : String(e)}, {status: 400});
  }
}
