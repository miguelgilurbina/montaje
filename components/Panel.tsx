'use client';

import type {PlayerRef} from '@remotion/player';
import Link from 'next/link';
import {useCallback, useEffect, useRef, useState} from 'react';
import {formatear, iguales} from '@/lib/json';
import type {Proyecto, Resumen} from '@/lib/proyectos';
import Reproductor from './Reproductor';
import Tira from './Tira';

type Meta = {generado?: string; imagenes?: number};

/**
 * El panel: a la izquierda los experimentos; al centro el video (sin renderizar)
 * y la tira de la canción; a la derecha proyecto.json y los botones que corren
 * montaje.py. Lo que imprime cada comando sale en la consola de abajo.
 */
export default function Panel({proyectos, inicial}: {proyectos: Resumen[]; inicial: Proyecto}) {
  const [p, setP] = useState(inicial);
  const [texto, setTexto] = useState(() => formatear(inicial.cfg));
  const [errorJson, setErrorJson] = useState<string | null>(null);
  const [frame, setFrame] = useState(0);
  const [consola, setConsola] = useState('');
  const [ocupado, setOcupado] = useState<string | null>(null);
  const [desde, setDesde] = useState(0);
  const [hasta, setHasta] = useState(20);
  const [ultimoRender, setUltimoRender] = useState<string | null>(null);
  const playerRef = useRef<PlayerRef>(null);
  const consolaRef = useRef<HTMLPreElement>(null);
  const tl = p.timeline;

  // El reproductor avisa en qué cuadro va; la tira dibuja el cabezal ahí.
  useEffect(() => {
    const pl = playerRef.current;
    if (!pl) return;
    const alCuadro = (e: {detail: {frame: number}}) => setFrame(e.detail.frame);
    pl.addEventListener('frameupdate', alCuadro);
    return () => pl.removeEventListener('frameupdate', alCuadro);
  }, [tl]);

  useEffect(() => {
    const el = consolaRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [consola]);

  const recargar = useCallback(async () => {
    const r = await fetch(`/api/proyectos/${p.nombre}`, {cache: 'no-store'});
    const datos = (await r.json()) as Proyecto;
    setP(datos);
    setTexto(formatear(datos.cfg));
  }, [p.nombre]);

  const correr = useCallback(
    async (comando: string, opciones: Record<string, unknown> = {}) => {
      setOcupado(comando);
      let todo = `$ python montaje.py ${comando} ${p.nombre}\n`;
      setConsola(todo);
      const r = await fetch('/api/correr', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({nombre: p.nombre, comando, opciones}),
      });
      const lector = r.body!.getReader();
      const dec = new TextDecoder();
      for (;;) {
        const {done, value} = await lector.read();
        if (done) break;
        todo += dec.decode(value, {stream: true});
        setConsola(todo);
      }
      setOcupado(null);
      return todo;
    },
    [p.nombre],
  );

  const guardar = async (): Promise<boolean> => {
    let cfg: unknown;
    try {
      cfg = JSON.parse(texto);
      setErrorJson(null);
    } catch (e) {
      setErrorJson((e as Error).message);
      return false;
    }
    // Si no cambió nada, no se reescribe el archivo (y su formato queda como estaba).
    if (iguales(cfg, p.cfg)) return true;
    const r = await fetch(`/api/proyectos/${p.nombre}`, {method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(cfg)});
    if (!r.ok) setErrorJson(`no se pudo guardar (${r.status})`);
    return r.ok;
  };

  const planificar = async () => {
    if (!(await guardar())) return;
    await correr('planificar');
    await recargar();
  };

  const renderizar = async (preview: boolean) => {
    const salida = await correr('render', preview ? {preview: true, desde, hasta} : {});
    const m = /→ (.+\.mp4)/.exec(salida);
    if (m) setUltimoRender(m[1].trim().split(/[\\/]/).pop()!);
  };

  const segundos = tl ? frame / tl.fps : 0;
  const compas = p.musica ? p.musica.primeros_tiempos.filter((t) => t <= segundos + 1e-6).length - 1 : null;
  const meta = (tl?.meta ?? {}) as Meta;

  return (
    <div className="panel">
      <aside className="lateral">
        <Link href="/" className="marca">
          montaje
        </Link>
        <nav>
          {proyectos.map((x) => (
            <Link key={x.nombre} href={`/p/${x.nombre}`} className={x.nombre === p.nombre ? 'activo' : ''} title={x.titulo}>
              {x.nombre}
              {x.tieneTimeline ? null : <span className="dato"> · sin timeline</span>}
            </Link>
          ))}
        </nav>
      </aside>

      <main className="centro">
        <header>
          <h1>{String(p.cfg.titulo ?? p.nombre)}</h1>
          <div className="dato">
            {tl
              ? `${tl.ancho}×${tl.alto} · ${tl.fps} cps · ${(tl.duracion / tl.fps).toFixed(1)} s · ${meta.imagenes ?? '?'} imágenes · planificado ${meta.generado ?? '?'}`
              : 'sin timeline: edita proyecto.json y planifica para ver el video'}
          </div>
        </header>
        {tl ? (
          <>
            <Reproductor tl={tl} playerRef={playerRef} />
            <Tira musica={p.musica} tl={tl} frame={frame} onBuscar={(s) => playerRef.current?.seekTo(Math.round(s * tl.fps))} />
            <div className="dato tiempo">
              {segundos.toFixed(2)} s · cuadro {frame}
              {compas !== null && compas >= 0 ? ` · compás ${compas}` : ''}
              {p.musica ? '' : ' · sin análisis de música (corre «Analizar música»)'}
            </div>
          </>
        ) : (
          <div className="vacio">Sin timeline todavía.</div>
        )}
        <pre className="consola" ref={consolaRef}>
          {consola || 'Aquí sale lo que imprime cada comando.'}
        </pre>
        {ultimoRender ? (
          <div className="render">
            <div className="dato">último render: {ultimoRender}</div>
            <video controls src={`/medios/${p.nombre}/render/${ultimoRender}`} />
          </div>
        ) : null}
      </main>

      <aside className="derecha">
        <h2>proyecto.json</h2>
        <textarea value={texto} onChange={(e) => setTexto(e.target.value)} spellCheck={false} />
        {errorJson ? <div className="error">{errorJson}</div> : null}
        <div className="botones">
          <button className="fuerte" onClick={planificar} disabled={!!ocupado}>
            Planificar
          </button>
          <button onClick={() => correr('musica').then(recargar)} disabled={!!ocupado}>
            Analizar música
          </button>
          <button onClick={() => correr('catalogo').then(recargar)} disabled={!!ocupado}>
            Catálogo
          </button>
        </div>
        <h2>Render</h2>
        <div className="fila">
          <label>
            desde <input type="number" min={0} step={1} value={desde} onChange={(e) => setDesde(Number(e.target.value))} /> s
          </label>
          <label>
            hasta <input type="number" min={0} step={1} value={hasta} onChange={(e) => setHasta(Number(e.target.value))} /> s
          </label>
        </div>
        <div className="botones">
          <button onClick={() => renderizar(true)} disabled={!!ocupado || !tl}>
            Preview del tramo
          </button>
          <button onClick={() => renderizar(false)} disabled={!!ocupado || !tl}>
            Render final
          </button>
        </div>
        <h2>Después del render</h2>
        <div className="botones">
          <button onClick={() => correr('sonorizar')} disabled={!!ocupado}>
            Sonorizar
          </button>
          <button onClick={() => correr('senal')} disabled={!!ocupado}>
            Señal
          </button>
        </div>
        {ocupado ? <div className="dato ocupado">corriendo {ocupado}…</div> : null}
      </aside>
    </div>
  );
}
