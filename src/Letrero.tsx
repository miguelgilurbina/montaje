import type {CSSProperties, ReactNode} from 'react';
import {AbsoluteFill, Easing, interpolate, random, useCurrentFrame, useVideoConfig} from 'remotion';
import {cssFamilia, useFuentes} from './fuentes';
import type {EstiloTexto, LetraLetrero, LugarLetrero} from './tipos';

/**
 * Un texto de la galería de textos (textos/<id>.json) dibujado en pantalla: la letra, su contorno,
 * sombra, caja o resaltado, el lugar y cómo entra y sale. Lo usan el modo planos (`letrero` en un
 * texto, y `subtitulos.letrero` para los subtítulos) y la galería del panel (/textos), que lo muestra
 * en vivo con este mismo componente.
 *
 * Los tamaños van en fracción del alto del cuadro y los espacios en em: el mismo estilo se ve igual en
 * 16:9, 9:16 o 1:1.
 *
 * Texto en movimiento (2026-11-19): la ventana (la imagen de abajo dentro de las letras), atravesar
 * una letra al salir, el karaoke de la voz, el latido con el golpe, las letras que se arman o llegan en
 * ola y el cursor de la máquina.
 */

const fijo = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const suave = Easing.out(Easing.cubic);

/** El margen seguro: lo que queda libre en los bordes, en fracción del cuadro. */
const MARGEN = {x: 0.07, y: 0.08};

function letra(l: LetraLetrero, H: number): CSSProperties {
  return {
    fontFamily: cssFamilia(l.fuente),
    fontWeight: l.peso ?? 400,
    fontStyle: l.cursiva ? 'italic' : 'normal',
    fontSize: l.tamano * H,
    lineHeight: l.interlineado ?? 1.12,
    letterSpacing: `${l.espaciado ?? 0}em`,
    textTransform: l.mayusculas ? 'uppercase' : 'none',
    color: l.color,
    ...(l.variacion ? {fontVariationSettings: Object.entries(l.variacion).map(([k, v]) => `'${k}' ${v}`).join(', ')} : {}),
  };
}

/** Dónde va el bloque: alineado en el cuadro y con su margen seguro. */
function caja(lugar: LugarLetrero, W: number, H: number): CSSProperties {
  const px = MARGEN.x * W;
  const py = MARGEN.y * H;
  const pos: Record<LugarLetrero, [CSSProperties['justifyContent'], CSSProperties['alignItems']]> = {
    centro: ['center', 'center'],
    arriba: ['flex-start', 'center'],
    abajo: ['flex-end', 'center'],
    'tercio-inferior': ['flex-end', 'flex-start'],
    'arriba-izquierda': ['flex-start', 'flex-start'],
    'abajo-izquierda': ['flex-end', 'flex-start'],
    'abajo-derecha': ['flex-end', 'flex-end'],
  };
  const [vertical, horizontal] = pos[lugar] ?? pos.centro;
  return {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: vertical,
    alignItems: horizontal,
    padding: `${py}px ${px}px`,
    // El tercio inferior sube un poco más: es donde van los nombres en un documental.
    ...(lugar === 'tercio-inferior' ? {paddingBottom: H * 0.16} : {}),
  };
}

/** Cada fila del texto con su caja o su resaltado (el fondo se repite fila por fila, no como un bloque). */
function conFondo(e: EstiloTexto, hijos: ReactNode): ReactNode {
  if (e.caja?.bloque) {
    // Un solo papel detrás de todo el texto (fila por fila, con relleno grande, una fila tapa a la otra).
    const r = e.caja.relleno;
    return (
      <span style={{display: 'inline-block', background: e.caja.color, padding: `${r * 0.7}em ${r}em`, borderRadius: `${e.caja.radio ?? 0}em`}}>
        {hijos}
      </span>
    );
  }
  if (e.caja) {
    const r = e.caja.relleno;
    return (
      <span
        style={{
          background: e.caja.color,
          padding: `${r * 0.55}em ${r}em`,
          borderRadius: `${e.caja.radio ?? 0}em`,
          boxDecorationBreak: 'clone',
          WebkitBoxDecorationBreak: 'clone',
        }}
      >
        {hijos}
      </span>
    );
  }
  if (e.resaltado) {
    const c = e.resaltado.color;
    return (
      <span
        style={{
          backgroundImage: `linear-gradient(transparent 52%, ${c} 52%, ${c} 90%, transparent 90%)`,
          padding: '0 0.12em',
          boxDecorationBreak: 'clone',
          WebkitBoxDecorationBreak: 'clone',
        }}
      >
        {hijos}
      </span>
    );
  }
  return hijos;
}

