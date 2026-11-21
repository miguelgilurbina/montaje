import type {CSSProperties} from 'react';
import {
  AbsoluteFill,
  Easing,
  Freeze,
  Html5Audio,
  Img,
  interpolate,
  OffthreadVideo,
  Sequence,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {Planos} from './Planos';
import {CapaSintesis, escalaPelicula, filtroDe, golpeDeZoom, temblorDe} from './Sintesis';
import type {Capa, CapaVideo, ClaveCamara, Eco, Momento, Pieza, Timeline} from './tipos';

/** Cuadros antes de su entrada en que la imagen ya está montada (invisible), para que el Studio la tenga cargada. */
const PRECARGA = 20;
/** Desde este ancho en pantalla (px), una pieza de la pared usa la imagen grande y no la miniatura. */
const UMBRAL_MINI = 420;
/** Bajo este alto en pantalla (px) la pieza no lleva calado: no se vería y cada máscara cuesta tiempo de render. */
const UMBRAL_CALADO = 60;

/** Un archivo de la biblioteca: en el render sale de --public-dir; en el panel, del servidor (`base`). */
const archivo = (tl: Timeline, ruta: string) => (tl.base ? tl.base + ruta : staticFile(ruta));

const fijo = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const suave = Easing.inOut(Easing.quad);
const curvaVuelo = Easing.inOut(Easing.cubic);

const lerp = (a: number, b: number, u: number) => a + (b - a) * u;
const entre = (par: [number, number], u: number) => lerp(par[0], par[1], u);
const avance = (frame: number, ini: number, fin: number) => Math.min(1, Math.max(0, (frame - ini) / Math.max(1, fin - ini)));

export const Montaje: React.FC<Timeline> = (tl) => {
  const frame = useCurrentFrame();
  const visibles = tl.capas.filter((c) => frame >= c.ini - PRECARGA && frame < c.fin);
  const ecos = (tl.ecos ?? []).filter((e) => frame >= e.ini && frame < e.fin);
  const hayPared = Boolean(tl.mural && tl.camara?.length);

  const sintesis = tl.sintesis ?? [];
  const escala = sintesis.length ? escalaPelicula(tl, frame) * golpeDeZoom(tl, frame) : 1;
  const temblor = sintesis.length ? [temblorDe(tl, frame), escala !== 1 ? `scale(${escala})` : ''].filter(Boolean).join(' ') || undefined : undefined;
  const {filtro, defs} = sintesis.length ? filtroDe(tl, frame) : {filtro: undefined, defs: null};

  return (
    <AbsoluteFill style={{backgroundColor: tl.fondo, isolation: 'isolate', overflow: 'hidden'}}>
      {sintesis
        .filter((s) => s.tipo === 'campo')
        .map((s, i) => (
          <CapaSintesis key={`campo-${i}`} tl={tl} s={s} frame={frame} />
        ))}
      {defs}
      {/* Sin temblor ni filtro el contenido va suelto, como siempre: un div con transform o filter cambiaría cómo se mezclan las capas. */}
      <Contenido temblor={temblor} filtro={filtro}>
        {tl.planos?.length ? <Planos tl={tl} frame={frame} /> : null}
        {tl.collage && tl.camara?.length ? <CollageInfinito tl={tl} frame={frame} /> : null}
        {tl.cinta ? <CintaInfinita tl={tl} frame={frame} /> : null}
        {(tl.momentos ?? []).map((mo) =>
          mo.tipo === 'video' ? <MomentoVideo key={`v-${mo.ini}`} tl={tl} mo={mo} /> : null,
        )}
        {(tl.momentos ?? [])
          .filter((mo) => frame >= mo.ini - PRECARGA && frame <= mo.fin)
          .map((mo) =>
            mo.tipo === 'destacado' ? (
              <Destacado key={`d-${mo.ini}`} tl={tl} mo={mo} frame={frame} />
            ) : mo.tipo === 'rafaga' ? (
              <Rafaga key={`r-${mo.ini}`} tl={tl} mo={mo} frame={frame} />
            ) : null,
          )}
        {hayPared ? <Pared tl={tl} g={frame} /> : null}
        {ecos.map((e) => (
          <CapaEco key={`eco-${e.ini}`} tl={tl} e={e} frame={frame} />
        ))}
        {visibles.map((c) => (
          <CapaImagen key={c.id} c={c} frame={frame} tl={tl} />
        ))}
      </Contenido>
      {sintesis
        .filter((s) => s.tipo !== 'campo')
        .map((s, i) => (
          <CapaSintesis key={`sintesis-${i}`} tl={tl} s={s} frame={frame} />
        ))}
      {tl.logo ? <LogoCuriana tl={tl} frame={frame} /> : null}
      <Audio tl={tl} />
    </AbsoluteFill>
  );
};

const Contenido: React.FC<{temblor?: string; filtro?: string; children: React.ReactNode}> = ({temblor, filtro, children}) =>
  temblor || filtro ? <AbsoluteFill style={{transform: temblor, filter: filtro}}>{children}</AbsoluteFill> : <>{children}</>;

/** El tramo de la canción, con fundidos opcionales al entrar y al salir. */
const Audio: React.FC<{tl: Timeline}> = ({tl}) => {
  if (!tl.audio) return null;
  const {src, desde, hasta, fundido = [0, 0]} = tl.audio;
  const fin = hasta !== undefined ? Math.round(hasta * tl.fps) : undefined;
  const largo = fin !== undefined ? fin - Math.round(desde * tl.fps) : tl.duracion;
  const [fe, fs] = fundido.map((s) => Math.max(0, Math.round(s * tl.fps)));
  const volumen = (f: number) => Math.min(fe ? Math.min(1, f / fe) : 1, fs ? Math.min(1, (largo - f) / fs) : 1);
  return (
    <Html5Audio
      src={archivo(tl, src)}
      trimBefore={Math.round(desde * tl.fps)}
      trimAfter={fin}
      volume={fe || fs ? volumen : undefined}
    />
  );
};

// ── Protagonistas ──────────────────────────────────────────────────────────

const CapaImagen: React.FC<{c: Capa; frame: number; tl: Timeline}> = ({c, frame, tl}) => {
  if (c.video) return <CapaClip c={c} frame={frame} tl={tl} />;
  if (c.vuelo && tl.mural && tl.camara && frame >= c.vuelo.desde) {
    return <ImagenEnVuelo c={c} frame={frame} tl={tl} />;
  }
  // Con vuelo, el zoom y la deriva se completan al despegar, para que el vuelo arranque sin salto.
  const finMovimiento = c.vuelo ? c.vuelo.desde : c.fin;
  const t = avance(frame, c.ini, finMovimiento);

  // entrada 0 = corte seco: visible entera desde su primer cuadro.
  const alEntrar = c.entrada > 0 ? interpolate(frame, [c.ini, c.ini + c.entrada], [0, 1], {...fijo, easing: suave}) : 1;
  const alSalir = c.salida > 0 ? interpolate(frame, [c.fin - c.salida, c.fin], [1, 0], {...fijo, easing: suave}) : 1;
  const opacidad = frame < c.ini ? 0 : c.opacidad * Math.min(alEntrar, alSalir);

  const estilo: CSSProperties = {
    position: 'absolute',
    left: c.x - c.ancho / 2,
    top: c.y - c.alto / 2,
    width: c.ancho,
    height: c.alto,
    opacity: opacidad,
    transform: `translate(${c.deriva[0] * t}px, ${c.deriva[1] * t}px) scale(${entre(c.zoom, t)})`,
    mixBlendMode: c.mezcla as CSSProperties['mixBlendMode'],
    ...mascara((c.borde ?? 0) * Math.min(c.ancho, c.alto)),
  };
  return <Img src={archivo(tl, c.img)} style={estilo} />;
};

/**
 * Un clip como capa: los mismos fundidos, zoom, deriva y mezcla que una imagen, pero
 * corre desde `video.desde` a `video.velocidad`. Con `relleno`, detrás va el mismo
 * clip cubriendo el cuadro, desenfocado y oscuro (un vertical en un cuadro horizontal).
 */
const CapaClip: React.FC<{c: Capa; frame: number; tl: Timeline}> = ({c, frame, tl}) => {
  const v = c.video!;
  const t = avance(frame, c.ini, c.fin);
  const alEntrar = c.entrada > 0 ? interpolate(frame, [c.ini, c.ini + c.entrada], [0, 1], {...fijo, easing: suave}) : 1;
  const alSalir = c.salida > 0 ? interpolate(frame, [c.fin - c.salida, c.fin], [1, 0], {...fijo, easing: suave}) : 1;
  let opacidad = frame < c.ini ? 0 : c.opacidad * Math.min(alEntrar, alSalir);
  // La transición: cómo entra sobre el clip que se va (que sigue entero debajo hasta que ésta termina).
  const paso = transicionDe(c, frame, alEntrar, tl);
  if (paso) opacidad = frame < c.ini ? 0 : c.opacidad * paso.opacidad * alSalir;
  // En una toma corta puede estar entrando todavía cuando ya la empujan: los dos movimientos se suman, no se pisan.
  const empuje = empujeDe(c, frame, tl);
  const sale: CSSProperties = empuje.transform && paso?.estilo.transform ? {transform: `${empuje.transform} ${paso.estilo.transform}`} : empuje;
  const src = archivo(tl, c.img);
  // La foto que despierta: quieta en `desde` durante `congelar` cuadros; para que después
  // corra desde ahí sin saltar, el clip arranca `congelar` cuadros antes.
  const congelar = v.congelar ?? 0;
  const local = frame - c.ini;
  const despierta = congelar ? interpolate(local, [congelar - 2, congelar + 12], [0, 1], fijo) : 1;
  // El cuadro de la toma que se ve: quieto mientras la foto despierta, o el que dicen los gestos de tiempo.
  const visto = congelar > 0 && local < congelar ? congelar : cuadroVisto(local, v.tiempo, congelar);
  const reproducir = {
    src,
    trimBefore: Math.max(0, Math.round(v.desde * tl.fps - congelar * v.velocidad)),
    playbackRate: v.velocidad,
    muted: !v.volumen,
    volume: v.volumen ?? 0,
  };
  const m = c.marco;
  const caja = (
    <div
      style={{
        position: 'absolute',
        left: c.x - c.ancho / 2 - (m ? m.x - m.ancho / 2 : 0),
        top: c.y - c.alto / 2 - (m ? m.y - m.alto / 2 : 0),
        width: c.ancho,
        height: c.alto,
        overflow: 'hidden',
        transform: `translate(${c.deriva[0] * t}px, ${c.deriva[1] * t}px) scale(${entre(c.zoom, t)})`,
        filter: despierta < 1 ? `sepia(${(0.6 * (1 - despierta)).toFixed(3)}) saturate(${(0.35 + 0.65 * despierta).toFixed(3)})` : undefined,
        boxShadow: c.sombra ? `0 ${c.alto * 0.02}px ${c.alto * 0.07}px rgba(0,0,0,${c.sombra})` : undefined,
        ...mascara((c.borde ?? 0) * Math.min(c.ancho, c.alto)),
      }}
    >
      <Freeze frame={visto} active={visto !== local}>
        <DibujoClip v={v} reproducir={reproducir} ancho={c.ancho} alto={c.alto} fps={tl.fps} fondo={tl.fondo} />
      </Freeze>
    </div>
  );
  return (
    <Sequence
      from={c.ini}
      durationInFrames={Math.max(1, c.fin - c.ini)}
      premountFor={PRECARGA}
      style={{opacity: opacidad, mixBlendMode: c.mezcla as CSSProperties['mixBlendMode'], ...paso?.estilo, ...sale}}
    >
      <AbsoluteFill style={paso?.contenido !== undefined ? {opacity: paso.contenido} : undefined}>
        {v.relleno ? (
          // Con la foto que despierta, el fondo desenfocado se queda quieto con ella (antes seguía corriendo detrás).
          <Freeze frame={visto} active={visto !== local}>
            <Relleno tl={tl} fuente={v.fuente} reproducir={reproducir} foto={v.foto} />
          </Freeze>
        ) : null}
        {m ? (
          <div style={{position: 'absolute', left: m.x - m.ancho / 2, top: m.y - m.alto / 2, width: m.ancho, height: m.alto, overflow: 'hidden'}}>
            {caja}
          </div>
        ) : (
          caja
        )}
      </AbsoluteFill>
      {/* El fogonazo va después del clip (encima de él) y sin z-index: con uno se pintaba también sobre títulos y rótulos. */}
      {paso?.encima}
    </Sequence>
  );
};

/**
 * Qué cuadro de la toma se ve en el cuadro `local` con los gestos de tiempo: quieto en el golpe, el pedacito
 * del golpe repetido, o a saltos (paso de cuadro). Nunca uno posterior a `local`: no gasta material. Ni anterior
 * a `minimo`: con la foto que despierta, lo de antes de `congelar` es el clip antes de su `desde`.
 */
export function cuadroVisto(local: number, t?: CapaVideo['tiempo'], minimo = 0): number {
  if (!t) return local;
  const paso = (f: number) => Math.max(minimo, t.paso && t.paso > 1 ? Math.floor(f / t.paso) * t.paso : f);
  for (const [ini, cuantos] of t.congelados ?? []) {
    if (local >= ini && local < ini + cuantos) return paso(ini);
  }
  for (const [ini, largo, veces] of t.tartamudeos ?? []) {
    if (local >= ini && local < ini + largo * veces) return paso(ini + ((local - ini) % largo));
  }
  return paso(local);
}

/**
 * La entrada de un clip con `transicion`: en vez de aparecer de a poco, se abre paso
 * sobre el que se va. `u` es el avance de su entrada (0 → 1, ya suavizado). Devuelve
 * la opacidad y el estilo de la capa entera en este cuadro, y lo que va encima (el fogonazo).
 */
function transicionDe(
  c: Capa,
  frame: number,
  u: number,
  tl: Timeline,
): {opacidad: number; estilo: CSSProperties; encima?: React.ReactNode; contenido?: number} | null {
  const tr = c.transicion;
  if (!tr || c.entrada <= 0 || frame >= c.ini + c.entrada) return null;
  const W = tl.ancho;
  const H = tl.alto;
  const [dx, dy] = tr.dir;
  const mascara_ = (m: string): CSSProperties => ({maskImage: m, WebkitMaskImage: m});
  // Hacia dónde avanza el borde: 90deg = de izquierda a derecha.
  const angulo = dx > 0 ? 90 : dx < 0 ? 270 : dy > 0 ? 180 : 0;
  if (tr.tipo === 'cortina') {
    const borde = 7; // % del cuadro que ocupa el borde blando
    const p = u * (100 + borde);
    return {opacidad: 1, estilo: mascara_(`linear-gradient(${angulo}deg, #000 ${(p - borde).toFixed(2)}%, transparent ${p.toFixed(2)}%)`)};
  }
  if (tr.tipo === 'iris') {
    const [cx, cy] = tr.centro ?? [W / 2, H / 2];
    const lejos = Math.hypot(Math.max(cx, W - cx), Math.max(cy, H - cy));
    const borde = H * 0.05;
    const r = u * (lejos + borde);
    return {opacidad: 1, estilo: mascara_(`radial-gradient(circle at ${cx}px ${cy}px, #000 ${Math.max(0, r - borde).toFixed(1)}px, transparent ${r.toFixed(1)}px)`)};
  }
  if (tr.tipo === 'persiana') {
    const horizontal = dx !== 0;
    const ancho = (horizontal ? W : H) / (horizontal ? 14 : 9);
    const lleno = (u * ancho).toFixed(1);
    return {
      opacidad: 1,
      estilo: mascara_(`repeating-linear-gradient(${angulo}deg, #000 0, #000 ${lleno}px, transparent ${lleno}px, transparent ${ancho.toFixed(1)}px)`),
    };
  }
  if (tr.tipo === 'empuje') {
    return {opacidad: 1, estilo: {transform: `translate(${(-dx * (1 - u) * W).toFixed(1)}px, ${(-dy * (1 - u) * H).toFixed(1)}px)`}};
  }
  if (tr.tipo === 'zoom') {
    return {opacidad: u, estilo: {transform: `scale(${(1 + 0.28 * (1 - u)).toFixed(4)})`, filter: `blur(${((1 - u) * H * 0.012).toFixed(1)}px)`}};
  }
  // destello: un fogonazo cálido sube sobre el clip que se va y lo tapa; el nuevo aparece
  // debajo justo en el tope de la luz, y se descubre cuando baja.
  const luz = u < 0.45 ? u / 0.45 : 1 - (u - 0.45) / 0.55;
  return {
    opacidad: 1,
    estilo: {},
    contenido: u < 0.45 ? 0 : 1,
    encima: (
      <AbsoluteFill style={{backgroundColor: '#fff1d0', opacity: Math.pow(Math.max(0, luz), 0.8), mixBlendMode: 'screen', pointerEvents: 'none'}} />
    ),
  };
}

/** El clip que se va cuando el siguiente entra con empuje: sale por el otro lado en los mismos cuadros. */
function empujeDe(c: Capa, frame: number, tl: Timeline): CSSProperties {
  const e = c.empujada;
  if (!e || e.cuadros <= 0 || frame < c.fin - e.cuadros) return {};
  const u = interpolate(frame, [c.fin - e.cuadros, c.fin], [0, 1], {...fijo, easing: suave});
  return {transform: `translate(${(e.dir[0] * u * tl.ancho).toFixed(1)}px, ${(e.dir[1] * u * tl.alto).toFixed(1)}px)`};
}

type Reproducir = {src: string; trimBefore: number; playbackRate: number; muted: boolean; volume: number};

/** Lo que se ve en la caja de una capa: el clip corriendo o, si la capa es una foto, la imagen. */
const Fuente: React.FC<{foto?: boolean; src: string; trimBefore: number; playbackRate: number; muted?: boolean; volume?: number; style?: CSSProperties}> = ({
  foto,
  style,
  ...reproducir
}) => (foto ? <Img src={reproducir.src} style={style} /> : <OffthreadVideo {...reproducir} style={style} />);

/**
 * El clip dentro de su caja: entero, en caleidoscopio (`espejo`: el centro del clip
 * repetido en espejo, en dos mitades o cuatro cuartos que empalman en las costuras)
 * o en mosaico de tiempo (`rejilla`: el clip en cada celda, cada una `desfase` s más
 * atrás, en diagonal, así el movimiento recorre la cuadrícula como una ola).
 */
const DibujoClip: React.FC<{v: CapaVideo; reproducir: Reproducir; ancho: number; alto: number; fps: number; fondo: string}> = ({
  v,
  reproducir,
  ancho,
  alto,
  fps,
  fondo,
}) => {
  const lleno: CSSProperties = {width: '100%', height: '100%', objectFit: 'fill', display: 'block'};
  if (v.espejo) {
    const cols = 2;
    const filas = v.espejo === 4 ? 2 : 1;
    const w = ancho / cols;
    const h = alto / filas;
    const celdas = [];
    for (let j = 0; j < filas; j++) {
      for (let i = 0; i < cols; i++) {
        celdas.push(
          <div
            key={`${i}-${j}`}
            style={{
              position: 'absolute',
              left: i * w,
              top: j * h,
              width: w,
              height: h,
              overflow: 'hidden',
              transform: `scale(${i ? -1 : 1}, ${j ? -1 : 1})`,
            }}
          >
            {/* El centro del clip: la caja entera corrida medio tramo. */}
            <Fuente
              foto={v.foto}
              {...reproducir}
              muted={i + j > 0 || reproducir.muted}
              style={{position: 'absolute', left: -(ancho - w) / 2, top: -(alto - h) / 2, width: ancho, height: alto, maxWidth: 'none'}}
            />
          </div>,
        );
      }
    }
    return <>{celdas}</>;
  }
  if (v.rejilla) {
    const {columnas, filas, desfase} = v.rejilla;
    const hueco = Math.max(2, Math.round(Math.min(ancho, alto) * 0.006));
    const w = (ancho - hueco * (columnas - 1)) / columnas;
    const h = (alto - hueco * (filas - 1)) / filas;
    const celdas = [];
    for (let j = 0; j < filas; j++) {
      for (let i = 0; i < columnas; i++) {
        const atras = Math.round((i + j) * desfase * fps);
        celdas.push(
          <div key={`${i}-${j}`} style={{position: 'absolute', left: i * (w + hueco), top: j * (h + hueco), width: w, height: h, overflow: 'hidden'}}>
            <Fuente
              foto={v.foto}
              {...reproducir}
              trimBefore={Math.max(0, reproducir.trimBefore - atras)}
              muted={i + j > 0 || reproducir.muted}
              style={{...lleno, objectFit: 'cover'}}
            />
          </div>,
        );
      }
    }
    return <div style={{position: 'absolute', inset: 0, backgroundColor: fondo}}>{celdas}</div>;
  }
  return <Fuente foto={v.foto} {...reproducir} style={lleno} />;
};

/** El clip cubriendo el cuadro, desenfocado y oscuro. Se dibuja a un cuarto y se agranda: el desenfoque cuesta mucho menos. */
const Relleno: React.FC<{
  tl: Timeline;
  fuente: [number, number];
  reproducir: {src: string; trimBefore: number; playbackRate: number};
  foto?: boolean;
}> = ({tl, fuente, reproducir, foto}) => {
  const k = 4;
  const W = tl.ancho / k;
  const H = tl.alto / k;
  const s = Math.max(W / fuente[0], H / fuente[1]) * 1.12;
  const w = fuente[0] * s;
  const h = fuente[1] * s;
  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        width: W,
        height: H,
        overflow: 'hidden',
        transformOrigin: '0 0',
        transform: `scale(${k})`,
        filter: 'blur(5px) brightness(0.4) saturate(0.8)',
      }}
    >
      <Fuente foto={foto} {...reproducir} muted style={{position: 'absolute', left: (W - w) / 2, top: (H - h) / 2, width: w, height: h, maxWidth: 'none'}} />
    </div>
  );
};

