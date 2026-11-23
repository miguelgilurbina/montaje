"""La radio: imágenes que llegan por el aire y la canción que se ve (tres aparatos de imagen de la mesa analógica).

Miguel, el 2026-11-22, en el mapa de la galería: eligió «La radio» entre los territorios para abrir. Curiana es una
radio («Transmisión cultural desde Abya Yala. 88.8 FM.»): estos aparatos son la radio mirada.

`radiofoto` (perilla `modo`), la foto que llega por un canal de sonido, línea por línea, de arriba abajo:

- **sstv**, la televisión de barrido lento de los radioaficionados: la foto en color, chica (320 × 256), que llega con
  el ruido de la banda: puntos de colores, rayas donde se cruza otra emisora, la imagen inclinada si el reloj del que
  recibe no calza con el del que manda.
- **fax**, el radiofacsímil: el mapa del tiempo que llegaba por onda corta a los barcos, impreso en papel térmico,
  con la franja de fase al principio.
- **telefoto**, la foto de prensa que llegaba por cable a los diarios: gris, con las rayas del tambor.

Cada `dura` segundos llega una: el encabezado, la imagen que se dibuja (el cuadro que había al empezar) y un rato
quieta. Con `sonido: tonos`, se oyen los tonos que la dibujan: cada línea, la altura del tono sigue el brillo de la
imagen (de 1 500 a 2 300 Hz, como en las de verdad). Está acelerado: una sstv de verdad tarda de 36 segundos a dos
minutos, así que los tonos no los lee un programa de radioaficionado.

`dial` (un gesto): alguien mueve el dial. La imagen se pierde en la estática mientras la aguja recorre la escala de
FM, y vuelve cuando la aguja se asienta en el 88.8. Con `sonido: sintonia`, la estática y el silbido entre emisoras.
Con `inicio`, una vez al empezar el video (la emisora que se sintoniza para abrir), además de los de `sintonizar`.

`osciloscopio`: la canción dibujada como una figura verde en la pantalla de un osciloscopio (un canal contra el otro,
corrido unos milisegundos para que una canción en mono también dibuje), con la retícula y el fósforo que dura.

La marca en el osciloscopio (Miguel, del osciloscopio: «Me encantaría expandir esta función»; eligió «La marca en el
osciloscopio», 2026-11-23). Con `dibujo`, cada `cada` segundos y durante `dura`, la canción se aparta (queda un 6 %) y el haz dibuja
la marca: la espiral del isotipo (el trazo de `~/Videos/montaje/marca/espiral.svg`, fuera del repo), el nombre en la
letra Curiana Cartel, o las dos. El dibujo es sonido: el canal izquierdo lleva la x y el derecho la y, y el haz
recorre la figura 50 veces por segundo (un zumbido grave con sus armónicos). Con `sonido: marca`, ese sonido va en el
audio: mirado en un osciloscopio de verdad, el audio dibuja la marca. La imagen y el sonido usan la misma cuenta
(`marca_xy`, `marca_ganancia`).

Los tiempos y los niveles son [sin verificar] salvo las frecuencias de los tonos (1 200 Hz el sincronismo, 1 500 el
negro, 2 300 el blanco: las de la norma sstv y las del radiofacsímil).
"""

from __future__ import annotations

import math
import subprocess

import numpy as np

from . import analogo as A
from .pelicula import _a_tamano, _desenfocar, evento_con_id