/** Contorno y sombra de la letra. El borde va detrás del relleno: el ancho pedido queda afuera, entero. */
function trazo(e: EstiloTexto, H: number): CSSProperties {
  const fs = e.tamano * H;
  return {
    ...(e.contorno ? {WebkitTextStroke: `${2 * e.contorno.ancho * fs}px ${e.contorno.color}`, paintOrder: 'stroke fill'} : {}),
    ...(e.sombra ? {textShadow: `0 ${(e.sombra.y ?? 0) * fs}px ${e.sombra.desenfoque * fs}px ${e.sombra.color}`} : {}),
  };
}

/**
 * Cuándo se dice cada una de las `n` palabras, en cuadros desde el comienzo del letrero: las de la voz si
 * vienen (si la corrección del subtítulo cambió cuántas son, se reparten en proporción); si no, parejo
 * entre `desde` y `hasta`.
 */
export function tiemposPalabras(n: number, palabras: [number, number][] | undefined, desde: number, hasta: number): [number, number][] {
  if (palabras?.length === n) return palabras;
  if (palabras?.length) {
    const a = palabras[0][0];
    const b = palabras[palabras.length - 1][1];
    return Array.from({length: n}, (_, k) => [a + ((b - a) * k) / n, a + ((b - a) * (k + 1)) / n]);
  }
  const paso = (hasta - desde) / Math.max(1, n);
  return Array.from({length: n}, (_, k) => [desde + k * paso, desde + (k + 1) * paso]);
}

type Revelar = {
  tipo?: string;
  /** Avance de la entrada: suavizado (`u`) y parejo (`p`). */
  u: number;
  p: number;
  f: number;
  fps: number;
  semilla: string;
  karaoke?: EstiloTexto['karaoke'];
  /** Los tiempos de cada palabra (cuadros desde el comienzo), ya resueltos. */
  tiempos?: [number, number][];
  cursor?: boolean;
  color: string;
};

