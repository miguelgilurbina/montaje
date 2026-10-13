'use client';

import type {Biblioteca} from '@/lib/proyectos';
import {MOMENTOS, TIPOS_IMAGEN, VERSIONES_LOGO, type TipoMomento} from '@/lib/vocabulario';
import type {MomentoCfg, SalvaCfg, Seleccion} from './Tira';

type Item = MomentoCfg | SalvaCfg;

type Props = {
  sel: Exclude<Seleccion, null>;
  item: Item;
  biblioteca: Biblioteca | null;
  bibliotecaNombre: string;
  onCambiar: (item: Item) => void;
  onBorrar: () => void;
};

const Numero = ({valor, min, max, paso, onCambiar}: {valor: number; min: number; max: number; paso: number; onCambiar: (v: number) => void}) => (
  <input type="number" value={valor} min={min} max={max} step={paso} onChange={(e) => onCambiar(Number(e.target.value))} />
);

/** La ficha del momento elegido en la tira: sus opciones con nombre, sin claves JSON. */
export default function Ficha({sel, item, biblioteca, bibliotecaNombre, onCambiar, onBorrar}: Props) {
  const tipo: TipoMomento = sel.lista === 'salvapantallas' ? 'salvapantallas' : ((item as MomentoCfg).tipo as TipoMomento);
  const info = MOMENTOS[tipo];
  const pon = (clave: string, valor: unknown) => {
    const copia: Record<string, unknown> = {...item};
    if (valor === undefined) delete copia[clave];
    else copia[clave] = valor;
    onCambiar(copia as Item);
  };
  const num = (clave: string, defecto: number) => (typeof item[clave] === 'number' ? (item[clave] as number) : defecto);

  let campos: React.ReactNode = null;
  if (tipo === 'destacado') {
    const img = typeof item.img === 'string' ? item.img : '';
    const modo = img === 'marca' ? 'marca' : img.startsWith('logo:') ? 'logo' : img ? 'imagen' : 'cualquiera';
    const marca = biblioteca?.imagenes.filter((i) => i.marca) ?? [];
    const elegida = biblioteca?.imagenes.find((i) => i.id === img);
    campos = (
      <>
        <div className="campo">
          <span>Qué imagen</span>
          <div className="opciones">
            {[
              ['marca', 'una de marca'],
              ['logo', 'el logo'],
              ['imagen', 'esta imagen'],
              ['cualquiera', 'la que elija el plan'],
            ].map(([v, n]) => (
              <button
                key={v}
                className={modo === v ? 'activo' : ''}
                onClick={() => pon('img', v === 'marca' ? 'marca' : v === 'logo' ? 'logo:lockup_claro' : v === 'imagen' ? (marca[0]?.id ?? '') : undefined)}
              >
                {n}
              </button>
            ))}
          </div>
        </div>
        {modo === 'logo' ? (
          <label className="campo">
            <span>Versión</span>
            <select value={img.slice(5)} onChange={(e) => pon('img', `logo:${e.target.value}`)}>
              {(biblioteca?.logos.length ? biblioteca.logos : Object.keys(VERSIONES_LOGO)).map((k) => (
                <option key={k} value={k}>
                  {VERSIONES_LOGO[k] ?? k}
                </option>
              ))}
            </select>
          </label>
        ) : null}
        {modo === 'imagen' ? (
          <div className="campo">
            <span>Cuál</span>
            <input list="imagenes-catalogo" value={img} onChange={(e) => pon('img', e.target.value)} placeholder="escribe para buscar por nombre" />
            <datalist id="imagenes-catalogo">
              {biblioteca?.imagenes.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.titulo}
                </option>
              ))}
            </datalist>
            {elegida ? <img className="mini" src={`/medios/${bibliotecaNombre}/${elegida.mini}`} alt={elegida.titulo} title={elegida.titulo} /> : null}
          </div>
        ) : null}
        <label className="campo">
          <span>Oscurecer el fondo</span>
          <input type="range" min={0} max={1} step={0.05} value={num('oscuro', 0.75)} onChange={(e) => pon('oscuro', Number(e.target.value))} />
          <b>{num('oscuro', 0.75).toFixed(2)}</b>
        </label>
        <label className="campo casilla">
          <input type="checkbox" checked={Boolean(item.firma)} onChange={(e) => pon('firma', e.target.checked || undefined)} />
          <span>Firma: se queda hasta el final en vez de volver a su lugar</span>
        </label>
      </>
    );
  } else if (tipo === 'rafaga') {
    const de = typeof item.de === 'string' ? item.de : '';
    campos = (
      <>
        <div className="campo">
          <span>Imágenes por compás</span>
          <div className="opciones">
            {[4, 8, 16, 32].map((n) => (
              <button key={n} className={num('por_compas', 8) === n ? 'activo' : ''} onClick={() => pon('por_compas', n)}>
                {n}
              </button>
            ))}
            <Numero valor={num('por_compas', 8)} min={1} max={64} paso={1} onCambiar={(v) => pon('por_compas', v)} />
          </div>
        </div>
        <label className="campo">
          <span>De qué tipo</span>
          <select value={de} onChange={(e) => pon('de', e.target.value || undefined)}>
            <option value="">cualquiera</option>
            {Object.entries(TIPOS_IMAGEN).map(([k, n]) => (
              <option key={k} value={k}>
                {n}
              </option>
            ))}
          </select>
        </label>
      </>
    );
  } else if (tipo === 'barrido') {
    const dir = Array.isArray(item.direccion) ? (item.direccion as number[]).join(',') : '';
    campos = (
      <>
        <label className="campo">
          <span>Duración del salto (cuadros)</span>
          <Numero valor={num('cuadros', 10)} min={2} max={60} paso={1} onCambiar={(v) => pon('cuadros', v)} />
        </label>
        <label className="campo">
          <span>Hacia dónde</span>
          <select value={dir} onChange={(e) => pon('direccion', e.target.value ? e.target.value.split(',').map(Number) : undefined)}>
            <option value="">alternando</option>
            <option value="1,0">→ derecha</option>
            <option value="-1,0">← izquierda</option>
            <option value="0,1">↓ abajo</option>
            <option value="0,-1">↑ arriba</option>
          </select>
        </label>
      </>
    );
  } else if (tipo === 'video') {
    const src = typeof item.src === 'string' ? item.src : '';
    campos = (
      <>
        <label className="campo">
          <span>Cuál</span>
          <select value={src} onChange={(e) => pon('src', e.target.value)}>
            {!biblioteca?.videos.includes(src) ? <option value={src}>{src || '(elige)'}</option> : null}
            {biblioteca?.videos.map((v) => (
              <option key={v} value={v}>
                {v.replace(/^video\//, '')}
              </option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span>Compases que ocupa</span>
          <Numero valor={num('compases', 1)} min={1} max={16} paso={1} onCambiar={(v) => pon('compases', v)} />
        </label>
        <label className="campo">
          <span>Volumen del video</span>
          <input type="range" min={0} max={1} step={0.05} value={num('volumen', 0)} onChange={(e) => pon('volumen', Number(e.target.value))} />
          <b>{num('volumen', 0).toFixed(2)}</b>
        </label>
        <label className="campo casilla">
          <input type="checkbox" checked={Array.isArray(item.recorte)} onChange={(e) => pon('recorte', e.target.checked ? [280, 0, 720, 720] : undefined)} />
          <span>Recortar al cuadrado central (los videos de Gemini: [280, 0, 720, 720])</span>
        </label>
      </>
    );
  } else if (tipo === 'salvapantallas') {
    const versiones = Array.isArray(item.versiones) ? (item.versiones as string[]) : ['lockup_oscuro', 'lockup_claro'];
    campos = (
      <>
        <label className="campo">
          <span>Compases que dura</span>
          <Numero valor={num('compases', 1)} min={1} max={32} paso={1} onCambiar={(v) => pon('compases', v)} />
        </label>
        <label className="campo">
          <span>Tamaño del logo</span>
          <input type="range" min={0.08} max={0.6} step={0.01} value={num('alto', 0.24)} onChange={(e) => pon('alto', Number(e.target.value))} />
          <b>{num('alto', 0.24).toFixed(2)}</b>
        </label>
        <label className="campo">
          <span>Velocidad</span>
          <input type="range" min={1} max={15} step={0.5} value={num('velocidad', 5)} onChange={(e) => pon('velocidad', Number(e.target.value))} />
          <b>{num('velocidad', 5)}</b>
        </label>
        <label className="campo">
          <span>Velo oscuro</span>
          <input type="range" min={0} max={1} step={0.05} value={num('oscuro', 0.45)} onChange={(e) => pon('oscuro', Number(e.target.value))} />
          <b>{num('oscuro', 0.45).toFixed(2)}</b>
        </label>
        <div className="campo">
          <span>Versiones que alterna</span>
          <div className="opciones">
            {Object.entries(VERSIONES_LOGO).map(([k, n]) => (
              <button
                key={k}
                className={versiones.includes(k) ? 'activo' : ''}
                onClick={() => {
                  const nuevas = versiones.includes(k) ? versiones.filter((v) => v !== k) : [...versiones, k];
                  pon('versiones', nuevas.length ? nuevas : undefined);
                }}
              >
                {n}
              </button>
            ))}
          </div>
        </div>
      </>
    );
  }

  return (
    <div className="ficha">
      <div className="ficha-cabeza">
        <span className="punto" style={{background: info.color}} />
        <b>{info.nombre}</b>
        <span className="dato">compás {item.compas}</span>
        <span className="dato frase">{info.frase}</span>
        <button className="quitar" onClick={onBorrar} title="Quitar (Supr)">
          quitar
        </button>
      </div>
      <div className="campos">{campos}</div>
    </div>
  );
}
