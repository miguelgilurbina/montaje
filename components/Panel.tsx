'use client';

import type {PlayerRef} from '@remotion/player';
import Link from 'next/link';
import {useCallback, useEffect, useRef, useState} from 'react';
import {iguales, obtener, poner, type Cfg} from '@/lib/json';
import type {Biblioteca, Musica, Proyecto, Resumen} from '@/lib/proyectos';
import type {TipoMomento} from '@/lib/vocabulario';
import type {Timeline} from '@/src/tipos';
import Ficha from './Ficha';
import Formulario from './Formulario';
import Reproductor from './Reproductor';
import Tira, {type MomentoCfg, type SalvaCfg, type Seleccion} from './Tira';

type Meta = {generado?: string; imagenes?: number};
const ESPERA_MS = 600;

const nuevoMomento = (compas: number, tipo: TipoMomento, biblioteca: Biblioteca | null): MomentoCfg => {
  switch (tipo) {
    case 'destacado':
      return {compas, tipo, img: 'marca'};
    case 'rafaga':
      return {compas, tipo, por_compas: 8, de: 'marca'};
    case 'video':
      return {compas, tipo, src: biblioteca?.videos[0] ?? 'video/cortina.mp4', compases: 3, recorte: [280, 0, 720, 720], volumen: 0};
    default:
      return {compas, tipo};
  }
};

/**
 * El panel: a la izquierda los experimentos; al centro el video (sin renderizar),
 * la tira donde se ponen los momentos y la ficha del elegido; a la derecha las
 * decisiones de proyecto.json como formulario. Cada cambio replanifica solo.
 */
