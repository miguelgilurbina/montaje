# El molde de un experimento

Miguel, el 2026-11-22: «También armar templates de trabajo para poder armar trabajo más adelante». Uno de los tres
moldes que eligió es éste: el paso a paso para sumar un efecto nuevo a la galería siempre igual. Sale de cómo se
hicieron del 24 al 31.

`python montaje.py experimento <NN-nombre> --titulo "…" --idea "…" --cita "…"` arma el comienzo:

- la carpeta, con su `proyecto.json` sobre el banco del probador;
- la `FICHA.md` con sus secciones;
- la fila en `EXPERIMENTOS.md`, con el veredicto en «—».

Lo demás son estos pasos.

## Los pasos

1. **La idea, con sus palabras.** Lo que dijo Miguel va entre comillas, tal cual, en la ficha (`--cita`) y en
   `direccion/REGISTRO.md`. Si hay que elegir entre caminos, se pregunta en tarjetas: una por punto, la recomendada
   primero.
2. **¿Es nuevo de verdad?** Antes de sumar un estilo hay que preguntarse:
   - si es una **variante** de otro (cambia un detalle: `variante_de` y `diferencia`);
   - si es un **gesto** (un momento encima de cualquier base: `gesto: true` y `sobre`).

   Medir el parecido con lo que ya hay (el 26 lo hizo cuadro a cuadro).
3. **El aparato o la capa.**
   - Lo analógico es un aparato de la mesa: un módulo en `py/montaje/` con `APARATOS`, `POR_DEFECTO`, `RANGOS`,
     `errores`, `calentar` y lo que recuerda en `ctx.estado`. Se suma en `analogo._imagen`.
   - Si es un gesto, va en `GESTOS` y en `componer`, con su lugar en la cadena.
   - Lo que es de norma va con su fuente; lo demás, marcado [sin verificar].
4. **El sonido en su momento.**
   - Si el efecto tiene un momento audible (un botón, un motor, una señal), lleva su perilla `sonido` y su ruido en
     `ruidos.py`.
   - Los eventos del sonido son los de la imagen: la misma semilla, `_paso`, `eventos_en`.
   - Claude no oye: mide que caiga donde se ve, y el oído es de Miguel.
5. **Mirar antes de opinar.**
   - Una hoja de cuadros sueltos con el aparato solo, en los momentos que importan.
   - Corregir lo que se ve mal antes de seguir (la quema en islas, la riso que parecía estática).
6. **Los estilos.** `estilos/<id>.json` con:
   - `estado: propuesta`;
   - `visto_en` en el experimento;
   - la `frase` de lo que se ve y lo que suena;
   - `evitar` con la regla del tono (lo analógico, sólo en ventanas sobre una imagen protagonista de la galería).

   Si un gesto o un evento tiene que caer dentro de la muestra, se elige su `semilla` midiendo con `eventos_en`.
7. **Las pruebas.** En `py/pruebas/`: que el aparato no toque nada sin sus perillas, que haga lo que dice y que el
   sonido caiga donde la imagen. `python -m pytest py/pruebas -q`.
8. **El probador.**
   - `python montaje.py probar <ids>` saca las muestras sobre el mismo banco.
   - Después, una hoja de cuadros de las muestras en los segundos de los eventos, y un espectrograma con lo que
     cambia la imagen debajo, para ver que el ruido cae donde pasa algo.
   - Si cambia el código de un estilo ya probado: `--rehacer`.
   - No se edita el código mientras el probador corre.
9. **La ficha.**
   - Qué se hizo y por qué.
   - Lo que midió Claude, con los números de la medida, no a mano.
   - Lo que dijo Miguel.
10. **La mesa.**
    - Las muestras nuevas van a la Mesa de montaje (un artifact privado; su dirección no va al repo), en «por
      juzgar», con lo que suena.
    - Una versión de la mesa tiene un tope de 511 archivos: las miniaturas de lo nuevo pueden ir dentro de la página.
    - Un estilo rehecho lleva `r`: un veredicto anterior ya no cuenta.
11. **El veredicto.**
    - Se lee la base de la mesa (`veredictos`) y cuenta sólo lo que llegó después de `r`.
    - Se anota: `python montaje.py veredicto <id> <estado> --via galeria`.
    - La fila de `EXPERIMENTOS.md` y la ficha llevan lo que dijo.
    - Un «no» o un «a medias» sin porqué se pregunta; antes de cambiar algo ya juzgado, se pregunta qué molesta.
12. **El commit, con su ok.**
    - Por ruta (nunca `git add -A`).
    - Sin `AGENTS.md` ni los timelines del 22.
    - Antes de subir, el grep de privacidad (el repo es público).
    - Subir es con su ok, y mergear lo decide Miguel.
