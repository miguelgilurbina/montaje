"""La película: Super 8, 8 mm y 16 mm, simulados en la emulsión (un aparato de la mesa analógica).

Miguel, el 2026-11-21: «acumulemos más efectos antes de evaluar lo que ya hiciste». La galería ya tenía la película
como capa pintada encima (`recuerdo`, `rayas`, `pelicula`); esto baja un piso, como la mesa con el video: la
imagen se vuelve la luz que llegó a la emulsión, y lo que se ve sale de lo que la película le hace a esa luz.

## Lo que pasa en cada cuadro

1. **La luz.** La imagen vuelve a luz lineal. El filtro 85 mal puesto la tiñe (la película «tungsteno» de los
   Super 8 se usaba de día con el filtro naranja de la cámara; de noche, con la ampolleta, había que sacarlo: si
   no, todo naranja). El parpadeo es la exposición que no es igual de un cuadro a otro.
2. **El quemado.** Al arrancar la cámara los primeros cuadros salen sobreexpuestos, y el principio y el final del
   rollo vienen velados: una mancha naranja que entra por un borde.
3. **El halo.** La luz más fuerte atraviesa la emulsión, rebota en la base y vuelve a exponer la capa de abajo,
   la sensible al rojo: alrededor de las luces queda un halo rojo anaranjado.
4. **La curva.** La película reversible (la de las películas caseras: Kodachrome, Ektachrome) es contrastada:
   negros hundidos y luces que se doblan suave, en vez de recortarse. Cada emulsión con su color.
5. **El grano**, en la densidad (donde vive: los granos de plata y las nubes de tinte), nuevo en cada cuadro de
   película y del tamaño que le toca al formato: el mismo grano en un cuadro chico (Super 8) se ve más grande.
6. **Los tintes que se destiñen.** En las copias de color que envejecen se van primero el cian y el amarillo y el
   magenta queda: la imagen se pone roja y pierde contraste.
7. **Lo que se pega a la película:** polvo (negro en la reversible proyectada; los rasguños de la emulsión,
   claros), rayas que duran, y el pelo en la ventanilla, que no se mueve con la imagen.
8. **El vaivén.** El Super 8 no tiene uña de registro: el cuadro baila un poco en la ventanilla.
9. **Los cuadros por segundo.** 18 por segundo es la velocidad de fábrica del Super 8; a 30 del video, cada cuadro
   de película dura dos o uno (2, 2, 1…): el paso un poco a saltos de las películas caseras.

Con `marco` se ve la ventanilla (el cuadro con sus esquinas redondeadas sobre negro) o el escaneo entero (la
tira con su perforación y los bordes de los cuadros vecinos, la luz del escáner por fuera). Con `fecha`, la fecha
naranja que imprimían las cámaras de rollo de bolsillo (para las fotos).

Las referencias, con sus fuentes y lo que no se pudo verificar, están en `direccion/ANALOGO.md` («La película»).
"""

from __future__ import annotations

import math

import numpy as np

from . import analogo as A

#: El cuadro de cada formato en la cámara (mm), qué tan blando lo deja el conjunto de lente y película (sigma en
#: pixeles a 1080 de alto) y el vaivén (desvío del cuadro, en fracción del ancho y del alto). Las medidas del
#: Super 8 son de la norma (ver ANALOGO.md); el blando y el vaivén, puntos de partida mirados en las hojas.
FORMATOS = {
    "super8": {"ancho_mm": 5.69, "alto_mm": 4.22, "blando": 1.8, "vaiven": (0.0016, 0.0024),
               # el escaneo: ancho de la tira, dónde empieza el cuadro, paso entre cuadros, la perforación (x, ancho, alto)
               "tira_mm": 7.976, "cuadro_x_mm": 1.5, "paso_mm": 4.234, "perforacion": (0.53, 0.91, 1.14), "perf_en": "centro"},
    "8mm": {"ancho_mm": 4.5, "alto_mm": 3.3, "blando": 2.1, "vaiven": (0.0022, 0.0030),
            "tira_mm": 8.0, "cuadro_x_mm": 2.6, "paso_mm": 3.81, "perforacion": (0.55, 1.83, 1.27), "perf_en": "linea"},
    "16mm": {"ancho_mm": 10.26, "alto_mm": 7.49, "blando": 0.9, "vaiven": (0.0008, 0.0012),
             "tira_mm": 16.0, "cuadro_x_mm": 3.1, "paso_mm": 7.62, "perforacion": (0.9, 1.83, 1.27), "perf_en": "linea"},
    # El rollo de fotos: el cuadro de 36 × 24 de la cámara de bolsillo, quieto (no hay vaivén en una foto). Su tira
    # corre de lado, con perforaciones arriba y abajo: el escaneo no está hecho para él (va con `ventanilla`).
    "35mm": {"ancho_mm": 36.0, "alto_mm": 24.0, "blando": 0.45, "vaiven": (0.0, 0.0)},
}
#: Cada emulsión: contraste (la pendiente de la curva), equilibrio (cuánto más o menos luz recibe cada capa, en
#: pasos: el color de la película), saturación, densidad máxima (qué tan negro es su negro) y granularidad (desvío
#: de la densidad a 48 µm, en milésimas: el «RMS granularity» de los catálogos). [sin verificar] las cifras exactas:
#: el Kodachrome 40 era de grano muy fino y colores densos; el Ektachrome, más frío y de más grano.
EMULSIONES = {
    "kodachrome": {"contraste": 1.25, "equilibrio": (0.10, 0.0, -0.12), "saturacion": 1.3, "dmax": 3.4, "granularidad": 9},
    "ektachrome": {"contraste": 1.05, "equilibrio": (-0.10, 0.0, 0.12), "saturacion": 1.08, "dmax": 3.0, "granularidad": 13},
    "blanco-y-negro": {"contraste": 1.3, "equilibrio": (0.0, 0.0, 0.0), "saturacion": 0.0, "dmax": 2.8, "granularidad": 15},
    # El negativo de color de los rollos de farmacia, copiado en papel en el laboratorio de una hora: menos
    # contraste que la reversible, negros que no llegan a negro (el papel), cálido el Kodak Gold y de verdes el Fuji
    # Superia [sin verificar las cifras: es el recuerdo de esas copias, ajustado mirando las hojas].
    "kodak-gold": {"contraste": 0.92, "equilibrio": (0.12, 0.05, -0.16), "saturacion": 1.15, "dmax": 2.2, "granularidad": 11},
    "fuji-superia": {"contraste": 0.95, "equilibrio": (-0.04, 0.07, 0.0), "saturacion": 1.18, "dmax": 2.2, "granularidad": 10},
}
#: La luz con el filtro bien o mal puesto (ganancia de cada canal en la luz que llega).
BALANCES = {"correcto": (1.0, 1.0, 1.0), "naranja": (1.0, 0.74, 0.44), "azul": (0.66, 0.86, 1.22)}
MARCOS = ("ninguno", "ventanilla", "escaneo")
GRUMO_UM = 14.0   # el tamaño de un grumo de grano en la película, µm [sin verificar]

