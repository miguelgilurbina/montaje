'use client';

import {useRouter} from 'next/navigation';
import {useState} from 'react';

const BOTONES = [
  {estado: 'aprobado', texto: 'sí'},
  {estado: 'a medias', texto: 'a medias'},
  {estado: 'rechazado', texto: 'no'},
] as const;

/**
 * El veredicto, en la misma tarjeta: Miguel mira la muestra, escribe (si quiere) lo
 * que le pareció y aprieta sí, a medias o no. Se guarda en el archivo del estilo y,
 * si hay palabras, también en el registro. «deshacer» lo devuelve a propuesta.
 */
export default function Veredicto({id, estado}: {id: string; estado: string}) {
  const router = useRouter();
  const [cita, setCita] = useState('');
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState('');

  async function dar(nuevo: string) {
    setOcupado(true);
    setError('');
    try {
      const r = await fetch(`/api/estilos/${encodeURIComponent(id)}`, {
        method: 'POST',
        headers: {'content-type': 'application/json'},
        body: JSON.stringify({estado: nuevo, cita}),
      });
      if (!r.ok) throw new Error(((await r.json().catch(() => null)) as {error?: string} | null)?.error ?? `error ${r.status}`);
      setCita('');
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setOcupado(false);
    }
  }

  return (
    <div className="veredicto">
      <input
        type="text"
        value={cita}
        onChange={(e) => setCita(e.target.value)}
        placeholder="qué te pareció (opcional, con tus palabras)"
        aria-label={`Qué te pareció ${id}`}
        disabled={ocupado}
      />
      <div className="botones">
        {BOTONES.map((b) => (
          <button
            key={b.estado}
            type="button"
            className={`v-${b.estado.replace(' ', '-')}${estado === b.estado ? ' activo' : ''}`}
            onClick={() => dar(b.estado)}
            disabled={ocupado}
          >
            {b.texto}
          </button>
        ))}
        {estado !== 'propuesta' && estado !== 'pedido' ? (
          <button type="button" className="v-deshacer" onClick={() => dar('propuesta')} disabled={ocupado} title="Vuelve a «propuesta»; las palabras ya anotadas quedan">
            deshacer
          </button>
        ) : null}
      </div>
      {error ? <p className="dato error">{error}</p> : null}
    </div>
  );
}
