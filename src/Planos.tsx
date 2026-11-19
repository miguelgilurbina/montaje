import type {CSSProperties} from 'react';
import {AbsoluteFill, Easing, Img, interpolate, OffthreadVideo, Sequence, staticFile} from 'remotion';
import {Letrero} from './Letrero';
import type {EfectoPlano, Encuadre, Plano, TextoPlano, Timeline} from './tipos';

/**
 * Modo planos: el video contado plano a plano, como en un guion de documental. Cada plano es una
 * imagen (o un clip) que la cámara recorre de un encuadre a otro, con sus textos en pantalla y unos
 * pocos efectos dibujados sobre la imagen (gris alrededor de una zona, un marcador que resalta, una
 * línea que tacha, islas que faltan, una silueta, una isla dibujada a mano). Los efectos viven en
 * las coordenadas de la imagen: siguen a la cámara. Los textos viven en la pantalla: no se mueven.
 *
 * Lo escribe py/montaje/planos.py desde `planos` de proyecto.json; el sonido ya viene mezclado en
 * una sola pista (`audio` del timeline).
 */

const archivo = (tl: Timeline, ruta: string) => (tl.base ? tl.base + ruta : staticFile(ruta));
const fijo = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const suave = Easing.inOut(Easing.cubic);
const lerp = (a: number, b: number, u: number) => a + (b - a) * u;
const avance = (f: number, ini: number, dura: number) => Math.min(1, Math.max(0, (f - ini) / Math.max(1, dura)));

/** Los colores de las etiquetas de un mapa ilustrado: letra azul noche, borde y alfiler rojo teja. */
const COLOR = {tinta: '#12324f', pin: '#d4492f', etiqueta: 'rgba(255,255,255,0.95)', marcador: '#ffd84a', arena: '#f2d8a2'};
const LETRA = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif";
const SERIF = "Georgia, 'Times New Roman', serif";

export const Planos: React.FC<{tl: Timeline; frame: number}> = ({tl, frame}) => (
  <AbsoluteFill>
    {(tl.planos ?? [])
      .filter((p) => frame >= p.ini && frame < p.fin)
      .map((p) => (
        <UnPlano key={p.id} tl={tl} p={p} f={frame - p.ini} />
      ))}
    {(tl.textos ?? []).map((t, i) => (
      <Texto key={`t-${i}`} t={t} f={frame} W={tl.ancho} H={tl.alto} fps={tl.fps} enPanel={Boolean(tl.base)} subs={Boolean(tl.subtitulos?.length)} />
    ))}
    {(tl.subtitulos ?? [])
      .filter((s) => frame >= s.ini && frame < s.fin)
      .map((s) => (
        <Subtitulo key={s.ini} texto={s.texto} H={tl.alto} />
      ))}
  </AbsoluteFill>
);

/** El subtítulo de la voz: abajo al centro, letra blanca sobre una caja oscura, como los del video del encuentro. */
const Subtitulo: React.FC<{texto: string; H: number}> = ({texto, H}) => {
  const k = H / 1080;
  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 44 * k}}>
      <div
        style={{
          maxWidth: 1240 * k,
          background: 'rgba(10,14,20,0.62)',
          borderRadius: 6 * k,
          padding: `${6 * k}px ${18 * k}px`,
          color: '#ffffff',
          fontFamily: "'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
          fontSize: 38 * k,
          fontWeight: 500,
          lineHeight: 1.25,
          textAlign: 'center',
          whiteSpace: 'pre-line',
        }}
      >
        {texto}
      </div>
    </AbsoluteFill>
  );
};

// ── La cámara ──────────────────────────────────────────────────────────────

/** Escala y centro de un encuadre: `null` es la imagen entera, contenida; un encuadre cubre la pantalla con su ancho. */
function encuadre(e: Encuadre, fw: number, fh: number, W: number, H: number) {
  if (!e) return {s: Math.min(W / fw, H / fh), cx: 0.5, cy: 0.5};
  return {s: W / (e[2] * fw), cx: e[0], cy: e[1]};
}

