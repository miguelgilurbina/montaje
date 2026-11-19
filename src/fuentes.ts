import {useEffect, useState} from 'react';
import {continueRender, delayRender, staticFile} from 'remotion';
import registro from '../fuentes/fuentes.json';

/**
 * Las tipografías del motor (fuentes/, libres, con su licencia al lado). En el render salen de la
 * carpeta pública (planificar pone en el timeline cuáles usa y el render las enlaza ahí); en el panel,
 * de la ruta /fuentes/. Una familia que no está en fuentes.json la busca el navegador en el sistema.
 */

export type ArchivoFuente = {archivo: string; peso: number[]; cursiva: boolean};
export type Familia = {voz: string; licencia: string; archivos: ArchivoFuente[]};

export const FAMILIAS = registro.familias as Record<string, Familia>;

export const urlFuente = (archivo: string, enPanel: boolean) => (enPanel ? `/fuentes/${archivo}` : staticFile(`fuentes/${archivo}`));

/** La familia en CSS, con un reemplazo de su misma clase mientras carga (o si falta). */
export function cssFamilia(familia: string): string {
  const serif = /Fraunces|Lora/.test(familia);
  const mono = /Mono|Elite/.test(familia);
  return `'${familia}', ${mono ? "'Courier New', monospace" : serif ? 'Georgia, serif' : "'Segoe UI', Arial, sans-serif"}`;
}

const cargadas = new Map<string, Promise<void>>();

/** Carga una vez (por página) todas las caras de una familia: normal y cursiva, con su rango de pesos. */
export function cargarFamilia(familia: string, enPanel: boolean): Promise<void> {
  const clave = `${familia}|${enPanel ? 'panel' : 'render'}`;
  const ya = cargadas.get(clave);
  if (ya) return ya;
  const f = FAMILIAS[familia];
  const p = !f
    ? Promise.resolve()
    : Promise.all(
        f.archivos.map(async (a) => {
          const cara = new FontFace(familia, `url("${urlFuente(a.archivo, enPanel)}") format("truetype")`, {
            weight: a.peso[0] === a.peso[1] ? String(a.peso[0]) : `${a.peso[0]} ${a.peso[1]}`,
            style: a.cursiva ? 'italic' : 'normal',
          });
          await cara.load();
          document.fonts.add(cara);
        }),
      ).then(() => undefined);
  cargadas.set(clave, p);
  return p;
}

/** Espera las familias antes de dibujar el cuadro: sin esto, el primer cuadro sale con la letra de reemplazo. */
export function useFuentes(familias: (string | undefined)[], enPanel: boolean): void {
  const clave = [...new Set(familias.filter((x): x is string => Boolean(x)))].sort().join('|');
  const [espera] = useState(() => delayRender(`tipografías: ${clave}`));
  useEffect(() => {
    let vivo = true;
    Promise.all(clave.split('|').filter(Boolean).map((x) => cargarFamilia(x, enPanel)))
      .catch((e) => console.error('no cargó una tipografía', e))
      .finally(() => {
        if (vivo) continueRender(espera);
      });
    return () => {
      vivo = false;
      continueRender(espera);
    };
  }, [clave, enPanel, espera]);
}
