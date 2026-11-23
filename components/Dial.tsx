'use client';
// Una perilla de la consola. Se gira arrastrando hacia arriba o hacia abajo (con Shift, fino), con la rueda, con las
// flechas (Re Pág y Av Pág saltan, Inicio y Fin van a los extremos); doble clic vuelve al valor de fábrica.
// Las de opciones giran por pasos; las bipolares (de menos a más) llenan el anillo desde el cero, al centro.
// Cada gesto avisa cuándo empieza y cuándo termina: mientras se sostiene, la consola puede grabarlo.
import {useEffect, useRef} from 'react';
import type {Valor} from '@/lib/consola-gl';
import {desdeNormal, normal, type Tipo} from '@/lib/consola-auto';

type Props = {
  nombre: string;
  tipo: Tipo;
  valor: Valor;
  defecto: Valor;
  automatizada: boolean;
  tocada: boolean;
  aprendiendo: boolean;
  atada: boolean;
  onTocar: () => void;
  onCambio: (v: Valor) => void;
  onSoltar: () => void;
  onAprender: () => void;
};

const GIRO = 270; // grados de recorrido, de -135 a 135

function texto(tipo: Tipo, v: Valor): string {
  if (tipo.clase === 'numero') {
    if (typeof v !== 'number') return 'auto';
    if (tipo.entero) return String(v);
    const a = Math.abs(v);
    return a >= 100 ? v.toFixed(0) : a >= 10 ? v.toFixed(1) : v.toFixed(2);
  }
  if (tipo.clase === 'si-no') return v ? 'sí' : 'no';
  return String(v ?? '');
}

function arco(cx: number, cy: number, r: number, a0: number, a1: number): string {
  const p = (a: number) => {
    const rad = ((a - 90) * Math.PI) / 180;
    return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
  };
  const [x0, y0] = p(a0);
  const [x1, y1] = p(a1);
  const grande = Math.abs(a1 - a0) > 180 ? 1 : 0;
  return `M ${x0.toFixed(2)} ${y0.toFixed(2)} A ${r} ${r} 0 ${grande} ${a1 > a0 ? 1 : 0} ${x1.toFixed(2)} ${y1.toFixed(2)}`;
}