/** Dónde está la cámara en el cuadro `f` del plano: entre dos encuadres se mueve suave; la escala, en proporción (un acercamiento parejo). */
function camara(p: Plano, f: number, W: number, H: number) {
  const [fw, fh] = p.fuente ?? [W, H];
  const claves = p.camara.length ? p.camara : [{t: 0, e: null}];
  let k = 0;
  while (k < claves.length - 1 && f >= claves[k + 1].t) k++;
  const a = encuadre(claves[k].e, fw, fh, W, H);
  const siguiente = claves[k + 1];
  const b = siguiente ? encuadre(siguiente.e, fw, fh, W, H) : a;
  const u = siguiente ? suave(avance(f, claves[k].t, siguiente.t - claves[k].t)) : 0;
  const s = Math.exp(lerp(Math.log(a.s), Math.log(b.s), u));
  const cx = lerp(a.cx, b.cx, u);
  const cy = lerp(a.cy, b.cy, u);
  return {s, fw, fh, tx: W / 2 - s * cx * fw, ty: H / 2 - s * cy * fh};
}

// ── Un plano ───────────────────────────────────────────────────────────────

const UnPlano: React.FC<{tl: Timeline; p: Plano; f: number}> = ({tl, p, f}) => {
  const W = tl.ancho;
  const H = tl.alto;
  const tr = p.transicion && p.entrada > 0 && f < p.entrada ? entradaDe(p.transicion, suave(avance(f, 0, p.entrada)), W, H) : null;
  const opacidad = tr ? tr.opacidad : p.entrada > 0 ? interpolate(f, [0, p.entrada], [0, 1], fijo) : 1;
  // El que se va cuando el siguiente entra empujando: sale por el otro lado en los mismos cuadros.
  const dura = p.fin - p.ini;
  const sale =
    p.empujada && f >= dura - p.empujada.cuadros
      ? `translate(${(p.empujada.dir[0] * suave(avance(f, dura - p.empujada.cuadros, p.empujada.cuadros)) * W).toFixed(1)}px, ${(p.empujada.dir[1] * suave(avance(f, dura - p.empujada.cuadros, p.empujada.cuadros)) * H).toFixed(1)}px)`
      : undefined;
  const cam = camara(p, f, W, H);
  const efectos = p.efectos ?? [];
  // Gris: el de toda la imagen y el de alrededor de una zona se dibujan igual (la imagen en gris debajo); la zona, a color encima.
  const gris = efectos.reduce((g, e) => (e.tipo === 'gris' || e.tipo === 'gris_fuera' ? Math.max(g, avance(f, e.ini, e.dura)) : g), 0);
  const zonaColor = efectos.find((e): e is Extract<EfectoPlano, {tipo: 'gris_fuera'}> => e.tipo === 'gris_fuera');
  const caja: CSSProperties = {position: 'absolute', left: 0, top: 0, width: cam.fw, height: cam.fh};
  return (
    <>
    <AbsoluteFill style={{opacity: tr?.oculto ? 0 : opacidad, backgroundColor: p.color ?? tl.fondo, overflow: 'hidden', ...(tr?.estilo ?? {}), ...(sale ? {transform: sale} : {})}}>
      {p.img ? (
        <div style={{...caja, transformOrigin: '0 0', transform: `translate(${cam.tx}px, ${cam.ty}px) scale(${cam.s})`}}>
          {p.video ? (
            <Sequence from={p.ini} layout="none">
              <OffthreadVideo src={archivo(tl, p.img)} trimBefore={Math.round(p.video.desde * tl.fps)} muted style={{...caja, filter: gris ? `grayscale(${gris})` : undefined}} />
            </Sequence>
          ) : (
            <Img src={archivo(tl, p.img)} style={{...caja, filter: gris ? `grayscale(${gris})` : undefined}} />
          )}
          {zonaColor && !p.video && gris > 0 ? (
            <Img
              src={archivo(tl, p.img!)}
              style={{
                ...caja,
                clipPath: `ellipse(${((zonaColor.zona[2] - zonaColor.zona[0]) / 2) * cam.fw}px ${((zonaColor.zona[3] - zonaColor.zona[1]) / 2) * cam.fh}px at ${((zonaColor.zona[0] + zonaColor.zona[2]) / 2) * cam.fw}px ${((zonaColor.zona[1] + zonaColor.zona[3]) / 2) * cam.fh}px)`,
              }}
            />
          ) : null}
          <svg width={cam.fw} height={cam.fh} viewBox={`0 0 ${cam.fw} ${cam.fh}`} style={{...caja, overflow: 'visible'}}>
            {efectos.map((e, i) => (
              <Efecto key={i} e={e} f={f} fw={cam.fw} fh={cam.fh} />
            ))}
          </svg>
        </div>
      ) : null}
      {p.velo ? <AbsoluteFill style={{backgroundColor: '#000000', opacity: p.velo}} /> : null}
      {p.rodillo ? <Rodillo lineas={p.rodillo} f={f} dura={p.fin - p.ini} W={W} H={H} oscuro={claroDe(p.color)} /> : null}
      {(p.textos ?? []).map((t, i) => (
        <Texto key={i} t={t} f={f} W={W} H={H} fps={tl.fps} enPanel={Boolean(tl.base)} subs={Boolean(tl.subtitulos?.length)} />
      ))}
    </AbsoluteFill>
    {tr?.encima ?? null}
    </>
  );
};

