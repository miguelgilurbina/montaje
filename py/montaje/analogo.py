"""La mesa analógica: el video pasado por aparatos de verdad, simulados en su señal.

Miguel, el 2026-11-20 antes de dormir: «Busca referencias para alteración de vídeo análogo y trabaja en
implementar eso en el proyecto. Sigue tu intuición». Viene de su idea del 2026-10-12, el flujo «Video
Glitch»: un aparato que rompe la señal y un TBC que la estabiliza. `senal` lo hace con filtros sueltos en
las transiciones; esto baja un piso: no pinta un «efecto VHS» encima, sino que simula lo que le pasa a la
señal en cada aparato, y los defectos salen solos de esa física (el color corrido, los puntos que caminan
por los bordes, el arcoíris en las rayas finas, la nieve de colores). Las referencias, con sus números y
sus fuentes, están en `direccion/ANALOGO.md`.

## La señal

La de la norma **NTSC-M**, la de la televisión de Venezuela: 480 líneas visibles, cada una una señal en
el tiempo de 52,66 µs, con el color montado en una subportadora de 3,58 MHz. Cada línea se procesa como lo
que era: los anchos de banda se escriben en MHz y se vuelven muestras (760 por línea, lo que toman los
digitalizadores «4fsc»); el cuadro de cualquier tamaño entra a esa grilla y vuelve a su tamaño al final.
Los filtros van en el espectro de cada línea (una FFT por fila), y ahí mismo se corre cada línea en el
tiempo: el temblor de la cinta es un retraso distinto por línea.

## Los aparatos, en el orden en que la señal pasa por ellos

| aparato | qué simula | perillas principales |
|---|---|---|
| `camara` | la cámara de video de los 90: la columna clara que deja una luz fuerte en el CCD, blancos que se queman y pierden el color, el balance que se corre, el realce de bordes, el ruido de las sombras | `mancha`, `blancos`, `balance`, `detalle`, `ruido` |
| `osd` | lo que el aparato escribe en la imagen: la fecha de la cámara (grabada: pasa por la cinta si va antes) o el «PLAY ▶» del VCR (si va después) | `textos`, `fecha`, `hora` |
| `cinta` | el VHS: luma en FM con poco ancho de banda, el color «rebajado» (color-under) que se corre, el realce de bordes, el ruido de cinta, los dropouts, el cambio de cabezal abajo, la base de tiempo que tiembla, el tracking que se pierde, las arrugas; y cada copia de una copia | `formato` (SP/LP/EP/S-VHS/Video8/Hi8/Betamax), `generaciones`, `desgaste`, `temblor`, `tracking`, `arrugas` |
| `antena` | la señal que llega por el aire: nieve, fantasmas (ecos de la señal rebotada), interferencias, la barra de zumbido que sube, la imagen que rueda o se tuerce cuando se pierde el sincronismo; con la señal muy débil, el televisor apaga el color | `nieve`, `fantasma`, `interferencia`, `zumbido`, `rodar`, `desenganche` |
| `tbc` | el corrector de base de tiempo (el JVC de la idea de Miguel): endereza las líneas que tiemblan, sin quitar el ruido ni el color corrido; trae los controles de un procesador (brillo, contraste, color, tono) | `fuerza`, `brillo`, `contraste`, `color`, `tono` |
| `colorizador` | el colorizador de los sintetizadores de video: el brillo se vuelve color, en bandas o continuo (por defecto, las tintas de Curiana) | `tintas`, `bandas`, `mezcla` |
| `iman` | el imán junto al tubo (el «Magnet TV» de Nam June Paik): la imagen se tuerce alrededor del imán y el color se corre de tono; con `ondas`, el «wobbulator» | `fuerza`, `radio`, `velocidad`, `ondas` |
| `relieve` | el procesador de barrido Rutt/Etra: cada línea se levanta según su brillo, y la imagen se vuelve un relieve de líneas | `lineas`, `altura`, `mezcla` |
| `realimentacion` | la cámara que mira su propio monitor: lo de antes vuelve, más chico y girado, y deja estelas en espiral | `mezcla`, `zoom`, `giro`, `tono` |
| `pantalla` | el televisor de tubo, al tamaño de salida: líneas de barrido cuyo haz engorda con el brillo, máscara de fósforos, curva del vidrio, el resplandor, la persistencia del fósforo, el blanco azulado de 9300 K, la convergencia imperfecta | `lineas`, `mascara`, `curva`, `brillo`, `persistencia`, `blanco` |

Y los que no trabajan en la señal sino en la imagen (2026-11-21), en sus módulos:

| aparato | qué simula | dónde |
|---|---|---|
| `pelicula` | Super 8, 8 mm y 16 mm en la emulsión: la curva, el grano en la densidad, el halo rojo, el vaivén, los 18 cuadros, polvo, rayas y pelos, el quemado, los tintes que se destiñen, la fecha naranja | `pelicula.py` |
| `sensor` | la cámara digital temprana: el celular, la webcam, la de bolsillo, la MiniDV | `digital.py` |
| `compresion` | el códec: bloques, lo que no se actualiza, el cuadro clave, los errores que se arrastran | `digital.py` |
| `consola` | la consola de mezcla de los 90: mosaico, estrobo, multi, pintura, negativo, llave (siempre, a ratos o al pulso) | `consola.py` |
| `proyector` | la película proyectada en la pared o en la sábana: la mancha de luz, el trapecio, el cuarto oscuro | `proyeccion.py` |

Y uno de señal en su propio módulo: `casetera` (la pausa, rebobinar, el arranque en azul, el entrelazado), en
`casetera.py`.

Una cadena puede mezclar los dos mundos: `[pelicula, cinta, pantalla]` es el Super 8 de la familia pasado a VHS y
visto en el televisor.

Un **gesto** (2026-11-22) es un momento que va encima de cualquier base: la pausa, el rebobinado o el arranque de la
casetera, el estrobo, la llave, la pintura, el mosaico o el multi de la consola. Su estilo lleva `"gesto": true`, la
cadena con sólo esos aparatos y `sobre`, la base de su muestra; `componer` lo pone en su lugar (la consola antes de la
cinta, la casetera después) y `--gesto` lo suma a cualquier `--cadena`.

Una **cadena** es la lista de aparatos con sus perillas (lo que no se dice toma su valor por defecto):

    [{"aparato": "cinta", "formato": "EP", "generaciones": 2}, {"aparato": "pantalla"}]

o, para decir también cómo se digitaliza al final (`captura`: `peine` o `muesca`, el filtro que separa luma y
color) y con qué semilla:

    {"aparatos": [...], "captura": "peine", "semilla": 3}

Entre aparatos la señal viaja **compuesta** (luma y color en un solo cable) cuando así salía del aparato:
la cinta y la antena entregan señal compuesta, y quien la recibe la separa con su filtro. Ahí nacen el
arcoíris y los puntos que caminan. La `pantalla` va siempre al final.

Todo lo aleatorio sale de la semilla y del número de cuadro: el mismo video con la misma cadena da el
mismo resultado, y los pedazos se procesan en paralelo sin que se note la costura.

## Uso

    python montaje.py analogo <video o foto> --cadena copia-de-copia     # un estilo de la galería
    python montaje.py analogo <video> --cadena '[{"aparato": "cinta", "formato": "LP"}]'
    python montaje.py analogo <video> --cadena vhs-de-la-casa --ventana 4 9 --ventana 20 26
    python montaje.py analogo <video> --cadena super-8-de-la-familia --gesto estrobo-de-la-consola   # un gesto encima
    python montaje.py analogo <video> --comparar vhs-de-la-casa,antena-lejana --en 2,5,9   # hoja lado a lado
    python montaje.py analogo <video> --recorrido vhs-de-la-casa,antena-lejana --desde 3 --segundos 6
    python montaje.py analogo --cadenas                                     # las cadenas de la galería
    python montaje.py analogo <render de p> --cadena consola-al-pulso --golpes <p>   # lo que va al pulso de su canción

La entrada es una ruta (absoluta o dentro de los medios). Sale `<nombre>-<cadena>.mp4` al lado, con el
audio de la entrada. Una foto sale como video de `--segundos`. Con `--ventana`, la cadena sólo entra en
esos segundos (con un fundido de `--fundido`): la regla de Miguel es que las imágenes protagonistas se
vean al 100 %, así que el video analógico va donde el guion lo pide, no encima de todo.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import time
import zlib
from collections import deque
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from pathlib import Path

import numpy as np

from .rutas import MEDIOS, RAIZ, salir

# ── La norma: NTSC-M ────────────────────────────────────────────────────────

LINEA_US = 52.66          # la parte visible de cada línea, en microsegundos
PERIODO_US = 63.556       # la línea entera, con su borrado horizontal
FSC = 3.579545            # la subportadora de color, en MHz
LINEAS = 480              # las líneas visibles de un cuadro
MUESTRAS = 760            # muestras por línea visible: ≈ 4 × fsc × 52,66 µs, como los digitalizadores «4fsc»
RELLENO = 132             # borde reflejado a cada lado antes de la FFT: ni el filtro ni un corrimiento dan la vuelta
N_FFT = 1024
FREC = np.fft.rfftfreq(N_FFT).astype(np.float32)     # ciclos por muestra
LINEA = np.arange(LINEAS, dtype=np.float32)
BORRADO = int(round((PERIODO_US - LINEA_US) * MUESTRAS / LINEA_US))   # el borrado horizontal, en muestras
BORRADO_V = 42            # el borrado vertical de un cuadro (21 líneas por campo), en líneas


def mhz(f: float) -> float:
    """Megahertz → ciclos por muestra de la línea."""
    return f * LINEA_US / MUESTRAS


def muestras_us(t: float) -> float:
    """Microsegundos → muestras."""
    return t * MUESTRAS / LINEA_US


# ── Filtros: el espectro de cada línea ──────────────────────────────────────

def _espectro(x: np.ndarray) -> np.ndarray:
    p = np.pad(x, ((0, 0), (RELLENO, N_FFT - x.shape[1] - RELLENO)), mode="reflect")
    return np.fft.rfft(p, axis=1)


def _senal(espectro: np.ndarray, ancho: int = MUESTRAS) -> np.ndarray:
    return np.fft.irfft(espectro, n=N_FFT, axis=1)[:, RELLENO:RELLENO + ancho].astype(np.float32)


def filtrar(x: np.ndarray, *respuestas: np.ndarray) -> np.ndarray:
    """Cada línea de `x` pasada por el producto de las respuestas (en frecuencia)."""
    e = _espectro(x)
    for r in respuestas:
        e = e * r
    return _senal(e, x.shape[1])


def pasabajos(corte: float, orden: int = 2) -> np.ndarray:
    """Butterworth de fase cero: −3 dB en `corte` MHz."""
    return (1 / np.sqrt(1 + (FREC / mhz(corte)) ** (2 * orden))).astype(np.float32)


def pasabajos_causal(corte: float, polos: int = 2) -> np.ndarray:
    """Polos simples en cascada, como un filtro analógico de verdad: lo que borra lo arrastra hacia la derecha."""
    a = math.exp(-2 * math.pi * mhz(corte))
    h = (1 - a) / (1 - a * np.exp(-2j * np.pi * FREC))
    return (h**polos).astype(np.complex64)


def pasabanda(centro: float, ancho: float, orden: int = 2) -> np.ndarray:
    """Una campana alrededor de `centro`, con un pasaaltos que la deja en cero abajo: sin él, la campana
    conserva algo de respuesta en la continua y le roba brillo a todo lo liso."""
    campana = 1 / np.sqrt(1 + ((FREC - mhz(centro)) / mhz(ancho)) ** (2 * orden))
    r = FREC.astype(np.float64) / mhz(max(0.3, centro - 1.7 * ancho))
    pasaaltos = r**4 / np.sqrt(1 + r**8)
    return (campana * pasaaltos).astype(np.float32)


def realce(centro: float, ancho: float, ganancia: float) -> np.ndarray:
    """Una loma en el espectro: el «peaking» que afila los bordes y deja su halo. Sin ganancia en la continua:
    afila, no aclara."""
    loma = np.exp(-(((FREC - mhz(centro)) / mhz(ancho)) ** 2))
    return (1 + ganancia * (loma - loma[0])).astype(np.float32)


def corrimiento(d) -> np.ndarray:
    """Un retraso (en muestras) como fase: un número para todas las líneas o uno por línea."""
    d = np.asarray(d, dtype=np.float32)
    if d.ndim == 0:
        return np.exp(-2j * np.pi * FREC * d).astype(np.complex64)
    return np.exp(-2j * np.pi * FREC[None, :] * d[:, None]).astype(np.complex64)


def _previa(x: np.ndarray) -> np.ndarray:
    """La línea anterior de cada línea. La primera no tiene: usa la segunda, que trae el color con la misma fase
    invertida que tendría la anterior (si se usara a sí misma, el peine le borraría el color)."""
    return np.vstack([x[1:2], x[:-1]])


# ── El color: YIQ y la subportadora ─────────────────────────────────────────

A_YIQ = np.array([[0.299, 0.587, 0.114], [0.5959, -0.2746, -0.3213], [0.2115, -0.5227, 0.3112]], np.float32)
A_RGB = np.linalg.inv(A_YIQ).astype(np.float32)
# La fase de la subportadora en cada muestra: 227,5 ciclos por línea entera, así que cada línea empieza
# medio ciclo corrida respecto de la anterior, y cada cuadro (525 líneas) respecto del anterior. Por eso
# los puntos del color que se cuela en la luma «caminan» (dot crawl).
_FASE = 2 * np.pi * mhz(FSC) * np.arange(MUESTRAS)[None, :] + np.pi * np.arange(LINEAS)[:, None]
COS = np.cos(_FASE).astype(np.float32)
SIN = np.sin(_FASE).astype(np.float32)


def a_yiq(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    yiq = rgb @ A_YIQ.T
    return yiq[..., 0].copy(), yiq[..., 1].copy(), yiq[..., 2].copy()


def a_rgb(y: np.ndarray, i: np.ndarray, q: np.ndarray) -> np.ndarray:
    return np.stack([y, i, q], axis=-1) @ A_RGB.T


def color_yiq(hexa: str) -> np.ndarray:
    rgb = np.array([int(hexa[k:k + 2], 16) / 255 for k in (1, 3, 5)], np.float32)
    return A_YIQ @ rgb


def codificar(y: np.ndarray, i: np.ndarray, q: np.ndarray, k: int) -> np.ndarray:
    """Componentes → señal compuesta: el codificador limita la luma a 4,2 MHz, I a 1,3 y Q a 0,5."""
    y = filtrar(y, pasabajos(4.2, 3))
    i = filtrar(i, pasabajos(1.3, 2))
    q = filtrar(q, pasabajos(0.5, 2))
    s = 1.0 if k % 2 == 0 else -1.0
    return y + s * (i * COS + q * SIN)


def decodificar(c: np.ndarray, k: int, modo: str = "peine", color: float = 1.0):
    """Compuesta → componentes. `muesca`: el color es lo que cae cerca de la subportadora (el televisor
    barato: la luma pierde detalle y los bordes dejan arcoíris). `peine`: resta la línea anterior, donde el
    color viene con la fase al revés (más fino; deja puntos colgando en los bordes horizontales)."""
    if modo == "peine":
        croma = filtrar((c - _previa(c)) * 0.5, pasabanda(FSC, 1.4, 2))
    else:
        croma = filtrar(c, pasabanda(FSC, 1.3, 2))
    y = filtrar(c - croma, pasabajos(4.2, 3))
    s = 2.0 if k % 2 == 0 else -2.0
    i = filtrar(croma * COS * s, pasabajos(1.3, 2)) * color
    q = filtrar(croma * SIN * s, pasabajos(0.5, 2)) * color
    return y, i, q


class Senal:
    """La señal de un cuadro: en componentes (y, i, q) o compuesta (c)."""

    def __init__(self, y, i, q, k: int):
        self.y, self.i, self.q, self.c = y, i, q, None
        self.k = k
        self.color = 1.0          # lo baja la antena cuando el televisor apaga el color
        self.sale_compuesta = False

    def componentes(self, modo: str = "peine") -> Senal:
        if self.c is not None:
            self.y, self.i, self.q = decodificar(self.c, self.k, modo, self.color)
            self.c = None
        return self

    def compuesta(self) -> Senal:
        if self.c is None:
            self.c = codificar(self.y, self.i, self.q, self.k)
            self.y = self.i = self.q = None
        return self


# ── El tiempo: lo que cambia despacio y lo que pasa de vez en cuando ────────

def _num(x) -> int:
    return x if isinstance(x, int) else zlib.crc32(str(x).encode())


def suave(semilla: int, nombre: str, t: float, base: float = 0.3, octavas: int = 3) -> float:
    """Ruido suave en el tiempo, entre −1 y 1: senos con frecuencias y fases fijas por semilla. No guarda
    estado: el valor en un segundo no depende de haber pasado por los anteriores."""
    r = np.random.default_rng([semilla, _num(nombre)])
    total, amp, norma = 0.0, 1.0, 0.0
    for o in range(octavas):
        f = base * (2**o) * (0.7 + 0.6 * r.random())
        total += amp * math.sin(2 * math.pi * f * t + 2 * math.pi * r.random())
        norma += amp
        amp *= 0.5
    return total / norma


def evento(semilla: int, nombre: str, t: float, por_minuto: float, dura: float) -> float | None:
    """¿Hay un evento en el segundo t? Devuelve en qué parte va (0 a 1) o None. Unos `por_minuto` eventos
    de `dura` segundos, repartidos al azar en ranuras de dos veces su duración."""
    if por_minuto <= 0:
        return None
    ranura = 2 * dura
    p = min(1.0, por_minuto / 60 * ranura)
    n = math.floor(t / ranura)
    for s in (n, n - 1):
        r = np.random.default_rng([semilla, _num(nombre), s + 1_000_000])
        if r.random() < p:
            inicio = (s + r.random()) * ranura
            if inicio <= t < inicio + dura:
                return (t - inicio) / dura
    return None


class Contexto:
    """Lo que un aparato sabe del cuadro: cuál es, en qué segundo, su semilla, y lo que recuerda del anterior."""

    def __init__(self, semilla: int, fps: float, alto: int, ancho: int):
        self.semilla, self.fps, self.alto, self.ancho = semilla, fps, alto, ancho
        self.aspecto = ancho / alto          # el de la imagen que se ve, no el de la grilla de muestras
        self.k, self.t, self.paso = 0, 0.0, 0
        self.estado: dict = {}
        # Cómo vuelve a la salida una imagen de otro tamaño (la del sensor de un celular): con barras o llenando,
        # y ampliada suave o con sus pixeles. Lo fija el sensor en cada cuadro.
        self.encuadre = ("barras", "suave")
        # Los golpes de la canción (beats, primeros_tiempos, energia, bpm), para lo que va al pulso; o None.
        self.musica: dict | None = None
        # El segundo de la entrada en que empieza la salida (con `--desde`): lo que es «al principio del video»
        # (la casetera que arranca) cuenta desde ahí; lo demás usa el segundo de la entrada (`t`).
        self.inicio = 0.0
        # El segundo de la entrada en que termina la salida: lo que es «al final del video» (la cola del rollo que se
        # acaba). None si no se sabe (un cuadro suelto).
        self.fin: float | None = None
        # El video que entra (el osciloscopio lee su audio). None si no se sabe.
        self.entrada = None
        # El cuadro como entró a la cadena, antes de cualquier aparato (lo pone `procesar_cuadro`).
        self.original = None

    def rng(self, *extra) -> np.random.Generator:
        return np.random.default_rng([self.semilla, self.paso, self.k, *(_num(x) for x in extra)])

    def suave(self, nombre: str, base: float = 0.3) -> float:
        return suave(self.semilla * 100 + self.paso, nombre, self.t, base)


def _ruido(rng: np.random.Generator, forma: np.ndarray, sigma: float, filas: int = LINEAS) -> np.ndarray:
    """Ruido con el espectro `forma` en cada línea (sin correlación entre líneas) y desvío `sigma`."""
    e = (rng.standard_normal((filas, len(FREC)), dtype=np.float32)
         + 1j * rng.standard_normal((filas, len(FREC)), dtype=np.float32)) * forma
    x = np.fft.irfft(e, n=N_FFT, axis=1)[:, :MUESTRAS]
    return (x * (sigma / (x.std() + 1e-12))).astype(np.float32)


# ── Los aparatos ────────────────────────────────────────────────────────────

FORMATOS = {
    # luma: ancho de banda de la luma (MHz); croma: del color rebajado (color-under); retraso: cuánto llega tarde
    # el color (muestras); ruido: desvío del ruido de luma y de croma (fracción del blanco). SP, LP y EP siguen a
    # los simuladores de código abierto (ntsc-rs, composite-video-simulator), que bajan el corte con la velocidad
    # de la cinta; los demás formatos, sus cifras nominales. Fuentes en direccion/ANALOGO.md.
    "SP": {"luma": 2.8, "croma": 0.32, "retraso": 4.0, "ruido": 0.010, "ruido_croma": 0.018},
    "LP": {"luma": 2.2, "croma": 0.30, "retraso": 5.0, "ruido": 0.014, "ruido_croma": 0.030},
    "EP": {"luma": 1.7, "croma": 0.28, "retraso": 6.0, "ruido": 0.019, "ruido_croma": 0.036},
    "S-VHS": {"luma": 5.0, "croma": 0.40, "retraso": 3.0, "ruido": 0.008, "ruido_croma": 0.020},
    "Betamax": {"luma": 3.2, "croma": 0.40, "retraso": 3.0, "ruido": 0.009, "ruido_croma": 0.022},
    "Video8": {"luma": 3.0, "croma": 0.40, "retraso": 4.0, "ruido": 0.011, "ruido_croma": 0.024},
    "Hi8": {"luma": 4.6, "croma": 0.45, "retraso": 3.0, "ruido": 0.009, "ruido_croma": 0.020},
}
TINTAS_CURIANA = ["#07090d", "#26396a", "#2154c5", "#c36712", "#e6b43c", "#f3ead4"]
LUGARES = ("arriba-izquierda", "arriba-derecha", "abajo-izquierda", "abajo-derecha", "centro")

POR_DEFECTO: dict[str, dict] = {
    "camara": {"mancha": 0.5, "blancos": 0.86, "balance": 0.3, "detalle": 0.4, "ruido": 0.3, "estela": 0.0, "sonido": "ninguno"},
    "osd": {"textos": [], "fecha": "1994-10-12", "hora": "19:42:00"},
    "cinta": {"formato": "SP", "generaciones": 1, "desgaste": 0.2, "temblor": 0.5, "tracking": 0.0, "cabezal": 1.0,
              "cabezal_lineas": 8, "realce": 0.6, "retraso_croma": None, "saturacion": 1.0, "tono": 2.0,
              "arrugas": 0.0, "svideo": False, "sonido": "ninguno"},
    "antena": {"nieve": 0.06, "fantasma": [], "interferencia": [], "zumbido": 0.0, "rodar": 0.0, "desenganche": 0.0,
               "sonido": "ninguno"},
    "tbc": {"fuerza": 1.0, "brillo": 0.0, "contraste": 1.0, "color": 1.0, "tono": 0.0},
    "colorizador": {"tintas": TINTAS_CURIANA, "bandas": 0, "mezcla": 1.0},
    "iman": {"fuerza": 0.6, "radio": 0.32, "velocidad": 0.12, "ondas": 0.0},
    "relieve": {"lineas": 110, "altura": 36.0, "mezcla": 0.0, "brillo": 1.0},
    "realimentacion": {"mezcla": 0.8, "zoom": 0.95, "giro": 2.0, "tono": 10.0, "contraste": 1.05, "modo": "aclarar"},
    "pantalla": {"lineas": 0.65, "mascara": "rejilla", "mascara_fuerza": 0.3, "curva": 0.05, "brillo": 0.3,
                 "persistencia": 0.0, "convergencia": 0.6, "blanco": 9300, "vineta": 0.35, "gamma": 2.4,
                 "decodificador": "muesca", "parpadeo": 0.0, "sonido": "ninguno"},
}
#: Lo que vale cada perilla: (mínimo, máximo) para números, o los valores posibles.
RANGOS: dict[str, dict] = {
    "camara": {"mancha": (0, 2), "blancos": (0.5, 1), "balance": (0, 1), "detalle": (0, 2), "ruido": (0, 2), "estela": (0, 0.95),
               "sonido": ("ninguno", "microfono")},   # los ruidos de la cámara, la antena y la pantalla: ruidos.py
    "cinta": {"formato": tuple(FORMATOS), "generaciones": (1, 6), "desgaste": (0, 1), "temblor": (0, 3),
              "tracking": (0, 1), "cabezal": (0, 3), "cabezal_lineas": (0, 30), "realce": (0, 2),
              "retraso_croma": (-20, 20), "saturacion": (0, 2), "tono": (0, 30), "arrugas": (0, 30),
              "sonido": ("ninguno", "lineal", "hifi")},
    "antena": {"nieve": (0, 1), "zumbido": (0, 0.5), "rodar": (-2, 2), "desenganche": (0, 1), "sonido": ("ninguno", "aire")},
    "tbc": {"fuerza": (0, 1), "brillo": (-0.3, 0.3), "contraste": (0.5, 1.5), "color": (0, 2), "tono": (-45, 45)},
    "colorizador": {"bandas": (0, 16), "mezcla": (0, 1)},
    "iman": {"fuerza": (0, 2), "radio": (0.05, 1), "velocidad": (0, 2), "ondas": (0, 2)},
    "relieve": {"lineas": (20, 240), "altura": (0, 120), "mezcla": (0, 1), "brillo": (0.2, 3)},
    "realimentacion": {"mezcla": (0, 0.98), "zoom": (0.8, 1.2), "giro": (-20, 20), "tono": (-60, 60),
                       "contraste": (0.8, 1.4), "modo": ("aclarar", "fundir")},
    "pantalla": {"lineas": (0, 1), "mascara": ("rejilla", "puntos", "ranuras", "ninguna"), "mascara_fuerza": (0, 1),
                 "curva": (0, 0.2), "brillo": (0, 1.5), "persistencia": (0, 0.9), "convergencia": (0, 4),
                 "blanco": (6500, 9300), "vineta": (0, 1), "gamma": (2.0, 2.8), "decodificador": ("muesca", "peine"),
                 "parpadeo": (0, 1), "sonido": ("ninguno", "parlante")},
}


def _cinta_base_de_tiempo(p: dict, ctx: Contexto, rng: np.random.Generator, g: int) -> tuple[np.ndarray, np.ndarray]:
    """Cuánto se corre cada línea (en muestras) y cuánto tracking perdido tiene cada una (0 a 1)."""
    d = np.zeros(LINEAS, np.float32)
    tbc_ = p.get("_tbc", 0.0)
    tb = p["temblor"] * (1 - tbc_)
    if tb > 0:
        # La cinta que se estira: unas pocas ondas a lo alto del cuadro, que cambian despacio («edge wave»).
        r = np.random.default_rng([ctx.semilla, _num("ondas"), ctx.paso, g])
        for _ in range(3):
            largo, vel, amp, fase = r.uniform(70, 420), r.uniform(0.2, 1.4), r.uniform(0.5, 1.0), r.uniform(0, 2 * np.pi)
            d += amp * np.sin(2 * np.pi * (LINEA / largo + vel * ctx.t) + fase)
        d *= 0.9 * tb
        # El temblor de línea a línea (el servo del cabezal no es perfecto).
        j = rng.standard_normal(LINEAS).astype(np.float32) * 0.4 * tb
        d += 0.5 * (j + np.concatenate([j[:1], j[:-1]]))
        # La bandera: las primeras líneas se tuercen hacia un lado (la tensión de la cinta, «flagging»).
        b = (3.0 + 2.0 * ctx.suave(f"bandera{g}", 0.4)) * tb * 2.0
        d += b * np.clip(1 - LINEA / 16, 0, 1) ** 2
    # El cambio de cabezal: en las últimas líneas un cabezal le pasa la cinta al otro y la línea salta de lado.
    n = int(round(p["cabezal_lineas"]))
    if p["cabezal"] > 0 and n:
        z = np.clip((LINEA - (LINEAS - n) + 1) / n, 0, 1)
        d += z**1.5 * p["cabezal"] * (48 + 8 * float(rng.standard_normal())) * (1 - 0.8 * tbc_)
        d += (z > 0) * rng.uniform(-0.5, 0.5, LINEAS).astype(np.float32)
    # El tracking perdido: una franja de líneas rotas abajo, que sube y se pasea cuando es grande.
    w = np.zeros(LINEAS, np.float32)
    tr = p["tracking"]
    if tr > 0:
        presencia = tr * float(np.clip(0.6 + 0.9 * ctx.suave(f"tracking{g}", 0.12), 0, 1))
        if presencia > 0.02:
            alto = 6 + 34 * tr
            sube = max(0.0, tr - 0.4) / 0.6 * (0.5 + 0.5 * ctx.suave(f"tracksube{g}", 0.07))
            centro = LINEAS - alto * 0.6 - sube * (LINEAS - alto)
            w = np.exp(-(((LINEA - centro) / alto) ** 2)).astype(np.float32)
            w = np.where(LINEA > centro, np.maximum(w, 0.6 * (LINEA > LINEAS - alto)), w) * presencia
            onda = 15 * np.sin(2 * np.pi * (LINEA / 37 + 2.3 * ctx.t))
            d += w * (onda + rng.standard_normal(LINEAS).astype(np.float32) * 10)
    # Más allá del borde reflejado el corrimiento daría la vuelta por el otro lado de la línea.
    return np.clip(d, -RELLENO + 8, RELLENO - 8), w.astype(np.float32)


def _dropouts(y, i, q, rng: np.random.Generator, n: int, largo_medio: float) -> None:
    """Rayas blancas: donde a la cinta le falta óxido el cabezal no lee nada; el destello se apaga hacia la derecha."""
    for _ in range(n):
        fila = int(rng.integers(0, LINEAS))
        largo = int(np.clip(rng.exponential(largo_medio), 6, 160))
        x0 = int(rng.integers(-largo // 2, MUESTRAS))
        a, b = max(0, x0), min(MUESTRAS, x0 + largo)
        if b <= a:
            continue
        x = np.arange(a, b) - x0
        w = (np.clip(x / 2, 0, 1) * (1 - x / largo) ** 2).astype(np.float32)
        brillo = 0.75 + 0.25 * rng.random()
        for f in range(fila, min(LINEAS, fila + int(rng.integers(1, 3)))):
            y[f, a:b] = y[f, a:b] * (1 - w) + w * (brillo + 0.06 * rng.standard_normal(b - a))
            i[f, a:b] *= 1 - w
            q[f, a:b] *= 1 - w


def cinta(s: Senal, p: dict, ctx: Contexto) -> Senal:
    s.componentes("peine")     # el VCR separa la entrada compuesta con su propio filtro de peine
    y, i, q = s.y, s.i, s.q
    f = FORMATOS[p["formato"]]
    desg = p["desgaste"]
    arruga = evento(ctx.semilla, "arruga", ctx.t, p["arrugas"], 0.3)
    e_arr = math.sin(math.pi * arruga) if arruga is not None else 0.0
    for g in range(int(p["generaciones"])):
        rng = ctx.rng("cinta", g)
        if g:  # una copia: el VCR que graba recibe la salida compuesta del que reproduce
            y, i, q = decodificar(codificar(y, i, q, ctx.k), ctx.k, "peine")
        d, w = _cinta_base_de_tiempo(p, ctx, rng, g)
        if e_arr:
            d += e_arr * rng.standard_normal(LINEAS).astype(np.float32) * 12
        fase = corrimiento(d)
        # Los niveles: el negro se levanta un poco y el blanco se dobla antes de cortar.
        y = 0.02 + 0.97 * y
        y = np.where(y < 0.92, y, 0.92 + 0.08 * np.tanh((y - 0.92) / 0.08))
        # Luma: el ancho de banda de la cinta y el realce de bordes del VCR (que deja su halo).
        y = _senal(_espectro(y) * pasabajos(f["luma"], 2) * realce(0.7 * f["luma"], 0.4 * f["luma"], p["realce"]) * fase)
        forma = (FREC / mhz(f["luma"]) + 0.15) * pasabajos(f["luma"], 2)   # el ruido de FM crece con la frecuencia
        y += _ruido(rng, forma, f["ruido"] * (1 + 2.0 * desg))
        # Color: el VCR promedia dos líneas y graba el color en una banda angosta; un filtro de verdad arrastra
        # lo que borra hacia la derecha, y el color llega un poco tarde respecto de la luma.
        retraso = f["retraso"] if p["retraso_croma"] is None else p["retraso_croma"]
        hc = pasabajos_causal(f["croma"], 2) * fase * corrimiento(retraso)
        i = _senal(_espectro(0.5 * (i + _previa(i))) * hc)
        q = _senal(_espectro(0.5 * (q + _previa(q))) * hc)
        forma_c = pasabajos(0.25, 1)
        rc = f["ruido_croma"] * (1 + 2.5 * desg)
        ni, nq = _ruido(rng, forma_c, rc), _ruido(rng, forma_c, rc)
        i += 0.5 * (ni + _previa(ni))
        q += 0.5 * (nq + _previa(nq))
        # El tono que se corre despacio y la saturación.
        ang = math.radians(p["tono"]) * ctx.suave(f"tono{g}", 0.05)
        ca, sa = math.cos(ang), math.sin(ang)
        i, q = (ca * i - sa * q) * p["saturacion"], (sa * i + ca * q) * p["saturacion"]
        # Las líneas del cambio de cabezal: ruido y color perdido.
        n = int(round(p["cabezal_lineas"]))
        if p["cabezal"] > 0 and n:
            z = np.clip((LINEA - (LINEAS - n)) / n, 0, 1)[:, None] * min(1.0, p["cabezal"])
            y = y * (1 - 0.5 * z) + z * (0.35 + 0.25 * rng.standard_normal((LINEAS, MUESTRAS), dtype=np.float32))
            i, q = i * (1 - z), q * (1 - z)
        # La franja del tracking perdido: luz rota, chispas blancas, sin color.
        if w.any():
            ww = w[:, None]
            chispas = _ruido(rng, forma, 0.22) + 0.45 + (rng.random((LINEAS, MUESTRAS), dtype=np.float32) > 0.985) * 0.6
            y = y * (1 - 0.85 * ww) + 0.85 * ww * chispas
            i, q = i * (1 - ww), q * (1 - ww)
        # Dropouts: más cuanto más gastada la cinta, y muchos en una arruga.
        _dropouts(y, i, q, rng, int(rng.poisson(0.15 + 5 * desg**2 + 40 * e_arr)), 14 + 30 * desg)
        # Líneas que pierden el color un instante (el color rebajado se cae).
        sin_croma = rng.random(LINEAS) < 0.0004 + 0.004 * desg
        if sin_croma.any():
            i[sin_croma], q[sin_croma] = 0.0, 0.0
    if e_arr:
        salto = int(round(e_arr * float(np.random.default_rng([ctx.semilla, _num("salto"), int(ctx.t / 0.6)]).integers(-14, 15))))
        y, i, q = (np.roll(x, salto, axis=0) for x in (y, i, q))
        i, q = i * (1 - 0.7 * e_arr), q * (1 - 0.7 * e_arr)
    s.y, s.i, s.q = y, i, q
    s.sale_compuesta = not p["svideo"]
    return s


#: La pista lineal de audio del VHS (graves, agudos en Hz) por formato: la cinta más lenta pierde agudos.
#: [sin verificar] en una fuente leída: cifras de catálogo de época, ver direccion/ANALOGO.md.
BANDA_LINEAL = {"SP": (90, 10000), "LP": (100, 7000), "EP": (110, 5000)}
SR_AUDIO = 48000


def sonido_de_cinta(x: np.ndarray, p: dict, semilla: int, t0: float, sr: int = SR_AUDIO, indice: int = 0) -> np.ndarray:
    """El audio (n × canales, −1…1) pasado por la misma cinta que la imagen: la velocidad que tiembla (wow y
    flutter: el sonido se estira y se encoge), y en la pista `lineal` la banda angosta, casi mono, el silbido y
    la saturación de la cinta; `hifi` (en el tambor, en FM) es casi limpio. Las arrugas hunden el sonido en los
    mismos instantes en que hacen saltar la imagen."""
    from scipy.signal import butter, sosfilt

    if p["sonido"] == "ninguno" or len(x) < 64:   # unas muestras sueltas no son sonido (y el silbido se iría al infinito)
        return x
    n = len(x)
    t = t0 + np.arange(n) / sr
    desg = p["desgaste"]
    # Wow (lento) y flutter (rápido): desviaciones de velocidad de unas décimas de por ciento.
    r = np.random.default_rng([semilla, _num("wow"), indice])
    desfase = np.zeros(n)
    for f, desvio in ((0.55, 0.0022), (1.3, 0.0011), (7.5, 0.0005), (13.0, 0.00025)):
        desvio *= (0.4 + p["temblor"]) * (1 + desg) * (1.0 if p["sonido"] == "lineal" else 0.5)
        desfase += desvio / (2 * np.pi * f) * np.sin(2 * np.pi * f * t + r.uniform(0, 2 * np.pi))
    pos = np.clip((t - t0 + desfase) * sr, 0, n - 1)
    y = np.stack([np.interp(pos, np.arange(n), x[:, c]) for c in range(x.shape[1])], axis=1)
    g = int(p["generaciones"])
    if p["sonido"] == "lineal":
        bajo, alto = BANDA_LINEAL.get(p["formato"], (80, 12000))
        alto = alto / (1 + 0.15 * (g - 1))
        y = sosfilt(butter(2, [bajo, alto], btype="bandpass", fs=sr, output="sos"), y, axis=0)
        if y.shape[1] == 2:  # la pista lineal de casa era casi mono
            medio, lado = (y[:, 0] + y[:, 1]) / 2, (y[:, 0] - y[:, 1]) / 2 * 0.3
            y = np.stack([medio + lado, medio - lado], axis=1)
        y = np.tanh(1.3 * y) / 1.3                # la cinta satura con suavidad: lo suave pasa igual, los picos se doblan
        silbido_db = -52 + 12 * desg + 3 * (g - 1)
    else:
        silbido_db = -72 + 6 * desg
    ruido = np.random.default_rng([semilla, _num("silbido"), indice]).standard_normal(y.shape)
    ruido = sosfilt(butter(2, [1500, min(15000, sr / 2 - 100)], btype="bandpass", fs=sr, output="sos"), ruido, axis=0)
    y = y + ruido / (ruido.std() + 1e-12) * 10 ** (silbido_db / 20)
    if p["arrugas"]:  # la arruga: el sonido se hunde y se apaga mientras la imagen salta
        rejilla = np.arange(t0, t[-1] + 0.01, 0.01)
        e = np.array([math.sin(math.pi * u) if (u := evento(semilla, "arruga", s, p["arrugas"], 0.3)) is not None else 0.0
                      for s in rejilla])
        e = np.interp(t, rejilla, e)[:, None]
        apagado = sosfilt(butter(2, 1200, btype="lowpass", fs=sr, output="sos"), y, axis=0)
        y = (y * (1 - e) + apagado * e) * (1 - 0.6 * e)
    return y.astype(np.float32)


def antena(s: Senal, p: dict, ctx: Contexto) -> Senal:
    s.compuesta()
    c = s.c
    rng = ctx.rng("antena")
    ecos = p["fantasma"]
    if ecos:  # la señal que rebota en un cerro o un edificio llega un poco después, más débil
        h = np.ones_like(FREC, dtype=np.complex64)
        for retraso, amplitud in ecos:
            h = h + amplitud * corrimiento(muestras_us(retraso))
        # El control automático de ganancia del televisor devuelve el nivel: el eco no aclara la imagen.
        c = _senal(_espectro(c) * h) / (1 + sum(abs(a) for _, a in ecos))
    for frecuencia, amplitud in p["interferencia"]:  # una portadora ajena: rayas diagonales que se mueven
        fase = (2 * np.pi * mhz(frecuencia) * np.arange(MUESTRAS)[None, :]
                + 2 * np.pi * frecuencia * PERIODO_US * np.arange(LINEAS)[:, None] + 2 * np.pi * 0.37 * ctx.t * frecuencia)
        c = c + amplitud * np.sin(fase).astype(np.float32)
    if p["zumbido"]:  # 60 Hz de la red contra 59,94 campos por segundo: una barra que sube cada ~17 s
        c = c + p["zumbido"] * np.sin(2 * np.pi * (LINEA / LINEAS + 0.06 * ctx.t))[:, None].astype(np.float32)
    if p["nieve"]:
        c = c + p["nieve"] * rng.standard_normal(c.shape, dtype=np.float32)
        # Con la señal débil el televisor apaga el color; cerca del umbral, el color va y viene.
        umbral = 0.16
        if p["nieve"] >= umbral:
            s.color = 0.0
        elif p["nieve"] > umbral - 0.06:
            lado = (p["nieve"] - (umbral - 0.06)) / 0.06
            s.color = 0.0 if np.random.default_rng([ctx.semilla, _num("killer"), int(ctx.t * 3)]).random() < lado else 1.0
    if p["desenganche"]:  # sin sincronismo horizontal: las líneas se corren y el borrado cruza en diagonal
        total = MUESTRAS + BORRADO
        o = ((p["desenganche"] * 9 * LINEA + 211 * ctx.t * p["desenganche"]) % total).astype(int)
        ext = np.hstack([c, np.full((LINEAS, BORRADO), -0.05, np.float32)])
        c = np.take_along_axis(ext, (np.arange(MUESTRAS)[None, :] + o[:, None]) % total, axis=1)
    if p["rodar"]:  # sin sincronismo vertical: la imagen rueda y se ve la barra del borrado
        total = LINEAS + BORRADO_V
        o = int(round((p["rodar"] * ctx.t * total) % total))
        o -= o % 2   # de a dos líneas: la fase de la subportadora se invierte en cada una, y el color también
        barra = np.full((BORRADO_V, MUESTRAS), -0.05, np.float32)
        barra[BORRADO_V // 3:BORRADO_V // 3 + 6] = 0.18   # el pulso de sincronismo vertical, gris en pantalla
        c = np.roll(np.vstack([c, barra]), o, axis=0)[:LINEAS]
    s.c = c
    return s


def tbc(s: Senal, p: dict, ctx: Contexto) -> Senal:
    """La base de tiempo la corrige al preparar la cadena (`_tbc` en la cinta de antes); aquí, el procesador."""
    s.componentes("peine")
    s.y = (s.y - 0.5) * p["contraste"] + 0.5 + p["brillo"]
    a = math.radians(p["tono"])
    ca, sa = math.cos(a) * p["color"], math.sin(a) * p["color"]
    s.i, s.q = ca * s.i - sa * s.q, sa * s.i + ca * s.q
    return s


def camara(s: Senal, p: dict, ctx: Contexto) -> Senal:
    from scipy import ndimage

    s.componentes()
    y0, i, q = s.y, s.i, s.q
    rng = ctx.rng("camara")
    y = y0
    if p["detalle"]:  # la corrección de apertura: bordes afilados con su halo
        y = y + p["detalle"] * (y - ndimage.gaussian_filter(y, (0.9, 1.6)))
    if p["mancha"]:  # una luz fuerte satura el CCD y deja su columna clara de arriba abajo
        exceso = np.clip(y0 - 0.9, 0, None).mean(axis=0)
        y = y + ndimage.gaussian_filter1d(exceso, 1.5)[None, :] * 9 * p["mancha"]
    b = p["blancos"]
    if b < 1:  # el blanco se dobla, y las luces pierden el color
        y = np.where(y < b, y, b + (1 - b) * np.tanh((y - b) / (1 - b)))
        apaga = np.clip((y - b) / (1 - b), 0, 1)
        i, q = i * (1 - apaga), q * (1 - apaga)
    if p["balance"]:  # el balance automático de blancos se corre despacio
        i = i + 0.05 * p["balance"] * ctx.suave("balance-i", 0.08)
        q = q + 0.035 * p["balance"] * ctx.suave("balance-q", 0.06)
    if p["estela"]:  # el tubo de la cámara (vidicón) tarda en olvidar lo claro: colas de cometa
        clave = ("estela", ctx.paso)
        antes = ctx.estado.get(clave)
        if antes is not None:
            ya, ia, qa = antes
            gana = ya * p["estela"] > y
            y = np.where(gana, ya * p["estela"], y)
            i = np.where(gana, ia * p["estela"], i)
            q = np.where(gana, qa * p["estela"], q)
        ctx.estado[clave] = (y, i, q)
    if p["ruido"]:  # la ganancia sube en lo oscuro y con ella el ruido
        sombra = (1 - np.clip(y, 0, 1)) ** 2
        y = y + rng.standard_normal(y.shape, dtype=np.float32) * 0.025 * p["ruido"] * sombra
        i = i + rng.standard_normal(y.shape, dtype=np.float32) * 0.02 * p["ruido"] * sombra
    s.y, s.i, s.q = y, i, q
    return s


_FUENTE_OSD = RAIZ / "fuentes" / "ibm-plex-mono" / "IBMPlexMono-Bold.ttf"
_MESES = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]


def _texto_osd(texto: str, p: dict, t: float) -> str:
    if "{fecha}" in texto:
        a, m, d = (int(x) for x in p["fecha"].split("-"))
        texto = texto.replace("{fecha}", f"{_MESES[m - 1]}.{d:2d} {a}")
    if "{hora}" in texto:
        h, mi, se = (int(x) for x in p["hora"].split(":"))
        total = int(h * 3600 + mi * 60 + se + t)
        texto = texto.replace("{hora}", f"{total // 3600 % 24:2d}:{total // 60 % 60:02d}:{total % 60:02d}")
    return texto


def _mascara_osd(texto: str, cache: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """El texto como lo dibuja un aparato: letras gruesas de pocos puntos, con su borde negro. Devuelve el
    relleno, el borde y el color de cada punto (blanco; el ● rojo)."""
    if texto in cache:
        return cache[texto]
    from PIL import Image, ImageDraw, ImageFont

    fuente = ImageFont.truetype(str(_FUENTE_OSD), 11)
    ancho = max(8, int(fuente.getlength("".join("  " if c in "▶◀●‖" else c for c in texto))) + 10)
    img = Image.new("L", (ancho, 16), 0)
    rojo = Image.new("L", (ancho, 16), 0)
    dib, dib_r = ImageDraw.Draw(img), ImageDraw.Draw(rojo)
    x = 2
    for ch in texto:
        if ch == "▶":
            dib.polygon([(x + 1, 3), (x + 1, 12), (x + 9, 7.5)], fill=255)
            x += 12
        elif ch == "◀":
            dib.polygon([(x + 9, 3), (x + 9, 12), (x + 1, 7.5)], fill=255)
            x += 10
        elif ch == "‖":
            dib.rectangle([x + 1, 3, x + 3, 12], fill=255)
            dib.rectangle([x + 6, 3, x + 8, 12], fill=255)
            x += 12
        elif ch == "●":
            dib.ellipse([x + 1, 3, x + 9, 11], fill=255)
            dib_r.ellipse([x + 1, 3, x + 9, 11], fill=255)
            x += 12
        else:
            dib.text((x, 1), ch, font=fuente, fill=255)
            x += fuente.getlength(ch)
    # Letras de pocos puntos: a la mitad de la grilla y de vuelta, sin suavizar.
    img = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
    rojo = rojo.resize(img.size, Image.NEAREST)
    a = (np.asarray(img, np.float32) / 255 > 0.45).astype(np.float32)
    from scipy import ndimage

    borde = np.clip(ndimage.maximum_filter(a, size=3) - a, 0, 1)
    cache[texto] = (a, borde, np.asarray(rojo, np.float32) / 255 > 0.45)
    return cache[texto]


def osd(s: Senal, p: dict, ctx: Contexto) -> Senal:
    s.componentes()
    s.y, s.i, s.q = s.y.copy(), s.i.copy(), s.q.copy()   # lo de antes puede ser la memoria de otro aparato
    cache = ctx.estado.setdefault(("osd", ctx.paso), {})
    rojo = color_yiq("#e8382c")
    for item in p["textos"]:
        if not (item.get("desde", 0) <= ctx.t < item.get("hasta", 1e9)):
            continue
        if item.get("parpadea") and int(ctx.t * 2) % 2:
            continue
        a, borde, es_rojo = _mascara_osd(_texto_osd(item["texto"], p, ctx.t), cache)
        h, w = a.shape
        lugar = item.get("lugar", "arriba-izquierda")
        y0 = 26 if lugar.startswith("arriba") else LINEAS - 26 - h - 18 * item.get("fila", 0) if lugar.startswith("abajo") else (LINEAS - h) // 2
        if lugar.startswith("arriba"):
            y0 += 18 * item.get("fila", 0)
        x0 = 44 if lugar.endswith("izquierda") else MUESTRAS - 44 - w if lugar.endswith("derecha") else (MUESTRAS - w) // 2
        y0, x0 = int(np.clip(y0, 0, LINEAS - h)), int(np.clip(x0, 0, MUESTRAS - w))
        sl = (slice(y0, y0 + h), slice(x0, x0 + w))
        s.y[sl] = s.y[sl] * (1 - 0.85 * borde)
        s.y[sl] = s.y[sl] * (1 - a) + a * np.where(es_rojo, rojo[0], 0.92)
        s.i[sl] = s.i[sl] * (1 - a) + a * np.where(es_rojo, rojo[1], 0)
        s.q[sl] = s.q[sl] * (1 - a) + a * np.where(es_rojo, rojo[2], 0)
    return s


def colorizador(s: Senal, p: dict, ctx: Contexto) -> Senal:
    s.componentes()
    tintas = np.stack([color_yiq(h) for h in p["tintas"]])
    y = np.clip(s.y, 0, 1)
    if p["bandas"]:
        n = int(p["bandas"])
        y = np.minimum(np.floor(y * n), n - 1) / max(1, n - 1)
    pos = np.linspace(0, 1, len(tintas))
    nuevo = [np.interp(y, pos, tintas[:, c]).astype(np.float32) for c in range(3)]
    m = p["mezcla"]
    s.y, s.i, s.q = (m * n_ + (1 - m) * v for n_, v in zip(nuevo, (s.y, s.i, s.q)))
    return s


def iman(s: Senal, p: dict, ctx: Contexto) -> Senal:
    from scipy import ndimage

    s.componentes()
    filas, cols = np.mgrid[0:LINEAS, 0:MUESTRAS].astype(np.float32)
    v = filas / LINEAS - 0.5
    u = (cols / MUESTRAS - 0.5) * ctx.aspecto          # en el plano de la pantalla, no de la grilla
    cu = 0.3 * ctx.suave("iman-x", p["velocidad"]) * ctx.aspecto
    cv = 0.28 * ctx.suave("iman-y", p["velocidad"] * 0.8)
    du, dv = u - cu, v - cv
    g = p["fuerza"] * np.exp(-(du**2 + dv**2) / p["radio"] ** 2)
    ang = 0.8 * g                                       # el haz se tuerce alrededor del imán
    ca, sa = np.cos(ang), np.sin(ang)
    su, sv = cu + ca * du - sa * dv, cv + sa * du + ca * dv
    fil = (sv + 0.5) * LINEAS
    col = (su / ctx.aspecto + 0.5) * MUESTRAS
    if p["ondas"]:  # el «wobbulator»: bobinas que hacen ondular el barrido
        col = col + p["ondas"] * 9 * np.sin(2 * np.pi * (filas / 55 + 0.7 * ctx.t))
        fil = fil + p["ondas"] * 3 * np.sin(2 * np.pi * (cols / 190 - 0.4 * ctx.t))
    coords = np.array([fil, col])
    y, i, q = (ndimage.map_coordinates(x, coords, order=1, mode="constant", cval=0.0).astype(np.float32)
               for x in (s.y, s.i, s.q))
    # La pureza: el haz pega en el fósforo equivocado y el color se corre de tono cerca del imán. Donde el haz
    # no llega (el imán lo sacó de la pantalla) no hay luz que teñir: el tinte va con el brillo.
    giro = 2.6 * g
    cg, sg = np.cos(giro), np.sin(giro)
    luz = np.clip(y, 0, 1)
    s.y, s.i, s.q = y, cg * i - sg * q + 0.12 * g * luz, sg * i + cg * q - 0.08 * g * luz
    return s


def relieve(s: Senal, p: dict, ctx: Contexto) -> Senal:
    from scipy import ndimage

    s.componentes()
    y = np.clip(ndimage.gaussian_filter(s.y, (1.0, 1.4)), 0, 1)
    n = int(p["lineas"])
    filas = np.linspace(4, LINEAS - 5, n).astype(np.float32)
    xs = np.linspace(0, MUESTRAS - 1, MUESTRAS * 3).astype(np.float32)
    valor = np.stack([np.interp(xs, np.arange(MUESTRAS), y[int(round(f))]) for f in filas])
    pos = filas[:, None] - p["altura"] * valor
    brillo = (0.3 + 0.7 * valor) * p["brillo"]
    r0 = np.floor(pos).astype(int)
    fr = (pos - r0).astype(np.float32)
    xi = np.broadcast_to(xs.astype(int)[None, :], pos.shape)
    ok = (r0 >= 0) & (r0 < LINEAS - 1)
    lienzo = np.zeros((LINEAS, MUESTRAS), np.float32)
    np.add.at(lienzo, (r0[ok], xi[ok]), (brillo * (1 - fr))[ok])
    np.add.at(lienzo, (r0[ok] + 1, xi[ok]), (brillo * fr)[ok])
    lienzo = lienzo / 2.2
    lienzo = lienzo + 0.6 * ndimage.gaussian_filter(lienzo, 1.6)
    m = p["mezcla"]
    s.y = m * s.y + (1 - m) * np.clip(lienzo, 0, 1.3)
    s.i, s.q = s.i * m, s.q * m
    return s


def realimentacion(s: Senal, p: dict, ctx: Contexto) -> Senal:
    from scipy import ndimage

    s.componentes()
    clave = ("realimentacion", ctx.paso)
    antes = ctx.estado.get(clave) or (s.y, s.i, s.q)
    # La cámara mira el monitor: lo de antes, más chico y girado alrededor del centro (en el plano de la
    # pantalla, que no tiene la forma de la grilla de muestras).
    a = math.radians(p["giro"])
    asp = ctx.aspecto * LINEAS / MUESTRAS
    rot = np.array([[math.cos(a), -math.sin(a) * asp], [math.sin(a) / asp, math.cos(a)]], np.float32) / p["zoom"]
    centro = np.array([LINEAS / 2, MUESTRAS / 2], np.float32)
    off = centro - rot @ centro
    ya, ia, qa = (ndimage.affine_transform(x, rot, offset=off, order=1, mode="constant", cval=0.0) for x in antes)
    t = math.radians(p["tono"])
    ia, qa = math.cos(t) * ia - math.sin(t) * qa, math.sin(t) * ia + math.cos(t) * qa
    ya = (ya - 0.5) * p["contraste"] + 0.5
    m = p["mezcla"]
    if p["modo"] == "fundir":
        y, i, q = (1 - m) * s.y + m * ya, (1 - m) * s.i + m * ia, (1 - m) * s.q + m * qa
    else:  # aclarar: lo de antes queda donde es más claro que lo de ahora
        gana = m * ya > s.y
        y, i, q = np.where(gana, m * ya, s.y), np.where(gana, m * ia, s.i), np.where(gana, m * qa, s.q)
    y = np.clip(y, -0.05, 1.1)
    ctx.estado[clave] = (y, i, q)
    s.y, s.i, s.q = y, i, q
    return s


# ── La pantalla: el tubo, al tamaño de salida ───────────────────────────────

#: El haz de electrones, en anchos de línea: fino en lo oscuro, grueso en lo claro (lo que hace que una línea
#: brillante se vea más ancha y las oscuras dejen ver el negro entre líneas).
HAZ_FINO, HAZ_GRUESO = 0.27, 0.47
_GAMMA_16 = ((np.arange(65536) / 65535) ** (1 / 2.2)).astype(np.float32)


def _geometria(p: dict, alto: int, ancho: int) -> dict:
    """Lo que no cambia de un cuadro a otro: dónde cae cada pixel de la pantalla en la grilla de la señal
    (con la curva del vidrio: las líneas se curvan), el perfil del haz ahí, la máscara de fósforos y la viñeta."""
    v, u = np.mgrid[0:alto, 0:ancho].astype(np.float32)
    x = (u + 0.5) / ancho * 2 - 1
    y = (v + 0.5) / alto * 2 - 1
    r2 = x * x + y * y
    xs, ys = x * (1 + p["curva"] * r2), y * (1 + p["curva"] * r2)
    fl = np.clip((ys + 1) / 2 * LINEAS - 0.5, 0, LINEAS - 1.001)
    fc = np.clip((xs + 1) / 2 * MUESTRAS - 0.5, 0, MUESTRAS - 1.001)
    l0 = np.minimum(np.floor(fl).astype(np.int32), LINEAS - 2)
    x0 = np.minimum(np.floor(fc).astype(np.int32), MUESTRAS - 2)
    dy = (fl - l0).astype(np.float32)
    i00 = (l0 * MUESTRAS + x0).ravel()
    geo: dict = {"idx": (i00, i00 + 1, i00 + MUESTRAS, i00 + MUESTRAS + 1), "fx": (fc - x0).astype(np.float32).ravel(),
                 "dy": dy}

    def haz(d: np.ndarray, s: float) -> np.ndarray:
        return (np.exp(-((d / s) ** 2)) / (s * math.sqrt(math.pi))).astype(np.float32)

    h0f, h1f = haz(dy, HAZ_FINO), haz(1 - dy, HAZ_FINO)
    geo.update(h0f=h0f, h1f=h1f, dh0=haz(dy, HAZ_GRUESO) - h0f, dh1=haz(1 - dy, HAZ_GRUESO) - h1f)
    borde = 3.0 / min(alto, ancho)
    dentro = np.clip((1 - np.abs(xs)) / borde, 0, 1) * np.clip((1 - np.abs(ys)) / borde, 0, 1)
    r = 0.06  # las esquinas redondeadas del tubo
    rx = np.maximum(np.abs(xs) - (1 - r), 0) / r
    ry = np.maximum(np.abs(ys) - (1 - r * ancho / alto), 0) / (r * ancho / alto)
    dentro *= np.clip((1 - np.sqrt(rx**2 + ry**2)) * 12, 0, 1)
    vineta = np.clip(1 - p["vineta"] * 0.45 * (xs**2 + ys**2) ** 1.3, 0, 1)
    geo["luz"] = (dentro * vineta).astype(np.float32)
    # La máscara de fósforos está en el vidrio: no se curva con la imagen. Lejos (pocos pixeles por tríada)
    # no se distingue, y se apaga en vez de dejar muaré.
    mf = p["mascara_fuerza"] * float(np.clip((ancho - 1100) / 500, 0, 1)) if p["mascara"] != "ninguna" else 0.0
    geo["mascara"] = None
    if mf:
        col = u.astype(np.int32)
        if p["mascara"] == "puntos":
            col = col + 2 * ((v.astype(np.int32) // 2) % 2)
        tri = np.zeros((3, alto, ancho), np.float32)
        np.put_along_axis(tri, (col % 3)[None], 3.0, axis=0)
        if p["mascara"] == "ranuras":
            tri *= np.where(((v.astype(np.int32) + 2 * ((u.astype(np.int32) // 3) % 2)) % 4) == 0, 0.55, 1.0)[None]
        geo["mascara"] = ((1 - mf) + mf * tri).astype(np.float32)
    # Para ampliar el resplandor (calculado a un cuarto) sin un remuestreo entero en cada cuadro.
    for eje, n in (("f", alto), ("c", ancho)):
        chico = n // 4
        pos = np.clip((np.arange(n) + 0.5) / 4 - 0.5, 0, chico - 1)
        a = np.minimum(np.floor(pos).astype(np.int32), chico - 2)
        geo[f"halo_{eje}"] = (a, a + 1, (pos - a).astype(np.float32))
    return geo


_GEOMETRIAS: dict = {}


def pantalla(s: Senal, p: dict, ctx: Contexto) -> np.ndarray:
    """El tubo, al tamaño de salida. Devuelve RGB de 8 bits (alto, ancho, 3)."""
    from scipy import ndimage

    s.componentes(p["decodificador"])
    alto, ancho = ctx.alto, ctx.ancho
    clave = (alto, ancho, p["curva"], p["vineta"], p["mascara"], p["mascara_fuerza"])
    geo = _GEOMETRIAS.get(clave)
    if geo is None:
        _GEOMETRIAS.clear()  # una sola por proceso: pesan decenas de MB
        geo = _GEOMETRIAS[clave] = _geometria(p, alto, ancho)
    rgb = np.clip(a_rgb(s.y, s.i, s.q), 0, 1.1)
    if p["convergencia"]:  # los tres cañones no apuntan exacto al mismo lugar
        for c, signo in ((0, 1), (2, -1)):
            rgb[..., c] = filtrar(rgb[..., c], corrimiento(signo * p["convergencia"]))
    luz = np.clip(rgb, 0, 1.1) ** p["gamma"]
    if p["blanco"] > 6500:  # el blanco de muchos televisores era azulado (9300 K)
        k = (p["blanco"] - 6500) / 2800
        luz = luz * np.array([1 - 0.12 * k, 1 - 0.03 * k, 1 + 0.10 * k], np.float32)
    luz = np.ascontiguousarray(np.moveaxis(luz.astype(np.float32), -1, 0))   # (color, línea, muestra)
    # Cada pixel de la pantalla, entre las dos líneas de la señal que le tocan (la grilla es chica y cabe en
    # la memoria rápida: muestrear ahí es más barato que remuestrear la imagen grande).
    k_lineas = p["lineas"] * float(np.clip((alto / LINEAS - 1.25) / 0.9, 0, 1))
    i00, i01, i10, i11 = geo["idx"]
    fx, dy = geo["fx"], geo["dy"]
    salida = np.empty((3, alto, ancho), np.float32)
    for c in range(3):
        src = luz[c].ravel()
        a = src[i00]
        c0 = (a + (src[i01] - a) * fx).reshape(alto, ancho)
        a = src[i10]
        c1 = (a + (src[i11] - a) * fx).reshape(alto, ancho)
        plano = c0 + (c1 - c0) * dy
        if k_lineas > 0:  # el haz: más grueso cuanto más brillo lleva
            barrido = c0 * (geo["h0f"] + geo["dh0"] * np.minimum(c0, 1)) + c1 * (geo["h1f"] + geo["dh1"] * np.minimum(c1, 1))
            plano += k_lineas * (barrido - plano)
        salida[c] = plano
    if p["brillo"]:  # el resplandor del vidrio alrededor de lo claro (cajas repetidas ≈ una campana)
        chico = salida[:, : alto // 4 * 4, : ancho // 4 * 4].reshape(3, alto // 4, 4, ancho // 4, 4).mean(axis=(2, 4))
        cerca = ndimage.uniform_filter(ndimage.uniform_filter(chico, (1, 7, 7)), (1, 7, 7))
        lejos = ndimage.uniform_filter(ndimage.uniform_filter(chico, (1, 25, 25)), (1, 25, 25))
        halo = cerca + 0.6 * lejos
        a, b, w = geo["halo_f"]
        halo = halo[:, a] * (1 - w)[None, :, None] + halo[:, b] * w[None, :, None]
        a, b, w = geo["halo_c"]
        halo = halo[:, :, a] * (1 - w) + halo[:, :, b] * w
        salida += (p["brillo"] * 0.3) * halo
    if p["persistencia"]:  # el fósforo tarda en apagarse (el P22 de verdad, apenas: ver ANALOGO.md)
        clave_f = ("fosforo", ctx.paso)
        antes = ctx.estado.get(clave_f)
        if antes is not None:
            salida = np.maximum(salida, antes * p["persistencia"])
        ctx.estado[clave_f] = salida.copy()
    luz_pantalla = geo["luz"]
    if p["parpadeo"]:
        luz_pantalla = luz_pantalla * (1 + 0.04 * p["parpadeo"] * math.sin(2 * math.pi * 7.3 * ctx.t))
    salida = salida * luz_pantalla
    sale = _GAMMA_16[np.clip(salida * 65535 + 0.5, 0, 65535).astype(np.uint16)]
    if geo["mascara"] is not None:
        # La máscara, después de la gamma y más leve en lo claro: en la pantalla de hoy un blanco con franjas
        # al 160 % se recortaría y saldría gris, y la muestra del probador (sin máscara) no se parecería al final.
        sale = sale * (1 + (geo["mascara"] - 1) * (1 - 0.75 * sale * sale))
    return np.ascontiguousarray(np.moveaxis((np.clip(sale, 0, 1) * 255 + 0.5).astype(np.uint8), 0, -1))


APARATOS = {"camara": camara, "osd": osd, "cinta": cinta, "antena": antena, "tbc": tbc, "colorizador": colorizador,
            "iman": iman, "relieve": relieve, "realimentacion": realimentacion, "pantalla": pantalla}
CAPTURAS = ("peine", "muesca")
# Qué es cada aparato de señal, en una línea (la consola del panel lo muestra en su tarjeta). Los de imagen lo dicen
# en la primera línea de su módulo.
DESCRIPCION = {
    "camara": "La cámara de tubo o de los 90: la mancha clara sobre las luces, los blancos que se queman, el ruido y la estela.",
    "osd": "Los letreros de la cámara y la casetera en pantalla: la fecha, la hora, REC, PLAY.",
    "cinta": "La cinta de video (VHS, Betamax, Video8): el color corrido, el temblor, el tracking, la costura del cabezal "
             "y el desgaste de las copias.",
    "antena": "La señal por el aire: la nieve, los fantasmas, la interferencia, la barra del zumbido y la imagen que rueda.",
    "tbc": "El corrector de base de tiempo: endereza la cinta que viene antes y ajusta brillo, contraste, color y tono.",
    "colorizador": "El colorizador del sintetizador de video: el brillo pasado a las tintas.",
    "iman": "El imán junto al tubo (Paik, Magnet TV, 1965): la imagen se tuerce y cambia de color alrededor de un punto.",
    "relieve": "El relieve de barrido (Rutt/Etra): el brillo levanta las líneas de la pantalla.",
    "realimentacion": "La cámara que mira su propio monitor: lo de antes vuelve más chico, girado y corrido de color.",
    "pantalla": "El televisor de tubo: el vidrio curvo, las líneas de barrido, la máscara de fósforos, el resplandor y "
                "la persistencia.",
}

# ── Los aparatos de imagen: la película y lo digital ───────────────────────

_IMAGEN: dict | None = None
_MODULOS_IMAGEN: list = []


def _imagen() -> dict:
    """Los aparatos que viven en sus propios módulos se suman a la mesa la primera vez que se pide una cadena: los
    que trabajan en la imagen y no en la señal (la película, el sensor y la compresión de lo digital, la consola
    de mezcla: su `APARATOS`) y los de señal que no están aquí (la casetera: su `SENAL`)."""
    global _IMAGEN
    if _IMAGEN is None:
        from . import (aire, casetera, cinemudo, cinetico, consola, digital, fotografia, imprenta, juguetes, optica, pelicula,
                       proyeccion, radio, rollo)

        _IMAGEN = {}
        for m in (optica, pelicula, rollo, cinemudo, proyeccion, fotografia, juguetes, imprenta, cinetico, radio, aire,
                  digital, consola, casetera):
            _IMAGEN.update(getattr(m, "APARATOS", {}))
            APARATOS.update(getattr(m, "SENAL", {}))
            POR_DEFECTO.update(m.POR_DEFECTO)
            RANGOS.update(m.RANGOS)
            _MODULOS_IMAGEN.append(m)
        APARATOS.update(_IMAGEN)
    return _IMAGEN


def _modulo(nombre: str):
    _imagen()
    return next((m for m in _MODULOS_IMAGEN if nombre in getattr(m, "APARATOS", {}) or nombre in getattr(m, "SENAL", {})), None)


# ── La cadena ───────────────────────────────────────────────────────────────

def _normalizar_cadena(cadena) -> dict:
    if isinstance(cadena, list):
        return {"aparatos": cadena}
    if isinstance(cadena, dict) and isinstance(cadena.get("aparatos"), list):
        return cadena
    return {"aparatos": None}


def errores(cadena) -> list[str]:
    """Lo que está mal en una cadena. Vacío = se puede usar."""
    imagen = _imagen()
    c = _normalizar_cadena(cadena)
    if c["aparatos"] is None:
        return ["una cadena es una lista de aparatos, o {\"aparatos\": [...]}"]
    mal = []
    if not c["aparatos"]:
        mal.append("la cadena no tiene aparatos")
    if c.get("captura", "peine") not in CAPTURAS:
        mal.append(f"`captura`: «{c['captura']}» no es {' / '.join(CAPTURAS)}")
    s = c.get("semilla", 1)
    if isinstance(s, bool) or not isinstance(s, int) or s < 0:
        mal.append(f"`semilla`: {s!r} tiene que ser un entero desde 0")
    for n, a in enumerate(c["aparatos"]):
        if not isinstance(a, dict) or a.get("aparato") not in APARATOS:
            mal.append(f"aparato {n + 1}: «{a.get('aparato') if isinstance(a, dict) else a}» no es {' / '.join(APARATOS)}")
            continue
        nombre = a["aparato"]
        if nombre == "pantalla" and n != len(c["aparatos"]) - 1:
            mal.append("la pantalla va al final de la cadena")
        for k, v in a.items():
            if k == "aparato":
                continue
            if k not in POR_DEFECTO[nombre]:
                mal.append(f"{nombre}: no tiene la perilla `{k}` (tiene: {', '.join(POR_DEFECTO[nombre])})")
                continue
            r = RANGOS.get(nombre, {}).get(k)
            if r is None or (v is None and POR_DEFECTO[nombre][k] is None):
                continue
            if isinstance(r[0], str):
                if v not in r:
                    mal.append(f"{nombre}.{k}: «{v}» no es {' / '.join(r)}")
            elif isinstance(v, bool) or not isinstance(v, (int, float)) or not r[0] <= v <= r[1]:
                mal.append(f"{nombre}.{k}: {v!r} tiene que ser un número entre {r[0]} y {r[1]}")
        if nombre == "realimentacion":
            m = a.get("mezcla", POR_DEFECTO[nombre]["mezcla"]) * a.get("contraste", POR_DEFECTO[nombre]["contraste"])
            if isinstance(m, (int, float)) and m >= 0.97:
                mal.append(f"realimentacion: mezcla × contraste = {m:.2f}; desde 0,97 lo claro no se apaga nunca")
        if nombre == "antena":
            fantasmas = a.get("fantasma", [])
            if isinstance(fantasmas, list) and any(isinstance(x, list) and x and isinstance(x[0], (int, float))
                                                   and not -4 <= x[0] <= 8 for x in fantasmas):
                mal.append("antena.fantasma: el retraso va entre −4 y 8 µs (más allá da la vuelta a la línea)")
            for k in ("fantasma", "interferencia"):
                pares = a.get(k, [])
                if not isinstance(pares, list) or not all(isinstance(x, list) and len(x) == 2 and all(isinstance(z, (int, float)) for z in x) for x in pares):
                    mal.append(f"antena.{k}: una lista de pares [{'retraso µs' if k == 'fantasma' else 'MHz'}, amplitud]")
        if nombre == "colorizador":
            t = a.get("tintas", TINTAS_CURIANA)
            if not isinstance(t, list) or len(t) < 2 or not all(isinstance(h, str) and len(h) == 7 and h[0] == "#" for h in t):
                mal.append("colorizador.tintas: al menos dos colores #rrggbb")
        if nombre == "osd":
            for item in a.get("textos", []):
                if not isinstance(item, dict) or not isinstance(item.get("texto"), str):
                    mal.append("osd.textos: cada uno con su `texto`")
                elif item.get("lugar", "arriba-izquierda") not in LUGARES:
                    mal.append(f"osd: «{item['lugar']}» no es {' / '.join(LUGARES)}")
        modulo = _modulo(nombre)
        if modulo is not None:
            mal.extend(modulo.errores(nombre, a))
    if not mal:
        mal.extend(errores_de_automatizacion(c))
    if not mal:  # lo que sólo se ve mirando la cadena entera (a 30 cuadros por segundo; `procesar` mira los del video)
        mal.extend(_revisar_memoria([(a["aparato"], {**POR_DEFECTO[a["aparato"]], **a}) for a in c["aparatos"]], 30.0))
    return mal


# ── La automatización: las perillas que se mueven en el tiempo ─────────────
#
# Miguel, el 2026-11-23: «podríamos además de tener una galería, tener un espacio para hacer edición manual de vídeo.
# Como modificación análoga de vídeo. Con diales manuales». La consola del panel (`/consola`) graba los movimientos de
# las perillas; el motor los repite al renderizar. Una cadena puede llevar:
#
#     "automatizacion": [{"paso": 0, "perilla": "nieve", "puntos": [[0.0, 0.1], [2.5, 0.6], [4.0, 0.0]]}, …]
#
# `paso` es el lugar del aparato en la cadena (desde 0); `puntos`, pares [segundo de la entrada, valor]. Entre punto y
# punto la perilla se mueve en línea recta (`curva: "lineal"`, la de fábrica) o salta (`"escalon"`); antes del primero
# y después del último, se queda en su valor. Las perillas de opciones (un modo, un sí o no) siempre saltan. Lo que
# suena usa el valor de la perilla al empezar (la automatización mueve la imagen).

CURVAS = ("lineal", "escalon")


def errores_de_automatizacion(c: dict) -> list[str]:
    auto = c.get("automatizacion", [])
    if not auto:
        return []
    if not isinstance(auto, list):
        return ["`automatizacion`: una lista de pistas {paso, perilla, puntos}"]
    mal = []
    aparatos = c["aparatos"]
    for n, pista in enumerate(auto):
        donde = f"automatizacion {n + 1}"
        if not isinstance(pista, dict):
            mal.append(f"{donde}: una pista es {{paso, perilla, puntos}}")
            continue
        paso = pista.get("paso")
        if isinstance(paso, bool) or not isinstance(paso, int) or not 0 <= paso < len(aparatos):
            mal.append(f"{donde}: `paso` es el lugar del aparato en la cadena, de 0 a {len(aparatos) - 1}")
            continue
        nombre = aparatos[paso]["aparato"]
        perilla = pista.get("perilla")
        if perilla not in POR_DEFECTO[nombre]:
            mal.append(f"{donde}: {nombre} no tiene la perilla `{perilla}`")
            continue
        if pista.get("curva", "lineal") not in CURVAS:
            mal.append(f"{donde}: `curva` es {' / '.join(CURVAS)}")
        puntos = pista.get("puntos")
        if not isinstance(puntos, list) or not puntos or not all(isinstance(x, list) and len(x) == 2 for x in puntos):
            mal.append(f"{donde}: `puntos` es una lista de [segundo, valor]")
            continue
        tiempos = [x[0] for x in puntos]
        if not all(isinstance(t, (int, float)) and not isinstance(t, bool) for t in tiempos) or tiempos != sorted(tiempos):
            mal.append(f"{donde}: los segundos de los puntos van en orden")
        r = RANGOS.get(nombre, {}).get(perilla)
        for _, v in puntos:
            if r is None:
                continue
            if isinstance(r[0], str):
                if v not in r:
                    mal.append(f"{donde}: {nombre}.{perilla}: «{v}» no es {' / '.join(r)}")
                    break
            elif isinstance(v, bool) or not isinstance(v, (int, float)) or not r[0] <= v <= r[1]:
                mal.append(f"{donde}: {nombre}.{perilla}: {v!r} tiene que ser un número entre {r[0]} y {r[1]}")
                break
    return mal


def _pistas_por_paso(c: dict) -> dict[int, list[dict]]:
    pistas: dict[int, list[dict]] = {}
    for pista in c.get("automatizacion", []) or []:
        pistas.setdefault(pista["paso"], []).append(pista)
    return pistas


def valor_en(pista: dict, t: float):
    """El valor de una perilla automatizada en el segundo t de la entrada."""
    puntos = pista["puntos"]
    if t <= puntos[0][0]:
        return puntos[0][1]
    if t >= puntos[-1][0]:
        return puntos[-1][1]
    for (t0, v0), (t1, v1) in zip(puntos, puntos[1:]):
        if t0 <= t < t1:
            if pista.get("curva", "lineal") == "escalon" or not isinstance(v0, (int, float)) or isinstance(v0, bool) \
                    or not isinstance(v1, (int, float)) or isinstance(v1, bool) or t1 <= t0:
                return v0
            v = v0 + (v1 - v0) * (t - t0) / (t1 - t0)
            # Si la perilla es entera lo dice su valor de fábrica (`_entero`, lo pone `preparar`): los puntos que
            # llegan del navegador en JSON no distinguen 1.0 de 1.
            entero = pista.get("_entero")
            if entero is None:
                entero = isinstance(v0, int) and isinstance(v1, int)
            return int(round(v)) if entero else float(v)
    return puntos[-1][1]


def _es_entero(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _con_automatizacion(p: dict, t: float) -> dict:
    """Las perillas del paso en el segundo t: las de la cadena con las automatizadas en su valor de ese instante."""
    pistas = p.get("_auto")
    if not pistas:
        return p
    return {**p, **{pista["perilla"]: valor_en(pista, t) for pista in pistas}}


def aparatos_json() -> dict:
    """Todos los aparatos de la mesa con sus perillas (el valor de fábrica y el rango): lo que la consola dibuja como
    diales. `tipo`: señal (trabaja en la señal de video) o imagen (en la imagen); `doc`: la primera línea de su módulo."""
    imagen = _imagen()
    sale = {}
    for nombre in APARATOS:
        m = _modulo(nombre)
        doc = DESCRIPCION.get(nombre) or ((m.__doc__ if m is not None else __doc__) or "").strip().splitlines()[0]
        perillas = {}
        for k, v in POR_DEFECTO[nombre].items():
            r = RANGOS.get(nombre, {}).get(k)
            perillas[k] = {"defecto": v, "rango": list(r) if r is not None else None, "entero": _es_entero(v)}
        sale[nombre] = {"tipo": "imagen" if nombre in imagen else "señal", "gesto": nombre in GESTOS,
                        "modulo": m.__name__.split(".")[-1] if m is not None else "analogo", "doc": doc, "perillas": perillas}
    return sale


def cadenas_json() -> list[dict]:
    """Las cadenas analógicas de la galería ya resueltas (sin los gestos): los puntos de partida de la consola."""
    from . import estilos as galeria

    todos = galeria.leer()
    sale = []
    for e in todos:
        t = e["tecnica"]
        if t.get("comando") != "analogo" or t.get("gesto"):
            continue
        try:
            c = _normalizar_cadena(cadena_de_tecnica(t, todos))
        except SystemExit:
            continue
        sale.append({"id": e["id"], "frase": e.get("frase", ""), "estado": e.get("estado", ""),
                     "aparatos": c["aparatos"], "captura": c.get("captura", "peine"), "semilla": c.get("semilla", 1)})
    return sale


def preparar(cadena) -> tuple[list[tuple[str, dict]], str, int]:
    """La cadena con cada perilla en su valor: [(aparato, perillas)], la captura y la semilla."""
    mal = errores(cadena)
    if mal:
        salir("cadena analógica con errores:\n  " + "\n  ".join(mal))
    c = _normalizar_cadena(cadena)
    pasos = []
    pistas = _pistas_por_paso(c)
    for n, a in enumerate(c["aparatos"]):
        p = {**POR_DEFECTO[a["aparato"]], **{k: v for k, v in a.items() if k != "aparato"}}
        p = json.loads(json.dumps(p))
        if n in pistas:   # las perillas que se mueven: arrancan en su primer valor (lo que suena usa ése)
            p["_auto"] = [{**pista, "_entero": _es_entero(POR_DEFECTO[a["aparato"]].get(pista["perilla"]))}
                          for pista in pistas[n]]
            for pista in p["_auto"]:
                v = pista["puntos"][0][1]
                p[pista["perilla"]] = int(round(v)) if pista["_entero"] and isinstance(v, (int, float)) else v
        pasos.append((a["aparato"], p))
    # El TBC endereza la base de tiempo de las cintas que vienen antes.
    for n, (nombre, p) in enumerate(pasos):
        if nombre == "tbc":
            for nombre_a, pa in pasos[:n]:
                if nombre_a == "cinta":
                    pa["_tbc"] = p["fuerza"]
    return pasos, c.get("captura", "peine"), int(c.get("semilla", 1))


def _memorias(pasos: list[tuple[str, dict]], fps: float) -> tuple[list[tuple[str, int]], int]:
    """Cuánto recuerda cada aparato, en cuadros del video: las memorias exactas (el cuadro de película, el códec
    desde su cuadro clave, la pausa, el rebobinado, el estrobo…: [(aparato, cuadros)]) y la que se apaga sola (la
    estela, la realimentación, el fósforo: con eso basta para que lo que queda se pierda en el ruido)."""
    _imagen()
    exactas, se_apaga = [], 0
    for n, (nombre, p) in enumerate(pasos):
        m = _modulo(nombre)
        if m is not None:
            w = m.calentar(pasos, fps, solo=n)
            if w:
                exactas.append((nombre, w))
        elif nombre == "realimentacion":
            ganancia = min(0.97, max(p["mezcla"] * p["contraste"], 0.05))
            se_apaga += int(math.ceil(math.log(0.01) / math.log(ganancia))) + 2
        elif nombre == "camara" and p["estela"]:
            se_apaga += int(math.ceil(math.log(0.01) / math.log(p["estela"]))) + 1
        elif nombre == "pantalla" and p["persistencia"]:
            se_apaga += int(math.ceil(math.log(0.01) / math.log(p["persistencia"]))) + 1
    return exactas, se_apaga


def calentar(pasos: list[tuple[str, dict]], fps: float = 30.0) -> int:
    """Cuántos cuadros hay que procesar antes de un pedazo para que lo que tiene memoria llegue igual. Encadenadas,
    las memorias se suman: lo que recuerda el de abajo (el cuadro de la pausa) lo tuvo que hacer el de arriba (el
    estrobo) ya caliente (la revisión del 2026-11-21 lo encontró como costura)."""
    exactas, se_apaga = _memorias(pasos, fps)
    return min(sum(w for _, w in exactas) + se_apaga, CALENTAR_MAX)


def _revisar_memoria(pasos: list[tuple[str, dict]], fps: float) -> list[str]:
    """Si lo que tiene memoria exacta necesita más que el tope, la costura se vería: qué mover, por aparato."""
    exactas, _ = _memorias(pasos, fps)
    total = sum(w for _, w in exactas)
    if total <= CALENTAR_MAX:
        return []
    consejos = []
    for nombre, _ in exactas:
        c = getattr(_modulo(nombre), "CONSEJO", {}).get(nombre)
        if c and c not in consejos:
            consejos.append(c)
    return [f"la cadena necesita recordar {total} cuadros a {fps:g} por segundo (el tope es {CALENTAR_MAX}): "
            + "; ".join(consejos)]


#: Lo más que se calienta un pedazo. El códec se calienta desde su cuadro clave: su `gop` tiene este techo.
CALENTAR_MAX = 240


def _ocho_bits(img: np.ndarray) -> np.ndarray:
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


def _encajar(img: np.ndarray, alto: int, ancho: int, como: tuple[str, str]) -> np.ndarray:
    """Una imagen de otro tamaño (la del sensor de un celular) a la salida: entera con barras negras o llenando
    (y recortando el centro), ampliada suave (como la ampliaba un reproductor) o con sus pixeles."""
    from PIL import Image

    h, w = img.shape[:2]
    if (h, w) == (alto, ancho):
        return img
    llenar, metodo = como
    f = (max if llenar == "llenar" else min)(alto / h, ancho / w)
    nh, nw = max(1, int(round(h * f))), max(1, int(round(w * f)))
    filtro = Image.NEAREST if metodo == "pixeles" else Image.BILINEAR
    grande = np.asarray(Image.fromarray(_ocho_bits(img)).resize((nw, nh), filtro), np.float32) / 255
    sale = np.zeros((alto, ancho, 3), np.float32)
    y0, x0 = (alto - nh) // 2, (ancho - nw) // 2
    ys, xs, yd, xd = max(0, -y0), max(0, -x0), max(0, y0), max(0, x0)
    hh, ww = min(nh - ys, alto - yd), min(nw - xs, ancho - xd)
    sale[yd:yd + hh, xd:xd + ww] = grande[ys:ys + hh, xs:xs + ww]
    return sale


def _de_senal(s: Senal, captura: str, alto: int, ancho: int) -> np.ndarray:
    s.componentes(captura)
    return _de_grilla(np.clip(a_rgb(s.y, s.i, s.q), 0, 1), alto, ancho)


def procesar_cuadro(rgb8: np.ndarray, pasos, captura: str, ctx: Contexto) -> np.ndarray:
    """Un cuadro de la entrada (RGB de 8 bits, al tamaño de salida) por la cadena entera → RGB de 8 bits al tamaño
    de salida. La imagen entra a la grilla de la señal cuando le toca a un aparato de señal, y vuelve a ser imagen
    cuando le toca a uno de imagen (la película, lo digital)."""
    imagen = _imagen()
    alto, ancho = ctx.alto, ctx.ancho
    ctx.encuadre = ("barras", "suave")
    ctx.estado.pop("captura", None)   # la captura del sensor es de este cuadro: un códec antes del sensor no la ve
    img = rgb8.astype(np.float32) / 255
    ctx.original = img   # el cuadro como entró a la cadena (el tintado elige su color por la escena, no por la copia)
    s = None
    for n, (nombre, p) in enumerate(pasos):
        ctx.paso = n
        p = _con_automatizacion(p, ctx.t)
        if nombre in imagen:
            if s is not None:
                img, s = _de_senal(s, captura, alto, ancho), None
            img = imagen[nombre](img, p, ctx)
            continue
        if s is None:
            s = Senal(*a_yiq(_a_grilla(_ocho_bits(_encajar(img, alto, ancho, ctx.encuadre)))), ctx.k)
        if nombre == "pantalla":
            return pantalla(s, p, ctx)
        s = APARATOS[nombre](s, p, ctx)
        if s.sale_compuesta:
            s.compuesta()
            s.sale_compuesta = False
    if s is not None:
        img = _de_senal(s, captura, alto, ancho)
    return _ocho_bits(_encajar(img, alto, ancho, ctx.encuadre))


def cuadro(rgb: np.ndarray, pasos, captura: str, ctx: Contexto) -> np.ndarray:
    """Un cuadro (en la grilla de la señal, RGB 0–1) por una cadena de aparatos de señal. Si termina en la
    pantalla devuelve RGB de 8 bits al tamaño de salida; si no, RGB 0–1 en la grilla. (El video usa
    `procesar_cuadro`, que además sabe de los aparatos de imagen.)"""
    s = Senal(*a_yiq(rgb), ctx.k)
    for n, (nombre, p) in enumerate(pasos):
        ctx.paso = n
        p = _con_automatizacion(p, ctx.t)
        if nombre == "pantalla":
            return pantalla(s, p, ctx)
        s = APARATOS[nombre](s, p, ctx)
        if s.sale_compuesta:
            s.compuesta()
            s.sale_compuesta = False
    s.componentes(captura)
    return np.clip(a_rgb(s.y, s.i, s.q), 0, 1)


# ── El video: pedazos en paralelo ───────────────────────────────────────────

def _sonda(ruta: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=codec_type,width,height,r_frame_rate,avg_frame_rate,nb_frames,color_space,duration,start_time"
                        ":stream_side_data=rotation:stream_tags=rotate:format=duration,start_time",
                        "-of", "json", str(ruta)], capture_output=True, text=True)
    if r.returncode:
        salir(f"ffprobe no pudo leer {ruta}: {r.stderr.strip()[-300:]}")
    d = json.loads(r.stdout)
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), None)
    if v is None:
        salir(f"{ruta} no tiene video")
    ancho, alto = int(v["width"]), int(v["height"])
    # Un video del teléfono puede venir girado: ffmpeg lo endereza al leerlo, así que ancho y alto se cruzan.
    giro = 0
    for lado in v.get("side_data_list", []):
        if "rotation" in lado:
            giro = int(round(float(lado["rotation"])))
    if "rotate" in v.get("tags", {}):
        giro = int(v["tags"]["rotate"])
    if abs(giro) % 180 == 90:
        ancho, alto = alto, ancho
    fmt = d.get("format", {})
    inicio_v = float(v.get("start_time") or 0)
    # Lo que dura y dónde empieza el video, no el contenedor: el audio puede ser más largo o empezar antes.
    return {"ancho": ancho, "alto": alto, "fps": v.get("avg_frame_rate") or v["r_frame_rate"],
            "fps_r": v["r_frame_rate"], "matriz": v.get("color_space", ""),
            "audio": any(s.get("codec_type") == "audio" for s in d["streams"]),
            "cuadros": int(v["nb_frames"]) if str(v.get("nb_frames", "")).isdigit() else None,
            "duracion": float(v.get("duration") or fmt.get("duration") or 0),
            "desfase": max(0.0, inicio_v - float(fmt.get("start_time") or 0))}


def _es_foto(ruta: Path) -> bool:
    return ruta.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}


def envolvente(t: float, ventanas: list[tuple[float, float]] | None, fundido: float) -> float:
    """Cuánto de la cadena entra en el segundo t (1 sin ventanas)."""
    if not ventanas:
        return 1.0
    e = 0.0
    for a, b in ventanas:
        if fundido > 0:  # entra en el `fundido` antes de `a` y se va en el que sigue a `b`
            e = max(e, min(1.0, (t - (a - fundido)) / fundido, ((b + fundido) - t) / fundido))
        elif a <= t < b:
            e = 1.0
    return float(np.clip(e, 0, 1))


def _a_grilla(rgb8: np.ndarray) -> np.ndarray:
    from PIL import Image

    # Al achicar, el promedio de cada caja; al agrandar (una entrada más chica que la grilla), bicúbico: la caja
    # agrandaría como vecino más cercano, y los serruchos se leerían como color falso.
    achica = rgb8.shape[1] >= MUESTRAS and rgb8.shape[0] >= LINEAS
    return np.asarray(Image.fromarray(rgb8).resize((MUESTRAS, LINEAS), Image.BOX if achica else Image.BICUBIC), np.float32) / 255


def _de_grilla(rgb: np.ndarray, alto: int, ancho: int) -> np.ndarray:
    from PIL import Image

    img = Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8))
    return np.asarray(img.resize((ancho, alto), Image.BICUBIC), np.float32) / 255


def _leer(entrada: Path, info: dict, a: int, n: int, alto: int, ancho: int):
    """Los cuadros a, a+1… (n) de la entrada, al tamaño de salida, en RGB de 8 bits."""
    if _es_foto(entrada):
        from PIL import Image, ImageOps

        img = ImageOps.fit(ImageOps.exif_transpose(Image.open(entrada)).convert("RGB"), (ancho, alto), Image.LANCZOS)
        cuadro_ = np.asarray(img)
        for _ in range(n):
            yield cuadro_
        return
    fps = Fraction(info["fps"])
    m = info["matriz"]
    matriz = ("bt2020" if m.startswith("bt2020") else "bt709" if m == "bt709" or (m in ("", "unknown") and info["alto"] >= 576)
              else "bt601")
    cmd = ["ffmpeg", "-v", "error"]
    if a > 0:
        cmd += ["-ss", f"{info.get('desfase', 0.0) + float((a - Fraction(1, 2)) / fps):.6f}"]
    cmd += ["-i", str(entrada), "-frames:v", str(n), "-vf",
            f"scale={ancho}:{alto}:flags=bicubic:in_color_matrix={matriz}:in_range=auto,format=rgb24",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    tam = alto * ancho * 3
    ultimo = None
    try:
        for _ in range(n):
            b = proc.stdout.read(tam)
            if len(b) < tam:  # el video terminó antes: se repite el último cuadro
                if ultimo is None:
                    raise RuntimeError(f"no salió ningún cuadro de {entrada.name} desde el {a}")
                yield ultimo
                continue
            ultimo = np.frombuffer(b, np.uint8).reshape(alto, ancho, 3)
            yield ultimo
    finally:
        proc.stdout.close()
        proc.wait()


def _pedazo(tarea: dict) -> str:
    """Un pedazo del video, en un proceso aparte: lee sus cuadros (más los de calentar), los pasa por la
    cadena y los escribe en su propio archivo."""
    pasos, captura, semilla = tarea["pasos"], tarea["captura"], tarea["semilla"]
    alto, ancho, fps = tarea["alto"], tarea["ancho"], float(Fraction(tarea["fps"]))
    a, b, cal = tarea["a"], tarea["b"], tarea["calentar"]
    desde = max(0, a - cal)
    ctx = Contexto(semilla, fps, alto, ancho)
    ctx.musica = tarea.get("musica")
    ctx.inicio = tarea["k0"] / fps
    ctx.fin = tarea["k_fin"] / fps if tarea.get("k_fin") is not None else None
    ctx.entrada = tarea["entrada"]
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{ancho}x{alto}",
           "-r", tarea["fps"], "-i", "-", "-vf", "scale=out_color_matrix=bt709:out_range=tv",
           "-c:v", "libx264", "-preset", "medium", "-crf", str(tarea["crf"]), "-threads", "2", "-pix_fmt", "yuv420p",
           "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", tarea["salida"]]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for n, rgb8 in enumerate(_leer(Path(tarea["entrada"]), tarea["info"], tarea["origen"] + desde, b - desde, alto, ancho)):
            k = desde + n
            ctx.k, ctx.t = tarea["k0"] + k, (tarea["k0"] + k) / fps
            e = envolvente(k / fps, tarea["ventanas"], tarea["fundido"])
            if e <= 0 and k >= a and not cal:
                enc.stdin.write(np.ascontiguousarray(rgb8).tobytes())
                continue
            # Lo que tiene memoria (estela, realimentación, fósforo) sigue andando fuera de las ventanas: si no, al
            # abrir una la memoria dependería de dónde cayó la costura entre pedazos.
            sale = procesar_cuadro(rgb8, pasos, captura, ctx)
            if k < a:
                continue
            if e <= 0:
                enc.stdin.write(np.ascontiguousarray(rgb8).tobytes())
                continue
            if e < 1:
                sale = (sale.astype(np.float32) * e + rgb8.astype(np.float32) * (1 - e) + 0.5).astype(np.uint8)
            enc.stdin.write(sale.tobytes())
    finally:
        enc.stdin.close()
        err = enc.stderr.read().decode(errors="replace")
        enc.wait()
    if enc.returncode:
        raise RuntimeError(f"ffmpeg no escribió el pedazo {a}–{b}: {err[-400:]}")
    return tarea["salida"]


#: Los aparatos que hacen un **gesto** (2026-11-22): un momento que se pone encima de cualquier base —la pausa
#: del VHS, el estrobo de la consola— en vez de ser un estilo propio. Miguel, al juzgar la mesa: «Hay muchos que
#: son muy parecidos entre sí»; medidos, la pausa, el estrobo o la llave sobre el VHS eran el VHS de la casa con un
#: momento distinto encima, y eligió que fueran gestos aparte.
GESTOS = ("consola", "casetera", "rollo", "dial")


def componer(base: list, gesto: list) -> list:
    """La cadena `base` con los aparatos de un gesto en su lugar. La consola mezcla lo que sale de la cámara o de la
    película antes de grabarlo: va antes de la primera cinta. La casetera reproduce lo grabado: va después de la
    última. Sin cinta, los dos van al final (antes de la pantalla, que siempre cierra). El rollo (2026-11-22) es lo que
    le pasa a la película en el proyector: va justo después de la última película; sin película, como la consola."""
    base = list(base)
    rollos = [a for a in gesto if a.get("aparato") == "rollo"]
    antes = [a for a in gesto if a.get("aparato") == "consola"]
    despues = [a for a in gesto if a.get("aparato") not in ("consola", "rollo")]
    peliculas = [n for n, a in enumerate(base) if isinstance(a, dict) and a.get("aparato") == "pelicula"]
    if rollos and peliculas:
        base = base[:peliculas[-1] + 1] + rollos + base[peliculas[-1] + 1:]
    else:
        antes = rollos + antes
    cintas = [n for n, a in enumerate(base) if isinstance(a, dict) and a.get("aparato") == "cinta"]
    fin = len(base) - 1 if base and isinstance(base[-1], dict) and base[-1].get("aparato") == "pantalla" else len(base)
    i0, i1 = (cintas[0], cintas[-1] + 1) if cintas else (fin, fin)
    return base[:i0] + antes + base[i0:i1] + despues + base[i1:]


def _estilo(id_: str, estilos: list[dict] | None = None) -> dict | None:
    if estilos is None:
        from . import estilos as galeria

        estilos = galeria.leer()
    return next((x for x in estilos if x["id"] == id_), None)


def base_de(sobre, estilos: list[dict] | None = None) -> dict:
    """La base de un gesto (`sobre` en su técnica): una cadena escrita, o el id de un estilo analógico que no sea gesto."""
    if isinstance(sobre, list):
        return {"aparatos": sobre}
    e = _estilo(sobre, estilos) if isinstance(sobre, str) else None
    if e is None or e["tecnica"].get("comando") != "analogo" or e["tecnica"].get("gesto"):
        salir(f"`sobre`: «{sobre}» no es una cadena ni un estilo analógico que no sea gesto")
    return cadena_de_tecnica(e["tecnica"], estilos)


def cadena_de_tecnica(t: dict, estilos: list[dict] | None = None) -> dict:
    """La cadena de una técnica `comando: analogo`, lista para `procesar`. La de un gesto es su base (`sobre`, la que
    usa su muestra) con el gesto encima."""
    propios = {k: t[k] for k in ("captura", "semilla") if k in t}
    if not t.get("gesto"):
        return {"aparatos": t["cadena"], **propios}
    base = base_de(t.get("sobre"), estilos)
    return {**base, "aparatos": componer(base["aparatos"], t["cadena"]), **propios}


def resolver_cadena(texto: str, gestos: list[str] | tuple = ()):
    """Un estilo de la galería con `comando: analogo`, o la cadena escrita en JSON; con `gestos`, los gestos de la
    galería encima, en orden (`--gesto pausa-del-vhs`)."""
    texto = texto.strip()
    todos = None
    if texto.startswith(("[", "{")):
        try:
            cadena, nombre = _normalizar_cadena(json.loads(texto)), "cadena"
        except json.JSONDecodeError as err:
            salir(f"la cadena no es JSON válido: {err}")
        if cadena["aparatos"] is None:
            salir("una cadena es una lista de aparatos, o {\"aparatos\": [...]}")
    else:
        from . import estilos as galeria

        todos = galeria.leer()
        e = _estilo(texto, todos)
        if e is None:
            from . import recetas   # una receta guardada: su base con sus gestos, y después los que se pidan

            r = recetas.buscar(texto)
            if r is not None:
                cadena, _ = resolver_cadena(r["base"], [*r["gestos"], *gestos])
                return cadena, texto + "".join("+" + g.strip() for g in gestos)
            salir(f"no hay un estilo ni una receta «{texto}» (las cadenas: python montaje.py analogo --cadenas; "
                  "las recetas: python montaje.py recetas)")
        t = e["tecnica"]
        if t.get("comando") != "analogo":
            salir(f"«{texto}» no es una cadena analógica (su técnica es {t})")
        cadena, nombre = cadena_de_tecnica(t, todos), texto
    for g in gestos:
        if todos is None:
            from . import estilos as galeria

            todos = galeria.leer()
        eg = _estilo(g.strip(), todos)
        if eg is None or not eg["tecnica"].get("gesto"):
            hay = ", ".join(x["id"] for x in todos if x["tecnica"].get("gesto"))
            salir(f"«{g}» no es un gesto de la galería (hay: {hay})")
        cadena = {**cadena, "aparatos": componer(cadena["aparatos"], eg["tecnica"]["cadena"])}
        nombre += "+" + eg["id"]
    return cadena, nombre


def musica_de(proyecto: str) -> dict:
    """Los golpes de la canción de un proyecto (su análisis), para lo que va al pulso en la mesa. Los segundos son
    los de la canción del proyecto: sirven para un render de ese proyecto, que empieza donde empieza la canción."""
    from . import musica
    from .rutas import Proyecto

    m = musica.cargar(Proyecto(proyecto))
    return {"beats": [float(b) for b in m["beats"]], "primeros_tiempos": [float(b) for b in m["primeros_tiempos"]],
            "energia": [float(e) for e in m["energia"]], "bpm": float(m["bpm"])}


def _sin_golpes(pasos, musica) -> None:
    _imagen()
    if musica is None and any(getattr(m, "necesita_golpes", lambda _: False)(pasos) for m in _MODULOS_IMAGEN):
        salir("la cadena va al pulso y no tiene los golpes: --golpes <proyecto> (el de la canción del video)")


def al_pulso(ctx: Contexto, cada: str, dura_golpes: float) -> float | None:
    """¿Hay un golpe sonando? En qué parte va (0 a 1) desde el último golpe elegido (`cada`: el uno de cada compás,
    cada golpe o los picos), durante `dura_golpes` golpes; o None. Lo usan los aparatos que van al pulso."""
    from .pulso import _golpes_de

    m = ctx.musica
    if not m:
        return None
    clave = ("golpes", cada)
    if clave not in ctx.estado:
        ctx.estado[clave] = np.asarray(_golpes_de(m, cada), float)
    golpes = ctx.estado[clave]
    i = int(np.searchsorted(golpes, ctx.t, side="right")) - 1
    if i < 0:
        return None
    u = (ctx.t - golpes[i]) / (dura_golpes * 60 / m["bpm"])
    return u if u < 1 else None


def ruta_entrada(texto: str) -> Path:
    r = Path(texto)
    for candidato in (r, MEDIOS / r):
        if candidato.exists():
            return candidato.resolve()
    salir(f"no encuentro {texto} (ni como ruta ni dentro de {MEDIOS})")


def procesar(entrada: Path, salida: Path, cadena, *, desde: float | None = None, hasta: float | None = None,
             segundos: float = 6.0, fps_foto: str = "30", alto: int | None = None, ventanas=None, fundido: float = 0.5,
             hilos: int | None = None, crf: int = 16, pedazo: int = 48, callado: bool = False,
             musica: dict | None = None) -> Path:
    """La entrada (video o foto) pasada por la cadena → `salida`, con el audio de la entrada. `musica`: los golpes
    de la canción (`musica_de`), para lo que va al pulso."""
    pasos, captura, semilla = preparar(cadena)
    _sin_golpes(pasos, musica)
    if _es_foto(entrada):
        from PIL import Image

        from PIL import ImageOps

        with Image.open(entrada) as img:
            derecha = ImageOps.exif_transpose(img)
            info = {"ancho": derecha.width, "alto": derecha.height, "fps": fps_foto, "matriz": "bt709", "audio": False,
                    "duracion": segundos}
        desde, hasta = 0.0, segundos
        # Una foto grande sale a lo más a 1080 de alto (la pantalla pesa en proporción al tamaño de salida).
        alto = alto or min(info["alto"], 1080)
    else:
        info = _sonda(entrada)
        if abs(float(Fraction(info["fps"])) / float(Fraction(info["fps_r"])) - 1) > 0.01:
            salir(f"{entrada.name} tiene cuadros por segundo variables: pásalo antes a fijos (sus copias de trabajo ya lo son)")
        info["fps"] = info["fps_r"]
    fps = Fraction(info["fps"])
    ancho, alto_ = info["ancho"], info["alto"]
    if alto:
        ancho, alto_ = int(round(ancho * alto / alto_ / 2)) * 2, alto
    ancho, alto_ = ancho // 2 * 2, alto_ // 2 * 2
    a0 = int(round((desde or 0) * fps))
    fin = min(hasta, info["duracion"]) if hasta is not None else info["duracion"]
    total = int(math.floor((fin - (desde or 0)) * fps + 1e-3))
    if info.get("cuadros"):
        total = min(total, info["cuadros"] - a0)
    if total <= 0:
        salir("no queda ningún cuadro entre esos segundos")
    cal = calentar(pasos, float(fps))
    for mal in _revisar_memoria(pasos, float(fps)):  # más memoria que el tope dejaría costuras
        salir(mal)
    hilos = hilos or max(1, min(12, (os.cpu_count() or 4) - 2))
    # Pedazos chicos si el video es corto (que trabajen todos los procesos), de hasta `pedazo` cuadros si no.
    pedazo = int(np.clip(math.ceil(total / hilos), 8, pedazo))
    if cal > pedazo:  # un calentamiento largo (el códec desde su cuadro clave) se reparte en pedazos más largos
        pedazo = max(pedazo, min(2 * cal, math.ceil(total / 2)))
    temporal = salida.parent / f".{salida.stem}-pedazos"
    shutil.rmtree(temporal, ignore_errors=True)
    temporal.mkdir(parents=True)
    vent = [(a - (desde or 0), b - (desde or 0)) for a, b in ventanas] if ventanas else None
    tareas = [{"entrada": str(entrada), "info": info, "origen": a0, "k0": a0, "k_fin": a0 + total, "a": a, "b": min(total, a + pedazo),
               "calentar": cal, "pasos": pasos, "captura": captura, "semilla": semilla, "alto": alto_, "ancho": ancho,
               "fps": info["fps"], "crf": crf, "ventanas": vent, "fundido": fundido, "musica": musica,
               "salida": str(temporal / f"{a:07d}.mp4")} for a in range(0, total, pedazo)]
    inicio = time.time()
    hechos = 0
    # Un hilo de BLAS por proceso (lo heredan los procesos al nacer): los procesos ya son el paralelismo, y
    # doce procesos con dieciséis hilos cada uno se ahogan.
    for var in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ.setdefault(var, "1")
    try:
        with ProcessPoolExecutor(max_workers=hilos) as ex:
            en_vuelo: deque = deque()
            pendientes = iter(tareas)
            for t in pendientes:
                en_vuelo.append(ex.submit(_pedazo, t))
                if len(en_vuelo) >= 2 * hilos:
                    break
            while en_vuelo:
                en_vuelo.popleft().result()
                hechos += 1
                siguiente = next(pendientes, None)
                if siguiente is not None:
                    en_vuelo.append(ex.submit(_pedazo, siguiente))
                if not callado and (hechos % max(1, len(tareas) // 5) == 0 or hechos == len(tareas)):
                    dt = time.time() - inicio
                    print(f"  {hechos}/{len(tareas)} pedazos · {min(total, hechos * pedazo) / max(dt, 1e-6):.1f} cuadros/s", flush=True)
        lista = temporal / "lista.txt"
        lista.write_text("".join(f"file '{Path(t['salida']).name}'\n" for t in tareas), encoding="utf-8")
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista)]
        # Cada uno sabe su lugar en la cadena (`_paso`: la semilla de sus eventos es la de la imagen) y a cuántas
        # capturas por segundo va el sensor que tiene antes (`_cps`: la llamada pierde paquetes por captura).
        sonidos = [(nombre, {**p_, "_paso": n, "_cps": _capturas_antes(pasos, n, float(fps)), "_fin": (a0 + total) / float(fps),
                                   "_entrada": str(entrada)})
                   for n, (nombre, p_) in enumerate(pasos) if p_.get("sonido", "ninguno") != "ninguno"]
        if info["audio"] and sonidos:
            cmd += ["-i", str(_audio_de_aparatos(entrada, temporal, (desde or 0.0) + info.get("desfase", 0.0), a0 / float(fps),
                                                 total / float(fps), sonidos, semilla, vent, fundido, float(fps))),
                    "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "192k"]
        elif info["audio"]:
            cmd += ["-ss", f"{(desde or 0) + info.get('desfase', 0.0):.6f}", "-t", f"{total / fps:.6f}", "-i", str(entrada),
                    "-map", "0:v", "-map", "1:a",
                    "-c:a", "aac", "-b:a", "192k"]
        cmd += ["-c:v", "copy", "-movflags", "+faststart", str(salida)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            salir(f"ffmpeg no pudo coser los pedazos: {r.stderr.strip()[-600:]}")
    finally:  # haya salido bien o no, los pedazos no se quedan ocupando disco
        shutil.rmtree(temporal, ignore_errors=True)
    if not callado:
        dt = time.time() - inicio
        print(f"→ {salida} ({total} cuadros en {dt:.0f} s, {total / max(dt, 1e-6):.1f} cuadros/s)")
    return salida


def _audio_de_aparatos(entrada: Path, carpeta: Path, corte: float, t0: float, dura: float, sonidos: list[tuple[str, dict]],
                       semilla: int, ventanas, fundido: float, fps: float = 30.0) -> Path:
    """El audio de la entrada pasado por los aparatos que suenan (la cinta, el micrófono del celular…), sólo
    dentro de las ventanas si las hay. `corte`: desde dónde se lee en el archivo; `t0`: a qué segundo de la imagen
    corresponde (para que el temblor y las arrugas caigan donde caen en la imagen)."""
    import soundfile as sf

    crudo, sale = carpeta / "audio.wav", carpeta / "audio-cinta.wav"
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{corte:.6f}", "-t", f"{dura:.6f}", "-i", str(entrada), "-vn",
                        "-ac", "2", "-ar", str(SR_AUDIO), "-c:a", "pcm_f32le", str(crudo)], capture_output=True, text=True)
    if r.returncode:
        salir(f"no pude leer el audio de {entrada.name}: {r.stderr.strip()[-300:]}")
    x, _ = sf.read(crudo, dtype="float32", always_2d=True)
    y = x
    from . import ruidos

    for n, (nombre, p) in enumerate(sonidos):
        if nombre == "cinta":
            y = sonido_de_cinta(y, p, semilla, t0, indice=n)
        elif nombre in ruidos.RUIDOS:   # la casetera, la antena, la pantalla, la cámara, la llamada (2026-11-22)
            y = ruidos.sonido(nombre, y, {**p, "_fps": fps}, semilla, t0, SR_AUDIO, n)
        else:
            y = _modulo(nombre).sonido(nombre, y, {**p, "_fps": fps}, semilla, t0, SR_AUDIO, n)
    if ventanas:
        rejilla = np.arange(0, dura + 0.01, 0.01)
        e = np.interp(np.arange(len(x)) / SR_AUDIO, rejilla, [envolvente(s, ventanas, fundido) for s in rejilla])[:, None]
        y = x * (1 - e) + y * e
    sf.write(sale, np.clip(y, -1, 1), SR_AUDIO, subtype="FLOAT")
    return sale


def _capturas_antes(pasos: list[tuple[str, dict]], n: int, fps: float) -> float:
    """A cuántas capturas por segundo llega la imagen al aparato `n`: las del último sensor antes, o las del video."""
    for nombre, p in reversed(pasos[:n]):
        if nombre == "sensor" and 0 < p.get("cuadros", 0) < fps:
            return float(p["cuadros"])
    return fps


def leer_cuadros(entrada: Path, tiempos: list[float], alto: int) -> list[np.ndarray]:
    """Cuadros sueltos de la entrada (para las hojas), al alto pedido."""
    if _es_foto(entrada):
        from PIL import Image, ImageOps

        img = ImageOps.exif_transpose(Image.open(entrada)).convert("RGB")
        img = img.resize((int(round(img.width * alto / img.height / 2)) * 2, alto), Image.LANCZOS)
        return [np.asarray(img) for _ in tiempos]
    info = _sonda(entrada)
    ancho = int(round(info["ancho"] * alto / info["alto"] / 2)) * 2
    fps = Fraction(info["fps"])
    return [next(_leer(entrada, info, int(round(t * fps)), 1, alto, ancho)) for t in tiempos]


def comparar(entrada: Path, cadenas: list[str], tiempos: list[float], salida: Path, alto: int = 540,
             musica: dict | None = None) -> Path:
    """Una hoja: una fila por cadena (la primera, la entrada tal cual) y una columna por segundo."""
    from PIL import Image, ImageDraw, ImageFont

    limpios = leer_cuadros(entrada, tiempos, alto)
    info = None if _es_foto(entrada) else _sonda(entrada)
    if info:
        info["fps"] = info["fps_r"]
    fps = float(Fraction(info["fps"])) if info else 30.0
    filas = [("tal cual", limpios)]
    for texto in cadenas:
        cadena, nombre = resolver_cadena(texto)
        pasos, captura, semilla = preparar(cadena)
        _sin_golpes(pasos, musica)
        for mal in _revisar_memoria(pasos, fps):
            salir(mal)
        cal = calentar(pasos, fps)
        cuadros = []
        for t, limpio in zip(tiempos, limpios):
            alto_, ancho_ = limpio.shape[:2]
            ctx = Contexto(semilla, fps, alto_, ancho_)
            ctx.musica = musica
            ctx.fin = info.get("duracion") if info else None
            ctx.entrada = entrada
            k_t = int(round(t * fps))
            k_a = max(0, k_t - cal)
            corrida = (list(_leer(entrada, info, k_a, k_t - k_a, alto_, ancho_)) if info and k_t > k_a
                       else [limpio] * (k_t - k_a))
            for j, previo in enumerate(corrida):  # lo que tiene memoria (fósforo, realimentación) llega como en el video
                ctx.k = k_a + j
                ctx.t = ctx.k / fps
                procesar_cuadro(previo, pasos, captura, ctx)
            ctx.k, ctx.t = k_t, k_t / fps
            cuadros.append(procesar_cuadro(limpio, pasos, captura, ctx))
        filas.append((nombre, cuadros))
    h, w = limpios[0].shape[:2]
    margen = 34
    hoja = Image.new("RGB", (w * len(tiempos), (h + margen) * len(filas)), (7, 9, 13))
    dib = ImageDraw.Draw(hoja)
    fuente = ImageFont.truetype(str(_FUENTE_OSD), 20)
    for r, (nombre, cuadros) in enumerate(filas):
        y0 = r * (h + margen)
        dib.text((8, y0 + 6), nombre, font=fuente, fill=(238, 230, 212))
        for c, (t, img) in enumerate(zip(tiempos, cuadros)):
            hoja.paste(Image.fromarray(img), (c * w, y0 + margen))
            if r == 0:
                dib.text((c * w + w - 70, y0 + 6), f"{t:.1f} s", font=fuente, fill=(126, 147, 170))
    salida.parent.mkdir(parents=True, exist_ok=True)
    hoja.save(salida)
    return salida


def _rotulo(nombre: str, frase: str, ancho: int, alto: int, destino: Path) -> None:
    """El nombre de la cadena arriba a la izquierda, sobre una placa oscura (para el recorrido)."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    grande = ImageFont.truetype(str(_FUENTE_OSD), max(14, int(alto * 0.034)))
    chica = ImageFont.truetype(str(RAIZ / "fuentes" / "ibm-plex-mono" / "IBMPlexMono-Regular.ttf"), max(11, int(alto * 0.019)))
    m = int(alto * 0.03)
    w1 = d.textlength(nombre, font=grande)
    w2 = d.textlength(frase, font=chica) if frase else 0
    alto_placa = int(alto * 0.034 * 1.5 + (alto * 0.019 * 1.6 if frase else 0)) + m // 2
    d.rectangle([m // 2, m // 2, m + max(w1, w2) + m // 2, m // 2 + alto_placa], fill=(7, 9, 13, 190))
    d.text((m, m * 0.7), nombre, font=grande, fill=(230, 180, 60, 255))
    if frase:
        d.text((m, m * 0.7 + alto * 0.034 * 1.45), frase, font=chica, fill=(238, 230, 212, 255))
    img.save(destino)


def recorrido(entrada: Path, cadenas: list[str], salida: Path, desde: float = 0.0, dura: float = 6.0,
              alto: int | None = None, hilos: int | None = None, musica: dict | None = None) -> Path:
    """Las cadenas una tras otra sobre el mismo tramo de la entrada (primero, tal cual), cada una con su nombre:
    un video para mirarlas en el teléfono y elegir."""
    if _es_foto(entrada):
        salir("el recorrido va sobre un video")
    info = _sonda(entrada)
    ancho, alto_ = info["ancho"], info["alto"]
    if alto:
        ancho, alto_ = int(round(ancho * alto / alto_ / 2)) * 2, alto
    ancho, alto_ = ancho // 2 * 2, alto_ // 2 * 2
    temporal = salida.parent / f".{salida.stem}-recorrido"
    shutil.rmtree(temporal, ignore_errors=True)
    temporal.mkdir(parents=True)
    from . import estilos as galeria

    frases = {e["id"]: e["frase"].split(":")[0].split(".")[0] for e in galeria.leer()}
    piezas = []
    for n, texto in enumerate(["tal cual", *cadenas]):
        crudo = temporal / f"{n:02d}-crudo.mp4"
        if texto == "tal cual":
            r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{desde:.3f}", "-t", f"{dura:.3f}", "-i", str(entrada),
                                "-vf", f"scale={ancho}:{alto_}:flags=lanczos", "-c:v", "libx264", "-crf", "16",
                                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(crudo)], capture_output=True, text=True)
            if r.returncode:
                salir(f"ffmpeg: {r.stderr.strip()[-400:]}")
            nombre, frase = "tal cual", ""
        else:
            cadena, nombre = resolver_cadena(texto)
            print(f"  {n}/{len(cadenas)} {nombre}", flush=True)
            procesar(entrada, crudo, cadena, desde=desde, hasta=desde + dura, alto=alto, hilos=hilos, callado=True, musica=musica)
            frase = frases.get(nombre, "")
        rotulo = temporal / f"{n:02d}.png"
        _rotulo(nombre, frase[:90], ancho, alto_, rotulo)
        pieza = temporal / f"{n:02d}.mp4"
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(crudo), "-i", str(rotulo), "-filter_complex",
                            "[0:v][1:v]overlay=0:0:enable='lt(t,3.5)',format=yuv420p", "-c:v", "libx264", "-crf", "18",
                            "-preset", "medium", "-c:a", "copy", str(pieza)], capture_output=True, text=True)
        if r.returncode:
            salir(f"ffmpeg no pudo rotular {nombre}: {r.stderr.strip()[-400:]}")
        piezas.append(pieza)
    lista = temporal / "lista.txt"
    lista.write_text("".join(f"file '{p.name}'\n" for p in piezas), encoding="utf-8")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy",
                        "-movflags", "+faststart", str(salida)], capture_output=True, text=True)
    if r.returncode:
        salir(f"ffmpeg no pudo coser el recorrido: {r.stderr.strip()[-400:]}")
    shutil.rmtree(temporal, ignore_errors=True)
    return salida


