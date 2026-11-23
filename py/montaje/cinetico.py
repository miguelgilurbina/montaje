"""El cinetismo: técnicas del arte cinético venezolano llevadas al video, sin copiar obras (un aparato de imagen de la
mesa analógica).

Miguel, el 2026-11-23: «Tu busca más por favor»; de lo que se encontró buscando eligió abrir «El cinetismo». El arte
cinético hace que el ojo ponga el movimiento y el color: líneas finas delante de un objeto lo hacen vibrar; dos tramas
superpuestas hacen ondas que no están en ninguna (el moiré); franjas de color muy finas hacen ver colores que no se
pintaron. Aquí son técnicas, no citas: ninguna obra se reproduce.

`cinetico` (perilla `tecnica`):

- **vibracion**: la imagen hecha de líneas verticales fijas, más gruesas donde es oscuro. Las líneas no se mueven; la
  imagen sí, y lo que se mueve vibra en la trama.
- **moire**: esa misma trama, y encima otra de líneas parejas un poco girada que se mueve despacio (`deriva`): las
  ondas del moiré cruzan la imagen.
- **induccion**: franjas finas, negras y claras según el brillo, y cada tanto una franja de color de la paleta según
  el color de la imagen en ese lugar; las franjas de color corren despacio.

`paso` es el ancho de un par de líneas en pixeles a 1080 de alto. Las tintas son las del arte de Curiana. Todo [sin
verificar]: puntos de partida mirados en las hojas.
"""

from __future__ import annotations

import math

import numpy as np

from . import analogo as A
from .pelicula import _desenfocar

TECNICAS = ("vibracion", "moire", "induccion")
POR_DEFECTO = {
    "cinetico": {"tecnica": "vibracion", "paso": 8.0, "angulo": 4.0, "deriva": 0.5, "tintas": None},
}
RANGOS = {
    "cinetico": {"tecnica": TECNICAS, "paso": (3, 40), "angulo": (0, 30), "deriva": (0, 3)},
}
#: El fondo y la línea por defecto (hueso y noche), y los colores de la inducción (eléctrico, ocre, rojo, oro, ácido).
FONDO, LINEA = "#f3ead4", "#07090d"
COLORES = ["#2154c5", "#c36712", "#b64924", "#e6b43c", "#c7c91c"]
LUMA = np.array([0.299, 0.587, 0.114], np.float32)


def _rgb(hexa: str) -> np.ndarray:
    return np.array([int(hexa[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)


def errores(nombre: str, a: dict) -> list[str]:
    t = a.get("tintas")
    if t is not None and (not isinstance(t, list) or len(t) != 2 or not all(isinstance(h, str) and len(h) == 7 and h[0] == "#" for h in t)):
        return ["cinetico.tintas: dos colores #rrggbb (el fondo y la línea), o nada"]
    return []


def calentar(pasos: list[tuple[str, dict]], fps: float, solo: int | None = None) -> int:
    return 0   # las tramas son fijas o salen del segundo: no recuerda nada


_GRILLAS: dict = {}


def _coordenada(h: int, w: int, angulo: float) -> np.ndarray:
    """La posición de cada pixel a lo ancho de una trama girada `angulo` grados (en pixeles)."""
    clave = (h, w, round(angulo, 3))
    if clave not in _GRILLAS:
        if len(_GRILLAS) > 8:
            _GRILLAS.clear()
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        a = math.radians(angulo)
        _GRILLAS[clave] = xx * math.cos(a) + yy * math.sin(a)
    return _GRILLAS[clave]


def _lineas(u: np.ndarray, periodo: float, ancho: np.ndarray | float, fase: float = 0.0) -> np.ndarray:
    """Cuánto cubre la línea en cada pixel (0 a 1, con el borde suavizado): líneas de `ancho` (fracción del periodo)."""
    f = ((u + fase) / periodo) % 1.0
    d = np.abs(f - 0.5) * periodo                       # distancia al centro de la línea, en pixeles
    return np.clip(np.asarray(ancho) * periodo / 2 - d + 0.5, 0, 1).astype(np.float32)


def _oscuridad(img: np.ndarray, h: int) -> np.ndarray:
    lum = _desenfocar((img @ LUMA)[..., None], max(0.8, h / 540))[..., 0]
    a, b = np.percentile(lum[::4, ::4], (2, 98))
    lum = np.clip((lum - a) / max(b - a, 0.05), 0, 1)
    return np.clip(0.08 + 0.84 * (1 - lum), 0, 1)       # nunca del todo: la trama siempre se ve


def cinetico(img: np.ndarray, p: dict, ctx) -> np.ndarray:
    h, w = img.shape[:2]
    periodo = max(3.0, p["paso"] * h / 1080)
    fondo, linea = (_rgb(c) for c in (p["tintas"] or [FONDO, LINEA]))
    oscuro = _oscuridad(img, h)
    u = _coordenada(h, w, 0.0)
    if p["tecnica"] == "induccion":
        # Tres franjas por grupo: dos negras y claras según el brillo, una de color según el color de la imagen.
        grupo = 3 * periodo
        negra = _lineas(u, periodo, oscuro)
        colores = np.stack([_rgb(c) for c in COLORES] + [fondo])
        chica = img[:: max(1, h // 60), :: max(1, w // 90)]
        # El color de la franja sale del tono de la imagen, no de su brillo; donde casi no hay color, el fondo.
        def tono(x):
            return x / (x.sum(-1, keepdims=True) + 1e-4)
        cercano = np.argmin(((tono(chica)[..., None, :] - tono(colores[:-1])[None, None]) ** 2).sum(-1), axis=-1)
        cercano = np.where(np.ptp(chica, axis=-1) < 0.08, len(COLORES), cercano)
        from PIL import Image

        idx = np.asarray(Image.fromarray(cercano.astype(np.uint8)).resize((w, h), Image.NEAREST))
        corre = p["deriva"] * ctx.t * periodo * 0.5     # las franjas de color corren despacio
        es_color = ((u + corre) / grupo) % 1.0 >= 2 / 3
        sale = fondo * (1 - negra[..., None]) + linea * negra[..., None]
        franja = colores[idx] * (1 - oscuro[..., None]) + linea * oscuro[..., None]   # en lo oscuro, la franja también
        sale = np.where(es_color[..., None], franja, sale)
        return np.clip(sale, 0, 1).astype(np.float32)
    cubre = _lineas(u, periodo, oscuro)                  # la trama de la imagen: líneas fijas, gruesas en lo oscuro
    sale = fondo * (1 - cubre[..., None]) + linea * cubre[..., None]
    if p["tecnica"] == "moire":
        # Una segunda trama pareja, girada unos grados, que gira y corre despacio: las ondas del moiré.
        giro = p["angulo"] + 1.5 * p["deriva"] * math.sin(2 * math.pi * ctx.t / 11.0)
        v = _coordenada(h, w, giro)
        otra = _lineas(v, periodo * 1.04, 0.5, fase=p["deriva"] * ctx.t * periodo * 0.3)
        sale = sale * (1 - 0.85 * otra[..., None]) + linea * 0.85 * otra[..., None]
    return np.clip(sale, 0, 1).astype(np.float32)


APARATOS = {"cinetico": cinetico}