MODOS = ("sstv", "fax", "telefoto")
POR_DEFECTO = {
    "radiofoto": {"modo": "sstv", "dura": 6.0, "ruido": 0.3, "inclinacion": 0.0, "sonido": "ninguno"},
    "dial": {"sintonizar": 0.0, "dura": 1.8, "frecuencia": 88.8, "inicio": False, "sonido": "ninguno"},
    "osciloscopio": {"mezcla": 0.0, "tinta": "verde", "trazo": 1.0, "retardo_ms": 2.0, "dibujo": "cancion", "cada": 8.0,
                     "dura": 3.0, "texto": "CURIANA", "sonido": "ninguno"},
}
DIBUJOS = ("cancion", "espiral", "nombre", "espiral-y-nombre")
RANGOS = {
    "radiofoto": {"modo": MODOS, "dura": (2, 7.5), "ruido": (0, 1), "inclinacion": (-1, 1), "sonido": ("ninguno", "tonos")},
    "dial": {"sintonizar": (0, 20), "dura": (0.8, 3), "frecuencia": (88, 108), "sonido": ("ninguno", "sintonia")},
    "osciloscopio": {"mezcla": (0, 1), "tinta": ("verde", "oro"), "trazo": (0.3, 3), "retardo_ms": (0, 20),
                     "dibujo": DIBUJOS, "cada": (0, 60), "dura": (0.5, 60), "sonido": ("ninguno", "marca")},
}

#: Las partes de una llegada, en fracción de `dura`: el encabezado, la imagen que se dibuja, y quieta.
ENCABEZADO, DIBUJO = 0.06, 0.64
#: Las líneas de cada modo (lo que se oye; la imagen de la sstv también tiene esas líneas).
LINEAS = {"sstv": 256, "fax": 180, "telefoto": 180}
SSTV_ALTO, SSTV_ANCHO = 256, 320
PAPEL_TERMICO = np.array([0.92, 0.92, 0.89], np.float32)
TINTA_TERMICA = np.array([0.14, 0.13, 0.16], np.float32)
PAPEL_TELEFOTO = np.array([0.90, 0.87, 0.80], np.float32)
FOSFORO = {"verde": np.array([0.45, 1.0, 0.55], np.float32), "oro": np.array([0.90, 0.71, 0.24], np.float32)}
LUMA = np.array([0.299, 0.587, 0.114], np.float32)
ORO = np.array([0.90, 0.71, 0.24], np.float32)


def errores(nombre: str, a: dict) -> list[str]:
    if nombre == "dial" and "inicio" in a and not isinstance(a["inicio"], bool):
        return ["dial.inicio: true o false"]
    if nombre == "osciloscopio" and "texto" in a and (not isinstance(a["texto"], str) or not a["texto"].strip()):
        return ["osciloscopio.texto: el nombre que dibuja el haz"]
    if nombre == "osciloscopio" and a.get("dibujo", "cancion") != "cancion" and a.get("cada", 8.0) and a.get("dura", 3.0) > a.get("cada", 8.0):
        return ["osciloscopio: la `dura` de la marca no puede ser más larga que `cada`"]
    return []


#: El número del movimiento del dial al empezar (para su cuenta: no choca con los de `evento_con_id`, que pasan del
#: millón).
INICIO = 7


def movimiento(p: dict, t: float, inicio: float, semilla: int) -> tuple[float, int] | None:
    """El movimiento del dial en el segundo t, si hay uno: (parte, número). El del principio va primero."""
    if p.get("inicio") and inicio <= t < inicio + p["dura"]:
        return (t - inicio) / p["dura"], INICIO
    if p["sintonizar"]:
        ev = evento_con_id(semilla, "dial", t, p["sintonizar"], p["dura"])
        # Uno que empezó mientras sonaba el del principio no va (el sonido tampoco lo pone).
        if ev is not None and p.get("inicio") and t - ev[0] * p["dura"] < inicio + p["dura"]:
            return None
        return ev
    return None


CONSEJO = {"radiofoto": "acorta la `dura` de la radiofoto"}


def calentar(pasos: list[tuple[str, dict]], fps: float, solo: int | None = None) -> int:
    """La radiofoto dibuja el cuadro que había al empezar su llegada; el osciloscopio, el fósforo que dura."""
    n = 0
    for i, (nombre, p) in enumerate(pasos):
        if solo is not None and i != solo:
            continue
        if nombre == "radiofoto":
            n = max(n, int(math.ceil(p["dura"] * fps)) + 2)
        if nombre == "osciloscopio":
            n = max(n, 12)
    return n


# ── La radiofoto ───────────────────────────────────────────────────────────

def llegada(t: float, dura: float) -> tuple[int, float]:
    """Qué llegada es y en qué parte va (0 a 1) en el segundo t."""
    c = math.floor(t / dura)
    return c, (t - c * dura) / dura


