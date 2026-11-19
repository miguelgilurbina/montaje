'use client';

import {useRouter} from 'next/navigation';
import {useCallback, useEffect, useRef, useState} from 'react';

export type Lado = {id: string; nombre: string; estado: string; frase: string; url: string; costo: number | null};

/**
 * Dos muestras del probador lado a lado y una sola pregunta: ¿cuál? Las dos suenan la misma
 * canción y empiezan con el mismo clip, así que corren sincronizadas: lo único distinto es el
 * estilo. Se elige con un clic (o con las flechas: ← la de la izquierda, → la de la derecha,
 * ↓ iguales) y viene otro par de la misma familia.
 */
export default function Comparador({a, b, siguiente}: {a: Lado; b: Lado; siguiente: string}) {
  const router = useRouter();
  const va = useRef<HTMLVideoElement>(null);
  const vb = useRef<HTMLVideoElement>(null);
  const [andando, setAndando] = useState(false);
  const [suena, setSuena] = useState<'a' | 'b'>('a');
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState('');

  const tocar = useCallback(() => {
    const [x, y] = [va.current, vb.current];
    if (!x || !y) return;
    if (x.paused) {
      y.currentTime = x.currentTime;
      void x.play();
      void y.play();
      setAndando(true);
    } else {
      x.pause();
      y.pause();
      setAndando(false);
    }
  }, []);

  // La de la derecha sigue a la de la izquierda: si se separan (un salto, la vuelta del bucle), se alinea.
  function seguir() {
    const [x, y] = [va.current, vb.current];
    if (x && y && Math.abs(x.currentTime - y.currentTime) > 0.08) y.currentTime = x.currentTime;
  }

  const elegir = useCallback(
    async (gana: string) => {
      setOcupado(true);
      setError('');
      try {
        const r = await fetch('/api/comparar', {method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify({a: a.id, b: b.id, gana})});
        if (!r.ok) throw new Error(((await r.json().catch(() => null)) as {error?: string} | null)?.error ?? `error ${r.status}`);
        router.push(`${siguiente}&n=${Date.now()}`);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        setOcupado(false);
      }
    },
    [a.id, b.id, router, siguiente],
  );

  useEffect(() => {
    function tecla(e: KeyboardEvent) {
      if (ocupado || e.target instanceof HTMLInputElement) return;
      if (e.key === 'ArrowLeft') void elegir(a.id);
      else if (e.key === 'ArrowRight') void elegir(b.id);
      else if (e.key === 'ArrowDown') void elegir('igual');
      else if (e.key === ' ') {
        e.preventDefault();
        tocar();
      } else return;
    }
    window.addEventListener('keydown', tecla);
    return () => window.removeEventListener('keydown', tecla);
  }, [a.id, b.id, elegir, ocupado, tocar]);

  const lado = (l: Lado, k: 'a' | 'b', ref: React.RefObject<HTMLVideoElement | null>) => (
    <figure className="lado">
      <div className="pantalla">
        <video ref={ref} src={`${l.url}#t=0.5`} loop playsInline preload="auto" muted={suena !== k} onTimeUpdate={k === 'a' ? seguir : undefined} />
      </div>
      <figcaption>
        <strong>{l.nombre}</strong> <span className="dato">{l.estado}{l.costo ? ` · dibujo ×${l.costo.toLocaleString('es')}` : ''}</span>
        <p>{l.frase}</p>
      </figcaption>
      <button type="button" className="elegir" onClick={() => void elegir(l.id)} disabled={ocupado}>
        {k === 'a' ? '← me quedo con esta' : 'me quedo con esta →'}
      </button>
    </figure>
  );

  return (
    <div className="comparador">
      <div className="lados">
        {lado(a, 'a', va)}
        {lado(b, 'b', vb)}
      </div>
      <div className="mando">
        <button type="button" onClick={tocar}>{andando ? 'pausa' : 'ver las dos'}</button>
        <button type="button" onClick={() => setSuena(suena === 'a' ? 'b' : 'a')} title="Las dos suenan igual; cambia sólo de cuál sale el sonido">
          sonido: {suena === 'a' ? 'izquierda' : 'derecha'}
        </button>
        <button type="button" onClick={() => void elegir('igual')} disabled={ocupado}>
          ↓ iguales
        </button>
        {/* La hora va en la dirección para que el servidor elija otro par; se calcula al apretar (al dibujar no coincidiría con la del servidor). */}
        <button type="button" className="otro" onClick={() => router.push(`${siguiente}&n=${Date.now()}`)} disabled={ocupado}>
          otro par sin elegir
        </button>
      </div>
      {error ? <p className="dato error">{error}</p> : null}
    </div>
  );
}
