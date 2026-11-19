'use client';

import {Player} from '@remotion/player';
import {useState} from 'react';
import Veredicto from '@/components/Veredicto';
import type {Letrero} from '@/lib/textos';
import {FONDOS_MUESTRA, MuestraTexto, type FondoMuestra} from '@/src/Letrero';
import {FAMILIAS} from '@/src/fuentes';

const FPS = 30;

/** Cuánto dura la muestra: lo que tarda en entrar, más tiempo para leerla; los créditos, lo que tarda el rollo. */
function segundos(l: Letrero): number {
  if (l.estilo.rodillo) return 9;
  return Math.max(3.5, (l.estilo.entrada?.dura ?? 0.5) + 2.6);
}

/** El cuadro donde el letrero ya entró entero y todavía no se va (los créditos, a mitad del rollo). */
function cuadroLeido(l: Letrero): number {
  if (l.estilo.rodillo) return Math.round(segundos(l) * 0.45 * FPS);
  return Math.round((0.3 + (l.estilo.entrada?.dura ?? 0.5) + 0.6) * FPS);
}

function Tarjeta({l, texto, secundario, fondo, quietas}: {l: Letrero; texto: string; secundario: string; fondo: FondoMuestra | 'propio'; quietas: boolean}) {
  const e = l.estilo;
  const letras = [e.fuente, e.secundario?.fuente].filter((x, i, a): x is string => Boolean(x) && a.indexOf(x) === i);
  return (
    <article className={`estilo letrero estado-${l.estado.replace(' ', '-')}`} id={l.id}>
      <div className="muestra">
        <Player
          // Al cambiar entre en movimiento y quietas, el reproductor se arma de nuevo en su cuadro.
          key={quietas ? 'quieta' : 'mueve'}
          initialFrame={quietas ? cuadroLeido(l) : 0}
          component={MuestraTexto}
          inputProps={{e, texto, secundario: secundario || undefined, fondo: fondo === 'propio' ? l.fondo : fondo}}
          durationInFrames={Math.round(segundos(l) * FPS)}
          fps={FPS}
          compositionWidth={1920}
          compositionHeight={1080}
          autoPlay={!quietas}
          loop
          clickToPlay
          style={{width: '100%', aspectRatio: '16 / 9'}}
          acknowledgeRemotionLicense
        />
      </div>
      <div className="cuerpo">
        <header>
          <h2>{l.nombre}</h2>
          <span className="sello">{l.estado}</span>
        </header>
        <p>{l.frase}</p>
        <p className="dato">
          {letras.map((x) => `${x} (${FAMILIAS[x]?.licencia ?? 'del sistema'})`).join(' + ')} · entra {e.entrada?.tipo ?? 'fundido'} · {e.lugar}
        </p>
        <ul className="chips">
          {l.para.map((x) => (
            <li key={x}>{x}</li>
          ))}
        </ul>
        {l.miguel.length > 0 && (
          <div className="miguel">
            {l.miguel.map((c) => (
              <blockquote key={c}>«{c}»</blockquote>
            ))}
          </div>
        )}
        <Veredicto id={l.id} estado={l.estado} />
        <footer className="dato">
          <code className="tecnica">&quot;letrero&quot;: &quot;{l.id}&quot;</code>
          {l.origen ? <span> · {l.origen}</span> : null}
        </footer>
      </div>
    </article>
  );
}

/**
 * La galería de textos en vivo: cada letrero dibujado por el mismo componente que lo pone en el video
 * (src/Letrero.tsx), sin renders ni muestras guardadas. Arriba se puede escribir un texto propio y
 * cambiar el fondo de todas a la vez.
 */
export default function Letreros({letreros, familias}: {letreros: Letrero[]; familias: [string, string][]}) {
  const [propio, setPropio] = useState('');
  const [segundo, setSegundo] = useState('');
  const [fondo, setFondo] = useState<FondoMuestra | 'propio'>('propio');
  const [quietas, setQuietas] = useState(false);
  return (
    <>
      <div className="probar-texto">
        <input
          type="text"
          value={propio}
          onChange={(ev) => setPropio(ev.target.value)}
          placeholder="escribe para probar tu texto en todos (\n = otra fila)"
          aria-label="Texto de prueba"
        />
        <input
          type="text"
          value={segundo}
          onChange={(ev) => setSegundo(ev.target.value)}
          placeholder="segunda línea (cargo, fecha, autor)"
          aria-label="Segunda línea de prueba"
        />
        <div className="filtros">
          <span className="dato">fondo</span>
          {(['propio', ...Object.keys(FONDOS_MUESTRA)] as (FondoMuestra | 'propio')[]).map((x) => (
            <button key={x} type="button" className={fondo === x ? 'activo' : ''} onClick={() => setFondo(x)}>
              {x === 'propio' ? 'el de cada uno' : x}
            </button>
          ))}
          <span className="dato">·</span>
          <button type="button" className={quietas ? '' : 'activo'} onClick={() => setQuietas(false)}>
            en movimiento
          </button>
          <button type="button" className={quietas ? 'activo' : ''} onClick={() => setQuietas(true)} title="cada una detenida donde ya entró entera">
            quietas
          </button>
        </div>
      </div>
      {familias.map(([clave, nombre]) => {
        const grupo = letreros.filter((l) => l.familia === clave);
        if (!grupo.length) return null;
        return (
          <section key={clave}>
            <h2 className="familia-texto">
              {nombre} <span className="dato">{grupo.length}</span>
            </h2>
            <div className="estilos">
              {grupo.map((l) => (
                <Tarjeta
                  key={l.id}
                  l={l}
                  texto={propio ? propio.replace(/\\n/g, '\n') : l.ejemplo.texto}
                  secundario={propio ? segundo : segundo || l.ejemplo.secundario || ''}
                  fondo={fondo}
                  quietas={quietas}
                />
              ))}
            </div>
          </section>
        );
      })}
    </>
  );
}
