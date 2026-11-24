# 38 · Las tablas de color

**Fecha:** 2026-11-23

## Idea

El etalonaje con tablas de color (LUT 3D): procesos de laboratorio escritos en código desde la paleta, y cualquier
archivo `.cube` de otro editor, en la mesa y en la consola. Era G2/K3 en `PROPUESTAS.md`; volvió al mirar lo que
trae OpenMontage (siete perfiles de color y `.cube`). Escrito desde cero, sin mirar su código.

## Material

El banco del probador (La Añoranza).

## Lo que se hizo

- `py/montaje/etalonaje.py`, aparato de imagen `color`: `tabla` (noche-de-curiana, noche-americana, infrarroja,
  blanqueo-saltado, proceso-cruzado o archivo), `archivo` (un `.cube`) y `fuerza`. Sin sonido: el laboratorio no
  suena.
- `python montaje.py color` lista las tablas; `--exportar <tabla> <salida.cube>` escribe una para otro editor;
  `--json` se la da a la consola.
- En la consola, el shader usa la misma tabla que escribe el motor (textura 3D); las perillas de texto (el `.cube`)
  se escriben en la tarjeta del aparato.
- Cinco estilos `propuesta`, uno por tabla, con su muestra en el probador.

## Lo que midió Claude (que no oye)

- La mesa aplica un `.cube` igual que `lut3d` de ffmpeg: diferencia media de 0,5 niveles sobre 255 (máximo 1, el
  redondeo); con el orden de los canales al revés sería de 17. Así, lo que sale de la mesa sirve en otro editor y lo
  de otro editor entra a la mesa.
- Escribir y volver a leer una tabla da la misma (5 × 10⁻⁷); la tabla identidad no cambia la imagen.
- En la hoja (`analogo --comparar`): la primera noche de Curiana casi no se veía (subí el peso de las sombras y las
  luces); la infrarroja dejaba verde el camino de tierra y el techo (ahora lo rojo refleja infrarrojo y sale
  amarillo, y el cielo se oscurece).
- `test_color.py`: 7 pruebas.

## Lo que dijo Miguel

- «y podríamos sacar nosotros algo de ahí pero hacerlo nosotros mismos?» (de OpenMontage); eligió el etalonaje con
  LUT, las transiciones en todo y la medida de monotonía.

## Veredicto

Por juzgar.
