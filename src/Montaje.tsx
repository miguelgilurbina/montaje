import type {CSSProperties} from 'react';
import {
  AbsoluteFill,
  Easing,
  Html5Audio,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import type {Capa, Timeline} from './tipos';

/** Cuadros antes de su entrada en que la imagen ya está montada (invisible), para que el Studio la tenga cargada. */
const PRECARGA = 20;

const fijo = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const suave = Easing.inOut(Easing.quad);

export const Montaje: React.FC<Timeline> = (tl) => {
  const frame = useCurrentFrame();
  const visibles = tl.capas.filter((c) => frame >= c.ini - PRECARGA && frame < c.fin);

  return (
    <AbsoluteFill style={{backgroundColor: tl.fondo, isolation: 'isolate', overflow: 'hidden'}}>
      {visibles.map((c) => (
        <CapaImagen key={c.id} c={c} frame={frame} />
      ))}
      {tl.audio ? (
        <Html5Audio src={staticFile(tl.audio.src)} trimBefore={Math.round(tl.audio.desde * tl.fps)} />
      ) : null}
    </AbsoluteFill>
  );
};

const CapaImagen: React.FC<{c: Capa; frame: number}> = ({c, frame}) => {
  const vida = Math.max(1, c.fin - c.ini);
  const t = Math.min(1, Math.max(0, (frame - c.ini) / vida));

  const alEntrar = interpolate(frame, [c.ini, c.ini + c.entrada], [0, 1], {...fijo, easing: suave});
  const alSalir = interpolate(frame, [c.fin - c.salida, c.fin], [1, 0], {...fijo, easing: suave});
  const opacidad = frame < c.ini ? 0 : c.opacidad * Math.min(alEntrar, alSalir);

  const escala = c.zoom[0] + (c.zoom[1] - c.zoom[0]) * t;
  const estilo: CSSProperties = {
    position: 'absolute',
    left: c.x - c.ancho / 2,
    top: c.y - c.alto / 2,
    width: c.ancho,
    height: c.alto,
    opacity: opacidad,
    transform: `translate(${c.deriva[0] * t}px, ${c.deriva[1] * t}px) scale(${escala})`,
    mixBlendMode: c.mezcla as CSSProperties['mixBlendMode'],
    ...mascaraDeBorde(c),
  };

  return <Img src={staticFile(c.img)} style={estilo} />;
};

/**
 * Bordes que se funden en vez de un rectángulo duro: dos degradados (horizontal y
 * vertical) intersectados. El ancho del fundido va en px sobre el lado menor, para
 * que una panorámica no quede con más difuminado a los lados que arriba.
 */
function mascaraDeBorde(c: Capa): CSSProperties {
  if (!c.borde) return {};
  const px = Math.round(c.borde * Math.min(c.ancho, c.alto));
  const tramo = (dir: string) =>
    `linear-gradient(${dir}, transparent, #000 ${px}px, #000 calc(100% - ${px}px), transparent)`;
  const mascara = `${tramo('to right')}, ${tramo('to bottom')}`;
  return {
    maskImage: mascara,
    WebkitMaskImage: mascara,
    maskComposite: 'intersect',
    WebkitMaskComposite: 'source-in',
  };
}
