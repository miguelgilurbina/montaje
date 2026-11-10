/**
 * Capas hechas en código: no salen de ningún archivo, se dibujan cuadro a cuadro
 * y siguen a la canción (sus golpes y su energía las calcula Python y vienen en el
 * timeline). Todo es determinista: el mismo cuadro siempre sale igual, en el panel
 * y en el render.
 *
 * - `recuerdo`: grano de película, viñeta, calidez, parpadeo, el cuadro que tiembla
 *   como en un proyector y un halo en las luces. Encima de cualquier montaje.
 * - `fugas`: fugas de luz (manchas cálidas que entran por un borde y cruzan) en los
 *   «uno» de las frases.
 * - `polvo`: motas de luz que flotan y brillan en los golpes.
 * - `partitura`: la canción dibujada como un horizonte que respira (su espectro).
 * - `campo`: un fondo de color de la paleta que respira con la energía; sin material.
 *
 * Y tres filtros que no se dibujan encima sino que cambian lo que hay (el contenido
 * entero pasa por un filtro SVG; Montaje.tsx lo aplica con `filtroDe`):
 *
 * - `tinta`: dos tintas de la paleta, una para las sombras y otra para las luces.
 * - `calima`: el aire caliente sobre los médanos; la imagen ondula hacia arriba y se
 *   agita en los golpes.
 * - `tv`: el televisor viejo; colores corridos (más líneas de barrido, la franja de
 *   luz que baja y la pantalla redondeada, que sí van encima).
 */
import {useEffect, useState} from 'react';
import type {CSSProperties} from 'react';
import {AbsoluteFill, continueRender, delayRender, interpolate, random, staticFile} from 'remotion';
import type {Sintesis, Timeline} from './tipos';

type Recuerdo_ = Extract<Sintesis, {tipo: 'recuerdo'}>;
type Fugas_ = Extract<Sintesis, {tipo: 'fugas'}>;
type Polvo_ = Extract<Sintesis, {tipo: 'polvo'}>;
type Partitura_ = Extract<Sintesis, {tipo: 'partitura'}>;
type Campo_ = Extract<Sintesis, {tipo: 'campo'}>;
type Tinta_ = Extract<Sintesis, {tipo: 'tinta'}>;
type Calima_ = Extract<Sintesis, {tipo: 'calima'}>;
type Tv_ = Extract<Sintesis, {tipo: 'tv'}>;
type Titulo_ = Extract<Sintesis, {tipo: 'titulo'}>;
type Credito_ = Extract<Sintesis, {tipo: 'credito'}>;
type Cuenta_ = Extract<Sintesis, {tipo: 'cuenta'}>;
type Pelicula_ = Extract<Sintesis, {tipo: 'pelicula'}>;
type Onda_ = Extract<Sintesis, {tipo: 'onda'}>;
type Foco_ = Extract<Sintesis, {tipo: 'foco'}>;
type Golpe_ = Extract<Sintesis, {tipo: 'golpe'}>;
type Rotulos_ = Extract<Sintesis, {tipo: 'rotulos'}>;
type Luz_ = Extract<Sintesis, {tipo: 'luz'}>;
type Barras_ = Extract<Sintesis, {tipo: 'barras'}>;
type Rayas_ = Extract<Sintesis, {tipo: 'rayas'}>;

/** Cuadros desde el último golpe (o -1 si todavía no hubo). */
const desdeGolpe = (golpes: number[], frame: number) => {
  let ultimo = -1;
  for (const g of golpes) {
    if (g > frame) break;
    ultimo = g;
  }
  return ultimo < 0 ? -1 : frame - ultimo;
};

/**
 * Las tres voces del manual de marca, con las fuentes de Windows más cercanas
 * mientras las de la marca (Archivo Black, Lora) no estén instaladas: el cartel
 * condensado (y comprimido a 0,82, «la compresión es la identidad»), el oráculo en
 * itálica serif y el dato en mono.
 */
const VOCES: Record<string, CSSProperties> = {
  cartel: {fontFamily: '"Archivo Black", Bahnschrift, "Arial Narrow", sans-serif', fontWeight: 700, fontStretch: 'condensed', textTransform: 'uppercase', letterSpacing: '0.01em'},
  oraculo: {fontFamily: 'Lora, Georgia, serif', fontStyle: 'italic', fontWeight: 400},
  dato: {fontFamily: 'Consolas, "Courier New", monospace', fontWeight: 400, letterSpacing: '0.04em'},
};

const archivo = (tl: Timeline, ruta: string) => (tl.base ? tl.base + ruta : staticFile(ruta));
const fijo = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/** Envolvente de una capa: aparece y se va en `fundido` cuadros. */
const envolvente = (s: {ini: number; fin: number; fundido?: number}, frame: number) => {
  const f = Math.max(1, s.fundido ?? 15);
  return Math.min(interpolate(frame, [s.ini, s.ini + f], [0, 1], fijo), interpolate(frame, [s.fin - f, s.fin], [1, 0], fijo));
};

/** Una oscilación suave y determinista (suma de senos con fases de la semilla), en −1..1. */
const vaiven = (semilla: string, t: number, frecuencias: number[]) => {
  let v = 0;
  let peso = 0;
  frecuencias.forEach((f, i) => {
    const w = 1 / (i + 1);
    v += w * Math.sin(2 * Math.PI * (f * t + random(`${semilla}-${i}`)));
    peso += w;
  });
  return v / peso;
};

