"""La imprenta: la imagen impresa, en serigrafía, risografía, el tramado del diario o la fotocopia (un aparato de imagen
de la mesa analógica).

Miguel, el 2026-11-22, en el mapa de la galería: eligió «Imprenta» (G7 en PROPUESTAS.md: «la voz serigráfica de las
tintas del arte»). Las tintas por defecto son las del arte de Curiana (`direccion/PALETA.md`) sobre el hueso.

- **Serigrafía**: la imagen en tres tintas planas y opacas, una encima de otra (la clara primero), cada una con su
  registro un poco corrido y la tinta que no cubre pareja.
- **Risografía**: dos tintas transparentes que se pisan (lo que se superpone se oscurece), cada una hecha de un grano
  al azar como el del tambor de la riso, y el registro que baila más.
- **Trama**: el diario: cian, magenta, amarillo y negro en puntos, cada color con la trama girada en su ángulo
  (15°, 75°, 0°, 45°), sobre el papel gris del diario.
- **Fotocopia**: blanco y negro quemado, el tóner que mancha lo negro y salpica lo blanco, las rayas del tambor y la
  sombra de la tapa abierta; con `copias`, la copia de la copia.

Cada impresión es un cuadro: con `cuadros` por segundo (8, como una animación impresa) el registro y la tinta cambian
a saltos; con 0, en cada cuadro del video. Las tramas y los ángulos son los de la imprenta de offset; lo demás
[sin verificar]: puntos de partida mirados en las hojas. Con `sonido: maquina`, la máquina andando (`ruidos.py`).
"""

from __future__ import annotations

import math

import numpy as np

from . import analogo as A
from .pelicula import _desenfocar, _grano

TECNICAS = ("serigrafia", "riso", "trama", "fotocopia")

POR_DEFECTO = {
    "imprenta": {"tecnica": "serigrafia", "tintas": None, "registro": 0.6, "cuadros": 8, "trama": 110, "papel": 0.6,
                 "grano": 0.6, "copias": 1, "sonido": "ninguno"},
}
RANGOS = {
    "imprenta": {"tecnica": TECNICAS, "registro": (0, 3), "cuadros": (0, 30), "trama": (30, 240), "papel": (0, 1),
                 "grano": (0, 2), "copias": (1, 6), "sonido": ("ninguno", "maquina")},
}

#: Las tintas de cada técnica si no se dan: de la más clara a la más oscura (la serigrafía) o las dos de la riso.
TINTAS = {
    "serigrafia": ["#e6b43c", "#b64924", "#26396a"],     # oro, rojo, índigo
    "riso": ["#2154c5", "#b64924"],                      # eléctrico, rojo
}
HUESO = "#f3ead4"
#: Las tintas del offset y el papel del diario.
CMYK = {"c": (0.0, 0.62, 0.89), "m": (0.89, 0.05, 0.48), "y": (1.0, 0.92, 0.05), "k": (0.12, 0.11, 0.11)}
ANGULOS = {"c": 15, "m": 75, "y": 0, "k": 45}
PAPEL_DIARIO = (0.90, 0.89, 0.83)
TONER = (0.07, 0.07, 0.08)
PAPEL_COPIA = (0.96, 0.96, 0.94)
LUMA = np.array([0.299, 0.587, 0.114], np.float32)


