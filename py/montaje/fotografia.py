"""La fotografía de antes: los procesos de antes del rollo y las copias de la foto de familia (dos aparatos de imagen
de la mesa analógica).

Miguel, el 2026-11-22, en el mapa de la galería: eligió «Fotografía de antes» entre los territorios para abrir. La
película (`pelicula.py`, con el 35 mm de laboratorio) ya cubría el rollo; esto va más atrás y más al costado.

`placa` (perilla `proceso`), la imagen hecha con un proceso del siglo XIX:

- **Cianotipo**: el papel pintado a pincel con sales de hierro y expuesto al sol: todo en azul de Prusia, con las
  pinceladas de la emulsión en el borde y la fibra del papel.
- **Colodión húmedo** (el ferrotipo): la placa de metal negro barnizada, sensible sólo al azul (el cielo sale blanco y
  lo rojo, negro), con el borde donde se vertió el colodión, la esquina donde la sostuvo el dedo, las manchas de plata
  y el lente de la época, nítido al centro y arremolinado en los bordes. Con `exposicion`, lo que se mueve se borra
  como en las exposiciones largas.
- **Daguerrotipo**: la placa de plata pulida como un espejo: según cómo le pega la luz se ve positiva o negativa
  (`angulo`: cuánto se mueve la placa), con el velo de colores del óxido en el borde. Con `marco: estuche`, el
  paspartú de bronce de los estuches.
- **Linterna mágica**: la placa de vidrio pintada a mano, proyectada en la pared: blanco y negro con los colores
  planos que se salen un poco de la línea, en su máscara redonda.

`copia` (perilla `forma`), la foto como objeto:

- **La instantánea**: el marco blanco con el borde de abajo ancho; con `revelado`, la imagen que aparece de a poco
  desde el gris verdoso.
- **El fotomatón**: la tira de cuatro cuadros en blanco y negro; cada `intervalo` segundos un flash congela el cuadro
  que viene, y la tira se llena y empieza otra vez.
- **La tarjeta estereoscópica**: las dos fotos casi iguales, de puntas redondeadas, sobre el cartón ocre.

Los colores y las proporciones son [sin verificar]: recuerdos de esos objetos ajustados mirando las hojas. Con
`sonido: camara`, la copia suena (`ruidos.py`): el obturador y el motor que expulsa la instantánea, el flash del
fotomatón.
"""

from __future__ import annotations

import math

import numpy as np

from . import analogo as A
from .pelicula import _a_tamano, _ampliar, _desenfocar, _grano, _vineta

PROCESOS = ("cianotipo", "colodion", "daguerrotipo", "linterna")
FORMAS = ("instantanea", "fotomaton", "estereo")

POR_DEFECTO = {
    "placa": {"proceso": "cianotipo", "exposicion": 0.0, "bordes": 0.6, "manchas": 0.5, "grano": 0.6, "angulo": 0.5,
              "marco": "ninguno"},
    "copia": {"forma": "instantanea", "revelado": 0.0, "intervalo": 1.6, "desvanecido": 0.4, "sonido": "ninguno"},
}
RANGOS = {
    "placa": {"proceso": PROCESOS, "exposicion": (0, 2), "bordes": (0, 1), "manchas": (0, 1), "grano": (0, 2),
              "angulo": (0, 1), "marco": ("ninguno", "estuche")},
    "copia": {"forma": FORMAS, "revelado": (0, 12), "intervalo": (0.6, 1.7), "desvanecido": (0, 1),
              "sonido": ("ninguno", "camara")},
}

#: Los tonos de cada proceso: de lo más oscuro a lo más claro (RGB 0–1). [sin verificar]: mirados en fotos de museo.
CIANOTIPO = [(0.0, (0.03, 0.12, 0.30)), (0.45, (0.10, 0.30, 0.56)), (0.8, (0.55, 0.68, 0.80)), (1.0, (0.95, 0.94, 0.89))]
FERROTIPO = [(0.0, (0.07, 0.06, 0.05)), (0.35, (0.24, 0.20, 0.16)), (0.75, (0.66, 0.62, 0.54)), (1.0, (0.88, 0.85, 0.76))]
PLATA = [(0.0, (0.05, 0.055, 0.06)), (0.5, (0.42, 0.43, 0.43)), (1.0, (0.90, 0.90, 0.87))]
ALBUMINA = [(0.0, (0.16, 0.09, 0.05)), (0.4, (0.46, 0.31, 0.18)), (0.8, (0.84, 0.72, 0.52)), (1.0, (0.95, 0.89, 0.74))]
PAPEL = np.array([0.95, 0.94, 0.90], np.float32)
MARCO_INSTANTANEA = np.array([0.93, 0.92, 0.88], np.float32)
CARTON = np.array([0.78, 0.66, 0.43], np.float32)
FONDO = np.array([0.06, 0.06, 0.065], np.float32)
BRONCE = np.array([0.74, 0.58, 0.30], np.float32)
#: Lo que ve un colodión: casi sólo el azul (y algo del verde) [sin verificar: la sensibilidad espectral exacta varía].
AZUL_SENSIBLE = np.array([0.06, 0.26, 0.68], np.float32)
LUMA = np.array([0.299, 0.587, 0.114], np.float32)