/** El texto según la entrada: letra a letra, palabra a palabra o letras que se arman se dibujan enteras y se destapan (el bloque no salta). */
function revelado(texto: string, r: Revelar): ReactNode {
  if (r.tipo === 'maquina') {
    const n = Math.floor(r.u * texto.length + 1e-6);
    // El cursor no ocupa lugar (va en una caja sin ancho): el texto no se corre mientras escribe. Parpadea al terminar.
    const parpadea = r.p >= 1 && Math.floor(r.f / (r.fps * 0.5)) % 2 === 1;
    return (
      <>
        {texto.slice(0, n)}
        {r.cursor ? (
          <span style={{position: 'relative'}}>
            <span style={{position: 'absolute', left: '0.04em', opacity: parpadea ? 0 : 1}}>▍</span>
          </span>
        ) : null}
        <span style={{opacity: 0}}>{texto.slice(n)}</span>
      </>
    );
  }
  const partes = texto.split(/(\s+)/);
  const palabras = partes.filter((x) => x.trim()).length;
  if (r.tipo === 'armar' || r.tipo === 'ola') {
    const letras = partes.reduce((s, x) => s + (x.trim() ? [...x].length : 0), 0);
    let c = -1;
    return partes.map((x, i) => {
      if (!x.trim()) return x;
      // La palabra no se corta entre filas; dentro, cada letra entra en su turno.
      return (
        <span key={i} style={{whiteSpace: 'nowrap'}}>
          {[...x].map((ch, j) => {
            c += 1;
            const turno = (c / Math.max(1, letras)) * 0.6;
            const v = suave(interpolate(r.p, [turno, turno + 0.4], [0, 1], fijo));
            let transform: string;
            if (r.tipo === 'armar') {
              // Desde un lugar al azar (el mismo en cada cuadro: la semilla es el letrero y la letra), girada y chica.
              const dx = (random(`${r.semilla}-${c}-x`) - 0.5) * 2.6;
              const dy = (random(`${r.semilla}-${c}-y`) - 0.5) * 1.8;
              const giro = (random(`${r.semilla}-${c}-g`) - 0.5) * 80;
              transform = `translate(${(dx * (1 - v)).toFixed(3)}em, ${(dy * (1 - v)).toFixed(3)}em) rotate(${(giro * (1 - v)).toFixed(1)}deg) scale(${(0.6 + 0.4 * v).toFixed(3)})`;
            } else {
              transform = `translateY(${((1 - v) * 0.7).toFixed(3)}em)`;
            }
            return (
              <span key={j} style={{display: 'inline-block', opacity: v, transform}}>
                {ch}
              </span>
            );
          })}
        </span>
      );
    });
  }
  if (r.karaoke && r.tiempos) {
    let k = -1;
    return partes.map((x, i) => {
      if (!x.trim()) return x;
      k += 1;
      const [ini, fin] = r.tiempos![k] ?? [Infinity, Infinity];
      const color = r.f >= fin ? (r.karaoke!.dicha ?? r.color) : r.f >= ini ? r.karaoke!.activa : (r.karaoke!.futura ?? r.color);
      return (
        <span key={i} style={{color}}>
          {x}
        </span>
      );
    });
  }
  if (r.tipo === 'palabras') {
    let k = -1;
    return partes.map((x, i) => {
      if (!x.trim()) return x;
      k += 1;
      // Cada palabra entra en su turno y tarda lo que dos turnos: se encadenan.
      const v = interpolate(r.u * (palabras + 1), [k, k + 2], [0, 1], fijo);
      return (
        <span key={i} style={{opacity: v, display: 'inline-block', transform: `translateY(${(1 - v) * 0.18}em)`}}>
          {x}
        </span>
      );
    });
  }
  return texto;
}

