"""La casetera: lo que el VCR le hacía a la imagen al reproducir la cinta (un aparato de señal de la mesa analógica).

Miguel, el 2026-11-21: «acumulemos más efectos». La cinta (`cinta` en `analogo.py`) es lo que quedó grabado; esto
es lo que hacía la casetera con los botones:

- **Pausa** (`pausa`, eventos por minuto, de `pausa_dura` segundos): la imagen queda quieta, pero de un solo campo
  (la mitad de las líneas, repetidas: los bordes en serrucho), temblando una línea arriba y abajo, con la barra de
  ruido donde los cabezales cruzan entre pistas.
- **Rebobinar** (`rebobinar`): la imagen corre hacia atrás, rápido, entre barras de ruido que suben despacio, con
  el color que se pierde y las líneas corridas.
- **El arranque** (`inicio`, segundos): la pantalla azul de la casetera sin señal; al apretar PLAY, el letrero y la
  imagen que entra con el ruido del tracking.
- **El entrelazado** (`entrelazado`): cada cuadro de video eran dos campos de instantes distintos; lo que se
  mueve se peina (las líneas impares son del cuadro anterior).

Con `letreros`, los de la casetera (‖, ◀◀, ▶ PLAY), en inglés como en las de la época. Las barras de la pausa y del
avance no se encontraron medidas en una fuente: son puntos de partida (ver `direccion/ANALOGO.md`).
"""

from __future__ import annotations

import math

import numpy as np

from . import analogo as A
from .pelicula import evento_con_id

#: El azul de la casetera sin señal: cada marca tenía el suyo [sin verificar]; éste, el que se recuerda.
AZUL = "#2340c8"
VELOCIDAD_REBOBINAR = 3

POR_DEFECTO = {
    "casetera": {"entrelazado": 0.0, "pausa": 0.0, "pausa_dura": 1.6, "rebobinar": 0.0, "rebobinar_dura": 1.2,
                 "inicio": 0.0, "letreros": True},
}
RANGOS = {
    "casetera": {"entrelazado": (0, 1), "pausa": (0, 20), "pausa_dura": (0.3, 3), "rebobinar": (0, 20),
                 "rebobinar_dura": (0.3, 1.8), "inicio": (0, 10)},
}


def errores(nombre: str, a: dict) -> list[str]:
    if "letreros" in a and not isinstance(a["letreros"], bool):
        return ["casetera.letreros: true o false"]
    return []


def calentar(pasos: list[tuple[str, dict]], fps: float) -> int:
    """La pausa guarda el cuadro donde empezó; el rebobinado, los cuadros de antes que va a mostrar."""
    n = 0
    for nombre, p in pasos:
        if nombre != "casetera":
            continue
        if p["entrelazado"]:
            n = max(n, 2)
        if p["pausa"]:
            n = max(n, int(math.ceil(p["pausa_dura"] * fps)) + 2)
        if p["rebobinar"]:
            n = max(n, int(math.ceil(p["rebobinar_dura"] * fps * (1 + VELOCIDAD_REBOBINAR))) + 2)
    return n


def _guardar(y, i, q):
    """Un cuadro para el rebobinado, liviano: la luma a la mitad de muestras y el color a un cuarto, en 8 bits."""
    return (np.clip(y[:, ::2] * 220 + 16, 0, 255).astype(np.uint8),
            np.clip(i[::2, ::4] * 200 + 128, 0, 255).astype(np.uint8),
            np.clip(q[::2, ::4] * 200 + 128, 0, 255).astype(np.uint8))


def _recuperar(g):
    y = (np.repeat(g[0].astype(np.float32), 2, axis=1)[:, :A.MUESTRAS] - 16) / 220
    i = (np.repeat(np.repeat(g[1].astype(np.float32), 2, axis=0), 4, axis=1)[:A.LINEAS, :A.MUESTRAS] - 128) / 200
    q = (np.repeat(np.repeat(g[2].astype(np.float32), 2, axis=0), 4, axis=1)[:A.LINEAS, :A.MUESTRAS] - 128) / 200
    return y, i, q


def _barra(y, i, q, centro: float, alto: float, rng: np.random.Generator) -> None:
    """La barra de ruido donde los cabezales leen entre dos pistas: líneas corridas, nieve y rayas claras."""
    a = int(max(0, centro - alto / 2))
    b = int(min(A.LINEAS, centro + alto / 2))
    if b <= a:
        return
    filas = np.arange(a, b)
    borde = np.minimum(filas - a + 1, b - filas) / max(1.0, alto * 0.25)
    fuerza = np.clip(borde, 0, 1)[:, None].astype(np.float32)
    corridas = np.stack([np.roll(y[f], int(rng.integers(-60, 60))) for f in filas])
    nieve = rng.standard_normal((b - a, A.MUESTRAS), dtype=np.float32) * 0.22
    rayas = (rng.random((b - a, A.MUESTRAS)) < 0.015).astype(np.float32)
    rayas = np.maximum(rayas, np.roll(rayas, 1, axis=1)) * 0.6
    y[a:b] = y[a:b] * (1 - fuerza) + fuerza * (0.55 * corridas + nieve + rayas + 0.05)
    i[a:b] = i[a:b] * (1 - fuerza) + fuerza * rng.standard_normal((b - a, A.MUESTRAS), dtype=np.float32) * 0.05
    q[a:b] = q[a:b] * (1 - fuerza) + fuerza * rng.standard_normal((b - a, A.MUESTRAS), dtype=np.float32) * 0.05


