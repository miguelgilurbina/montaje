// La automatización de la consola: los puntos que deja una perilla al girarla con el video corriendo, y cómo se leen.
// Lo mismo que `valor_en` del motor (py/montaje/analogo.py): si cambia allá, cambia aquí.
import type {Valor} from '@/lib/consola-gl';

export type Punto = [number, Valor];

export type PerillaInfo = {defecto: unknown; rango: unknown[] | null; entero?: boolean};

export type Tipo =
  | {clase: 'numero'; min: number; max: number; entero: boolean; bipolar: boolean}
  | {clase: 'opcion'; opciones: string[]}
  | {clase: 'si-no'}
  | {clase: 'fija'};

/** Qué clase de perilla es, según lo que el motor dice de ella. Las listas (fantasmas, tintas, el sol) quedan fijas. */
export function tipoDe(info: PerillaInfo): Tipo {
  const r = info.rango;
  if (typeof info.defecto === 'boolean') return {clase: 'si-no'};
  if (r && r.length && typeof r[0] === 'string') return {clase: 'opcion', opciones: r as string[]};
  if (r && r.length === 2 && typeof r[0] === 'number' && typeof r[1] === 'number') {
    const [min, max] = r as [number, number];
    return {clase: 'numero', min, max, entero: Boolean(info.entero), bipolar: min < 0 && max > 0};
  }
  return {clase: 'fija'};
}

/** De 0 a 1, para dibujar el dial. Un número vacío (el `auto` del retraso del croma) va al medio. */
export function normal(tipo: Tipo, v: Valor): number {
  if (tipo.clase === 'numero') {
    if (typeof v !== 'number') return tipo.bipolar ? (0 - tipo.min) / (tipo.max - tipo.min) : 0.5;
    return Math.min(1, Math.max(0, (v - tipo.min) / (tipo.max - tipo.min)));
  }
  if (tipo.clase === 'opcion') {
    const i = typeof v === 'string' ? tipo.opciones.indexOf(v) : 0;
    return tipo.opciones.length > 1 ? Math.max(0, i) / (tipo.opciones.length - 1) : 0;
  }
  if (tipo.clase === 'si-no') return v ? 1 : 0;
  return 0;
}

/** El valor de la perilla en esa posición del recorrido (0 a 1). */
export function desdeNormal(tipo: Tipo, n: number): Valor {
  const x = Math.min(1, Math.max(0, n));
  if (tipo.clase === 'numero') {
    const v = tipo.min + x * (tipo.max - tipo.min);
    return tipo.entero ? Math.round(v) : Math.round(v * 1000) / 1000;
  }
  if (tipo.clase === 'opcion') return tipo.opciones[Math.round(x * (tipo.opciones.length - 1))];
  if (tipo.clase === 'si-no') return x >= 0.5;
  return null;
}

/** El valor grabado en el segundo t: recto entre dos puntos si son números, a saltos si no. */
export function valorEn(puntos: Punto[], t: number, entero = false): Valor {
  if (!puntos.length) return null;
  if (t <= puntos[0][0]) return puntos[0][1];
  const ultimo = puntos[puntos.length - 1];
  if (t >= ultimo[0]) return ultimo[1];
  for (let i = 0; i < puntos.length - 1; i++) {
    const [t0, v0] = puntos[i];
    const [t1, v1] = puntos[i + 1];
    if (t0 <= t && t < t1) {
      if (typeof v0 !== 'number' || typeof v1 !== 'number' || t1 <= t0) return v0;
      const v = v0 + ((v1 - v0) * (t - t0)) / (t1 - t0);
      return entero ? Math.round(v) : v;
    }
  }
  return ultimo[1];
}

/** Menos puntos con la misma forma: los números que caen sobre la recta de sus vecinos se van (con una tolerancia
 * del 0,4 % del recorrido); las opciones guardan sólo sus cambios. */
export function simplificar(puntos: Punto[], tipo: Tipo): Punto[] {
  if (puntos.length <= 2) return puntos;
  if (tipo.clase !== 'numero') {
    const sale: Punto[] = [puntos[0]];
    for (const p of puntos.slice(1)) if (p[1] !== sale[sale.length - 1][1]) sale.push(p);
    return sale;
  }
  const tol = (tipo.max - tipo.min) * 0.004;
  // Douglas-Peucker sobre (t, v).
  const queda = new Array(puntos.length).fill(false);
  queda[0] = queda[puntos.length - 1] = true;
  const pila: [number, number][] = [[0, puntos.length - 1]];
  while (pila.length) {
    const [a, b] = pila.pop()!;
    const [ta, va] = puntos[a] as [number, number];
    const [tb, vb] = puntos[b] as [number, number];
    let peor = -1;
    let dist = tol;
    for (let i = a + 1; i < b; i++) {
      const [t, v] = puntos[i] as [number, number];
      const esperado = tb > ta ? va + ((vb - va) * (t - ta)) / (tb - ta) : va;
      const d = Math.abs(v - esperado);
      if (d > dist) {
        dist = d;
        peor = i;
      }
    }
    if (peor >= 0) {
      queda[peor] = true;
      pila.push([a, peor], [peor, b]);
    }
  }
  return puntos.filter((_, i) => queda[i]);
}

/** Lo grabado mientras se sostuvo la perilla (de `desde` a `hasta`) reemplaza lo que había en ese tramo; antes y
 * después sigue lo de antes, con un puente corto para que no salte (el modo «touch»). */
export function fusionar(antes: Punto[], nuevos: Punto[], desde: number, hasta: number, tipo: Tipo, entero: boolean): Punto[] {
  if (!nuevos.length) return antes;
  const fuera = antes.filter(([t]) => t < desde - 1e-6 || t > hasta + 1e-6);
  const puente: Punto[] = [];
  if (antes.length) {
    if (antes[0][0] < desde) puente.push([Math.max(0, desde - 0.001), valorEn(antes, desde, entero)]);
    if (antes[antes.length - 1][0] > hasta) puente.push([hasta + 0.04, valorEn(antes, hasta + 0.04, entero)]);
  }
  const todos = [...fuera, ...puente, ...nuevos].sort((a, b) => a[0] - b[0]);
  // Dos puntos en el mismo instante: gana el último que llegó (lo nuevo va al final del arreglo antes de ordenar).
  const unicos: Punto[] = [];
  for (const p of todos) {
    if (unicos.length && Math.abs(unicos[unicos.length - 1][0] - p[0]) < 1e-4) unicos[unicos.length - 1] = p;
    else unicos.push(p);
  }
  return simplificar(unicos, tipo).map(([t, v]) => [Math.round(t * 1000) / 1000, v]);
}

export type Pista = {paso: number; perilla: string; puntos: Punto[]; curva?: 'lineal' | 'escalon'};

/** Lo grabado en el formato del motor: el `paso` es el lugar del aparato en la cadena que se renderiza (sólo los
 * encendidos). */
export function aPistas(
  modulos: {id: string; activo: boolean}[],
  auto: Record<string, Record<string, Punto[]>>,
): Pista[] {
  const sale: Pista[] = [];
  modulos
    .filter((m) => m.activo)
    .forEach((m, paso) => {
      for (const [perilla, puntos] of Object.entries(auto[m.id] ?? {})) {
        if (puntos.length) sale.push({paso, perilla, puntos});
      }
    });
  return sale;
}
