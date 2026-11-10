# Cantera: el contenedor

**Construida la versión 1 el 2026-11-09** en `../cantera` (repo local, sin subir a GitHub): ver su README.
Lo que sigue es el diseño con que se decidió.

Una infraestructura aparte de `montaje`, abierta como él: un lugar donde guardar y clasificar el
material de un proyecto de video —series de Midjourney, clips, fotos, documentos— y desde donde
alimentar un montaje. Miguel: «La idea es levantar una infraestructura aparte que sea interesante
para este proyecto que al final es un proyecto opensource».

## Lo decidido (2026-11-09)

| Punto | Decisión |
|---|---|
| Dónde guarda | Disco propio o cualquier servicio compatible con S3 (Cloudflare R2, Backblaze, MinIO). Nada que obligue a usar un proveedor. |
| Código | Repo nuevo y público, hermano de `montaje`. Se crea en local; a GitHub sólo con el ok de Miguel. |
| Primera versión | Subir, series y etiquetas, conexión con `montaje`. |
| Orden | «Primero desde el desktop. Luego vemos la conexión del cel.» |
| Afuera por ahora | Importar lo de Midjourney con sus metadatos y el acceso desde el teléfono. |
| Nombre | **Cantera**: de donde sale el material en bruto antes de labrarlo; `montaje` lo labra. (2026-11-09) |
| Lenguaje | **TypeScript con Next**, como el panel de `montaje`. (2026-11-09) |

## Propuesta para la primera versión

Un solo programa que se levanta con un comando y escucha en el computador, como el panel de `montaje`.

- **Almacén.** Una interfaz con cuatro verbos (guardar, leer, borrar, listar) y dos salidas: `disco` y
  `s3`. Se elige en un archivo de configuración; las claves, por variables de entorno, nunca en el repo.
- **Índice.** Una base SQLite con piezas (archivo, tipo, tamaño, huella, medidas), series, etiquetas y
  estrellas. La huella evita guardar dos veces lo mismo. El índice se puede rehacer desde el almacén.
- **Pantalla.** Galería con filtros, subida arrastrando, crear series y etiquetar de a muchos.
- **API.** Listar, leer y marcar piezas: lo que usan la pantalla, los scripts y `montaje`.
- **Con `montaje`.** Un comando trae a la biblioteca de un proyecto lo que esté en una serie, por
  ejemplo `python montaje.py traer <p> --serie anoranza`, y de ahí sigue a la mesa de selección.

## Lo que falta decidir

- Qué servicio S3 usará Miguel. Se mide cuánto material hay antes de elegir.
- La licencia del repo.
