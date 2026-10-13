'use client';

import {useEffect, useRef, useState} from 'react';
import type {Musica} from '@/lib/proyectos';
import {MOMENTOS, type TipoMomento} from '@/lib/vocabulario';

export type MomentoCfg = {compas: number; tipo: string; compases?: number; por_compas?: number; [k: string]: unknown};
export type SalvaCfg = {compas: number; compases?: number; [k: string]: unknown};
export type Seleccion = {lista: 'momentos' | 'salvapantallas'; i: number} | null;

const ALTO = 152;
const ALTO_CURVA = 70;
const Y_FILA = 80;
const ALTO_FILA = 32;

type Props = {
  musica: Musica | null;
  duracion: number;
  fps: number;
  frame: number;
  momentos: MomentoCfg[];
  salvapantallas: SalvaCfg[];
  seleccion: Seleccion;
  onBuscar: (segundos: number) => void;
  onSeleccionar: (sel: Seleccion) => void;
  onAgregar: (compas: number, tipo: TipoMomento) => void;
  onMover: (sel: Seleccion, compas: number) => void;
};

/**
 * La canción y la edición en una tira. Arriba, la energía por golpe y el cabezal
 * (clic o arrastre para ir a ese punto). Abajo, una celda por compás, numerada
 * como en proyecto.json: clic en una vacía agrega un momento; clic en uno lo
 * elige; arrastrarlo lo mueve de compás.
 */