def errores(nombre: str, a: dict) -> list[str]:
    return []


CONSEJO = {"placa": "baja la `exposicion`", "copia": "baja el `intervalo` del fotomatón"}


def calentar(pasos: list[tuple[str, dict]], fps: float, solo: int | None = None) -> int:
    """La exposición larga promedia los cuadros de antes (hasta que lo viejo pesa menos de un 1 %); el fotomatón
    guarda los cuadros que congeló en la vuelta."""
    n = 0
    for i, (nombre, p) in enumerate(pasos):
        if solo is not None and i != solo:
            continue
        if nombre == "placa" and p["exposicion"]:
            n = max(n, int(math.ceil(4.6 * p["exposicion"] * fps)) + 1)
        if nombre == "copia" and p["forma"] == "fotomaton":
            n = max(n, int(math.ceil(4.5 * p["intervalo"] * fps)) + 2)   # del primer flash al final de la vuelta
    return n


# ── Piezas ─────────────────────────────────────────────────────────────────

def _tonos(lum: np.ndarray, tabla) -> np.ndarray:
    """La luminancia (0–1) llevada a los tonos de un proceso, interpolando entre sus puntos."""
    xs = [x for x, _ in tabla]
    sale = np.empty(lum.shape + (3,), np.float32)
    for c in range(3):
        sale[..., c] = np.interp(lum, xs, [col[c] for _, col in tabla])
    return sale


def _mezclar(a: np.ndarray, b, m: np.ndarray) -> np.ndarray:
    return a * (1 - m[..., None]) + np.asarray(b, np.float32) * m[..., None]


_CACHE: dict = {}


def _fibra(h: int, w: int, semilla: int) -> np.ndarray:
    """La fibra del papel: ruido estirado en una dirección, fijo (el papel no cambia de un cuadro a otro). Desvío 1."""
    from scipy import ndimage

    clave = ("fibra", h, w, semilla)
    if clave not in _CACHE:
        r = np.random.default_rng([semilla, A._num("fibra")])
        n = r.standard_normal((h, w)).astype(np.float32)
        n = ndimage.gaussian_filter(n, (max(0.6, h / 900), max(2.0, w / 160)))
        _CACHE[clave] = n / (n.std() + 1e-6)
    return _CACHE[clave]


def _lento(h: int, w: int, semilla: int, nombre: str, tam: float) -> np.ndarray:
    """Un ruido suave y fijo (las manchas, lo desparejo de la emulsión). Desvío 1."""
    clave = ("lento", h, w, semilla, nombre, round(tam, 2))
    if clave not in _CACHE:
        _CACHE[clave] = _grano(np.random.default_rng([semilla, A._num(nombre)]), h, w, tam)
    return _CACHE[clave]


def _radio(h: int, w: int) -> np.ndarray:
    """La distancia al centro, normalizada a 1 en las esquinas."""
    clave = ("radio", h, w)
    if clave not in _CACHE:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        _CACHE[clave] = np.hypot((yy - h / 2) / (h / 2), (xx - w / 2) / (w / 2)) / math.sqrt(2)
    return _CACHE[clave]


def _borde_irregular(h: int, w: int, semilla: int, nombre: str, ancho: float, tam: float, irregular: float = 0.45) -> np.ndarray:
    """1 adentro y 0 afuera de un rectángulo de bordes irregulares (`ancho`: el margen, en fracción del alto)."""
    clave = ("borde", h, w, semilla, nombre, round(ancho, 3), round(tam, 2), irregular)
    if clave not in _CACHE:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        hasta_borde = np.minimum(np.minimum(yy, h - 1 - yy), np.minimum(xx, w - 1 - xx)) / h
        ruido = _lento(h, w, semilla, nombre + "-r", tam)
        _CACHE[clave] = np.clip((hasta_borde - ancho * (1 + irregular * ruido)) / (0.25 * ancho + 1e-3), 0, 1).astype(np.float32)
    return _CACHE[clave]


