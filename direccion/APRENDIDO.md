# Lo aprendido

> **Lo escribe `python montaje.py aprender`** desde `direccion/LECCIONES.json` y los veredictos de `estilos/`.
> No se corrige aquí: una lección nueva va a LECCIONES.json, con la cita de Miguel.

## Las lecciones

### la-banda-flota · 2026-11-09

«Las finales, siento que el primer tramo o la primera mitad del video no calzó al 100 con el feel porque los videos estaban en velocidad normal en muchos casos, y al final si se hicieron esos ajustes a la velocidad ya que justo la canción lleva a eso.»

**Regla:** En una canción de recuerdo, la banda no acelera la imagen: los clips van tan lentos como en la calma, la música avanza y la imagen flota.

**Cuándo:** energia: media o alta, modo: pulso, tono: recuerdo. **Qué hace:** el primer armado de `guion` le pone `velocidad` [0.4, 0.5], `velocidad_min` 0.38.

**Medido:** En el 22, gente, ciudad y campo pasaron de ×0,63–0,75 a ×0,47–0,50; sobre esa versión Miguel dijo «excelente».

### letra-al-centro · 2026-11-09

«excelente, ahora lo único que agregaría sería subtitulos de la canción en el medio.»

**Regla:** Si la canción tiene letra y ya está transcrita, la letra va al centro, palabra por palabra cuando se canta, con un halo oscuro detrás para que se lea sobre cualquier imagen.

**Cuándo:** letra: True. **Qué hace:** el primer armado suma la capa `rotulos`.

### producir-para-el-guion · 2026-11-09

«Mira, de 10 le doy un 6. [...] creo que igual es porque estamos usando material ya hecho, nada producido específicamente para este video.»

**Regla:** Primero el guion, después el material: con los tramos escritos, `python montaje.py tomas <p>` dice qué tomas producir antes de elegir clips de lo que ya hay.

**Cuándo:** siempre. **Qué hace:** `guion` lo dice como consejo.

## Los veredictos como datos

La galería tiene 67 estilos: 54 aprobado, 6 a medias, 2 propuesta, 5 rechazado.
Por perilla, los valores de lo aprobado y de lo que quedó a medias o en «no» (un rango es su punto medio).
Con tan pocos «no», es una pista: dice dónde mirar, no qué hacer.

| Perilla | Aprobado | A medias o no |
|---|---|---|
| `pulso · frase_compases` | 1–4 (19) | 2–4 (4) |
| `pulso · frase_compases_calma` | 2–4 (3) | — (0) |
| `pulso · fundido_calma_golpes` | 1,5–4 (3) | — (0) |
| `pulso · fundido_golpes` | 0,25–2 (9) | 2 (1) |
| `pulso · velocidad` | 0,525–0,85 (4) | 0,9 (1) |
| `tinta · fuerza` | 0,85–0,9 (3) | — (0) |
| `transformar · fuerza` | 0,6–2 (4) | — (0) |

## Lo que falta saber

Estos estilos tienen «no» o «a medias» sin porqué: hasta saberlo, su `evitar` queda vacío y el motor sólo
puede no elegirlos, no aprender de ellos.

- `calima-con-recuerdo` (a medias): El aire caliente que ondula, con el grano y la viñeta del recuerdo: los médanos al mediodía, filmados hace cincuenta años.
- `calima` (a medias): El aire caliente sobre los médanos: la imagen ondula hacia arriba, despacio, y se agita un instante en cada golpe.
- `diptico` (a medias): Dos clips a la vez, cada uno en su mitad: cada clip con su pareja de la otra mitad del archivo (el mar con el campo), recortados siguiendo al sujeto.
- `salto-al-golpe` (rechazado): Dentro de cada clip, un salto a otro momento en cada golpe de la canción: el pulso se ve en la imagen sin cambiar de clip.
- `transicion-persiana` (rechazado): El clip nuevo entra en franjas verticales que se ensanchan hasta cerrarse.
- `ventana` (rechazado): El clip al 62 % del cuadro, con sombra, flotando sobre un campo de color de la paleta que respira con la canción; polvo de luz encima.
