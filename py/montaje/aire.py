"""Lo que viaja por el aire, segunda vuelta de la radio: el satélite del tiempo, el texto que llega por radio y la
imagen escondida en la cascada de frecuencias (tres aparatos de imagen de la mesa analógica, con su sonido aquí mismo).

Miguel, el 2026-11-23: «Tu busca más por favor»; de lo que se encontró buscando eligió abrir «La radio, segunda
vuelta». Sigue a `radio.py` (la foto que llega por radio, el dial, el osciloscopio).

- **satelite**: la imagen que mandaban los satélites meteorológicos por radio (APT): dos imágenes lado a lado, la de
  luz y la infrarroja (lo frío claro), cada una con su barra de sincronismo a la izquierda y su cuña de grises a la
  derecha, que llega línea por línea. Su sonido es el de verdad: una portadora de 2 400 Hz modulada en amplitud por el
  brillo de cada línea, con el sincronismo A (1 040 Hz, 7 ciclos) y el B (832 pulsos por segundo, 7 pulsos), a dos
  líneas por segundo: el tic-tac. La imagen está acelerada; el tic-tac no. Los últimos satélites que la mandaban se
  apagaron en 2025.
- **hell**: el texto que llega por radio (Hellschreiber, 1929): letras de una grilla de puntos impresas dos veces en
  una tira de papel que corre, para que siempre se pueda leer una aunque los relojes no calcen (`inclinacion`: el
  texto se inclina y se corre). Su sonido: un tono que se prende y se apaga punto por punto.
- **cascada**: la pantalla de una radio por software: las frecuencias de la canción cayendo de arriba abajo, y cada
  `dura` segundos el cuadro del video dibujado en la cascada con el sonido mismo (cada fila de la imagen, un instante;
  cada columna, una frecuencia entre 1 y 4 kHz). Lo que se ve es lo que suena: la imagen está en el audio.

Las cifras de la norma (APT, Hellschreiber) van con su fuente en la ficha del 33; lo demás es [sin verificar].
"""

from __future__ import annotations

import math
import subprocess

import numpy as np

from . import analogo as A
from .pelicula import _a_tamano, _desenfocar

POR_DEFECTO = {
    "satelite": {"dura": 7.0, "ruido": 0.3, "sonido": "ninguno"},
    "hell": {"texto": "CURIANA RADIO 88.8 FM", "velocidad": 2.5, "alto": 0.13, "y": 0.8, "inclinacion": 0.25, "sonido": "ninguno"},
    "cascada": {"dura": 6.0, "historia": 8.0, "mezcla": 0.2, "pintar": True, "sonido": "ninguno"},
}
RANGOS = {
    "satelite": {"dura": (3, 7.5), "ruido": (0, 1), "sonido": ("ninguno", "tictac")},
    "hell": {"velocidad": (0.5, 6), "alto": (0.05, 0.4), "y": (0.1, 0.9), "inclinacion": (-2, 2), "sonido": ("ninguno", "tonos")},
    "cascada": {"dura": (2, 7.5), "historia": (2, 20), "mezcla": (0, 1), "sonido": ("ninguno", "pintura")},
}
LUMA = np.array([0.299, 0.587, 0.114], np.float32)
SR = 48000

#: La línea APT, en pixeles de los 2 080 de cada línea: sincronismo, espacio, imagen y telemetría de cada canal.
APT = [("sync_a", 39), ("espacio_a", 47), ("imagen_a", 909), ("tele_a", 45), ("sync_b", 39), ("espacio_b", 47),
       ("imagen_b", 909), ("tele_b", 45)]
APT_PORTADORA, APT_LINEAS_POR_SEGUNDO = 2400.0, 2.0
#: El Hellschreiber: el tono (Hz) y la grilla de cada letra (7 filas; aquí 5 columnas de letra y 2 de espacio).
HELL_TONO = 980.0
#: La cascada: hasta dónde llega a lo ancho, y la banda donde se dibuja la imagen.
CASCADA_FMAX, PINTURA = 8000.0, (1000.0, 4000.0)
#: Las tintas de la cascada, de lo callado a lo fuerte (noche, índigo, eléctrico, oro, hueso).
CASCADA_TINTAS = ["#07090d", "#26396a", "#2154c5", "#e6b43c", "#f3ead4"]


