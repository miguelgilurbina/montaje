"""Lo digital temprano: el sensor y la compresión (dos aparatos de la mesa analógica).

Miguel, el 2026-11-21: «acumulemos más efectos». Después del VHS vino lo digital barato: el celular con cámara
(2004–2008), la webcam, el «modo video» de la cámara de fotos de bolsillo, la MiniDV. Como en la mesa, no se pinta
un «efecto pixelado» encima: la imagen pasa por un sensor chico y por un códec, y lo que se ve sale de ahí.

## `sensor`

La cámara: pocos pixeles (`resolucion`), pocas capturas por segundo (`cuadros`) y a veces perdidas (`irregular`:
al teléfono no le alcanzaba), el ruido que sube en lo oscuro, poco rango (`rango`: las luces se recortan en seco,
no como en la película), el balance de blancos que se equivoca (`balance`, `tinte`), la exposición automática que
tarda y se pasa (`exposicion`), el realce de bordes (`detalle`), la columna clara que deja una luz en un CCD
(`mancha`), el borde morado de las luces (`franja`), el obturador que lee línea por línea y tuerce lo que se mueve
(`rodar`) y la lectura salteada de los sensores baratos, que deja serruchos (`aliasing`). La imagen sale al tamaño
del sensor; al final de la cadena vuelve a la salida con barras o llenando (`encuadre`), suave o con sus pixeles
(`ampliar`). Con `sonido`, el micrófono del aparato.

## `compresion`

El códec, escrito aquí (en bloques de 8×8 con la transformada del coseno, como los de la época): `jpeg` (cada
cuadro solo, como el MJPEG de las cámaras de fotos), `dv` (cada cuadro solo, color 4:1:1, alta calidad: la MiniDV)
y `mpeg` (un cuadro clave cada `gop` capturas y, entre ellos, sólo lo que cambió: H.263 y MPEG-4 de los celulares).
Con poca `calidad`, lo que se mueve arrastra bloques viejos y cada cuadro clave «revienta» la imagen de nuevo. Los
`errores` son paquetes perdidos: en `mpeg` el error se arrastra con el movimiento hasta el próximo cuadro clave; en
`dv`, rectángulos con colores equivocados o con un pedazo del cuadro anterior. Con `residuo` bajo, el códec sólo
mueve lo que ya tenía y no corrige: el «datamosh», la imagen que se derrite.

Las referencias están en `direccion/ANALOGO.md` («Lo digital temprano»).
"""

from __future__ import annotations

import math

import numpy as np

from . import analogo as A

TINTES = {"azul": (0.84, 0.97, 1.18), "naranja": (1.15, 1.0, 0.78), "verde": (0.9, 1.08, 0.88)}
SONIDOS = ("ninguno", "celular", "webcam", "camara")
MODOS = ("mpeg", "jpeg", "dv")

POR_DEFECTO = {
    "sensor": {"resolucion": [320, 240], "cuadros": 0, "irregular": 0.0, "ruido": 0.5, "rango": 0.5, "balance": 0.0,
               "tinte": "azul", "exposicion": 0.0, "detalle": 0.4, "mancha": 0.0, "franja": 0.0, "rodar": 0.0,
               "aliasing": 0.3, "encuadre": "barras", "ampliar": "suave", "sonido": "ninguno"},
    "compresion": {"modo": "mpeg", "calidad": 0.4, "gop": 30, "busqueda": 7, "residuo": 1.0, "errores": 0.0},
}
RANGOS = {
    "sensor": {"cuadros": (0, 60), "irregular": (0, 1), "ruido": (0, 3), "rango": (0, 1), "balance": (0, 1),
               "tinte": tuple(TINTES), "exposicion": (0, 1), "detalle": (0, 2), "mancha": (0, 2), "franja": (0, 2),
               "rodar": (0, 2), "aliasing": (0, 1), "encuadre": ("barras", "llenar"), "ampliar": ("suave", "pixeles"),
               "sonido": SONIDOS},
    "compresion": {"modo": MODOS, "calidad": (0, 1), "gop": (1, 120), "busqueda": (0, 15), "residuo": (0, 1),
                   "errores": (0, 1)},
}