POR_DEFECTO = {
    "pelicula": {"formato": "super8", "emulsion": "kodachrome", "cuadros": 18, "exposicion": 0.0, "balance": "correcto",
                 "grano": 1.0, "halo": 1.0, "vaiven": 1.0, "parpadeo": 0.3, "vineta": 0.3, "polvo": 0.6, "rayas": 0.3,
                 "pelo": 0.0, "quemado": 0.0, "desvanecido": 0.0, "marco": "ninguno", "fecha": "", "sonido": "ninguno"},
}
SONIDOS = ("ninguno", "magnetico", "proyector")
RANGOS = {
    "pelicula": {"formato": tuple(FORMATOS), "emulsion": tuple(EMULSIONES), "cuadros": (0, 60), "exposicion": (-3, 3),
                 "balance": tuple(BALANCES), "grano": (0, 3), "halo": (0, 3), "vaiven": (0, 4), "parpadeo": (0, 2),
                 "vineta": (0, 1), "polvo": (0, 4), "rayas": (0, 4), "pelo": (0, 6), "quemado": (0, 30),
                 "desvanecido": (0, 1), "marco": MARCOS, "sonido": ("ninguno", "magnetico", "proyector")},
}
_CARACTERES_FECHA = set("0123456789 '-.:")


def errores(nombre: str, a: dict) -> list[str]:
    mal = []
    f = a.get("fecha", "")
    if not isinstance(f, str) or not set(f) <= _CARACTERES_FECHA or len(f) > 16:
        mal.append("pelicula.fecha: dígitos, espacios y ' - . : (hasta 16), como «'94 10 12»")
    if a.get("marco") == "escaneo" and a.get("formato") == "35mm":
        mal.append("pelicula: el escaneo con la tira es de la película de cine; para el 35 mm de fotos, `ventanilla`")
    return mal


def sonido(nombre: str, x: np.ndarray, p: dict, semilla: int, t0: float, sr: int, indice: int) -> np.ndarray:
    """El sonido de la película. `magnetico`: la banda magnética del Super 8 sonoro (estrecha y con más temblor que
    el VHS, [sin verificar] las cifras: van las de la pista lineal en LP con el temblor subido). `proyector`: el
    traqueteo del proyector (un golpecito por cuadro de película, el motor) debajo del audio, 18 dB más bajo."""
    if p.get("sonido", "ninguno") == "ninguno" or not len(x):
        return x
    if p["sonido"] == "magnetico":
        return A.sonido_de_cinta(x, {"sonido": "lineal", "formato": "LP", "generaciones": 1, "desgaste": 0.35, "temblor": 1.6,
                                     "arrugas": 0.0}, semilla, t0, sr, indice)
    from .proyector import traqueteo

    rng = np.random.default_rng([semilla, A._num("traqueteo"), indice])
    fps = p.get("_fps")   # el traqueteo va a los cuadros de película que se ven: los suyos, o los del video si son menos
    ritmo = p["cuadros"] if p["cuadros"] and (fps is None or p["cuadros"] < fps) else (fps or 18)
    ruido = traqueteo(len(x) / sr, ritmo, rng)[: len(x)]
    if len(ruido) < len(x):
        ruido = np.pad(ruido, ((0, len(x) - len(ruido)), (0, 0)))
    if x.shape[1] != ruido.shape[1]:
        ruido = ruido[:, : x.shape[1]] if x.shape[1] < 2 else np.repeat(ruido[:, :1], x.shape[1], axis=1)
    nivel = max(float(np.sqrt(np.mean(x ** 2))), 10 ** (-30 / 20))
    return (x + ruido * nivel * 10 ** (-18 / 20)).astype(np.float32)


