import Link from 'next/link';
import Comparador, {type Lado} from '@/components/Comparador';
import {cuantasComparaciones, FAMILIAS, leerEstilos, type Estilo, type Familia} from '@/lib/estilos';

export const dynamic = 'force-dynamic';

type Pedido = {a?: string; b?: string; familia?: string};

function lado(e: Estilo): Lado {
  return {id: e.id, nombre: e.nombre, estado: e.estado, frase: e.frase, url: e.probador!.url, costo: e.probador!.costo};
}

/** De una familia, primero el que menos se ha comparado; al lado, otro de la misma familia (al azar entre los menos vistos). */
function par(candidatos: Estilo[], fijo?: Estilo): [Estilo, Estilo] | null {
  const vistas = (e: Estilo) => e.elecciones?.jugadas ?? 0;
  const mezcla = [...candidatos].sort(() => Math.random() - 0.5).sort((x, y) => vistas(x) - vistas(y));
  const a = fijo ?? mezcla[0];
  const otros = mezcla.filter((e) => e.id !== a?.id);
  if (!a || otros.length === 0) return null;
  return [a, otros[Math.floor(Math.random() * Math.min(3, otros.length))]];
}

export default async function Comparar({searchParams}: {searchParams: Promise<Pedido>}) {
  const pedido = await searchParams;
  // Se compara lo que se puede usar: lo rechazado ya tiene su no.
  const probados = leerEstilos().filter((e) => e.probador && e.estado !== 'rechazado');
  const porId = new Map(probados.map((e) => [e.id, e]));
  const conPar = FAMILIAS.filter((f) => probados.filter((e) => e.familia === f).length >= 2);
  const fijo = pedido.a ? porId.get(pedido.a) : undefined;
  const familia: Familia | undefined =
    fijo?.familia ?? (conPar.includes(pedido.familia as Familia) ? (pedido.familia as Familia) : conPar[Math.floor(Math.random() * conPar.length)]);
  let elegidos: [Estilo, Estilo] | null = null;
  if (fijo && pedido.b && porId.get(pedido.b)) elegidos = [fijo, porId.get(pedido.b)!];
  else if (familia) elegidos = par(probados.filter((e) => e.familia === familia), fijo);
  const total = cuantasComparaciones();

  return (
    <div className="galeria">
      <nav className="migas">
        <Link href="/">montaje</Link> / <Link href="/estilos">estilos</Link> / elegir entre dos
      </nav>
      <h1>Elegir entre dos</h1>
      <p className="dato">
        Dos estilos de la misma familia en el probador: los mismos clips y el mismo trozo de canción, sincronizados. Lo
        único distinto es el estilo. Elige uno y viene otro par; de muchas elecciones sale un orden que el guion usa para
        desempatar entre lo aprobado. {total} {total === 1 ? 'elección' : 'elecciones'} hasta ahora.
      </p>
      <div className="filtros">
        <span className="dato">familia</span>
        {conPar.map((f) => (
          <Link key={f} href={`/estilos/comparar?familia=${encodeURIComponent(f)}`} className={f === familia ? 'activo' : ''}>
            {f}
          </Link>
        ))}
      </div>
      {elegidos ? (
        <Comparador
          key={`${elegidos[0].id}-${elegidos[1].id}`}
          a={lado(elegidos[0])}
          b={lado(elegidos[1])}
          siguiente={`/estilos/comparar?familia=${encodeURIComponent(familia ?? '')}`}
        />
      ) : (
        <p className="dato">
          Todavía no hay dos estilos de esta familia con muestra del probador. Se hacen con{' '}
          <code>python montaje.py probar --todos</code>.
        </p>
      )}
    </div>
  );
}
