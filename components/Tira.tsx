'use client';

import {useEffect, useRef, useState} from 'react';
import type {Musica} from '@/lib/proyectos';
import type {Timeline} from '@/src/tipos';

/** Los colores de las tintas del arte, uno por tipo de momento. */
const COLOR: Record<string, string> = {
  destacado: '#b64924',
  rafaga: '#c36712',
  barrido: '#2154c5',
  video: '#26396a',
  salvapantallas: '#7e93aa',
};
const ALTO = 112;
const ALTO_CURVA = 68;
const Y_MOMENTOS = 80;

/**
 * La canción y la edición en una tira: la energía por golpe, los compases
 * numerados (como se nombran en proyecto.json), los momentos y el salvapantallas,
 * y el cabezal. Clic o arrastre para ir a ese punto del video.
 */
export default function Tira({musica, tl, frame, onBuscar}: {musica: Musica | null; tl: Timeline; frame: number; onBuscar: (segundos: number) => void}) {
  const caja = useRef<HTMLDivElement>(null);
  const [W, setW] = useState(1000);
  useEffect(() => {
    const el = caja.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setW(el.clientWidth || 1000));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const dur = tl.duracion / tl.fps;
  const x = (s: number) => (s / dur) * W;
  const buscar = (e: React.PointerEvent<SVGSVGElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    onBuscar(Math.max(0, Math.min(dur, ((e.clientX - r.left) / r.width) * dur)));
  };

  const curva = musica
    ? ['0,' + ALTO_CURVA, ...musica.beats.map((b, i) => `${x(b).toFixed(1)},${(ALTO_CURVA - musica.energia[i] * ALTO_CURVA).toFixed(1)}`), `${x(dur).toFixed(1)},${ALTO_CURVA}`].join(' ')
    : '';
  const momentos = [
    ...(tl.momentos ?? []).map((mo) => ({tipo: mo.tipo, ini: mo.ini, fin: mo.fin})),
    ...(tl.logo?.salvapantallas ?? []).map((s) => ({tipo: 'salvapantallas', ini: s.ini, fin: s.fin})),
  ];

  return (
    <div ref={caja} className="tira">
      <svg
        width={W}
        height={ALTO}
        viewBox={`0 0 ${W} ${ALTO}`}
        onPointerDown={(e) => {
          e.currentTarget.setPointerCapture(e.pointerId);
          buscar(e);
        }}
        onPointerMove={(e) => e.buttons === 1 && buscar(e)}
      >
        <rect x={0} y={0} width={W} height={ALTO} fill="#07090d" />
        {musica ? <polygon points={curva} fill="#3a4b61" /> : null}
        {musica?.primeros_tiempos.map((t, i) => (
          <g key={i}>
            <line x1={x(t)} x2={x(t)} y1={0} y2={ALTO} stroke={i % 4 === 0 ? '#5a6d85' : '#1f2c3e'} strokeWidth={1} />
            {i % 2 === 0 ? (
              <text x={x(t) + 3} y={ALTO - 4} fill="#7e93aa" fontSize={10} fontFamily="ui-monospace, monospace">
                {i}
              </text>
            ) : null}
          </g>
        ))}
        {momentos.map((m, i) => (
          <rect key={i} x={x(m.ini / tl.fps)} y={Y_MOMENTOS} width={Math.max(2, x((m.fin - m.ini) / tl.fps))} height={12} fill={COLOR[m.tipo] ?? '#eee6d4'} rx={2}>
            <title>{m.tipo}</title>
          </rect>
        ))}
        <line x1={x(frame / tl.fps)} x2={x(frame / tl.fps)} y1={0} y2={ALTO} stroke="#e6b43c" strokeWidth={2} />
      </svg>
    </div>
  );
}