CONSEJO = {"pelicula": "sube los `cuadros` de la película"}


def calentar(pasos: list[tuple[str, dict]], fps: float, solo: int | None = None) -> int:
    """Un cuadro de película dura varios del video: el pedazo tiene que haber visto el primero. Con `solo`, sólo
    el aparato de ese lugar de la cadena."""
    n = 0
    for i, (nombre, p) in enumerate(pasos):
        if solo is not None and i != solo:
            continue
        if nombre == "pelicula" and 0 < p["cuadros"] < fps:
            n = max(n, int(math.ceil(fps / p["cuadros"])) + 1)
    return n


# ── El tiempo de la película ───────────────────────────────────────────────

def cuadro_de_pelicula(k: int, fps: float, cuadros: float) -> int:
    """Qué cuadro de película se ve en el cuadro `k` del video."""
    if not cuadros or cuadros >= fps:
        return k
    return int(math.floor(k * cuadros / fps + 1e-6))


def evento_con_id(semilla: int, nombre: str, t: float, por_minuto: float, dura: float) -> tuple[float, int] | None:
    """Como `analogo.evento`, pero dice también cuál evento es (para que una raya conserve su lugar mientras dura)."""
    if por_minuto <= 0:
        return None
    ranura = 2 * dura
    prob = min(1.0, por_minuto / 60 * ranura)
    n = math.floor(t / ranura)
    for s in (n, n - 1):
        r = np.random.default_rng([semilla, A._num(nombre), s + 1_000_000])
        if r.random() < prob:
            inicio = (s + r.random()) * ranura
            if inicio <= t < inicio + dura:
                return (t - inicio) / dura, s + 1_000_000   # positivo: sirve de semilla
    return None


# ── Piezas ─────────────────────────────────────────────────────────────────

def _a_tamano(img: np.ndarray, h: int, w: int) -> np.ndarray:
    """Recorta el centro a la proporción h×w y lleva la imagen a ese tamaño."""
    from PIL import Image

    ih, iw = img.shape[:2]
    if (ih, iw) == (h, w):
        return img
    if iw / ih > w / h:
        cw = int(round(ih * w / h))
        x0 = (iw - cw) // 2
        img = img[:, x0:x0 + cw]
    else:
        ch = int(round(iw * h / w))
        y0 = (ih - ch) // 2
        img = img[y0:y0 + ch]
    return np.asarray(Image.fromarray(A._ocho_bits(img)).resize((w, h), Image.LANCZOS), np.float32) / 255


def _ampliar(plano: np.ndarray, h: int, w: int) -> np.ndarray:
    from PIL import Image

    return np.asarray(Image.fromarray(np.ascontiguousarray(plano, np.float32), mode="F").resize((w, h), Image.BICUBIC))


def _grano(rng: np.random.Generator, h: int, w: int, tam: float) -> np.ndarray:
    """Ruido de desvío 1 con grumos de `tam` pixeles."""
    if tam < 1.3:
        return rng.standard_normal((h, w), dtype=np.float32)
    n = rng.standard_normal((max(2, int(math.ceil(h / tam))), max(2, int(math.ceil(w / tam)))), dtype=np.float32)
    g = _ampliar(n, h, w)
    return g / (g.std() + 1e-6)


def _desenfocar(x: np.ndarray, sigma: float) -> np.ndarray:
    from scipy import ndimage

    if sigma < 0.3:
        return x
    return ndimage.gaussian_filter(x, (sigma, sigma, 0) if x.ndim == 3 else sigma, mode="nearest", truncate=2.5)


