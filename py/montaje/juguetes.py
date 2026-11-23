"""Antes del cine: los juguetes ópticos que movían imágenes antes de la película (un aparato de imagen de la mesa
analógica).

Miguel, el 2026-11-23: «Tu busca más por favor»; de lo que se encontró buscando eligió abrir «Antes del cine».

`juguete` (perilla `modo`):

- **zootropo**: el tambor que gira con la tira de figuras adentro, mirado por las ranuras: un loop corto (`cuadros`
  figuras a 12 por segundo), oscuro y cortado en franjas que pasan, sobre la curva del tambor.
- **fenaquistiscopio**: el disco con sus figuras en círculo (`cuadros`), cada una un instante del loop; mirado por las
  ranuras del borde, cada figura se mueve en su lugar.
- **libro**: el libro animado: cada hoja una figura, que pasa con el pulgar doblándose desde la esquina.
- **lenticular**: la postal de dos imágenes que se cambian al inclinarla: lo de ahora y lo de hace `separacion`
  segundos, con las rayas de su lente y el brillo del plástico.
- **cronofotografia**: varias exposiciones en una sola placa, como las de Marey: cada `intervalo` segundos una pose
  más de lo que se mueve (lo claro sobre lo oscuro), las últimas `poses` encimadas.

El loop del zoótropo, del disco y del libro se llena cada `ciclo` segundos: el primer segundo se ve en vivo y después
se repite (como la tira que se cambia). Con `sonido: mecanismo`, el juguete suena (`ruidos.py`). Las proporciones y
las velocidades son [sin verificar]: las de las descripciones y mirados en las hojas.
"""

from __future__ import annotations

import math

import numpy as np

from . import analogo as A
from .pelicula import _a_tamano, _desenfocar

MODOS = ("zootropo", "fenaquistiscopio", "libro", "lenticular", "cronofotografia")
FIGURAS_POR_SEGUNDO = 12
POR_DEFECTO = {
    "juguete": {"modo": "zootropo", "cuadros": 12, "ciclo": 4.0, "separacion": 2.0, "intervalo": 0.12, "poses": 10,
                "sonido": "ninguno"},
}
RANGOS = {
    "juguete": {"modo": MODOS, "cuadros": (4, 24), "ciclo": (2, 7), "separacion": (0.5, 6), "intervalo": (0.04, 0.4),
                "poses": (2, 16), "sonido": ("ninguno", "mecanismo")},
}
LUMA = np.array([0.299, 0.587, 0.114], np.float32)
PAPEL = np.array([0.93, 0.89, 0.80], np.float32)
FONDO = np.array([0.05, 0.045, 0.04], np.float32)


def errores(nombre: str, a: dict) -> list[str]:
    return []


CONSEJO = {"juguete": "acorta el `ciclo`, la `separacion` o las `poses` por el `intervalo`"}


def calentar(pasos: list[tuple[str, dict]], fps: float, solo: int | None = None) -> int:
    n = 0
    for i, (nombre, p) in enumerate(pasos):
        if nombre != "juguete" or (solo is not None and i != solo):
            continue
        if p["modo"] in ("zootropo", "fenaquistiscopio", "libro"):
            n = max(n, int(math.ceil(p["ciclo"] * fps)) + 2)
        elif p["modo"] == "lenticular":
            n = max(n, int(math.ceil(p["separacion"] * fps)) + 2)
        else:
            n = max(n, int(math.ceil(p["poses"] * p["intervalo"] * fps)) + 2)
    return n


def _mezclar(a, b, m):
    return a * (1 - m[..., None]) + np.asarray(b, np.float32) * m[..., None]


# ── El loop: las figuras de la tira ───────────────────────────────────────

def _loop(img: np.ndarray, p: dict, ctx, alto: int, ancho: int) -> tuple[np.ndarray, int]:
    """La figura del loop que toca ahora, y su número. La tira se llena en el primer segundo del ciclo."""
    est = ctx.estado.setdefault(("juguete-loop", ctx.paso), {})
    ciclo = math.floor(ctx.t / p["ciclo"])
    dentro = ctx.t - ciclo * p["ciclo"]
    j = math.floor(dentro * FIGURAS_POR_SEGUNDO)
    if j < p["cuadros"] and (ciclo, j) not in est:   # la figura j del ciclo: el primer cuadro que cae en ella
        est[(ciclo, j)] = _a_tamano(img, alto, ancho)
        for viejo in [k for k in est if k[0] < ciclo - 1]:
            del est[viejo]
    hay = [k[1] for k in est if k[0] == ciclo]
    if not hay:   # sin nada guardado de este ciclo (no debería pasar si se calentó): la figura en vivo
        return _a_tamano(img, alto, ancho), j
    n = j % p["cuadros"] if j >= p["cuadros"] else j
    n = n if n in hay else max(hay)
    return est[(ciclo, n)], n


