// proyecto.json se escribe a mano y se lee en diffs: un formato estable y
// legible importa. Sangría de un espacio (como escribir_json en Python), listas
// de objetos con un objeto por línea, y lo corto en una sola línea.

const compacto = (v: unknown): string => {
  if (Array.isArray(v)) return '[' + v.map(compacto).join(', ') + ']';
  if (v && typeof v === 'object') {
    return '{' + Object.entries(v).map(([k, x]) => `${JSON.stringify(k)}: ${compacto(x)}`).join(', ') + '}';
  }
  return JSON.stringify(v);
};

const esObjeto = (v: unknown): v is Record<string, unknown> => Boolean(v) && typeof v === 'object' && !Array.isArray(v);
const CORTO = 90;

export function formatear(v: unknown, nivel = 0): string {
  const sangria = ' '.repeat(nivel + 1);
  const cierre = ' '.repeat(nivel);
  if (Array.isArray(v)) {
    if (v.length === 0) return '[]';
    const plano = compacto(v);
    if (v.every((x) => !x || typeof x !== 'object') || plano.length <= CORTO) return plano;
    return '[\n' + v.map((x) => sangria + (esObjeto(x) ? compacto(x) : formatear(x, nivel + 1))).join(',\n') + '\n' + cierre + ']';
  }
  if (esObjeto(v)) {
    const entradas = Object.entries(v);
    if (entradas.length === 0) return '{}';
    const plano = compacto(v);
    if (nivel > 0 && plano.length <= CORTO && entradas.every(([, x]) => !x || typeof x !== 'object')) return plano;
    return '{\n' + entradas.map(([k, x]) => `${sangria}${JSON.stringify(k)}: ${formatear(x, nivel + 1)}`).join(',\n') + '\n' + cierre + '}';
  }
  return JSON.stringify(v);
}

/** ¿Son el mismo valor? (Comparación por estructura, sin importar el formato.) */
export const iguales = (a: unknown, b: unknown): boolean => JSON.stringify(a) === JSON.stringify(b);