def _resplandor(x: np.ndarray, sigma: float) -> np.ndarray:
    """Un desenfoque ancho, calculado a un cuarto (el halo no tiene detalle)."""
    from scipy import ndimage

    h, w = x.shape[:2]
    h4, w4 = max(2, h // 4), max(2, w // 4)
    chico = x[: h4 * 4, : w4 * 4].reshape(h4, 4, w4, 4).mean(axis=(1, 3))
    chico = ndimage.gaussian_filter(chico, sigma / 4, mode="constant")
    return _ampliar(chico, h, w)


def _correr(img: np.ndarray, dx: float, dy: float) -> np.ndarray:
    """La imagen corrida (dx, dy) pixeles, con fracción; el borde se repite."""
    if abs(dx) < 1e-3 and abs(dy) < 1e-3:
        return img
    h, w = img.shape[:2]
    ix, iy = math.floor(dx), math.floor(dy)
    fx, fy = dx - ix, dy - iy
    c0 = np.clip(np.arange(w) - ix, 0, w - 1)
    c1 = np.clip(c0 - 1, 0, w - 1)
    f0 = np.clip(np.arange(h) - iy, 0, h - 1)
    f1 = np.clip(f0 - 1, 0, h - 1)
    a = img[:, c0] * (1 - fx) + img[:, c1] * fx
    return a[f0] * (1 - fy) + a[f1] * fy


_VINETAS: dict = {}


def _vineta(h: int, w: int, fuerza: float) -> np.ndarray:
    clave = (h, w, fuerza)
    if clave not in _VINETAS:
        _VINETAS.clear()
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        r2 = ((x + 0.5) / w * 2 - 1) ** 2 * (w / max(h, w)) ** 2 + ((y + 0.5) / h * 2 - 1) ** 2 * (h / max(h, w)) ** 2
        _VINETAS[clave] = (1 - fuerza * 0.55 * np.clip(r2, 0, 2) ** 1.4).astype(np.float32)[..., None]
    return _VINETAS[clave]


# ── La fecha de las cámaras de rollo: siete segmentos ─────────────────────

#: Los segmentos de cada dígito: a arriba, b arriba a la derecha, c abajo a la derecha, d abajo, e abajo a la
#: izquierda, f arriba a la izquierda, g al medio.
_SIETE = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc",
          "8": "abcdefg", "9": "abcdfg", "-": "g"}


def _digito(x0: float, y0: float, a: float, h: float, g: float, segs: str) -> list[list[tuple[float, float]]]:
    """Los polígonos de un dígito de siete segmentos (ancho `a`, alto `h`, grosor `g`), con la esquina arriba a la
    izquierda en (x0, y0)."""
    m = g / 2
    horiz = {"a": y0, "g": y0 + h / 2, "d": y0 + h}
    vert = {"f": (x0, y0, y0 + h / 2), "b": (x0 + a, y0, y0 + h / 2), "e": (x0, y0 + h / 2, y0 + h), "c": (x0 + a, y0 + h / 2, y0 + h)}
    pol = []
    for s in segs:
        if s in horiz:
            y = horiz[s]
            pol.append([(x0 + m, y), (x0 + 2 * m, y - m), (x0 + a - 2 * m, y - m), (x0 + a - m, y), (x0 + a - 2 * m, y + m),
                        (x0 + 2 * m, y + m)])
        else:
            x, ya, yb = vert[s]
            pol.append([(x, ya + m), (x + m, ya + 2 * m), (x + m, yb - 2 * m), (x, yb - m), (x - m, yb - 2 * m), (x - m, ya + 2 * m)])
    return pol


_FECHAS: dict = {}


def _fecha(texto: str, h: int, w: int) -> np.ndarray:
    """La máscara (0–1) de la fecha abajo a la derecha, en siete segmentos inclinados, un poco difusa (la imprimían
    unos diodos desde atrás de la película)."""
    from PIL import Image, ImageDraw, ImageFilter

    clave = (texto, h, w)
    if clave in _FECHAS:
        return _FECHAS[clave]
    alto_d = 0.046 * h
    a, g = alto_d * 0.52, alto_d * 0.15
    avance = a + alto_d * 0.42
    ancho_total = sum(alto_d * 0.25 if c in "'.: " else avance for c in texto)
    x = w - 0.075 * w - ancho_total
    y0 = h - 0.085 * h - alto_d
    lienzo = Image.new("L", (w, h))
    d = ImageDraw.Draw(lienzo)
    inclinar = 0.12

    def sesgo(pts):
        return [(px + (y0 + alto_d - py) * inclinar, py) for px, py in pts]

    for c in texto:
        if c in _SIETE:
            for pol in _digito(x, y0, a, alto_d, g, _SIETE[c]):
                d.polygon(sesgo(pol), fill=255)
            x += avance
        elif c == "'":
            d.polygon(sesgo([(x, y0), (x + g, y0), (x + g * 0.4, y0 + alto_d * 0.3), (x - g * 0.4, y0 + alto_d * 0.3)]), fill=255)
            x += alto_d * 0.25
        elif c in ".:":
            for yy in ((y0 + alto_d - g,) if c == "." else (y0 + alto_d * 0.3, y0 + alto_d * 0.7)):
                d.polygon(sesgo([(x, yy), (x + g, yy), (x + g, yy + g), (x, yy + g)]), fill=255)
            x += alto_d * 0.25
        else:
            x += alto_d * 0.25
    lienzo = lienzo.filter(ImageFilter.GaussianBlur(max(0.6, h / 1080 * 1.2)))
    _FECHAS.clear()
    _FECHAS[clave] = np.asarray(lienzo, np.float32) / 255
    return _FECHAS[clave]


# ── Lo que se pega a la película ──────────────────────────────────────────

