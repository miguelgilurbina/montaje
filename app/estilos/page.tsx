import Link from 'next/link';
import {ESTADOS, leerEstilos, type Estilo} from '@/lib/estilos';

export const dynamic = 'force-dynamic';

type Filtros = {estado?: string; para?: string; material?: string};

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

function Tarjeta({e}: {e: Estilo}) {
  return (
    <article className={`estilo estado-${e.estado.replace(' ', '-')}`} id={e.id}>
      {/* `#t=0.5`: con preload="metadata" el navegador muestra ese cuadro en vez de negro. */}
      <div className="muestra">
        {e.video ? (
          <video src={`${e.video.url}#t=0.5`} controls loop playsInline preload="metadata" />
        ) : (
          <p className="dato">sin muestra · se corta del próximo render que lo use</p>
        )}
      </div>
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
        {e.evitar.length > 0 && (
          <ul className="evitar">
            {e.evitar.map((x) => (
              <li key={x}>{x}</li>
            ))}
          </ul>
        )}
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
  const todos = leerEstilos();
  const elegidos = todos.filter(
    (e) => (!f.estado || e.estado === f.estado) && (!f.para || e.para.includes(f.para)) && (!f.material || e.material === f.material),
  );
  const contar = (pred: (e: Estilo) => boolean) => todos.filter(pred).length;
  const usos = [...new Set(todos.flatMap((e) => e.para))].sort((a, b) => a.localeCompare(b, 'es'));
  const materiales = [...new Set(todos.map((e) => e.material))].sort();
  const peso = todos.reduce((s, e) => s + (e.video?.mb ?? 0), 0);

  return (
    <div className="galeria">
      <nav className="migas">
        <Link href="/">montaje</Link> / estilos
      </nav>
      <h1>Estilos</h1>
      <p className="dato">
        Cada estilo es una receta con nombre para elegir según el guion: la técnica con sus valores, para qué sirve y lo que
        dijo Miguel. Los renders de los ejercicios se borran; la receta y la muestra quedan. {todos.length} estilos ·
        muestras {peso.toFixed(1)} MB.
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
        <span className="dato">para</span>
        {usos.map((x) => (
          <Link key={x} href={con(f, 'para', x)} className={f.para === x ? 'activo' : ''}>
            {x}
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