/**
 * La entrada de un plano con transición, como en la galería (Montaje.tsx, `transicionDe`): `u` es su avance, ya
 * suavizado. Devuelve la opacidad y el estilo del plano en este cuadro, si se esconde (el destello lo destapa en el
 * tope de la luz) y lo que va encima (el fogonazo).
 */
function entradaDe(tr: NonNullable<Plano['transicion']>, u: number, W: number, H: number): {opacidad: number; estilo: CSSProperties; oculto?: boolean; encima?: React.ReactNode} {
  const [dx, dy] = tr.dir;
  const mascara = (m: string): CSSProperties => ({maskImage: m, WebkitMaskImage: m});
  const angulo = dx > 0 ? 90 : dx < 0 ? 270 : dy > 0 ? 180 : 0;
  if (tr.tipo === 'cortina') {
    const borde = 7;
    const q = u * (100 + borde);
    return {opacidad: 1, estilo: mascara(`linear-gradient(${angulo}deg, #000 ${(q - borde).toFixed(2)}%, transparent ${q.toFixed(2)}%)`)};
  }
  if (tr.tipo === 'iris') {
    const [fx, fy] = tr.centro ?? [0.5, 0.5];
    const cx = fx * W;
    const cy = fy * H;
    const lejos = Math.hypot(Math.max(cx, W - cx), Math.max(cy, H - cy));
    const borde = H * 0.05;
    const r = u * (lejos + borde);
    return {opacidad: 1, estilo: mascara(`radial-gradient(circle at ${cx}px ${cy}px, #000 ${Math.max(0, r - borde).toFixed(1)}px, transparent ${r.toFixed(1)}px)`)};
  }
  if (tr.tipo === 'empuje') {
    return {opacidad: 1, estilo: {transform: `translate(${(-dx * (1 - u) * W).toFixed(1)}px, ${(-dy * (1 - u) * H).toFixed(1)}px)`}};
  }
  if (tr.tipo === 'zoom') {
    return {opacidad: u, estilo: {transform: `scale(${(1 + 0.28 * (1 - u)).toFixed(4)})`, filter: `blur(${((1 - u) * H * 0.012).toFixed(1)}px)`}};
  }
  // destello: un fogonazo cálido tapa el plano que se va; el nuevo aparece debajo en el tope de la luz.
  const luz = u < 0.45 ? u / 0.45 : 1 - (u - 0.45) / 0.55;
  return {
    opacidad: 1,
    estilo: {},
    oculto: u < 0.45,
    encima: <AbsoluteFill style={{backgroundColor: '#fff1d0', opacity: Math.pow(Math.max(0, luz), 0.8), mixBlendMode: 'screen', pointerEvents: 'none'}} />,
  };
}

// ── Lo que se dibuja sobre la imagen ───────────────────────────────────────

/** Un contorno de isla hecho a mano: un círculo con el radio que tiembla, siempre igual para la misma semilla. */
function contorno(cx: number, cy: number, rx: number, ry: number, semilla: number, puntos = 28): [number, number][] {
  const azar = (k: number) => {
    const x = Math.sin((k + 1) * 12.9898 + semilla * 78.233) * 43758.5453;
    return x - Math.floor(x);
  };
  return Array.from({length: puntos}, (_, k) => {
    const a = (k / puntos) * Math.PI * 2;
    const r = 0.82 + 0.3 * azar(k) + 0.08 * Math.sin(3 * a + semilla);
    return [cx + Math.cos(a) * rx * r, cy + Math.sin(a) * ry * r];
  });
}