/** El temblor del proyector: cuánto se corre el cuadro entero (px). Montaje.tsx lo aplica al contenido. */
export function temblorDe(tl: Timeline, frame: number): string | undefined {
  const r = (tl.sintesis ?? []).find((s): s is Recuerdo_ => s.tipo === 'recuerdo' && frame >= s.ini && frame < s.fin);
  if (!r || !r.temblor) return undefined;
  const t = frame / tl.fps;
  const k = r.temblor * envolvente(r, frame);
  const x = k * (0.8 * vaiven(`tx${r.semilla}`, t, [0.31, 0.83]) + 0.2 * (random(`jx${frame}`) * 2 - 1));
  const y = k * (0.8 * vaiven(`ty${r.semilla}`, t, [0.27, 1.13]) + 0.2 * (random(`jy${frame}`) * 2 - 1));
  return `translate(${x.toFixed(2)}px, ${y.toFixed(2)}px) scale(${1 + (r.temblor / tl.alto) * 3})`;
}

export const CapaSintesis: React.FC<{tl: Timeline; s: Sintesis; frame: number}> = ({tl, s, frame}) => {
  if (frame < s.ini || frame >= s.fin) return null;
  if (s.tipo === 'recuerdo') return <Recuerdo tl={tl} s={s} frame={frame} />;
  if (s.tipo === 'fugas') return <Fugas tl={tl} s={s} frame={frame} />;
  if (s.tipo === 'polvo') return <Polvo tl={tl} s={s} frame={frame} />;
  if (s.tipo === 'partitura') return <Partitura tl={tl} s={s} frame={frame} />;
  if (s.tipo === 'campo') return <Campo tl={tl} s={s} frame={frame} />;
  if (s.tipo === 'tv') return <Tv tl={tl} s={s} frame={frame} />;
  if (s.tipo === 'titulo') return <Titulo tl={tl} s={s} frame={frame} />;
  if (s.tipo === 'credito') return <Credito tl={tl} s={s} frame={frame} />;
  if (s.tipo === 'cuenta') return <Cuenta tl={tl} s={s} frame={frame} />;
  if (s.tipo === 'pelicula') return <Pelicula tl={tl} s={s} frame={frame} />;
  if (s.tipo === 'rotulos') return <Rotulos tl={tl} s={s} frame={frame} />;
  if (s.tipo === 'barras') return <Barras tl={tl} s={s} frame={frame} />;
  if (s.tipo === 'rayas') return <Rayas tl={tl} s={s} frame={frame} />;
  return null;
};

// ── Letras ─────────────────────────────────────────────────────────────────

