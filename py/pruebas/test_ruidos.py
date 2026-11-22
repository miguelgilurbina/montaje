"""Pruebas de los ruidos de los aparatos (`py/montaje/ruidos.py`): que suenen donde se ven y lo que dicen.

    python -m pytest py/pruebas -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from montaje import analogo as A  # noqa: E402
from montaje import casetera as C  # noqa: E402
from montaje import ruidos as R  # noqa: E402
from montaje.pelicula import evento_con_id  # noqa: E402

SR = 48000


def cancion(segundos: float = 8.0) -> np.ndarray:
    t = np.arange(int(segundos * SR)) / SR
    m = (0.25 * np.sin(2 * np.pi * 220 * t) + 0.1 * np.random.default_rng(1).standard_normal(len(t))).astype(np.float32)
    return np.stack([m, m], axis=1)


def db(y: np.ndarray) -> float:
    return 20 * np.log10(np.sqrt(np.mean(np.square(y))) + 1e-12)


def test_los_eventos_del_sonido_son_los_de_la_imagen():
    for semilla, nombre, por_minuto, dura in ((101, "pausa", 4.0, 1.6), (7, "rebobinar", 6.0, 1.2), (3, "manos", 4.0, 0.3)):
        hay = R.eventos_en(semilla, nombre, 0.0, 30.0, por_minuto, dura)
        for t in np.arange(0, 30, 0.01):
            assert (evento_con_id(semilla, nombre, t, por_minuto, dura) is not None) == any(a <= t < b for a, b in hay)


def test_sin_sonido_el_audio_pasa_igual():
    x = cancion(2)
    for nombre, p in (("casetera", {**C.POR_DEFECTO["casetera"], "pausa": 8.0}), ("antena", A.POR_DEFECTO["antena"]),
                      ("pantalla", A.POR_DEFECTO["pantalla"]), ("camara", A.POR_DEFECTO["camara"]),
                      ("compresion", {"errores": 1.0, "sonido": "ninguno"})):
        assert np.array_equal(R.sonido(nombre, x, p, 1, 0.0, SR, 0), x), nombre


def test_la_pausa_calla_la_cinta_justo_en_la_pausa():
    x = cancion(21)
    p = {**C.POR_DEFECTO["casetera"], "pausa": 4.0, "sonido": "mecanica", "_paso": 1}
    y = R.casetera(x, p, 1, 0.0, SR, 0)
    pausas = R.eventos_en(101, "pausa", 0.0, 21.0, 4.0, C.POR_DEFECTO["casetera"]["pausa_dura"])
    assert pausas
    for a, b in pausas:
        dentro = y[int((a + 0.2) * SR):int((b - 0.2) * SR)]
        antes = y[int(max(0.0, a - 1.0) * SR):int((a - 0.1) * SR)]
        assert db(dentro) < db(antes) - 15
        # el clac: un pico al entrar
        assert np.abs(y[int(a * SR):int((a + 0.03) * SR)]).max() > np.abs(dentro).max()


def test_el_arranque_calla_hasta_el_play():
    x = cancion(6)
    y = R.casetera(x, {**C.POR_DEFECTO["casetera"], "inicio": 2.0, "sonido": "mecanica", "_paso": 1}, 1, 0.0, SR, 0)
    assert db(y[: int(0.2 * SR)]) < db(x) - 40          # la pantalla azul: ni la canción
    assert abs(db(y[int(3 * SR):]) - db(x[int(3 * SR):])) < 1   # después, la canción entera


def test_mas_nieve_mas_siseo():
    x = cancion(4)
    ruido = [db(R.antena(x, {**A.POR_DEFECTO["antena"], "nieve": n, "sonido": "aire"}, 1, 0.0, SR, 0) - x) for n in (0.02, 0.1, 0.2)]
    assert ruido[0] < ruido[1] < ruido[2]


def test_el_parlante_del_televisor_no_da_graves_ni_brillo():
    t = np.arange(SR) / SR

    def respuesta(f: float) -> float:
        s = (0.2 * np.sin(2 * np.pi * f * t)).astype(np.float32)
        x = np.stack([s, s], axis=1)
        return db(R.pantalla(x, {"sonido": "parlante"}, 1, 0.0, SR, 0)) - db(x)

    assert respuesta(60) < -12 and respuesta(9000) < -10 and abs(respuesta(1000)) < 2 and respuesta(400) > 1


def test_la_llamada_se_corta_en_capturas_que_rompen_la_imagen():
    x = cancion(10)
    p = {"sonido": "llamada", "errores": 0.6, "_paso": 1, "_cps": 10.0}
    y = R.llamada(x, p, 1, 0.0, SR, 0)
    s = 101
    rotas = {j for j in range(100) if np.random.default_rng([s, A._num("codec"), j]).random() < 0.35 * 0.6}
    sueltas = {j for j in rotas if np.random.default_rng([s, A._num("llamada-audio"), j]).random() < R.PAQUETES_DE_AUDIO}
    assert sueltas and sueltas < rotas
    # Donde se pierde el paquete, el final del hueco está apagado.
    j = min(x for x in sueltas if x > 0)
    hueco = y[int((j / 10 + 0.08) * SR):int((j / 10 + 0.1) * SR)]
    assert db(hueco) < db(y) - 10