/** De su lugar como protagonista a su pieza en la pared, siguiendo a la cámara mientras vuela. */
const ImagenEnVuelo: React.FC<{c: Capa; frame: number; tl: Timeline}> = ({c, frame, tl}) => {
  const mural = tl.mural!;
  const pieza = mural.piezas[c.vuelo!.pieza];
  const u = curvaVuelo(avance(frame, c.vuelo!.desde, c.fin));
  const [, cx, cy, s] = camaraEn(tl.camara!, frame);

  const origen = {x: c.x + c.deriva[0], y: c.y + c.deriva[1], w: c.ancho * c.zoom[1], h: c.alto * c.zoom[1]};
  const destino = {
    x: tl.ancho / 2 + (pieza.x - cx) * s,
    y: tl.alto / 2 + (pieza.y - cy) * s,
    w: pieza.ancho * s,
    h: pieza.alto * s,
  };
  const x = lerp(origen.x, destino.x, u);
  const y = lerp(origen.y, destino.y, u);
  const w = lerp(origen.w, destino.w, u);
  const h = lerp(origen.h, destino.h, u);
  const borde = lerp((c.borde ?? 0) * Math.min(origen.w, origen.h), mural.borde * Math.min(destino.w, destino.h), u);

  const estilo: CSSProperties = {
    position: 'absolute',
    left: x - w / 2,
    top: y - h / 2,
    width: w,
    height: h,
    opacity: lerp(c.opacidad, valorEn(mural.luz, frame), u),
    mixBlendMode: (u < 0.5 ? c.mezcla : 'normal') as CSSProperties['mixBlendMode'],
    ...mascara(borde),
  };
  return <Img src={archivo(tl, c.img)} style={estilo} />;
};

