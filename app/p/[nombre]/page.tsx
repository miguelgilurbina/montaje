import {notFound} from 'next/navigation';
import Panel from '@/components/Panel';
import {leerProyecto, listar} from '@/lib/proyectos';

export const dynamic = 'force-dynamic';

export default async function PaginaProyecto({params}: {params: Promise<{nombre: string}>}) {
  const {nombre} = await params;
  const p = leerProyecto(nombre);
  if (!p) notFound();
  return <Panel proyectos={listar()} inicial={p} />;
}
