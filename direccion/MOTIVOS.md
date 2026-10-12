# Motivos

Los recursos que vuelven de un video a otro y hacen que se reconozcan como de
Curiana Radio. **Estado:** *aprobado* (Miguel lo dijo), *pedido* (Miguel lo pidió
y está hecho, falta su veredicto), *propuesta* (de Claude).

| Motivo | Qué es | Estado | Dónde vive |
|---|---|---|---|
| **Collage infinito** | papeles nítidos al 100 % que caen al pulso y se quedan; la cámara se aleja | aprobado: «Excelente» (03) | `modo: collage` |
| **Carrusel** | imágenes cuadradas de marca a pantalla completa, una por semicorchea, cortes secos | aprobado: «me gustó muchísimo» (05, 07) | `momentos` `rafaga` con `"de": "marca"` |
| **Destacado de marca** | el collage se detiene y oscurece; una imagen con «Curiana Radio» al frente, respira y vuelve a su lugar | pedido (05) | `destacado` con `"img": "marca"` |
| **Sello que late** | el isotipo en una esquina, late en cada primer tiempo y se esconde cuando un momento ocupa el cuadro | pedido (05) | `logo.sello` |
| **Salvapantallas** | en el silencio de la canción, el logo suelto rebota por el cuadro como el del DVD y cambia de versión en cada borde | pedido (05) | `logo.salvapantallas` |
| **Firma** | el logotipo completo al frente en el último compás | propuesta (05, 07) | `destacado` con `"firma": true` |
| **Cortinas** | piezas cortas con su propio sonido que cortan el programa | idea de Miguel (08) | `ensamblar` |
| **Loop sin costura** | el último cuadro empalma con el primero | pedido (06) | `modo: cinta` |
| **Barrido** | la cámara salta de golpe a otra zona del collage | propuesta (04, 05) | `barrido` |
| **La radio en el sonido** | estática AM y silbido de sintonía en el silencio; los rebotes del logo afinados a la canción | propuesta (09) | `sonorizar` |

## Por hacer (propuestas)

- **«Sonando ahora»:** el crédito de la canción como lo mostraría una emisora:
  cartel + dato en mono, oro de arena, abajo a la izquierda, unos segundos al
  empezar. Resuelve además el crédito en pantalla.
- **Dial 88.8:** una aguja que recorre una escala en las transiciones; aparece
  con la estática.
- **La espiral:** el trazo del isotipo dibujado en código (canvas), como
  transición o como marco que se arma, pariente del marco de espirales del
  video de Gemini.
- **Tipos de corte rápido:** acelerando, sincopado, estroboscópico, raccord,
  tartamudeo y destello blanco, como variantes del carrusel.
