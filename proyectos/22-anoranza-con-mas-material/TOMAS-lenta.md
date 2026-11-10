# 22 · Añoranza con más material · lista de tomas

> **La escribe `python montaje.py tomas`**: no se corrige a mano (se corrige el guion y se vuelve a
> correr). Dice lo que la música y el montaje le piden a cada toma; lo que se ve lo decide Miguel.

34 tomas para musica/La Añoranza de Natalia.wav (3:01,3, 92 BPM), en 3:2 (versión lenta). 4 usan más de 5,2 s de clip (lo que trae uno de Midjourney): hay que extenderlas o irán más lentas.

**En pantalla** es la velocidad a la que va a ir cada toma: a ×0,45 lo que dura un segundo se ve en dos, y lo que se
mueve se ve flotando. Por eso en la banda conviene generar con más movimiento del que se quiere ver. **Se usan** son
los segundos del clip que entran al video (con los fundidos); `--motion` es el ajuste de movimiento de Midjourney.

**Cómo nombrar los archivos:** empezando por el número de la toma («T3-02 pareja en la playa.mp4»), en una
carpeta de `clips` del proyecto. `python montaje.py tomas 22-anoranza-con-mas-material --estado` dice cuáles faltan.

## T1 · el mar despierta

0:00,0–0:11,7 · 1 toma

**Lo que pasa:** el mar despierta; el título

**Estilos:** `foto-que-despierta`, `titulo-al-pulso`

**Evitar:** congelar menos que el fundido (con 2 golpes de cada uno la foto se quedaba quieta sólo mientras aparecía y no se notaba) (foto-que-despierta)

| Toma | Canción | Compases | Música | En pantalla | Se usan | Movimiento | Entra | Ojo |
|---|---|---|---|---|---|---|---|---|
| **T1-01** | 0:00,0–0:11,7 | 5 | calma | ×0,45 | 6,3 s · extender | casi quieta: algo que respira, un paneo muy lento · `--motion low` | sale del negro | entra quieta y arranca en el golpe: el primer cuadro tiene que valer como foto |

## T2 · las postales del mar

0:11,7–0:27,3 · 3 tomas

**Lo que pasa:** las postales del mar

**Estilos:** `toma-por-frase`

**Evitar:** clips cortos para una canción larga: la cámara lenta pasa de la mitad y, sin cuadros interpolados (`clips_interpolar`), traba (toma-por-frase)

| Toma | Canción | Compases | Música | En pantalla | Se usan | Movimiento | Entra | Ojo |
|---|---|---|---|---|---|---|---|---|
| **T2-01** | 0:11,7–0:16,9 | 2 | calma | ×0,45 | 3,4 s | casi quieta: algo que respira, un paneo muy lento · `--motion low` | fundido |  |
| **T2-02** | 0:16,9–0:22,1 | 2 | calma | ×0,45 | 3,4 s | casi quieta: algo que respira, un paneo muy lento · `--motion low` | fundido |  |
| **T2-03** | 0:22,1–0:27,3 | 2 | media | ×0,47 | 3,3 s | suave y continua: un paneo, un acercamiento, gente que conversa · `--motion low` | fundido |  |

## T3 · entra la banda: la gente

0:27,3–0:53,4 · 5 tomas

**Lo que pasa:** entra la banda: la gente, cara por cara

**Estilos:** `transicion-iris`

**Evitar:** clips sin un sujeto claro: el círculo se abre desde cualquier parte (transicion-iris)

| Toma | Canción | Compases | Música | En pantalla | Se usan | Movimiento | Entra | Ojo |
|---|---|---|---|---|---|---|---|---|
| **T3-01** | 0:27,3–0:32,5 | 2 | media | ×0,42 | 2,9 s | suave y continua: un paneo, un acercamiento, gente que conversa · `--motion low` | iris | un sujeto claro: el círculo se abre desde él |
| **T3-02** | 0:32,5–0:37,8 | 2 | media | ×0,47 | 3,3 s | suave y continua: un paneo, un acercamiento, gente que conversa · `--motion high` | iris | un sujeto claro: el círculo se abre desde él |
| **T3-03** | 0:37,8–0:43,0 | 2 | media | ×0,49 | 3,4 s | suave y continua: un paneo, un acercamiento, gente que conversa · `--motion high` | iris | un sujeto claro: el círculo se abre desde él |
| **T3-04** | 0:43,0–0:48,2 | 2 | media | ×0,47 | 3,2 s | suave y continua: un paneo, un acercamiento, gente que conversa · `--motion high` | iris | un sujeto claro: el círculo se abre desde él |
| **T3-05** | 0:48,2–0:53,4 | 2 | media | ×0,46 | 3,2 s | suave y continua: un paneo, un acercamiento, gente que conversa · `--motion high` | iris | un sujeto claro: el círculo se abre desde él |

## T4 · la gente se atropella: hacia la ciudad

0:53,4–1:14,3 · 8 tomas

**Lo que pasa:** se atropellan, del pueblo a la ciudad, hasta un hombre que mira la refinería

**Estilos:** `clip-por-compas`, `golpe-de-zoom`

