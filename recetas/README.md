# Recetas

Combinaciones con nombre de una base de la mesa analógica y sus gestos, para pedirlas de una vez. Miguel, el
2026-11-22: «También armar templates de trabajo para poder armar trabajo más adelante»; es uno de los tres moldes
que eligió (con las plantillas de piezas, en `plantillas/`, y el molde de experimento, en `direccion/MOLDE.md`).

```
python montaje.py recetas                                         # las lista, con lo que valen, y las valida
python montaje.py analogo <video> --cadena la-familia-en-super-8  # se piden como cualquier cadena
python montaje.py analogo <video> --cadena la-familia-en-super-8 --gesto pausa-del-vhs   # y se les suman gestos
```

## Qué guarda una receta

`recetas/<id>.json`; el `id` es el nombre del archivo y no puede llamarse como un estilo.

| Campo | Qué es |
|---|---|
| `nombre` | cómo la llamamos |
| `frase` | qué se ve y qué suena |
| `para` | para qué sirve, con el vocabulario de los estilos |
| `base` | un estilo analógico que no es gesto (la cinta, la película, la antena…) |
| `gestos` | estilos gesto, en el orden en que se ponen; cada aparato cae en su lugar de la cadena |

Una receta no tiene veredicto propio: vale lo peor entre su base y sus gestos (si uno está rechazado, la receta lo
dice). Cuando una combinación se usa seguido y Miguel la aprueba, se guarda aquí.