/** El contorno como curva cerrada suave (Catmull-Rom → Bézier) y su largo aproximado. */
function curva(p: [number, number][]): {d: string; largo: number} {
  const n = p.length;
  let d = `M ${p[0][0]} ${p[0][1]}`;
  let largo = 0;
  for (let i = 0; i < n; i++) {
    const [p0, p1, p2, p3] = [p[(i - 1 + n) % n], p[i], p[(i + 1) % n], p[(i + 2) % n]];
    const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
    const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
    d += ` C ${c1[0]} ${c1[1]}, ${c2[0]} ${c2[1]}, ${p2[0]} ${p2[1]}`;
    largo += Math.hypot(p2[0] - p1[0], p2[1] - p1[1]);
  }
  return {d: d + ' Z', largo: largo * 1.04};
}

const Efecto: React.FC<{e: EfectoPlano; f: number; fw: number; fh: number}> = ({e, f, fw, fh}) => {
  if (e.tipo === 'resaltar' || e.tipo === 'tachar') {
    const u = suave(avance(f, e.ini, e.dura));
    if (u <= 0) return null;
    const [x0, y0, x1, y1] = [e.zona[0] * fw, e.zona[1] * fh, e.zona[2] * fw, e.zona[3] * fh];
    if (e.tipo === 'resaltar') {
      return <rect x={x0} y={y0} width={(x1 - x0) * u} height={y1 - y0} rx={(y1 - y0) * 0.12} fill={e.color ?? COLOR.marcador} opacity={0.55} style={{mixBlendMode: 'multiply'}} />;
    }
    const y = (y0 + y1) / 2;
    return <line x1={x0} y1={y} x2={x0 + (x1 - x0) * u} y2={y} stroke={COLOR.pin} strokeWidth={(y1 - y0) * 0.16} strokeLinecap="round" />;
  }
  if (e.tipo === 'islas_fantasma') {
    return (
      <>
        {e.islas.map((isla, i) => {
          const u = suave(avance(f, e.ini + i * e.cada, 18));
          if (u <= 0) return null;
          const rx = (isla.ancho * fw) / 2;
          const ry = rx * 0.62;
          const cx = isla.x * fw;
          const cy = isla.y * fh;
          const {d} = curva(contorno(cx, cy, rx, ry, i + 3));
          const letra = rx * 0.34;
          const ancho = letra * 0.62 * isla.texto.length + letra * 1.6;
          return (
            <g key={i} opacity={u} transform={`translate(${cx} ${cy}) scale(${0.85 + 0.15 * u}) translate(${-cx} ${-cy})`}>
              <path d={d} fill="rgba(255,255,255,0.32)" stroke={COLOR.tinta} strokeWidth={rx * 0.035} strokeDasharray={`${rx * 0.12} ${rx * 0.09}`} />
              <text x={cx} y={cy + ry * 0.12} textAnchor="middle" fontFamily={LETRA} fontWeight={700} fontSize={ry * 0.9} fill={COLOR.tinta} opacity={0.55}>
                ?
              </text>
              <rect x={cx - ancho / 2} y={cy + ry * 1.05} width={ancho} height={letra * 1.7} rx={letra * 0.85} fill={COLOR.etiqueta} stroke={COLOR.pin} strokeWidth={letra * 0.12} />
              <text x={cx} y={cy + ry * 1.05 + letra * 1.18} textAnchor="middle" fontFamily={LETRA} fontSize={letra} fill={COLOR.tinta}>
                {isla.texto}
              </text>
            </g>
          );
        })}
      </>
    );
  }
  if (e.tipo === 'silueta') {
    const u = suave(avance(f, e.ini, e.dura));
    if (u <= 0) return null;
    const h = e.alto * fh;
    const cx = e.x * fw;
    const top = e.y * fh - h / 2;
    const r = h * 0.14;
    const hombro = h * 0.36;
    // Una cabeza y unos hombros, sin rasgos: un cuerpo cualquiera, «sin marcas».
    const cuerpo = `M ${cx - hombro} ${top + h} C ${cx - hombro} ${top + h * 0.55}, ${cx - hombro * 0.55} ${top + h * 0.42}, ${cx} ${top + h * 0.42} C ${cx + hombro * 0.55} ${top + h * 0.42}, ${cx + hombro} ${top + h * 0.55}, ${cx + hombro} ${top + h}`;
    return (
      <g opacity={u * 0.9} fill="none" stroke="#ffffff" strokeWidth={h * 0.012} strokeLinecap="round">
        <circle cx={cx} cy={top + r * 1.1} r={r} />
        <path d={cuerpo} />
      </g>
    );
  }
  if (e.tipo === 'isla_nueva') {
    const rx = (e.ancho * fw) / 2;
    const {d, largo} = curva(contorno(e.x * fw, e.y * fh, rx, rx * 0.6, e.semilla ?? 7, 36));
    const trazo = avance(f, e.ini, e.dura * 0.7);
    const relleno = avance(f, e.ini + e.dura * 0.6, e.dura * 0.4);
    if (trazo <= 0) return null;
    return (
      <path
        d={d}
        fill={COLOR.arena}
        fillOpacity={relleno * 0.85}
        stroke={COLOR.tinta}
        strokeWidth={rx * 0.03}
        strokeLinecap="round"
        strokeDasharray={largo}
        strokeDashoffset={largo * (1 - suave(trazo))}
      />
    );
  }
  return null;
};