def errores(nombre: str, a: dict) -> list[str]:
    mal = []
    if nombre == "sensor" and "resolucion" in a:
        r = a["resolucion"]
        if not (isinstance(r, list) and len(r) == 2 and all(isinstance(v, int) and 32 <= v <= 1920 for v in r)):
            mal.append("sensor.resolucion: [ancho, alto] en pixeles, entre 32 y 1920 (por ejemplo [176, 144])")
    if nombre == "compresion":
        for k in ("gop", "busqueda"):
            if k in a and (isinstance(a[k], bool) or not isinstance(a[k], int)):
                mal.append(f"compresion.{k}: un número entero")
    return mal


def _por_captura(pasos, fps: float) -> int:
    """Cuántos cuadros del video dura una captura del sensor (1 si no hay sensor o captura a la par del video)."""
    for nombre, p in pasos:
        if nombre == "sensor" and 0 < p["cuadros"] < fps:
            return int(math.ceil(fps / p["cuadros"]))
    return 1


CONSEJO = {"sensor": "sube los `cuadros` del sensor o baja su `irregular`",
           "compresion": "baja el `gop` o sube los `cuadros` del sensor"}


def calentar(pasos: list[tuple[str, dict]], fps: float, solo: int | None = None) -> int:
    """El sensor recuerda sus últimas capturas (las que se repiten, la exposición que tarda); el códec necesita
    volver a su último cuadro clave. Con capturas perdidas, lo que se ve puede ser de hasta dos capturas atrás, y
    lo anterior a eso (el movimiento que tuerce, el cuadro clave), de una más. Con `solo`, sólo el aparato de ese
    lugar de la cadena."""
    f = _por_captura(pasos, fps)
    irregular = any(nombre == "sensor" and p["irregular"] for nombre, p in pasos)
    atras = 2 if irregular else 0
    n = 0
    for i, (nombre, p) in enumerate(pasos):
        if solo is not None and i != solo:
            continue
        if nombre == "sensor":
            n = max(n, f * (1 + atras) + 1, (2 + atras) * f + 1 if p["rodar"] else 0, 30 * f if p["exposicion"] else 0)
        if nombre == "compresion":
            n = max(n, (p["gop"] + 1 + atras) * f + 2 if p["modo"] == "mpeg" else ((2 + atras) * f + 1 if p["errores"] else 0))
    return n


# ── El sensor ──────────────────────────────────────────────────────────────

def _perdida(semilla: int, i: int, irregular: float) -> bool:
    return i > 0 and np.random.default_rng([semilla, A._num("perdida"), i]).random() < 0.45 * irregular


def captura(ctx, p: dict, semilla: int) -> int:
    """Qué captura del sensor se ve en este cuadro del video: el sensor captura a `cuadros` por segundo y, si es
    `irregular`, pierde algunas (nunca más de dos seguidas, ni la primera) y repite la anterior."""
    cps = p["cuadros"] if 0 < p["cuadros"] < ctx.fps else ctx.fps
    j = int(math.floor(ctx.k * cps / ctx.fps + 1e-6))
    if p["irregular"] and _perdida(semilla, j, p["irregular"]):
        return j - 1 if not _perdida(semilla, j - 1, p["irregular"]) else max(0, j - 2)
    return j


def _ampliar(plano: np.ndarray, h: int, w: int) -> np.ndarray:
    from PIL import Image

    return np.asarray(Image.fromarray(np.ascontiguousarray(plano, np.float32), mode="F").resize((w, h), Image.BILINEAR))