def _polvo(rng: np.random.Generator, h: int, w: int, n: int, escala: float) -> tuple[np.ndarray, np.ndarray]:
    """Polvo y fibras de un cuadro: máscaras (oscuro, claro). En la reversible proyectada el polvo es negro; un
    rasguño que se llevó la emulsión deja pasar la luz: claro."""
    from PIL import Image, ImageDraw, ImageFilter

    oscuro, claro = Image.new("L", (w, h)), Image.new("L", (w, h))
    do, dc = ImageDraw.Draw(oscuro), ImageDraw.Draw(claro)
    for _ in range(n):
        d = do if rng.random() < 0.72 else dc
        cx, cy = rng.uniform(0, w), rng.uniform(0, h)
        if rng.random() < 0.18:  # una fibra: una línea que dobla
            puntos = [(cx, cy)]
            ang = rng.uniform(0, 2 * math.pi)
            paso = rng.uniform(3, 11) * escala
            for _ in range(4):
                ang += rng.normal(0, 0.6)
                puntos.append((puntos[-1][0] + math.cos(ang) * paso, puntos[-1][1] + math.sin(ang) * paso))
            d.line(puntos, fill=int(rng.uniform(150, 255)), width=max(1, int(round(rng.uniform(0.8, 1.8) * escala))))
        else:  # una mota: un polígono irregular
            r = rng.uniform(0.8, 4.0) * escala * (3.0 if rng.random() < 0.08 else 1.0)
            angulos = np.sort(rng.uniform(0, 2 * math.pi, 7))
            d.polygon([(cx + r * rng.uniform(0.55, 1.2) * math.cos(t), cy + r * rng.uniform(0.55, 1.2) * math.sin(t))
                       for t in angulos], fill=int(rng.uniform(170, 255)))
    suave = ImageFilter.GaussianBlur(max(0.4, 0.6 * escala))
    return (np.asarray(oscuro.filter(suave), np.float32) / 255, np.asarray(claro.filter(suave), np.float32) / 255)


def _rayas(T: np.ndarray, p: dict, semilla: int, j: int, tj: float, escala: float) -> np.ndarray:
    """Rayas verticales que duran unos segundos en su lugar (la película pasó rozando algo): claras si se llevaron
    la emulsión, oscuras si son de la base."""
    h, w = T.shape[:2]
    x = np.arange(w, dtype=np.float32)
    for m in range(3):
        ev = evento_con_id(semilla, f"raya-{m}", tj, p["rayas"] * 2.5, 2.6)
        if ev is None:
            continue
        _, ident = ev
        r = np.random.default_rng([semilla, A._num("raya"), m, ident])
        x0 = r.uniform(0.06, 0.94) * w + 2.5 * escala * A.suave(semilla + ident, f"raya-x{m}", tj, 0.5)
        ancho = r.uniform(0.6, 1.6) * escala
        claro = r.random() < 0.6
        fuerza = r.uniform(0.25, 0.6) * np.random.default_rng([semilla, A._num("raya-pulso"), m, j]).uniform(0.6, 1.0)
        perfil = np.exp(-0.5 * ((x - x0) / ancho) ** 2)
        largo = 0.6 + 0.4 * np.sin(np.linspace(0, r.uniform(2, 7), h) + r.uniform(0, 6.3)).astype(np.float32)
        mascara = (fuerza * largo[:, None] * perfil[None, :])[..., None]
        T = T + mascara * (1 - T) * 0.9 if claro else T * (1 - mascara)
    return T


def _pelo(p: dict, semilla: int, j: int, tj: float, h: int, w: int, escala: float) -> np.ndarray | None:
    """El pelo en la ventanilla: entra por un borde y se queda unos segundos, temblando apenas; no se mueve con la
    imagen porque está en la ventanilla, no en la película."""
    from PIL import Image, ImageDraw

    ev = evento_con_id(semilla, "pelo", tj, p["pelo"], 4.0)
    if ev is None:
        return None
    _, ident = ev
    r = np.random.default_rng([semilla, A._num("pelo"), ident])
    lado = int(r.integers(4))
    largo = r.uniform(0.1, 0.28) * h
    base = r.uniform(0.15, 0.85)
    x, y = [(0, base * h), (w, base * h), (base * w, 0), (base * w, h)][lado]
    ang = [0.0, math.pi, math.pi / 2, -math.pi / 2][lado] + r.uniform(-0.6, 0.6)
    tiembla = np.random.default_rng([semilla, A._num("pelo-tiembla"), ident, j]).normal(0, 0.035)
    puntos = [(x, y)]
    curva = r.normal(0, 0.5)
    for s in range(14):
        ang += curva / 14 + tiembla
        puntos.append((puntos[-1][0] + math.cos(ang) * largo / 14, puntos[-1][1] + math.sin(ang) * largo / 14))
    lienzo = Image.new("L", (w, h))
    ImageDraw.Draw(lienzo).line(puntos, fill=245, width=max(1, int(round(r.uniform(1.4, 2.4) * escala))), joint="curve")
    return np.asarray(lienzo, np.float32) / 255


