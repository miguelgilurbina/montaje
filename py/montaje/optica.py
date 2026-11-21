"""La lente: lo que el vidrio le hace a la luz antes de llegar a la película o al sensor (un aparato de imagen de la
mesa analógica).

Miguel, el 2026-11-21, en tarjetas: «Luz y óptica». La galería ya tenía luces que se cuelan pintadas (`fugas`) y
un foco que respira; esto simula la lente, con el mismo criterio de la mesa:

- **Aberración cromática** (`aberracion`): el vidrio dobla cada color un poco distinto, y cada uno sale a otra
  escala: en los bordes, los contornos se separan en rojo y azul (la lateral, la de las lentes baratas).
- **Barril** (`barril`): las líneas rectas se curvan hacia afuera; fuerte, es el ojo de pez de los videos de skate.
- **Destello** (`destello`): la luz fuerte rebota entre los vidrios y deja fantasmas de colores (por el
  antirreflejo de cada vidrio) en la línea que va de la luz al centro, del otro lado; y un velo que lava el
  contraste.
- **La raya anamórfica** (`raya`): las lentes anamórficas estiran el destello en una raya horizontal azulada.
- **Niebla** (`niebla`): la lente empañada (o un filtro de difusión): lo claro se derrama alrededor y los negros se
  levantan.
- **Suciedad** (`suciedad`): las manchas del vidrio sólo se ven cuando una luz les pega: aparecen en el velo.
- **Foco** (`foco`), y el foco que golpea con la canción (`foco_al_pulso`: se va un instante en cada golpe y
  vuelve). Al pulso necesita los golpes (`--golpes <proyecto>`).
- **Viñeta** (`vineta`): las esquinas reciben menos luz (la caída del coseno a la cuarta y el cuerpo de la lente).

Todo en luz lineal. Lo que no cambia de un cuadro a otro (dónde cae cada pixel con el barril y la aberración, la
viñeta, las manchas) se calcula una vez. Las referencias, en `direccion/ANALOGO.md` («La lente»).
"""

from __future__ import annotations

import math

import numpy as np

from . import analogo as A

POR_DEFECTO = {
    "lente": {"aberracion": 0.0, "barril": 0.0, "destello": 0.0, "raya": 0.0, "niebla": 0.0, "suciedad": 0.0,
              "foco": 0.0, "foco_al_pulso": 0.0, "golpes_cada": "golpe", "vineta": 0.0},
}
RANGOS = {
    "lente": {"aberracion": (0, 3), "barril": (-0.5, 1.5), "destello": (0, 3), "raya": (0, 3), "niebla": (0, 2),
              "suciedad": (0, 2), "foco": (0, 6), "foco_al_pulso": (0, 6), "golpes_cada": ("compas", "golpe", "pico"),
              "vineta": (0, 1)},
}
CONSEJO = {"lente": ""}

#: Los fantasmas del destello: dónde caen (en la línea que va de la luz al centro: negativo, del otro lado; 1, en
#: la luz), cuánto los abre el desenfoque (fracción del alto), cuánto pesan y su color (el del antirreflejo de cada
#: vidrio: ámbar, verde, magenta, cian). [sin verificar] en una lente concreta: puntos de partida mirados.
FANTASMAS = [(-0.45, 0.030, 0.55, (1.0, 0.72, 0.35)), (-0.95, 0.055, 0.35, (0.45, 1.0, 0.55)),
             (-1.35, 0.090, 0.22, (0.95, 0.45, 1.0)), (0.40, 0.020, 0.30, (0.55, 0.85, 1.0)),
             (0.72, 0.045, 0.18, (1.0, 0.85, 0.6))]


def errores(nombre: str, a: dict) -> list[str]:
    return []


def calentar(pasos: list[tuple[str, dict]], fps: float, solo: int | None = None) -> int:
    return 0   # no recuerda nada: el foco al pulso sale de los golpes y del segundo


def necesita_golpes(pasos: list[tuple[str, dict]]) -> bool:
    return any(nombre == "lente" and p["foco_al_pulso"] for nombre, p in pasos)


_GEOMETRIAS: dict = {}