// ── La pared ───────────────────────────────────────────────────────────────

/**
 * La pared vista por la cámara en el cuadro `g` (los ecos la piden en un cuadro pasado).
 * `recorte` es cuánto más grande que el cuadro es la zona que se dibuja: 1 para la
 * pared principal; un eco que la achica necesita ver más allá del cuadro.
 */
const Pared: React.FC<{tl: Timeline; g: number; recorte?: number}> = ({tl, g, recorte = 1}) => {
  const mural = tl.mural!;
  const [, cx, cy, s] = camaraEn(tl.camara!, g);
  const W = tl.ancho;
  const H = tl.alto;
  const piezas = mural.piezas.filter((p) => p.llega <= g && enCuadro(p, cx, cy, s, W, H, recorte));

  return (
    <AbsoluteFill style={{opacity: valorEn(mural.luz, g)}}>
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          transformOrigin: '0 0',
          transform: `translate(${W / 2}px, ${H / 2}px) scale(${s}) translate(${-cx}px, ${-cy}px)`,
        }}
      >
        {piezas.map((p) => (
          <Img
            key={p.id}
            src={archivo(tl, p.ancho * s > UMBRAL_MINI ? p.img : p.mini)}
            style={{
              position: 'absolute',
              left: p.x - p.ancho / 2,
              top: p.y - p.alto / 2,
              width: p.ancho,
              height: p.alto,
              ...(p.alto * s >= UMBRAL_CALADO ? mascara(mural.borde * Math.min(p.ancho, p.alto)) : {}),
            }}
          />
        ))}
      </div>
    </AbsoluteFill>
  );
};