def _fuga(semilla: int, tj: float, quemado: float, h: int, w: int) -> np.ndarray | None:
    """El velo del principio o el final del rollo: luz naranja que entra por un borde, sube y se va."""
    ev = evento_con_id(semilla, "fuga", tj, quemado * 0.7, 1.4)
    if ev is None:
        return None
    u, ident = ev
    r = np.random.default_rng([semilla, A._num("fuga"), ident])
    fuerza = math.sin(math.pi * u) ** 0.7 * r.uniform(2.5, 7.0)
    lado = int(r.integers(4))
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    d = [x / w, 1 - x / w, y / h, 1 - y / h][lado]
    a_lo_largo = [y / h, y / h, x / w, x / w][lado]
    forma = np.exp(-d / r.uniform(0.15, 0.35)) * (0.55 + 0.45 * np.sin(a_lo_largo * r.uniform(2, 5) + r.uniform(0, 6.3)))
    return (forma[..., None] * np.array([1.0, 0.42, 0.10], np.float32) * fuerza).astype(np.float32)


# ── El cuadro ──────────────────────────────────────────────────────────────

def _expuesto(escena: np.ndarray, p: dict, semilla: int, j: int, tj: float, cps: float) -> np.ndarray:
    """La escena vuelta luz sobre la emulsión: el filtro, la exposición, el quemado, la fecha, el halo y lo blando."""
    h, w = escena.shape[:2]
    fmt = FORMATOS[p["formato"]]
    rng = np.random.default_rng([semilla, A._num("expo"), j])
    E = np.power(np.clip(escena, 0, 1), 2.2, dtype=np.float32) * np.array(BALANCES[p["balance"]], np.float32)
    ganancia = 2 ** p["exposicion"] * (1 + 0.07 * p["parpadeo"] * float(np.clip(rng.standard_normal(), -2.5, 2.5)))
    if p["quemado"]:  # al arrancar la cámara el motor todavía no llega a su velocidad: los primeros cuadros se queman
        u = A.evento(semilla, "arranque", tj, p["quemado"] * 1.5, 3 / max(cps, 1))
        if u is not None:
            ganancia *= 2 ** (2.6 * (1 - u))
    E = E * ganancia
    if p["vineta"]:
        E = E * _vineta(h, w, p["vineta"])
    if p["quemado"]:
        fuga = _fuga(semilla, tj, p["quemado"], h, w)
        if fuga is not None:
            E = E + fuga
    if p["fecha"]:  # la luz de los diodos, rojo anaranjada: el rojo llega al hombro de la curva y el verde no
        E = E + _fecha(p["fecha"], h, w)[..., None] * np.array([2.0, 0.2, 0.03], np.float32)
    escala = h / 1080
    blanda = _desenfocar(E, fmt["blando"] * escala)
    if p["halo"]:  # la luz que rebota en la base vuelve a la capa de abajo, la del rojo
        luz = E.max(axis=2) if E.ndim == 3 else E
        halo = _resplandor(np.clip(luz - 0.9, 0, None), 0.016 * h) * p["halo"] * 1.2
        tinte = np.array([1.0, 0.3, 0.06], np.float32) if p["emulsion"] != "blanco-y-negro" else np.array([0.5, 0.5, 0.5], np.float32)
        blanda = blanda + halo[..., None] * tinte
    return blanda


def _revelado(E: np.ndarray, p: dict) -> np.ndarray:
    """La curva de la reversible: de la luz a lo que deja pasar la película (transmitancia, 0–1). En pasos: la
    pendiente es el contraste; las luces se doblan suave y las sombras se hunden."""
    emu = EMULSIONES[p["emulsion"]]
    c = 1.107 * emu["contraste"]   # pendiente que deja el gris medio en su lugar con un contraste de ~1,3 (ver arriba)
    u0 = 1.476 / c
    tmax, tmin = 0.97, 10 ** -emu["dmax"]
    if p["emulsion"] == "blanco-y-negro":
        E = (E @ np.array([0.25, 0.62, 0.13], np.float32))[..., None]
    pasos_ = np.log2(np.maximum(E, 1e-6) / 0.18)
    if E.shape[-1] == 3:
        pasos_ = pasos_ + np.array(emu["equilibrio"], np.float32)
    T = tmin + (tmax - tmin) / (1 + np.exp(-c * (pasos_ - u0)))
    if emu["saturacion"] and T.shape[-1] == 3 and emu["saturacion"] != 1:
        lt = np.log(T)
        medio = lt @ np.array([0.3, 0.59, 0.11], np.float32)
        T = np.exp(medio[..., None] + emu["saturacion"] * (lt - medio[..., None]))
    return T.astype(np.float32)