# ── La placa ───────────────────────────────────────────────────────────────

def _cianotipo(img: np.ndarray, p: dict, semilla: int, rng) -> np.ndarray:
    h, w = img.shape[:2]
    lum = np.clip((img @ LUMA) ** 0.9, 0, 1)
    lum = np.clip(lum + 0.05 * _lento(h, w, semilla, "cian-desparejo", h / 5), 0, 1)
    sale = _tonos(lum, CIANOTIPO)
    papel = PAPEL * (1 + 0.012 * _fibra(h, w, semilla)[..., None])
    if p["bordes"]:  # las pinceladas: el borde de lo emulsionado, con los trazos del pincel donde se acaba
        dentro = _borde_irregular(h, w, semilla, "cian-borde", 0.03 + 0.06 * p["bordes"], h / 6, 0.18)
        trazos = np.clip(0.5 + 0.35 * _fibra(h, w, semilla + 1), 0.05, 1)
        parcial = dentro ** (0.4 + 1.6 * (1 - trazos))       # adentro (1) queda 1; en el borde, los trazos
        sale = _mezclar(papel, sale, parcial)
    sale = sale * (1 + 0.012 * _fibra(h, w, semilla)[..., None])
    return sale


def _colodion(img: np.ndarray, p: dict, semilla: int, rng, ctx) -> np.ndarray:
    h, w = img.shape[:2]
    if p["exposicion"]:  # la exposición larga: lo que se mueve se borra
        clave = ("placa-exposicion", ctx.paso)
        a = 1 / max(1.0, p["exposicion"] * ctx.fps)
        prom = ctx.estado.get(clave)
        prom = img.copy() if prom is None or prom.shape != img.shape else prom * (1 - a) + img * a
        ctx.estado[clave] = prom
        img = prom
    lum = np.clip(img @ AZUL_SENSIBLE / AZUL_SENSIBLE.sum(), 0, 1)
    lum = 1 / (1 + np.exp(-6 * (lum - 0.5)))                            # la curva: contrastada, las luces lechosas
    lum = (lum - lum.min()) / (np.ptp(lum) + 1e-6)
    # El lente de la época: nítido al centro, arremolinado y oscuro en los bordes.
    r = _radio(h, w)
    blando = _desenfocar(lum[..., None], max(1.0, h / 180))[..., 0]
    lum = lum * (1 - np.clip(r * 1.4 - 0.45, 0, 1)) + blando * np.clip(r * 1.4 - 0.45, 0, 1)
    lum = lum * _vineta(h, w, 0.75)[..., 0]
    if p["grano"]:
        lum = lum + 0.025 * p["grano"] * rng.standard_normal((h, w)).astype(np.float32)
    sale = _tonos(np.clip(lum, 0, 1), FERROTIPO)
    if p["manchas"]:  # las manchas de plata y las vetas del revelador
        m = np.clip(_lento(h, w, semilla, "plata", h / 9) - 1.1, 0, 1) * p["manchas"]
        sale = _mezclar(sale, (0.55, 0.48, 0.36), m * 0.6)
        vetas = np.clip(_lento(h, w, semilla, "vetas", h / 40) * 0.5 + 0.5, 0, 1) ** 6 * p["manchas"]
        sale = sale * (1 + 0.25 * vetas[..., None])
    if p["bordes"]:  # el borde donde corrió el colodión, y la esquina del dedo
        dentro = _borde_irregular(h, w, semilla, "colodion-borde", 0.015 + 0.05 * p["bordes"], h / 10, 0.3)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        dedo = np.exp(-(((yy - 0.93 * h) / (0.09 * h)) ** 2 + ((xx - 0.05 * w) / (0.07 * h)) ** 2))
        sale = _mezclar(sale, FERROTIPO[0][1], 1 - dentro * (1 - dedo * p["bordes"]))
    return sale