/** Montaje sobre montaje: la pared (quizá como era hace un rato) escalada, girada y fundida sobre sí misma. */
const CapaEco: React.FC<{tl: Timeline; e: Eco; frame: number}> = ({tl, e, frame}) => {
  const t = avance(frame, e.ini, e.fin);
  const alEntrar = interpolate(frame, [e.ini, e.ini + Math.max(1, e.entrada)], [0, 1], {...fijo, easing: suave});
  const alSalir = interpolate(frame, [e.fin - Math.max(1, e.salida), e.fin], [1, 0], {...fijo, easing: suave});
  // Qué parte de la pared puede caer en cuadro después de escalar, girar y desplazar el eco.
  const k = entre(e.escala, t);
  const desplazamiento = Math.max(Math.abs(entre(e.dx, t)) / tl.ancho, Math.abs(entre(e.dy, t)) / tl.alto);
  const recorte = (1.45 + 2 * desplazamiento) / k;
  return (
    <AbsoluteFill
      style={{
        opacity: e.opacidad * Math.min(alEntrar, alSalir),
        mixBlendMode: e.mezcla as CSSProperties['mixBlendMode'],
        transform: `translate(${entre(e.dx, t)}px, ${entre(e.dy, t)}px) rotate(${entre(e.rot, t)}deg) scale(${entre(e.escala, t)})`,
      }}
    >
      <Pared tl={tl} g={frame - e.desfase} recorte={recorte} />
    </AbsoluteFill>
  );
};