export const Letrero: React.FC<{
  e: EstiloTexto;
  texto: string;
  secundario?: string;
  /** Cuadro desde que empieza el letrero, y cuántos dura. */
  f: number;
  dura: number;
  fps: number;
  W: number;
  H: number;
  enPanel: boolean;
  /** Cuándo se dice cada palabra (cuadros desde el comienzo del letrero), para el karaoke. */
  palabras?: [number, number][];
}> = ({e, texto, secundario, f, dura, fps, W, H, enPanel, palabras}) => {
  useFuentes([e.fuente, e.secundario?.fuente], enPanel);
  if (f < 0 || f >= dura) return null;
  const entra = Math.max(1, Math.round((e.entrada?.dura ?? 0.5) * fps));
  const sale = Math.max(1, Math.round((e.salida?.dura ?? 0.4) * fps));
  const tipo = e.entrada?.tipo ?? 'fundido';
  const p = tipo === 'ninguna' ? 1 : interpolate(f, [0, entra], [0, 1], fijo);
  const u = suave(p);
  const salida = e.salida?.tipo ?? 'fundido';
  const v = salida === 'ninguna' ? 0 : suave(interpolate(f, [dura - sale, dura], [0, 1], fijo));

  if (e.rodillo) return <Rodillo e={e} texto={texto} f={f} dura={dura} H={H} W={W} />;

  // La salida: de a poco, bajando, o atravesando una letra (crece hasta que el cuadro queda adentro de ella).
  let opacidad = salida === 'fundido' || salida === 'bajar' ? 1 - v : salida === 'atravesar' && !e.ventana ? 1 - interpolate(v, [0.55, 1], [0, 1], fijo) : 1;
  let transform = '';
  let filter: string | undefined;
  let clipPath: string | undefined;
  const entraParejo = tipo === 'fundido' || tipo === 'subir' || tipo === 'acercar' || tipo === 'desenfoque';
  if (entraParejo) opacidad *= u;
  if (tipo === 'subir') transform += ` translateY(${(1 - u) * 0.35 * e.tamano * H}px)`;
  if (tipo === 'acercar') transform += ` scale(${0.93 + 0.07 * u})`;
  if (tipo === 'desenfoque') filter = `blur(${(1 - u) * 0.12 * e.tamano * H}px)`;
  if (tipo === 'barrido') clipPath = `inset(-20% ${((1 - u) * 100).toFixed(2)}% -20% -5%)`;
  if (salida === 'bajar') transform += ` translateY(${v * 0.3 * e.tamano * H}px)`;
  if (salida === 'atravesar') transform += ` scale(${Math.pow(70, v).toFixed(4)})`;
  if (e.latido) {
    // Un golpe: crece de una vez y vuelve en unos 100 ms, como un parlante.
    const bpm = typeof e.latido.bpm === 'number' ? e.latido.bpm : 100;
    const t = f / fps - (e.latido.fase ?? 0);
    if (t >= 0) transform += ` scale(${(1 + e.latido.fuerza * Math.exp(-(t % (60 / bpm)) / 0.11)).toFixed(4)})`;
  }
  if (e.giro) transform += ` rotate(${e.giro}deg)`;

  const alineado = e.alineado ?? (e.lugar.includes('izquierda') || e.lugar === 'tercio-inferior' ? 'izquierda' : e.lugar.includes('derecha') ? 'derecha' : 'centro');
  const textAlign = alineado === 'izquierda' ? 'left' : alineado === 'derecha' ? 'right' : 'center';
  const origen = alineado === 'izquierda' ? 'left center' : alineado === 'derecha' ? 'right center' : 'center center';
  // La compresión aprieta la línea a lo ancho; el bloque se ensancha en la misma medida para que ocupe lo pedido.
  const apretada = e.compresion && e.compresion !== 1 ? e.compresion : 1;
  const n = texto.split(/\s+/).filter(Boolean).length;
  const tiempos = e.karaoke ? tiemposPalabras(n, palabras, entra, Math.max(entra + 1, dura - sale - Math.round(0.4 * fps))) : undefined;
  const revelar = (color: string): Revelar => ({tipo, u, p, f, fps, semilla: e.id, karaoke: e.karaoke, tiempos, cursor: e.cursor, color});

  /** El bloque de texto; con `color`, todo de ese color y sin adornos (las dos capas de la ventana). */
  const bloque = (color?: string) => {
    const linea2 =
      secundario && e.secundario ? (
        <div
          style={{
            ...letra(e.secundario, H),
            ...(color ? {color} : {}),
            marginTop: e.secundario.arriba ? 0 : '0.35em',
            marginBottom: e.secundario.arriba ? '0.3em' : 0,
            ...(e.secundario.compresion ? {transform: `scaleX(${e.secundario.compresion})`, transformOrigin: origen} : {}),
          }}
        >
          {revelado(secundario, {...revelar(color ?? e.secundario.color), tipo: tipo === 'maquina' || tipo === 'palabras' ? tipo : undefined, karaoke: undefined, cursor: false})}
        </div>
      ) : null;
    const principal = revelado(texto, revelar(color ?? e.color));
    return (
      <div
        style={{
          maxWidth: ((e.ancho ?? 0.8) * W) / apretada,
          textAlign,
          opacity: opacidad,
          transform: transform || undefined,
          transformOrigin: e.ventana && salida === 'atravesar' ? '50% 52%' : undefined,
          filter,
          clipPath,
          whiteSpace: 'pre-line',
          ...(e.barra && !color ? {borderLeft: `${e.barra.ancho * e.tamano * H}px solid ${e.barra.color}`, paddingLeft: `${0.45 * e.tamano * H}px`} : {}),
        }}
      >
        {e.secundario?.arriba ? linea2 : null}
        <div
          style={{
            ...letra(e, H),
            ...(color ? {color} : trazo(e, H)),
            ...(apretada !== 1 ? {transform: `scaleX(${apretada})`, transformOrigin: origen} : {}),
          }}
        >
          {color ? principal : conFondo(e, principal)}
        </div>
        {e.secundario?.arriba ? null : linea2}
      </div>
    );
  };

  if (e.ventana) {
    // La imagen de abajo, sólo dentro de las letras: una capa negra con la letra blanca que multiplica (afuera, negro;
    // adentro, la imagen) y otra del color de afuera con la letra negra que aclara (afuera, ese color; adentro, nada).
    // Con dos capas sirve igual sobre un video. El fondo entra con la letra y, al atravesarla, se queda.
    const capa = (entraParejo ? u : 1) * (salida === 'fundido' || salida === 'bajar' ? 1 - v : 1);
    return (
      <>
        <AbsoluteFill style={{background: '#000000', mixBlendMode: 'multiply', opacity: capa}}>
          <AbsoluteFill style={caja(e.lugar, W, H)}>{bloque('#ffffff')}</AbsoluteFill>
        </AbsoluteFill>
        <AbsoluteFill style={{background: e.ventana.fuera, mixBlendMode: 'screen', opacity: capa}}>
          <AbsoluteFill style={caja(e.lugar, W, H)}>{bloque('#000000')}</AbsoluteFill>
        </AbsoluteFill>
      </>
    );
  }
  return <AbsoluteFill style={caja(e.lugar, W, H)}>{bloque()}</AbsoluteFill>;
};

