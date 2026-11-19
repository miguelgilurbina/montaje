// La galería de textos, leída del disco: las recetas en textos/*.json (el repo). Lo valida
// `python montaje.py textos`; aquí se lee para mostrarla en vivo. Sólo del lado del servidor.
import fs from 'node:fs';
import path from 'node:path';
import {RAIZ} from '@/lib/proyectos';
import type {Estado} from '@/lib/estilos';
import type {EstiloTexto} from '@/src/tipos';

export const TEXTOS = path.join(RAIZ, 'textos');

export type FamiliaTexto = 'titulos' | 'frases' | 'rotulos' | 'subtitulos' | 'movimiento';
export const FAMILIAS_TEXTO: Record<FamiliaTexto, string> = {
  titulos: 'títulos y portadas',
  frases: 'frases destacadas',
  rotulos: 'rótulos y citas',
  subtitulos: 'subtítulos y créditos',
  movimiento: 'texto en movimiento',
};

/** Lo que dibuja Letrero.tsx (el resto de la receta es de la galería). Igual que DIBUJO en py/montaje/textos.py. */
const DIBUJO = [
  'fuente', 'peso', 'cursiva', 'variacion', 'tamano', 'mayusculas', 'espaciado', 'interlineado', 'color', 'compresion',
  'contorno', 'sombra', 'caja', 'resaltado', 'barra', 'alineado', 'lugar', 'ancho', 'giro', 'entrada', 'salida',
  'secundario', 'rodillo', 'ventana', 'karaoke', 'latido', 'cursor',
] as const;

export type Letrero = {
  id: string;
  nombre: string;
  familia: FamiliaTexto;
  frase: string;
  para: string[];
  estado: Estado;
  miguel: string[];
  origen?: string;
  ejemplo: {texto: string; secundario?: string};
  fondo: 'oscuro' | 'claro' | 'imagen' | 'mapa';
  estilo: EstiloTexto;
};

export function leerTextos(): Letrero[] {
  if (!fs.existsSync(TEXTOS)) return [];
  return fs
    .readdirSync(TEXTOS)
    .filter((f) => f.endsWith('.json'))
    .sort()
    .map((f) => {
      const id = f.slice(0, -5);
      const e = JSON.parse(fs.readFileSync(path.join(TEXTOS, f), 'utf-8')) as Record<string, unknown>;
      const estilo = {id, ...Object.fromEntries(DIBUJO.filter((k) => k in e).map((k) => [k, e[k]]))} as EstiloTexto;
      return {
        id,
        nombre: String(e.nombre),
        familia: e.familia as FamiliaTexto,
        frase: String(e.frase),
        para: (e.para as string[]) ?? [],
        estado: e.estado as Estado,
        miguel: (e.miguel as string[]) ?? [],
        origen: e.origen as string | undefined,
        ejemplo: e.ejemplo as Letrero['ejemplo'],
        fondo: e.fondo as Letrero['fondo'],
        estilo,
      };
    });
}
