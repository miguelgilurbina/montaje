"""El proyector en la pared: la película (o lo que sea) proyectada en la casa y vista así (un aparato de imagen de la
mesa analógica).

Miguel, el 2026-11-21: «Seguir acumulando». Las películas de la familia se veían proyectadas en una pared o en una
sábana colgada, con la luz apagada. El aparato `proyector` pone la imagen en la pared:

- **La mancha de luz**: la ampolleta y el condensador dejan el centro más claro que los bordes, y la luz es cálida
  (tungsteno).
- **El trapecio** (`trapecio`): el proyector sobre una mesa, inclinado hacia arriba, abre la imagen arriba.
- **La pared** (`pared`): el revoque con su textura, la **sábana** con sus pliegues (que sombrean y tuercen la
  imagen), o una pantalla lisa.
- **El foco** (`foco`): nunca perfecto en la casa.
- **El parpadeo**: el obturador del proyector (tres aspas a 18 cuadros: 54 destellos por segundo) contra los 60
  campos de la cámara que filma la pared, o el ojo: un latido de unos 6 por segundo [sin verificar: depende del
  proyector y de la cámara].
- **El cuarto**: oscuro, con lo que rebota de la propia imagen alrededor.

Va después de `pelicula` (con `marco: ninguno`): `[pelicula, proyector]`.
"""

from __future__ import annotations

import math

import numpy as np

from . import analogo as A

PAREDES = ("pared", "sabana", "pantalla")

POR_DEFECTO = {
    "proyector": {"tamano": 0.84, "trapecio": 0.06, "pared": "pared", "foco": 0.6, "mancha": 0.5, "parpadeo": 0.4,
                  "calidez": 0.5, "cuarto": 0.5},
}
RANGOS = {
    "proyector": {"tamano": (0.4, 1.0), "trapecio": (0, 0.3), "pared": PAREDES, "foco": (0, 3), "mancha": (0, 1),
                  "parpadeo": (0, 2), "calidez": (0, 1), "cuarto": (0, 1)},
}


def errores(nombre: str, a: dict) -> list[str]:
    return []


def calentar(pasos: list[tuple[str, dict]], fps: float, solo: int | None = None) -> int:
    return 0   # no recuerda nada: el latido sale del segundo y la geometría no cambia


_GEOMETRIAS: dict = {}