def _recibida(img: np.ndarray, p: dict, semilla: int, c: int, alto: int, ancho: int) -> np.ndarray:
    """La imagen como llega entera (con su ruido, fijo para esa llegada), al tamaño de salida."""
    r = np.random.default_rng([semilla, A._num("radiofoto"), c])
    modo = p["modo"]
    if modo == "sstv":
        chica = _a_tamano(img, SSTV_ALTO, SSTV_ANCHO)
        ruido = p["ruido"]
        # Puntos de colores sueltos y líneas enteras donde se cruza otra emisora.
        puntos = (r.random((SSTV_ALTO, SSTV_ANCHO)) < 0.01 * ruido)[..., None] * r.random((SSTV_ALTO, SSTV_ANCHO, 3))
        chica = np.where(puntos.any(-1, keepdims=True), puntos, chica)
        for y in np.nonzero(r.random(SSTV_ALTO) < 0.03 * ruido)[0]:
            chica[y] = np.clip(chica[y] + r.standard_normal((SSTV_ANCHO, 3)) * 0.35 * ruido + r.uniform(-0.2, 0.3), 0, 1)
        if p["inclinacion"]:   # el reloj que no calza: cada línea un poco más corrida
            corre = (np.arange(SSTV_ALTO) * p["inclinacion"] * 0.25).astype(np.int32)
            chica = np.stack([np.roll(chica[y], corre[y], axis=0) for y in range(SSTV_ALTO)])
        # En la pantalla del que recibe, a lo alto, con barras a los lados (la sstv es 5:4).
        h = alto
        w = int(round(h * SSTV_ANCHO / SSTV_ALTO))
        grande = np.asarray(_ampliar_rgb(chica, h, min(w, ancho)), np.float32)
        sale = np.zeros((alto, ancho, 3), np.float32)
        x0 = (ancho - grande.shape[1]) // 2
        sale[:, x0:x0 + grande.shape[1]] = grande
        return sale
    lum = _a_tamano(img, alto, ancho) @ LUMA
    if modo == "fax":
        lum = np.clip((lum - 0.15) / 0.7, 0, 1)
        lum = np.round(lum * 3) / 3                                       # el papel térmico: pocos grises
        lum = _suavizar_lineas(lum, r, 0.04 + 0.05 * p["ruido"])
        motas = r.random(lum.shape) < 0.002 * p["ruido"]
        lum = np.where(motas, 0.0, lum)
        sale = TINTA_TERMICA + (PAPEL_TERMICO - TINTA_TERMICA) * lum[..., None]
        fase = int(alto * 0.07)                                           # la franja de fase, arriba
        sale[:fase] = TINTA_TERMICA
        sale[:fase, int(0.04 * ancho):int(0.07 * ancho)] = PAPEL_TERMICO
    else:
        lum = _suavizar_lineas(np.clip(lum, 0, 1), r, 0.03 + 0.04 * p["ruido"])
        tambor = 1 - 0.05 * (np.sin(np.arange(ancho) / ancho * 2 * math.pi * 90) > 0.95)[None, :]
        sale = PAPEL_TELEFOTO * (0.12 + 0.88 * lum * tambor)[..., None]
    if p["inclinacion"]:
        corre = (np.arange(alto) * p["inclinacion"] * 0.04).astype(np.int32)
        sale = np.stack([np.roll(sale[y], corre[y], axis=0) for y in range(alto)])
    return sale.astype(np.float32)


def _ampliar_rgb(chica: np.ndarray, h: int, w: int) -> np.ndarray:
    from PIL import Image

    return np.asarray(Image.fromarray(A._ocho_bits(chica)).resize((w, h), Image.BILINEAR), np.float32) / 255


def _suavizar_lineas(lum: np.ndarray, r: np.random.Generator, desparejo: float) -> np.ndarray:
    """Cada línea impresa con su propia intensidad: las franjas finas de lo que llega línea por línea."""
    franjas = 1 + desparejo * r.standard_normal(lum.shape[0]).astype(np.float32)
    return np.clip(lum * franjas[:, None], 0, 1)