// ── Collage ────────────────────────────────────────────────────────────────

/**
 * Papeles que caen y se quedan, vistos por una cámara que se aleja. Cada imagen va
 * opaca, sin máscara ni mezcla: se ve con todo su detalle. Su orden en la lista es
 * su altura en la pila.
 */
const CollageInfinito: React.FC<{tl: Timeline; frame: number}> = ({tl, frame}) => {
  const {piezas, sombra} = tl.collage!;
  const [, cx, cy, s] = camaraEn(tl.camara!, frame);
  const W = tl.ancho;
  const H = tl.alto;
  const visibles = piezas.filter(
    (p) => p.ini <= frame + PRECARGA && (p.tapada === undefined || frame < p.tapada) && enCuadro(p, cx, cy, s, W, H, 1.1),
  );
  return (
    <AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          transformOrigin: '0 0',
          transform: `translate(${W / 2}px, ${H / 2}px) scale(${s}) translate(${-cx}px, ${-cy}px)`,
        }}
      >
        {visibles.map((p) => {
          const u = curvaVuelo(avance(frame, p.ini, p.ini + Math.max(1, p.entrada)));
          // Resolución completa mientras se ve grande; cuando la cámara ya la achicó,
          // la miniatura alcanza para su tamaño en pantalla y ahorra memoria de render.
          const grande = Math.max(p.ancho, p.alto) * s > UMBRAL_MINI;
          return (
            <Img
              key={p.id}
              src={archivo(tl, grande ? p.img : p.img.replace(/^imagenes\//, 'miniaturas/'))}
              style={{
                position: 'absolute',
                left: p.x - p.ancho / 2,
                top: p.y - p.alto / 2,
                width: p.ancho,
                height: p.alto,
                opacity: frame < p.ini ? 0 : u,
                transform: `rotate(${p.rot}deg) scale(${lerp(1.06, 1, u)})`,
                boxShadow: sombra ? `0 ${p.alto * 0.015}px ${p.alto * 0.035}px rgba(0,0,0,${sombra})` : undefined,
              }}
            />
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ── Momentos ───────────────────────────────────────────────────────────────

type Destacado_ = Extract<Momento, {tipo: 'destacado'}>;
type Rafaga_ = Extract<Momento, {tipo: 'rafaga'}>;

/**
 * Una imagen al frente: el collage se oscurece, ella sube grande y nítida (nunca
 * más que su tamaño nativo), respira con un acercamiento lento y al final vuela a
 * su lugar en el collage, siguiendo a la cámara.
 */
const Destacado: React.FC<{tl: Timeline; mo: Destacado_; frame: number}> = ({tl, mo, frame}) => {
  if (frame < mo.ini) {
    // Montada invisible para que esté cargada cuando entra.
    return <Img src={archivo(tl, mo.img)} style={{position: 'absolute', width: 1, height: 1, opacity: 0}} />;
  }
  const W = tl.ancho;
  const H = tl.alto;
  const despega = mo.pieza >= 0 || mo.desde ? mo.fin - mo.salida : mo.fin;
  const alEntrar = curvaVuelo(avance(frame, mo.ini, mo.ini + mo.entrada));
  const respira = lerp(1, 1.035, avance(frame, mo.ini, despega));
  const k = (mo.desde ? 1 : lerp(0.92, 1, alEntrar)) * respira;
  let x = W / 2;
  let y = H / 2;
  let w = mo.ancho * k;
  let h = mo.alto * k;
  let rot = 0;
  let oscuro = mo.oscuro * alEntrar;
  let opacidad = mo.desde ? 1 : alEntrar;

  if (mo.desde) {
    // Sale de su lugar (en la cinta), crece al frente y al final vuelve ahí.
    const d = mo.desde;
    const vuelta = frame >= despega ? curvaVuelo(avance(frame, despega, mo.fin)) : 0;
    const u = alEntrar * (1 - vuelta);
    x = lerp(d.x, x, u);
    y = lerp(d.y, y, u);
    w = lerp(d.ancho, w, u);
    h = lerp(d.alto, h, u);
    oscuro = mo.oscuro * u;
    opacidad = 1;
  } else if (frame >= despega && mo.pieza >= 0 && tl.collage && tl.camara) {
    const p = tl.collage.piezas[mo.pieza];
    const [, cx, cy, s] = camaraEn(tl.camara, frame);
    const u = curvaVuelo(avance(frame, despega, mo.fin));
    x = lerp(x, W / 2 + (p.x - cx) * s, u);
    y = lerp(y, H / 2 + (p.y - cy) * s, u);
    w = lerp(w, p.ancho * s, u);
    h = lerp(h, p.alto * s, u);
    rot = lerp(0, p.rot, u);
    oscuro *= 1 - u;
  }

  return (
    <>
      <AbsoluteFill style={{backgroundColor: '#000', opacity: oscuro}} />
      <Img
        src={archivo(tl, mo.img)}
        style={{
          position: 'absolute',
          left: x - w / 2,
          top: y - h / 2,
          width: w,
          height: h,
          opacity: opacidad,
          transform: `rotate(${rot}deg)`,
          boxShadow: `0 ${h * 0.02}px ${h * 0.06}px rgba(0,0,0,0.6)`,
        }}
      />
    </>
  );
};

type Video_ = Extract<Momento, {tipo: 'video'}>;

/**
 * Un video dentro del montaje (la intro hecha con Gemini): se recorta la parte que
 * importa, se centra sobre el fondo y se ajusta su velocidad para que dure justo
 * sus compases. Tapa lo que haya detrás mientras dura.
 */
const MomentoVideo: React.FC<{tl: Timeline; mo: Video_}> = ({tl, mo}) => {
  const [sx, sy, sw, sh] = mo.recorte;
  const k = mo.ancho / sw;
  return (
    <Sequence from={mo.ini} durationInFrames={mo.fin - mo.ini}>
      <AbsoluteFill style={{backgroundColor: tl.fondo}}>
        <div
          style={{
            position: 'absolute',
            left: (tl.ancho - mo.ancho) / 2,
            top: (tl.alto - mo.alto) / 2,
            width: mo.ancho,
            height: mo.alto,
            overflow: 'hidden',
          }}
        >
          <OffthreadVideo
            src={archivo(tl, mo.src)}
            playbackRate={mo.velocidad}
            volume={mo.volumen}
            muted={mo.volumen === 0}
            style={{
              position: 'absolute',
              left: -sx * k,
              top: -sy * k,
              width: mo.fuente[0] * k,
              height: mo.fuente[1] * k,
              maxWidth: 'none',
            }}
          />
        </div>
      </AbsoluteFill>
    </Sequence>
  );
};

// ── Cinta ──────────────────────────────────────────────────────────────────

/**
 * Una columna de imágenes que sube un paso por golpe. Se dibuja cíclica (cada imagen
 * también un largo más arriba y más abajo), así el último cuadro empalma con el primero.
 */
const CintaInfinita: React.FC<{tl: Timeline; frame: number}> = ({tl, frame}) => {
  const c = tl.cinta!;
  const desp = valorEn(c.desplazamiento, frame);
  const W = tl.ancho;
  const H = tl.alto;
  const piezas: {key: string; img: string; y: number; ancho: number; alto: number}[] = [];
  for (const it of c.items) {
    for (const vuelta of [-1, 0, 1]) {
      const y = H / 2 + it.y - desp + vuelta * c.largo;
      if (y + it.alto / 2 > -40 && y - it.alto / 2 < H + 40) {
        piezas.push({key: `${it.id}-${vuelta}`, img: it.img, y, ancho: it.ancho, alto: it.alto});
      }
    }
  }
  return (
    <AbsoluteFill>
      {piezas.map((p) => (
        <Img
          key={p.key}
          src={archivo(tl, p.img)}
          style={{
            position: 'absolute',
            left: (W - p.ancho) / 2,
            top: p.y - p.alto / 2,
            width: p.ancho,
            height: p.alto,
            boxShadow: c.sombra ? `0 ${p.alto * 0.015}px ${p.alto * 0.04}px rgba(0,0,0,${c.sombra})` : undefined,
          }}
        />
      ))}
    </AbsoluteFill>
  );
};

// ── Logo ───────────────────────────────────────────────────────────────────

/**
 * El sello de Curiana Radio en una esquina (late en los primeros tiempos) y, en los
 * tramos de salvapantallas, el logo suelto rebotando por el cuadro como el del DVD:
 * cada vez que toca un borde cambia de versión.
 */
const LogoCuriana: React.FC<{tl: Timeline; frame: number}> = ({tl, frame}) => {
  const {sello, salvapantallas = []} = tl.logo!;
  const W = tl.ancho;
  const H = tl.alto;
  const activo = salvapantallas.find((s) => frame >= s.ini && frame < s.fin);
  const elementos: React.ReactNode[] = [];

  if (sello) {
    const oculto = sello.ocultar.some(([a, b]) => frame >= a - 6 && frame < b + 6);
    const transicion = sello.ocultar.reduce((m, [a, b]) => {
      if (frame >= a - 6 && frame < a) return Math.min(m, (a - frame) / 6);
      if (frame >= b && frame < b + 6) return Math.min(m, (frame - b) / 6);
      return m;
    }, 1);
    const ultimo = [...sello.pulsos].reverse().find((f) => f <= frame);
    const pulso = ultimo === undefined ? 0 : Math.exp(-(frame - ultimo) / 4);
    const op = oculto && transicion === 1 ? 0 : sello.opacidad * transicion;
    elementos.push(
      <Img
        key="sello"
        src={archivo(tl, sello.img)}
        style={{
          position: 'absolute',
          left: sello.x,
          top: sello.y,
          width: sello.ancho,
          height: sello.alto,
          opacity: op,
          transform: `scale(${1 + 0.08 * pulso})`,
          filter: 'drop-shadow(0 4px 10px rgba(0,0,0,0.55))',
        }}
      />,
    );
  }

  if (activo) {
    const t = frame - activo.ini;
    const rebote = (p: number, max: number) => {
      const periodo = 2 * max;
      const m = ((p % periodo) + periodo) % periodo;
      return {pos: m <= max ? m : periodo - m, toques: Math.floor(p / max)};
    };
    const bx = rebote(activo.x0 + activo.vx * t, W - activo.ancho);
    const by = rebote(activo.y0 + activo.vy * t, H - activo.alto);
    const img = activo.imgs[(bx.toques + by.toques) % activo.imgs.length];
    const aparece = Math.min(1, t / 8, (activo.fin - frame) / 8);
    elementos.push(
      <AbsoluteFill key="velo" style={{backgroundColor: '#000', opacity: activo.oscuro * aparece}} />,
      <Img
        key="dvd"
        src={archivo(tl, img)}
        style={{
          position: 'absolute',
          left: bx.pos,
          top: by.pos,
          width: activo.ancho,
          height: activo.alto,
          opacity: aparece,
          filter: 'drop-shadow(0 8px 24px rgba(0,0,0,0.6))',
        }}
      />,
    );
  }
  return <>{elementos}</>;
};

/** Una imagen tras otra a pantalla completa, en cortes secos al pulso; tapa el collage mientras dura. */
const Rafaga: React.FC<{tl: Timeline; mo: Rafaga_; frame: number}> = ({tl, mo, frame}) => {
  if (frame >= mo.fin) return null;
  const actual = [...mo.imagenes].reverse().find((im) => im.ini <= frame);
  const siguiente = mo.imagenes.find((im) => im.ini > frame);
  return (
    <AbsoluteFill style={{backgroundColor: frame >= mo.ini ? tl.fondo : 'transparent'}}>
      {actual && frame >= mo.ini ? (
        <Img
          key={actual.id}
          src={archivo(tl, actual.img)}
          style={{
            position: 'absolute',
            left: (tl.ancho - actual.ancho) / 2,
            top: (tl.alto - actual.alto) / 2,
            width: actual.ancho,
            height: actual.alto,
          }}
        />
      ) : null}
      {siguiente ? (
        <Img src={archivo(tl, siguiente.img)} style={{position: 'absolute', width: 1, height: 1, opacity: 0}} />
      ) : null}
    </AbsoluteFill>
  );
};

// ── Utilidades ─────────────────────────────────────────────────────────────

/** Interpolación lineal entre claves [cuadro, ...valores], con búsqueda binaria. */
function claveEn<T extends number[]>(claves: T[], g: number): T {
  if (g <= claves[0][0]) return claves[0];
  const ultima = claves[claves.length - 1];
  if (g >= ultima[0]) return ultima;
  let lo = 0;
  let hi = claves.length - 1;
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1;
    if (claves[mid][0] <= g) lo = mid;
    else hi = mid;
  }
  const a = claves[lo];
  const b = claves[hi];
  const u = (g - a[0]) / (b[0] - a[0]);
  return a.map((v, i) => lerp(v, b[i], u)) as T;
}

const camaraEn = (claves: ClaveCamara[], g: number): ClaveCamara => claveEn(claves, g);
const valorEn = (claves: [number, number][], g: number): number => (claves.length ? claveEn(claves, g)[1] : 1);

/** ¿La pieza cae dentro de la zona centrada en el cuadro, `recorte` veces más grande que él? */
type Caja = Pick<Pieza, 'x' | 'y' | 'ancho' | 'alto'>;

function enCuadro(p: Caja, cx: number, cy: number, s: number, W: number, H: number, recorte = 1): boolean {
  const dx = Math.abs((p.x - cx) * s) - (p.ancho * s) / 2;
  const dy = Math.abs((p.y - cy) * s) - (p.alto * s) / 2;
  return dx < (W / 2) * recorte + 50 && dy < (H / 2) * recorte + 50;
}

/**
 * Bordes que se funden en vez de un rectángulo duro: dos degradados (horizontal y
 * vertical) intersectados. `px` es el ancho del fundido en el espacio del elemento.
 */
function mascara(px: number): CSSProperties {
  if (!px || px < 0.5) return {};
  const tramo = (dir: string) =>
    `linear-gradient(${dir}, transparent, #000 ${px}px, #000 calc(100% - ${px}px), transparent)`;
  const m = `${tramo('to right')}, ${tramo('to bottom')}`;
  return {maskImage: m, WebkitMaskImage: m, maskComposite: 'intersect', WebkitMaskComposite: 'source-in'};
}