def _en_la_densidad(T: np.ndarray, p: dict, semilla: int, j: int, um_px: float) -> np.ndarray:
    """El grano y los tintes que se destiñen, donde viven: en la densidad (D = −log10 T)."""
    h, w = T.shape[:2]
    D = -np.log10(np.maximum(T, 1e-5))
    if p["grano"]:
        emu = EMULSIONES[p["emulsion"]]
        # La granularidad del catálogo es a 48 µm; un pixel más chico que el grumo ve el grumo entero (Selwyn).
        sigma = p["grano"] * emu["granularidad"] / 1000 * 48 / max(GRUMO_UM, um_px)
        tam = max(1.0, GRUMO_UM / um_px)
        rng = np.random.default_rng([semilla, A._num("grano"), j])
        comun = _grano(rng, h, w, tam)
        if D.shape[-1] == 3:  # tres capas, cada una con su grano; se parecen porque las expuso la misma luz
            ruido = np.stack([0.75 * comun + 0.66 * _grano(rng, h, w, tam) for _ in range(3)], axis=-1)
        else:
            ruido = comun[..., None]
        D = D + sigma * np.sqrt(np.clip(D, 0.03, 3.0) / 0.75) * ruido
    if p["desvanecido"]:
        f = p["desvanecido"]
        if D.shape[-1] == 3:  # el cian (que frena el rojo) y el amarillo (el azul) se van primero: queda rojo
            D = D * np.array([1 - 0.62 * f, 1 - 0.16 * f, 1 - 0.45 * f], np.float32) + 0.04 * f
        else:  # la plata no se destiñe así: pierde contraste y la base amarillea
            D = D * (1 - 0.35 * f) + 0.05 * f
    T = 10 ** (-D)
    if p["desvanecido"] and T.shape[-1] == 1:
        T = T * np.array([1.0, 0.95 - 0.05 * p["desvanecido"], 0.82 - 0.1 * p["desvanecido"]], np.float32)
    return T.astype(np.float32)