def radiofoto(img: np.ndarray, p: dict, ctx) -> np.ndarray:
    alto, ancho = ctx.alto, ctx.ancho
    semilla = ctx.semilla * 100 + ctx.paso
    c, u = llegada(ctx.t, p["dura"])
    est = ctx.estado.setdefault(("radiofoto", ctx.paso), {})
    if est.get("llegada") != c:   # el primer cuadro de la llegada: ése es el que se manda
        est["llegada"] = c
        est["recibida"] = _recibida(img, p, semilla, c, alto, ancho)
    recibida = est["recibida"]
    fondo = np.zeros((alto, ancho, 3), np.float32) if p["modo"] == "sstv" else (
        np.broadcast_to(PAPEL_TERMICO if p["modo"] == "fax" else PAPEL_TELEFOTO, (alto, ancho, 3)).copy())
    dibujado = min(1.0, max(0.0, (u - ENCABEZADO) / DIBUJO))
    y = int(round(dibujado * alto))
    sale = fondo
    sale[:y] = recibida[:y]
    if 0 < dibujado < 1:   # la línea que está llegando, más clara
        linea = slice(max(0, y - 2), min(alto, y + 1))
        sale[linea] = np.minimum(1.0, recibida[linea] * 0.6 + 0.5)
    elif u < ENCABEZADO and p["modo"] == "sstv":   # el encabezado: la pantalla espera con ruido de la banda
        rng = ctx.rng("radiofoto-espera")
        sale = sale + rng.random((alto, 1, 1)).astype(np.float32) * 0.08 * (1 + p["ruido"])
    return np.clip(sale, 0, 1).astype(np.float32)


def lineas_de(img: np.ndarray, modo: str) -> np.ndarray:
    """Para el sonido: la imagen en sus líneas de transmisión, (líneas, muestras, 3) RGB 0–1."""
    n = LINEAS[modo]
    return _a_tamano(img, n, SSTV_ANCHO if modo == "sstv" else 360)


# ── El dial ────────────────────────────────────────────────────────────────

def desintonia(u: float, ident: int, semilla: int) -> tuple[float, float]:
    """Cuánto se pierde la emisora (0 en sintonía, 1 perdida) y cuánto se corre la aguja (MHz), en la parte u de un
    movimiento del dial: se va, busca, y se asienta. La imagen y el sonido usan esta misma cuenta."""
    if ident == INICIO:   # al empezar el video la emisora ya está perdida: el movimiento empieza buscando
        u = 0.3 + 0.7 * u
    r = np.random.default_rng([semilla, A._num("dial"), ident])
    lejos = r.uniform(4, 9) * (1 if r.random() < 0.5 else -1)
    if u < 0.3:
        a = u / 0.3
        d, corre = a ** 0.7, lejos * a
    elif u < 0.75:
        a = (u - 0.3) / 0.45
        corre = lejos * (1 - a) + 1.2 * math.sin(a * 9 + r.uniform(0, 6))
        d = min(1.0, 0.55 + 0.45 * abs(math.sin(a * 13 + r.uniform(0, 6))))
    else:
        a = (u - 0.75) / 0.25
        corre = 1.2 * math.sin(9 + 0.3) * (1 - a) ** 2 * 0.4
        d = (1 - a) ** 1.8
    return float(np.clip(d, 0, 1)), float(corre)


_ESCALAS: dict = {}


