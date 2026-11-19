import Link from 'next/link';
import Letreros from '@/components/Letreros';
import {ESTADOS} from '@/lib/estilos';
import {FAMILIAS_TEXTO, leerTextos, type FamiliaTexto} from '@/lib/textos';
import registro from '@/fuentes/fuentes.json';

// El registro directo del JSON: src/fuentes.ts trae los ganchos de React que cargan las letras, y ésta es una página del servidor.
const FAMILIAS = registro.familias as Record<string, {voz: string; licencia: string}>;

export const dynamic = 'force-dynamic';

type Filtros = {estado?: string; familia?: string; fuente?: string};

/** La URL de la galería con un filtro cambiado (el mismo valor otra vez lo quita). */
function con(f: Filtros, clave: keyof Filtros, valor: string): string {
  const q = new URLSearchParams();
  const nuevo = {...f, [clave]: f[clave] === valor ? undefined : valor};
  for (const [k, v] of Object.entries(nuevo)) if (v) q.set(k, v);
  const s = q.toString();
  return s ? `/textos?${s}` : '/textos';
}

export default async function Textos({searchParams}: {searchParams: Promise<Filtros>}) {
  const f = await searchParams;
  const todos = leerTextos();
  const usa = (fuente: string) => (l: (typeof todos)[number]) => l.estilo.fuente === fuente || l.estilo.secundario?.fuente === fuente;
  const elegidos = todos.filter(
    (l) => (!f.estado || l.estado === f.estado) && (!f.familia || l.familia === f.familia) && (!f.fuente || usa(f.fuente)(l)),
  );
  const contar = (pred: (l: (typeof todos)[number]) => boolean) => todos.filter(pred).length;
  const familias = Object.entries(FAMILIAS_TEXTO) as [FamiliaTexto, string][];

  return (
    <div className="galeria">
      <nav className="migas">
        <Link href="/">montaje</Link> / textos
      </nav>
      <h1>Textos</h1>
      <p className="dato">
        Letreros con nombre para títulos, frases, rótulos, subtítulos y créditos: cada uno con su tipografía, su forma, su lugar y
        cómo entra. Se dibujan en vivo con el mismo componente que los pone en el video, así que no hay muestras guardadas. En{' '}
        <code>planos</code>, un texto los usa por su nombre, <code>&quot;letrero&quot;: &quot;oraculo&quot;</code>. Las {Object.keys(FAMILIAS).length}{' '}
        tipografías son libres y viven en el repo (<code>fuentes/</code>). {todos.length} letreros.
      </p>

      <div className="filtros">
        <span className="dato">estado</span>
        {ESTADOS.filter((s) => contar((l) => l.estado === s) > 0).map((s) => (
          <Link key={s} href={con(f, 'estado', s)} className={f.estado === s ? 'activo' : ''}>
            {s} <span className="dato">{contar((l) => l.estado === s)}</span>
          </Link>
        ))}
      </div>
      <div className="filtros">
        <span className="dato">familia</span>
        {familias.map(([clave, nombre]) => (
          <Link key={clave} href={con(f, 'familia', clave)} className={f.familia === clave ? 'activo' : ''}>
            {nombre} <span className="dato">{contar((l) => l.familia === clave)}</span>
          </Link>
        ))}
      </div>
      <div className="filtros">
        <span className="dato">letra</span>
        {Object.keys(FAMILIAS).map((x) => (
          <Link key={x} href={con(f, 'fuente', x)} className={f.fuente === x ? 'activo' : ''} title={FAMILIAS[x].voz}>
            {x} <span className="dato">{contar(usa(x))}</span>
          </Link>
        ))}
      </div>

      {elegidos.length === 0 ? <p className="dato">Ningún letrero con esos filtros.</p> : <Letreros letreros={elegidos} familias={familias} />}
    </div>
  );
}