def _daguerrotipo(img: np.ndarray, p: dict, semilla: int, ctx) -> np.ndarray:
    h, w = img.shape[:2]
    lum = img @ LUMA
    nitido = lum + 0.6 * (lum - _desenfocar(lum[..., None], max(1.0, h / 400))[..., 0])
    lum = np.clip(nitido, 0, 1)
    positiva = _tonos(lum, PLATA)
    negativa = _tonos(1 - lum, [(0.0, (0.02, 0.03, 0.05)), (1.0, (0.36, 0.42, 0.52))])
    # La placa se mueve en la mano: cuánto se ve negativa.
    giro = p["angulo"] * (0.5 + 0.5 * ctx.suave("placa-angulo", 0.12))
    m = np.clip((giro - 0.35) / 0.4, 0, 1)
    reflejo = np.clip(1 - _radio(h, w) * 1.3 + 0.3 * (giro - 0.5), 0, 1)   # el espejo agarra la luz de un lado
    sale = _mezclar(positiva, negativa, np.full((h, w), m, np.float32) * (0.6 + 0.4 * reflejo))
    if p["manchas"]:  # el velo del óxido: un anillo de colores en el borde, y los rayones finos
        r = _radio(h, w)
        anillo = np.clip((r - 0.62) / 0.3, 0, 1) * p["manchas"]
        fase = 6 * r + 0.8 * _lento(h, w, semilla, "oxido", h / 6)
        iris = np.stack([0.55 + 0.35 * np.sin(fase), 0.35 + 0.3 * np.sin(fase + 2.1), 0.45 + 0.4 * np.sin(fase + 4.2)], -1)
        sale = _mezclar(sale, iris.astype(np.float32), anillo * 0.32)
        rayas = np.clip(np.abs(_fibra(h, w, semilla + 7)) - 2.6, 0, 1) * p["manchas"]
        sale = sale + 0.35 * rayas[..., None]
    return sale