/** Créditos que suben: entran por abajo y salen por arriba en lo que dura el letrero. «rol | nombre» va en dos letras. */
const Rodillo: React.FC<{e: EstiloTexto; texto: string; f: number; dura: number; W: number; H: number}> = ({e, texto, f, dura, W, H}) => {
  const filas = texto.split('\n');
  // Lo que mide el rollo, a ojo: cada par ocupa dos filas y un respiro. Sube del borde de abajo hasta salir por arriba.
  const alto = filas.reduce((s, x) => s + (x.includes('|') ? 2.6 : x.trim() ? 1.5 : 0.8), 0) * e.tamano * H * (e.interlineado ?? 1.12);
  const y = interpolate(f, [0, dura], [H, -alto], fijo);
  return (
    <AbsoluteFill style={{alignItems: 'center', overflow: 'hidden'}}>
      <div style={{position: 'absolute', top: y, width: (e.ancho ?? 0.7) * W, textAlign: 'center'}}>
        {filas.map((x, i) => {
          const [rol, nombre] = x.includes('|') ? x.split('|').map((s) => s.trim()) : [null, x];
          return (
            <div key={i} style={{marginBottom: `${0.9 * e.tamano * H}px`}}>
              {rol && e.secundario ? <div style={letra(e.secundario, H)}>{rol}</div> : null}
              <div style={{...letra(e, H), ...trazo(e, H)}}>{nombre || ' '}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/** Los fondos de la galería: oscuro, claro, una imagen simulada y el color de un mapa. */
export const FONDOS_MUESTRA = {
  oscuro: '#121212',
  claro: '#efe8da',
  imagen:
    'radial-gradient(ellipse at 28% 32%, #f6d39a 0%, transparent 46%), radial-gradient(ellipse at 74% 64%, #3f6f84 0%, transparent 52%), radial-gradient(ellipse at 52% 92%, #1f2a22 0%, transparent 60%), linear-gradient(165deg, #d79b55 0%, #7d6a52 45%, #26343c 100%)',
  mapa: 'linear-gradient(180deg, #bfe6f2 0%, #a6dbee 100%)',
} as const;
export type FondoMuestra = keyof typeof FONDOS_MUESTRA;

/** La muestra de la galería del panel: el letrero sobre un fondo, en un lazo de unos segundos. */
export const MuestraTexto: React.FC<{e: EstiloTexto; texto: string; secundario?: string; fondo: FondoMuestra}> = ({e, texto, secundario, fondo}) => {
  const f = useCurrentFrame();
  const {fps, width, height, durationInFrames} = useVideoConfig();
  const ini = Math.round(0.3 * fps);
  return (
    <AbsoluteFill style={{background: FONDOS_MUESTRA[fondo]}}>
      <Letrero e={e} texto={texto} secundario={secundario} f={f - ini} dura={durationInFrames - ini - Math.round(0.2 * fps)} fps={fps} W={width} H={height} enPanel />
    </AbsoluteFill>
  );
};