def _geometria_escaneo(p: dict, alto: int, ancho: int) -> dict:
    fmt = FORMATOS[p["formato"]]
    # Pixeles por mm: el cuadro y un poco de sus vecinos; en una salida angosta (vertical, cuadrada) manda el ancho
    # de la tira, con un poco de luz a los lados.
    s = min(alto / (fmt["paso_mm"] * 1.3), ancho / (fmt["tira_mm"] * 1.12))
    tira_w = fmt["tira_mm"] * s
    x_tira = (ancho - tira_w) / 2
    h, w = int(round(fmt["alto_mm"] * s)) // 2 * 2, int(round(fmt["ancho_mm"] * s)) // 2 * 2
    return {"s": s, "x_tira": x_tira, "tira_w": tira_w, "h": h, "w": w,
            "x0": int(round(x_tira + fmt["cuadro_x_mm"] * s)), "y0": (alto - h) // 2}


def ventana(p: dict, alto: int, ancho: int) -> tuple[int, int, int, int]:
    """(y0, x0, alto, ancho) del cuadro de película en la salida."""
    fmt = FORMATOS[p["formato"]]
    if p["marco"] == "ninguno":
        return 0, 0, alto, ancho
    if p["marco"] == "escaneo":
        g = _geometria_escaneo(p, alto, ancho)
        return g["y0"], g["x0"], g["h"], g["w"]
    prop = fmt["ancho_mm"] / fmt["alto_mm"]
    h = min(alto * 0.92, ancho * 0.94 / prop)
    h, w = int(round(h)) // 2 * 2, int(round(h * prop)) // 2 * 2
    return (alto - h) // 2, (ancho - w) // 2, h, w


def _esquinas(h: int, w: int, radio: float, borde: float) -> np.ndarray:
    """Un rectángulo de esquinas redondeadas con el borde difuso (la ventanilla está fuera de foco)."""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = np.maximum(np.maximum(radio - (x + 0.5), (x + 0.5) - (w - radio)), 0)
    dy = np.maximum(np.maximum(radio - (y + 0.5), (y + 0.5) - (h - radio)), 0)
    fuera = np.sqrt(dx * dx + dy * dy) - radio
    lado = np.minimum(np.minimum(x + 0.5, w - x - 0.5), np.minimum(y + 0.5, h - y - 0.5))
    d = np.where((dx > 0) & (dy > 0), -fuera, lado)
    return np.clip(d / max(borde, 0.5), 0, 1).astype(np.float32)[..., None]


_MARCOS: dict = {}


def _componer(img: np.ndarray, p: dict, alto: int, ancho: int, dx: float, dy: float) -> np.ndarray:
    """El cuadro de película en la salida, con su ventanilla o su escaneo."""
    y0, x0, h, w = ventana(p, alto, ancho)
    if p["marco"] == "ninguno":
        return _correr(img, dx, dy)
    escala = alto / 1080
    if p["marco"] == "ventanilla":  # la ventanilla del proyector, quieta; la imagen baila detrás
        clave = ("ventanilla", alto, ancho, p["formato"])
        if clave not in _MARCOS:
            _MARCOS[clave] = _esquinas(h, w, 0.045 * h, 2.5 * escala)
        sale = np.zeros((alto, ancho, 3), np.float32)
        sale[y0:y0 + h, x0:x0 + w] = _correr(img, dx, dy) * _MARCOS[clave]
        return sale
    # El escaneo: la luz del escáner, la tira (la reversible sin exponer es negra), los cuadros con sus esquinas,
    # la perforación (un hueco: deja pasar la luz). Todo baila junto: es la tira la que se mueve.
    g = _geometria_escaneo(p, alto, ancho)
    fmt = FORMATOS[p["formato"]]
    clave = ("escaneo", alto, ancho, p["formato"])
    if clave not in _MARCOS:
        luz = np.full((alto, ancho, 1), 0.93, np.float32)
        a, b = int(round(g["x_tira"])), int(round(g["x_tira"] + g["tira_w"]))
        luz[:, max(0, a):max(0, min(ancho, b))] = 0.0
        esquinas = _esquinas(h, w, 0.06 * h, 1.2 * escala)
        px, pw, ph = (v * g["s"] for v in fmt["perforacion"])
        perf = []
        paso = fmt["paso_mm"] * g["s"]
        vecinos = int(math.ceil(alto / (2 * paso))) + 1   # en una salida alta se ven más cuadros de la tira
        for n in range(-vecinos, vecinos + 1):
            centro = g["y0"] + h / 2 + n * paso + (paso / 2 if fmt["perf_en"] == "linea" else 0)
            perf.append((int(round(g["x_tira"] + px)), int(round(centro - ph / 2)), int(round(pw)), int(round(ph))))
        hueco = _esquinas(int(round(ph)), int(round(pw)), 0.18 * pw, 1.0 * escala)   # la perforación, de esquinas redondas
        _MARCOS.clear()
        _MARCOS[clave] = (luz, esquinas, perf, paso, hueco)
    luz, esquinas, perf, paso, hueco = _MARCOS[clave]
    lienzo = luz.repeat(3, axis=2)
    vecinos = int(math.ceil(alto / (2 * paso))) + 1
    for n in range(-vecinos, vecinos + 1):  # el cuadro y lo que se ve de sus vecinos (la misma imagen: cambian poco)
        ya = int(round(g["y0"] + n * paso))
        a, b = max(0, ya), min(alto, ya + h)
        if b > a:
            lienzo[a:b, g["x0"]:g["x0"] + w] = (img * esquinas)[a - ya:b - ya]
    for x, y, pw, ph in perf:
        a, b = max(0, y), min(alto, y + ph)
        if b > a and x >= 0:
            m = hueco[a - y:b - y]
            lienzo[a:b, x:x + pw] = lienzo[a:b, x:x + pw] * (1 - m) + 0.96 * m
    return _correr(lienzo, dx, dy)


def pelicula(img: np.ndarray, p: dict, ctx) -> np.ndarray:
    """El aparato: la imagen (RGB 0–1) → el cuadro de película, al tamaño de salida."""
    cps = p["cuadros"] if 0 < p["cuadros"] < ctx.fps else ctx.fps
    j = cuadro_de_pelicula(ctx.k, ctx.fps, p["cuadros"])
    clave = ("pelicula", ctx.paso)
    guardado = ctx.estado.get(clave)
    if guardado is not None and guardado[0] == j:   # el mismo cuadro de película: se repite tal cual (grano incluido)
        return guardado[1].copy()
    alto, ancho = ctx.alto, ctx.ancho
    tj = j / cps
    semilla = ctx.semilla * 100 + ctx.paso
    _, _, h, w = ventana(p, alto, ancho)
    fmt = FORMATOS[p["formato"]]
    escena = _a_tamano(img, h, w)
    E = _expuesto(escena, p, semilla, j, tj, cps)
    T = _revelado(E, p)
    T = _en_la_densidad(T, p, semilla, j, fmt["ancho_mm"] * 1000 / w)
    escala = h / 1080
    rng = np.random.default_rng([semilla, A._num("polvo"), j])
    if p["polvo"]:
        n = int(rng.poisson(p["polvo"] * 3.0))
        if n:
            oscuro, claro = _polvo(rng, h, w, n, escala)
            T = T * (1 - 0.9 * oscuro[..., None]) + 0.85 * claro[..., None] * (1 - T)
    if p["rayas"]:
        T = _rayas(T, p, semilla, j, tj, escala)
    if T.shape[-1] == 1:
        T = np.repeat(T, 3, axis=-1)
    imagen_ = np.power(np.clip(T, 0, 1), 1 / 2.2, dtype=np.float32)
    vx, vy = fmt["vaiven"]
    r = np.random.default_rng([semilla, A._num("vaiven"), j])
    dx = p["vaiven"] * vx * w * (0.55 * r.standard_normal() + 0.9 * A.suave(semilla, "vaiven-x", tj, 0.35))
    dy = p["vaiven"] * vy * h * (0.55 * r.standard_normal() + 0.9 * A.suave(semilla, "vaiven-y", tj, 0.3))
    sale = _componer(imagen_, p, alto, ancho, dx, dy)
    if p["pelo"]:
        y0, x0, _, _ = ventana(p, alto, ancho)
        pelo = _pelo(p, semilla, j, tj, h, w, escala)
        if pelo is not None:
            sale[y0:y0 + h, x0:x0 + w] *= (1 - 0.92 * pelo[..., None])
    ctx.estado[clave] = (j, sale)
    return sale.copy()


APARATOS = {"pelicula": pelicula}
