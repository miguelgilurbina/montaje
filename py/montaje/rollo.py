"""El rollo: lo que le pasaba a la película dentro del proyector, como gestos (un aparato de imagen de la mesa analógica).

Miguel, el 2026-11-22, en el mapa de la galería: eligió «Gestos de la película». Son lo mismo que la pausa y el
rebobinado de la casetera, del lado de la película: momentos que van encima de cualquier base (`gesto: true`).

- **La película que se quema** (`quema`, eventos por minuto, de `quema_dura` segundos): el cuadro se traba en la
  ventanilla, la lámpara lo calienta, y se abre un agujero desde un punto: el borde se ampolla y se tuesta, el centro
  es la luz blanca de la lámpara, hasta que no queda imagen.
- **El cuadro que se corre** (`corrido`): el proyector pierde el lazo y la línea negra entre dos cuadros recorre la
  pantalla, una, dos o tres vueltas, hasta que alguien ajusta el encuadre.
- **El cambio de rollo** (`cambio`): las dos marcas en la esquina de arriba que le avisaban al proyeccionista, la del
  motor unos siete segundos antes de la del cambio, cuatro cuadros cada una (las de las copias de cine).
- **El empalme** (`empalme`): donde dos pedazos se pegaron con cinta: el cuadro salta, la cinta lechosa con sus
  burbujas y un destello.
- **La cola** (`cola`, segundos antes del final): el rollo que se acaba: la luz que vela la punta, la cola transparente
  con su mugre y, al final, la punta suelta que golpea.

Va después de la última `pelicula` de la cadena y antes del `proyector`: lo que se quema es la película, y la pared
lo muestra. Con `sonido: proyector`, cada gesto suena en su momento (`ruidos.py`). Los tiempos y los colores son
[sin verificar]: puntos de partida mirados en las hojas.
"""

from __future__ import annotations

import math

import numpy as np

from . import analogo as A
from .pelicula import _grano, evento_con_id

POR_DEFECTO = {
    "rollo": {"quema": 0.0, "quema_dura": 2.4, "corrido": 0.0, "corrido_dura": 1.5, "cambio": 0.0, "empalme": 0.0,
              "cola": 0.0, "sonido": "ninguno"},
}
RANGOS = {
    "rollo": {"quema": (0, 20), "quema_dura": (0.8, 4), "corrido": (0, 20), "corrido_dura": (0.4, 3), "cambio": (0, 6),
              "empalme": (0, 30), "cola": (0, 8), "sonido": ("ninguno", "proyector")},
}

#: El cambio de rollo: la marca del motor, siete segundos después la del cambio, y un segundo después el otro rollo.
CAMBIO_DURA = 8.2
MARCA_MOTOR, MARCA_CAMBIO = 0.0, 7.0
MARCA_SEGUNDOS = 4 / 24      # cada marca: cuatro cuadros de la copia, a 24 por segundo
EMPALME_DURA = 0.3
#: La línea entre dos cuadros, en fracción del alto del cuadro (en el Super 8, ≈ 0,4 mm de 4,2: [sin verificar]).
LINEA_ENTRE_CUADROS = 0.09
#: La luz blanca de la lámpara a través de la base transparente, y los colores de la película que se quema.
LAMPARA = np.array([1.0, 0.97, 0.88], np.float32)
BRASA = np.array([1.0, 0.52, 0.10], np.float32)
COSTRA = np.array([0.10, 0.045, 0.02], np.float32)
TOSTADO = np.array([0.78, 0.46, 0.16], np.float32)


def errores(nombre: str, a: dict) -> list[str]:
    return []


CONSEJO = {"rollo": "acorta `quema_dura`"}


def calentar(pasos: list[tuple[str, dict]], fps: float, solo: int | None = None) -> int:
    """La quema guarda el cuadro que se trabó: el pedazo tiene que haber visto el principio del evento."""
    n = 0
    for i, (nombre, p) in enumerate(pasos):
        if nombre == "rollo" and (solo is None or i == solo) and p["quema"]:
            n = max(n, int(math.ceil(p["quema_dura"] * fps)) + 2)
    return n


# ── Los gestos ─────────────────────────────────────────────────────────────

def _mezclar(a: np.ndarray, b: np.ndarray, m: np.ndarray) -> np.ndarray:
    return a * (1 - m[..., None]) + b * m[..., None]