def _geometria(p: dict, alto: int, ancho: int, semilla: int) -> dict:
    """Dónde cae cada pixel de la salida en la imagen de entrada, para cada color: el barril (r → r · (1 + k·r²),
    agrandado para que el borde no quede vacío) y la aberración (cada color a su escala). Y la viñeta y las manchas."""
    from scipy import ndimage

    clave = (alto, ancho, p["barril"], p["aberracion"], p["vineta"], p["suciedad"], semilla)
    if clave in _GEOMETRIAS:
        return _GEOMETRIAS[clave]
    y, x = np.mgrid[0:alto, 0:ancho].astype(np.float32)
    cy, cx = (alto - 1) / 2, (ancho - 1) / 2
    escala = math.hypot(cx, cy)
    dx, dy = (x - cx) / escala, (y - cy) / escala   # 1 en la esquina
    r2 = dx * dx + dy * dy
    k = 0.35 * p["barril"]
    # Con barril, la esquina de la salida tira de más afuera de la imagen: se agranda para que caiga adentro.
    llenar = 1 + k if k > 0 else 1.0
    mapas = []
    for c, a in enumerate((1.0, 0.0, -1.0)):   # rojo más grande, verde quieto, azul más chico
        # La aberración lateral es otra escala por color: el corrimiento crece con la distancia al centro.
        s = (1 + k * r2) / llenar / (1 + a * 0.006 * p["aberracion"])
        sx = np.clip(cx + dx * escala * s, 0, ancho - 1)
        sy = np.clip(cy + dy * escala * s, 0, alto - 1)
        x0, y0 = np.floor(sx).astype(np.int32), np.floor(sy).astype(np.int32)
        mapas.append((y0, x0, np.minimum(y0 + 1, alto - 1), np.minimum(x0 + 1, ancho - 1),
                      (sx - x0).astype(np.float32), (sy - y0).astype(np.float32)))
    vineta = (1 / (1 + 0.6 * p["vineta"] * r2 * 1.6) ** 2).astype(np.float32)   # el coseno a la cuarta, suavizado
    manchas = np.ones((alto // 4 + 1, ancho // 4 + 1), np.float32)
    if p["suciedad"]:  # huellas y polvo del vidrio, fuera de foco: manchas blandas que sólo se ven en el velo
        rng = np.random.default_rng([semilla, A._num("suciedad")])
        h4, w4 = manchas.shape
        campo = np.zeros((h4, w4), np.float32)
        for _ in range(int(6 + 10 * p["suciedad"])):
            yy, xx = rng.uniform(0, h4), rng.uniform(0, w4)
            r = rng.uniform(0.03, 0.12) * h4
            g = np.exp(-(((np.arange(h4)[:, None] - yy) ** 2 + (np.arange(w4)[None, :] - xx) ** 2) / (2 * r * r)))
            campo += rng.uniform(0.5, 1.5) * g.astype(np.float32)
        campo = ndimage.gaussian_filter(campo, 1.5)
        manchas = 0.4 + 1.6 * campo / (campo.max() + 1e-6)
    geo = {"mapas": mapas, "vineta": vineta[..., None], "manchas": manchas}
    _GEOMETRIAS.clear()
    _GEOMETRIAS[clave] = geo
    return geo


def _remapear(lin: np.ndarray, geo: dict) -> np.ndarray:
    sale = np.empty_like(lin)
    for c, (y0, x0, y1, x1, fx, fy) in enumerate(geo["mapas"]):
        canal = lin[..., c]
        arriba = canal[y0, x0] * (1 - fx) + canal[y0, x1] * fx
        abajo = canal[y1, x0] * (1 - fx) + canal[y1, x1] * fx
        sale[..., c] = arriba * (1 - fy) + abajo * fy
    return sale


def _ampliar(chico: np.ndarray, alto: int, ancho: int) -> np.ndarray:
    from PIL import Image

    return np.stack([np.asarray(Image.fromarray(np.ascontiguousarray(chico[..., c]), mode="F").resize((ancho, alto),
                                                                                                         Image.BILINEAR))
                     for c in range(chico.shape[2])], axis=-1)


_ESCALAS: dict = {}


def _escalar(campo: np.ndarray, s: float) -> np.ndarray:
    """El campo agrandado (o achicado, o dado vuelta si `s` es negativo) alrededor del centro: lo que estaba en x
    queda en centro + s·(x − centro)."""
    h, w = campo.shape[:2]
    clave = (h, w, s)
    if clave not in _ESCALAS:
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        cy, cx = (h - 1) / 2, (w - 1) / 2
        sy, sx = cy + (y - cy) / s, cx + (x - cx) / s
        dentro = (sy >= 0) & (sy <= h - 1) & (sx >= 0) & (sx <= w - 1)
        if len(_ESCALAS) > 32:
            _ESCALAS.clear()
        _ESCALAS[clave] = (np.clip(np.round(sy), 0, h - 1).astype(np.int32), np.clip(np.round(sx), 0, w - 1).astype(np.int32),
                           dentro)
    fy, fx, dentro = _ESCALAS[clave]
    sale = campo[fy, fx]
    sale[~dentro] = 0
    return sale


def lente(img: np.ndarray, p: dict, ctx) -> np.ndarray:
    from scipy import ndimage

    alto, ancho = img.shape[:2]
    semilla = ctx.semilla * 100 + ctx.paso
    escala = alto / 1080
    lin = np.power(np.clip(img, 0, 1), 2.2, dtype=np.float32)
    sigma = p["foco"] * 1.6 * escala
    if p["foco_al_pulso"]:  # el foco se va en el golpe y vuelve
        u = A.al_pulso(ctx, p["golpes_cada"], 0.75)
        if u is not None:
            sigma += p["foco_al_pulso"] * 4 * escala * (1 - u) ** 2
    if sigma >= 0.3:
        lin = ndimage.gaussian_filter(lin, (sigma, sigma, 0), mode="nearest", truncate=2.5)
    geo = _geometria(p, alto, ancho, semilla)
    if p["barril"] or p["aberracion"]:
        lin = _remapear(lin, geo)
    if p["vineta"]:
        lin = lin * geo["vineta"]
    if p["destello"] or p["raya"] or p["niebla"]:
        # Lo que hace el vidrio con la luz fuerte, a un cuarto (no tiene detalle).
        h4, w4 = alto // 4, ancho // 4
        chico = lin[: h4 * 4, : w4 * 4].reshape(h4, 4, w4, 4, 3).mean(axis=(1, 3))
        # En un video el blanco ya es lo más claro que hay (lo que de verdad era el sol quedó recortado ahí): lo que
        # brilla es lo que pasa de la mitad de la luz, cada vez más.
        brillo = (np.clip(chico.max(axis=2) - 0.5, 0, None) / 0.5) ** 2
        luz = chico * (brillo / (chico.max(axis=2) + 1e-6))[..., None]   # el color de lo que brilla
        extra = np.zeros_like(chico)
        if p["destello"]:
            for s, abre, peso, tinte in FANTASMAS:
                fantasma = _escalar(luz, s)
                r = max(1.0, abre * h4)
                fantasma = ndimage.gaussian_filter(fantasma, (0.7 * r, 0.7 * r, 0))   # fuera de foco: un disco blando
                extra += p["destello"] * peso * 2.2 * fantasma * np.array(tinte, np.float32)
            extra += p["destello"] * 0.04 * float(brillo.mean()) * 30   # el velo: el contraste se lava
        if p["raya"]:  # la raya anamórfica: el brillo estirado de lado, azulado
            raya = ndimage.uniform_filter1d(ndimage.gaussian_filter1d(brillo, 0.6, axis=0), max(3, int(w4 * 0.35)), axis=1)
            raya = raya + ndimage.uniform_filter1d(brillo, max(3, int(w4 * 0.08)), axis=1)
            extra += p["raya"] * 2.2 * raya[..., None] * np.array([0.35, 0.6, 1.0], np.float32)
        if p["niebla"]:  # la lente empañada: lo claro se derrama, los negros suben
            glow = ndimage.gaussian_filter(chico, (0.03 * h4, 0.03 * h4, 0)) * 0.6 + ndimage.gaussian_filter(chico, (0.1 * h4, 0.1 * h4, 0)) * 0.4
            extra += p["niebla"] * 0.45 * glow
            lin = lin * (1 - 0.25 * min(1.0, p["niebla"]))
        if p["suciedad"]:
            extra = extra * geo["manchas"][:h4, :w4, None]
        lin = lin + _ampliar(extra, alto, ancho)
    return np.power(np.clip(lin, 0, 1), 1 / 2.2, dtype=np.float32)


APARATOS = {"lente": lente}
