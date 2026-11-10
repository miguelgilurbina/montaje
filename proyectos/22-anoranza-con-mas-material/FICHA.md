# 22 · Añoranza con más material

**Fecha:** 2026-11-09 (primer preview armado, esperando a Miguel)

## Idea

Miguel, después de mirar la galería: «un vídeo así de largo. O más bien audio. Se hace
muy corto usar 20 videos. Me gustaría que hiciéramos una nueva iteración del vídeo.
Pero con más contenido». Y sobre cómo: «Aún no la armemos. Vamos primero a seleccionar.
Ahí yo meteré la mano de cuales elegir».

La cuenta: la canción tiene 67 compases. Un clip cada dos compases son 34; uno por compás
en la banda y uno cada dos en el resto, unos 52.

## Material

- Los 20 clips de la práctica (`clips/`).
- 99 clips de Midjourney (`clips-mj/`), copiados del zip que Miguel tenía guardado (106 clips,
  7 ya estaban entre los 20). El zip no se tocó. Sus prompts están en
  `practica/analisis/clips-mj.json`.
- Falta lo que Miguel tiene clasificado en Midjourney: se recorre cuando inicie sesión en el
  navegador del PC. Permiso que dio: «Mirar, clasificar y bajar», sin generar; antes de bajar se le dice cuántas son y
  cuánto pesan.

## La mesa de selección

`python montaje.py seleccion 22-anoranza-con-mas-material`: de cada clip, una muestra muda de cinco
segundos, un cuadro fijo, sus medidas y un grupo sacado del prompt (119 candidatos: ficción 27, campo
23, gente 17, mar 15, historia 15, ciudad 14, petróleo 6, otros 2). No decide nada.

Miguel elige desde el teléfono, en una página privada de claude.ai que también trae la galería de
estilos. Lo que marca queda en la base de esa página (`seleccion/<id>` y `veredictos/<id>`) y Claude lo
trae: lo elegido a `proyectos/22-…/seleccion.json` (`seleccion.guardar`) y los veredictos con
`montaje.py veredicto`. Desde que existe `seleccion.json`, el proyecto sólo ve esos clips.

Las copias de trabajo interpoladas (`clips <p>`) se hacen después, sólo de lo elegido.

## Lo que eligió

34 clips desde el teléfono (`seleccion.json`): 20 nuevos de Midjourney y 14 de los 20 originales. Por grupo:
gente 10, campo 10, mar 7, petróleo 4, ciudad 3. Da justo un clip cada dos compases sin repetir ninguno. Dejó fuera
seis de los originales: casa de palma, perro, palmeras en la laguna, curiara, árboles sobre la arena y casa blanca.

## El armado

Con «Dale, hagámoslo», Claude propuso un guion (`GUION.md`) de nueve tramos con estilos aprobados, cada clip una sola
vez. Los grupos de la mesa salían del texto de los prompts; al mirar los clips se repartieron por lo que se ve (el hombre
frente a la refinería estaba en «ciudad», la garza en «gente»). Hay dos pares casi iguales: el bote desde el restaurante
abre y cierra; el ciclista va una vez en la ciudad y otra en el campo. Lo que Miguel tenga clasificado en Midjourney no
entró todavía.

Técnica nueva: `material_en_orden` en un tramo, para que la lista de `material` diga también el orden.

## Render

`~/Videos/montaje/22-anoranza-con-mas-material/render/preview.mp4`: 3:01, 810×540, 19 MB. `revisar`: sin negro, sin
cuadros repetidos, 1 destello por segundo como máximo, −15,6 LUFS. El preview entero tardó 2:40 y corregir el título (un
tramo), 17 s. El final todavía no se ha hecho.

## Lo que dijo Miguel

«Mira, de 10 le doy un 6. Tiene partes que se sincronizan muy bien, y encuentro que se nota un uso muy bueno de la galería que estamos haciendo. Pero siento que no está del todo listo. O sea quedó bien, pero no es uff, muy buen ejemplo, creo que igual es porque estamos usando material ya hecho, nada producido específicamente para este video. Pero igual creo que es buen score.»

El preview del 2026-11-09, antes de cualquier corrección.

Sobre qué sincronizó mejor: «Las finales, siento que el primer tramo o la primera mitad del video no calzó al 100 con el feel porque los videos estaban en velocidad normal en muchos casos, y al final si se hicieron esos ajustes a la velocidad ya que justo la canción lleva a eso.»

Medido en el plan: los tramos con banda iban a ×0,63–0,75 (gente, ciudad y campo) y el final a ×0,39. La versión `lenta` lleva esos tres tramos a ×0,40–0,50.

## La letra en pantalla

Miguel, sobre la versión lenta: «excelente, ahora lo único que agregaría sería subtitulos de la canción en el medio.
Puedes hacrr la transcripción ?». `transcribir --cancion` en este computador (38 s para 3:01; 136 palabras, 9 dudosas,
27 líneas) y una capa de `rotulos` que lee el `.srt` de `~/Videos/montaje/transcripciones/`: al centro, palabra por
palabra cuando se canta. La letra no se copió al proyecto; la revisa y corrige Miguel en el `.srt`. Con fondos claros
no se leía: letra a 0,064 y halo a 0,78.
