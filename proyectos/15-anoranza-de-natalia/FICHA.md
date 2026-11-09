# 15 · Añoranza de Natalia

**Fecha:** 2026-11-08 (de noche: Miguel dejó el material y la sesión trabajando hasta la mañana)

## Idea

El primer ejercicio del paquete de práctica, y el primero con **clips** en vez de
imágenes. Miguel: «una mezcla de la primera con la segunda», entre las dos ideas
que le propuse: **que siga la canción** (cortes al pulso) y **que se sienta como
un recuerdo** (fundidos, doble exposición, calma). El nombre es suyo.

## Material

- **20 clips** de Miguel, en `~/Videos/montaje/practica/clips/` (biblioteca
  `practica`), numerados y agrupados por él: lanchas (1–5), playa (6–9), hamacas
  (10–11), campo (12–20). Postales de costa y campo con color de película vieja;
  768×512 (3:2), 24 cps, 5,1–5,2 s cada uno: **104 s de material**.
- **«La Añoranza de Natalia»** (`practica/musica/`), WAV 48 kHz: 3:01, 92,3 BPM,
  seis secciones (intro calma hasta 0:27, dos tramos plenos 0:27–1:14 y 1:24–2:18
  con un respiro entre ellos, un quiebre casi en silencio 2:18–2:28 y una salida
  en calma). Es la canción de la abuela de Miguel; experimento privado.

## Lo que pide el material

- **3:2, 1620×1080, a 24 cps.** La forma de los clips (sin recortar) y su cadencia:
  pasar 24 a 30 hace que el movimiento tironee.
- **Cámara lenta.** 104 s para 181 s de canción: los clips van entre 0,33× y 0,75×.
  Para que no trabe, las copias de trabajo se hacen a **48 cps con cuadros
  inventados** (`clips_interpolar: 2`, `minterpolate`); revisados de cerca en la
  bicicleta, el perro y el agua: sin deformaciones visibles.
- Clips hechos sin el pulgar en el botón: `borde_toma` 0,1 s en vez de 0,35.

## Técnica nueva: clips en el motor

- `clips <p>`: copias de trabajo (giradas, HDR→SDR, cadencia pareja, interpoladas
  si se pide) y las curvas de cada clip (movimiento sin la cámara, cámara,
  temblor, nitidez, luz, cortes) → `analisis/clips.json` y `hojas/clips.png`.
- Modo **`pulso`** (`py/montaje/pulso.py`): cada clip ocupa frases de la canción y
  dentro de ellas salta al pulso entre sus mejores momentos; fundidos entre clips;
  fantasmas en `screen` (doble y estela); más lento en la calma; `reparto: ronda`
  (los clips vuelven en orden, cada vuelta con otros momentos) y
  `frase_compases_calma` (frases más largas donde la música descansa).
- `versiones` en proyecto.json y `--version` en `planificar`/`render`.
- Capas de **síntesis** (`sintesis`, src/Sintesis.tsx) y clips **transformados**
  (`transformar`): ver la skill.

## Las versiones

| | Nombre | Qué hace |
|---|---|---|
| a | **Una toma por frase** | un clip por frase de 4 compases (≈10 s), de corrido, en cámara lenta (≈0,42×); fundidos de 2 golpes, de 4 en la calma. Lo más «recuerdo». |
| b | **Un clip por compás** | cambia de clip en cada compás (≈2,6 s; cada dos en la calma), los 20 en ronda, tres vueltas con otros momentos; fundido corto (¼ de golpe) y una estela de 1,5 golpes del que se va. Lo más «pulso». |
| c | **Respira con la canción** | dos compases por clip en lo pleno, cuatro en la calma (con el clip que viene asomándose en doble exposición 4 golpes antes); ronda: en la salida vuelven las lanchas y la playa. La mezcla. |
| c-recuerdo | c + **textura de recuerdo** | grano, viñeta, parpadeo, temblor de proyector, halo, fugas de luz cada 8 compases y polvo. |
| sola | **la canción sola** | sin clips: campo de color, la partitura de la canción, polvo y grano. Una idea de pieza hecha sólo en código. |

## Renders

En `~/Videos/montaje/15-anoranza-de-natalia/render/`.

## Arreglos del motor (2026-11-09)

La revisión del motor (ver la ficha del 21) cambia `b` y `c`; **la `a`, la aprobada, planifica idéntico.**

- `b`: de 54 cambios de clip, sólo 32 tenían su estela (las otras se perdían sin aviso); ahora las 54.
- `c`: 6 estelas de 27 → 27; y de sus 6 dobles, 5 no empalmaban con la toma que entraba (saltos de hasta 1,03 s) → empalman.
- Renders con el motor arreglado: `b-final-arreglado.mp4`, `c-final-arreglado.mp4` (los de la noche quedan al lado para comparar).
- Las muestras de `fugas-de-luz`, `polvo-de-luz` y `textura-de-recuerdo` salieron de `c-recuerdo` antes del arreglo: muestran la capa de síntesis, que no cambió.

## Lo que dijo Miguel

- Versión a (una toma por frase): «Esta buenísimo. Me gustó».

## Aprendido

- Remotion copia la carpeta pública entera en cada render: con clips se arma
  `.publico/` con vínculos duros de lo usado (los simbólicos los rechaza su
  servidor). Sin tope de caché, el compositor se quedó sin memoria a los 53 s.
- `trimBefore` va en cuadros de la composición y no lo afecta `playbackRate`.
