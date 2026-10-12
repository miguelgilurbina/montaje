import type {CSSProperties} from 'react';
import {
  AbsoluteFill,
  Easing,
  Html5Audio,
  Img,
  interpolate,
  OffthreadVideo,
  Sequence,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import type {Capa, ClaveCamara, Eco, Momento, Pieza, Timeline} from './tipos';

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

  return (
    <AbsoluteFill style={{backgroundColor: tl.fondo, isolation: 'isolate', overflow: 'hidden'}}>
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
      {tl.logo ? <LogoCuriana tl={tl} frame={frame} /> : null}
      <Audio tl={tl} />
    </AbsoluteFill>
  );
};

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
  if (c.vuelo && tl.mural && tl.camara && frame >= c.vuelo.desde) {
    return <ImagenEnVuelo c={c} frame={frame} tl={tl} />;
  }
  // Con vuelo, el zoom y la deriva se completan al despegar, para que el vuelo arranque sin salto.
  const finMovimiento = c.vuelo ? c.vuelo.desde : c.fin;
  const t = avance(frame, c.ini, finMovimiento);

  const alEntrar = interpolate(frame, [c.ini, c.ini + Math.max(1, c.entrada)], [0, 1], {...fijo, easing: suave});
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
