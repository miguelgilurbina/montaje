"""Pruebas de lo que se encontró buscando (2026-11-23): el cinetismo (`cinetico.py`), la radio en su segunda vuelta
(`aire.py`), el color del cine mudo (`cinemudo.py`) y los juguetes de antes del cine (`juguetes.py`).

    python -m pytest py/pruebas -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from montaje import aire as AI  # noqa: E402
from montaje import analogo as A  # noqa: E402
from montaje import cinemudo as CM  # noqa: E402
from montaje import cinetico as CI  # noqa: E402
from montaje import juguetes as J  # noqa: E402

SR = 48000


def imagen(alto: int = 90, ancho: int = 120, semilla: int = 1, corre: int = 0) -> np.ndarray:
    r = np.random.default_rng(semilla)
    yy, xx = np.mgrid[0:alto, 0:ancho].astype(np.float32)
    base = np.stack([((xx + corre) % ancho) / ancho, yy / alto, 0.5 + 0.5 * np.sin((xx + corre) / 9)], -1)
    return np.clip(base * 0.8 + 0.1 * r.random((alto, ancho, 3)), 0, 1).astype(np.float32)


def contexto(t: float = 0.0, alto: int = 90, ancho: int = 120, fps: float = 24.0) -> A.Contexto:
    c = A.Contexto(1, fps, alto, ancho)
    c.t, c.k = t, int(round(t * fps))
    return c


# ── El cinetismo ───────────────────────────────────────────────────────────

def test_la_vibracion_es_de_dos_tintas():
    sale = CI.cinetico(imagen(), CI.POR_DEFECTO["cinetico"], contexto())
    fondo, linea = CI._rgb(CI.FONDO), CI._rgb(CI.LINEA)
    # Cada pixel es una mezcla del fondo y la línea: está sobre el segmento entre los dos colores.
    m = ((sale - linea) @ (fondo - linea)) / ((fondo - linea) @ (fondo - linea))
    assert np.abs(sale - (linea + m[..., None] * (fondo - linea))).max() < 0.02
    # Lo oscuro lleva más línea que lo claro (el brillo se mide dentro del cuadro: mitad oscura, mitad clara).
    mitad = np.full((90, 120, 3), 0.9, np.float32)
    mitad[:, :60] = 0.1
    sale = CI.cinetico(mitad, CI.POR_DEFECTO["cinetico"], contexto())
    assert sale[:, 5:55].mean() < sale[:, 65:115].mean() - 0.1


def test_el_moire_se_mueve_con_el_tiempo():
    p = {**CI.POR_DEFECTO["cinetico"], "tecnica": "moire"}
    a, b = CI.cinetico(imagen(), p, contexto(0.0)), CI.cinetico(imagen(), p, contexto(2.0))
    assert np.abs(a - b).mean() > 0.02
    p0 = {**p, "deriva": 0.0, "angulo": 4.0}
    assert np.allclose(CI.cinetico(imagen(), p0, contexto(0.0)), CI.cinetico(imagen(), p0, contexto(2.0)))


# ── El color del cine mudo ─────────────────────────────────────────────────

def test_el_tintado_deja_el_negro_negro_y_tine_lo_claro():
    p = {**CM.POR_DEFECTO["tinte"], "tinta": "azul", "fuerza": 1.0}
    blanco = CM.tinte(np.ones((8, 8, 3), np.float32), p, contexto())[0, 0]
    negro = CM.tinte(np.zeros((8, 8, 3), np.float32), p, contexto())[0, 0]
    assert np.allclose(blanco, CM.TINTES["azul"], atol=0.01) and negro.max() < 0.01


def test_el_tintado_automatico_elige_por_la_escena():
    p = CM.POR_DEFECTO["tinte"]
    noche = np.full((40, 40, 3), [0.08, 0.09, 0.12], np.float32)
    lampara = np.full((40, 40, 3), [0.85, 0.6, 0.35], np.float32)
    c = contexto()
    c.original = noche
    azul = CM.tinte(noche * 0 + 0.5, p, c).mean((0, 1))
    c2 = contexto()
    c2.original = lampara
    ambar = CM.tinte(lampara * 0 + 0.5, p, c2).mean((0, 1))
    # La noche, azulada; la lámpara, cálida (aunque la copia que llega sea gris: el color sale de la escena).
    assert azul[2] > azul[0] and ambar[0] > ambar[2]


def test_el_virado_y_los_dos_colores():
    p = {**CM.POR_DEFECTO["tinte"], "modo": "virado", "tinta": "sepia", "fuerza": 1.0}
    assert np.allclose(CM.tinte(np.zeros((4, 4, 3), np.float32), p, contexto())[0, 0], CM.VIRADOS["sepia"], atol=0.01)
    assert np.allclose(CM.tinte(np.ones((4, 4, 3), np.float32), p, contexto())[0, 0], 1.0, atol=0.01)
    azul = np.full((4, 4, 3), [0.1, 0.2, 0.95], np.float32)
    sale = CM.tinte(azul, {**CM.POR_DEFECTO["tinte"], "modo": "dos-colores", "fuerza": 1.0}, contexto())[0, 0]
    assert sale[2] < 0.5          # sin azules de verdad


def test_los_dos_colores_que_se_corren_dejan_franja_en_lo_que_se_mueve():
    p = {**CM.POR_DEFECTO["tinte"], "modo": "kinemacolor", "fuerza": 1.0}
    def barra(x0):
        img = np.zeros((30, 60, 3), np.float32)
        img[:, x0:x0 + 10] = 1.0
        return img
    c = contexto(alto=30, ancho=60)
    CM.tinte(barra(20), p, c)
    c.k += 1
    sin_mover = CM.tinte(barra(20), p, c)
    c.k += 1
    movido = CM.tinte(barra(34), p, c)
    rojo_verde = lambda x: np.abs(x[..., 0] - x[..., 1]).mean()  # noqa: E731
    # Quieta, la barra es del mismo color; movida, el rojo es de ahora y el verde de antes: dos franjas.
    assert rojo_verde(sin_mover) < 0.01 and rojo_verde(movido) > 0.1


# ── Antes del cine ─────────────────────────────────────────────────────────

def test_el_zootropo_repite_su_loop():
    p = {**J.POR_DEFECTO["juguete"], "modo": "zootropo", "cuadros": 12, "ciclo": 4.0}
    c = contexto()
    vistos = {}
    for k in range(0, 72):    # tres segundos a 24 cuadros: la tira se llena en el primero
        c.t, c.k = k / 24, k
        J._loop(imagen(semilla=k, corre=k), p, c, 30, 40)
        vistos[k] = J._loop(imagen(semilla=k, corre=k), p, c, 30, 40)[1]
    assert vistos[60] == vistos[60 - 24] or vistos[60] in range(12)
    assert max(vistos.values()) < 12


def test_la_cronofotografia_encima_las_poses():
    p = {**J.POR_DEFECTO["juguete"], "modo": "cronofotografia", "intervalo": 0.1, "poses": 5}
    c = contexto(alto=40, ancho=40)
    for j in range(5):
        img = np.zeros((40, 40, 3), np.float32)
        img[10:20, j * 8:j * 8 + 4] = 1.0          # algo claro que se corre a la derecha
        c.t, c.k = j * 0.1 + 0.001, j * 3
        sale = J.juguete(img, p, c)
    marcas = (sale[15, :, 0] > 0.3).astype(int)
    assert np.count_nonzero(np.diff(marcas) == 1) >= 4   # cada pose dejó su marca


def test_la_lenticular_cambia_entre_ahora_y_antes():
    p = {**J.POR_DEFECTO["juguete"], "modo": "lenticular", "separacion": 1.0}
    c = contexto(alto=30, ancho=40)
    negro, blanco = np.zeros((30, 40, 3), np.float32), np.ones((30, 40, 3), np.float32)
    medias = []
    for k in range(0, 24 * 8):
        c.t, c.k = k / 24, k
        sale = J.juguete(negro if (k // 24) % 2 == 0 else blanco, p, c)   # cada segundo, lo contrario del anterior
        if k >= 48:
            medias.append(sale.mean())
    assert min(medias) < 0.3 and max(medias) > 0.7       # a veces se ve lo de hace un segundo, a veces lo de ahora


# ── La radio, segunda vuelta ───────────────────────────────────────────────

def test_el_texto_por_radio_suena_punto_por_punto():
    p = {**AI.POR_DEFECTO["hell"], "texto": "I", "velocidad": 1.0, "sonido": "tonos"}
    y = AI._sonido_hell(np.zeros((SR, 2), np.float32), p, 1, 0.0, SR, 0)
    # La I tiene columnas vacías a los lados (sin tono) y una columna llena al medio (tono todo el rato).
    col = SR // 7
    rms = lambda a, b: float(np.sqrt(np.mean(y[a:b] ** 2)))  # noqa: E731
    assert rms(int(2.2 * col), int(2.8 * col)) > 0.5 and rms(int(5.2 * col), int(5.8 * col)) < 0.05


def test_el_satelite_hace_tic_tac_dos_veces_por_segundo():
    p = {**AI.POR_DEFECTO["satelite"], "dura": 7.0, "sonido": "tictac"}
    y = AI._sonido_satelite(np.zeros((6 * SR, 2), np.float32), p, 1, 0.0, SR, 0)
    envolvente = np.abs(y).reshape(-1, SR // 100).mean(1)          # cada centésima
    tramo = envolvente[100:500] - envolvente[100:500].mean()       # mientras se dibuja
    auto = np.correlate(tramo, tramo, "full")[len(tramo) - 1:]
    assert auto[50] > 0.5 * auto[0]                                 # se repite cada medio segundo


def test_la_pintura_de_la_cascada_suena_en_su_banda(monkeypatch):
    p = {**AI.POR_DEFECTO["cascada"], "dura": 4.0, "sonido": "pintura"}
    cuadro = np.zeros((96, 64, 3), np.float32)
    cuadro[:, 32:] = 1.0                                            # la mitad derecha clara: los tonos altos
    monkeypatch.setattr(AI, "_cuadro_de", lambda ruta, t, alto=270: cuadro)   # sin video: el cuadro de prueba
    y = AI._sonido_cascada(np.zeros((4 * SR, 2), np.float32), p, 1, 0.0, SR, 0)
    f = np.fft.rfftfreq(len(y), 1 / SR)
    e = np.abs(np.fft.rfft(y))
    bajos, altos = e[(f > 1000) & (f < 2400)].sum(), e[(f > 2600) & (f < 4000)].sum()
    assert altos > 3 * bajos and e[f > 5000].sum() < 0.05 * e.sum()


# ── La marca en el osciloscopio (2026-11-23) ───────────────────────────────

def test_el_audio_dibuja_la_marca():
    from montaje import radio as RA

    if not RA.ESPIRAL.exists():
        import pytest

        pytest.skip("sin la espiral en la biblioteca de medios")
    p = {**RA.POR_DEFECTO["osciloscopio"], "dibujo": "espiral", "cada": 8.0, "dura": 3.0, "sonido": "marca"}
    t = np.arange(int(4 * SR)) / SR
    cancion = (0.2 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
    x = np.stack([cancion, cancion], 1)
    y = RA.sonido("osciloscopio", x, p, 1, 0.0, SR, 0)
    medio = slice(int(1.0 * SR), int(2.0 * SR))          # la marca entera
    mx, my = RA.marca_xy(t[medio], p)
    # Los dos canales, uno contra el otro, son la figura (más un poco de canción que queda debajo).
    assert np.corrcoef(y[medio, 0], mx)[0, 1] > 0.95 and np.corrcoef(y[medio, 1], my)[0, 1] > 0.95
    fuera = slice(int(3.5 * SR), int(4.0 * SR))           # pasada la marca, la canción tal cual
    assert np.allclose(y[fuera], x[fuera], atol=1e-5)


def test_el_nombre_tiene_sus_letras():
    from montaje import radio as RA

    contornos = RA._nombre("CURIANA")
    assert len(contornos) >= 7                            # al menos un contorno por letra (la A y la R tienen dos)
    rec = RA._recorrido("nombre", "CURIANA")
    assert rec.shape == (RA.PUNTOS, 2) and np.abs(rec).max() <= 1.0