def _zootropo(img, p, ctx):
    alto, ancho = ctx.alto, ctx.ancho
    fh = int(0.62 * alto)
    figura, _ = _loop(img, p, ctx, fh, int(fh * 1.25))
    # La curva del tambor: la figura se comprime hacia los bordes.
    fw = figura.shape[1]
    xs = np.linspace(-1, 1, ancho)
    fuente = ((np.arcsin(np.clip(xs * 0.92, -1, 1)) / (math.pi / 2) + 1) / 2 * (fw - 1)).astype(np.int32)
    tira = figura[:, fuente]
    sombra = (0.35 + 0.65 * np.cos(xs * math.pi / 2 * 0.92) ** 0.8).astype(np.float32)
    sale = np.broadcast_to(FONDO, (alto, ancho, 3)).copy()
    y0 = (alto - fh) // 2
    sale[y0:y0 + fh] = tira * sombra[None, :, None]
    # Las ranuras que pasan: franjas abiertas que corren de lado; entre ellas, la pared del tambor.
    periodo = ancho / 5.0
    corre = (ctx.t * 2.6 * ancho) % periodo
    abierta = ((np.arange(ancho) + corre) % periodo) / periodo
    luz = np.clip(1 - np.abs(abierta - 0.5) / 0.22, 0, 1) ** 0.6
    sale = sale * (0.12 + 0.88 * luz[None, :, None])
    pared = np.zeros(alto, np.float32)
    pared[:y0] = 1
    pared[y0 + fh:] = 1
    madera = np.array([0.22, 0.13, 0.07], np.float32) * (0.6 + 0.4 * luz[None, :])[..., None]
    sale = np.where(pared[:, None, None] > 0, madera, sale)
    titila = 0.88 + 0.12 * ctx.rng("zootropo").random()
    return sale * titila


def _fenaquistiscopio(img, p, ctx):
    alto, ancho = ctx.alto, ctx.ancho
    n = int(p["cuadros"])
    est = ctx.estado.setdefault(("juguete-disco", ctx.paso), {})
    lado = int(alto * 0.4)
    figura, j = _loop(img, p, ctx, lado, lado)
    est.setdefault("figuras", {})[j] = figura
    figuras = est["figuras"]
    clave = (alto, ancho, n)
    if est.get("geo") is None or est["geo"][0] != clave:
        yy, xx = np.mgrid[0:alto, 0:ancho].astype(np.float32)
        dy, dx = yy - alto / 2, xx - ancho / 2
        r = np.hypot(dy, dx) / (0.47 * alto)
        th = (np.arctan2(dy, dx) + 2 * math.pi) % (2 * math.pi)
        sector = np.floor(th / (2 * math.pi / n)).astype(np.int32)
        u = (th / (2 * math.pi / n)) % 1.0
        v = np.clip((r - 0.34) / (0.92 - 0.34), 0, 1)
        est["geo"] = (clave, r, sector, u, v)
    _, r, sector, u, v = est["geo"]
    sale = np.broadcast_to(FONDO, (alto, ancho, 3)).copy()
    disco = r <= 1.0
    sale[disco] = PAPEL * 0.92
    figura_zona = (r >= 0.34) & (r <= 0.92)
    # Cada sector muestra la figura que le toca en este paso del loop (girado un sector por figura: se mueven en su
    # lugar, como se ve por las ranuras).
    for s in range(n):
        k = (s + j) % n
        f = figuras.get(k)
        if f is None:
            continue
        m = figura_zona & (sector == s)
        fx = np.clip((u[m] * 0.8 + 0.1) * (lado - 1), 0, lado - 1).astype(np.int32)
        fy = np.clip((1 - v[m]) * (lado - 1), 0, lado - 1).astype(np.int32)
        sale[m] = f[fy, fx] * 0.95
    # Las ranuras del borde y el eje.
    ranura = (r > 0.94) & (r < 1.0) & (np.abs((u - 0.5)) < 0.08)
    sale[ranura] = FONDO
    sale[r < 0.05] = np.array([0.4, 0.33, 0.25], np.float32)
    return sale * (0.85 + 0.15 * ctx.rng("disco").random())


