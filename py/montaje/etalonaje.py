"""El etalonaje: el color de la imagen pasado por una tabla de color (una LUT 3D), un aparato de imagen de la mesa
analógica.

Miguel, el 2026-11-23, después de mirar lo que trae OpenMontage: «y podríamos sacar nosotros algo de ahí pero
hacerlo nosotros mismos?»; eligió el etalonaje con LUT (era G2/K3 en PROPUESTAS.md). Escrito desde cero, sin mirar
código ajeno.

Una tabla de color dice, para cada color que entra, qué color sale: una grilla de N×N×N colores, y entre los puntos de
la grilla se interpola (trilineal). Es el formato con que los editores comparten correcciones (`.cube`, de Adobe):
lo que se haga en otro editor entra a la mesa, y lo de la mesa sale a otro editor.

`color` (perilla `tabla`):

- **noche-de-curiana**: la paleta de la marca (`direccion/PALETA.md`) como etalonaje: las sombras van al índigo
  `#26396a`, las luces al oro de arena `#e6b43c`, los medios quedan; el color baja un poco.
- **noche-americana**: la noche filmada de día: subexpuesta, desaturada y azul, con las luces contenidas.
- **infrarroja**: la película infrarroja de falso color (como la Aerochrome): lo verde de la vegetación sale rojo o
  magenta, el rojo sale amarillo, el cielo se oscurece. Sin infrarrojo de verdad, la vegetación se adivina por el
  verde: es una aproximación [sin verificar contra la película].
- **blanqueo-saltado**: el revelado que se salta el blanqueo (bleach bypass): la plata queda con el color, la imagen
  sale desaturada, dura y metálica.
- **proceso-cruzado**: la diapositiva revelada como negativo (E-6 en C-41): luces amarillo verdosas, sombras cian, el
  contraste alto y el color corrido.
- **archivo**: un `.cube` (`archivo`: ruta absoluta o dentro de los medios), hecho en otro editor.

`fuerza` funde el original con lo etalonado. Las tablas de la mesa se escriben a `.cube` con
`python montaje.py color --exportar <tabla> <salida.cube>` (para usarlas en otro editor).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from . import analogo as A

TAMANO = 33   # los puntos por lado de las tablas escritas aquí (el tamaño de uso común)
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)


def _hex(c: str) -> np.ndarray:
    return np.array([int(c[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)


def _lin(x):
    return np.power(np.clip(x, 0, 1), 2.2)


def _gam(x):
    return np.power(np.clip(x, 0, 1), 1 / 2.2)


def _sat(c, s):
    y = (c @ LUMA)[..., None]
    return y + s * (c - y)


def _suave(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def noche_de_curiana(c: np.ndarray) -> np.ndarray:
    y = (c @ LUMA)[..., None]
    sombra, luz = _hex("#26396a"), _hex("#e6b43c")
    c = _sat(c, 0.78)
    peso_sombra = (1 - _suave(y, 0.0, 0.5)) * 0.65
    peso_luz = _suave(y, 0.45, 1.0) * 0.55
    # Mezcla en «luz suave»: el tono entra sin cambiar el brillo de cada pixel.
    sale = c * (1 - peso_sombra - peso_luz) + (y * sombra / max(float(sombra @ LUMA), 1e-3)) * peso_sombra \
        + (y * luz / max(float(luz @ LUMA), 1e-3)) * peso_luz
    return np.clip(sale, 0, 1)


def noche_americana(c: np.ndarray) -> np.ndarray:
    lin = _lin(c) * 0.32
    lin = _sat(lin, 0.45) * np.array([0.72, 0.9, 1.3], np.float32)
    lin = lin / (1 + lin * 0.8)   # las luces contenidas: la luna, no el sol
    return np.clip(_gam(lin) * 0.95 + np.array([0.0, 0.01, 0.035], np.float32), 0, 1)


def infrarroja(c: np.ndarray) -> np.ndarray:
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    # Lo que vería el infrarrojo, adivinado desde lo visible: la vegetación (más verde que el promedio de rojo y azul)
    # y lo rojo lo reflejan mucho (por eso lo rojo sale amarillo); el cielo (más azul que rojo) casi nada.
    vegetacion = np.clip((g - 0.5 * (r + b)) * 4.0, 0, 1)
    cielo = np.clip((b - r) * 3.0, 0, 1)
    nir = np.clip(0.8 * r + 0.15 * g + 0.9 * vegetacion, 0, 1) * (1 - 0.8 * cielo)
    # La película: la capa del infrarrojo da el rojo, la del rojo el verde, la del verde el azul (sin azul: filtro amarillo).
    sale = np.stack([nir, r * 0.9, g * 0.85], -1)
    return np.clip(_sat(sale, 1.15), 0, 1)


def blanqueo_saltado(c: np.ndarray) -> np.ndarray:
    y = (c @ LUMA)[..., None]
    gris = np.repeat(y, 3, axis=-1)
    # La plata encima del color: el color mezclado con su luz en «superponer».
    sobre = np.where(c < 0.5, 2 * c * gris, 1 - 2 * (1 - c) * (1 - gris))
    sale = _sat(c * 0.35 + sobre * 0.65, 0.55)
    return np.clip((sale - 0.5) * 1.15 + 0.5, 0, 1)


def proceso_cruzado(c: np.ndarray) -> np.ndarray:
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    curva = lambda x, k: 1 / (1 + np.exp(-k * (x - 0.5)))   # noqa: E731
    norm = lambda x, k: (curva(x, k) - curva(0, k)) / (curva(1, k) - curva(0, k))   # noqa: E731
    sale = np.stack([norm(r, 7.0), norm(g, 5.0) * 0.95 + 0.04, 0.18 + 0.58 * b], -1)
    return np.clip(_sat(sale, 1.2), 0, 1)


DESCRIPCION = {
    "noche-de-curiana": "la paleta de la marca: sombras al índigo, luces al oro de arena",
    "noche-americana": "la noche filmada de día: subexpuesta, desaturada y azul",
    "infrarroja": "la película infrarroja de falso color: la vegetación roja, el cielo oscuro",
    "blanqueo-saltado": "el revelado sin blanqueo: desaturado, duro y metálico",
    "proceso-cruzado": "la diapositiva revelada como negativo: luces amarillo verdosas, sombras cian",
}
TABLAS = {"noche-de-curiana": noche_de_curiana, "noche-americana": noche_americana, "infrarroja": infrarroja,
          "blanqueo-saltado": blanqueo_saltado, "proceso-cruzado": proceso_cruzado}

POR_DEFECTO = {"color": {"tabla": "noche-de-curiana", "archivo": "", "fuerza": 1.0}}
RANGOS = {"color": {"tabla": (*TABLAS, "archivo"), "fuerza": (0, 1)}}


# ── Las tablas: escribirlas, leerlas, aplicarlas ────────────────────────────

def grilla(n: int = TAMANO) -> np.ndarray:
    """Los colores de entrada de una tabla de lado n, como [r][g][b] → (n, n, n, 3)."""
    x = np.linspace(0, 1, n, dtype=np.float32)
    r, g, b = np.meshgrid(x, x, x, indexing="ij")
    return np.stack([r, g, b], -1)


def ruta_cube(texto: str) -> Path:
    r = Path(texto)
    return r if r.is_absolute() else A.MEDIOS / r


def leer_cube(ruta: Path) -> np.ndarray:
    """Un `.cube` 3D → (n, n, n, 3) indexada [r][g][b]. En el archivo el rojo cambia más rápido."""
    n = None
    minimo, maximo = np.zeros(3, np.float32), np.ones(3, np.float32)
    datos = []
    for linea in Path(ruta).read_text(encoding="utf-8", errors="replace").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        partes = linea.split()
        clave = partes[0].upper()
        if clave == "LUT_3D_SIZE":
            n = int(partes[1])
        elif clave == "LUT_1D_SIZE":
            raise ValueError("es una tabla 1D: la mesa lee tablas 3D")
        elif clave == "DOMAIN_MIN":
            minimo = np.array([float(v) for v in partes[1:4]], np.float32)
        elif clave == "DOMAIN_MAX":
            maximo = np.array([float(v) for v in partes[1:4]], np.float32)
        elif clave in ("TITLE", "LUT_3D_INPUT_RANGE", "LUT_1D_INPUT_RANGE"):
            continue
        else:
            try:
                datos.append([float(v) for v in partes[:3]])
            except ValueError:
                continue
    if n is None:
        raise ValueError("no dice LUT_3D_SIZE")
    if len(datos) != n ** 3:
        raise ValueError(f"tiene {len(datos)} colores y LUT_3D_SIZE {n} pide {n ** 3}")
    if np.any(minimo != 0) or np.any(maximo != 1):
        # El dominio dice qué colores de ENTRADA cubre la grilla; casi todas las tablas usan 0–1.
        raise ValueError(f"su dominio de entrada es {minimo.tolist()}–{maximo.tolist()}: la mesa lee tablas de 0 a 1")
    tabla = np.array(datos, np.float32).reshape(n, n, n, 3).transpose(2, 1, 0, 3)   # [b][g][r] → [r][g][b]
    return np.clip(tabla, 0, 1)


def escribir_cube(tabla: np.ndarray, destino, titulo: str) -> None:
    n = tabla.shape[0]
    filas = tabla.transpose(2, 1, 0, 3).reshape(-1, 3)   # el rojo cambia más rápido
    texto = [f'TITLE "{titulo}"', f"LUT_3D_SIZE {n}", "DOMAIN_MIN 0.0 0.0 0.0", "DOMAIN_MAX 1.0 1.0 1.0"]
    texto += [f"{r:.6f} {g:.6f} {b:.6f}" for r, g, b in filas]
    contenido = "\n".join(texto) + "\n"
    if destino == "-":
        print(contenido, end="")
    else:
        Path(destino).write_text(contenido, encoding="utf-8")


_TABLAS: dict = {}


def tabla_de(p: dict, n: int = TAMANO) -> np.ndarray:
    """La tabla del paso: una de la mesa (escrita en su grilla) o la del archivo. Se guarda: escribirla cuesta."""
    if p["tabla"] == "archivo":
        ruta = ruta_cube(p["archivo"])
        clave = ("archivo", str(ruta), ruta.stat().st_mtime)
    else:
        clave = (p["tabla"], n)
    if clave not in _TABLAS:
        _TABLAS[clave] = leer_cube(ruta) if p["tabla"] == "archivo" else np.clip(TABLAS[p["tabla"]](grilla(n)), 0, 1).astype(np.float32)
    return _TABLAS[clave]


def aplicar(img: np.ndarray, tabla: np.ndarray) -> np.ndarray:
    """Cada pixel por la tabla, interpolando entre los ocho puntos de la grilla que lo rodean."""
    n = tabla.shape[0]
    x = np.clip(img, 0, 1) * (n - 1)
    i0 = np.minimum(np.floor(x).astype(np.int32), n - 2)
    f = x - i0
    r0, g0, b0 = i0[..., 0], i0[..., 1], i0[..., 2]
    fr, fg, fb = f[..., 0:1], f[..., 1:2], f[..., 2:3]
    c = lambda dr, dg, db: tabla[r0 + dr, g0 + dg, b0 + db]   # noqa: E731
    c00 = c(0, 0, 0) * (1 - fr) + c(1, 0, 0) * fr
    c10 = c(0, 1, 0) * (1 - fr) + c(1, 1, 0) * fr
    c01 = c(0, 0, 1) * (1 - fr) + c(1, 0, 1) * fr
    c11 = c(0, 1, 1) * (1 - fr) + c(1, 1, 1) * fr
    c0 = c00 * (1 - fg) + c10 * fg
    c1 = c01 * (1 - fg) + c11 * fg
    return (c0 * (1 - fb) + c1 * fb).astype(np.float32)


# ── El aparato ──────────────────────────────────────────────────────────────

def errores(nombre: str, a: dict) -> list[str]:
    if a.get("tabla") != "archivo":
        return []
    archivo = a.get("archivo", "")
    if not isinstance(archivo, str) or not archivo:
        return ["color: con `tabla: archivo` hace falta `archivo` (un .cube)"]
    ruta = ruta_cube(archivo)
    if not ruta.is_file():
        return [f"color: no encuentro {archivo} (ni como ruta ni dentro de los medios)"]
    try:
        leer_cube(ruta)
    except ValueError as e:
        return [f"color: {archivo}: {e}"]
    return []


def calentar(pasos, fps: float, solo: int | None = None) -> int:
    return 0


def color(img: np.ndarray, p: dict, ctx) -> np.ndarray:
    f = float(p["fuerza"])
    if f <= 0:
        return img
    sale = aplicar(img, tabla_de(p))
    return sale if f >= 1 else (img * (1 - f) + sale * f).astype(np.float32)


APARATOS = {"color": color}


def cmd(a) -> None:
    """`python montaje.py color …`: listar las tablas, escribirlas a .cube o pasarlas a la consola en JSON."""
    import json

    if a.exportar:
        nombre, destino = a.exportar
        p = {"tabla": "archivo", "archivo": nombre} if nombre.lower().endswith(".cube") else {"tabla": nombre, "archivo": ""}
        if p["tabla"] != "archivo" and p["tabla"] not in TABLAS:
            A.salir(f"no hay una tabla «{nombre}» (las tablas: {', '.join(TABLAS)})")
        escribir_cube(tabla_de(p, a.tamano), destino, f"montaje · {nombre}")
        if destino != "-":
            print(f"→ {destino}")
        return
    if a.json:
        nombre = a.json
        p = {"tabla": "archivo", "archivo": nombre} if nombre.lower().endswith(".cube") else {"tabla": nombre, "archivo": ""}
        if p["tabla"] != "archivo" and p["tabla"] not in TABLAS:
            A.salir(f"no hay una tabla «{nombre}»")
        mal = errores("color", p)
        if mal:
            A.salir(mal[0])
        t = tabla_de(p, a.tamano)
        filas = t.transpose(2, 1, 0, 3).reshape(-1)   # el rojo cambia más rápido, como la textura 3D del navegador
        print(json.dumps({"n": int(t.shape[0]), "datos": [round(float(v), 4) for v in filas]}))
        return
    for nombre in TABLAS:
        print(f"{nombre:<20} {DESCRIPCION[nombre]}")
    print("archivo              un .cube de otro editor (`archivo`: ruta o dentro de los medios)")
