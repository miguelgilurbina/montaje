"""La consola de mezcla de los 90: los efectos de la memoria de cuadro (un aparato de imagen de la mesa analógica).

Miguel, el 2026-11-21: «acumulemos más efectos». Los videos de boda, de quince años y de los canales locales de los
90 pasaban por un mezclador de video con memoria de cuadro (el Panasonic WJ-MX50 y sus parecidos): digitalizaba la
señal y le hacía efectos que el operador tocaba a mano. La consola trabaja en la imagen (era digital por dentro) y
se encadena con la cámara antes y con la cinta después, como en la sala de edición:

- `mosaico`: la imagen en cuadrados (`bloque`, en pixeles de 720 de ancho); a ratos, crece y vuelve.
- `estrobo`: la imagen se queda `cada` cuadros y salta: el movimiento a golpes.
- `multi`: una cuadrícula de `celdas` × `celdas` que se va llenando, una celda cada `cada` cuadros, con el momento
  que pasaba: el tiempo repartido en la pantalla.
- `pintura`: la luz y el color en pocos escalones (`niveles`), como un afiche.
- `negativo`: la imagen invertida.
- `llave`: donde la imagen es oscura (bajo `umbral`) se ve lo que la memoria guardó hace un rato (cada `memoria`
  segundos guarda un cuadro): dos tiempos encimados.

`cuando`: `siempre`, `a ratos` (`por_minuto` veces, de `dura` segundos, como un operador que aprieta el botón) o
`al pulso`: en los golpes de la canción (`golpes_cada`: el uno de cada compás, cada golpe o los picos), durante
`dura_golpes` golpes; como la sincronía con la música del MX50. Al pulso necesita los golpes: `analogo --golpes
<proyecto>` (el probador pasa los del banco).
"""

from __future__ import annotations

import math

import numpy as np

from . import analogo as A

EFECTOS = ("mosaico", "estrobo", "multi", "pintura", "negativo", "llave")

POR_DEFECTO = {
    "consola": {"efecto": "mosaico", "cuando": "siempre", "por_minuto": 4.0, "dura": 2.0, "bloque": 16, "cada": 4,
                "celdas": 3, "niveles": 4, "umbral": 0.35, "memoria": 4.0, "golpes_cada": "compas", "dura_golpes": 1.0},
}
RANGOS = {
    "consola": {"efecto": EFECTOS, "cuando": ("siempre", "a ratos", "al pulso"), "por_minuto": (0, 60), "dura": (0.2, 10),
                "bloque": (2, 96), "cada": (1, 60), "celdas": (2, 4), "niveles": (2, 12), "umbral": (0, 1),
                "memoria": (0.5, 7), "golpes_cada": ("compas", "golpe", "pico"), "dura_golpes": (0.1, 8)},
}


def necesita_golpes(pasos: list[tuple[str, dict]]) -> bool:
    return any(nombre == "consola" and p["cuando"] == "al pulso" for nombre, p in pasos)


def _al_pulso(ctx, p: dict) -> float | None:
    return A.al_pulso(ctx, p["golpes_cada"], p["dura_golpes"])


def errores(nombre: str, a: dict) -> list[str]:
    mal = []
    for k in ("cada", "celdas", "niveles"):
        if k in a and (isinstance(a[k], bool) or not isinstance(a[k], int)):
            mal.append(f"consola.{k}: un número entero")
    return mal


CONSEJO = {"consola": "baja `celdas` o `cada` del multi, `cada` del estrobo o la `memoria` de la llave"}


def calentar(pasos: list[tuple[str, dict]], fps: float, solo: int | None = None) -> int:
    """El estrobo guarda su cuadro; el multi, sus celdas; la llave, su memoria. Con `solo`, sólo el aparato de ese
    lugar de la cadena."""
    n = 0
    for i, (nombre, p) in enumerate(pasos):
        if nombre != "consola" or (solo is not None and i != solo):
            continue
        if p["efecto"] == "estrobo":
            n = max(n, p["cada"] + 1)
        elif p["efecto"] == "multi":
            n = max(n, p["celdas"] ** 2 * p["cada"] + 1)
        elif p["efecto"] == "llave":
            n = max(n, int(math.ceil(p["memoria"] * fps)) + 1)
    return n