// ── Lo que se escribe en la pantalla ───────────────────────────────────────

const Texto: React.FC<{t: TextoPlano; f: number; W: number; H: number; fps: number; enPanel: boolean; subs?: boolean}> = ({t, f, W, H, fps, enPanel, subs}) => {
  // Un estilo de la galería de textos: lo dibuja Letrero, con su entrada y su salida.
  if (t.letrero) {
    return <Letrero e={t.letrero} texto={t.texto} secundario={t.secundario} f={f - t.ini} dura={t.fin - t.ini} fps={fps} W={W} H={H} enPanel={enPanel} />;
  }
  const funde = Math.min(10, Math.max(1, (t.fin - t.ini) / 4));
  const op = interpolate(f, [t.ini, t.ini + funde, t.fin - funde, t.fin], [0, 1, 1, 0], fijo);
  if (op <= 0) return null;
  const k = H / 1080;
  const claro = t.tono === 'claro';
  const sombra = claro ? '0 2px 22px rgba(0,0,0,0.65)' : '0 0 22px rgba(255,255,255,0.95), 0 0 6px rgba(255,255,255,0.9)';
  // Con subtítulos abajo al centro, los rótulos y las citas suben para no pisarlos.
  const abajo = (subs ? 168 : 92) * k;
  if (t.estilo === 'portada') {
    // El título del video: letra negra, grande, en dos filas, que entra con un leve acercamiento.
    const u = interpolate(f, [t.ini, t.ini + 24], [0, 1], fijo);
    return (
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', opacity: op}}>
        <div
          style={{
            maxWidth: 1600 * k,
            textAlign: 'center',
            fontFamily: "'Segoe UI Black', 'Arial Black', 'Segoe UI', sans-serif",
            fontWeight: 900,
            fontSize: 132 * k,
            lineHeight: 1.0,
            letterSpacing: '-0.015em',
            color: claro || t.tono === 'contorno' ? '#ffffff' : COLOR.tinta,
            // contorno: blanca con borde negro (el trazo va detrás del relleno, para que la letra no adelgace).
            ...(t.tono === 'contorno' ? {WebkitTextStroke: `${7 * k}px #000000`, paintOrder: 'stroke fill'} : {}),
            textShadow:
              t.tono === 'contorno'
                ? '0 6px 22px rgba(0,0,0,0.45)'
                : claro
                  ? '0 4px 30px rgba(0,0,0,0.7)'
                  : '0 0 34px rgba(255,255,255,0.98), 0 0 12px rgba(255,255,255,0.95), 0 0 3px rgba(255,255,255,1)',
            transform: `scale(${0.94 + 0.06 * suave(u)})`,
            whiteSpace: 'pre-line',
          }}
        >
          {t.texto}
        </div>
      </AbsoluteFill>
    );
  }
  if (t.estilo === 'titulo' || t.estilo === 'frase') {
    const titulo = t.estilo === 'titulo';
    return (
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', opacity: op}}>
        <div
          style={{
            maxWidth: 1400 * k,
            textAlign: 'center',
            fontFamily: titulo ? LETRA : SERIF,
            fontStyle: titulo ? 'normal' : 'italic',
            fontWeight: titulo ? 650 : 400,
            fontSize: (titulo ? 70 : 60) * k,
            lineHeight: 1.18,
            color: claro ? '#ffffff' : COLOR.tinta,
            textShadow: sombra,
            transform: `translateY(${(1 - op) * 12 * k}px)`,
          }}
        >
          {t.texto}
        </div>
      </AbsoluteFill>
    );
  }
  if (t.estilo === 'rotulo') {
    // Como las etiquetas del mapa: blanca, con borde y alfiler rojo teja.
    return (
      <div style={{position: 'absolute', left: 80 * k, ...(t.lugar === 'arriba' ? {top: 70 * k} : {bottom: abajo}), opacity: op, display: 'flex', alignItems: 'center', gap: 12 * k, maxWidth: 1180 * k}}>
        <svg width={30 * k} height={40 * k} viewBox="0 0 30 40" style={{flex: 'none'}}>
          <path d="M15 1 C7 1 1 7 1 15 C1 26 15 39 15 39 C15 39 29 26 29 15 C29 7 23 1 15 1 Z" fill={COLOR.pin} />
          <circle cx="15" cy="15" r="5.5" fill="#ffffff" />
        </svg>
        <div
          style={{
            background: COLOR.etiqueta,
            border: `${3 * k}px solid ${COLOR.pin}`,
            borderRadius: 999,
            padding: `${10 * k}px ${28 * k}px`,
            fontFamily: LETRA,
            fontSize: 32 * k,
            fontWeight: 500,
            color: COLOR.tinta,
            boxShadow: `0 ${4 * k}px ${18 * k}px rgba(0,0,0,0.18)`,
          }}
        >
          {t.texto}
        </div>
      </div>
    );
  }
  if (t.estilo === 'cita') {
    return (
      <div
        style={{
          position: 'absolute',
          ...(t.lugar === 'arriba' ? {left: 80 * k, top: 70 * k} : {right: 80 * k, bottom: abajo + 4 * k}),
          opacity: op,
          maxWidth: 820 * k,
          background: 'rgba(18,50,79,0.86)',
          color: '#ffffff',
          borderRadius: 6 * k,
          padding: `${8 * k}px ${18 * k}px`,
          fontFamily: LETRA,
          fontSize: 24 * k,
          letterSpacing: '0.01em',
          textAlign: t.lugar === 'arriba' ? 'left' : 'right',
        }}
      >
        {t.texto}
      </div>
    );
  }
  // aviso: lo que falta en un borrador, para que nadie lo confunda con el video terminado.
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', opacity: op}}>
      <div
        style={{
          maxWidth: 1300 * k,
          border: `${3 * k}px dashed #e2a158`,
          borderRadius: 10 * k,
          padding: `${28 * k}px ${40 * k}px`,
          background: 'rgba(7,9,13,0.82)',
          color: '#f3e6cf',
          fontFamily: LETRA,
          fontSize: 38 * k,
          textAlign: 'center',
          lineHeight: 1.3,
        }}
      >
        {t.texto}
      </div>
    </AbsoluteFill>
  );
};