/** Cada letra aparece en su cuadro (subiendo un poco y enfocándose); todas se van juntas. */
const Titulo: React.FC<{tl: Timeline; s: Titulo_; frame: number}> = ({tl, s, frame}) => {
  // Al menos un cuadro: con `fundido: 0` el rango quedaba vacío y el render se caía.
  const salida = interpolate(frame, [s.fin - Math.max(1, s.fundido ?? 12), s.fin], [1, 0], fijo);
  const alto = s.tam * tl.alto;
  const comprimir = s.voz === 'cartel' ? 0.82 : 1;
  return (
    <AbsoluteFill style={{pointerEvents: 'none', opacity: salida}}>
      <div
        style={{
          position: 'absolute',
          left: s.alinear === 'centro' ? 0 : s.x * tl.ancho,
          width: s.alinear === 'centro' ? tl.ancho : undefined,
          top: s.y * tl.alto - alto / 2,
          textAlign: s.alinear === 'centro' ? 'center' : 'left',
          transform: `scaleX(${comprimir})`,
          transformOrigin: s.alinear === 'centro' ? '50% 50%' : '0 50%',
          whiteSpace: 'pre',
          fontSize: alto,
          lineHeight: 1,
          color: s.color,
          textShadow: `0 ${alto * 0.04}px ${alto * 0.18}px rgba(0,0,0,0.55)`,
          ...VOCES[s.voz],
        }}
      >
        {[...s.texto].map((letra, i) => {
          const u = interpolate(frame, [s.letras[i] ?? s.ini, (s.letras[i] ?? s.ini) + 6], [0, 1], fijo);
          return (
            <span
              key={i}
              style={{
                display: 'inline-block',
                opacity: u,
                transform: `translateY(${(1 - u) * alto * 0.12}px)`,
                filter: u < 1 ? `blur(${((1 - u) * alto * 0.05).toFixed(1)}px)` : undefined,
              }}
            >
              {letra === ' ' ? '\u00a0' : letra}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/** Sonando ahora: una raya de oro que crece y, detrás, el nombre en cartel y el dato en mono. */
const Credito: React.FC<{tl: Timeline; s: Credito_; frame: number}> = ({tl, s, frame}) => {
  const f = Math.max(1, s.fundido ?? 12);
  const entra = interpolate(frame, [s.ini, s.ini + 14], [0, 1], {...fijo, easing: (x) => 1 - Math.pow(1 - x, 3)});
  const sale = interpolate(frame, [s.fin - f, s.fin], [1, 0], fijo);
  const H = tl.alto;
  const margen = H * 0.07;
  return (
    <AbsoluteFill style={{pointerEvents: 'none', opacity: sale}}>
      <div style={{position: 'absolute', left: margen, bottom: margen, display: 'flex', alignItems: 'stretch', gap: H * 0.014}}>
        <div style={{width: H * 0.005, backgroundColor: s.color, transform: `scaleY(${entra})`, transformOrigin: '50% 100%'}} />
        <div style={{clipPath: `inset(0 ${(1 - entra) * 100}% 0 0)`}}>
          <div style={{...VOCES.dato, fontSize: H * 0.022, color: '#c6cfd9', marginBottom: H * 0.006}}>{s.lineas[1]}</div>
          <div style={{...VOCES.cartel, fontSize: H * 0.05, lineHeight: 1, color: s.color, transform: 'scaleX(0.82)', transformOrigin: '0 50%', whiteSpace: 'nowrap'}}>
            {s.lineas[0]}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/**
 * Las frases del guion: la que toca en este cuadro, con cada palabra subiendo a su
 * lugar en su golpe. Detrás, una mancha oscura y blanda para que se lea sobre lo que haya.
 */
const Rotulos: React.FC<{tl: Timeline; s: Rotulos_; frame: number}> = ({tl, s, frame}) => {
  const l = s.lineas.find((x) => frame >= x.ini && frame < x.fin);
  if (!l) return null;
  const sale = interpolate(frame, [l.fin - Math.max(1, s.fundido ?? 10), l.fin], [1, 0], fijo);
  // Del lado menor: en un vertical, la letra no crece con el alto y la frase sigue cabiendo.
  const alto = s.tam * Math.min(tl.ancho, tl.alto);
  const comprimir = s.voz === 'cartel' ? 0.84 : 1;
  const lugar = s.lugar === 'arriba' ? 'flex-start' : s.lugar === 'centro' ? 'center' : 'flex-end';
  return (
    <AbsoluteFill
      style={{pointerEvents: 'none', opacity: sale, display: 'flex', flexDirection: 'column', justifyContent: lugar, alignItems: 'center', padding: `${tl.alto * 0.075}px ${tl.ancho * 0.08}px`}}
    >
      <div style={{position: 'relative', maxWidth: '100%'}}>
        {s.sombra > 0 ? (
          <div
            style={{
              position: 'absolute',
              inset: `${-alto * 1.1}px ${-alto * 2.2}px`,
              background: `radial-gradient(ellipse 50% 50% at 50% 50%, rgba(7,9,13,${s.sombra}), rgba(7,9,13,0))`,
            }}
          />
        ) : null}
        <div
          style={{
            position: 'relative',
            textAlign: 'center',
            fontSize: alto,
            lineHeight: 1.22,
            color: s.color,
            textShadow: `0 ${(alto * 0.04).toFixed(1)}px ${(alto * 0.22).toFixed(1)}px rgba(0,0,0,0.6)`,
            transform: `scaleX(${comprimir})`,
            ...VOCES[s.voz],
          }}
        >
          {l.palabras.map(([texto, cuando], i) => {
            const u = interpolate(frame, [cuando, cuando + 6], [0, 1], {...fijo, easing: (x) => 1 - Math.pow(1 - x, 3)});
            return (
              <span key={i} style={{display: 'inline-block', opacity: u, transform: `translateY(${((1 - u) * alto * 0.22).toFixed(1)}px)`, margin: '0 0.14em'}}>
                {texto}
              </span>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── Película ───────────────────────────────────────────────────────────────

/** La cola de la película: un círculo, la cruz, el barrido que gira y el número; uno por golpe. */
const Cuenta: React.FC<{tl: Timeline; s: Cuenta_; frame: number}> = ({tl, s, frame}) => {
  const actual = [...s.numeros].reverse().find(([ini]) => frame >= ini);
  if (!actual) return null;
  const [ini, numero] = actual;
  const siguiente = s.numeros.find(([i]) => i > ini)?.[0] ?? s.fin;
  const u = (frame - ini) / Math.max(1, siguiente - ini);
  const H = tl.alto;
  const W = tl.ancho;
  const r = H * 0.36;
  const parpadeo = 0.92 + 0.08 * random(`cuenta-${s.semilla}-${frame}`);
  return (
    <AbsoluteFill style={{backgroundColor: '#1a1a18', pointerEvents: 'none', opacity: parpadeo}}>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
        <defs>
          <radialGradient id="cuenta-luz">
            <stop offset="0" stopColor="#9a968c" />
            <stop offset="1" stopColor="#4a4844" />
          </radialGradient>
        </defs>
        <rect width={W} height={H} fill="url(#cuenta-luz)" />
        {/* El barrido: un sector más oscuro que da la vuelta en el golpe. */}
        <path
          d={`M ${W / 2} ${H / 2} L ${W / 2} ${H / 2 - r * 3} A ${r * 3} ${r * 3} 0 ${u > 0.5 ? 1 : 0} 1 ${W / 2 + Math.sin(u * 2 * Math.PI) * r * 3} ${H / 2 - Math.cos(u * 2 * Math.PI) * r * 3} Z`}
          fill="rgba(0,0,0,0.28)"
        />
        <line x1={0} y1={H / 2} x2={W} y2={H / 2} stroke="#1c1b19" strokeWidth={H * 0.004} />
        <line x1={W / 2} y1={0} x2={W / 2} y2={H} stroke="#1c1b19" strokeWidth={H * 0.004} />
        <circle cx={W / 2} cy={H / 2} r={r} fill="none" stroke="#e8e4da" strokeWidth={H * 0.008} />
        <circle cx={W / 2} cy={H / 2} r={r * 0.86} fill="none" stroke="#e8e4da" strokeWidth={H * 0.004} />
        {/* Con números de caja alta: los de Georgia son de texto (el 3 y el 4 bajan de la línea, el 1 y el 2 no) y saltaban de altura.
            La línea de base va a media altura del dígito (0,716 de la letra en Arial), para que quede centrado en la cruz. */}
        <text x={W / 2} y={H / 2 + H * 0.48 * 0.358} textAnchor="middle" fontSize={H * 0.48} fontFamily="Arial, Helvetica, sans-serif" fill="#141412">
          {numero}
        </text>
      </svg>
    </AbsoluteFill>
  );
};

/** Las franjas del cine: entran desde arriba y desde abajo en `abre` cuadros y se van igual. */
const Barras: React.FC<{tl: Timeline; s: Barras_; frame: number}> = ({tl, s, frame}) => {
  const alto = Math.max(0, (tl.alto - tl.ancho / s.formato) / 2);
  if (alto <= 0) return null;
  const suave = (x: number) => x * x * (3 - 2 * x);
  const n = Math.max(1, s.abre);
  // Si la capa llega hasta el final del video, no se abren: el video termina en cine.
  const sale = s.fin >= tl.duracion ? 1 : interpolate(frame, [s.fin - n, s.fin], [1, 0], fijo);
  const u = suave(Math.min(interpolate(frame, [s.ini, s.ini + n], [0, 1], fijo), sale));
  const h = alto * u;
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div style={{position: 'absolute', left: 0, top: 0, width: '100%', height: h, backgroundColor: s.color}} />
      <div style={{position: 'absolute', left: 0, bottom: 0, width: '100%', height: h, backgroundColor: s.color}} />
    </AbsoluteFill>
  );
};

/**
 * La película gastada. Los rayones viven en «carriles»: cada carril decide, cada tantos
 * cuadros, si tiene un rayón y dónde; mientras dura, tiembla un poco. Las manchas duran
 * un cuadro. Todo sale de `random` con semilla: el mismo cuadro siempre se dibuja igual.
 */
const Rayas: React.FC<{tl: Timeline; s: Rayas_; frame: number}> = ({tl, s, frame}) => {
  const e = envolvente(s, frame);
  const W = tl.ancho;
  const H = tl.alto;
  const piezas: React.ReactNode[] = [];
  for (let k = 0; k < 7; k++) {
    const periodo = 10 + Math.floor(random(`raya-p-${s.semilla}-${k}`) * 44);
    const turno = Math.floor((frame + k * 7) / periodo);
    if (random(`raya-s-${s.semilla}-${k}-${turno}`) > s.rayones * 0.55) continue;
    const x = random(`raya-x-${s.semilla}-${k}-${turno}`) * W + (random(`raya-t-${s.semilla}-${k}-${frame}`) - 0.5) * 3;
    const clara = random(`raya-c-${s.semilla}-${k}-${turno}`) > 0.35;
    const fuerza = 0.12 + 0.3 * random(`raya-f-${s.semilla}-${k}-${frame}`);
    piezas.push(
      <div
        key={`r${k}`}
        style={{position: 'absolute', left: x, top: 0, width: 1 + Math.round(random(`raya-w-${s.semilla}-${k}-${turno}`) * 1.4), height: H, backgroundColor: clara ? '#f4ecd8' : '#0b0a09', opacity: fuerza}}
      />,
    );
  }
  const cuantas = Math.floor(random(`mancha-n-${s.semilla}-${frame}`) * (1 + s.manchas * 5));
  for (let k = 0; k < cuantas; k++) {
    const r = (0.002 + 0.008 * Math.pow(random(`mancha-r-${s.semilla}-${frame}-${k}`), 2)) * H;
    const clara = random(`mancha-c-${s.semilla}-${frame}-${k}`) > 0.6;
    piezas.push(
      <div
        key={`m${k}`}
        style={{
          position: 'absolute',
          left: random(`mancha-x-${s.semilla}-${frame}-${k}`) * W,
          top: random(`mancha-y-${s.semilla}-${frame}-${k}`) * H,
          width: r * 2 * (0.6 + random(`mancha-a-${s.semilla}-${frame}-${k}`)),
          height: r * 2,
          borderRadius: '50%',
          backgroundColor: clara ? '#f4ecd8' : '#0b0a09',
          opacity: 0.35 + 0.4 * random(`mancha-o-${s.semilla}-${frame}-${k}`),
          filter: `blur(${(r * 0.25).toFixed(1)}px)`,
        }}
      />,
    );
  }
  return <AbsoluteFill style={{pointerEvents: 'none', opacity: e}}>{piezas}</AbsoluteFill>;
};

/** Las bandas de la tira con sus perforaciones, corriendo hacia abajo. Montaje.tsx achica el contenido para que quepa. */
const Pelicula: React.FC<{tl: Timeline; s: Pelicula_; frame: number}> = ({tl, s, frame}) => {
  const e = envolvente(s, frame);
  const W = tl.ancho;
  const H = tl.alto;
  const banda = s.borde * W;
  const paso = H / 6;
  const corre = ((frame / tl.fps) * s.velocidad * paso) % paso;
  const agujeros = [];
  for (let k = -1; k < 8; k++) {
    const y = k * paso + corre;
    for (const x of [banda * 0.3, W - banda * 0.7]) {
      agujeros.push(
        <div key={`${k}-${x}`} style={{position: 'absolute', left: x, top: y + paso * 0.25, width: banda * 0.4, height: paso * 0.5, borderRadius: banda * 0.08, backgroundColor: '#d8d2c2', opacity: 0.85}} />,
      );
    }
  }
  return (
    <AbsoluteFill style={{pointerEvents: 'none', opacity: e}}>
      <div style={{position: 'absolute', left: 0, top: 0, width: banda, height: H, backgroundColor: '#0b0a09'}} />
      <div style={{position: 'absolute', right: 0, top: 0, width: banda, height: H, backgroundColor: '#0b0a09'}} />
      {agujeros}
    </AbsoluteFill>
  );
};

/** El empujón de zoom de este cuadro (1 = nada): sube en un golpe y vuelve en unos cuadros. */
export function golpeDeZoom(tl: Timeline, frame: number): number {
  const g = (tl.sintesis ?? []).find((s): s is Golpe_ => s.tipo === 'golpe' && frame >= s.ini && frame < s.fin);
  if (!g) return 1;
  const d = desdeGolpe(g.golpes, frame);
  return d < 0 ? 1 : 1 + g.fuerza * envolvente(g, frame) * Math.exp(-d / 5);
}

/** Cuánto achicar el contenido para que quepa entre las bandas de la película (1 = nada). */
export function escalaPelicula(tl: Timeline, frame: number): number {
  const p = (tl.sintesis ?? []).find((s): s is Pelicula_ => s.tipo === 'pelicula' && frame >= s.ini && frame < s.fin);
  return p ? 1 - 2 * p.borde * envolvente(p, frame) : 1;
}

// ── Filtros sobre el contenido ─────────────────────────────────────────────

const hex = (c: string): [number, number, number] => {
  const h = c.replace('#', '');
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16) / 255) as [number, number, number];
};

/**
 * Los filtros activos en este cuadro: la lista para `filter` del contenido y sus
 * definiciones SVG (que Montaje.tsx pone en la página). Sin filtros, nada.
 */
export function filtroDe(tl: Timeline, frame: number): {filtro?: string; defs: React.ReactNode} {
  const activos = (tl.sintesis ?? []).filter(
    (s): s is Tinta_ | Calima_ | Tv_ | Onda_ | Foco_ | Luz_ =>
      frame >= s.ini && frame < s.fin && ['tinta', 'calima', 'tv', 'onda', 'foco', 'luz'].includes(s.tipo),
  );
  if (!activos.length) return {defs: null};
  const orden: Record<string, number> = {foco: 0, onda: 1, calima: 2, luz: 3, tinta: 4, tv: 5};
  activos.sort((a, b) => orden[a.tipo] - orden[b.tipo]);
  const defs: React.ReactNode[] = [];
  const urls: string[] = [];
  activos.forEach((s, i) => {
    const id = `filtro-${s.tipo}-${i}`;
    const e = envolvente(s, frame);
    if (s.tipo === 'tinta') defs.push(<FiltroTinta key={id} id={id} s={s} e={e} />);
    if (s.tipo === 'calima') defs.push(<FiltroCalima key={id} id={id} s={s} e={e} tl={tl} frame={frame} />);
    if (s.tipo === 'tv') defs.push(<FiltroTv key={id} id={id} k={s.corrimiento * e} />);
    if (s.tipo === 'onda') defs.push(<FiltroOnda key={id} id={id} s={s} e={e} tl={tl} frame={frame} />);
    if (s.tipo === 'luz') {
      // La luz tampoco: brillo y saturación CSS, según la energía de ese cuadro y lo que falta desde el último golpe.
      const en = valor(s.energia, frame);
      const d = desdeGolpe(s.golpes, frame);
      const latido = d < 0 ? 0 : s.golpe * Math.exp(-d / 4);
      const brillo = 1 + (s.brillo[0] + (s.brillo[1] - s.brillo[0]) * en + latido - 1) * e;
      const color = 1 + (s.color[0] + (s.color[1] - s.color[0]) * en - 1) * e;
      urls.push(`brightness(${brillo.toFixed(3)}) saturate(${color.toFixed(3)})`);
      return;
    }
    if (s.tipo === 'foco') {
      // El foco no necesita SVG: un desenfoque CSS que se cierra en cada golpe.
      const d = desdeGolpe(s.golpes, frame);
      const abierto = d < 0 ? 1 : Math.min(1, d / 10);
      urls.push(`blur(${(s.fuerza * e * abierto).toFixed(2)}px)`);
      return;
    }
    urls.push(`url(#${id})`);
  });
  return {
    filtro: urls.join(' '),
    defs: (
      <svg width={0} height={0} style={{position: 'absolute'}}>
        <defs>{defs}</defs>
      </svg>
    ),
  };
}

/** Gris por luminancia → dos tintas (tabla de dos puntos) → mezcla con el original según `fuerza`. */
const FiltroTinta: React.FC<{id: string; s: Tinta_; e: number}> = ({id, s, e}) => {
  const [r1, g1, b1] = hex(s.oscuro);
  const [r2, g2, b2] = hex(s.claro);
  const k = s.fuerza * e;
  return (
    <filter id={id} colorInterpolationFilters="sRGB">
      <feColorMatrix type="matrix" values="0.2126 0.7152 0.0722 0 0  0.2126 0.7152 0.0722 0 0  0.2126 0.7152 0.0722 0 0  0 0 0 1 0" result="gris" />
      <feComponentTransfer in="gris" result="dos">
        <feFuncR type="table" tableValues={`${r1} ${r2}`} />
        <feFuncG type="table" tableValues={`${g1} ${g2}`} />
        <feFuncB type="table" tableValues={`${b1} ${b2}`} />
      </feComponentTransfer>
      <feComposite in="dos" in2="SourceGraphic" operator="arithmetic" k1={0} k2={k} k3={1 - k} k4={0} />
    </filter>
  );
};

/**
 * Turbulencia estirada a lo ancho (ondas horizontales) que sube con el tiempo y
 * desplaza la imagen. El ruido cubre tres alturas de cuadro para que al subir no se
 * acabe; el desplazamiento crece un momento en cada golpe.
 */
const FiltroCalima: React.FC<{id: string; s: Calima_; e: number; tl: Timeline; frame: number}> = ({id, s, e, tl, frame}) => {
  let ultimo = -1;
  for (const g of s.golpes) {
    if (g > frame) break;
    ultimo = g;
  }
  const empujon = ultimo >= 0 ? s.golpe * Math.exp(-(frame - ultimo) / 6) : 0;
  const sube = ((frame / tl.fps) * 0.06 * tl.alto) % tl.alto;
  return (
    <filter id={id} x="0" y="-100%" width="100%" height="300%" colorInterpolationFilters="sRGB">
      <feTurbulence type="turbulence" baseFrequency="0.0035 0.028" numOctaves={2} seed={s.semilla} result="ruido" />
      <feOffset in="ruido" dx={0} dy={-sube} result="sube" />
      <feDisplacementMap in="SourceGraphic" in2="sube" scale={(s.fuerza + empujon) * e} xChannelSelector="R" yChannelSelector="G" />
    </filter>
  );
};

/**
 * Un anillo de distorsión que se abre desde el centro: el mapa de desplazamiento es un
 * degradado radial que repite (anillos grises), cuyo radio crece desde el golpe; la
 * fuerza se apaga mientras se aleja.
 */
const FiltroOnda: React.FC<{id: string; s: Onda_; e: number; tl: Timeline; frame: number}> = ({id, s, e, tl, frame}) => {
  const d = desdeGolpe(s.golpes, frame);
  if (d < 0 || d > s.dura) return <filter id={id}><feOffset dx={0} dy={0} /></filter>;
  const u = d / s.dura;
  const W = tl.ancho;
  const H = tl.alto;
  const r = (0.05 + u * 0.8) * Math.hypot(W, H);
  // Un anillo: gris neutro y una ola senoidal (clara y después oscura) en el borde del
  // círculo; en escalones duros las líneas rectas se veían como un serrucho.
  const paradas = Array.from({length: 13}, (_, k) => {
    const o = 0.76 + (k / 12) * 0.24;
    const v = Math.round(128 + 80 * Math.sin((k / 12) * 2 * Math.PI) * Math.sin((k / 12) * Math.PI));
    return `<stop offset='${o.toFixed(3)}' stop-color='rgb(${v},${v},${v})'/>`;
  }).join('');
  const mapa = `<svg xmlns='http://www.w3.org/2000/svg' width='${W}' height='${H}'><defs><radialGradient id='g' gradientUnits='userSpaceOnUse' cx='${W / 2}' cy='${H / 2}' r='${r}'><stop offset='0' stop-color='rgb(128,128,128)'/>${paradas}</radialGradient></defs><rect width='100%' height='100%' fill='url(#g)'/></svg>`;
  return (
    <filter id={id} x="0" y="0" width="100%" height="100%" colorInterpolationFilters="sRGB">
      <feImage href={`data:image/svg+xml;utf8,${encodeURIComponent(mapa)}`} x={0} y={0} width={W} height={H} result="crudo" preserveAspectRatio="none" />
      <feGaussianBlur in="crudo" stdDeviation={H * 0.006} result="mapa" />
      <feDisplacementMap in="SourceGraphic" in2="mapa" scale={s.fuerza * (1 - u) * e} xChannelSelector="R" yChannelSelector="G" />
    </filter>
  );
};

/** El rojo a un lado y el azul al otro, sumados de vuelta: los colores corridos del tubo. */
const FiltroTv: React.FC<{id: string; k: number}> = ({id, k}) => (
  <filter id={id} colorInterpolationFilters="sRGB">
    <feColorMatrix in="SourceGraphic" type="matrix" values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" result="r" />
    <feOffset in="r" dx={k} dy={0} result="r2" />
    <feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0  0 1 0 0 0  0 0 0 0 0  0 0 0 1 0" result="g" />
    <feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0" result="b" />
    <feOffset in="b" dx={-k} dy={0} result="b2" />
    <feBlend in="r2" in2="g" mode="screen" result="rg" />
    <feBlend in="rg" in2="b2" mode="screen" />
  </filter>
);

/** Lo que va encima del televisor: líneas de barrido, la franja de luz que baja, el parpadeo y la pantalla redondeada. */
const Tv: React.FC<{tl: Timeline; s: Tv_; frame: number}> = ({tl, s, frame}) => {
  const e = envolvente(s, frame);
  const t = frame / tl.fps;
  const franja = ((t * 0.11 + random(`tvf${s.semilla}`)) % 1.4) - 0.2; // baja de arriba abajo cada ~13 s
  const radio = s.curva * tl.alto;
  return (
    <AbsoluteFill style={{pointerEvents: 'none', opacity: e}}>
      <AbsoluteFill
        style={{
          backgroundImage: `repeating-linear-gradient(to bottom, rgba(0,0,0,${s.lineas}) 0px, rgba(0,0,0,${s.lineas}) 1px, transparent 2px, transparent 3px)`,
        }}
      />
      <AbsoluteFill
        style={{
          background: `linear-gradient(to bottom, transparent ${(franja - 0.06) * 100}%, rgba(255,250,235,0.07) ${franja * 100}%, transparent ${(franja + 0.06) * 100}%)`,
          mixBlendMode: 'screen',
        }}
      />
      <AbsoluteFill style={{backgroundColor: '#000', opacity: 0.04 * random(`tvp${s.semilla}-${frame}`)}} />
      {/* La pantalla: esquinas redondeadas (lo de afuera, negro) y la orilla que se oscurece. */}
      <div
        style={{
          position: 'absolute',
          inset: tl.alto * 0.012,
          borderRadius: radio,
          boxShadow: `0 0 0 ${tl.alto}px #050608, inset 0 0 ${tl.alto * 0.09}px rgba(0,0,0,0.75)`,
        }}
      />
    </AbsoluteFill>
  );
};

// ── Recuerdo ───────────────────────────────────────────────────────────────

const Recuerdo: React.FC<{tl: Timeline; s: Recuerdo_; frame: number}> = ({tl, s, frame}) => {
  const e = envolvente(s, frame);
  const parpadeo = s.parpadeo * (0.5 + 0.5 * random(`parpadeo-${s.semilla}-${frame}`));
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {s.halo > 0 ? (
        // Las luces se abren un poco, como en la película: el mismo cuadro, desenfocado, sumado.
        <AbsoluteFill style={{backdropFilter: 'blur(10px) brightness(1.25)', mixBlendMode: 'screen', opacity: s.halo * e}} />
      ) : null}
      {s.calidez > 0 ? (
        <>
          <AbsoluteFill style={{backgroundColor: '#8f6a3a', mixBlendMode: 'color', opacity: 0.35 * s.calidez * e}} />
          <AbsoluteFill style={{backgroundColor: '#e6b43c', mixBlendMode: 'soft-light', opacity: s.calidez * e}} />
        </>
      ) : null}
      {s.grano > 0 ? <Grano tl={tl} fuerza={s.grano * e} semilla={s.semilla} frame={frame} /> : null}
      {s.vineta > 0 ? (
        <AbsoluteFill
          style={{background: `radial-gradient(ellipse at 50% 48%, transparent 52%, rgba(7,9,13,${(s.vineta * e).toFixed(3)}) 100%)`}}
        />
      ) : null}
      {s.parpadeo > 0 ? <AbsoluteFill style={{backgroundColor: '#07090d', opacity: parpadeo * e}} /> : null}
    </AbsoluteFill>
  );
};

/** Grano: ruido nuevo en cada cuadro, gris neutro (no cambia la luz media), en `overlay`. Se dibuja a la mitad y se agranda. */
const Grano: React.FC<{tl: Timeline; fuerza: number; semilla: number; frame: number}> = ({tl, fuerza, semilla, frame}) => {
  const id = `grano-${frame}`;
  const w = Math.round(tl.ancho / 2);
  const h = Math.round(tl.alto / 2);
  return (
    <AbsoluteFill style={{mixBlendMode: 'overlay', opacity: fuerza}}>
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" style={{width: '100%', height: '100%'}}>
        <filter id={id} x="0" y="0" width="100%" height="100%" colorInterpolationFilters="sRGB">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={(semilla * 7919 + frame) % 100000} stitchTiles="stitch" />
          <feColorMatrix type="matrix" values="0.33 0.33 0.33 0 0  0.33 0.33 0.33 0 0  0.33 0.33 0.33 0 0  0 0 0 0 1" />
          <feComponentTransfer>
            <feFuncR type="linear" slope="3" intercept="-1" />
            <feFuncG type="linear" slope="3" intercept="-1" />
            <feFuncB type="linear" slope="3" intercept="-1" />
          </feComponentTransfer>
        </filter>
        <rect width={w} height={h} filter={`url(#${id})`} />
      </svg>
    </AbsoluteFill>
  );
};

// ── Fugas de luz ───────────────────────────────────────────────────────────

const Fugas: React.FC<{tl: Timeline; s: Fugas_; frame: number}> = ({tl, s, frame}) => {
  const vivas = s.destellos.filter((d) => frame >= d.ini && frame < d.fin);
  return (
    <AbsoluteFill style={{mixBlendMode: 'screen', pointerEvents: 'none'}}>
      {vivas.map((d) => {
        const u = (frame - d.ini) / Math.max(1, d.fin - d.ini);
        // Entra rápido (un quinto de su vida) y se apaga despacio.
        const luz = u < 0.2 ? Math.sin((u / 0.2) * (Math.PI / 2)) : Math.pow(1 - (u - 0.2) / 0.8, 1.6);
        const x = (d.x + d.dx * u) * tl.ancho;
        const y = (d.y + d.dy * u) * tl.alto;
        const r = d.radio * tl.ancho;
        const estilo: CSSProperties = {
          position: 'absolute',
          left: x - r,
          top: y - r * 0.7,
          width: r * 2,
          height: r * 1.4,
          opacity: d.fuerza * luz,
          background: `radial-gradient(ellipse at center, ${d.color} 0%, ${d.color}aa 22%, ${d.color}33 50%, transparent 72%)`,
          transform: `rotate(${d.giro}deg)`,
          filter: 'blur(20px)',
        };
        return <div key={`${d.ini}-${d.x}`} style={estilo} />;
      })}
    </AbsoluteFill>
  );
};

// ── Polvo ──────────────────────────────────────────────────────────────────

const Polvo: React.FC<{tl: Timeline; s: Polvo_; frame: number}> = ({tl, s, frame}) => {
  const e = envolvente(s, frame);
  const t = frame / tl.fps;
  // El último golpe antes de este cuadro: las motas que le tocan brillan y se apagan.
  let ultimo = -1;
  for (let i = s.golpes.length - 1; i >= 0; i--) {
    if (s.golpes[i] <= frame) {
      ultimo = i;
      break;
    }
  }
  const motas = [];
  for (let i = 0; i < s.motas; i++) {
    const k = `${s.semilla}-${i}`;
    const cerca = random(`cerca-${k}`); // 0 lejos … 1 cerca: más grande, más rápida, más borrosa
    const tam = 1.2 + 4.5 * cerca * cerca;
    const sube = (0.004 + 0.018 * cerca) * tl.alto; // px por segundo, hacia arriba
    const x0 = random(`x-${k}`) * tl.ancho;
    const y0 = random(`y-${k}`) * tl.alto;
    const x = (((x0 + vaiven(`dx-${k}`, t, [0.05, 0.13]) * 0.04 * tl.ancho) % tl.ancho) + tl.ancho) % tl.ancho;
    const y = (((y0 - sube * t + vaiven(`dy-${k}`, t, [0.07, 0.17]) * 0.02 * tl.alto) % tl.alto) + tl.alto) % tl.alto;
    const base = 0.18 + 0.35 * random(`luz-${k}`);
    const toca = ultimo >= 0 && random(`golpe-${k}-${ultimo}`) < 0.35;
    const brillo = toca ? s.brillo * Math.exp(-(frame - s.golpes[ultimo]) / 7) : 0;
    const titila = 0.75 + 0.25 * vaiven(`tit-${k}`, t, [0.6 + random(`f-${k}`)]);
    motas.push(
      <div
        key={i}
        style={{
          position: 'absolute',
          left: x - tam,
          top: y - tam,
          width: tam * 2,
          height: tam * 2,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(243,234,212,1) 0%, rgba(230,180,60,0.55) 45%, transparent 72%)',
          opacity: Math.min(1, (base * titila + brillo) * e),
          filter: cerca > 0.75 ? `blur(${((cerca - 0.75) * 8).toFixed(1)}px)` : undefined,
        }}
      />,
    );
  }
  return <AbsoluteFill style={{mixBlendMode: 'screen', pointerEvents: 'none'}}>{motas}</AbsoluteFill>;
};

// ── Partitura ──────────────────────────────────────────────────────────────

type Espectro = {fps: number; bandas: number; valores: number[][]};
const espectros = new Map<string, Promise<Espectro>>();

function useEspectro(url: string): Espectro | null {
  const [datos, setDatos] = useState<Espectro | null>(null);
  const [espera] = useState(() => delayRender(`espectro ${url}`));
  useEffect(() => {
    if (!espectros.has(url)) espectros.set(url, fetch(url).then((r) => r.json() as Promise<Espectro>));
    espectros
      .get(url)!
      .then((d) => {
        setDatos(d);
        continueRender(espera);
      })
      .catch(() => continueRender(espera));
  }, [url, espera]);
  return datos;
}

/** La canción como un horizonte: los graves en el centro, los agudos hacia los bordes, en espejo. */
const Partitura: React.FC<{tl: Timeline; s: Partitura_; frame: number}> = ({tl, s, frame}) => {
  const datos = useEspectro(archivo(tl, s.espectro));
  if (!datos) return null;
  const e = envolvente(s, frame);
  const i = Math.min(datos.valores.length - 1, Math.max(0, Math.round((frame / tl.fps + s.desde) * datos.fps)));
  const v = datos.valores[i];
  const n = v.length;
  const W = tl.ancho;
  const y0 = s.y * tl.alto;
  const amp = s.alto * tl.alto;
  // Del centro hacia los bordes: banda 0 (grave) en el medio.
  const puntos: [number, number][] = [];
  const pasos = n * 2 - 1;
  for (let k = 0; k < pasos; k++) {
    const banda = Math.abs(k - (n - 1));
    const x = (k / (pasos - 1)) * W;
    const borde = Math.sin((k / (pasos - 1)) * Math.PI); // se apaga hacia los bordes del cuadro
    puntos.push([x, y0 - (v[banda] / 99) * amp * (0.25 + 0.75 * borde)]);
  }
  // Curva suave por los puntos (Catmull-Rom a Bézier).
  let d = `M ${puntos[0][0]} ${puntos[0][1]}`;
  for (let k = 0; k < puntos.length - 1; k++) {
    const p0 = puntos[Math.max(0, k - 1)];
    const p1 = puntos[k];
    const p2 = puntos[k + 1];
    const p3 = puntos[Math.min(puntos.length - 1, k + 2)];
    d += ` C ${p1[0] + (p2[0] - p0[0]) / 6} ${p1[1] + (p2[1] - p0[1]) / 6}, ${p2[0] - (p3[0] - p1[0]) / 6} ${p2[1] - (p3[1] - p1[1]) / 6}, ${p2[0]} ${p2[1]}`;
  }
  const relleno = `${d} L ${W} ${tl.alto} L 0 ${tl.alto} Z`;
  return (
    <AbsoluteFill style={{opacity: s.opacidad * e, pointerEvents: 'none'}}>
      <svg width={W} height={tl.alto} viewBox={`0 0 ${W} ${tl.alto}`}>
        <defs>
          <linearGradient id="partitura-relleno" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={s.color} stopOpacity={0.22} />
            <stop offset={Math.min(1, (amp * 1.2) / (tl.alto - y0 + amp))} stopColor={s.color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <path d={relleno} fill="url(#partitura-relleno)" />
        <path d={d} fill="none" stroke={s.color} strokeWidth={2.2} style={{filter: 'drop-shadow(0 0 6px rgba(230,180,60,0.7))'}} />
      </svg>
    </AbsoluteFill>
  );
};

// ── Campo de color ─────────────────────────────────────────────────────────

/** Manchas grandes de la paleta que derivan despacio y crecen con la energía; laten en los «uno». */
const Campo: React.FC<{tl: Timeline; s: Campo_; frame: number}> = ({tl, s, frame}) => {
  const e = envolvente(s, frame);
  const t = frame / tl.fps;
  const energia = valor(s.energia, frame);
  let latido = 0;
  for (const g of s.golpes) {
    if (g > frame) break;
    latido = Math.exp(-(frame - g) / 10);
  }
  const W = tl.ancho;
  const H = tl.alto;
  return (
    <AbsoluteFill style={{opacity: s.opacidad * e, mixBlendMode: s.mezcla as CSSProperties['mixBlendMode'], pointerEvents: 'none'}}>
      {s.colores.map((color, i) => {
        const k = `${s.semilla}-${i}`;
        const x = (0.5 + 0.42 * vaiven(`cx-${k}`, t, [0.021 + 0.01 * i, 0.047])) * W;
        const y = (0.5 + 0.38 * vaiven(`cy-${k}`, t, [0.017 + 0.008 * i, 0.039])) * H;
        const r = (0.32 + 0.22 * energia + 0.05 * latido) * Math.max(W, H) * (0.8 + 0.4 * random(`r-${k}`));
        return (
          <div
            key={color + i}
            style={{
              position: 'absolute',
              left: x - r,
              top: y - r,
              width: r * 2,
              height: r * 2,
              borderRadius: '50%',
              background: `radial-gradient(circle, ${color} 0%, ${color}99 30%, ${color}22 60%, transparent 72%)`,
              mixBlendMode: 'screen',
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

function valor(claves: [number, number][], g: number): number {
  if (!claves.length) return 0;
  if (g <= claves[0][0]) return claves[0][1];
  for (let i = 1; i < claves.length; i++) {
    if (claves[i][0] >= g) {
      const [a, va] = claves[i - 1];
      const [b, vb] = claves[i];
      return va + ((vb - va) * (g - a)) / Math.max(1, b - a);
    }
  }
  return claves[claves.length - 1][1];
}