export default function Panel({proyectos, inicial}: {proyectos: Resumen[]; inicial: Proyecto}) {
  const nombre = inicial.nombre;
  const [cfg, setCfg] = useState<Cfg>(inicial.cfg);
  const [guardado, setGuardado] = useState<Cfg>(inicial.cfg);
  const [timeline, setTimeline] = useState<Timeline | null>(inicial.timeline);
  const [musica, setMusica] = useState<Musica | null>(inicial.musica);
  const [biblioteca, setBiblioteca] = useState<Biblioteca | null>(null);
  const [historial, setHistorial] = useState<Cfg[]>([]);
  const [sel, setSel] = useState<Seleccion>(null);
  const [enVivo, setEnVivo] = useState(true);
  const [frame, setFrame] = useState(0);
  const [consola, setConsola] = useState('');
  const [ocupado, setOcupado] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [desde, setDesde] = useState(0);
  const [hasta, setHasta] = useState(20);
  const [ultimoRender, setUltimoRender] = useState<string | null>(null);
  const playerRef = useRef<PlayerRef>(null);
  const consolaRef = useRef<HTMLPreElement>(null);
  const cfgRef = useRef(cfg);
  const guardadoRef = useRef(guardado);
  const corriendo = useRef(false);
  const pendiente = useRef(false);

  useEffect(() => {
    cfgRef.current = cfg;
  }, [cfg]);
  useEffect(() => {
    guardadoRef.current = guardado;
  }, [guardado]);

  const cargarBiblioteca = useCallback(async () => {
    const r = await fetch(`/api/biblioteca/${nombre}`, {cache: 'no-store'});
    if (r.ok) setBiblioteca((await r.json()) as Biblioteca);
  }, [nombre]);
  useEffect(() => {
    void cargarBiblioteca();
  }, [cargarBiblioteca]);

  // El reproductor avisa en qué cuadro va; la tira dibuja el cabezal ahí.
  useEffect(() => {
    const pl = playerRef.current;
    if (!pl) return;
    const alCuadro = (e: {detail: {frame: number}}) => setFrame(e.detail.frame);
    pl.addEventListener('frameupdate', alCuadro);
    return () => pl.removeEventListener('frameupdate', alCuadro);
  }, [timeline]);

  useEffect(() => {
    const el = consolaRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [consola]);

  const recargarTimeline = useCallback(async () => {
    const r = await fetch(`/api/proyectos/${nombre}`, {cache: 'no-store'});
    const datos = (await r.json()) as Proyecto;
    setTimeline(datos.timeline);
    setMusica(datos.musica);
  }, [nombre]);

  const correr = useCallback(
    async (comando: string, opciones: Record<string, unknown> = {}) => {
      setOcupado(comando);
      let todo = `$ python montaje.py ${comando} ${nombre}\n`;
      setConsola(todo);
      const r = await fetch('/api/correr', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({nombre, comando, opciones}),
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
      // Si el comando falló, lo que dijo (la línea «montaje: …») va al encabezado, no sólo a la consola.
      const fallo = /\[fin: código \d+\]/.test(todo);
      setError(fallo ? (todo.split('\n').find((l) => l.startsWith('montaje: ')) ?? `${comando} falló: mira la consola`).replace(/^montaje: /, '') : null);
      return todo;
    },
    [nombre],
  );

  /** Guarda proyecto.json si cambió y replanifica. Si ya está corriendo, encola una vuelta más. */
  const planificar = useCallback(async () => {
    if (corriendo.current) {
      pendiente.current = true;
      return;
    }
    corriendo.current = true;
    try {
      const actual = cfgRef.current;
      if (!iguales(actual, guardadoRef.current)) {
        const r = await fetch(`/api/proyectos/${nombre}`, {method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(actual)});
        if (!r.ok) {
          setConsola(`no se pudo guardar proyecto.json (${r.status})`);
          return;
        }
        setGuardado(actual);
        guardadoRef.current = actual;
      }
      await correr('planificar');
      await recargarTimeline();
    } finally {
      corriendo.current = false;
      if (pendiente.current) {
        pendiente.current = false;
        void planificar();
      }
    }
  }, [nombre, correr, recargarTimeline]);

  // En vivo: cada cambio replanifica, con una pausa corta para no correr por cada tecla.
  useEffect(() => {
    if (!enVivo || iguales(cfg, guardado)) return;
    const t = setTimeout(() => void planificar(), ESPERA_MS);
    return () => clearTimeout(t);
  }, [cfg, guardado, enVivo, planificar]);

  const cambiar = useCallback((nuevo: Cfg) => {
    setHistorial((h) => [...h.slice(-49), cfgRef.current]);
    setCfg(nuevo);
  }, []);

  const deshacer = useCallback(() => {
    setHistorial((h) => {
      if (!h.length) return h;
      setCfg(h[h.length - 1]);
      setSel(null);
      return h.slice(0, -1);
    });
  }, []);

  // ── Los momentos, por compás ──
  const modo = (obtener(cfg, ['montaje', 'modo']) as string) || 'collage';
  const momentos = (Array.isArray(cfg.momentos) ? cfg.momentos : []) as MomentoCfg[];
  const salvas = ((obtener(cfg, ['logo', 'salvapantallas']) as SalvaCfg[] | undefined) ?? []) as SalvaCfg[];
  const porCompas = <T extends {compas: number}>(lista: T[]) => [...lista].sort((a, b) => a.compas - b.compas);
  const guardarLista = (lista: Seleccion extends null ? never : 'momentos' | 'salvapantallas', items: (MomentoCfg | SalvaCfg)[]) =>
    lista === 'momentos' ? poner(cfg, ['momentos'], items.length ? items : undefined) : poner(cfg, ['logo', 'salvapantallas'], items.length ? items : undefined);
  const itemDe = (s: Seleccion) => (s ? (s.lista === 'momentos' ? momentos[s.i] : salvas[s.i]) : undefined);

  const agregar = (compas: number, tipo: TipoMomento) => {
    const lista = tipo === 'salvapantallas' ? 'salvapantallas' : 'momentos';
    const nuevo = tipo === 'salvapantallas' ? ({compas, compases: 2} as SalvaCfg) : nuevoMomento(compas, tipo, biblioteca);
    const items = porCompas([...(lista === 'momentos' ? momentos : salvas), nuevo]);
    cambiar(guardarLista(lista, items));
    setSel({lista, i: items.indexOf(nuevo)});
  };
  const mover = (s: Seleccion, compas: number) => {
    const item = itemDe(s);
    if (!s || !item || item.compas === compas) return;
    const movido = {...item, compas};
    const base = s.lista === 'momentos' ? momentos : salvas;
    const items = porCompas(base.map((x, i) => (i === s.i ? movido : x)));
    cambiar(guardarLista(s.lista, items));
    setSel({lista: s.lista, i: items.indexOf(movido)});
  };
  const borrar = (s: Seleccion) => {
    if (!s) return;
    const base = s.lista === 'momentos' ? momentos : salvas;
    cambiar(guardarLista(s.lista, base.filter((_, i) => i !== s.i)));
    setSel(null);
  };
  const cambiarItem = (s: Seleccion, item: MomentoCfg | SalvaCfg) => {
    if (!s) return;
    const base = s.lista === 'momentos' ? momentos : salvas;
    cambiar(guardarLista(s.lista, base.map((x, i) => (i === s.i ? item : x))));
  };

  // Teclas: Supr quita el momento elegido; Ctrl+Z deshace. No dentro de un campo de texto.
  useEffect(() => {
    const alTeclear = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement | null;
      if (t && /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)) return;
      if ((e.key === 'Delete' || e.key === 'Backspace') && sel) {
        e.preventDefault();
        borrar(sel);
      } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') {
        e.preventDefault();
        deshacer();
      }
    };
    window.addEventListener('keydown', alTeclear);
    return () => window.removeEventListener('keydown', alTeclear);
  });

  const renderizar = async (preview: boolean) => {
    const salida = await correr('render', preview ? {preview: true, desde, hasta} : {});
    const m = /→ (.+\.mp4)/.exec(salida);
    if (m) setUltimoRender(m[1].trim().split(/[\\/]/).pop()!);
  };

  const fps = timeline?.fps ?? Number(obtener(cfg, ['salida', 'fps']) ?? 30);
  const duracion = timeline ? timeline.duracion / timeline.fps : (musica?.duracion ?? 0);
  const segundos = frame / fps;
  const compas = musica ? musica.primeros_tiempos.filter((t) => t <= segundos + 1e-6).length - 1 : null;
  const meta = (timeline?.meta ?? {}) as Meta;
  const sinGuardar = !iguales(cfg, guardado);
  const item = itemDe(sel);

  return (
    <div className="panel">
      <aside className="lateral">
        <Link href="/" className="marca">
          montaje
        </Link>
        <nav>
          {proyectos.map((x) => (
            <Link key={x.nombre} href={`/p/${x.nombre}`} className={x.nombre === nombre ? 'activo' : ''} title={x.titulo}>
              {x.nombre}
              {x.tieneTimeline ? null : <span className="dato"> · sin timeline</span>}
            </Link>
          ))}
        </nav>
      </aside>

      <main className="centro">
        <header>
          <h1>{String(cfg.titulo ?? nombre)}</h1>
          <div className="dato">
            {timeline
              ? `${timeline.ancho}×${timeline.alto} · ${timeline.fps} cps · ${(timeline.duracion / timeline.fps).toFixed(1)} s · ${meta.imagenes ?? '?'} imágenes · planificado ${meta.generado ?? '?'}`
              : 'sin timeline: planifica para ver el video'}
            {ocupado ? <span className="chip ocupado"> {ocupado}…</span> : sinGuardar ? <span className="chip"> cambios sin planificar</span> : null}
            {error && !ocupado ? <span className="chip error"> {error}</span> : null}
          </div>
        </header>
        {timeline ? <Reproductor tl={timeline} playerRef={playerRef} /> : <div className="vacio">Sin timeline todavía.</div>}
        {duracion > 0 ? (
          <Tira
            musica={musica}
            duracion={duracion}
            fps={fps}
            frame={frame}
            momentos={modo === 'cinta' ? [] : momentos}
            salvapantallas={modo === 'cinta' ? [] : salvas}
            seleccion={sel}
            onBuscar={(s) => playerRef.current?.seekTo(Math.round(s * fps))}
            onSeleccionar={setSel}
            onAgregar={agregar}
            onMover={mover}
          />
        ) : null}
        <div className="dato tiempo">
          {segundos.toFixed(2)} s · cuadro {frame}
          {compas !== null && compas >= 0 ? ` · compás ${compas}` : ''}
          {modo === 'cinta' ? ' · en modo cinta los momentos van en «compases» (Avanzado)' : ' · clic en un compás vacío para poner un momento'}
        </div>
        {sel && item ? (
          <Ficha sel={sel} item={item} biblioteca={biblioteca} bibliotecaNombre={inicial.biblioteca} onCambiar={(it) => cambiarItem(sel, it)} onBorrar={() => borrar(sel)} />
        ) : null}
        <pre className="consola" ref={consolaRef}>
          {consola || 'Aquí sale lo que imprime cada comando.'}
        </pre>
        {ultimoRender ? (
          <div className="render">
            <div className="dato">último render: {ultimoRender}</div>
            <video controls src={`/medios/${nombre}/render/${ultimoRender}`} />
          </div>
        ) : null}
      </main>

      <aside className="derecha">
        <div className="botones">
          <label className="casilla">
            <input type="checkbox" checked={enVivo} onChange={(e) => setEnVivo(e.target.checked)} />
            <span>Planificar al cambiar</span>
          </label>
          <button className="fuerte" onClick={() => void planificar()} disabled={!!ocupado}>
            Planificar ahora
          </button>
          <button onClick={deshacer} disabled={!historial.length} title="Ctrl+Z">
            Deshacer{historial.length ? ` (${historial.length})` : ''}
          </button>
        </div>
        <Formulario cfg={cfg} onCambiar={cambiar} />
        <h2>Preparar</h2>
        <div className="botones">
          <button onClick={() => correr('catalogo').then(cargarBiblioteca)} disabled={!!ocupado}>
            Catálogo
          </button>
          <button onClick={() => correr('musica').then(recargarTimeline)} disabled={!!ocupado}>
            Analizar música
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
          <button onClick={() => renderizar(true)} disabled={!!ocupado || !timeline}>
            Preview del tramo
          </button>
          <button onClick={() => renderizar(false)} disabled={!!ocupado || !timeline}>
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
      </aside>
    </div>
  );
}
