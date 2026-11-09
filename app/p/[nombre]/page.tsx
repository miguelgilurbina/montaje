import {notFound} from 'next/navigation';
import Panel from '@/components/Panel';
import {leerProyecto, listar} from '@/lib/proyectos';

export const dynamic = 'force-dynamic';

export default async function PaginaProyecto({
  params,
  searchParams,
}: {
  params: Promise<{nombre: string}>;
  searchParams: Promise<{v?: string}>;
}) {
  const {nombre} = await params;
  const {v} = await searchParams;
  const p = leerProyecto(nombre, v);
  if (!p) notFound();
  return <Panel key={v ?? ''} proyectos={listar()} inicial={p} version={v ?? null} />;
}