**Evitar:** pocos clips en una canción larga: en ronda se repiten varias vueltas (clip-por-compas)

| Toma | Canción | Compases | Música | En pantalla | Se usan | Movimiento | Entra | Ojo |
|---|---|---|---|---|---|---|---|---|
| **T4-01** | 0:53,4–0:56,0 | 1 | media | ×0,49 | 2,0 s | suave y continua: un paneo, un acercamiento, gente que conversa · `--motion high` | fundido | se queda un momento como estela sobre la que sigue |
| **T4-02** | 0:56,0–0:58,6 | 1 | media | ×0,47 | 2,0 s | suave y continua: un paneo, un acercamiento, gente que conversa · `--motion high` | fundido | se queda un momento como estela sobre la que sigue |
| **T4-03** | 0:58,6–1:01,2 | 1 | alta | ×0,50 | 2,1 s | viva: alguien que camina, agua, viento, la cámara que se mueve · `--motion high` | fundido | se queda un momento como estela sobre la que sigue |
| **T4-04** | 1:01,2–1:03,9 | 1 | alta | ×0,50 | 2,1 s | viva: alguien que camina, agua, viento, la cámara que se mueve · `--motion high` | fundido | se queda un momento como estela sobre la que sigue |
| **T4-05** | 1:03,9–1:06,5 | 1 | alta | ×0,50 | 2,1 s | viva: alguien que camina, agua, viento, la cámara que se mueve · `--motion high` | fundido | se queda un momento como estela sobre la que sigue |
| **T4-06** | 1:06,5–1:09,1 | 1 | alta | ×0,50 | 2,1 s | viva: alguien que camina, agua, viento, la cámara que se mueve · `--motion high` | fundido | se queda un momento como estela sobre la que sigue |
| **T4-07** | 1:09,1–1:11,7 | 1 | alta | ×0,50 | 2,1 s | viva: alguien que camina, agua, viento, la cámara que se mueve · `--motion high` | fundido | se queda un momento como estela sobre la que sigue |
| **T4-08** | 1:11,7–1:14,3 | 1 | media | ×0,43 | 1,8 s | suave y continua: un paneo, un acercamiento, gente que conversa · `--motion low` | fundido | se queda un momento como estela sobre la que sigue |

## T5 · el respiro

1:14,3–1:24,7 · 2 tomas

**Lo que pasa:** el respiro

**Estilos:** `toma-por-frase`, `polvo-de-luz`

**Evitar:** clips cortos para una canción larga: la cámara lenta pasa de la mitad y, sin cuadros interpolados (`clips_interpolar`), traba (toma-por-frase)

| Toma | Canción | Compases | Música | En pantalla | Se usan | Movimiento | Entra | Ojo |
|---|---|---|---|---|---|---|---|---|
| **T5-01** | 1:14,3–1:19,5 | 2 | calma | ×0,45 | 3,7 s | casi quieta: algo que respira, un paneo muy lento · `--motion low` | fundido |  |
| **T5-02** | 1:19,5–1:24,7 | 2 | media | ×0,49 | 3,7 s | suave y continua: un paneo, un acercamiento, gente que conversa · `--motion low` | fundido |  |

## T6 · el campo en doble exposición

1:24,7–2:06,5 · 8 tomas

**Lo que pasa:** el campo, un recuerdo encima de otro

**Estilos:** `doble-exposicion-siempre`

| Toma | Canción | Compases | Música | En pantalla | Se usan | Movimiento | Entra | Ojo |
|---|---|---|---|---|---|---|---|---|
| **T6-01** | 1:24,7–1:29,9 | 2 | media | ×0,46 | 2,9 s | suave y continua: un paneo, un acercamiento, gente que conversa · `--motion high` | fundido | va en doble exposición con la siguiente: zonas oscuras o un cielo liso dejan ver la otra |
| **T6-02** | 1:29,9–1:35,2 | 2 | media | ×0,49 | 3,1 s | suave y continua: un paneo, un acercamiento, gente que conversa · `--motion high` | fundido | va en doble exposición con la siguiente: zonas oscuras o un cielo liso dejan ver la otra |
| **T6-03** | 1:35,2–1:40,4 | 2 | media | ×0,49 | 3,0 s | suave y continua: un paneo, un acercamiento, gente que conversa · `--motion high` | fundido | va en doble exposición con la siguiente: zonas oscuras o un cielo liso dejan ver la otra |
| **T6-04** | 1:40,4–1:45,6 | 2 | media | ×0,48 | 3,0 s | suave y continua: un paneo, un acercamiento, gente que conversa · `--motion high` | fundido | va en doble exposición con la siguiente: zonas oscuras o un cielo liso dejan ver la otra |
| **T6-05** | 1:45,6–1:50,8 | 2 | media | ×0,47 | 3,0 s | suave y continua: un paneo, un acercamiento, gente que conversa · `--motion high` | fundido | va en doble exposición con la siguiente: zonas oscuras o un cielo liso dejan ver la otra |
| **T6-06** | 1:50,8–1:56,0 | 2 | media | ×0,49 | 3,1 s | suave y continua: un paneo, un acercamiento, gente que conversa · `--motion high` | fundido | va en doble exposición con la siguiente: zonas oscuras o un cielo liso dejan ver la otra |
| **T6-07** | 1:56,0–2:01,2 | 2 | alta | ×0,50 | 3,1 s | viva: alguien que camina, agua, viento, la cámara que se mueve · `--motion high` | fundido | va en doble exposición con la siguiente: zonas oscuras o un cielo liso dejan ver la otra |
| **T6-08** | 2:01,2–2:06,5 | 2 | alta | ×0,50 | 3,1 s | viva: alguien que camina, agua, viento, la cámara que se mueve · `--motion high` | fundido | va en doble exposición con la siguiente: zonas oscuras o un cielo liso dejan ver la otra |