def _letrero(s: A.Senal, texto: str, ctx) -> None:
    sale = A.osd(s, {"textos": [{"texto": texto, "lugar": "arriba-izquierda"}], "fecha": "1994-10-12", "hora": "00:00:00"}, ctx)
    s.y, s.i, s.q = sale.y, sale.i, sale.q


def casetera(s: A.Senal, p: dict, ctx) -> A.Senal:
    s.componentes()
    y, i, q = s.y.copy(), s.i.copy(), s.q.copy()
    semilla = ctx.semilla * 100 + ctx.paso
    t, k, fps = ctx.t, ctx.k, ctx.fps
    est = ctx.estado.setdefault(("casetera", ctx.paso), {"guardados": {}, "antes": None, "pausa": None})
    rng = ctx.rng("casetera")
    texto = None
    # Lo que tiene memoria se guarda siempre, haya evento o no: los pedazos en paralelo no dejan costura.
    if p["rebobinar"]:
        est["guardados"][k] = _guardar(y, i, q)
        limite = k - int(math.ceil(p["rebobinar_dura"] * fps * (1 + VELOCIDAD_REBOBINAR))) - 2
        for viejo in [c for c in est["guardados"] if c < limite]:
            del est["guardados"][viejo]
    if p["entrelazado"]:  # el campo impar es del cuadro anterior: lo que se mueve se peina
        antes, est["antes"] = est["antes"], (y.copy(), i.copy(), q.copy())
        if antes is not None:
            e = p["entrelazado"]
            for actual, previo in zip((y, i, q), antes):
                actual[1::2] = (1 - e) * actual[1::2] + e * previo[1::2]
    pausa = evento_con_id(semilla, "pausa", t, p["pausa"], p["pausa_dura"]) if p["pausa"] else None
    rebobina = evento_con_id(semilla, "rebobinar", t, p["rebobinar"], p["rebobinar_dura"]) if p["rebobinar"] and pausa is None else None
    if pausa is not None:
        _, ident = pausa
        if est["pausa"] is None or est["pausa"][0] != ident:   # el primer cuadro de la pausa: ése queda
            est["pausa"] = (ident, (y.copy(), i.copy(), q.copy()))
        y, i, q = (a.copy() for a in est["pausa"][1])
        for a in (y, i, q):  # un solo campo, repetido: los bordes en serrucho
            a[1::2] = a[0::2]
        if k % 2:  # tiembla una línea
            y, i, q = (np.vstack([a[:1], a[:-1]]) for a in (y, i, q))
        r = np.random.default_rng([semilla, A._num("barra"), ident])
        centro = r.uniform(0.6, 0.9) * A.LINEAS + rng.uniform(-2, 2)
        _barra(y, i, q, centro, r.uniform(14, 26), rng)
        texto = "‖"
    else:
        est["pausa"] = None
    if rebobina is not None:
        u, _ = rebobina
        inicio = k - int(round(u * p["rebobinar_dura"] * fps))
        fuente = inicio - VELOCIDAD_REBOBINAR * (k - inicio)
        disponibles = [c for c in est["guardados"] if c <= fuente] or [min(est["guardados"])]
        y, i, q = _recuperar(est["guardados"][max(disponibles)])
        # Las líneas corridas, el color que va y viene, y dos barras de ruido que suben despacio.
        corr = (rng.standard_normal(A.LINEAS) * 2.5 + 6 * np.sin(np.arange(A.LINEAS) / 37 + 9 * t)).astype(np.int32)
        filas = np.arange(A.LINEAS)[:, None]
        cols = np.clip(np.arange(A.MUESTRAS)[None, :] - corr[:, None], 0, A.MUESTRAS - 1)
        y, i, q = y[filas, cols], i[filas, cols] * 0.45, q[filas, cols] * 0.45
        for n in range(2):
            centro = ((n / 2 + 0.11 * VELOCIDAD_REBOBINAR * t) % 1) * (A.LINEAS + 40) - 20
            _barra(y, i, q, centro, 24, rng)
        texto = "◀◀"
    if p["inicio"]:
        if t < p["inicio"]:  # la pantalla azul de la casetera sin señal
            azul = A.color_yiq(AZUL)
            y, i, q = (np.full((A.LINEAS, A.MUESTRAS), v, np.float32) for v in azul)
        elif t < p["inicio"] + 0.6:  # la imagen entra con el ruido del tracking, de abajo arriba
            u = (t - p["inicio"]) / 0.6
            _barra(y, i, q, (1 - u) * A.LINEAS, 40 * (1 - u) + 10, rng)
        if p["inicio"] - 1.2 <= t < p["inicio"] + 2.5:
            texto = "▶ PLAY"
    s.y, s.i, s.q = y.astype(np.float32), i.astype(np.float32), q.astype(np.float32)
    if texto and p["letreros"]:
        _letrero(s, texto, ctx)
    return s


SENAL = {"casetera": casetera}