def _rgb(hexa: str) -> np.ndarray:
    return np.array([int(hexa[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)


def errores(nombre: str, a: dict) -> list[str]:
    t = a.get("tintas")
    if t is not None and (not isinstance(t, list) or not 1 <= len(t) <= 4
                          or not all(isinstance(h, str) and len(h) == 7 and h[0] == "#" for h in t)):
        return ["imprenta.tintas: de una a cuatro tintas #rrggbb (o nada: las de la técnica)"]
    return []


CONSEJO = {"imprenta": "sube los `cuadros` de la imprenta"}


def calentar(pasos: list[tuple[str, dict]], fps: float, solo: int | None = None) -> int:
    """Una impresión dura varios cuadros del video y sale del primero: el pedazo tiene que haberlo visto."""
    n = 0
    for i, (nombre, p) in enumerate(pasos):
        if nombre == "imprenta" and (solo is None or i == solo) and 0 < p["cuadros"] < fps:
            n = max(n, int(math.ceil(fps / p["cuadros"])) + 1)
    return n


# ── Piezas ─────────────────────────────────────────────────────────────────

_CACHE: dict = {}


def _fibra(h: int, w: int) -> np.ndarray:
    from scipy import ndimage

    clave = ("fibra", h, w)
    if clave not in _CACHE:
        n = np.random.default_rng(7).standard_normal((h, w)).astype(np.float32)
        n = ndimage.gaussian_filter(n, (max(0.6, h / 900), max(1.5, w / 200)))
        _CACHE[clave] = n / (n.std() + 1e-6)
    return _CACHE[clave]


def _papel(color, h: int, w: int, fuerza: float) -> np.ndarray:
    return np.asarray(color, np.float32) * (1 + 0.02 * fuerza * _fibra(h, w))[..., None]


def _correr(m: np.ndarray, dx: float, dy: float) -> np.ndarray:
    """Una capa corrida (dx, dy) pixeles enteros, rellenando con lo que no tiene tinta (0)."""
    dx, dy = int(round(dx)), int(round(dy))
    sale = np.zeros_like(m)
    h, w = m.shape[:2]
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    sale[yd, xd] = m[ys, xs]
    return sale


def _registros(semilla: int, impresion: int, n: int, registro: float, h: int) -> list[tuple[float, float]]:
    """Dónde cae cada tinta: un corrimiento fijo por tinta (la máquina) más uno que cambia en cada impresión."""
    fijo = np.random.default_rng([semilla, A._num("registro-fijo")])
    salto = np.random.default_rng([semilla, A._num("registro"), impresion])
    escala = registro * h / 540
    return [(escala * (2.2 * fijo.standard_normal() + 1.0 * salto.standard_normal()),
             escala * (2.2 * fijo.standard_normal() + 1.0 * salto.standard_normal())) for _ in range(n)]


def _uniforme(rng: np.random.Generator, h: int, w: int, tam: float) -> np.ndarray:
    """Ruido parejo entre 0 y 1 con grumos de `tam` pixeles (el umbral del grano de la riso)."""
    from scipy.special import ndtr

    return ndtr(_grano(rng, h, w, tam)).astype(np.float32)


def _normalizada(img: np.ndarray) -> np.ndarray:
    """La luminancia estirada entre lo más oscuro y lo más claro del cuadro (un 2 % de cada lado), mitad y mitad con
    la de verdad: que una imagen oscura no quede toda de la tinta oscura, sin que cada cuadro cambie entero."""
    lum = img @ LUMA
    a, b = np.percentile(lum[::4, ::4], (2, 98))
    estirada = np.clip((lum - a) / max(b - a, 0.05), 0, 1)
    return 0.5 * estirada + 0.5 * lum


# ── Las técnicas ───────────────────────────────────────────────────────────

def _serigrafia(img: np.ndarray, p: dict, semilla: int, impresion: int, rng) -> np.ndarray:
    h, w = img.shape[:2]
    tintas = [_rgb(x) for x in (p["tintas"] or TINTAS["serigrafia"])]
    lum = _desenfocar(_normalizada(img)[..., None], max(0.8, h / 500))[..., 0]
    lum = lum + 0.02 * _grano(rng, h, w, 1.5)                       # el borde de la tinta, que no es una línea limpia
    sale = _papel(_rgb(HUESO), h, w, p["papel"])
    umbrales = np.linspace(0.78, 0.3, len(tintas))                  # la clara cubre más; la oscura, sólo lo oscuro
    for (dx, dy), tinta, u in zip(_registros(semilla, impresion, len(tintas), p["registro"], h), tintas, umbrales):
        capa = np.clip((u - lum) * max(h / 90, 6.0), 0, 1)
        capa = _correr(capa, dx, dy)
        pareja = 1 + 0.06 * p["grano"] * _grano(rng, h, w, h / 40)  # la tinta que no cubre pareja
        sale = sale * (1 - capa[..., None]) + (tinta * pareja[..., None]) * capa[..., None]
    return sale


def _riso(img: np.ndarray, p: dict, semilla: int, impresion: int, rng) -> np.ndarray:
    h, w = img.shape[:2]
    tintas = [_rgb(x) for x in (p["tintas"] or TINTAS["riso"])]
    lum = _desenfocar(_normalizada(img)[..., None], max(0.8, h / 400))[..., 0]
    oscuro = 1 - lum
    # La separación: la primera tinta lleva lo frío y lo oscuro; la segunda, lo cálido y los medios. Lo claro queda
    # papel: la riso no imprime un velo de puntos donde no hay tinta.
    calido = _desenfocar(np.clip((img[..., 0] - img[..., 2]) * 1.5 + 0.5, 0, 1)[..., None], max(1.0, h / 200))[..., 0]
    densidades = [np.clip((oscuro - 0.15) / 0.85, 0, 1) ** 1.25 * (1.1 - 0.55 * calido),
                  np.clip((oscuro - 0.3) / 0.7, 0, 1) ** 1.1 * np.clip(calido * 1.4 - 0.2, 0, 1)]
    if len(tintas) > 2:
        densidades += [np.clip(oscuro ** 2, 0, 1)] * (len(tintas) - 2)
    sale = _papel(_rgb(HUESO), h, w, p["papel"])
    celda = h / (0.55 * p["trama"])                                  # la trama de la riso, más gruesa que la del diario
    regs = _registros(semilla, impresion, len(tintas), p["registro"] * 1.8, h)
    for n, ((dx, dy), tinta, d) in enumerate(zip(regs, tintas, densidades)):
        cubre = _puntos(d, celda, (22.5, 67.5, 45.0, 0.0)[n % 4])
        # La tinta no carga pareja: un grano fijo del máster (lo que baila es el registro, no la textura).
        clave = ("riso", h, w, semilla, n)
        if clave not in _CACHE:
            _CACHE[clave] = 0.82 + 0.18 * _uniforme(np.random.default_rng([semilla, A._num("riso-grano"), n]), h, w,
                                                    max(1.2, h / 400))
        cubre = _correr(cubre * _CACHE[clave] ** p["grano"], dx, dy)
        sale = sale * (1 - cubre[..., None] * (1 - tinta))             # transparentes: lo que se pisa se oscurece
    return sale


_GRILLAS: dict = {}


def _puntos(canal: np.ndarray, celda: float, angulo: float, irregular: float = 0.0) -> np.ndarray:
    """Cuánto cubre la tinta en cada pixel: una trama de puntos redondos girada en `angulo`, cada punto del tamaño del
    tono en el centro de su celda (el área del punto es el tono)."""
    h, w = canal.shape
    clave = (h, w, round(celda, 3), angulo)
    if clave not in _GRILLAS:
        if len(_GRILLAS) > 12:
            _GRILLAS.clear()
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        a = math.radians(angulo)
        u = (xx * math.cos(a) + yy * math.sin(a)) / celda
        v = (-xx * math.sin(a) + yy * math.cos(a)) / celda
        iu, iv = np.floor(u) + 0.5, np.floor(v) + 0.5
        cx = np.clip(((iu * math.cos(a) - iv * math.sin(a)) * celda).astype(np.int32), 0, w - 1)
        cy = np.clip(((iu * math.sin(a) + iv * math.cos(a)) * celda).astype(np.int32), 0, h - 1)
        _GRILLAS[clave] = (cy, cx, np.hypot(u - iu, v - iv).astype(np.float32))
    cy, cx, d = _GRILLAS[clave]
    radio = np.sqrt(np.clip(canal[cy, cx], 0, 1) / math.pi) * (1 + irregular)
    return np.clip((radio - d) * celda + 0.5, 0, 1)


def _trama(img: np.ndarray, p: dict, rng) -> np.ndarray:
    h, w = img.shape[:2]
    celda = h / p["trama"]
    c, m, y = (1 - img[..., 0]), (1 - img[..., 1]), (1 - img[..., 2])
    k = np.minimum(np.minimum(c, m), y) * 0.85                      # el negro saca lo gris de los tres colores
    canales = {"c": (c - k) / (1 - k + 1e-6), "m": (m - k) / (1 - k + 1e-6), "y": (y - k) / (1 - k + 1e-6), "k": k}
    sale = _papel(PAPEL_DIARIO, h, w, p["papel"])
    for nombre in ("y", "c", "m", "k"):
        cubre = _puntos(canales[nombre], celda, ANGULOS[nombre], 0.05 * p["grano"] * float(rng.standard_normal()))
        sale = sale * (1 - cubre[..., None] * (1 - np.asarray(CMYK[nombre], np.float32)))
    return sale


def _fotocopia(img: np.ndarray, p: dict, semilla: int, impresion: int, rng) -> np.ndarray:
    h, w = img.shape[:2]
    lum = _normalizada(img)
    for _ in range(int(p["copias"])):   # cada copia: más contraste y menos detalle
        lum = _desenfocar(lum[..., None], max(0.7, h / 700))[..., 0]
        lum = 1 / (1 + np.exp(-7 * (lum - 0.5)))
    negro = 1 - lum
    negro = negro * (1 + 0.07 * p["grano"] * _grano(rng, h, w, max(2.0, h / 150)))       # el tóner no cubre parejo
    salpica = (rng.random((h, w)) < 0.00025 * p["copias"] * p["grano"]).astype(np.float32)  # y salpica lo blanco
    negro = np.clip(np.maximum(negro, salpica), 0, 1)
    r = np.random.default_rng([semilla, A._num("tambor")])
    for x in r.integers(0, w, 3):   # las rayas del tambor, siempre en el mismo lugar
        negro[:, x:x + max(1, w // 900)] = np.maximum(negro[:, x:x + max(1, w // 900)], 0.25 + 0.2 * r.random())
    tapa = np.clip((np.arange(w, dtype=np.float32) - 0.955 * w) / (0.045 * w), 0, 1) ** 1.5   # la tapa abierta
    negro = np.maximum(negro, tapa[None, :] * 0.9)
    papel = _papel(PAPEL_COPIA, h, w, p["papel"])
    return papel * (1 - negro[..., None]) + np.asarray(TONER, np.float32) * negro[..., None]


def imprenta(img: np.ndarray, p: dict, ctx) -> np.ndarray:
    """El aparato: la imagen (RGB 0–1) impresa. Cada impresión dura 1/`cuadros` segundos: se repite tal cual."""
    impresion = int(math.floor(ctx.t * p["cuadros"] + 1e-6)) if p["cuadros"] else ctx.k
    clave = ("imprenta", ctx.paso)
    guardado = ctx.estado.get(clave)
    if guardado is not None and guardado[0] == impresion and p["cuadros"]:
        return guardado[1].copy()
    semilla = ctx.semilla * 100 + ctx.paso
    rng = np.random.default_rng([semilla, A._num("imprenta"), impresion])
    t = p["tecnica"]
    if t == "serigrafia":
        sale = _serigrafia(img, p, semilla, impresion, rng)
    elif t == "riso":
        sale = _riso(img, p, semilla, impresion, rng)
    elif t == "trama":
        sale = _trama(img, p, rng)
    else:
        sale = _fotocopia(img, p, semilla, impresion, rng)
    sale = np.clip(sale, 0, 1).astype(np.float32)
    ctx.estado[clave] = (impresion, sale)
    return sale.copy()


APARATOS = {"imprenta": imprenta}
