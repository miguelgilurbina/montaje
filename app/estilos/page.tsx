import Link from 'next/link';
import Muestras from '@/components/Muestras';
import Veredicto from '@/components/Veredicto';
import {cuantasComparaciones, ESTADOS, FAMILIAS, leerEstilos, type Estilo} from '@/lib/estilos';

export const dynamic = 'force-dynamic';

type Filtros = {estado?: string; para?: string; material?: string; en?: string; familia?: string};

/** La URL de la galería con un filtro cambiado (el mismo valor otra vez lo quita). */
function con(f: Filtros, clave: keyof Filtros, valor: string): string {
  const q = new URLSearchParams();
  const nuevo = {...f, [clave]: f[clave] === valor ? undefined : valor};
  for (const [k, v] of Object.entries(nuevo)) if (v) q.set(k, v);
  const s = q.toString();
  return s ? `/estilos?${s}` : '/estilos';
}

function Tecnica({t}: {t: Record<string, unknown>}) {
  return <code className="tecnica">{JSON.stringify(t)}</code>;
}

/** Lo que dijo el probador de este estilo, en una línea. */
function EnElProbador({e}: {e: Estilo}) {
  const p = e.probador;
  if (e.falla) return <p className="dato probador error">probador: falló ({e.falla})</p>;
  if (!p) return e.noSePrueba ? <p className="dato probador">probador: no se prueba · {e.noSePrueba}</p> : null;
  const partes = [
    p.costo ? `dibujo ×${p.costo.toLocaleString('es')} del banco` : null,
    p.parecido === null ? 'referencia nueva' : p.cambio ? `CAMBIÓ contra su referencia (${Math.min(...p.parecido).toFixed(3)})` : 'igual a su referencia',
    e.elecciones ? `elegido ${e.elecciones.ganadas.toLocaleString('es')} de ${e.elecciones.jugadas}` : null,
  ].filter(Boolean);
  return (
    <p className={`dato probador${p.cambio ? ' error' : ''}`}>
      probador: {partes.join(' · ')}
      {e.estado !== 'rechazado' ? (
        <>
          {' · '}
          <Link href={`/estilos/comparar?a=${e.id}`}>comparar</Link>
        </>
      ) : null}
    </p>
  );
}

function Tarjeta({e}: {e: Estilo}) {
  return (
    <article className={`estilo estado-${e.estado.replace(' ', '-')}`} id={e.id}>
      <Muestras probador={e.probador?.url ?? null} video={e.video?.url ?? null} sin="sin muestra · se corta del próximo render que lo use, o con el probador" />
      <div className="cuerpo">
        <header>
          <h2>{e.nombre}</h2>
          <span className="sello">{e.estado}</span>
        </header>
        <p>{e.frase}</p>
        <p className="dato">
          {e.material} · energía {e.energia} · {e.dura}
          {e.video ? ` · muestra ${e.video.mb.toFixed(1)} MB` : ''}
        </p>
        <ul className="chips">
          {e.para.map((x) => (
            <li key={x}>{x}</li>
          ))}
        </ul>
        {e.miguel.length > 0 && (
          <div className="miguel">
            {e.miguel.map((c) => (
              <blockquote key={c}>«{c}»</blockquote>
            ))}
          </div>
        )}
        {e.tecnica.gesto === true && (
          <p className="dato">
            gesto: va encima de cualquier base (<code>--gesto {e.id}</code>); su muestra, sobre{' '}
            {typeof e.tecnica.sobre === 'string'
              ? e.tecnica.sobre
              : ((e.tecnica.sobre as {aparato: string}[] | undefined) ?? []).map((a) => a.aparato).join(' → ')}
          </p>
        )}
        {e.variantes && e.variantes.length > 0 && (
          <ul className="variantes">
            {e.variantes.map((v) => (
              <li key={v.id}>
                <span className="dato">variante</span> {v.nombre}: {v.diferencia} <span className="dato">· {v.estado}</span>
                {v.probador ? (
                  <>
                    {' · '}
                    <a href={v.probador}>su muestra</a>
                  </>
                ) : null}
              </li>
            ))}
          </ul>
        )}
        <EnElProbador e={e} />
        {e.evitar.length > 0 && (
          <ul className="evitar">
            {e.evitar.map((x) => (
              <li key={x}>{x}</li>
            ))}
          </ul>
        )}
        <Veredicto id={e.id} estado={e.estado} />
        <footer className="dato">
          <Tecnica t={e.tecnica} />
          <span>
            {' '}
            en{' '}
            {e.visto_en.map((p, i) => (
              <span key={p}>
                {i > 0 ? ', ' : ''}
                <Link href={`/p/${p}`}>{p}</Link>
              </span>
            ))}
          </span>
        </footer>
      </div>
    </article>
  );
}