/** Los créditos, de abajo hacia arriba durante todo el plano. Empiezan a media pantalla: diez segundos dan para poco recorrido. */
/** ¿Es claro este color (#rrggbb)? Sobre un fondo claro la letra va oscura. */
const claroDe = (color?: string) => {
  const m = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(color ?? '');
  return m ? 0.2126 * parseInt(m[1], 16) + 0.7152 * parseInt(m[2], 16) + 0.0722 * parseInt(m[3], 16) > 150 : false;
};

const Rodillo: React.FC<{lineas: string[]; f: number; dura: number; W: number; H: number; oscuro?: boolean}> = ({lineas, f, dura, W, H, oscuro}) => {
  const k = H / 1080;
  const tam = 30 * k;
  const porLinea = Math.max(40, Math.floor((1300 * k) / (tam * 0.5)));
  const alto = lineas.reduce((a, l) => a + Math.ceil(l.length / porLinea) * tam * 1.35 + tam * 0.9, 0);
  const y = lerp(H * 0.5, -alto + H * 0.12, f / Math.max(1, dura));
  return (
    <div style={{position: 'absolute', left: (W - 1300 * k) / 2, width: 1300 * k, top: y, textAlign: 'center', fontFamily: LETRA, color: oscuro ? COLOR.tinta : '#ffffff', textShadow: oscuro ? 'none' : '0 1px 8px rgba(0,0,0,0.35)'}}>
      {lineas.map((l, i) => (
        <div key={i} style={{fontSize: tam, lineHeight: 1.35, marginBottom: tam * 0.9, fontWeight: i === 0 ? 600 : 400}}>
          {l}
        </div>
      ))}
    </div>
  );
};