def _libro(img, p, ctx):
    alto, ancho = ctx.alto, ctx.ancho
    ph, pw = int(0.78 * alto), int(0.78 * alto * 1.3)
    figura, j = _loop(img, p, ctx, int(ph * 0.84), int(pw * 0.86))
    pagina = np.broadcast_to(PAPEL, (ph, pw, 3)).copy()
    y0, x0 = int(ph * 0.08), int(pw * 0.07)
    pagina[y0:y0 + figura.shape[0], x0:x0 + figura.shape[1]] = figura
    # La hoja que pasa: en el primer 40 % de cada figura, el doblez corre de derecha a izquierda.
    fase = (ctx.t * FIGURAS_POR_SEGUNDO) % 1.0
    if fase < 0.4:
        borde = int((1 - fase / 0.4) * pw)
        xs = np.arange(pw)
        cerca = np.clip(1 - np.abs(xs - borde) / (0.08 * pw), 0, 1)
        pagina *= (1 - 0.45 * cerca)[None, :, None]
        pagina[:, borde:] = pagina[:, borde:] * 0.92 + PAPEL * 0.08
    sale = np.broadcast_to(FONDO * 2, (alto, ancho, 3)).copy()
    oy, ox = (alto - ph) // 2, (ancho - pw) // 2
    for k in range(6, 0, -1):   # el canto de las hojas de abajo
        sale[oy + k * 3:oy + ph + k * 3, ox + k * 2:ox + pw + k * 2] = PAPEL * (0.7 - 0.05 * k)
    sale[oy:oy + ph, ox:ox + pw] = pagina
    return sale


def _lenticular(img, p, ctx):
    alto, ancho = ctx.alto, ctx.ancho
    est = ctx.estado.setdefault(("juguete-lente", ctx.paso), {})
    k = ctx.k
    est[k] = img
    atras = k - int(round(p["separacion"] * ctx.fps))
    for viejo in [c for c in est if c < atras]:
        del est[viejo]
    b = est.get(atras, est[min(est)])
    # La postal se inclina sola, de un lado al otro, con la mano que no es exacta.
    incl = 0.5 + 0.5 * math.sin(2 * math.pi * ctx.t / 3.2) + 0.15 * ctx.suave("lente-mano", 0.4)
    m = np.clip((incl - 0.42) / 0.16, 0, 1)
    xs = np.arange(ancho, dtype=np.float32)
    periodo = max(3.0, 6 * alto / 1080)
    fase = (xs / periodo) % 1.0
    # En la transición, cada raya muestra un poco de cada imagen: el fantasma de la lenticular.
    cual = np.clip((fase - (1 - m)) * 4 + 0.5, 0, 1) if 0 < m < 1 else np.full(ancho, m, np.float32)
    sale = img * (1 - cual[None, :, None]) + b * cual[None, :, None]
    lente = 0.93 + 0.07 * np.cos(2 * math.pi * fase)                  # la curva de cada lente
    brillo = np.exp(-((xs / ancho - incl) / 0.08) ** 2) * 0.18       # el reflejo del plástico, que corre al inclinar
    return np.clip(sale * lente[None, :, None] + brillo[None, :, None], 0, 1)


def _cronofotografia(img, p, ctx):
    alto, ancho = ctx.alto, ctx.ancho
    est = ctx.estado.setdefault(("juguete-placa", ctx.paso), {})
    j = math.floor(ctx.t / p["intervalo"])
    if j not in est:
        lum = img @ LUMA
        est[j] = np.clip((lum - 0.38) * 2.0, 0, 1).astype(np.float32)   # sólo lo claro deja marca (el fondo negro)
        for viejo in [c for c in est if c <= j - p["poses"]]:
            del est[viejo]
    placa = np.zeros((alto, ancho), np.float32)
    for c, pose in est.items():
        edad = j - c
        placa = np.maximum(placa, pose * (1 - 0.06 * edad))
    placa = _desenfocar(placa[..., None], max(0.6, alto / 900))[..., 0]
    sale = np.stack([placa * 0.92, placa * 0.95, placa], -1) + np.array([0.03, 0.035, 0.045], np.float32)
    yy, xx = np.mgrid[0:alto, 0:ancho].astype(np.float32)
    borde = np.minimum(np.minimum(yy, alto - yy), np.minimum(xx, ancho - xx)) / alto
    return sale * np.clip(borde / 0.03, 0.3, 1)[..., None]


def juguete(img: np.ndarray, p: dict, ctx) -> np.ndarray:
    modo = p["modo"]
    sale = {"zootropo": _zootropo, "fenaquistiscopio": _fenaquistiscopio, "libro": _libro, "lenticular": _lenticular,
            "cronofotografia": _cronofotografia}[modo](img, p, ctx)
    return np.clip(sale, 0, 1).astype(np.float32)


APARATOS = {"juguete": juguete}
