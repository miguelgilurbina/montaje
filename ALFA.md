# La alfa pública

Miguel, el 2026-11-23: «pensar en lo que sería una versión alfa para publicar. Tenemos que pensar además en un vídeo
interesante de teaser. Para publicarlo como open source».

El repo ya es público y MIT desde el 2026-10-13. La alfa es otra cosa: **la primera versión que se anuncia**, con una
etiqueta (`v0.1.0-alfa`), sus notas, un teaser y un modo de probarla sin material propio. Nada de esto se publica sin
el ok de Miguel; este archivo es el plan y la lista.

## Qué la distingue

Editar video con un agente ya tiene proyectos conocidos: video-use (browser-use, MIT) y OpenMontage (AGPL-3.0), este
último con casi la misma pila (Python, Remotion, FFmpeg, un CLAUDE.md) y README en español. Anunciar «un agente que
edita video» llega tarde. Lo que montaje tiene y ellos no:

1. **La mesa analógica**: los aparatos simulados en su señal (la cinta, la antena, el tubo, la película, la imprenta,
   el cine mudo, los juguetes ópticos), cada uno con sus referencias y su sonido.
2. **La consola de diales**: la mesa a mano, en vivo, con lo grabado renderizado por el motor.
3. **La galería con veredictos**: cada estilo con su muestra en el mismo banco y lo que dijo quien dirige.
4. **El corte al pulso**: la canción leída como números (golpes, compases, energía) y el montaje que la sigue.
5. **En español, de punta a punta**, a propósito.

El anuncio abre con 1 y 2 (se ven en dos segundos) y deja al agente para el párrafo siguiente.

En Hacker News lo analógico y el glitch tienen buena acogida (ntsc-rs, FFglitch y cables.gl pasaron los 250 puntos,
medido el 2026-11-23), y los Show HN recientes de editores con agente quedaron entre 1 y 4. La crítica que más se
repitió a ntsc-rs fue «demasiados controles»: por eso la consola parte de las cadenas de la galería y no de una
pared de perillas.

## Lo que entra en la alfa

- Todo el flujo de montaje al pulso (catálogo, música, planificar, render, hojas, panel), como está.
- La mesa analógica con todos sus aparatos y la galería de estilos.
- La consola de diales (`/consola`), con la automatización en el motor (`analogo --automatizacion`).
- `python montaje.py demo`: el material de prueba hecho con código, CC0, para probar sin nada propio.

## Dónde se probó

Sólo en Windows 11, con Node 22.19, Python 3.13.7, ffmpeg 8.1.1 y un navegador Chromium. Las notas de la alfa lo
dicen así: macOS y Linux sin probar. Web MIDI anda en Chrome y en Firefox (con el complemento de permiso), no en
Safari.

## La lista antes de anunciar

Cada punto lo decide o lo hace Miguel; lo marcado ✓ ya está en el repo.

- [x] La consola, sus pruebas y `direccion/CONSOLA.md`.
- [x] El material de prueba (`demo`) y la sección «Probar sin material propio» del README.
- [x] Las licencias de lo estudiado, separadas en `direccion/CONSOLA.md`; la de Remotion, en el README.
- [ ] **Revisión de privacidad antes de subir** (el repo es público): que no entren los timelines del 22, `AGENTS.md`,
      nada del proyecto 23, ni direcciones de páginas privadas. Un `git grep` de nombres y rutas personales sobre lo
      que se va a subir, como antes de cada push.
- [ ] **El teaser** (`direccion/TEASER.md`): elegir concepto y material, y hacerlo con montaje mismo.
- [ ] **Las notas de la versión** (abajo, en borrador) y la etiqueta `v0.1.0-alfa`.
- [ ] **Una prueba en otra máquina**, desde cero: clonar, instalar, `demo`, panel, consola, render. Si se puede, en
      macOS o Linux.
- [ ] **Dónde anunciar** (abajo) y en qué orden.
- [ ] *(Después de la alfa)* La consola como página estática con el material de prueba, para probarla en el navegador
      sin instalar nada. Hacker News pide eso: que se pueda probar sin registrarse.

## Las notas de la versión (borrador)

> **montaje v0.1.0-alfa**
>
> Editar video con un agente de IA, en español, con una mesa de aparatos analógicos simulados en su señal.
>
> - La consola de diales: el video pasa en vivo por la cinta, la antena, el tubo, la película, la imprenta o el cine
>   mudo, y cada perilla se gira con el mouse o un controlador MIDI. Lo que se gira con el video corriendo queda
>   grabado y el motor lo renderiza igual.
> - La galería: cada estilo con su muestra y su veredicto.
> - El montaje al pulso: la canción leída como números y los cortes que la siguen.
> - `python montaje.py demo` para probar sin material propio.
>
> Es una alfa: se probó en Windows 11. Remotion tiene su propia licencia (gratis para personas y empresas chicas).
>
> *English:* a text-first video editing harness for working with an AI agent, in Spanish, with a desk of analog
> devices simulated in their signal (tape, antenna, CRT, film, print, silent-film color) and a dial console to play
> them live. What you turn while the video runs is recorded and rendered by the engine.

## Dónde anunciar

- **Show HN** (en inglés, con el loop arriba): sus reglas piden que se pueda probar, nada de registros ni páginas de
  aterrizaje, contar por qué se hizo y quedarse a responder.
- **CDM** (cdm.link), que cubrió Hydra y cables.gl; el foro **lines** (llllllll.co); Mastodon (post.lurk.org,
  merveilles.town).
- **En español**: los proyectos que crecieron en la región lo hicieron con talleres y comunidad local (Hydra en
  Medellín y Bogotá; Flok); vale más un taller o una charla que un post. Y la difusión de Curiana Radio.
- **Product Hunt**, como Remotion y ntsc-rs, si Miguel quiere.

## Lo que no hay que hacer

- Prometer de más: Olive anunció una 0.2 que nunca salió. La alfa dice lo que anda y lo que no.
- Subir clips de bancos de imágenes al repo (Pexels y Pixabay prohíben redistribuirlos sueltos): el material de
  prueba se genera con código.
- Copiar shaders GPL, Shadertoy (no comercial por defecto) o Hydra (AGPL) a un repo MIT.
