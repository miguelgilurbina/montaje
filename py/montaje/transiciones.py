"""Las transiciones: cómo entra una imagen o un clip sobre el que se va. Las dibuja `src/Montaje.tsx`
(`transicionDe`); aquí se eligen, para `pulso` y para los modos de fotos.

- Las de siempre: fundido, cortina, iris, empuje, destello, zoom, persiana.
- Las del 2026-11-23 (G1/K1 de PROPUESTAS.md; la idea de tenerlas juntas volvió al mirar el catálogo de OpenMontage,
  y están hechas desde cero): **luz** (lo claro de la nueva primero), **desenfoque** (llega desenfocada), **doble**
  (doble exposición pasajera), **quemado** (la película que se quema desde un borde), **sacudon** (entra de golpe y
  tiembla), **separacion** (los colores llegan corridos), **pixeles** (se arma por bloques), **latigazo** (el paneo
  rápido) y **cinta** (la idea de Miguel del 2026-11-09: «la imagen siguiente se agranda», llega chica desde el
  costado y crece).

La `ronda` recorre sólo las de siempre que no están rechazadas: si las nuevas entraran solas, cambiaría lo que Miguel
ya juzgó (el 21 tiene una ronda). Las nuevas se piden por su nombre.
"""

from __future__ import annotations

import functools

from .rutas import salir

TRANSICIONES = ("fundido", "cortina", "iris", "empuje", "destello", "zoom", "persiana",
                "luz", "desenfoque", "doble", "quemado", "sacudon", "separacion", "pixeles", "latigazo", "cinta")
#: Las que recorre la ronda (las de antes del 2026-11-23).
RONDA = ("cortina", "iris", "empuje", "destello", "zoom", "persiana")
DIRECCIONES = {"derecha": [1, 0], "izquierda": [-1, 0], "abajo": [0, 1], "arriba": [0, -1]}
#: Las que corren a la que se va: sale por el otro lado en los mismos cuadros.
EMPUJAN = ("empuje", "latigazo")
#: Las que se mezclan con la que se va (aclarar, sumar): la que se va se apaga en esta parte final de la entrada,
#: si no, al terminar la transición la imagen saltaría.
APAGAN = {"luz": 0.45, "doble": 0.45}


@functools.lru_cache(maxsize=1)
def en_ronda() -> tuple[str, ...]:
    """Las transiciones que recorre la `ronda`: las de siempre menos las que Miguel rechazó en la galería
    (el estilo `transicion-<tipo>`). La persiana entraba a la ronda aunque la había rechazado (2026-11-10)."""
    from . import estilos

    rechazadas = {e["id"].removeprefix("transicion-") for e in estilos.leer()
                  if e["id"].startswith("transicion-") and e.get("estado") == "rechazado"}
    return tuple(t for t in RONDA if t not in rechazadas) or RONDA


def elegir(tipo: str, direccion: str, n: int) -> tuple[str, list[int]] | None:
    """La transición del `n`-ésimo cambio: (tipo, hacia dónde). None = fundido.

    `ronda` recorre las de la ronda, una por cambio; `alterna` va a la derecha y a la izquierda.
    """
    pedido = tipo
    if tipo == "ronda":
        tipo = en_ronda()[n % len(en_ronda())]
    if tipo not in TRANSICIONES:
        salir(f"transicion desconocida: {tipo} (hay: {', '.join(TRANSICIONES)}, ronda)")
    if tipo == "fundido":
        return None
    d = direccion
    if d == "alterna":
        # En una ronda de un número par de tipos, si el lado dependiera sólo de `n`, cada tipo saldría
        # siempre para el mismo lado: cada vuelta empieza por el otro. Con un número impar ya cambia solo.
        k = len(en_ronda())
        vuelta = n // k if pedido == "ronda" and k % 2 == 0 else 0
        d = ("derecha", "izquierda")[(n + vuelta) % 2]
    if d not in DIRECCIONES:
        salir(f"transicion_dir desconocida: {d} (hay: {', '.join(DIRECCIONES)}, alterna)")
    return tipo, DIRECCIONES[d]


def para_la_que_se_va(siguiente: tuple[str, list[int]] | None, cuadros: int) -> dict:
    """Lo que la capa que se va necesita para la transición de la que llega en `cuadros`: que la empujen o que se
    apague al final."""
    if not siguiente or cuadros <= 0:
        return {}
    tipo, hacia = siguiente
    if tipo in EMPUJAN:
        return {"empujada": {"cuadros": int(cuadros), "dir": hacia}}
    if tipo in APAGAN:
        return {"salida": max(1, int(round(cuadros * APAGAN[tipo])))}
    return {}
