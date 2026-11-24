"""Pruebas de la medida de monotonía de `revisar` (2026-11-23), con cuadros hechos a mano.

    python -m pytest py/pruebas -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from montaje import revisar as R  # noqa: E402

FPS = 24.0
ALTO, ANCHO = 90, 160


def _escena(semilla: int) -> np.ndarray:
    """Una imagen con estructura (manchas grandes), distinta para cada semilla."""
    rng = np.random.default_rng(semilla)
    chica = rng.random((9, 16)) * 200 + 20
    return np.kron(chica, np.ones((10, 10)))


def _video(planos: list[tuple[int, float]], movimiento: float = 3.0, semilla: int = 0) -> np.ndarray:
    """Cuadros grises: cada plano es (escena, segundos), con un poco de ruido que se mueve."""
    rng = np.random.default_rng(semilla)
    cuadros = []
    for escena, segundos in planos:
        base = _escena(escena)
        for _ in range(int(segundos * FPS)):
            cuadros.append(np.clip(base + rng.normal(0, movimiento, base.shape), 0, 255))
    return np.array(cuadros, np.uint8)


def _medir(cuadros: np.ndarray) -> dict:
    dif = np.abs(np.diff(cuadros.astype(np.int16), axis=0)).reshape(len(cuadros) - 1, -1).mean(axis=1)
    m = R.medir_monotonia(cuadros, dif, FPS)
    m["segundos"] = len(cuadros) / FPS
    return m


def test_encuentra_los_planos_y_el_metronomo():
    m = _medir(_video([(i, 2.0) for i in range(12)]))
    assert 11 <= m["planos"] <= 12
    assert m["planos_cv"] < 0.1
    assert any(s.startswith("metrónomo") for s in R.senales_de_monotonia(m))


def test_con_largos_distintos_no_hay_metronomo():
    m = _medir(_video([(i, d) for i, d in enumerate([1, 4, 2, 6, 1.5, 3, 5, 1, 2.5, 4])]))
    assert m["planos_cv"] > 0.4
    assert not any(s.startswith("metrónomo") for s in R.senales_de_monotonia(m))


def test_los_planos_que_vuelven():
    m = _medir(_video([(i % 2, 1.5) for i in range(10)]))   # dos escenas que se alternan
    assert m["planos_que_vuelven"] > 0.7
    assert any(s.startswith("vuelven") for s in R.senales_de_monotonia(m))


def test_un_fundido_tambien_es_un_cambio_de_plano():
    a, b = _escena(1), _escena(2)
    largo = int(2 * FPS)
    fundido = [a * (1 - u) + b * u for u in np.linspace(0, 1, int(0.8 * FPS))]
    cuadros = np.array([a] * largo + fundido + [b] * largo, np.uint8)
    assert _medir(cuadros)["planos"] == 2


def test_lo_quieto():
    m = _medir(_video([(i, 2.0) for i in range(6)], movimiento=0.0))
    assert m["poco_movimiento"] > 0.9
    assert any(s.startswith("quieto") for s in R.senales_de_monotonia(m))