export default async function Estilos({searchParams}: {searchParams: Promise<Filtros>}) {
  const f = await searchParams;
  // Las variantes van dentro de su principal: la galería muestra uno por grupo.
  const todos = leerEstilos().filter((e) => !e.variante_de);
  const variantes = todos.reduce((s, e) => s + (e.variantes?.length ?? 0), 0);
  const elegidos = todos.filter(
    (e) =>
      (!f.estado || e.estado === f.estado) &&
      (!f.para || e.para.includes(f.para)) &&
      (!f.material || e.material === f.material) &&
      (!f.en || e.visto_en.includes(f.en)) &&
      (!f.familia || e.familia === f.familia),
  );
  const contar = (pred: (e: Estilo) => boolean) => todos.filter(pred).length;
  const usos = [...new Set(todos.flatMap((e) => e.para))].sort((a, b) => a.localeCompare(b, 'es'));
  const materiales = [...new Set(todos.map((e) => e.material))].sort();
  // Los experimentos, del más nuevo al más viejo: el número va adelante.
  const experimentos = [...new Set(todos.flatMap((e) => e.visto_en))].sort((a, b) => b.localeCompare(a, 'es', {numeric: true}));
  const peso = todos.reduce((s, e) => s + (e.video?.mb ?? 0) + (e.probador?.mb ?? 0), 0);
  const probados = contar((e) => e.probador !== null);
  const elecciones = cuantasComparaciones();

  return (
    <div className="galeria">
      <nav className="migas">
        <Link href="/">montaje</Link> / estilos
      </nav>
      <h1>Estilos</h1>
      <p className="dato">
        Cada estilo es una receta con nombre para elegir según el guion: la técnica con sus valores, para qué sirve y lo que
        dijo Miguel. Los renders de los ejercicios se borran; la receta y la muestra quedan. El veredicto se da aquí mismo:
        sí, a medias o no, con o sin palabras. {todos.length} estilos (y {variantes} variantes dentro de ellos) · {probados} en el probador · muestras {peso.toFixed(1)} MB.
      </p>
      <p className="entrada-comparar">
        <Link href="/estilos/comparar">Elegir entre dos →</Link>{' '}
        <span className="dato">
          dos estilos de la misma familia, sincronizados en el probador · {elecciones} {elecciones === 1 ? 'elección' : 'elecciones'}
        </span>
      </p>

      <div className="filtros">
        <span className="dato">estado</span>
        {ESTADOS.filter((s) => contar((e) => e.estado === s) > 0).map((s) => (
          <Link key={s} href={con(f, 'estado', s)} className={f.estado === s ? 'activo' : ''}>
            {s} <span className="dato">{contar((e) => e.estado === s)}</span>
          </Link>
        ))}
      </div>
      <div className="filtros">
        <span className="dato">familia</span>
        {FAMILIAS.filter((x) => contar((e) => e.familia === x) > 0).map((x) => (
          <Link key={x} href={con(f, 'familia', x)} className={f.familia === x ? 'activo' : ''}>
            {x} <span className="dato">{contar((e) => e.familia === x)}</span>
          </Link>
        ))}
      </div>
      <div className="filtros">
        <span className="dato">para</span>
        {usos.map((x) => (
          <Link key={x} href={con(f, 'para', x)} className={f.para === x ? 'activo' : ''}>
            {x}
          </Link>
        ))}
      </div>
      <div className="filtros">
        <span className="dato">en</span>
        {experimentos.map((x) => (
          <Link key={x} href={con(f, 'en', x)} className={f.en === x ? 'activo' : ''}>
            {x} <span className="dato">{contar((e) => e.visto_en.includes(x))}</span>
          </Link>
        ))}
      </div>
      <div className="filtros">
        <span className="dato">material</span>
        {materiales.map((x) => (
          <Link key={x} href={con(f, 'material', x)} className={f.material === x ? 'activo' : ''}>
            {x}
          </Link>
        ))}
      </div>

      {elegidos.length === 0 ? (
        <p className="dato">Ningún estilo con esos filtros.</p>
      ) : (
        <div className="estilos">
          {elegidos.map((e) => (
            <Tarjeta key={e.id} e={e} />
          ))}
        </div>
      )}
    </div>
  );
}
