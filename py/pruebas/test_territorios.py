"""Pruebas de los cuatro territorios del mapa de la galería (2026-11-22): los gestos de la película (`rollo.py`), la
fotografía de antes (`fotografia.py`), la imprenta (`imprenta.py`) y la radio (`radio.py`), con sus ruidos.

    python -m pytest py/pruebas -q
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from montaje import analogo as A  # noqa: E402
from montaje import fotografia as F  # noqa: E402
from montaje import imprenta as I  # noqa: E402
from montaje import radio as RA  # noqa: E402
from montaje import rollo as RO  # noqa: E402
from montaje import ruidos as R  # noqa: E402
from montaje.pelicula import evento_con_id  # noqa: E402

SR = 48000


def imagen(alto: int = 90, ancho: int = 120, semilla: int = 1) -> np.ndarray:
    r = np.random.default_rng(semilla)
    yy, xx = np.mgrid[0:alto, 0:ancho].astype(np.float32)
    base = np.stack([xx / ancho, yy / alto, 0.5 + 0.5 * np.sin(xx / 9)], -1)
    return np.clip(base * 0.8 + 0.1 * r.random((alto, ancho, 3)), 0, 1).astype(np.float32)


def contexto(alto: int = 90, ancho: int = 120, t: float = 0.0, fps: float = 24.0) -> A.Contexto:
    c = A.Contexto(1, fps, alto, ancho)
    c.t, c.k = t, int(round(t * fps))
    return c


def cancion(segundos: float = 8.0) -> np.ndarray:
    t = np.arange(int(segundos * SR)) / SR
    m = (0.25 * np.sin(2 * np.pi * 220 * t) + 0.1 * np.random.default_rng(1).standard_normal(len(t))).astype(np.float32)
    return np.stack([m, m], axis=1)


def db(y: np.ndarray) -> float:
    return 20 * np.log10(np.sqrt(np.mean(np.square(y))) + 1e-12)


# ── Los gestos de la película ──────────────────────────────────────────────

def test_el_rollo_va_despues_de_la_pelicula_y_antes_del_proyector():
    base = [{"aparato": "pelicula"}, {"aparato": "proyector"}]
    cadena = A.componer(base, [{"aparato": "rollo", "quema": 2.0}])
    assert [a["aparato"] for a in cadena] == ["pelicula", "rollo", "proyector"]
    # Sin película, va donde iría la consola: antes de la cinta.
    cadena = A.componer([{"aparato": "cinta"}, {"aparato": "pantalla"}], [{"aparato": "rollo", "empalme": 4.0}])
    assert [a["aparato"] for a in cadena] == ["rollo", "cinta", "pantalla"]


def test_sin_gestos_el_rollo_no_toca_la_imagen():
    img = imagen()
    assert np.allclose(RO.rollo(img, RO.POR_DEFECTO["rollo"], contexto(t=3.0)), img, atol=1e-6)


def test_la_quema_traba_el_cuadro_y_termina_en_la_luz():
    p = {**RO.POR_DEFECTO["rollo"], "quema": 20.0}
    ctx = contexto()
    semilla = ctx.semilla * 100
    t = next(t for t in np.arange(0, 30, 1 / 24) if (e := evento_con_id(semilla, "quema", t, 20.0, p["quema_dura"])) and e[0] < 0.02)
    primero = imagen(semilla=1)
    ctx.t, ctx.k = t, int(round(t * 24))
    RO.rollo(primero, p, ctx)
    # Medio segundo después, con otra imagen entrando: lo que se ve sale del cuadro trabado, no del nuevo.
    ctx.t, ctx.k = t + 0.06, ctx.k + 1
    otra = imagen(semilla=2)[::-1]
    sale = RO.rollo(otra, p, ctx)
    assert np.abs(sale - primero).mean() < np.abs(sale - otra).mean()
    # Al final de la quema no queda imagen: la luz de la lámpara.
    final = RO._quema(primero, 0.97, 5, semilla, np.random.default_rng(0), {})
    assert np.abs(final - RO.LAMPARA).mean() < 0.08


def test_la_cola_sale_del_final_del_video():
    p = {**RO.POR_DEFECTO["rollo"], "cola": 3.0}
    img = imagen()
    ctx = contexto(t=5.0)
    assert np.allclose(RO.rollo(img, p, ctx), img, atol=1e-6)          # sin saber dónde termina, no hay cola
    ctx.fin = 10.0
    assert np.allclose(RO.rollo(img, p, ctx), img, atol=1e-6)          # lejos del final, tampoco
    ctx.t, ctx.k = 8.6, 206
    assert np.abs(RO.rollo(img, p, ctx) - img).mean() > 0.2            # en la cola, la luz y la mugre


def test_el_empalme_suena_donde_salta():
    x = cancion(30)
    p = {**RO.POR_DEFECTO["rollo"], "empalme": 6.0, "sonido": "proyector", "_paso": 1}
    y = R.rollo(x, p, 19, 0.0, SR, 0)                                 # la semilla de la muestra de «el-empalme»
    empalmes = R.eventos_en(1901, "empalme", 0.0, 30.0, 6.0, RO.EMPALME_DURA)
    assert empalmes
    for a, _ in empalmes:
        i = int(a * SR)
        assert np.abs(y[i:i + int(0.02 * SR)] - x[i:i + int(0.02 * SR)]).max() > 0.05


# ── La fotografía de antes ─────────────────────────────────────────────────

def test_cada_proceso_da_una_imagen_del_tamano_de_la_salida():
    img = imagen()
    for proceso in F.PROCESOS:
        sale = F.placa(img, {**F.POR_DEFECTO["placa"], "proceso": proceso}, contexto(t=1.0))
        assert sale.shape == img.shape and sale.dtype == np.float32 and 0 <= sale.min() and sale.max() <= 1
    for forma in F.FORMAS:
        sale = F.copia(img, {**F.POR_DEFECTO["copia"], "forma": forma}, contexto(t=1.0))
        assert sale.shape == img.shape


def test_el_cianotipo_es_azul():
    sale = F.placa(imagen(), {**F.POR_DEFECTO["placa"], "proceso": "cianotipo", "bordes": 0.0}, contexto())
    r, g, b = sale.reshape(-1, 3).mean(0)
    assert b > r + 0.1


def test_la_instantanea_aparece_de_a_poco():
    img = imagen()
    p = {**F.POR_DEFECTO["copia"], "forma": "instantanea", "revelado": 4.0}
    al_principio = F.copia(img, p, contexto(t=0.1))
    revelada = F.copia(img, p, contexto(t=5.0))
    centro = (slice(30, 60), slice(45, 75))
    assert al_principio[centro].std() < 0.5 * revelada[centro].std()


def test_el_fotomaton_dispara_cuando_suena():
    assert [round(t, 6) for t in F.disparos(1.6, 0.0, 8.0)] == [0.8, 2.4, 4.0, 5.6]
    x = cancion(9)
    y = R.copia(x, {**F.POR_DEFECTO["copia"], "forma": "fotomaton", "intervalo": 1.6, "sonido": "camara"}, 1, 0.0, SR, 0)
    for t in F.disparos(1.6, 0.0, 9.0):
        i = int(t * SR)
        assert np.abs(y[i:i + int(0.01 * SR)] - x[i:i + int(0.01 * SR)]).max() > 0.05


# ── La imprenta ────────────────────────────────────────────────────────────

def test_una_impresion_dura_lo_que_dicen_sus_cuadros():
    p = {**I.POR_DEFECTO["imprenta"], "tecnica": "serigrafia", "cuadros": 8}
    ctx = contexto(t=1.0)
    a = I.imprenta(imagen(semilla=1), p, ctx)
    ctx.t, ctx.k = 1.04, 25                                           # el mismo octavo de segundo
    assert np.array_equal(I.imprenta(imagen(semilla=2), p, ctx), a)
    ctx.t, ctx.k = 1.2, 29                                            # la impresión siguiente
    assert not np.array_equal(I.imprenta(imagen(semilla=2), p, ctx), a)


def test_los_puntos_cubren_lo_que_dice_el_tono():
    for tono in (0.1, 0.3, 0.6):
        cubre = I._puntos(np.full((240, 320), tono, np.float32), 8.0, 15.0)
        assert abs(cubre.mean() - tono) < 0.04


def test_la_fotocopia_es_blanco_y_negro():
    sale = I.imprenta(imagen(), {**I.POR_DEFECTO["imprenta"], "tecnica": "fotocopia"}, contexto())
    assert np.abs(sale - sale.mean(-1, keepdims=True)).max() < 0.03


# ── La radio ───────────────────────────────────────────────────────────────

def test_la_radiofoto_se_dibuja_de_arriba_abajo():
    img = imagen()
    p = {**RA.POR_DEFECTO["radiofoto"], "modo": "telefoto", "dura": 6.0, "ruido": 0.0}
    ctx = contexto(t=0.0)
    RA.radiofoto(img, p, ctx)
    ctx.t, ctx.k = 6.0 * (RA.ENCABEZADO + RA.DIBUJO / 2), 50          # a la mitad del dibujo
    sale = RA.radiofoto(img, p, ctx)
    arriba, abajo = sale[:35], sale[60:]
    assert np.abs(abajo - RA.PAPEL_TELEFOTO).max() < 1e-5             # lo que falta llegar: el papel
    assert np.abs(arriba - RA.PAPEL_TELEFOTO).mean() > 0.05


def test_los_tonos_del_blanco_y_del_negro():
    for v, f in ((1.0, 2300), (0.0, 1500)):
        lineas = np.full((180, 360, 3), v, np.float32)
        y = R._tonos_radiofoto(lineas, "fax", 6.0, SR)
        tramo = y[int(6.0 * RA.ENCABEZADO * SR) + 2000: int(6.0 * RA.ENCABEZADO * SR) + 2000 + SR // 50]
        cruces = np.count_nonzero(np.diff(np.signbit(tramo))) / 2 / (len(tramo) / SR)
        assert abs(cruces - f) < 150, (v, cruces)


def test_el_dial_se_asienta_y_la_cancion_vuelve():
    d0, _ = RA.desintonia(0.0, 1_000_003, 100)
    d1, corre = RA.desintonia(1.0, 1_000_003, 100)
    assert d0 < 0.02 and d1 < 0.02 and abs(corre) < 0.05
    assert max(RA.desintonia(u, 1_000_003, 100)[0] for u in np.linspace(0.3, 0.7, 20)) > 0.5
    x = cancion(30)
    p = {**RA.POR_DEFECTO["dial"], "sintonizar": 6.0, "sonido": "sintonia", "_paso": 0}
    y = R.dial(x, p, 1, 0.0, SR, 0)
    eventos = R.eventos_en(100, "dial", 0.0, 30.0, 6.0, p["dura"])
    assert eventos
    a, b = eventos[0]
    medio = slice(int((a + 0.45 * (b - a)) * SR), int((a + 0.55 * (b - a)) * SR))
    # En medio de la búsqueda la canción se va: lo que queda no se parece a ella (la estática, el silbido).
    assert np.corrcoef(y[medio, 0], x[medio, 0])[0, 1] < 0.5
    despues = slice(int((b + 0.2) * SR), int((b + 0.6) * SR))
    if despues.stop < len(x) and not any(c < b + 0.6 and b + 0.2 < d for c, d in eventos[1:]):
        assert np.allclose(y[despues], x[despues], atol=1e-5)