def _escala(alto: int, ancho: int) -> tuple[np.ndarray, np.ndarray, int, int, int, int]:
    """La escala del dial (88 a 108 MHz), dibujada una vez: color, máscara, y dónde está (y0, x0, x1)."""
    from PIL import Image, ImageDraw, ImageFont

    clave = (alto, ancho)
    if clave not in _ESCALAS:
        h = max(24, int(0.11 * alto))
        y0 = alto - h - int(0.05 * alto)
        x0, x1 = int(0.12 * ancho), int(0.88 * ancho)
        capa = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
        d = ImageDraw.Draw(capa)
        d.rectangle([x0 - int(0.02 * ancho), y0, x1 + int(0.02 * ancho), y0 + h], fill=(7, 9, 13, 200))
        try:
            letra = ImageFont.truetype(str(A._FUENTE_OSD), max(10, int(h * 0.3)))
        except OSError:
            letra = ImageFont.load_default()
        for mhz in range(88, 109):
            x = x0 + (mhz - 88) / 20 * (x1 - x0)
            largo = 0.38 if mhz % 2 == 0 else 0.2
            d.line([(x, y0 + h * 0.12), (x, y0 + h * (0.12 + largo))], fill=(243, 234, 212, 230), width=max(1, h // 30))
            if mhz % 4 == 0:
                d.text((x, y0 + h * 0.62), str(mhz), fill=(243, 234, 212, 230), font=letra, anchor="mm")
        d.text((x0 - int(0.035 * ancho), y0 + h * 0.62), "FM", fill=(126, 147, 170, 230), font=letra, anchor="rm")
        a = np.asarray(capa, np.float32) / 255
        _ESCALAS[clave] = (a[..., :3], a[..., 3], y0, x0, x1, h)
    return _ESCALAS[clave]


def dial(img: np.ndarray, p: dict, ctx) -> np.ndarray:
    if not p["sintonizar"] and not p.get("inicio"):
        return img
    semilla = ctx.semilla * 100 + ctx.paso
    ev = movimiento(p, ctx.t, ctx.inicio, semilla)
    if ev is None:
        return img
    u, ident = ev
    d, corre = desintonia(u, ident, semilla)
    alto, ancho = img.shape[:2]
    rng = ctx.rng("dial")
    # La emisora que se va: la imagen se desgarra en líneas y se tapa de estática.
    sale = img
    if d > 0.02:
        corr = (rng.standard_normal(alto) * 30 * d + 40 * d * np.sin(np.arange(alto) / 23 + 7 * ctx.t)).astype(np.int32)
        filas = np.arange(alto)[:, None]
        cols = np.clip(np.arange(ancho)[None, :] - corr[:, None], 0, ancho - 1)
        sale = img[filas, cols]
        gris = sale @ LUMA
        sale = gris[..., None] + (sale - gris[..., None]) * (1 - d)
        nieve = 0.2 + 0.55 * rng.random((alto // 2 + 1, ancho // 2 + 1)).astype(np.float32)
        nieve = np.repeat(np.repeat(nieve, 2, 0), 2, 1)[:alto, :ancho, None]
        sale = sale * (1 - 0.72 * d) + nieve * 0.72 * d       # la emisora no se va del todo: queda su fantasma
    # La escala, que aparece y se va, con la aguja en su lugar.
    color, mascara, y0, x0, x1, h = _escala(alto, ancho)
    aparece = min(1.0, u / 0.08, (1 - u) / 0.08)
    sale = sale * (1 - mascara[..., None] * aparece) + color * mascara[..., None] * aparece
    mhz = min(108.0, max(88.0, p["frecuencia"] + corre))
    x = int(x0 + (mhz - 88) / 20 * (x1 - x0))
    g = max(2, ancho // 500)
    sale[y0 + 2:y0 + h - 2, max(0, x - g):x + g] = ORO * aparece + sale[y0 + 2:y0 + h - 2, max(0, x - g):x + g] * (1 - aparece)
    return np.clip(sale, 0, 1).astype(np.float32)


# ── El osciloscopio ────────────────────────────────────────────────────────

_AUDIOS: dict = {}
SR = 48000


def _audio(ruta) -> np.ndarray | None:
    """El audio de la entrada, estéreo a 48 kHz (se lee una vez por proceso)."""
    if ruta is None:
        return None
    ruta = str(ruta)
    if ruta not in _AUDIOS:
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", ruta, "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                           capture_output=True)
        x = np.frombuffer(r.stdout, np.float32).reshape(-1, 2) if r.returncode == 0 and r.stdout else None
        _AUDIOS[ruta] = (x, float(np.percentile(np.abs(x), 99.5)) + 1e-4) if x is not None and len(x) else (None, 1.0)
    return _AUDIOS[ruta]


def _reticula(alto: int, ancho: int) -> np.ndarray:
    clave = ("reticula", alto, ancho)
    if clave not in _ESCALAS:
        r = np.zeros((alto, ancho), np.float32)
        lado = int(0.86 * alto)
        y0, x0 = (alto - lado) // 2, (ancho - lado) // 2
        for k in range(11):
            y = y0 + k * lado // 10
            x = x0 + k * lado // 10
            r[y, x0:x0 + lado] = 0.16 if k != 5 else 0.28
            r[y0:y0 + lado, x] = 0.16 if k != 5 else 0.28
        _ESCALAS[clave] = (r, y0, x0, lado)
    return _ESCALAS[clave]


def osciloscopio(img: np.ndarray, p: dict, ctx) -> np.ndarray:
    from scipy import ndimage

    alto, ancho = img.shape[:2]
    reticula, y0, x0, lado = _reticula(alto, ancho)
    fosforo = FOSFORO[p["tinta"]]
    clave = ("osciloscopio", ctx.paso)
    antes = ctx.estado.get(clave)
    traza = np.zeros((alto, ancho), np.float32) if antes is None else antes * 0.55   # el fósforo que dura
    audio = _audio(getattr(ctx, "entrada", None))
    if audio is not None and audio[0] is not None:
        x, pico = audio
        b = int(ctx.t * SR)
        a = max(0, b - int(SR * 1.5 / ctx.fps))
        retardo = int(p["retardo_ms"] / 1000 * SR)
        if b - a > 8 and b <= len(x):
            izq = x[a:b, 0]
            der = x[max(0, a - retardo):max(0, b - retardo), 1]
            n = min(len(izq), len(der))
            izq, der = izq[-n:], der[-n:]
            if p["dibujo"] != "cancion":   # la marca: la canción se aparta y el haz dibuja la figura
                ts = (b - n + np.arange(n)) / SR
                g = marca_ganancia(ts, p)
                mx, my = marca_xy(ts, p)
                izq = izq * (1 - MARCA_APARTA * g) + mx * g * MARCA_AMPLITUD * pico
                der = der * (1 - MARCA_APARTA * g) + my * g * MARCA_AMPLITUD * pico
            # Entre muestra y muestra, puntos intermedios: el haz es una línea, no puntos sueltos.
            fino = np.linspace(0, n - 1, n * 4)
            xs = np.interp(fino, np.arange(n), izq) / pico
            ys = np.interp(fino, np.arange(n), der) / pico
            px = np.clip((x0 + lado / 2 + xs * lado * 0.45).astype(np.int32), 0, ancho - 1)
            py = np.clip((y0 + lado / 2 - ys * lado * 0.45).astype(np.int32), 0, alto - 1)
            np.add.at(traza, (py, px), 0.08 * p["trazo"])
    ctx.estado[clave] = traza
    brillo = np.clip(traza, 0, 1.5)
    halo = ndimage.gaussian_filter(brillo, max(1.0, alto / 270)) * 2.5
    luz = np.clip(brillo + halo, 0, 1.6)
    fondo = img * 0.35 * p["mezcla"]
    sale = fondo + fosforo * (luz + reticula)[..., None] + np.clip(luz - 1, 0, 1)[..., None] * 0.6
    return np.clip(sale, 0, 1).astype(np.float32)


# ── La marca en el osciloscopio ────────────────────────────────────────────

#: La espiral del isotipo (copiada del sitio a la biblioteca de medios: la marca no va en este repo público).
ESPIRAL = A.MEDIOS / "marca" / "espiral.svg"
LETRA = A.RAIZ / "fuentes" / "curiana-cartel" / "CurianaCartel-Regular.ttf"
#: Cuántas veces por segundo recorre el haz la figura, y cuántos puntos tiene el recorrido.
TRAZOS_POR_SEGUNDO, PUNTOS = 50.0, 2400
#: El tamaño de la marca contra la canción (en veces el pico de la canción), y cuánto se aparta la canción mientras
#: suena la marca (con un 15 % el dibujo temblaba donde la canción es fuerte; con un 6 % se lee).
MARCA_AMPLITUD, MARCA_APARTA = 0.8, 0.94
_RECORRIDOS: dict = {}


def _cubica(p0, p1, p2, p3, n: int = 24) -> np.ndarray:
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3


def _cuadratica(p0, p1, p2, n: int = 16) -> np.ndarray:
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2


def _espiral() -> list[np.ndarray]:
    """El trazo de la espiral (un solo camino de curvas en el SVG), en puntos."""
    import re

    if not ESPIRAL.exists():
        return []
    d = re.search(r'\sd="([^"]+)"', ESPIRAL.read_text(encoding="utf-8"))
    if not d:
        return []
    fichas = re.findall(r"[MmCcLlZz]|-?\d*\.?\d+", d.group(1))
    puntos, actual, cmd, i = [], np.zeros(2), None, 0
    while i < len(fichas):
        if fichas[i].isalpha():
            cmd = fichas[i]
            i += 1
            continue
        if cmd in ("M", "L"):
            actual = np.array([float(fichas[i]), float(fichas[i + 1])])
            puntos.append(actual[None, :])
            i += 2
        elif cmd == "C":
            c = [np.array([float(fichas[i + k]), float(fichas[i + k + 1])]) for k in (0, 2, 4)]
            puntos.append(_cubica(actual, *c)[1:])
            actual = c[2]
            i += 6
        else:
            i += 1
    return [np.concatenate(puntos) * np.array([1, -1])] if puntos else []   # la y del SVG va hacia abajo


def _nombre(texto: str) -> list[np.ndarray]:
    """El contorno de cada letra del nombre, en la letra Curiana Cartel."""
    from fontTools.pens.recordingPen import RecordingPen
    from fontTools.ttLib import TTFont

    fuente = TTFont(str(LETRA))
    glifos, mapa = fuente.getGlyphSet(), fuente.getBestCmap()
    contornos, corre = [], 0.0
    for ch in texto:
        nombre = mapa.get(ord(ch))
        if nombre is None:
            continue
        pluma = RecordingPen()
        glifos[nombre].draw(pluma)
        actual, uno = np.zeros(2), []
        for op, args in pluma.value:
            pts = [np.array(a, float) + [corre, 0] for a in args]
            if op == "moveTo":
                actual, uno = pts[0], [pts[0][None, :]]
            elif op == "lineTo":
                uno.append(pts[0][None, :])
                actual = pts[0]
            elif op == "curveTo":
                uno.append(_cubica(actual, *pts)[1:])
                actual = pts[-1]
            elif op == "qCurveTo":   # TrueType: los puntos de control seguidos llevan un punto sobre la curva implícito
                ctrl, fin = pts[:-1], pts[-1]
                for k, c in enumerate(ctrl):
                    sig = fin if k == len(ctrl) - 1 else (c + ctrl[k + 1]) / 2
                    uno.append(_cuadratica(actual, c, sig)[1:])
                    actual = sig
            elif op in ("closePath", "endPath") and uno:
                uno.append(uno[0][:1])
                contornos.append(np.concatenate(uno))
                uno = []
        corre += glifos[nombre].width
    return contornos


def _recorrido(dibujo: str, texto: str) -> np.ndarray:
    """La figura entera como un solo recorrido del haz, de `PUNTOS` puntos repartidos por largo, entre −1 y 1. La
    espiral se recorre de ida y de vuelta (sin salto); entre letras, el haz salta rápido (el salto casi no se ve)."""
    clave = (dibujo, texto)
    if clave in _RECORRIDOS:
        return _RECORRIDOS[clave]
    partes = []
    if dibujo in ("espiral", "espiral-y-nombre"):
        for c in _espiral():
            partes.append(("espiral", np.concatenate([c, c[::-1]])))
    if dibujo in ("nombre", "espiral-y-nombre") or not partes:
        for c in _nombre(texto):
            partes.append(("nombre", c))
    if not partes:
        _RECORRIDOS[clave] = np.zeros((PUNTOS, 2))
        return _RECORRIDOS[clave]

    def encajar(cs, x0, x1, y0, y1):
        todo = np.concatenate(cs)
        lo, hi = todo.min(0), todo.max(0)
        esc = min((x1 - x0) / max(hi[0] - lo[0], 1e-6), (y1 - y0) / max(hi[1] - lo[1], 1e-6))
        centro = (lo + hi) / 2
        medio = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
        return [(c - centro) * esc + medio for c in cs]

    esp = [c for k, c in partes if k == "espiral"]
    nom = [c for k, c in partes if k == "nombre"]
    if esp and nom:
        esp, nom = encajar(esp, -0.55, 0.55, -0.05, 0.95), encajar(nom, -0.95, 0.95, -0.95, -0.25)
    elif esp:
        esp = encajar(esp, -0.95, 0.95, -0.95, 0.95)
    else:
        nom = encajar(nom, -0.95, 0.95, -0.4, 0.4)
    camino = np.concatenate(esp + nom)
    largo = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(camino, axis=0).T))])
    # Los saltos entre contornos no cuentan como largo: el haz los cruza en un punto (casi no deja traza).
    tramos = np.diff(largo)
    saltos = tramos > 0.25
    tramos[saltos] = 0.002
    largo = np.concatenate([[0], np.cumsum(tramos)])
    u = np.linspace(0, largo[-1], PUNTOS, endpoint=False)
    rec = np.stack([np.interp(u, largo, camino[:, 0]), np.interp(u, largo, camino[:, 1])], -1)
    _RECORRIDOS[clave] = rec
    return rec


