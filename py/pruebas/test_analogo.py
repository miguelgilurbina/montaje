"""Pruebas de la mesa analógica (`py/montaje/analogo.py`): que la física de la señal haga lo que dice.

    python -m pytest py/pruebas -q
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from montaje import analogo as A  # noqa: E402
from montaje import estilos  # noqa: E402

H, W = A.LINEAS, A.MUESTRAS


def plano(y=0.5, i=0.0, q=0.0):
    return (np.full((H, W), y, np.float32), np.full((H, W), i, np.float32), np.full((H, W), q, np.float32))


def cinta_quieta(**extra) -> dict:
    """Una cinta sin nada que dependa del azar ni del tiempo: sólo sus filtros."""
    p = {**A.POR_DEFECTO["cinta"], "desgaste": 0.0, "temblor": 0.0, "cabezal": 0.0, "tracking": 0.0, "tono": 0.0}
    p.update(extra)
    return p


def sin_ruido(monkeypatch):
    monkeypatch.setattr(A, "_ruido", lambda rng, forma, sigma, filas=H: np.zeros((filas, W), np.float32))
    monkeypatch.setattr(A, "_dropouts", lambda *a, **k: None)


# ── La señal ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("modo", ["muesca", "peine"])
def test_un_color_liso_vuelve_igual(modo):
    y, i, q = plano(0.55, 0.12, -0.08)
    c = A.codificar(y, i, q, 0)
    y2, i2, q2 = A.decodificar(c, 0, modo)
    centro = (slice(40, H - 40), slice(60, W - 60))
    assert np.abs(y2[centro] - 0.55).max() < 0.01
    assert np.abs(i2[centro] - 0.12).max() < 0.01
    assert np.abs(q2[centro] + 0.08).max() < 0.01


def test_rayas_finas_de_luma_se_vuelven_color_falso():
    """El arcoíris: detalle de luma cerca de la subportadora que el televisor lee como color."""
    x = np.arange(W)
    y = np.tile((0.5 + 0.3 * np.sin(2 * np.pi * A.mhz(3.4) * x))[None, :], (H, 1)).astype(np.float32)
    _, i, q = A.decodificar(A.codificar(y, *plano(0, 0, 0)[1:], 0), 0, "muesca")
    gris = A.decodificar(A.codificar(*plano(0.5), 0), 0, "muesca")
    assert np.abs(i).mean() + np.abs(q).mean() > 20 * (np.abs(gris[1]).mean() + np.abs(gris[2]).mean() + 1e-4)


def test_los_puntos_del_color_caminan_de_un_cuadro_al_otro():
    """El color que se cuela en la luma en un borde cambia de signo cada cuadro (dot crawl); en lo liso, nada."""
    y, i, q = plano(0.5)
    i[:, W // 2:] = 0.3
    ya = A.decodificar(A.codificar(y, i, q, 0), 0, "muesca")[0]
    yb = A.decodificar(A.codificar(y, i, q, 1), 1, "muesca")[0]
    borde = np.abs(ya - yb)[100:300, W // 2 - 6:W // 2 + 6].mean()
    liso = np.abs(ya - yb)[100:300, 100:200].mean()
    assert borde > 0.005 and liso < 0.1 * borde


# ── La cinta ───────────────────────────────────────────────────────────────

def _borde(fila: np.ndarray, umbral: float) -> float:
    """Dónde cruza la fila el umbral (en muestras, con fracción)."""
    k = int(np.argmax(fila > umbral))
    return k - 1 + (umbral - fila[k - 1]) / (fila[k] - fila[k - 1])


def test_la_cinta_corre_el_color_a_la_derecha_y_lo_ensancha(monkeypatch):
    sin_ruido(monkeypatch)
    y, i, q = plano(0.5)
    y[:, W // 2:] = 0.7
    i[:, W // 2:] = 0.25
    s = A.Senal(y, i, q, 0)
    ctx = A.Contexto(1, 30, 480, 640)
    s = A.cinta(s, cinta_quieta(svideo=True), ctx)
    def marcas(fila):
        bajo, alto = fila[40:W // 2 - 40].mean(), fila[W // 2 + 120:W - 40].mean()
        return [_borde(fila, bajo + f * (alto - bajo)) for f in (0.1, 0.5, 0.9)]

    yi, ym, ys = marcas(s.y[200])
    ii, im, is_ = marcas(s.i[200])
    assert im - ym > 4                      # el color llega tarde
    assert (is_ - ii) > 6 * (ys - yi)       # y se arrastra: del 10 al 90 % tarda mucho más que la luma
    assert abs(s.y[200, 40:W // 2 - 40].mean() - (0.02 + 0.97 * 0.5)) < 0.003   # el realce no aclara lo liso


@pytest.mark.parametrize("formato", ["SP", "EP"])
def test_la_cinta_borra_el_detalle_fino_y_deja_el_grueso(monkeypatch, formato):
    sin_ruido(monkeypatch)
    x = np.arange(W)
    ctx = A.Contexto(1, 30, 480, 640)

    def queda(f_mhz):
        y = np.tile((0.5 + 0.2 * np.sin(2 * np.pi * A.mhz(f_mhz) * x))[None, :], (H, 1)).astype(np.float32)
        s = A.cinta(A.Senal(y, *plano(0, 0, 0)[1:], 0), cinta_quieta(formato=formato, realce=0.0, svideo=True), ctx)
        return float(s.y[100:300, 100:-100].std() / (0.2 / np.sqrt(2)))

    # Butterworth de segundo orden, como en los simuladores: lo grueso pasa, lo fino se va (más en EP que en SP).
    assert queda(0.8) > 0.8
    corte = A.FORMATOS[formato]["luma"]
    assert queda(4.0) == pytest.approx(1 / np.sqrt(1 + (4.0 / corte) ** 4), abs=0.06)
    assert queda(6.0) < 0.25


def test_el_tbc_endereza_las_lineas(monkeypatch):
    sin_ruido(monkeypatch)
    y, i, q = plano(0.3)
    y[:, W // 2:] = 0.8

    def bordes(con_tbc: bool):
        pasos, captura, semilla = A.preparar([{"aparato": "cinta", "temblor": 2.0, "cabezal": 0.0, "desgaste": 0.0, "svideo": True},
                                              *([{"aparato": "tbc"}] if con_tbc else [])])
        ctx = A.Contexto(semilla, 30, 480, 640)
        ctx.t = 1.3
        s = A.Senal(y.copy(), i.copy(), q.copy(), 0)
        for n, (nombre, p) in enumerate(pasos):
            ctx.paso = n
            s = A.APARATOS[nombre](s, p, ctx)
        return np.array([_borde(f, 0.55) for f in s.y[20:400]])

    assert bordes(False).std() > 0.5
    assert bordes(True).std() < 0.1 * bordes(False).std()


def test_el_cambio_de_cabezal_solo_toca_las_ultimas_lineas(monkeypatch):
    sin_ruido(monkeypatch)
    y, i, q = plano(0.3)
    y[:, W // 2:] = 0.8
    ctx = A.Contexto(1, 30, 480, 640)
    s = A.cinta(A.Senal(y, i, q, 0), cinta_quieta(cabezal=1.0, cabezal_lineas=8, svideo=True), ctx)
    medio = [_borde(f, 0.55) for f in s.y[100:460]]
    assert max(medio) - min(medio) < 0.05
    assert abs(_borde(s.y[H - 1], 0.55) - np.mean(medio)) > 20


# ── Determinista y sin costura ─────────────────────────────────────────────

def test_el_mismo_cuadro_sale_igual_solo_o_en_su_secuencia():
    """Lo que no tiene memoria sale igual procesado suelto que después de los anteriores: los pedazos en
    paralelo no dejan costura. Y dos veces con la misma semilla, idéntico."""
    rng = np.random.default_rng(3)
    cuadros = [rng.random((H, W, 3), dtype=np.float32) for _ in range(4)]
    pasos, captura, semilla = A.preparar([{"aparato": "cinta", "desgaste": 0.5, "tracking": 0.5},
                                          {"aparato": "antena", "nieve": 0.05, "fantasma": [[1.0, 0.2]]}])
    seguido = A.Contexto(semilla, 30, 480, 640)
    for k, c in enumerate(cuadros):
        seguido.k, seguido.t = k, k / 30
        ultimo = A.cuadro(c, pasos, captura, seguido)
    suelto = A.Contexto(semilla, 30, 480, 640)
    suelto.k, suelto.t = 3, 3 / 30
    assert np.array_equal(ultimo, A.cuadro(cuadros[3], pasos, captura, suelto))
    otra = A.Contexto(semilla + 1, 30, 480, 640)
    otra.k, otra.t = 3, 3 / 30
    assert not np.array_equal(ultimo, A.cuadro(cuadros[3], pasos, captura, otra))


def test_lo_que_tiene_memoria_pide_calentar():
    assert A.calentar(A.preparar([{"aparato": "cinta"}])[0]) == 0
    assert A.calentar(A.preparar([{"aparato": "realimentacion", "mezcla": 0.8}])[0]) > 15
    assert A.calentar(A.preparar([{"aparato": "camara", "estela": 0.7}])[0]) > 5


def test_suave_y_evento_no_dependen_del_camino():
    assert A.suave(1, "x", 3.7) == A.suave(1, "x", 3.7)
    assert all(-1 <= A.suave(2, "y", t / 10) <= 1 for t in range(200))
    vistos = [A.evento(5, "arruga", t / 30, 6, 0.3) for t in range(30 * 60)]
    hay = sum(v is not None for v in vistos) / 30 / 0.3
    assert 2 <= hay <= 12  # unos seis por minuto
    assert all(v is None or 0 <= v < 1 for v in vistos)


# ── La pantalla ────────────────────────────────────────────────────────────

def test_la_pantalla_conserva_el_brillo_de_un_gris():
    p = {**A.POR_DEFECTO["pantalla"], "curva": 0.0, "vineta": 0.0, "brillo": 0.0, "blanco": 6500, "gamma": 2.2,
         "convergencia": 0.0}
    ctx = A.Contexto(1, 30, 1080, 1620)
    for gris in (0.3, 0.7):
        sale = A.pantalla(A.Senal(*plano(gris), 0), p, ctx)
        centro = sale[300:780, 400:1200].astype(np.float32) / 255
        assert abs(centro.mean() - gris) < 0.04
        # Las líneas se ven: el brillo cambia de una fila a la siguiente.
        assert centro.mean(axis=(1, 2)).std() > 0.02


def test_lejos_las_lineas_y_la_mascara_se_apagan():
    ctx = A.Contexto(1, 30, 540, 810)
    p = {**A.POR_DEFECTO["pantalla"], "curva": 0.0, "vineta": 0.0, "brillo": 0.0}
    sale = A.pantalla(A.Senal(*plano(0.5), 0), p, ctx).astype(np.float32)
    assert sale[100:440, 200:600].mean(axis=(1, 2)).std() < 0.5   # sin franjas que hagan muaré


def test_el_fosforo_no_quema_la_imagen():
    """La persistencia se guardaba antes de una multiplicación en su lugar: desde el segundo cuadro, blanco."""
    p = {**A.POR_DEFECTO["pantalla"], "persistencia": 0.5, "brillo": 0.0}
    ctx = A.Contexto(1, 30, 540, 810)
    medias = []
    for k in range(3):
        ctx.k = k
        medias.append(A.pantalla(A.Senal(*plano(0.3), k), p, ctx)[100:440, 200:600].mean())
    assert max(medias) - min(medias) < 2


def test_el_blanco_no_cambia_con_la_resolucion():
    """La máscara (que sólo aparece a 1080) recortaba los blancos: el final salía más oscuro que el probador."""
    p = {**A.POR_DEFECTO["pantalla"], "curva": 0.0, "vineta": 0.0, "brillo": 0.0, "blanco": 6500}
    chico = A.pantalla(A.Senal(*plano(1.0), 0), p, A.Contexto(1, 30, 540, 810))[100:440, 200:600].mean() / 255
    grande = A.pantalla(A.Senal(*plano(1.0), 0), p, A.Contexto(1, 30, 1080, 1620))[200:880, 400:1200].mean() / 255
    assert abs(chico - grande) < 0.07


def test_la_primera_linea_conserva_su_color_con_el_peine():
    y, i, q = plano(0.5, 0.15, 0.0)
    _, i2, _ = A.decodificar(A.codificar(y, i, q, 0), 0, "peine")
    assert abs(i2[0, 100:-100].mean() - 0.15) < 0.02


def test_rodar_no_invierte_el_color():
    """Correr la compuesta un número impar de líneas cambia la fase de la subportadora: el color se invertía."""
    p = {**A.POR_DEFECTO["antena"], "nieve": 0.0, "rodar": 0.37}
    for t in (0.1, 0.33, 0.71, 1.29, 2.05):
        ctx = A.Contexto(1, 30, 480, 640)
        ctx.t = t
        s = A.antena(A.Senal(*plano(0.5, 0.15, 0.0), 0), p, ctx).componentes("muesca")
        imagen = s.y > 0.3   # fuera de la barra del borrado
        assert s.i[imagen].mean() > 0.1


def test_la_realimentacion_que_no_se_apaga_se_rechaza():
    assert A.errores([{"aparato": "realimentacion", "mezcla": 0.95, "contraste": 1.05}])
    assert not A.errores([{"aparato": "realimentacion", "mezcla": 0.85}])
    assert A.calentar(A.preparar([{"aparato": "realimentacion", "mezcla": 0.9, "contraste": 1.07}])[0]) > \
        A.calentar(A.preparar([{"aparato": "realimentacion", "mezcla": 0.9, "contraste": 1.0}])[0])


# ── La cadena ──────────────────────────────────────────────────────────────

def test_errores_de_una_cadena():
    assert A.errores([{"aparato": "cinta"}, {"aparato": "pantalla"}]) == []
    assert A.errores({"aparatos": [{"aparato": "antena", "fantasma": [[1.5, 0.3]]}], "captura": "muesca"}) == []
    mal = " ".join(A.errores([{"aparato": "pantalla"}, {"aparato": "cinta", "formato": "UHS", "desgaste": 3},
                              {"aparato": "licuadora"}, {"aparato": "colorizador", "tintas": ["rojo"]}]))
    for pedazo in ("al final", "UHS", "desgaste", "licuadora", "tintas"):
        assert pedazo in mal
    assert A.errores("cinta")
    assert A.errores([])


def test_el_tbc_endereza_solo_las_cintas_de_antes():
    pasos, _, _ = A.preparar([{"aparato": "cinta"}, {"aparato": "tbc", "fuerza": 0.8}, {"aparato": "cinta"}])
    assert pasos[0][1]["_tbc"] == 0.8 and "_tbc" not in pasos[2][1]


def test_las_cadenas_de_la_galeria_son_validas():
    cadenas = [e for e in estilos.leer() if e["tecnica"].get("comando") == "analogo"]
    assert cadenas, "la galería no tiene cadenas analógicas"
    for e in cadenas:
        assert estilos.errores(e) == [], e["id"]


def test_la_envolvente_de_las_ventanas():
    v = [(2.0, 4.0)]
    assert A.envolvente(0.0, v, 0.5) == 0 and A.envolvente(3.0, v, 0.5) == 1
    assert A.envolvente(1.75, v, 0.5) == pytest.approx(0.5) and A.envolvente(4.25, v, 0.5) == pytest.approx(0.5)
    assert A.envolvente(9.0, None, 0.5) == 1


# ── El sonido de la cinta ──────────────────────────────────────────────────

def _tono(f=1000.0, dur=4.0, amp=0.3):
    t = np.arange(int(dur * A.SR_AUDIO)) / A.SR_AUDIO
    return np.stack([amp * np.sin(2 * np.pi * f * t)] * 2, axis=1).astype(np.float32)


def _variacion_de_altura(y: np.ndarray) -> float:
    """Cuánto se mueve la altura de un tono (pico, en fracción), contando cruces por cero cada 100 ms."""
    s = np.signbit(y[:, 0])
    cruces = np.nonzero(s[1:] != s[:-1])[0]
    fs = []
    for a in np.arange(0.5, len(y) / A.SR_AUDIO - 0.6, 0.1):
        c = cruces[(cruces >= a * A.SR_AUDIO) & (cruces < (a + 0.1) * A.SR_AUDIO)]
        fs.append((len(c) - 1) / 2 / ((c[-1] - c[0]) / A.SR_AUDIO))
    return (max(fs) - min(fs)) / 2 / np.mean(fs)


def test_sin_sonido_la_cinta_no_toca_el_audio():
    x = _tono()
    assert A.sonido_de_cinta(x, {**A.POR_DEFECTO["cinta"]}, 1, 0.0) is x


def test_la_pista_lineal_tiembla_corta_agudos_y_silba():
    p = {**A.POR_DEFECTO["cinta"], "sonido": "lineal", "formato": "EP"}
    variacion = _variacion_de_altura(A.sonido_de_cinta(_tono(), p, 1, 0.0))
    assert 0.001 < variacion < 0.01   # unas décimas de por ciento: se oye como cinta, no como sirena
    agudo = A.sonido_de_cinta(_tono(9000), p, 1, 0.0)
    assert np.sqrt(np.mean(agudo**2)) < 0.4 * 0.3 / np.sqrt(2)   # EP corta en unos 5 kHz: a 9 kHz, −8 dB o más
    silencio = A.sonido_de_cinta(np.zeros((A.SR_AUDIO * 2, 2), np.float32), p, 1, 0.0)
    assert -60 < 20 * np.log10(np.sqrt(np.mean(silencio**2))) < -35
    assert np.array_equal(silencio, A.sonido_de_cinta(np.zeros((A.SR_AUDIO * 2, 2), np.float32), p, 1, 0.0))


def test_la_arruga_hunde_el_sonido_cuando_salta_la_imagen():
    p = {**A.POR_DEFECTO["cinta"], "sonido": "hifi", "arrugas": 20.0}
    x = _tono(440, 6.0)
    y = A.sonido_de_cinta(x, p, 7, 0.0)
    t = np.arange(len(x)) / A.SR_AUDIO
    en_arruga = np.array([(u := A.evento(7, "arruga", s, 20.0, 0.3)) is not None and 0.3 < u < 0.7 for s in t[::480]])
    nivel = np.sqrt(np.convolve(y[:, 0] ** 2, np.ones(480) / 480, mode="same"))[::480]
    assert en_arruga.any() and not en_arruga.all()
    assert nivel[en_arruga].mean() < 0.7 * nivel[~en_arruga].mean()


# ── Un video de verdad ─────────────────────────────────────────────────────

@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="sin ffmpeg")
def test_un_video_pasa_entero_y_con_su_audio(tmp_path):
    entrada = tmp_path / "prueba.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=320x240:rate=24:duration=2",
                    "-f", "lavfi", "-i", "sine=frequency=440:duration=2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-shortest", str(entrada)], check=True)
    salida = A.procesar(entrada, tmp_path / "sale.mp4", [{"aparato": "cinta"}, {"aparato": "antena"}],
                        hilos=2, callado=True, ventanas=[(0.5, 1.5)], fundido=0.25)
    r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_entries", "stream=codec_type,nb_read_frames,width,height",
                        "-of", "json", str(salida)], capture_output=True, text=True, check=True)
    flujos = {s["codec_type"]: s for s in json.loads(r.stdout)["streams"]}
    assert int(flujos["video"]["nb_read_frames"]) == 48
    assert (flujos["video"]["width"], flujos["video"]["height"]) == (320, 240)
    assert "audio" in flujos
    assert not any(tmp_path.glob(".sale-pedazos"))


def _cuadros(video: Path, ancho: int, alto: int) -> np.ndarray:
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(-1, alto, ancho, 3).astype(np.int16)


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="sin ffmpeg")
def test_con_memoria_la_ventana_no_depende_de_los_pedazos(tmp_path):
    """Fuera de las ventanas la realimentación seguía sin andar: al abrir una, la memoria dependía de la costura."""
    entrada = tmp_path / "prueba.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=320x240:rate=24:duration=3",
                    "-c:v", "libx264", "-crf", "0", "-pix_fmt", "yuv420p", str(entrada)], check=True)
    cadena = [{"aparato": "realimentacion", "mezcla": 0.85}]
    a = A.procesar(entrada, tmp_path / "a.mp4", cadena, hilos=2, callado=True, ventanas=[(1.6, 2.4)], fundido=0.2,
                   crf=0, pedazo=48)
    b = A.procesar(entrada, tmp_path / "b.mp4", cadena, hilos=3, callado=True, ventanas=[(1.6, 2.4)], fundido=0.2,
                   crf=0, pedazo=10)
    assert np.abs(_cuadros(a, 320, 240) - _cuadros(b, 320, 240)).max() <= 2


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="sin ffmpeg")
def test_un_video_girado_sale_derecho(tmp_path):
    """Un video del teléfono trae su giro aparte: ffmpeg lo endereza al leerlo, y el motor tiene que saberlo."""
    crudo, girado = tmp_path / "crudo.mp4", tmp_path / "girado.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=320x240:rate=24:duration=1",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(crudo)], check=True)
    r = subprocess.run(["ffmpeg", "-v", "error", "-display_rotation", "90", "-i", str(crudo), "-c", "copy", str(girado)],
                       capture_output=True, text=True)
    if r.returncode:
        pytest.skip("este ffmpeg no sabe poner el giro (-display_rotation)")
    info = A._sonda(girado)
    assert (info["ancho"], info["alto"]) == (240, 320)
    sale = A.procesar(girado, tmp_path / "sale.mp4", [{"aparato": "cinta"}], hilos=2, callado=True)
    s = A._sonda(sale)
    assert (s["ancho"], s["alto"]) == (240, 320)