def _estuche(img: np.ndarray, h: int, w: int) -> np.ndarray:
    """El paspartú de bronce de un estuche: la ventana ovalada, el bisel y el bronce gastado."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    e = np.hypot((yy - h / 2) / (0.44 * h), (xx - w / 2) / (0.36 * w))
    dentro = np.clip((1 - e) / 0.01, 0, 1)
    bisel = np.clip(1 - np.abs(e - 1.02) / 0.025, 0, 1)
    luz = 0.75 + 0.25 * np.clip(1 - (yy / h + xx / w) / 2, 0, 1)
    bronce = BRONCE * luz[..., None] * (1 - 0.35 * bisel[..., None])
    return _mezclar(bronce, img, dentro)


def _linterna(img: np.ndarray, p: dict, semilla: int) -> np.ndarray:
    """La placa pintada a mano: la foto en blanco y negro, contrastada, y encima los colores planos de la paleta del
    pintor, corridos y desbordados, en su máscara redonda; proyectada, con la luz cálida que cae hacia el borde."""
    from PIL import Image

    h, w = img.shape[:2]
    lum = np.clip((img @ LUMA) ** 0.75 * 1.15, 0, 1)
    chico = np.asarray(Image.fromarray(A._ocho_bits(img)).resize((max(2, w // 24), max(2, h // 24)), Image.BOX), np.float32) / 255
    gris = chico @ LUMA
    sat = np.clip((chico - gris[..., None]) * 4.0 + 0.5, 0, 1)                   # colores de acuarela, planos y vivos
    sat = np.round(sat * 4) / 4                                                  # pocos colores, como la paleta del pintor
    pintura = _ampliar(sat[..., 0], h, w), _ampliar(sat[..., 1], h, w), _ampliar(sat[..., 2], h, w)
    pintura = np.stack(pintura, -1)
    pintura = np.roll(np.roll(_desenfocar(pintura, max(2.0, h / 120)), int(0.006 * h), axis=0), int(0.008 * w), axis=1)
    sale = lum[..., None] * (0.15 + 1.0 * np.clip(pintura, 0, 1))
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    rr = np.hypot(yy - h / 2, xx - w / 2) / (0.46 * h)
    mascara = np.clip((1 - rr) / 0.015, 0, 1)
    luz = np.array([1.0, 0.9, 0.72], np.float32) * (1 - 0.35 * np.clip(rr, 0, 1) ** 2)[..., None]
    return sale * luz * mascara[..., None]


def placa(img: np.ndarray, p: dict, ctx) -> np.ndarray:
    semilla = ctx.semilla * 100 + ctx.paso
    rng = ctx.rng("placa")
    proceso = p["proceso"]
    if proceso == "cianotipo":
        sale = _cianotipo(img, p, semilla, rng)
    elif proceso == "colodion":
        sale = _colodion(img, p, semilla, rng, ctx)
    elif proceso == "daguerrotipo":
        sale = _daguerrotipo(img, p, semilla, ctx)
    else:
        sale = _linterna(img, p, semilla)
    if p["marco"] == "estuche" and proceso != "linterna":   # la linterna ya trae su máscara redonda
        sale = _estuche(sale, *sale.shape[:2])
    return np.clip(sale, 0, 1).astype(np.float32)


# ── La copia ───────────────────────────────────────────────────────────────

def _caja(sale: np.ndarray, y0: int, x0: int, img: np.ndarray) -> None:
    h, w = img.shape[:2]
    sale[y0:y0 + h, x0:x0 + w] = img


def _sombra(sale: np.ndarray, y0: int, x0: int, h: int, w: int) -> None:
    """La sombra de la copia sobre la mesa."""
    d = max(2, int(0.012 * sale.shape[0]))
    sale[y0 + d:y0 + h + d, x0 + d:x0 + w + d] *= 0.55


def _mirada_instantanea(img: np.ndarray, desvanecido: float) -> np.ndarray:
    """El color de la película instantánea: negros levantados, poco contraste, sombras frías y luces tibias."""
    lum = img @ LUMA
    sale = 0.08 + 0.84 * img
    sale = lum[..., None] + (sale - lum[..., None]) * (0.85 - 0.3 * desvanecido)
    sale = sale + np.stack([0.03 * lum - 0.02, 0.0 * lum, 0.04 * (1 - lum)], -1)
    return sale * _vineta(*img.shape[:2], 0.35)


def _instantanea(img: np.ndarray, p: dict, ctx) -> np.ndarray:
    alto, ancho = ctx.alto, ctx.ancho
    alto_marco = int(0.9 * alto)
    ancho_marco = int(alto_marco * 88 / 107)
    lado = int(ancho_marco * 79 / 88)
    margen, arriba = (ancho_marco - lado) // 2, int(ancho_marco * 6 / 88)
    foto = _mirada_instantanea(_a_tamano(img, lado, lado), p["desvanecido"])
    if p["revelado"]:   # desde el gris verdoso: primero la luz, después el color
        v = min(1.0, max(0.0, (ctx.t - ctx.inicio) / p["revelado"]))
        lum = foto @ LUMA
        gris = np.broadcast_to(np.array([0.30, 0.34, 0.29], np.float32), foto.shape)
        luz = np.clip(v / 0.7, 0, 1) ** 1.5
        color = np.clip((v - 0.3) / 0.7, 0, 1)
        sin_color = lum[..., None] + (foto - lum[..., None]) * color
        foto = gris * (1 - luz) + sin_color * luz
    sale = np.broadcast_to(FONDO, (alto, ancho, 3)).copy()
    y0, x0 = (alto - alto_marco) // 2, (ancho - ancho_marco) // 2
    _sombra(sale, y0, x0, alto_marco, ancho_marco)
    marco = np.broadcast_to(MARCO_INSTANTANEA, (alto_marco, ancho_marco, 3)).copy()
    marco *= (1 + 0.015 * _fibra(alto_marco, ancho_marco, 3)[..., None])
    _caja(marco, arriba, margen, foto)
    _caja(sale, y0, x0, marco)
    return sale


def _fotomaton(img: np.ndarray, p: dict, ctx) -> np.ndarray:
    """La tira de cuatro, acostada sobre la mesa: el cuadro que viene se ve en vivo, el flash lo congela."""
    alto, ancho = ctx.alto, ctx.ancho
    pad = int(0.018 * ancho)
    cw = (int(0.94 * ancho) - 5 * pad) // 4
    ch = int(cw * 1.25)
    if ch + 2 * pad > 0.94 * alto:
        ch = int(0.94 * alto) - 2 * pad
        cw = int(ch / 1.25)
    tira_w, tira_h = 4 * cw + 5 * pad, ch + 2 * pad
    intervalo = p["intervalo"]
    ciclo = 5 * intervalo
    tau = ctx.t % ciclo
    vuelta = int(ctx.t // ciclo)
    est = ctx.estado.setdefault(("copia-fotomaton", ctx.paso), {})
    lum = img @ LUMA
    bn = np.clip(1 / (1 + np.exp(-7 * (lum - 0.48))), 0, 1)
    bn = (bn - bn.min()) / (np.ptp(bn) + 1e-6)
    celda_viva = _a_tamano(np.repeat(bn[..., None], 3, -1), ch, cw)
    tira = np.broadcast_to(np.array([0.95, 0.95, 0.93], np.float32), (tira_h, tira_w, 3)).copy()
    destello = 0.0
    for n in range(4):
        disparo = (n + 0.5) * intervalo
        x0 = pad + n * (cw + pad)
        if tau >= disparo:
            clave = (vuelta, n)
            if clave not in est:   # el primer cuadro después del flash: ése queda
                est[clave] = celda_viva
                for viejo in [c for c in est if c[0] < vuelta - 1]:
                    del est[viejo]
            _caja(tira, pad, x0, est[clave])
            destello = max(destello, math.exp(-(tau - disparo) / 0.12))
        elif n == 0 or tau >= (n - 0.5) * intervalo:
            _caja(tira, pad, x0, celda_viva * 0.9)          # el cuadro que viene, en vivo
        else:
            tira[pad:pad + ch, x0:x0 + cw] = 0.82            # el papel que espera
    sale = np.broadcast_to(FONDO, (alto, ancho, 3)).copy()
    y0, x0 = (alto - tira_h) // 2, (ancho - tira_w) // 2
    _sombra(sale, y0, x0, tira_h, tira_w)
    _caja(sale, y0, x0, tira)
    return np.minimum(1.0, sale + 0.7 * destello)


def _estereo(img: np.ndarray, p: dict, ctx) -> np.ndarray:
    """La tarjeta estereoscópica: dos copias a la albúmina, la de la derecha un poco corrida, con las puntas de
    arriba redondeadas, sobre el cartón ocre."""
    alto, ancho = ctx.alto, ctx.ancho
    tw = int(0.94 * ancho)
    th = min(int(tw / 2.0), int(0.94 * alto))
    lado_h = int(th * 0.8)
    lado_w = int(min(lado_h * 0.95, (tw - 3 * int(0.04 * tw)) / 2))
    sep = (tw - 2 * lado_w) // 3
    lum = img @ LUMA
    tono = _tonos(np.clip(lum * (1 - 0.25 * p["desvanecido"]) + 0.1 * p["desvanecido"], 0, 1), ALBUMINA)
    h, w = tono.shape[:2]
    corre = int(0.025 * w)
    izquierda = _a_tamano(tono[:, : w - corre], lado_h, lado_w)
    derecha = _a_tamano(tono[:, corre:], lado_h, lado_w)
    yy, xx = np.mgrid[0:lado_h, 0:lado_w].astype(np.float32)
    radio = 0.22 * lado_w
    puntas = np.ones((lado_h, lado_w), np.float32)
    for cx in (radio, lado_w - radio):
        esquina = (yy < radio) & ((xx < radio) if cx == radio else (xx > lado_w - radio))
        d = np.hypot(yy - radio, xx - cx)
        puntas = np.where(esquina, np.clip(radio - d, 0, 1), puntas)
    carton = CARTON * (1 + 0.03 * _fibra(th, tw, 5)[..., None])
    manchas = np.clip(_lento(th, tw, 5, "foxing", th / 30) - 1.6, 0, 1) * p["desvanecido"]
    carton = _mezclar(carton, (0.55, 0.40, 0.22), manchas * 0.6)
    y_l = int((th - lado_h) * 0.45)
    for x_l, foto in ((sep, izquierda), (2 * sep + lado_w, derecha)):
        zona = carton[y_l:y_l + lado_h, x_l:x_l + lado_w]
        carton[y_l:y_l + lado_h, x_l:x_l + lado_w] = _mezclar(zona, foto, puntas)
    sale = np.broadcast_to(FONDO, (alto, ancho, 3)).copy()
    y0, x0 = (alto - th) // 2, (ancho - tw) // 2
    _sombra(sale, y0, x0, th, tw)
    _caja(sale, y0, x0, carton)
    return sale


def copia(img: np.ndarray, p: dict, ctx) -> np.ndarray:
    forma = p["forma"]
    if forma == "instantanea":
        sale = _instantanea(img, p, ctx)
    elif forma == "fotomaton":
        sale = _fotomaton(img, p, ctx)
    else:
        sale = _estereo(img, p, ctx)
    return np.clip(sale, 0, 1).astype(np.float32)


#: Para el sonido: cuándo dispara el fotomatón (los mismos segundos que la imagen).
def disparos(intervalo: float, desde: float, hasta: float) -> list[float]:
    ciclo = 5 * intervalo
    hay = []
    for v in range(int(desde // ciclo) - 1, int(hasta // ciclo) + 1):
        for n in range(4):
            t = v * ciclo + (n + 0.5) * intervalo
            if desde <= t < hasta:
                hay.append(t)
    return hay


APARATOS = {"placa": placa, "copia": copia}