def marca_xy(t: np.ndarray, p: dict) -> tuple[np.ndarray, np.ndarray]:
    """Dónde está el haz en cada instante t (segundos): la figura recorrida `TRAZOS_POR_SEGUNDO` veces por segundo, que
    se mece un poco de lado (como si girara en la pantalla)."""
    rec = _recorrido(p["dibujo"], p["texto"])
    fase = (np.asarray(t) * TRAZOS_POR_SEGUNDO) % 1.0 * len(rec)
    i0 = np.floor(fase).astype(np.int64) % len(rec)
    f = fase - np.floor(fase)
    punto = rec[i0] * (1 - f[:, None]) + rec[(i0 + 1) % len(rec)] * f[:, None]
    giro = np.cos(0.55 * np.sin(2 * np.pi * np.asarray(t) / 9.0))
    return punto[:, 0] * giro, punto[:, 1]


def marca_ganancia(t: np.ndarray, p: dict) -> np.ndarray:
    """Cuánto de marca hay en cada instante (0 a 1): cada `cada` segundos, durante `dura`, con entradas suaves."""
    t = np.asarray(t, float)
    if p["dibujo"] == "cancion":
        return np.zeros_like(t)
    if not p["cada"]:
        return np.ones_like(t)
    u = t % p["cada"]
    rampa = min(0.4, p["dura"] / 3)
    return np.clip(np.minimum(u / rampa, (p["dura"] - u) / rampa), 0, 1)


def sonido(nombre: str, x: np.ndarray, p: dict, semilla: int, t0: float, sr: int, indice: int) -> np.ndarray:
    """La marca en el audio: donde la imagen la dibuja, la canción se aparta y el haz suena (x a la izquierda, y a la
    derecha). Mirado en un osciloscopio de verdad, el audio dibuja la marca."""
    if nombre != "osciloscopio" or p.get("sonido", "ninguno") == "ninguno" or not len(x) or p["dibujo"] == "cancion":
        return x
    t = t0 + np.arange(len(x)) / sr
    g = marca_ganancia(t, p)
    mx, my = marca_xy(t, p)
    audio = _audio(p.get("_entrada"))
    pico = audio[1] if audio is not None and audio[0] is not None else float(np.percentile(np.abs(x), 99.5)) + 1e-4
    sale = x * (1 - MARCA_APARTA * g)[:, None]
    marca = np.stack([mx, my], -1) * (g * MARCA_AMPLITUD * pico)[:, None]
    if sale.shape[1] == 2:
        sale = sale + marca
    else:
        sale = sale + marca.mean(1, keepdims=True)
    return sale.astype(np.float32)


APARATOS = {"radiofoto": radiofoto, "dial": dial, "osciloscopio": osciloscopio}
