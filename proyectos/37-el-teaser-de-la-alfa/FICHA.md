# 37 · El teaser de la alfa

**Fecha:** 2026-11-23

## Idea

Un video corto para anunciar la alfa pública (`ALFA.md`), hecho con montaje mismo y con material generado con código:
la imagen que se sintoniza, los aparatos uno tras otro y la marca que dibuja el sonido. Los tres conceptos, sus
referencias y lo que falta decidir están en `direccion/TEASER.md`.

## Material

El material de prueba (`python montaje.py demo`, CC0): el cielo con sol. Nada de la biblioteca de nadie, para que el
borrador se pueda mostrar en cualquier parte. El material del teaser final lo elige Miguel.

## Lo que se hizo

`armar.py` arma el borrador en cuatro partes, todas por el motor (`analogo`), y las junta:

1. **Sintonía** (3,5 s): antena → dial (88.8, `inicio`) → tubo. La nieve, el rodar y el desenganche bajan a mano:
   `sintonia.json` es lo que grabaría la consola girando esas tres perillas (`--automatizacion`).
2. **Los aparatos** (16 s, `--recorrido`): tal cual, cinta gastada, Super 8 de la familia, película tintada,
   risografía, moiré, destello de sol e imán en el televisor, dos segundos cada uno sobre el mismo tramo.
3. **La marca** (5 s): el osciloscopio dibuja MONTAJE con las letras de la marca (`dibujo: nombre`, tinta oro); el
   sonido es el dibujo.
4. **El cartón** (3,5 s): «montaje · editar video con un agente, en español · una mesa de aparatos analógicos · alfa ·
   MIT» y la dirección del repo, por el tubo.

Salida: `<medios>/37-el-teaser-de-la-alfa/borrador.mp4` (28 s), con sus partes en `partes/` y la hoja en `hojas/`.

## Lo que midió Claude (que no oye)

- La hoja cada medio segundo (`hojas/borrador-cada-medio.png`): la nieve rueda con la escala del dial abajo y la
  imagen sale a los 2,5 s; los ocho tramos del recorrido con su nombre; MONTAJE de 19,5 a 24,5; el cartón al final.
- Cuadros: 840 de 840 (28 s a 30). La primera vez el borrador salió de 24,6 s: el filtro `concat` de ffmpeg perdía
  cuadros del recorrido (cosido de pedazos, con cuadros B) aun renumerándolos (480 → 423). Se junta con el
  «demuxer» de concat, que no pierde ninguno.
- El dial antes de la antena quedaba tapado por la nieve; va entre la antena y el tubo (el tubo va siempre al final).
- Lo que veo flojo, para la próxima vuelta:
  - los dos segundos de «tal cual» son tiempo muerto en un teaser;
  - las letras del osciloscopio salen finas y quedan demasiado (5 s);
  - el sonido es el pulso del material de prueba: la música la decide Miguel, y el oído es suyo.

## Lo que dijo Miguel

- «Tenemos que pensar además en un vídeo interesante de teaser. Para publicarlo como open source.»

## Veredicto

Por juzgar.