def _achicar(img: np.ndarray, w: int, h: int, aliasing: float) -> np.ndarray:
    """La escena en el sensor: recortada a su proporción y a sus pixeles. Un sensor bueno promedia; uno barato
    lee salteado y deja serruchos."""
    from PIL import Image

    ih, iw = img.shape[:2]
    if iw / ih > w / h:
        cw = int(round(ih * w / h))
        img = img[:, (iw - cw) // 2:(iw - cw) // 2 + cw]
    else:
        ch = int(round(iw * h / w))
        img = img[(ih - ch) // 2:(ih - ch) // 2 + ch]
    fuente = Image.fromarray(A._ocho_bits(img))
    caja = np.asarray(fuente.resize((w, h), Image.BOX), np.float32) / 255
    if not aliasing:
        return caja
    salteada = np.asarray(fuente.resize((w, h), Image.NEAREST), np.float32) / 255
    return caja * (1 - aliasing) + salteada * aliasing


def _movimiento_global(antes: np.ndarray, ahora: np.ndarray) -> tuple[float, float]:
    """Cuánto se corrió la imagen entera entre dos capturas (correlación de fase), en pixeles (dy, dx)."""
    h, w = ahora.shape
    v = np.outer(np.hanning(h), np.hanning(w)).astype(np.float32)
    F = np.fft.fft2(ahora * v) * np.conj(np.fft.fft2(antes * v))
    r = np.fft.ifft2(F / (np.abs(F) + 1e-9)).real
    dy, dx = np.unravel_index(int(np.argmax(r)), r.shape)
    return float(dy - h if dy > h // 2 else dy), float(dx - w if dx > w // 2 else dx)


def _sensor_captura(img: np.ndarray, p: dict, ctx, semilla: int, cid: int) -> np.ndarray:
    from scipy import ndimage

    w, h = p["resolucion"]
    x = _achicar(img, w, h, p["aliasing"])
    luma = x @ np.array([0.299, 0.587, 0.114], np.float32)
    t = cid / (p["cuadros"] if 0 < p["cuadros"] < ctx.fps else ctx.fps)
    rng = np.random.default_rng([semilla, A._num("sensor"), cid])
    ganancia = 1.0
    if p["exposicion"]:  # la exposición automática persigue el gris medio, tarde, y se pasa (sub-amortiguada)
        clave = ("exposicion", ctx.paso)
        g, v, ultimo = ctx.estado.get(clave, (None, 0.0, None))
        objetivo = float(np.clip(0.42 / max(float(luma.mean()), 0.02), 0.4, 3.0))
        if g is None:
            g = objetivo
        elif ultimo != cid:
            v = 0.72 * v + 0.11 * (objetivo - g)
            g = g + v
        ctx.estado[clave] = (g, v, cid)
        ganancia = float(np.clip(g / objetivo, 0.3, 3.0)) ** p["exposicion"]
        x = x * ganancia
    if p["balance"]:  # el balance de blancos que se equivoca, y se corre despacio
        k = p["balance"] * (0.75 + 0.25 * A.suave(semilla, "balance", t, 0.07))
        x = x * (1 + k * (np.array(TINTES[p["tinte"]], np.float32) - 1))
    if p["mancha"]:  # una luz fuerte rebalsa el CCD y deja su columna de arriba abajo
        exceso = np.clip(x.max(axis=2) - 0.95, 0, None).mean(axis=0)
        x = x + (ndimage.gaussian_filter1d(exceso, 0.8) * 7 * p["mancha"])[None, :, None] * np.array([1.0, 0.94, 1.0], np.float32)
    if p["ruido"]:  # sube en lo oscuro (la ganancia); el del color, en manchas
        L = np.clip(luma * ganancia, 0, 1)[..., None]
        x = x + rng.standard_normal(x.shape[:2], dtype=np.float32)[..., None] * (0.018 * p["ruido"] * (0.4 + (1 - L)))
        cr = rng.standard_normal((max(2, h // 2), max(2, w // 2), 2), dtype=np.float32)
        cr = np.stack([_ampliar(cr[..., c], h, w) for c in range(2)], axis=-1) * (0.03 * p["ruido"]) * (1 - L) ** 1.5
        x = x + np.concatenate([cr[..., :1], -0.5 * (cr[..., :1] + cr[..., 1:]), cr[..., 1:]], axis=-1)
        fijo = np.random.default_rng([semilla, A._num("columnas")]).standard_normal(w).astype(np.float32)
        x = x + (0.005 * p["ruido"] * fijo)[None, :, None]   # el patrón fijo de columnas del sensor
    r = p["rango"]
    if r:  # poco rango: las luces se recortan en seco (cada canal por su lado: la piel se pone amarilla) y los negros se juntan
        tope = 1 - 0.2 * r
        x = np.clip((x / tope - 0.05 * r) / (1 - 0.05 * r), 0, 1)
        x = x + 0.35 * r * (x * x * (3 - 2 * x) - x)
    if p["franja"]:  # el borde morado alrededor de lo que se quemó
        quemado = (x.min(axis=2) > 0.97).astype(np.float32)
        borde = np.clip(ndimage.gaussian_filter(quemado, 1.3) * 2.2 - quemado, 0, 1)[..., None]
        x = x + borde * p["franja"] * 0.55 * (np.array([0.62, 0.12, 0.95], np.float32) - x)
    if p["detalle"]:  # el realce de bordes, con su halo
        x = x + p["detalle"] * (x - ndimage.gaussian_filter(x, (0.8, 0.8, 0)))
    if p["rodar"]:  # el obturador que lee línea por línea: lo que se mueve en horizontal sale inclinado
        clave = ("rodar", ctx.paso)
        chica = luma[:: max(1, h // 96), :: max(1, w // 128)]
        antes = ctx.estado.get(clave)
        ctx.estado[clave] = (cid, chica)
        if antes is not None and antes[0] != cid and antes[1].shape == chica.shape:
            _, dx = _movimiento_global(antes[1], chica)
            dx *= w / chica.shape[1]
            corr = -dx * p["rodar"] * (np.arange(h, dtype=np.float32) / h - 0.5)
            cols = np.arange(w, dtype=np.float32)[None, :] - corr[:, None]
            c0 = np.clip(np.floor(cols).astype(np.int32), 0, w - 1)
            c1 = np.clip(c0 + 1, 0, w - 1)
            f = (cols - np.floor(cols))[..., None]
            filas = np.arange(h)[:, None]
            x = x[filas, c0] * (1 - f) + x[filas, c1] * f
    return np.clip(x, 0, 1).astype(np.float32)


def sensor(img: np.ndarray, p: dict, ctx) -> np.ndarray:
    semilla = ctx.semilla * 100 + ctx.paso
    cid = captura(ctx, p, semilla)
    ctx.encuadre = (p["encuadre"], p["ampliar"])
    clave = ("capturas", ctx.paso)
    guardadas: dict = ctx.estado.setdefault(clave, {})
    if cid not in guardadas:
        guardadas[cid] = _sensor_captura(img, p, ctx, semilla, cid)
        for viejo in [c for c in guardadas if c < cid - 3]:
            del guardadas[viejo]
    ctx.estado["captura"] = cid
    return guardadas[cid].copy()


# ── El códec ───────────────────────────────────────────────────────────────

#: Las tablas de cuantización de la norma JPEG (anexo K): la de luma y la de color.
TABLA_Y = np.array([16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55, 14, 13, 16, 24, 40, 57, 69, 56,
                    14, 17, 22, 29, 51, 87, 80, 62, 18, 22, 37, 56, 68, 109, 103, 77, 24, 35, 55, 64, 81, 104, 113, 92,
                    49, 64, 78, 87, 103, 121, 120, 101, 72, 92, 95, 98, 112, 100, 103, 99], np.float32).reshape(8, 8)
TABLA_C = np.full((8, 8), 99, np.float32)
TABLA_C[:4, :4] = np.array([17, 18, 24, 47, 18, 21, 26, 66, 24, 26, 56, 99, 47, 66, 99, 99], np.float32).reshape(4, 4)


def _escala(calidad: float) -> float:
    """De la calidad (0–1) al multiplicador de las tablas: 1 ≈ casi sin pérdida, 0 ≈ lo peor de un celular."""
    return 0.12 * 30 ** (1 - calidad)


def _bloques(x: np.ndarray) -> np.ndarray:
    h, w = x.shape
    return x.reshape(h // 8, 8, w // 8, 8).transpose(0, 2, 1, 3)


def _plano(b: np.ndarray) -> np.ndarray:
    by, bx = b.shape[:2]
    return b.transpose(0, 2, 1, 3).reshape(by * 8, bx * 8)


def _dct(x: np.ndarray) -> np.ndarray:
    from scipy.fft import dctn

    return dctn(_bloques(x), type=2, axes=(2, 3), norm="ortho")


def _idct(c: np.ndarray) -> np.ndarray:
    from scipy.fft import idctn

    return _plano(idctn(c, type=2, axes=(2, 3), norm="ortho"))


def _intra(x: np.ndarray, tabla: np.ndarray, escala: float) -> np.ndarray:
    q = tabla * escala
    return _idct(np.round(_dct(x - 128) / q) * q) + 128


def _inter(residuo: np.ndarray, escala: float) -> np.ndarray:
    """El residuo con el cuantizador de zona muerta de los códecs de movimiento (la matriz plana de 16): lo chico
    se vuelve cero, y ese bloque no se actualiza."""
    q = 16 * escala
    c = _dct(residuo)
    return _idct(np.trunc(c / q) * q)


def _a_ycc(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = rgb * 255
    y = x @ np.array([0.299, 0.587, 0.114], np.float32)
    cb = 128 + x @ np.array([-0.168736, -0.331264, 0.5], np.float32)
    cr = 128 + x @ np.array([0.5, -0.418688, -0.081312], np.float32)
    return y, cb, cr


def _a_rgb(y: np.ndarray, cb: np.ndarray, cr: np.ndarray) -> np.ndarray:
    return np.clip(np.stack([y + 1.402 * (cr - 128), y - 0.344136 * (cb - 128) - 0.714136 * (cr - 128),
                             y + 1.772 * (cb - 128)], axis=-1) / 255, 0, 1).astype(np.float32)


def _submuestreo(modo: str) -> tuple[int, int]:
    return (1, 4) if modo == "dv" else (2, 2)


def _achicar_color(c: np.ndarray, sy: int, sx: int) -> np.ndarray:
    h, w = c.shape
    return c.reshape(h // sy, sy, w // sx, sx).mean(axis=(1, 3))


def _agrandar_color(c: np.ndarray, sy: int, sx: int) -> np.ndarray:
    return np.repeat(np.repeat(c, sy, axis=0), sx, axis=1)


def _movimiento(ahora: np.ndarray, ref: np.ndarray, radio: int) -> np.ndarray:
    """El vector de cada macrobloque (16×16): dónde está en el cuadro anterior lo que se parece más (búsqueda
    completa en ±radio). Quedarse quieto gana los empates."""
    H, W = ahora.shape
    by, bx = H // 16, W // 16
    refp = np.pad(ref, radio, mode="edge")
    mejor = np.full((by, bx), np.inf, np.float32)
    mv = np.zeros((by, bx, 2), np.int32)
    for dy in range(-radio, radio + 1):
        for dx in range(-radio, radio + 1):
            cand = refp[radio + dy:radio + dy + H, radio + dx:radio + dx + W]
            sad = np.abs(ahora - cand).reshape(by, 16, bx, 16).sum(axis=(1, 3))
            if dy == 0 and dx == 0:
                sad = sad - 256 * 1.5
            m = sad < mejor
            mejor[m] = sad[m]
            mv[m] = (dy, dx)
    return mv


def _predecir(ref: np.ndarray, mv: np.ndarray, b: int) -> np.ndarray:
    """El cuadro anterior movido bloque por bloque (bloques de `b` pixeles)."""
    by, bx = mv.shape[:2]
    r = max(1, int(np.abs(mv).max()))
    refp = np.pad(ref, r, mode="edge")
    yy = (np.arange(by) * b)[:, None, None, None] + np.arange(b)[None, None, :, None] + mv[..., 0][:, :, None, None] + r
    xx = (np.arange(bx) * b)[None, :, None, None] + np.arange(b)[None, None, None, :] + mv[..., 1][:, :, None, None] + r
    return refp[yy, xx].transpose(0, 2, 1, 3).reshape(by * b, bx * b)


def _errores_mpeg(planos: list[np.ndarray], rng: np.random.Generator, mb: tuple[int, int]) -> None:
    """Un paquete perdido: desde un macrobloque, una tira de bloques con basura (un vector equivocado, el color
    corrido). Queda en la referencia, así que se arrastra con el movimiento hasta el próximo cuadro clave."""
    by, bx = mb
    inicio = int(rng.integers(by * bx))
    largo = int(rng.integers(2, max(3, int(bx * 1.6))))
    y, cb, cr = planos
    desvio = rng.uniform(-45, 45), rng.uniform(-70, 70), rng.uniform(-70, 70)
    for n in range(inicio, min(by * bx, inicio + largo)):
        fy, fx = divmod(n, bx)
        sy, sx = slice(fy * 16, fy * 16 + 16), slice(fx * 16, fx * 16 + 16)
        y[sy, sx] = np.roll(y[sy, sx], int(rng.integers(-6, 7)), axis=int(rng.integers(2))) + desvio[0]
        cy, cx = slice(fy * 8, fy * 8 + 8), slice(fx * 8, fx * 8 + 8)
        cb[cy, cx] += desvio[1]
        cr[cy, cx] += desvio[2]


def _errores_intra(rgb: np.ndarray, antes: np.ndarray | None, rng: np.random.Generator, modo: str) -> np.ndarray:
    """Los dropouts de la cinta digital: rectángulos (32×8 en la MiniDV, su macrobloque) con colores equivocados,
    o con el pedazo del cuadro anterior que el reproductor puso para taparlos. Vienen en grupos, en una zona."""
    h, w = rgb.shape[:2]
    bw, bh = (32, 8) if modo == "dv" else (16, 16)
    cy, cx = rng.uniform(0, h), rng.uniform(0, w)
    for _ in range(int(rng.integers(3, 18))):
        y0 = int(np.clip(cy + rng.normal(0, h * 0.08), 0, h - bh)) // bh * bh
        x0 = int(np.clip(cx + rng.normal(0, w * 0.12), 0, w - bw)) // bw * bw
        bloque = rgb[y0:y0 + bh, x0:x0 + bw]
        tapar = rng.random() < 0.5   # siempre se sortea: el azar de los que siguen no depende de si hay cuadro anterior
        if antes is not None and tapar and antes.shape == rgb.shape:
            bloque[:] = antes[y0:y0 + bh, x0:x0 + bw]
        else:
            color = rng.uniform(0, 1, 3).astype(np.float32)
            bloque[:] = np.clip(0.55 * color + 0.45 * np.roll(bloque, int(rng.integers(-bw, bw)), axis=1), 0, 1)
    return rgb


def compresion(img: np.ndarray, p: dict, ctx) -> np.ndarray:
    semilla = ctx.semilla * 100 + ctx.paso
    cid = ctx.estado.get("captura", ctx.k)
    clave = ("compresion", ctx.paso)
    st = ctx.estado.get(clave)
    if st is not None and st["cid"] == cid:
        return st["salida"].copy()
    h0, w0 = img.shape[:2]
    modo = p["modo"]
    sy, sx = _submuestreo(modo)
    m = 32 if modo == "dv" else 16
    H, W = -(-h0 // m) * m, -(-w0 // m) * m
    x = np.pad(img, ((0, H - h0), (0, W - w0), (0, 0)), mode="edge")
    y, cb, cr = _a_ycc(x)
    cb, cr = _achicar_color(cb, sy, sx), _achicar_color(cr, sy, sx)
    escala = _escala(p["calidad"])
    rng = np.random.default_rng([semilla, A._num("codec"), cid])
    gop = p["gop"]
    clave_nueva = st is None or modo != "mpeg" or st["cid"] // gop != cid // gop or st["forma"] != (H, W)
    if clave_nueva:  # el cuadro clave (o cada cuadro, en jpeg y dv): solo, con las tablas
        e = escala * (1.3 if modo == "mpeg" else 1.0)
        planos = [_intra(y, TABLA_Y, e), _intra(cb, TABLA_C, e), _intra(cr, TABLA_C, e)]
    else:  # un cuadro de diferencia: lo de antes movido, más lo que cambió (si alcanzó)
        ry, rcb, rcr = st["ref"]
        mv = _movimiento(y, ry, p["busqueda"]) if p["busqueda"] else np.zeros((H // 16, W // 16, 2), np.int32)
        mvc = np.floor_divide(mv, 2)
        pred = [_predecir(ry, mv, 16), _predecir(rcb, mvc, 8), _predecir(rcr, mvc, 8)]
        planos = [pr + p["residuo"] * _inter(actual - pr, escala) for pr, actual in zip(pred, (y, cb, cr))]
    if p["errores"] and modo == "mpeg" and rng.random() < 0.35 * p["errores"]:
        _errores_mpeg(planos, rng, (H // 16, W // 16))
    planos = [np.clip(pl, 0, 255).astype(np.float32) for pl in planos]
    rgb = _a_rgb(planos[0], _agrandar_color(planos[1], sy, sx), _agrandar_color(planos[2], sy, sx))[:h0, :w0]
    limpia = rgb
    if p["errores"] and modo != "mpeg" and rng.random() < 0.35 * p["errores"]:
        # El reproductor tapa con el cuadro anterior tal como salió del códec (sin sus propios dropouts): así la
        # memoria es de un cuadro y los pedazos en paralelo no dejan costura.
        rgb = _errores_intra(rgb.copy(), None if st is None else st["limpia"], rng, modo)
    ctx.estado[clave] = {"cid": cid, "ref": planos, "salida": rgb, "limpia": limpia, "forma": (H, W)}
    return rgb.copy()


# ── El micrófono ───────────────────────────────────────────────────────────

#: Banda (Hz), frecuencia de muestreo del aparato, ruido propio (dBFS), cuánto aprieta el control automático de
#: ganancia y si zumba la tierra del USB. El celular: la banda angosta del habla telefónica (AMR-NB muestrea a
#: 8 kHz); los demás, [sin verificar]: puntos de partida.
MICROFONOS = {
    "celular": {"banda": (300, 3400), "sr": 8000, "ruido_db": -50, "agc": 0.85, "zumbido": 0.0},
    "webcam": {"banda": (120, 7000), "sr": 16000, "ruido_db": -46, "agc": 0.7, "zumbido": 1.0},
    "camara": {"banda": (100, 5200), "sr": 11025, "ruido_db": -52, "agc": 0.5, "zumbido": 0.0},
}


def sonido(nombre: str, x: np.ndarray, p: dict, semilla: int, t0: float, sr: int, indice: int) -> np.ndarray:
    """El audio (n × canales) por el micrófono del aparato: mono, banda angosta, el control automático de ganancia
    que sube el ruido en los silencios y recorta los picos, y la muestra gruesa del aparato."""
    from scipy.signal import butter, sosfilt

    if p.get("sonido", "ninguno") == "ninguno" or not len(x):
        return x
    m = MICROFONOS[p["sonido"]]
    n = len(x)
    mono = x.mean(axis=1).astype(np.float64)
    rng = np.random.default_rng([semilla, A._num("microfono"), indice])
    mono = mono + rng.standard_normal(n) * 10 ** (m["ruido_db"] / 20)
    if m["zumbido"]:  # la tierra del USB: 60 Hz y sus armónicos
        t = t0 + np.arange(n) / sr
        mono = mono + sum(10 ** ((-52 - 6 * k) / 20) * np.sin(2 * np.pi * 60 * (k + 1) * t) for k in range(4))
    # El micrófono chico pierde los graves; el filtro antes de la muestra gruesa corta empinado arriba.
    bajo, alto = m["banda"]
    y = sosfilt(butter(2, bajo, btype="highpass", fs=sr, output="sos"), mono)
    y = sosfilt(butter(8, alto, btype="lowpass", fs=sr, output="sos"), y)
    if m["agc"]:  # el control automático: sigue la envolvente (sube rápido, baja lento) y la lleva a un nivel
        env = np.abs(y)
        a_sube, a_baja = math.exp(-1 / (0.01 * sr)), math.exp(-1 / (0.4 * sr))
        seg = np.empty(n)
        e = 0.0
        for i0 in range(0, n, 256):  # por tramos de 256 muestras: la envolvente no necesita más detalle
            pico = float(env[i0:i0 + 256].max())
            e = a_sube ** 256 * e + (1 - a_sube ** 256) * pico if pico > e else a_baja ** 256 * e + (1 - a_baja ** 256) * pico
            seg[i0:i0 + 256] = e
        ganancia = np.clip(0.3 / np.maximum(seg, 1e-4), 0.5, 12.0) ** m["agc"]
        y = y * ganancia
    paso = max(1, int(round(sr / m["sr"])))
    if paso > 1:  # la muestra del aparato, vuelta a la de salida sin filtro: un brillo metálico arriba
        bajo = y[::paso]
        y = np.interp(np.arange(n) / paso, np.arange(len(bajo)), bajo)
    if p["sonido"] == "celular":  # ley μ en 8 bits: el grano del habla digital barata
        mu = 255.0
        c = np.sign(y) * np.log1p(mu * np.minimum(np.abs(y), 1)) / np.log1p(mu)
        c = np.round(c * 127) / 127
        y = np.sign(c) * np.expm1(np.abs(c) * np.log1p(mu)) / mu
    y = np.tanh(1.6 * y) / 1.6
    return np.stack([y, y], axis=1).astype(np.float32)


APARATOS = {"sensor": sensor, "compresion": compresion}
