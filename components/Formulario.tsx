'use client';

import {useEffect, useState} from 'react';
import {formatear, obtener, poner, type Cfg} from '@/lib/json';
import {ESQUINAS, FORMATOS, MODOS, PARAMETROS, VERSIONES_LOGO, type Modo, type Parametro} from '@/lib/vocabulario';

const mmss = (s: number) => `${Math.floor(s / 60)}:${(s % 60).toFixed(2).padStart(5, '0')}`;

/** Una perilla del montaje: su nombre, qué hace, y el control que corresponde a su tipo. */
function Perilla({prm, valor, cambiado, onCambiar}: {prm: Parametro; valor: unknown; cambiado: boolean; onCambiar: (v: unknown) => void}) {
  let control: React.ReactNode;
  if (prm.tipo === 'numero') {
    const v = typeof valor === 'number' ? valor : Number(prm.defecto);
    control = (
      <>
        <input type="range" min={prm.min} max={prm.max} step={prm.paso} value={v} onChange={(e) => onCambiar(Number(e.target.value))} />
        <input type="number" min={prm.min} max={prm.max} step={prm.paso} value={v} onChange={(e) => onCambiar(Number(e.target.value))} />
      </>
    );
  } else if (prm.tipo === 'entero') {
    const v = typeof valor === 'number' ? valor : Number(prm.defecto);
    control = (
      <>
        <input type="number" min={prm.min} max={prm.max} step={1} value={v} onChange={(e) => onCambiar(Math.round(Number(e.target.value)))} />
        {prm.clave === 'semilla' ? (
          <button title="Otra semilla al azar" onClick={() => onCambiar(Math.floor(Math.random() * 1000))}>
            🎲
          </button>
        ) : null}
      </>
    );
  } else if (prm.tipo === 'par' || prm.tipo === 'trio') {
    const defecto = prm.defecto as number[];
    const v = Array.isArray(valor) && valor.length === defecto.length ? (valor as number[]) : defecto;
    control = (
      <div className="partes">
        {v.map((x, i) => (
          <label key={i}>
            <span className="dato">{prm.partes?.[i]}</span>
            <input
              type="number"
              min={prm.min}
              max={prm.max}
              step={prm.paso}
              value={x}
              onChange={(e) => {
                const nuevo = [...v];
                nuevo[i] = Number(e.target.value);
                onCambiar(nuevo);
              }}
            />
          </label>
        ))}
      </div>
    );
  } else if (prm.tipo === 'bool') {
    control = <input type="checkbox" checked={typeof valor === 'boolean' ? valor : Boolean(prm.defecto)} onChange={(e) => onCambiar(e.target.checked)} />;
  } else {
    control = (
      <select value={typeof valor === 'string' ? valor : String(prm.defecto)} onChange={(e) => onCambiar(e.target.value)}>
        {prm.opciones?.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    );
  }
  return (
    <div className={`perilla ${cambiado ? 'cambiada' : ''}`}>
      <div className="perilla-nombre">
        <b>{prm.nombre}</b>
        {cambiado ? (
          <button className="quitar" title="Volver al valor por defecto" onClick={() => onCambiar(undefined)}>
            ×
          </button>
        ) : null}
      </div>
      <div className="frase">{prm.frase}</div>
      <div className="control">{control}</div>
    </div>
  );
}

/** proyecto.json como preguntas: la canción, el formato, el montaje, la marca; y el JSON, plegado, para lo demás. */
export default function Formulario({cfg, onCambiar}: {cfg: Cfg; onCambiar: (c: Cfg) => void}) {
  const pon = (ruta: string[], v: unknown) => onCambiar(poner(cfg, ruta, v));
  const modo = ((obtener(cfg, ['montaje', 'modo']) as string) || 'collage') as Modo;
  const tramo = Array.isArray(cfg.tramo) ? (cfg.tramo as number[]) : null;
  const fundido = Array.isArray(cfg.fundido_audio) ? (cfg.fundido_audio as number[]) : [0, 0];
  const fase = obtener(cfg, ['fase_compas']);
  const salida = (cfg.salida ?? {}) as Record<string, unknown>;
  const ancho = Number(salida.ancho ?? 1920);
  const alto = Number(salida.alto ?? 1080);
  const sello = obtener(cfg, ['logo', 'sello']) as Record<string, unknown> | undefined;

  // El JSON crudo: se escribe cuando el formulario cambia, y vuelve al formulario cuando se edita y es válido.
  const [texto, setTexto] = useState(() => formatear(cfg));
  const [editando, setEditando] = useState(false);
  const [errorJson, setErrorJson] = useState<string | null>(null);
  useEffect(() => {
    if (!editando) setTexto(formatear(cfg));
  }, [cfg, editando]);

  return (
    <div className="formulario">
      <details open className="seccion">
        <summary>La canción</summary>
        <label className="campo">
          <span>Archivo (dentro de la biblioteca)</span>
          <input value={String(cfg.musica ?? '')} onChange={(e) => pon(['musica'], e.target.value)} placeholder="audio/cancion.mp3" />
        </label>
        <label className="campo casilla">
          <input type="checkbox" checked={Boolean(tramo)} onChange={(e) => pon(['tramo'], e.target.checked ? [0, 60] : undefined)} />
          <span>Sólo un tramo de la canción</span>
        </label>
        {tramo ? (
          <div className="campo">
            <span>
              Desde y hasta, en segundos ({mmss(tramo[0])} – {mmss(tramo[1])})
            </span>
            <div className="partes">
              <input type="number" min={0} step={0.01} value={tramo[0]} onChange={(e) => pon(['tramo'], [Number(e.target.value), tramo[1]])} />
              <input type="number" min={0} step={0.01} value={tramo[1]} onChange={(e) => pon(['tramo'], [tramo[0], Number(e.target.value)])} />
            </div>
          </div>
        ) : null}
        <div className="campo">
          <span>El «uno» del compás</span>
          <div className="opciones">
            <button className={fase === undefined ? 'activo' : ''} onClick={() => pon(['fase_compas'], undefined)} title="Lo detecta el análisis (falla con tramos cortos)">
              auto
            </button>
            {[0, 1, 2, 3].map((f) => (
              <button key={f} className={fase === f ? 'activo' : ''} onClick={() => pon(['fase_compas'], f)}>
                {f}
              </button>
            ))}
          </div>
          <div className="frase">Qué golpe es el primero del compás. Si los cortes te suenan corridos, prueba otro.</div>
        </div>
        <div className="campo">
          <span>Fundidos de audio (segundos)</span>
          <div className="partes">
            <label>
              <span className="dato">entrada</span>
              <input type="number" min={0} step={0.05} value={fundido[0]} onChange={(e) => pon(['fundido_audio'], [Number(e.target.value), fundido[1]])} />
            </label>
            <label>
              <span className="dato">salida</span>
              <input type="number" min={0} step={0.05} value={fundido[1]} onChange={(e) => pon(['fundido_audio'], [fundido[0], Number(e.target.value)])} />
            </label>
          </div>
        </div>
      </details>

      <details className="seccion">
        <summary>El formato</summary>
        <div className="campo">
          <div className="opciones">
            {FORMATOS.map((f) => (
              <button key={f.nombre} className={f.ancho === ancho && f.alto === alto ? 'activo' : ''} onClick={() => onCambiar(poner(poner(cfg, ['salida', 'ancho'], f.ancho), ['salida', 'alto'], f.alto))}>
                {f.nombre}
              </button>
            ))}
          </div>
          <div className="partes">
            <label>
              <span className="dato">ancho</span>
              <input type="number" min={16} step={2} value={ancho} onChange={(e) => pon(['salida', 'ancho'], Number(e.target.value))} />
            </label>
            <label>
              <span className="dato">alto</span>
              <input type="number" min={16} step={2} value={alto} onChange={(e) => pon(['salida', 'alto'], Number(e.target.value))} />
            </label>
            <label>
              <span className="dato">cps</span>
              <select value={Number(salida.fps ?? 30)} onChange={(e) => pon(['salida', 'fps'], Number(e.target.value))}>
                {[24, 25, 30, 50, 60].map((f) => (
                  <option key={f} value={f}>
                    {f}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span className="dato">fondo</span>
              <input type="color" value={String(salida.fondo ?? '#08080a')} onChange={(e) => pon(['salida', 'fondo'], e.target.value)} />
            </label>
          </div>
        </div>
      </details>

      <details open className="seccion">
        <summary>El montaje</summary>
        <label className="campo">
          <span>Modo</span>
          <select value={modo} onChange={(e) => pon(['montaje', 'modo'], e.target.value)}>
            {(Object.keys(MODOS) as Modo[]).map((m) => (
              <option key={m} value={m}>
                {MODOS[m].nombre}
              </option>
            ))}
          </select>
          <div className="frase">{MODOS[modo].frase}</div>
        </label>
        {PARAMETROS[modo].map((prm) => {
          const valor = obtener(cfg, ['montaje', prm.clave]);
          return <Perilla key={prm.clave} prm={prm} valor={valor} cambiado={valor !== undefined} onCambiar={(v) => pon(['montaje', prm.clave], v)} />;
        })}
      </details>

      <details className="seccion">
        <summary>La marca</summary>
        <label className="campo casilla">
          <input type="checkbox" checked={Boolean(sello)} onChange={(e) => pon(['logo', 'sello'], e.target.checked ? {esquina: 'abajo-derecha', alto: 0.075, opacidad: 0.85} : undefined)} />
          <span>Sello en una esquina (el isotipo, late en cada primer tiempo)</span>
        </label>
        {sello ? (
          <>
            <div className="campo">
              <span>Esquina</span>
              <div className="opciones esquinas">
                {ESQUINAS.map((e) => (
                  <button key={e} className={(sello.esquina ?? 'abajo-derecha') === e ? 'activo' : ''} onClick={() => pon(['logo', 'sello', 'esquina'], e)} title={e}>
                    {e.replace('arriba', '↑').replace('abajo', '↓').replace('-izquierda', '←').replace('-derecha', '→')}
                  </button>
                ))}
              </div>
            </div>
            <label className="campo">
              <span>Tamaño</span>
              <input type="range" min={0.03} max={0.25} step={0.005} value={Number(sello.alto ?? 0.08)} onChange={(e) => pon(['logo', 'sello', 'alto'], Number(e.target.value))} />
              <b>{Number(sello.alto ?? 0.08).toFixed(3)}</b>
            </label>
            <label className="campo">
              <span>Opacidad</span>
              <input type="range" min={0} max={1} step={0.05} value={Number(sello.opacidad ?? 0.85)} onChange={(e) => pon(['logo', 'sello', 'opacidad'], Number(e.target.value))} />
              <b>{Number(sello.opacidad ?? 0.85).toFixed(2)}</b>
            </label>
            <label className="campo">
              <span>Versión</span>
              <select value={String(sello.version ?? 'isotipo_claro')} onChange={(e) => pon(['logo', 'sello', 'version'], e.target.value)}>
                {Object.entries(VERSIONES_LOGO).map(([k, n]) => (
                  <option key={k} value={k}>
                    {n}
                  </option>
                ))}
              </select>
            </label>
          </>
        ) : null}
        <div className="frase">El salvapantallas y la firma se ponen en la tira, como momentos.</div>
      </details>

      <details className="seccion">
        <summary>Avanzado: el JSON</summary>
        <textarea
          value={texto}
          spellCheck={false}
          onFocus={() => setEditando(true)}
          onBlur={() => setEditando(false)}
          onChange={(e) => {
            setTexto(e.target.value);
            try {
              const nuevo = JSON.parse(e.target.value) as Cfg;
              setErrorJson(null);
              onCambiar(nuevo);
            } catch (err) {
              setErrorJson((err as Error).message);
            }
          }}
        />
        {errorJson ? <div className="error">{errorJson}</div> : null}
      </details>
    </div>
  );
}