export default function Tira(p: Props) {
  const caja = useRef<HTMLDivElement>(null);
  const [W, setW] = useState(1000);
  const [menu, setMenu] = useState<{compas: number; x: number} | null>(null);
  const [arrastre, setArrastre] = useState<{sel: Seleccion; x0: number; compas: number; movido: boolean} | null>(null);

  useEffect(() => {
    const el = caja.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setW(el.clientWidth || 1000));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const {musica, duracion, fps, frame} = p;
  const inicios = musica?.primeros_tiempos ?? [];
  const limites = [...inicios, duracion];
  const x = (s: number) => (s / duracion) * W;
  const segundosEn = (clientX: number, el: Element) => {
    const r = el.getBoundingClientRect();
    return Math.max(0, Math.min(duracion, ((clientX - r.left) / r.width) * duracion));
  };
  const compasEn = (s: number) => Math.max(0, inicios.filter((t) => t <= s + 1e-6).length - 1);

  // Qué compases ya tienen algo: no se agrega ni se mueve encima.
  const ocupado = new Map<number, Seleccion>();
  p.momentos.forEach((m, i) => {
    for (let k = 0; k < (m.compases ?? 1); k++) ocupado.set(m.compas + k, {lista: 'momentos', i});
  });
  p.salvapantallas.forEach((s, i) => {
    for (let k = 0; k < (s.compases ?? 1); k++) ocupado.set(s.compas + k, {lista: 'salvapantallas', i});
  });
  const mismo = (a: Seleccion, b: Seleccion) => Boolean(a && b && a.lista === b.lista && a.i === b.i);
  const libre = (desde: number, largo: number, salvo: Seleccion) => {
    for (let k = 0; k < largo; k++) {
      const quien = ocupado.get(desde + k);
      if (quien && !mismo(quien, salvo)) return false;
    }
    return desde + largo <= inicios.length;
  };

  const curva = musica
    ? ['0,' + ALTO_CURVA, ...musica.beats.map((b, i) => `${x(b).toFixed(1)},${(ALTO_CURVA - musica.energia[i] * ALTO_CURVA).toFixed(1)}`), `${x(duracion).toFixed(1)},${ALTO_CURVA}`].join(' ')
    : '';

  const bloques = [
    ...p.momentos.map((m, i) => ({sel: {lista: 'momentos', i} as Seleccion, tipo: m.tipo as TipoMomento, compas: m.compas, largo: m.compases ?? 1, rotulo: `${MOMENTOS[m.tipo as TipoMomento]?.letra ?? '?'}${m.por_compas ?? ''}`})),
    ...p.salvapantallas.map((s, i) => ({sel: {lista: 'salvapantallas', i} as Seleccion, tipo: 'salvapantallas' as TipoMomento, compas: s.compas, largo: s.compases ?? 1, rotulo: 'S'})),
  ];
  const celdaX = (c: number) => x(limites[Math.min(c, limites.length - 1)]);
  const anchoCeldas = (c: number, n: number) => celdaX(Math.min(c + n, limites.length - 1)) - celdaX(c);
  const cadaCuantos = inicios.length && W / inicios.length < 22 ? 2 : 1;

  return (
    <div ref={caja} className="tira">
      <svg
        width={W}
        height={ALTO}
        viewBox={`0 0 ${W} ${ALTO}`}
        onPointerDown={(e) => {
          const r = e.currentTarget.getBoundingClientRect();
          if (e.clientY - r.top >= Y_FILA) return; // la fila de compases tiene sus propios manejadores
          setMenu(null);
          e.currentTarget.setPointerCapture(e.pointerId);
          p.onBuscar(segundosEn(e.clientX, e.currentTarget));
        }}
        onPointerMove={(e) => {
          if (arrastre) {
            const c = compasEn(segundosEn(e.clientX, e.currentTarget));
            if (c !== arrastre.compas || Math.abs(e.clientX - arrastre.x0) > 3) setArrastre({...arrastre, compas: c, movido: true});
            return;
          }
          if (e.buttons === 1 && e.currentTarget.hasPointerCapture(e.pointerId)) p.onBuscar(segundosEn(e.clientX, e.currentTarget));
        }}
        onPointerUp={(e) => {
          if (!arrastre) return;
          const c = compasEn(segundosEn(e.clientX, e.currentTarget));
          if (arrastre.movido) p.onMover(arrastre.sel, c);
          else p.onSeleccionar(arrastre.sel);
          setArrastre(null);
        }}
      >
        <rect x={0} y={0} width={W} height={ALTO} fill="#07090d" />
        {musica ? <polygon points={curva} fill="#3a4b61" /> : null}
        {inicios.map((t, i) => (
          <line key={`l${i}`} x1={x(t)} x2={x(t)} y1={0} y2={ALTO} stroke={i % 4 === 0 ? '#5a6d85' : '#1f2c3e'} strokeWidth={1} />
        ))}
        {!musica ? (
          <text x={W / 2} y={ALTO_CURVA / 2} fill="#7e93aa" fontSize={12} textAnchor="middle">
            sin análisis de música: corre «Analizar música» para ver los compases
          </text>
        ) : null}

        {/* Las celdas: una por compás. */}
        {inicios.map((t, c) => {
          const quien = ocupado.get(c);
          const destino = arrastre?.movido && arrastre.compas === c;
          return (
            <g key={`c${c}`}>
              <rect
                className={quien ? 'celda llena' : 'celda'}
                x={celdaX(c) + 0.5}
                y={Y_FILA}
                width={Math.max(1, anchoCeldas(c, 1) - 1)}
                height={ALTO_FILA}
                fill={destino ? 'rgba(230,180,60,0.25)' : 'transparent'}
                onPointerDown={(e) => {
                  e.stopPropagation();
                  if (quien) return;
                  setMenu(menu?.compas === c ? null : {compas: c, x: celdaX(c)});
                  p.onSeleccionar(null);
                }}
              />
              {c % cadaCuantos === 0 ? (
                <text x={celdaX(c) + 3} y={ALTO - 5} fill="#7e93aa" fontSize={10} fontFamily="ui-monospace, monospace" pointerEvents="none">
                  {c}
                </text>
              ) : null}
            </g>
          );
        })}

        {/* Los momentos y el salvapantallas, encima de sus celdas. */}
        {bloques.map((b) => {
          const elegido = mismo(b.sel, p.seleccion);
          const enArrastre = arrastre?.movido && mismo(b.sel, arrastre.sel);
          const c = enArrastre ? arrastre!.compas : b.compas;
          const ancho = Math.max(3, anchoCeldas(c, b.largo) - 2);
          return (
            <g
              key={`${b.sel!.lista}-${b.sel!.i}`}
              className="bloque"
              opacity={enArrastre && !libre(c, b.largo, b.sel) ? 0.35 : 1}
              onPointerDown={(e) => {
                e.stopPropagation();
                setMenu(null);
                (e.currentTarget as SVGGElement).setPointerCapture?.(e.pointerId);
                setArrastre({sel: b.sel, x0: e.clientX, compas: b.compas, movido: false});
              }}
            >
              <rect x={celdaX(c) + 1} y={Y_FILA + 3} width={ancho} height={ALTO_FILA - 6} rx={3} fill={MOMENTOS[b.tipo]?.color ?? '#eee6d4'} stroke={elegido ? '#e6b43c' : 'none'} strokeWidth={2}>
                <title>{MOMENTOS[b.tipo]?.nombre ?? b.tipo}</title>
              </rect>
              {ancho > 16 ? (
                <text x={celdaX(c) + 1 + ancho / 2} y={Y_FILA + ALTO_FILA / 2 + 4} fill="#eee6d4" fontSize={11} fontWeight={600} textAnchor="middle" pointerEvents="none" fontFamily="ui-monospace, monospace">
                  {b.rotulo}
                </text>
              ) : null}
            </g>
          );
        })}

        <line x1={x(frame / fps)} x2={x(frame / fps)} y1={0} y2={Y_FILA} stroke="#e6b43c" strokeWidth={2} pointerEvents="none" />
      </svg>

      {menu ? (
        <div className="menu-momentos" style={{left: Math.min(menu.x, W - 190)}}>
          <div className="dato">compás {menu.compas}</div>
          {(Object.keys(MOMENTOS) as TipoMomento[]).map((t) => (
            <button
              key={t}
              title={MOMENTOS[t].frase}
              onClick={() => {
                p.onAgregar(menu.compas, t);
                setMenu(null);
              }}
            >
              <span className="punto" style={{background: MOMENTOS[t].color}} />
              {MOMENTOS[t].nombre}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
