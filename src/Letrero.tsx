import type {CSSProperties, ReactNode} from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {cssFamilia, useFuentes} from './fuentes';
import type {EstiloTexto, LetraLetrero, LugarLetrero} from './tipos';

/**
 * Un texto de la galería de textos (textos/<id>.json) dibujado en pantalla: la letra, su contorno,
 * sombra, caja o resaltado, el lugar y cómo entra y sale. Lo usan el modo planos (`letrero` en un
 * texto) y la galería del panel (/textos), que lo muestra en vivo con este mismo componente.
 *
 * Los tamaños van en fracción del alto del cuadro y los espacios en em: el mismo estilo se ve igual en
 * 16:9, 9:16 o 1:1.
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

/** El texto según la entrada: letra a letra o palabra a palabra se dibujan enteras y se destapan (el bloque no salta). */
function revelado(texto: string, tipo: string | undefined, u: number): ReactNode {
  if (tipo === 'maquina') {
    const n = Math.floor(u * texto.length + 1e-6);
    return (
      <>
        {texto.slice(0, n)}
        <span style={{opacity: 0}}>{texto.slice(n)}</span>
      </>
    );
  }
  if (tipo === 'palabras') {
    const partes = texto.split(/(\s+)/);
    const palabras = partes.filter((x) => x.trim()).length;
    let k = -1;
    return partes.map((x, i) => {
      if (!x.trim()) return x;
      k += 1;
      // Cada palabra entra en su turno y tarda lo que dos turnos: se encadenan.
      const v = interpolate(u * (palabras + 1), [k, k + 2], [0, 1], fijo);
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
}> = ({e, texto, secundario, f, dura, fps, W, H, enPanel}) => {
  useFuentes([e.fuente, e.secundario?.fuente], enPanel);
  if (f < 0 || f >= dura) return null;
  const entra = Math.max(1, Math.round((e.entrada?.dura ?? 0.5) * fps));
  const sale = Math.max(1, Math.round((e.salida?.dura ?? 0.4) * fps));
  const tipo = e.entrada?.tipo ?? 'fundido';
  const u = tipo === 'ninguna' ? 1 : suave(interpolate(f, [0, entra], [0, 1], fijo));
  const v = e.salida?.tipo === 'ninguna' ? 0 : suave(interpolate(f, [dura - sale, dura], [0, 1], fijo));

  if (e.rodillo) return <Rodillo e={e} texto={texto} f={f} dura={dura} H={H} W={W} />;

  let opacidad = 1 - v;
  let transform = '';
  let filter: string | undefined;
  let clipPath: string | undefined;
  if (tipo === 'fundido' || tipo === 'subir' || tipo === 'acercar' || tipo === 'desenfoque') opacidad *= u;
  if (tipo === 'subir') transform += ` translateY(${(1 - u) * 0.35 * e.tamano * H}px)`;
  if (tipo === 'acercar') transform += ` scale(${0.93 + 0.07 * u})`;
  if (tipo === 'desenfoque') filter = `blur(${(1 - u) * 0.12 * e.tamano * H}px)`;
  if (tipo === 'barrido') clipPath = `inset(-20% ${((1 - u) * 100).toFixed(2)}% -20% -5%)`;
  if (e.salida?.tipo === 'bajar') transform += ` translateY(${v * 0.3 * e.tamano * H}px)`;

  if (e.giro) transform += ` rotate(${e.giro}deg)`;

  const alineado = e.alineado ?? (e.lugar.includes('izquierda') || e.lugar === 'tercio-inferior' ? 'izquierda' : e.lugar.includes('derecha') ? 'derecha' : 'centro');
  const textAlign = alineado === 'izquierda' ? 'left' : alineado === 'derecha' ? 'right' : 'center';
  const origen = alineado === 'izquierda' ? 'left center' : alineado === 'derecha' ? 'right center' : 'center center';
  // La compresión aprieta la línea a lo ancho; el bloque se ensancha en la misma medida para que ocupe lo pedido.
  const apretada = e.compresion && e.compresion !== 1 ? e.compresion : 1;
  const linea2 = secundario && e.secundario ? (
    <div
      style={{
        ...letra(e.secundario, H),
        marginTop: e.secundario.arriba ? 0 : '0.35em',
        marginBottom: e.secundario.arriba ? '0.3em' : 0,
        ...(e.secundario.compresion ? {transform: `scaleX(${e.secundario.compresion})`, transformOrigin: origen} : {}),
      }}
    >
      {revelado(secundario, tipo === 'maquina' || tipo === 'palabras' ? tipo : undefined, u)}
    </div>
  ) : null;

  return (
    <AbsoluteFill style={caja(e.lugar, W, H)}>
      <div
        style={{
          maxWidth: ((e.ancho ?? 0.8) * W) / apretada,
          textAlign,
          opacity: opacidad,
          transform: transform || undefined,
          filter,
          clipPath,
          whiteSpace: 'pre-line',
          ...(e.barra ? {borderLeft: `${e.barra.ancho * e.tamano * H}px solid ${e.barra.color}`, paddingLeft: `${0.45 * e.tamano * H}px`} : {}),
        }}
      >
        {e.secundario?.arriba ? linea2 : null}
        <div style={{...letra(e, H), ...trazo(e, H), ...(apretada !== 1 ? {transform: `scaleX(${apretada})`, transformOrigin: origen} : {})}}>
          {conFondo(e, revelado(texto, tipo, u))}
        </div>
        {e.secundario?.arriba ? null : linea2}
      </div>
    </AbsoluteFill>
  );
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
