"""El color del cine mudo: cómo se le daba color a la película antes del color (un aparato de imagen de la mesa
analógica).

Miguel, el 2026-11-23: «Tu busca más por favor»; de lo que se encontró buscando eligió abrir «El color del cine mudo».

`tinte` (perilla `modo`):

- **tintado**: la copia en blanco y negro teñida entera de un color, escena por escena: lo claro toma el color y lo
  negro queda negro. Con `tinta: auto` el color sale de la escena: el azul para lo oscuro (la noche se filmaba de día
  y se teñía de azul), el ámbar para lo cálido (la luz de lámpara), el rojo para lo que arde, el verde para el campo.
  Las convenciones no eran fijas; éstas son las más citadas.
- **virado**: lo contrario: lo oscuro toma el color (sepia, azul, verde) y lo claro queda limpio.
- **dos-colores**: la copia de dos colores de los años 20: lo que la cámara vio por el filtro rojo y por el verde,
  copiado en un tinte rojo anaranjado y uno verde azulado. Sin azules ni violetas de verdad.
- **kinemacolor**: el color aditivo de dos colores que se proyectaba alternando rojo y verde: lo que se mueve rápido
  deja una franja roja de un lado y verde del otro, porque los dos colores no son del mismo instante.

Va después de `pelicula` (con su emulsión en blanco y negro para el tintado y el virado). Los colores son [sin
verificar]: tomados de las descripciones de época y mirados en las hojas.
"""

from __future__ import annotations

import numpy as np

from . import analogo as A

MODOS = ("tintado", "virado", "dos-colores", "kinemacolor")
#: Los tintes del tintado (el color que toma lo claro) y del virado (el que toma lo oscuro).
TINTES = {"azul": (0.40, 0.60, 1.00), "ambar": (1.00, 0.76, 0.42), "rojo": (1.00, 0.42, 0.32), "verde": (0.62, 1.00, 0.60),
          "sepia": (1.00, 0.86, 0.66), "rosa": (1.00, 0.70, 0.80)}
VIRADOS = {"sepia": (0.36, 0.20, 0.09), "azul": (0.08, 0.20, 0.42), "verde": (0.10, 0.30, 0.16), "rojo": (0.42, 0.10, 0.08)}
POR_DEFECTO = {"tinte": {"modo": "tintado", "tinta": "auto", "fuerza": 0.9}}
RANGOS = {"tinte": {"modo": MODOS, "tinta": ("auto", *TINTES), "fuerza": (0, 1)}}
LUMA = np.array([0.299, 0.587, 0.114], np.float32)
#: Cuánto pesa el cuadro nuevo en lo que el tintado automático recuerda de la escena (para que no titile).
MEMORIA = 0.25


def errores(nombre: str, a: dict) -> list[str]:
    if a.get("modo") == "virado" and a.get("tinta", "auto") not in ("auto", *VIRADOS):
        return [f"tinte: el virado es {' / '.join(VIRADOS)} (o auto, sepia)"]
    return []


def calentar(pasos: list[tuple[str, dict]], fps: float, solo: int | None = None) -> int:
    """El tintado automático recuerda la escena unos cuadros; el kinemacolor, el cuadro anterior."""
    n = 0
    for i, (nombre, p) in enumerate(pasos):
        if nombre == "tinte" and (solo is None or i == solo):
            n = max(n, 16 if p["modo"] == "tintado" and p["tinta"] == "auto" else 2 if p["modo"] == "kinemacolor" else 0)
    return n


def _sigmoide(x):
    return 1 / (1 + np.exp(-x))


def tinta_de_la_escena(img: np.ndarray, recuerdo: np.ndarray | None) -> tuple[np.ndarray, np.ndarray]:
    """El color del tintado según la escena (y lo que se recuerda de las anteriores): los pesos de azul, ámbar, rojo,
    verde y sepia, sin saltos."""
    chica = img[::8, ::8].reshape(-1, 3)
    lum = float((chica @ LUMA).mean())
    r, g, b = chica.mean(0)
    medidas = np.array([lum, r - b, r - g, g - (r + b) / 2], np.float32)
    medidas = medidas if recuerdo is None else recuerdo * (1 - MEMORIA) + medidas * MEMORIA
    lum, calido, rojo, verde = medidas
    pesos = np.array([_sigmoide((0.28 - lum) / 0.04),                 # azul: lo oscuro, la noche
                      _sigmoide((calido - 0.05) / 0.03),              # ámbar: la luz cálida
                      _sigmoide((rojo - 0.18) / 0.03) * 1.5,          # rojo: lo que arde
                      _sigmoide((verde - 0.04) / 0.02),               # verde: el campo
                      0.35])                                          # sepia: lo demás
    color = (pesos[:, None] * np.array([TINTES[k] for k in ("azul", "ambar", "rojo", "verde", "sepia")])).sum(0) / pesos.sum()
    return color.astype(np.float32), medidas


def tinte(img: np.ndarray, p: dict, ctx) -> np.ndarray:
    modo, f = p["modo"], p["fuerza"]
    lum = img @ LUMA
    if modo == "tintado":
        if p["tinta"] == "auto":
            clave = ("tinte", ctx.paso)
            escena = getattr(ctx, "original", None)
            escena = escena if escena is not None and escena.shape == img.shape else img
            color, ctx.estado[clave] = tinta_de_la_escena(escena, ctx.estado.get(clave))
        else:
            color = np.array(TINTES[p["tinta"]], np.float32)
        sale = lum[..., None] * (color * f + (1 - f))
    elif modo == "virado":
        oscuro = np.array(VIRADOS.get(p["tinta"], VIRADOS["sepia"]), np.float32)
        sale = 1 - (1 - lum[..., None]) * (1 - oscuro) * f - (1 - lum[..., None]) * (1 - f)
    elif modo == "dos-colores":
        # Dos capas de tinte sobre luz blanca: la verde azulada absorbe el rojo según lo que vio el filtro rojo; la
        # roja anaranjada absorbe el verde y casi todo el azul según lo que vio el filtro verde.
        a, b = 1 - img[..., 0], 1 - img[..., 1]
        sale = np.stack([1 - a, (1 - b) * (1 - 0.08 * a), (1 - 0.3 * a) * (1 - 0.85 * b)], -1)
        sale = lum[..., None] * (1 - f) + sale * f
    else:  # kinemacolor: el rojo es de este cuadro y el verde del anterior
        clave = ("tinte-kinema", ctx.paso)
        antes = ctx.estado.get(clave)
        ctx.estado[clave] = img.copy()
        verde = (antes if antes is not None and antes.shape == img.shape else img)[..., 1]
        rojo = img[..., 0]
        sale = np.stack([rojo, verde, 0.45 * verde + 0.15 * rojo], -1)
        sale = sale * (1 + 0.05 * (1 if ctx.k % 2 else -1) * np.array([1, -1, -0.5], np.float32))   # el filtro que alterna
        sale = lum[..., None] * (1 - f) + sale * f
    return np.clip(sale, 0, 1).astype(np.float32)


APARATOS = {"tinte": tinte}