def _campos_de_quema(ident: int, semilla: int, h: int, w: int, cache: dict) -> tuple[np.ndarray, np.ndarray]:
    """Lo que no cambia en una quema: la distancia de cada pixel al punto donde empieza (en fracción de la diagonal) y
    el ruido que hace irregular el borde. Se calcula una vez por evento."""
    if cache.get("id") != ident:
        r = np.random.default_rng([semilla, A._num("quema-lugar"), ident])
        cy, cx = r.uniform(0.3, 0.7) * h, r.uniform(0.3, 0.7) * w
        borde = 0.6 * _grano(r, h, w, max(4.0, h / 8)) + 0.4 * _grano(r, h, w, max(1.5, h / 60))
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        d = np.hypot(yy - cy, xx - cx) / math.hypot(h, w)
        cache.clear()
        cache.update(id=ident, d=d.astype(np.float32), borde=borde.astype(np.float32), centro=(cy, cx))
    return cache["d"], cache["borde"]


def _quema(img: np.ndarray, u: float, ident: int, semilla: int, rng: np.random.Generator, cache: dict) -> np.ndarray:
    """El cuadro trabado que se quema: primero se calienta un punto, después el agujero crece con su borde ampollado."""
    h, w = img.shape[:2]
    d, borde = _campos_de_quema(ident, semilla, h, w, cache)
    calor = min(1.0, u / 0.12)
    # La lámpara calienta: un punto que se aclara y se entibia antes de abrirse.
    mancha = np.exp(-(d / (0.05 + 0.08 * calor)) ** 2) * calor
    sale = _mezclar(img, np.minimum(1.0, img * 1.25 + 0.25), mancha)
    sale = sale * (1 - 0.12 * calor) + TOSTADO * 0.12 * calor   # todo el cuadro se entibia con el calor
    a = (u - 0.12) / 0.72
    if a <= 0:
        return sale
    r = 0.95 * min(a, 1.3) ** 1.8
    ancho_borde = 0.012
    # El borde es irregular pero continuo: una burbuja que se abre, no islas sueltas.
    frente = (d + 0.022 * borde * min(1.0, 4 * r) - r) / ancho_borde      # < 0: ya se quemó; el borde, entre −2 y 0,4
    # Lo que está por quemarse se ampolla: se mueve a borbotones y se tuesta, en un anillo ancho alrededor.
    cerca = np.clip(1 - (frente - 0.4) / 5.0, 0, 1) * (frente > -0.6)
    if cerca.any():
        hierve = rng.standard_normal((max(2, h // 24), max(2, w // 24))).astype(np.float32)
        from .pelicula import _ampliar

        dy = _ampliar(hierve, h, w) * 3.5 * (h / 540) * cerca
        dx = _ampliar(np.roll(hierve, 1, axis=0), h, w) * 3.5 * (h / 540) * cerca
        filas = np.clip((np.arange(h)[:, None] + dy).astype(np.int32), 0, h - 1)
        cols = np.clip((np.arange(w)[None, :] + dx).astype(np.int32), 0, w - 1)
        sale = _mezclar(sale, sale[filas, cols], cerca)
        sale = _mezclar(sale, sale * 0.45 + TOSTADO * 0.5, cerca * 0.85)
    titila = 0.94 + 0.06 * rng.random()
    costra = np.clip(1 - np.abs(frente + 0.1) / 0.5, 0, 1)
    brasa = np.clip(1 - np.abs(frente + 1.3) / 0.8, 0, 1)
    adentro = np.clip(-(frente + 1.6) / 0.6, 0, 1)
    sale = _mezclar(sale, np.broadcast_to(COSTRA, sale.shape), costra)
    sale = _mezclar(sale, np.broadcast_to(BRASA * titila, sale.shape), brasa)
    sale = _mezclar(sale, np.broadcast_to(LAMPARA * titila, sale.shape), adentro)
    if a > 1:  # ya no queda imagen: la luz, con las escamas que se van
        escamas = (rng.random((h, w)) < 0.004 * max(0.0, 1.6 - a)).astype(np.float32)
        sale = _mezclar(sale, np.broadcast_to(COSTRA, sale.shape), escamas)
    return sale


def _corrido(img: np.ndarray, u: float, ident: int, semilla: int, rng: np.random.Generator) -> np.ndarray:
    """La línea entre cuadros que recorre la pantalla: la ventanilla ve la tira corrida, con la línea negra donde se
    juntan dos cuadros y la perforación clara en ella. Frena al final, con el cuadro otra vez en su lugar."""
    from scipy import ndimage

    h, w = img.shape[:2]
    vueltas = int(np.random.default_rng([semilla, A._num("corrido-vueltas"), ident]).integers(1, 4))
    linea = max(2, int(round(LINEA_ENTRE_CUADROS * h)))
    periodo = h + linea
    avance = vueltas * (1 - (1 - u) ** 2)                # en cuadros; frena al final
    corre = int(round((avance % 1) * periodo))
    z = (np.arange(h) + corre) % periodo
    es_linea = z >= h
    sale = img[np.minimum(z, h - 1)]
    sale[es_linea] = 0.02
    if es_linea.any():  # la perforación del Super 8, en la línea, deja pasar la luz
        filas = np.nonzero(es_linea)[0]
        x0, x1 = int(0.025 * w), int(0.075 * w)
        alto_perf = max(1, int(len(filas) * 0.7))
        medio = filas[len(filas) // 2]
        a = max(0, medio - alto_perf // 2)
        sale[a:a + alto_perf, x0:x1] = 0.85
    velocidad = vueltas * 2 * (1 - u) * periodo / 30     # pixeles por cuadro de video, aproximado
    if velocidad > 1:
        sale = ndimage.gaussian_filter1d(sale, min(velocidad * 0.35, 18.0), axis=0, mode="wrap")
    return sale * (0.82 + 0.18 * rng.random())


def _marca(img: np.ndarray, semilla: int, ident: int) -> np.ndarray:
    """La marca de cambio de rollo: un círculo raspado en la emulsión, arriba a la derecha, con su borde oscuro."""
    h, w = img.shape[:2]
    cy, cx, radio = 0.13 * h, 0.87 * w, 0.042 * h
    r = np.random.default_rng([semilla, A._num("marca"), ident])
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ang = np.arctan2(yy - cy, xx - cx)
    irregular = radio * (1 + 0.08 * np.sin(3 * ang + r.uniform(0, 6.3)) + 0.05 * np.sin(7 * ang + r.uniform(0, 6.3)))
    dist = np.hypot(yy - cy, xx - cx) - irregular
    relleno = np.clip(0.5 - dist, 0, 1)
    anillo = np.clip(1 - np.abs(dist) / max(1.6, 0.006 * h), 0, 1)
    sale = _mezclar(img, np.full_like(img, 0.93), relleno)
    return _mezclar(sale, np.full_like(img, 0.05), anillo * 0.8)


def _empalme(img: np.ndarray, u: float, ident: int, semilla: int, rng: np.random.Generator) -> np.ndarray:
    """El empalme pasando por la ventanilla: el cuadro salta, la cinta lechosa con su borde y sus burbujas, y un
    destello en el primer cuadro."""
    h, w = img.shape[:2]
    r = np.random.default_rng([semilla, A._num("empalme"), ident])
    sale = img
    if u < 0.5:  # el cuadro salta en la ventanilla
        salto = int(r.uniform(0.03, 0.07) * h)
        sale = np.concatenate([np.zeros((salto, w, 3), np.float32), img[: h - salto]])
    if u < 0.67:
        y0 = int(r.uniform(0.05, 0.6) * h)
        y1 = min(h, y0 + int(r.uniform(0.22, 0.35) * h))
        cinta = sale[y0:y1] * 0.72 + 0.16
        burbujas = (rng.random(cinta.shape[:2]) < 0.0015).astype(np.float32)
        cinta = _mezclar(cinta, np.full_like(cinta, 0.95), burbujas)
        sale = sale.copy()
        sale[y0:y1] = cinta
        for y in (y0, y1 - 1):
            sale[max(0, y - 1):y + 1] *= 0.35
    if u < 0.25:
        sale = np.minimum(1.0, sale * 1.35 + 0.08)
    return sale


def _cola(img: np.ndarray, v: float, semilla: int, k: int, rng: np.random.Generator) -> np.ndarray:
    """El rollo que se acaba (v de 0 a 1): la punta velada entra por un borde, después la cola transparente pasa con
    su mugre, y al final la punta suelta golpea: la pantalla titila entre la luz y lo oscuro."""
    h, w = img.shape[:2]
    if v < 0.35:  # la punta velada: luz naranja que entra desde la derecha
        a = v / 0.35
        xx = np.linspace(0, 1, w, dtype=np.float32)[None, :]
        vela = np.clip((xx - (1 - 1.3 * a)) / 0.35, 0, 1) ** 1.5
        vela = np.broadcast_to(vela, (h, w))
        luz = np.minimum(1.0, img * 0.6 + BRASA * 0.9 + 0.1)
        return _mezclar(img, luz, vela * (0.6 + 0.4 * a))
    sale = np.broadcast_to(LAMPARA, (h, w, 3)).copy()
    titila = 0.85 + 0.15 * rng.random()
    if v < 0.8:  # la cola transparente con su mugre: motas y pelos oscuros, nuevos en cada cuadro
        a = (v - 0.35) / 0.45
        mezcla = max(0.0, 1 - a / 0.15)          # la imagen se va en el primer pedazo
        sale = _mezclar(sale, img, np.full((h, w), 0.35 * mezcla, np.float32))
        from scipy import ndimage

        motas = (rng.random((h, w)) < 0.0012).astype(np.float32)
        motas = np.clip(ndimage.gaussian_filter(motas, max(0.6, h / 600)) * 6, 0, 1)
        if rng.random() < 0.3:   # a veces un pelo: una curva fina que cruza el cuadro
            yy = np.linspace(rng.uniform(0, h), rng.uniform(0, h), w) + 12 * np.sin(np.linspace(0, rng.uniform(2, 6), w))
            filas = np.clip(yy.astype(np.int32), 0, h - 1)
            motas[filas, np.arange(w)] = np.maximum(motas[filas, np.arange(w)], 0.8 * (rng.random(w) < 0.6))
        sale = _mezclar(sale, np.full_like(sale, 0.08), motas)
        return sale * titila
    # La punta suelta: lo oscuro y la luz a golpes, cada vez más lentos.
    a = (v - 0.8) / 0.2
    golpes = 12 - 7 * a
    fase = (k * golpes / 30.0) % 1
    return sale * (0.15 if fase < 0.35 else titila)


def rollo(img: np.ndarray, p: dict, ctx) -> np.ndarray:
    """El aparato: la imagen (RGB 0–1, al tamaño de salida) con el gesto que le toque en este cuadro."""
    semilla = ctx.semilla * 100 + ctx.paso
    t, k = ctx.t, ctx.k
    est = ctx.estado.setdefault(("rollo", ctx.paso), {"trabado": None, "quema": {}})
    rng = ctx.rng("rollo")
    sale = img
    quema = evento_con_id(semilla, "quema", t, p["quema"], p["quema_dura"]) if p["quema"] else None
    corrido = evento_con_id(semilla, "corrido", t, p["corrido"], p["corrido_dura"]) if p["corrido"] and quema is None else None
    empalme = (evento_con_id(semilla, "empalme", t, p["empalme"], EMPALME_DURA)
               if p["empalme"] and quema is None and corrido is None else None)
    if quema is not None:
        u, ident = quema
        if est["trabado"] is None or est["trabado"][0] != ident:   # el primer cuadro de la quema: ése se traba
            est["trabado"] = (ident, img.copy())
        sale = _quema(est["trabado"][1], u, ident, semilla, rng, est["quema"])
    else:
        est["trabado"] = None
    if corrido is not None:
        sale = _corrido(sale, corrido[0], corrido[1], semilla, rng)
    if empalme is not None:
        sale = _empalme(sale, empalme[0], empalme[1], semilla, rng)
    if p["cambio"]:
        c = evento_con_id(semilla, "cambio", t, p["cambio"], CAMBIO_DURA)
        if c is not None:
            dentro = c[0] * CAMBIO_DURA
            if any(m <= dentro < m + MARCA_SEGUNDOS for m in (MARCA_MOTOR, MARCA_CAMBIO)):
                sale = _marca(sale, semilla, c[1])
    fin = getattr(ctx, "fin", None)
    if p["cola"] and fin is not None and fin - p["cola"] <= t < fin:
        sale = _cola(sale, (t - (fin - p["cola"])) / p["cola"], semilla, k, rng)
    return np.clip(sale, 0, 1).astype(np.float32)


APARATOS = {"rollo": rollo}