export default function Dial(props: Props) {
  const {nombre, tipo, valor, defecto, automatizada, tocada, aprendiendo, atada} = props;
  const caja = useRef<HTMLDivElement>(null);
  const arrastre = useRef<{y: number; n: number} | null>(null);
  const suelta = useRef<number | null>(null);
  // Los avisos van por una referencia: la rueda se escucha fuera de React (para poder frenar el desplazamiento).
  const avisos = useRef(props);
  avisos.current = props;

  const n = normal(tipo, valor);
  const pasos = tipo.clase === 'opcion' ? tipo.opciones.length - 1 : tipo.clase === 'numero' && tipo.entero ? tipo.max - tipo.min : 0;

  // Un gesto corto (rueda, teclado): empieza, cambia, y termina solo si no llega otro en un rato.
  const momento = (v: Valor) => {
    const a = avisos.current;
    if (suelta.current === null) a.onTocar();
    else window.clearTimeout(suelta.current);
    a.onCambio(v);
    suelta.current = window.setTimeout(() => {
      suelta.current = null;
      avisos.current.onSoltar();
    }, 450);
  };

  const mover = (delta: number) => {
    const ahora = normal(tipo, avisos.current.valor);
    const paso = pasos > 0 ? Math.sign(delta) * Math.max(1 / pasos, Math.abs(delta)) : delta;
    momento(desdeNormal(tipo, ahora + paso));
  };

  useEffect(() => {
    const el = caja.current;
    if (!el) return;
    const rueda = (e: WheelEvent) => {
      if (tipo.clase === 'fija') return;
      e.preventDefault();
      const fino = e.shiftKey ? 0.2 : 1;
      mover((e.deltaY < 0 ? 1 : -1) * 0.02 * fino);
    };
    el.addEventListener('wheel', rueda, {passive: false});
    return () => el.removeEventListener('wheel', rueda);
  });

  if (tipo.clase === 'fija') return null;

  if (tipo.clase === 'si-no') {
    return (
      <div className={`dial dial-si-no${automatizada ? ' auto' : ''}${atada ? ' atada' : ''}`} title={nombre}>
        <button
          type="button"
          role="switch"
          aria-checked={Boolean(valor)}
          className={valor ? 'encendido' : ''}
          onClick={() => (aprendiendo ? props.onAprender() : momento(!valor))}
        >
          {valor ? 'sí' : 'no'}
        </button>
        <span className="dial-nombre">{nombre}</span>
      </div>
    );
  }

  const angulo = -GIRO / 2 + n * GIRO;
  const cero = tipo.clase === 'numero' && tipo.bipolar ? -GIRO / 2 + normal(tipo, 0) * GIRO : -GIRO / 2;
  const marcas = tipo.clase === 'opcion' ? tipo.opciones.map((_, i) => -GIRO / 2 + (i / Math.max(1, pasos)) * GIRO) : [];

  return (
    <div
      ref={caja}
      className={`dial${automatizada ? ' auto' : ''}${tocada ? ' tocada' : ''}${aprendiendo ? ' aprendiendo' : ''}${atada ? ' atada' : ''}`}
      role="slider"
      tabIndex={0}
      aria-label={nombre}
      aria-valuemin={0}
      aria-valuemax={tipo.clase === 'opcion' ? tipo.opciones.length - 1 : 100}
      aria-valuenow={tipo.clase === 'opcion' ? Math.round(n * pasos) : Math.round(n * 100)}
      aria-valuetext={`${nombre} ${texto(tipo, valor)}`}
      title={`${nombre}: ${texto(tipo, valor)} · fábrica ${texto(tipo, defecto)}${automatizada ? ' · grabada' : ''}`}
      onPointerDown={(e) => {
        if (aprendiendo) {
          props.onAprender();
          return;
        }
        if (e.button !== 0) return;
        (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
        arrastre.current = {y: e.clientY, n: normal(tipo, valor)};
        props.onTocar();
      }}
      onPointerMove={(e) => {
        const a = arrastre.current;
        if (!a) return;
        const sensible = e.shiftKey ? 900 : 180;
        const nuevo = desdeNormal(tipo, a.n + (a.y - e.clientY) / sensible);
        if (nuevo !== avisos.current.valor) props.onCambio(nuevo);
      }}
      onPointerUp={(e) => {
        if (!arrastre.current) return;
        arrastre.current = null;
        (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
        props.onSoltar();
      }}
      onPointerCancel={() => {
        if (arrastre.current) {
          arrastre.current = null;
          props.onSoltar();
        }
      }}
      onDoubleClick={() => momento(defecto)}
      onKeyDown={(e) => {
        const fino = e.shiftKey ? 0.2 : 1;
        const paso = 0.01 * fino;
        if (e.key === 'ArrowUp' || e.key === 'ArrowRight') mover(paso);
        else if (e.key === 'ArrowDown' || e.key === 'ArrowLeft') mover(-paso);
        else if (e.key === 'PageUp') mover(0.1);
        else if (e.key === 'PageDown') mover(-0.1);
        else if (e.key === 'Home') momento(desdeNormal(tipo, 0));
        else if (e.key === 'End') momento(desdeNormal(tipo, 1));
        else return;
        e.preventDefault();
        e.stopPropagation();
      }}
    >
      <svg viewBox="0 0 48 48" width="48" height="48" aria-hidden="true">
        <path d={arco(24, 24, 19, -GIRO / 2, GIRO / 2)} className="dial-pista" />
        {Math.abs(angulo - cero) > 0.5 ? <path d={arco(24, 24, 19, Math.min(cero, angulo), Math.max(cero, angulo))} className="dial-lleno" /> : null}
        {marcas.map((a) => {
          const rad = ((a - 90) * Math.PI) / 180;
          return <circle key={a} cx={24 + 22.5 * Math.cos(rad)} cy={24 + 22.5 * Math.sin(rad)} r="0.9" className="dial-marca" />;
        })}
        <circle cx="24" cy="24" r="13" className="dial-cuerpo" />
        <line
          x1={24 + 5 * Math.cos(((angulo - 90) * Math.PI) / 180)}
          y1={24 + 5 * Math.sin(((angulo - 90) * Math.PI) / 180)}
          x2={24 + 12 * Math.cos(((angulo - 90) * Math.PI) / 180)}
          y2={24 + 12 * Math.sin(((angulo - 90) * Math.PI) / 180)}
          className="dial-aguja"
        />
        {automatizada ? <circle cx="40" cy="42" r="2.6" className="dial-grabada" /> : null}
      </svg>
      <span className="dial-nombre">{nombre}</span>
      <span className="dial-valor">{texto(tipo, valor)}</span>
    </div>
  );
}
