import {ESTADOS, guardarVeredicto, type Estado} from '@/lib/estilos';

export const dynamic = 'force-dynamic';

/**
 * El veredicto de Miguel sobre un estilo, dado desde la galería: cambia `estado` en
 * estilos/<id>.json, anota cuándo y, si escribió algo, guarda sus palabras en `miguel`
 * y en direccion/REGISTRO.md. Cuerpo: `{estado, cita?}`.
 */
export async function POST(req: Request, {params}: {params: Promise<{id: string}>}) {
  // El panel escucha sólo en este computador; igual, que otra página abierta en el
  // navegador no pueda mandar veredictos: el pedido tiene que venir del panel mismo.
  const origen = req.headers.get('origin');
  if (origen && new URL(origen).host !== req.headers.get('host')) {
    return Response.json({error: 'el veredicto se da desde el panel'}, {status: 403});
  }
  const {id} = await params;
  const cuerpo = (await req.json().catch(() => null)) as {estado?: string; cita?: string} | null;
  const estado = cuerpo?.estado as Estado | undefined;
  if (!estado || !ESTADOS.includes(estado)) {
    return Response.json({error: `estado inválido (hay: ${ESTADOS.join(', ')})`}, {status: 400});
  }
  try {
    const guardado = guardarVeredicto(id, estado, typeof cuerpo?.cita === 'string' ? cuerpo.cita : '');
    if (!guardado) return Response.json({error: `no existe el estilo ${id}`}, {status: 404});
    return Response.json({ok: true, estado: guardado.estado, miguel: guardado.miguel});
  } catch (e) {
    return Response.json({error: e instanceof Error ? e.message : String(e)}, {status: 500});
  }
}