def listar() -> None:
    from . import estilos as galeria

    _imagen()
    cadenas = [e for e in galeria.leer() if e["tecnica"].get("comando") == "analogo"]
    if not cadenas:
        print("no hay cadenas analógicas en estilos/")
        return
    for e in cadenas:
        aparatos = " → ".join(a["aparato"] for a in e["tecnica"]["cadena"])
        if e["tecnica"].get("gesto"):
            aparatos = f"gesto: {aparatos} (su muestra, sobre " + (e["tecnica"]["sobre"] if isinstance(e["tecnica"].get("sobre"), str)
                                                                  else " → ".join(a["aparato"] for a in e["tecnica"].get("sobre", []))) + ")"
        print(f"{e['id']:<26} {e['estado']:<10} {aparatos}")
        print(f"{'':<26} {e['frase']}")
    print(f"{len(cadenas)} cadenas · aparatos: {', '.join(APARATOS)}")


def cmd(a) -> None:
    """`python montaje.py analogo …` (ver el encabezado de este archivo)."""
    if a.cadenas:
        listar()
        return
    if getattr(a, "aparatos", False):   # para la consola del panel: los aparatos con sus perillas
        print(json.dumps({"aparatos": aparatos_json(), "cadenas": cadenas_json()}, ensure_ascii=False))
        return
    if not a.entrada:
        salir("falta la entrada: un video o una foto (o --cadenas para ver las cadenas de la galería)")
    entrada = ruta_entrada(a.entrada)
    musica = musica_de(a.golpes) if getattr(a, "golpes", None) else None
    if a.recorrido:
        cadenas = [c.strip() for c in a.recorrido.split(",") if c.strip()]
        destino = Path(a.salida) if a.salida else entrada.with_name(f"{entrada.stem}-recorrido.mp4")
        print(f"→ {recorrido(entrada, cadenas, destino, a.desde or 0.0, a.segundos, a.alto, a.hilos, musica)}")
        return
    if a.comparar:
        tiempos = [float(x) for x in a.en.split(",")]
        destino = Path(a.salida) if a.salida else entrada.with_name(f"{entrada.stem}-comparar.png")
        print(f"→ {comparar(entrada, [c for c in a.comparar.split(',') if c.strip()], tiempos, destino, a.alto or 540, musica)}")
        return
    if not a.cadena:
        salir("falta --cadena (un estilo de la galería, o la cadena en JSON) o --comparar")
    cadena, nombre = resolver_cadena(a.cadena, getattr(a, "gesto", None) or [])
    if getattr(a, "automatizacion", None):   # los movimientos de las perillas, grabados en la consola
        datos = json.loads(Path(a.automatizacion).read_text(encoding="utf-8"))
        pistas = datos.get("automatizacion", []) if isinstance(datos, dict) else datos
        cadena = {**cadena, "automatizacion": [*cadena.get("automatizacion", []), *pistas]}
        nombre += "-a-mano"
    destino = Path(a.salida) if a.salida else entrada.with_name(f"{entrada.stem}-{nombre}.mp4")
    if destino.resolve() == entrada:
        salir("la salida no puede pisar la entrada")
    procesar(entrada, destino, cadena, desde=a.desde, hasta=a.hasta, segundos=a.segundos, alto=a.alto,
             ventanas=[tuple(v) for v in a.ventana] if a.ventana else None, fundido=a.fundido, hilos=a.hilos, musica=musica)
