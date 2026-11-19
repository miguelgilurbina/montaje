'use client';

import {useState} from 'react';

type Fuente = {clave: string; texto: string; url: string};

/**
 * La muestra de un estilo, en dos versiones: la del probador (el mismo banco para todos: se
 * comparan) y la de su video (donde se vio por primera vez y se juzgó). Arranca en la del probador.
 */
export default function Muestras({probador, video, sin}: {probador: string | null; video: string | null; sin: string}) {
  const fuentes: Fuente[] = [];
  if (probador) fuentes.push({clave: 'probador', texto: 'en el probador', url: probador});
  if (video) fuentes.push({clave: 'video', texto: 'en su video', url: video});
  const [cual, setCual] = useState(fuentes[0]?.clave);
  const actual = fuentes.find((f) => f.clave === cual) ?? fuentes[0];
  return (
    <div className="muestra">
      {/* `#t=0.5`: con preload="metadata" el navegador muestra ese cuadro en vez de negro. */}
      {actual ? <video key={actual.url} src={`${actual.url}#t=0.5`} controls loop playsInline preload="metadata" /> : <p className="dato">{sin}</p>}
      {fuentes.length > 1 ? (
        <div className="pestanas" role="group" aria-label="Qué muestra">
          {fuentes.map((f) => (
            <button key={f.clave} type="button" className={f.clave === actual?.clave ? 'activo' : ''} onClick={() => setCual(f.clave)}>
              {f.texto}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