def errores(nombre: str, a: dict) -> list[str]:
    if nombre == "hell" and "texto" in a and (not isinstance(a["texto"], str) or not a["texto"].strip()):
        return ["hell.texto: el texto que llega"]
    if nombre == "cascada" and "pintar" in a and not isinstance(a["pintar"], bool):
        return ["cascada.pintar: true o false"]
    return []


CONSEJO = {"satelite": "acorta la `dura` del satélite", "cascada": "acorta la `dura` de la cascada"}


def calentar(pasos: list[tuple[str, dict]], fps: float, solo: int | None = None) -> int:
    n = 0
    for i, (nombre, p) in enumerate(pasos):
        if solo is not None and i != solo:
            continue
        if nombre == "satelite":
            n = max(n, int(math.ceil(p["dura"] * fps)) + 2)
    return n


def _rgb(hexa: str) -> np.ndarray:
    return np.array([int(hexa[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)


def _cuadro_de(entrada, t: float, alto: int = 270) -> np.ndarray | None:
    """Un cuadro de la entrada en el segundo t (para el sonido, que no tiene la imagen)."""
    from pathlib import Path

    if not entrada:
        return None
    try:
        return A.leer_cuadros(Path(entrada), [max(0.0, t)], alto)[0].astype(np.float32) / 255
    except (StopIteration, SystemExit, OSError):
        return None


# ── El satélite ────────────────────────────────────────────────────────────

def _canales(img: np.ndarray, alto: int) -> tuple[np.ndarray, np.ndarray]:
    """La luz (canal A) y el infrarrojo (canal B: lo frío claro, lo tibio oscuro), en grises."""
    lum = img @ LUMA
    luz = np.clip((lum - 0.04) / 0.9, 0, 1)
    ir = np.clip(1.05 - 0.85 * _desenfocar(lum[..., None], max(1.0, alto / 300))[..., 0] - 0.25 * (img[..., 0] - img[..., 2]), 0, 1)
    return luz.astype(np.float32), ir.astype(np.float32)


def _linea_apt(luz: np.ndarray, ir: np.ndarray, y: int, ancho: int) -> np.ndarray:
    """Una línea APT (los 2 080 pixeles, 0 a 1) a `ancho` muestras: sincronismos, imagen y telemetría."""
    partes = []
    cuna = (y // max(1, luz.shape[0] // 16)) % 16
    gris = (cuna + 1) / 8 if cuna < 8 else 0.0 if cuna == 8 else 0.3 + 0.04 * (cuna - 9)
    for nombre, n in APT:
        if nombre == "sync_a":
            partes.append((np.arange(n) % 4 >= 2).astype(np.float32) * 0.9 + 0.05)       # 7 ciclos finos
        elif nombre == "sync_b":
            partes.append((np.arange(n) % 5 >= 2).astype(np.float32) * 0.9 + 0.05)       # 7 pulsos más anchos
        elif nombre.startswith("espacio"):
            partes.append(np.full(n, 0.08 if nombre.endswith("a") else 0.92, np.float32))
        elif nombre.startswith("tele"):
            partes.append(np.full(n, gris, np.float32))
        else:
            fila = (luz if nombre.endswith("a") else ir)[y]
            partes.append(np.interp(np.linspace(0, len(fila) - 1, n), np.arange(len(fila)), fila).astype(np.float32))
    linea = np.concatenate(partes)
    return np.interp(np.linspace(0, len(linea) - 1, ancho), np.arange(len(linea)), linea).astype(np.float32)


def satelite(img: np.ndarray, p: dict, ctx) -> np.ndarray:
    from .radio import DIBUJO, ENCABEZADO, llegada

    alto, ancho = ctx.alto, ctx.ancho
    c, u = llegada(ctx.t, p["dura"])
    est = ctx.estado.setdefault(("satelite", ctx.paso), {})
    if est.get("llegada") != c:
        est["llegada"] = c
        chica = _a_tamano(img, alto, int(alto * 909 / 640))
        luz, ir = _canales(chica, alto)
        r = np.random.default_rng([ctx.semilla * 100 + ctx.paso, A._num("satelite"), c])
        imagen = np.stack([_linea_apt(luz, ir, y, ancho) for y in range(alto)])
        ruido = p["ruido"]
        imagen += r.standard_normal(imagen.shape).astype(np.float32) * 0.04 * ruido
        for y in np.nonzero(r.random(alto) < 0.015 * ruido)[0]:   # líneas que se pierden: blancas o negras
            imagen[y] = float(r.random() < 0.5)
        est["imagen"] = np.clip(imagen, 0, 1)
    dibujado = min(1.0, max(0.0, (u - ENCABEZADO) / DIBUJO))
    y = int(round(dibujado * alto))
    gris = np.full((alto, ancho), 0.03, np.float32)
    gris[:y] = est["imagen"][:y]
    if 0 < dibujado < 1:
        gris[max(0, y - 1):y + 1] = 0.9
    tono = np.array([0.94, 0.97, 1.0], np.float32)    # el gris frío de las impresiones de satélite
    return np.clip(gris[..., None] * tono, 0, 1).astype(np.float32)


def _sonido_satelite(x, p, semilla, t0, sr, indice):
    """El tic-tac: dos líneas por segundo, cada una el brillo de la fila que va llegando, en amplitud sobre 2 400 Hz."""
    from .radio import DIBUJO, ENCABEZADO

    n = len(x)
    y = np.zeros(n)
    t = t0 + np.arange(n) / sr
    dura = p["dura"]
    imagenes: dict = {}
    por_linea = int(sr / APT_LINEAS_POR_SEGUNDO)
    for k in range(math.floor(t0 * APT_LINEAS_POR_SEGUNDO), math.ceil(t[-1] * APT_LINEAS_POR_SEGUNDO) + 1):
        inicio = k / APT_LINEAS_POR_SEGUNDO
        c = math.floor(inicio / dura)
        u = (inicio - c * dura) / dura
        dibujado = (u - ENCABEZADO) / DIBUJO
        if not 0 <= dibujado < 1:
            continue
        if c not in imagenes:
            cuadro = _cuadro_de(p.get("_entrada"), c * dura)
            cuadro = cuadro if cuadro is not None else np.random.default_rng(c).random((60, 80, 3)).astype(np.float32)
            imagenes[c] = _canales(_a_tamano(cuadro, 120, 170), 120)
        luz, ir = imagenes[c]
        brillo = _linea_apt(luz, ir, int(dibujado * (luz.shape[0] - 1)), por_linea)
        a = int(round((inicio - t0) * sr))
        desde, hasta = max(a, 0), min(a + por_linea, n)
        if hasta > desde:
            y[desde:hasta] = brillo[desde - a:hasta - a]
    portadora = np.sin(2 * np.pi * APT_PORTADORA * t)
    señal = (0.13 + 0.87 * y) * portadora * (y > 0)
    return señal


# ── El texto que llega por radio ───────────────────────────────────────────

#: Una letra de 5 × 7 puntos por carácter (dibujada aquí; no es la del Hellschreiber original).
_LETRAS = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"],
    "Ñ": [".#.#.", "#.#..", "#...#", "##..#", "#.#.#", "#..##", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": ["..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."],
    ".": [".....", ".....", ".....", ".....", ".....", ".##..", ".##.."],
    ",": [".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."],
    ":": [".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."],
    "-": [".....", ".....", ".....", "#####", ".....", ".....", "....."],
    "/": ["....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."],
    "!": ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    " ": ["....."] * 7,
}
_SIN_TILDE = str.maketrans("ÁÉÍÓÚÜ", "AEIOUU")


def _patron(texto: str) -> np.ndarray:
    """El texto como grilla de puntos: 7 filas × (7 columnas por letra: 5 de letra y 2 de espacio)."""
    cols = []
    for ch in texto.upper().translate(_SIN_TILDE):
        filas = _LETRAS.get(ch, _LETRAS["?"])
        cols.append(np.array([[c == "#" for c in f] for f in filas], bool))
        cols.append(np.zeros((7, 2), bool))
    return np.concatenate(cols, axis=1)


def _columnas_hasta(t: float, inicio: float, p: dict, total: int) -> int:
    """Cuántas columnas del texto se imprimieron hasta el segundo t (el texto se repite con un espacio)."""
    return int(max(0.0, t - inicio) * p["velocidad"] * 7)


def hell(img: np.ndarray, p: dict, ctx) -> np.ndarray:
    alto, ancho = img.shape[:2]
    patron = _patron(p["texto"] + "   ")
    total = patron.shape[1]
    h_tira = int(p["alto"] * alto)
    punto = max(1.0, h_tira / 17)                        # dos copias de 7 puntos, y un margen
    impresas = _columnas_hasta(ctx.t, ctx.inicio, p, total)
    cabezal = int(0.86 * ancho)
    y0 = int(p["y"] * alto - h_tira / 2)
    sale = img.copy()
    papel = np.array([0.93, 0.90, 0.80], np.float32)
    sale[max(0, y0):y0 + h_tira, :cabezal] = papel * (0.96 + 0.04 * np.sin(np.arange(cabezal) / 7.0))[None, :, None]
    tinta = np.array([0.10, 0.12, 0.22], np.float32)
    n_vis = int(cabezal / punto) + 1
    for j in range(max(0, impresas - n_vis), impresas):
        x = int(cabezal - (impresas - j) * punto)
        col = patron[:, j % total]
        if not col.any() or x < 0:
            continue
        # Los relojes que no calzan: cada columna cae un poco más abajo (o arriba), y la tira lo da vuelta.
        corre = (j * p["inclinacion"] * 0.08) % 7
        for copia in (0, 7):
            for fila in np.nonzero(col)[0]:           # fila 0 arriba; el cabezal barre de abajo arriba
                yy = y0 + punto * (1 + ((fila + corre) % 7) + copia) - punto * 0.5
                ya, yb = int(yy), int(yy + punto * 0.85)
                if ya >= y0 and yb <= y0 + h_tira:
                    sale[ya:yb, x:x + max(1, int(punto * 0.85))] = tinta
    return np.clip(sale, 0, 1).astype(np.float32)


def _sonido_hell(x, p, semilla, t0, sr, indice):
    """El tono que se prende y se apaga punto por punto: cada columna se barre de abajo arriba en 14 medios puntos."""
    n = len(x)
    t = t0 + np.arange(n) / sr
    patron = _patron(p["texto"] + "   ")
    total = patron.shape[1]
    inicio = t0   # la salida empieza en t0, como la imagen cuenta desde `ctx.inicio`
    columnas = np.maximum(0.0, t - inicio) * p["velocidad"] * 7
    j = np.floor(columnas).astype(np.int64)
    dentro = columnas - j
    fila = np.clip(np.floor(dentro * 14) // 2, 0, 6).astype(np.int64)   # 14 medios puntos: cada fila, dos
    prendido = patron[6 - fila, j % total].astype(np.float64)
    # Bordes suaves (sin clics): el tono sube y baja en 2 ms.
    from scipy.ndimage import uniform_filter1d

    prendido = uniform_filter1d(prendido, max(1, int(0.002 * sr)))
    return prendido * np.sin(2 * np.pi * HELL_TONO * t)


# ── La cascada ─────────────────────────────────────────────────────────────

_ESPECTROS: dict = {}
FILAS_POR_SEGUNDO = 60.0


def _espectro(ruta) -> tuple[np.ndarray, float] | None:
    """El espectro de la canción de la entrada, una fila cada 1/60 s hasta 8 kHz, en 0–1 (se calcula una vez)."""
    if not ruta:
        return None
    ruta = str(ruta)
    if ruta not in _ESPECTROS:
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", ruta, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True)
        x = np.frombuffer(r.stdout, np.float32) if r.returncode == 0 else np.zeros(0, np.float32)
        if len(x) < 4096:
            _ESPECTROS[ruta] = None
        else:
            salto, nfft = int(SR / FILAS_POR_SEGUNDO), 2048
            filas = (len(x) - nfft) // salto
            idx = np.arange(nfft)[None, :] + salto * np.arange(filas)[:, None]
            bins = int(CASCADA_FMAX / (SR / nfft))
            mag = np.abs(np.fft.rfft(x[idx] * np.hanning(nfft), axis=1))[:, :bins]
            db = 20 * np.log10(mag + 1e-6)
            tope = np.percentile(db, 99.5)
            _ESPECTROS[ruta] = (np.clip((db - (tope - 70)) / 70, 0, 1).astype(np.float32), nfft / 2 / SR)
    return _ESPECTROS[ruta]


def _paleta(v: np.ndarray) -> np.ndarray:
    tintas = np.stack([_rgb(c) for c in CASCADA_TINTAS])
    pos = np.clip(v, 0, 1) * (len(tintas) - 1)
    i = np.clip(np.floor(pos).astype(np.int32), 0, len(tintas) - 2)
    f = (pos - i)[..., None]
    return tintas[i] * (1 - f) + tintas[i + 1] * f


def _pintura_de(cuadro: np.ndarray, filas: int, cols: int = 64) -> np.ndarray:
    """La imagen que se dibuja en la cascada: en grises, contrastada, `filas` × `cols`."""
    lum = _a_tamano(cuadro, filas, cols) @ LUMA
    a, b = np.percentile(lum, (5, 95))
    return np.clip((lum - a) / max(b - a, 0.05), 0, 1) ** 1.3


_PINTURAS: dict = {}


def _pintura_guardada(ruta, c: int, dura: float, cuadro_ahora: np.ndarray | None) -> np.ndarray | None:
    """La pintura de la llegada c: el cuadro de la entrada al empezarla (una vez por proceso)."""
    clave = (str(ruta), c, dura)
    if clave not in _PINTURAS:
        cuadro = _cuadro_de(ruta, c * dura)
        if cuadro is None:
            if cuadro_ahora is None:
                return None
            cuadro = cuadro_ahora
        if len(_PINTURAS) > 64:
            _PINTURAS.clear()
        _PINTURAS[clave] = _pintura_de(cuadro, 96)
    return _PINTURAS[clave]


def cascada(img: np.ndarray, p: dict, ctx) -> np.ndarray:
    alto, ancho = img.shape[:2]
    filas = np.arange(alto, dtype=np.float32)
    tiempos = ctx.t - filas / alto * p["historia"]                   # arriba lo de ahora, abajo lo de antes
    v = np.zeros((alto, ancho), np.float32)
    datos = _espectro(getattr(ctx, "entrada", None))
    if datos is not None:
        esp, retraso = datos
        k = np.clip(((tiempos - retraso) * FILAS_POR_SEGUNDO).astype(np.int64), 0, len(esp) - 1)
        cols = np.clip((np.arange(ancho) / ancho * esp.shape[1]).astype(np.int64), 0, esp.shape[1] - 1)
        v = esp[k][:, cols] * (tiempos >= 0)[:, None]
    if p["pintar"]:
        # La imagen que el sonido dibuja: cada llegada, el cuadro de la entrada al empezar (el mismo que lee el
        # sonido), de la última fila a la primera (así cae derecha en una cascada que baja). Se lee de la entrada y no
        # se recuerda: los pedazos en paralelo dibujan igual las pinturas viejas que siguen cayendo.
        x0, x1 = int(PINTURA[0] / CASCADA_FMAX * ancho), int(PINTURA[1] / CASCADA_FMAX * ancho)
        c_ahora = math.floor(ctx.t / p["dura"])
        for c in range(max(0, c_ahora - math.ceil(p["historia"] / p["dura"]) - 1), c_ahora + 1):
            pintura = _pintura_guardada(getattr(ctx, "entrada", None), c, p["dura"], img if c == c_ahora else None)
            if pintura is None:
                continue
            a, b = c * p["dura"] + 0.1 * p["dura"], c * p["dura"] + 0.9 * p["dura"]
            en = (tiempos >= a) & (tiempos < b) & (tiempos <= ctx.t)
            if not en.any():
                continue
            fila_img = ((1 - (tiempos[en] - a) / (b - a)) * (pintura.shape[0] - 1)).astype(np.int64)
            cols_img = np.clip(((np.arange(x0, x1) - x0) / max(1, x1 - x0) * pintura.shape[1]).astype(np.int64), 0, pintura.shape[1] - 1)
            v[np.nonzero(en)[0][:, None], np.arange(x0, x1)[None, :]] = np.maximum(
                v[np.nonzero(en)[0][:, None], np.arange(x0, x1)[None, :]], 0.25 + 0.75 * pintura[fila_img][:, cols_img])
    sale = _paleta(v)
    # La escala de frecuencias abajo, cada kilohercio una marca.
    for khz in range(1, int(CASCADA_FMAX / 1000)):
        x = int(khz * 1000 / CASCADA_FMAX * ancho)
        sale[alto - max(3, alto // 60):, x:x + max(1, ancho // 800)] = 0.6
    if p["mezcla"]:
        sale = sale * (1 - p["mezcla"]) + img * p["mezcla"] * (0.4 + 0.6 * v[..., None])
    return np.clip(sale, 0, 1).astype(np.float32)


def _sonido_cascada(x, p, semilla, t0, sr, indice):
    """La pintura: cada llegada, el cuadro del principio dibujado con 64 tonos entre 1 y 4 kHz, de la última fila a la
    primera; cada tono suena con el brillo de su columna."""
    n = len(x)
    y = np.zeros(n)
    t = t0 + np.arange(n) / sr
    dura = p["dura"]
    f = np.linspace(PINTURA[0], PINTURA[1], 64)
    for c in range(math.floor(t0 / dura), math.floor(t[-1] / dura) + 1):
        a, b = c * dura + 0.1 * dura, c * dura + 0.9 * dura
        sel = (t >= a) & (t < b)
        if not sel.any():
            continue
        cuadro = _cuadro_de(p.get("_entrada"), c * dura)
        if cuadro is None:
            continue
        pintura = _pintura_de(cuadro, 96)
        tt = t[sel]
        fila = (1 - (tt - a) / (b - a)) * (pintura.shape[0] - 1)
        i0 = np.clip(np.floor(fila).astype(np.int64), 0, pintura.shape[0] - 1)
        amp = pintura[i0]                                                    # (muestras, 64)
        fases = np.random.default_rng([semilla, c]).uniform(0, 2 * np.pi, 64)
        y[sel] = (amp * np.sin(2 * np.pi * f[None, :] * tt[:, None] + fases[None, :])).sum(1) / 8
    return y


def sonido(nombre: str, x: np.ndarray, p: dict, semilla: int, t0: float, sr: int, indice: int) -> np.ndarray:
    """El sonido de los tres, encima de la canción (que baja un poco mientras llega algo)."""
    if p.get("sonido", "ninguno") == "ninguno" or not len(x):
        return x
    if nombre == "satelite":
        señal, nivel = _sonido_satelite(x, p, semilla, t0, sr, indice), -15
    elif nombre == "hell":
        señal, nivel = _sonido_hell(x, p, semilla, t0, sr, indice), -16
    else:
        señal, nivel = _sonido_cascada(x, p, semilla, t0, sr, indice), -17
    ref = max(float(np.sqrt(np.mean(np.square(x)))), 10 ** (-30 / 20))
    rms = float(np.sqrt(np.mean(np.square(señal)))) if np.any(señal) else 1.0
    encima = señal / (rms + 1e-9) * ref * 10 ** (nivel / 20)
    hay = np.abs(señal) > 0
    from scipy.ndimage import uniform_filter1d

    baja = 1 - 0.45 * uniform_filter1d(hay.astype(np.float64), int(0.2 * sr))   # la canción cede un poco
    return (x * baja[:, None] + encima[:, None]).astype(np.float32)


APARATOS = {"satelite": satelite, "hell": hell, "cascada": cascada}