def _geometria(p: dict, alto: int, ancho: int, semilla: int) -> dict:
    """Lo que no cambia: dónde cae cada pixel de la pared en la imagen proyectada (el trapecio y, en la sábana, lo
    que tuercen los pliegues), la mancha de luz, la textura de la pared y la sombra de los pliegues."""
    from scipy import ndimage

    clave = (alto, ancho, p["tamano"], p["trapecio"], p["pared"], p["mancha"], semilla)
    if clave in _GEOMETRIAS:
        return _GEOMETRIAS[clave]
    rng = np.random.default_rng([semilla, A._num("pared")])
    y, x = np.mgrid[0:alto, 0:ancho].astype(np.float32)
    # El cuadro proyectado: con la proporción de la imagen, `tamano` de la pared, un poco arriba del centro.
    h = alto * p["tamano"]
    w_abajo = h * ancho / alto * (1 - p["trapecio"] / 2)
    w_arriba = w_abajo * (1 + p["trapecio"])
    top = (alto - h) / 2 - 0.03 * alto
    v = (y - top) / h
    ancho_v = w_arriba * (1 - v) + w_abajo * v
    u = (x - ancho / 2) / ancho_v + 0.5
    sombra = np.ones((alto, ancho), np.float32)
    if p["pared"] == "sabana":  # los pliegues: ondas largas, casi verticales, que tuercen la imagen y la sombrean
        pliegue = np.zeros((alto, ancho), np.float32)
        for _ in range(5):
            f = rng.uniform(1.5, 4.5) / ancho
            fase = rng.uniform(0, 2 * math.pi)
            inclin = rng.uniform(-0.25, 0.25)
            pliegue += rng.uniform(0.4, 1.0) * np.sin(2 * math.pi * f * (x + inclin * y) + fase)
        pliegue /= 5
        u = u + 0.022 * pliegue
        v = v + 0.006 * np.roll(pliegue, 7, axis=1)
        pendiente = np.gradient(pliegue, axis=1)
        pendiente = pendiente / (np.abs(pendiente).max() + 1e-9)
        sombra = np.clip(1 + 0.4 * pendiente, 0.55, 1.3).astype(np.float32)
    dentro = (u >= 0) & (u <= 1) & (v >= 0) & (v <= 1)
    # Borde un poco blando (el foco y la ventanilla del proyector).
    borde = np.minimum(np.minimum(u, 1 - u) * ancho_v, np.minimum(v, 1 - v) * h)
    luz = np.clip(borde / (0.004 * alto + 1), 0, 1) * dentro
    r2 = ((u - 0.5) * 2) ** 2 + ((v - 0.5) * 2) ** 2
    luz = luz * (1 - p["mancha"] * 0.5 * np.clip(r2, 0, 2) ** 0.9)   # la mancha de luz del condensador
    if p["pared"] == "pantalla":
        textura = np.ones((alto, ancho), np.float32)
    else:
        grueso = ndimage.zoom(rng.standard_normal((max(2, alto // 40), max(2, ancho // 40))).astype(np.float32),
                              (alto / max(2, alto // 40), ancho / max(2, ancho // 40)), order=1)[:alto, :ancho]
        fino = rng.standard_normal((alto, ancho)).astype(np.float32)
        textura = 1 + 0.035 * grueso + 0.025 * ndimage.gaussian_filter(fino, 0.8) / 0.2
        if p["pared"] == "sabana":
            textura = 1 + 0.02 * grueso + 0.03 * np.sin(y * 2.2)   # la trama de la tela
    sy = np.clip(v * (alto - 1), 0, alto - 1)
    sx = np.clip(u * (ancho - 1), 0, ancho - 1)
    y0, x0 = np.floor(sy).astype(np.int32), np.floor(sx).astype(np.int32)
    y1, x1 = np.minimum(y0 + 1, alto - 1), np.minimum(x0 + 1, ancho - 1)
    # Lo que rebota de la imagen ilumina la pared cerca de ella; lejos, el cuarto queda a oscuras.
    chico = dentro[::8, ::8].astype(np.float32)
    rebote = ndimage.zoom(ndimage.gaussian_filter(chico, alto / 8 * 0.12), (alto / chico.shape[0], ancho / chico.shape[1]),
                          order=1)[:alto, :ancho]
    rebote = np.pad(rebote, ((0, alto - rebote.shape[0]), (0, ancho - rebote.shape[1])), mode="edge")
    rebote = rebote / (rebote.max() + 1e-9) * (1 - dentro)
    geo = {"idx": (y0, x0, y1, x1), "f": ((sy - y0)[..., None].astype(np.float32), (sx - x0)[..., None].astype(np.float32)),
           "luz": (luz * sombra).astype(np.float32)[..., None], "textura": textura.astype(np.float32)[..., None],
           "rebote": rebote.astype(np.float32)[..., None]}
    _GEOMETRIAS.clear()
    _GEOMETRIAS[clave] = geo
    return geo


def proyector(img: np.ndarray, p: dict, ctx) -> np.ndarray:
    from scipy import ndimage

    alto, ancho = img.shape[:2]
    semilla = ctx.semilla * 100 + ctx.paso
    geo = _geometria(p, alto, ancho, semilla)
    fuente = img
    if p["foco"]:
        fuente = ndimage.gaussian_filter(img, (p["foco"] * alto / 1080 * 1.6,) * 2 + (0,), mode="nearest", truncate=2.5)
    lin = np.power(np.clip(fuente, 0, 1), 2.2, dtype=np.float32)
    y0, x0, y1, x1 = geo["idx"]
    fy, fx = geo["f"]
    proyectada = ((lin[y0, x0] * (1 - fx) + lin[y0, x1] * fx) * (1 - fy) + (lin[y1, x0] * (1 - fx) + lin[y1, x1] * fx) * fy)
    lampara = 1 - p["calidez"] * np.array([0.0, 0.08, 0.22], np.float32)   # la ampolleta: tungsteno
    latido = 1 + 0.05 * p["parpadeo"] * math.sin(2 * math.pi * 6.0 * ctx.t + 0.7) \
        + 0.02 * p["parpadeo"] * float(np.random.default_rng([semilla, A._num("lampara"), ctx.k]).standard_normal())
    luz = proyectada * geo["luz"] * lampara * latido
    # El cuarto: casi negro, con la luz que rebota de la imagen en la pared cercana (y el color de lo que se proyecta).
    media = luz.reshape(-1, 3).mean(axis=0)
    cuarto = p["cuarto"] * (0.0008 + 0.06 * media * geo["rebote"])
    pared = (luz + cuarto) * geo["textura"]
    return np.power(np.clip(pared, 0, 1), 1 / 2.2, dtype=np.float32)


APARATOS = {"proyector": proyector}