## T7 · llega el petróleo

2:06,5–2:16,9 · 2 tomas

**Lo que pasa:** cuando la banda se apaga llega el petróleo

**Estilos:** `transicion-destello`, `barras-de-cine`

**Evitar:** más de una vez cada pocos compases: una luz que pega seguido cansa (y molesta a quien es sensible a los destellos) (transicion-destello); un cuadro vertical: las franjas se comen dos tercios de la imagen (barras-de-cine); sujetos pegados al borde de arriba o de abajo (barras-de-cine)

| Toma | Canción | Compases | Música | En pantalla | Se usan | Movimiento | Entra | Ojo |
|---|---|---|---|---|---|---|---|---|
| **T7-01** | 2:06,5–2:11,7 | 2 | media | ×0,52 | 3,3 s | suave y continua: un paneo, un acercamiento, gente que conversa · `--motion low` | destello | entra con un fogonazo: aguanta bien una luz fuerte |
| **T7-02** | 2:11,7–2:16,9 | 2 | media | ×0,48 | 3,0 s | suave y continua: un paneo, un acercamiento, gente que conversa · `--motion low` | destello | entra con un fogonazo: aguanta bien una luz fuerte |

## T8 · el silencio

2:16,9–2:27,3 · 2 tomas

**Lo que pasa:** el silencio de la canción se queda con el petróleo

**Estilos:** `toma-por-frase`, `barras-de-cine`, `pelicula-gastada`

**Evitar:** clips cortos para una canción larga: la cámara lenta pasa de la mitad y, sin cuadros interpolados (`clips_interpolar`), traba (toma-por-frase); un cuadro vertical: las franjas se comen dos tercios de la imagen (barras-de-cine); sujetos pegados al borde de arriba o de abajo (barras-de-cine); encima de rótulos chicos: las manchas se confunden con la letra (pelicula-gastada)

| Toma | Canción | Compases | Música | En pantalla | Se usan | Movimiento | Entra | Ojo |
|---|---|---|---|---|---|---|---|---|
| **T8-01** | 2:16,9–2:22,1 | 2 | calma | ×0,45 | 3,7 s | casi quieta: algo que respira, un paneo muy lento · `--motion low` | fundido |  |
| **T8-02** | 2:22,1–2:27,3 | 2 | calma | ×0,45 | 3,7 s | casi quieta: algo que respira, un paneo muy lento · `--motion low` | fundido |  |

## T9 · vuelve el mar

2:27,3–3:01,2 · 3 tomas

**Lo que pasa:** vuelve el mar: una orilla, el cementerio frente al agua y el mismo bote del principio

**Estilos:** `toma-por-frase`, `postal`, `sonando-ahora`

**Evitar:** clips cortos para una canción larga: la cámara lenta pasa de la mitad y, sin cuadros interpolados (`clips_interpolar`), traba (toma-por-frase)

| Toma | Canción | Compases | Música | En pantalla | Se usan | Movimiento | Entra | Ojo |
|---|---|---|---|---|---|---|---|---|
| **T9-01** | 2:27,3–2:38,1 | 4 | calma | ×0,45 | 6,2 s · extender | casi quieta: algo que respira, un paneo muy lento · `--motion low` | fundido |  |
| **T9-02** | 2:38,1–2:48,3 | 4 | calma | ×0,45 | 6,0 s · extender | casi quieta: algo que respira, un paneo muy lento · `--motion low` | fundido |  |
| **T9-03** | 2:48,3–3:01,2 | 3 | calma | ×0,45 | 7,2 s · extender | casi quieta: algo que respira, un paneo muy lento · `--motion low` | fundido |  |

## Para el montaje

Con los clips en su carpeta, cada tramo los toma en orden:

```json
{"nombre": "el mar despierta", "material": ["T1-"]},
{"nombre": "las postales del mar", "material": ["T2-"]},
{"nombre": "entra la banda: la gente", "material": ["T3-"]},
{"nombre": "la gente se atropella: hacia la ciudad", "material": ["T4-"]},
{"nombre": "el respiro", "material": ["T5-"]},
{"nombre": "el campo en doble exposición", "material": ["T6-"]},
{"nombre": "llega el petróleo", "material": ["T7-"]},
{"nombre": "el silencio", "material": ["T8-"]},
{"nombre": "vuelve el mar", "material": ["T9-"]},
```