def _a(img: np.ndarray, w: int, h: int, filtro) -> np.ndarray:
    from PIL import Image

    return np.asarray(Image.fromarray(A._ocho_bits(img)).resize((max(1, w), max(1, h)), filtro), np.float32) / 255


def _mosaico(img: np.ndarray, bloque: float) -> np.ndarray:
    from PIL import Image

    h, w = img.shape[:2]
    b = bloque * w / 720
    if b < 1.5:
        return img.copy()
    chica = _a(img, int(math.ceil(w / b)), int(math.ceil(h / b)), Image.BOX)
    return _a(chica, w, h, Image.NEAREST)


def _pintura(img: np.ndarray, niveles: int) -> np.ndarray:
    """Cada canal en pocos escalones, como un afiche (con el color un poco subido: escalonar en la luz y el color
    por separado lo apagaba todo a gris)."""
    y = (img @ np.array([0.299, 0.587, 0.114], np.float32))[..., None]
    vivo = np.clip(y + 1.35 * (img - y), 0, 1)
    n = niveles - 1
    return (np.round(vivo * n) / n).astype(np.float32)


def consola(img: np.ndarray, p: dict, ctx) -> np.ndarray:
    from PIL import Image

    h, w = img.shape[:2]
    semilla = ctx.semilla * 100 + ctx.paso
    est = ctx.estado.setdefault(("consola", ctx.paso), {})
    efecto = p["efecto"]
    # Lo que tiene memoria se actualiza en cada cuadro, prendido o no: sin costura entre pedazos.
    if efecto == "estrobo":
        n = ctx.k // p["cada"]
        if est.get("n") != n or est.get("forma") != img.shape:
            est.update(n=n, forma=img.shape, cuadro=img.copy())
    elif efecto == "multi":
        c = p["celdas"]
        n = ctx.k // p["cada"]
        if est.get("forma") != img.shape:
            est.update(forma=img.shape, tablero=np.zeros_like(img), n=None)
        if est.get("n") != n:
            est["n"] = n
            celda = n % (c * c)
            fy, fx = divmod(celda, c)
            y0, y1 = fy * h // c, (fy + 1) * h // c
            x0, x1 = fx * w // c, (fx + 1) * w // c
            margen = max(1, h // 180)
            chica = _a(img, x1 - x0 - 2 * margen, y1 - y0 - 2 * margen, Image.BILINEAR)
            est["tablero"][y0:y1, x0:x1] = 0
            est["tablero"][y0 + margen:y1 - margen, x0 + margen:x1 - margen] = chica
    elif efecto == "llave":
        n = ctx.k // max(1, int(round(p["memoria"] * ctx.fps)))
        if est.get("n") != n or est.get("forma") != img.shape:
            est.update(n=n, forma=img.shape, memoria=img.copy())
    u = None
    if p["cuando"] != "siempre":
        u = A.evento(semilla, "consola", ctx.t, p["por_minuto"], p["dura"]) if p["cuando"] == "a ratos" else _al_pulso(ctx, p)
        if u is None:
            return img.copy()
    if efecto == "mosaico":
        fuerza = 1.0 if u is None else math.sin(math.pi * u) ** 0.6   # a ratos: crece y vuelve
        return _mosaico(img, p["bloque"] * fuerza)
    if efecto == "estrobo":
        return est["cuadro"].copy()
    if efecto == "multi":
        return est["tablero"].copy()
    if efecto == "pintura":
        return _pintura(img, p["niveles"])
    if efecto == "negativo":
        return (1 - img).astype(np.float32)
    luma = img @ np.array([0.299, 0.587, 0.114], np.float32)
    m = np.clip((p["umbral"] - luma) / 0.08 + 0.5, 0, 1)[..., None]
    return (img * (1 - m) + est["memoria"] * m).astype(np.float32)


APARATOS = {"consola": consola}
