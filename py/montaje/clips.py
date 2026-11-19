"""Los clips de un proyecto: copias de trabajo, lo que pasa en cada uno, y una hoja para verlo.

Claude no ve un clip correr. Lo lee como curvas, diez veces por segundo:

- **movimiento**: cuánto cambia la imagen de un instante al siguiente, descontado
  el movimiento de la cámara (lo que se mueve dentro del cuadro: alguien que camina,
  una mano, el pelo con el viento);
- **cámara**: cuánto se desplaza el cuadro entero (paneo, caminar con el teléfono) y
  cuánto **tiembla** (lo que queda de ese desplazamiento después de suavizarlo);
- **nitidez**: el detalle fino (la varianza del laplaciano), que cae con el foco
  perdido y con el barrido de un movimiento rápido;
- **luz**, y los **cortes** si el clip ya viene editado;
- **centro** (`cx`, `cy`): dónde está lo que importa en el cuadro (lo que se mueve y
  lo que tiene detalle), para que un recorte a otro formato siga al sujeto.

Con eso `mejor_tramo` elige qué segundos de cada clip van en el montaje: nítidos,
sin temblor, lejos del arranque y el final de la toma, y con el movimiento que pide
la música en ese momento.

Con `clips_interpolar`, `clips` hace sólo un **borrador** (`borradores/`, sin inventar cuadros) y
las curvas salen de ahí; la copia interpolada espera al render final y sólo de lo que quedó en el
video (`asegurar_copias`). El preview dibuja el borrador en lugar de la copia que falta.

Las copias de trabajo (`proxies/`) son lo que dibuja Remotion: H.264 a 1080 como
mucho, cuadros parejos (30 o 60 por segundo, según el original), girados como se
ven en el teléfono, en rango normal (el HDR del teléfono se lleva a SDR: si no, se
ve lavado) y con un cuadro clave cada medio segundo para que saltar a cualquier
punto sea rápido. **Los originales no se tocan.**

proyecto.json:

    "clips": "clips"          # carpeta de los clips, relativa a la biblioteca
    "fotos": "fotos"          # opcional: fotos que entran al mismo montaje (una carpeta o varias)

Las **fotos** entran al catálogo como clips quietos (`"foto": true`): no llevan copia
de trabajo (Remotion dibuja la imagen) y de sus curvas sólo importan la nitidez, la
luz y el centro de interés. El movimiento se lo da el montaje: un acercamiento lento
(`pulso` con `mezclar_fotos`).
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from .rutas import Proyecto, escribir_json, leer_json, salir

#: Clips que se copian a la vez. Medido el 2026-11-09 en 16 hilos: 4 rinden 2,3 veces una sola; 8, 2,8; 12, lo mismo que 8.
A_LA_VEZ = 8
EXTENSIONES = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".3gp", ".mts"}
FOTOS = {".jpg", ".jpeg", ".png", ".webp"}
#: Segundos que «dura» una foto para el reparto (cuánto material cuenta); en pantalla dura lo que su frase.
SEGUNDOS_FOTO = 6.0
#: Lado mayor de las copias de trabajo (px).
LADO_PROXY = 1920
#: Muestras por segundo del análisis, y ancho de los cuadros que se analizan (px).
HZ = 10
ANCHO_ANALISIS = 192
#: Segundos del arranque y del final de cada toma que no se usan (el pulgar en el botón).
BORDE_TOMA = 0.35
HDR = {"arib-std-b67", "smpte2084"}


# ── Lectura de un archivo ──────────────────────────────────────────────────

def _sondear(ruta: Path) -> dict:
    """Lo que ffprobe sabe del archivo: duración, tamaño ya girado, cuadros por segundo, color y fecha."""
    salida = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(ruta)],
        capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout
    info = json.loads(salida)
    video = next((s for s in info["streams"] if s.get("codec_type") == "video" and not s.get("disposition", {}).get("attached_pic")), None)
    if video is None:
        salir(f"{ruta.name} no tiene video")
    audio = any(s.get("codec_type") == "audio" for s in info["streams"])
    giro = 0
    for lado in video.get("side_data_list", []):
        if "rotation" in lado:
            giro = int(round(float(lado["rotation"])))
    if "rotate" in video.get("tags", {}):
        giro = -int(video["tags"]["rotate"])
    w, h = int(video["width"]), int(video["height"])
    if abs(giro) % 180 == 90:
        w, h = h, w
    num, den = (video.get("avg_frame_rate") or video.get("r_frame_rate") or "30/1").split("/")
    fps = float(num) / float(den) if float(den) else 30.0
    duracion = float(info["format"].get("duration") or video.get("duration") or 0)
    etiquetas = {**info["format"].get("tags", {}), **video.get("tags", {})}
    fecha = etiquetas.get("com.apple.quicktime.creationdate") or etiquetas.get("creation_time")
    return {
        "w": w,
        "h": h,
        "fps": fps,
        "duracion": duracion,
        "audio": audio,
        "codec": video.get("codec_name"),
        "hdr": video.get("color_transfer") in HDR,
        "transfer": video.get("color_transfer"),
        "fecha": fecha,
    }


def _medidas_proxy(w: int, h: int) -> tuple[int, int]:
    k = min(1.0, LADO_PROXY / max(w, h))
    par = lambda v: max(2, int(round(v * k / 2)) * 2)  # noqa: E731
    return par(w), par(h)


CADENCIAS = (23.976, 24, 25, 29.97, 30, 48, 50, 59.94, 60)


def _cadencia(fps: float) -> float:
    """La cadencia estándar más cercana (un teléfono graba a cuadros variables: 29.93, 30.02…)."""
    # Sobre 61 ya no es un teléfono con cuadros variables: es material que viene interpolado (72, 90, 120) y se respeta.
    return min(CADENCIAS, key=lambda c: abs(c - fps)) if fps <= 61 else round(fps, 3)


def _hacer_proxy(origen: Path, destino: Path, s: dict, interpolar: int = 1) -> None:
    """La copia de trabajo: girada, en SDR, a cuadros parejos (los del original) y fácil de recorrer.

    `interpolar` (2, 3…): inventa los cuadros intermedios (`minterpolate`) para que la
    cámara lenta no trabe: a 24 cps con `interpolar: 2`, la mitad de velocidad sigue
    teniendo un cuadro distinto en cada cuadro del video.
    """
    pw, ph = _medidas_proxy(s["w"], s["h"])
    fps = _cadencia(s["fps"])
    filtros = []
    if s["hdr"]:
        # HDR del teléfono (HLG o PQ) a SDR BT.709: lineal, gama de color, tonemap y vuelta.
        filtros += [
            "zscale=t=linear:npl=100",
            "format=gbrpf32le",
            "zscale=p=bt709",
            "tonemap=tonemap=hable:desat=0",
            "zscale=t=bt709:m=bt709:r=tv",
        ]
    filtros += [f"scale={pw}:{ph}:flags=lanczos", f"fps={fps}"]
    # Lo que ya viene a más de 61 cps (un clip transformado sale de una copia ya interpolada) no se interpola otra vez.
    if interpolar > 1 and s["fps"] <= 61:
        fps = min(120, round(fps * interpolar, 3))
        filtros.append(f"minterpolate=fps={fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1")
    filtros.append("format=yuv420p")
    orden = [
        "ffmpeg", "-y", "-v", "error", "-i", str(origen),
        "-map", "0:v:0", "-map", "0:a:0?",
        "-vf", ",".join(filtros),
        "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-g", str(max(1, int(fps // 2))),
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-c:a", "aac", "-b:a", "160k",
        "-movflags", "+faststart",
        str(destino),
    ]
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_suffix(".tmp.mp4")
    orden[-1] = str(temporal)
    subprocess.run(orden, check=True)
    temporal.replace(destino)


def _cuadros(ruta: Path, w: int, h: int, hz: float = HZ, ancho: int = ANCHO_ANALISIS) -> np.ndarray:
    """Los cuadros del clip en grises, chicos, `hz` por segundo: (n, alto, ancho) en 0..1."""
    alto = max(2, int(round(ancho * h / w / 2)) * 2)
    crudo = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(ruta), "-vf", f"fps={hz},scale={ancho}:{alto}:flags=area,format=gray",
         "-f", "rawvideo", "-"],
        capture_output=True, check=True,
    ).stdout
    n = len(crudo) // (ancho * alto)
    return np.frombuffer(crudo[: n * ancho * alto], dtype=np.uint8).reshape(n, alto, ancho).astype(np.float32) / 255


# ── Las curvas ─────────────────────────────────────────────────────────────

def _desplazamiento(a: np.ndarray, b: np.ndarray, ventana: np.ndarray) -> tuple[int, int]:
    """Cuánto se corrió el cuadro entero de `a` a `b` (correlación de fase), en px."""
    fa = np.fft.rfft2((a - a.mean()) * ventana)
    fb = np.fft.rfft2((b - b.mean()) * ventana)
    r = fa * np.conj(fb)
    r /= np.abs(r) + 1e-9
    c = np.fft.irfft2(r, s=a.shape)
    dy, dx = np.unravel_index(int(np.argmax(c)), c.shape)
    h, w = a.shape
    if dy > h // 2:
        dy -= h
    if dx > w // 2:
        dx -= w
    return int(dx), int(dy)


def _suavizar(x: np.ndarray, n: int) -> np.ndarray:
    if len(x) < 3 or n <= 1:
        return x.copy()
    nucleo = np.hanning(n + 2)[1:-1]
    nucleo /= nucleo.sum()
    return np.convolve(np.pad(x, (n // 2, n - 1 - n // 2), mode="edge"), nucleo, mode="valid")


def _curvas(cuadros: np.ndarray) -> dict:
    from scipy import ndimage

    n, h, w = cuadros.shape
    ventana = np.outer(np.hanning(h), np.hanning(w)).astype(np.float32)
    mov = np.zeros(n)
    total = np.zeros(n)
    dx = np.zeros(n)
    dy = np.zeros(n)
    for i in range(1, n):
        a, b = cuadros[i - 1], cuadros[i]
        total[i] = np.abs(b - a).mean()
        x, y = _desplazamiento(a, b, ventana)
        dx[i], dy[i] = x, y
        # Lo que cambió dentro del cuadro una vez descontado el paneo (sin los bordes que entran).
        m = max(abs(x), abs(y)) + 2
        if m * 2 < min(h, w):
            b_alineado = np.roll(b, (y, x), axis=(0, 1))
            mov[i] = np.abs(b_alineado[m:-m, m:-m] - a[m:-m, m:-m]).mean()
        else:
            mov[i] = total[i]
    if n > 1:
        mov[0], total[0], dx[0], dy[0] = mov[1], total[1], dx[1], dy[1]
    nit = np.array([ndimage.laplace(c).var() for c in cuadros])
    luz = cuadros.mean(axis=(1, 2))

    # El centro de interés de cada instante: detalle (laplaciano) y, el doble, movimiento;
    # suavizado en el espacio y elevado al cuadrado para que mande lo más fuerte.
    xs, ys = np.arange(w) / max(1, w - 1), np.arange(h) / max(1, h - 1)
    cx, cy = np.full(n, 0.5), np.full(n, 0.5)
    for i in range(n):
        detalle = np.abs(ndimage.laplace(cuadros[i]))
        cambio = np.abs(cuadros[i] - cuadros[i - 1]) if i else np.zeros_like(detalle)
        mapa = ndimage.gaussian_filter(detalle / (detalle.mean() + 1e-6) + 2 * cambio / (cambio.mean() + 1e-6), 4) ** 2
        total_mapa = mapa.sum()
        if total_mapa > 0:
            cx[i] = float((mapa.sum(axis=0) * xs).sum() / total_mapa)
            cy[i] = float((mapa.sum(axis=1) * ys).sum() / total_mapa)
    cx, cy = _suavizar(cx, 9), _suavizar(cy, 9)

    # Cámara: el paneo como fracción del ancho por segundo; el temblor, lo que el suavizado no explica.
    vx, vy = dx / w * HZ, dy / w * HZ
    camara = np.hypot(_suavizar(vx, 7), _suavizar(vy, 7))
    temblor = np.hypot(vx - _suavizar(vx, 7), vy - _suavizar(vy, 7))

    # Cortes: un cambio total muy por encima de lo habitual en el clip.
    base = np.median(total) + 1e-4
    cortes = [i / HZ for i in range(1, n) if total[i] > max(0.12, 8 * base) and total[i] > 2.5 * max(total[i - 1], total[min(n - 1, i + 1)])]
    return {"mov": mov, "camara": camara, "temblor": temblor, "nit": nit, "luz": luz, "cx": cx, "cy": cy, "cortes": cortes}


def _color(ruta: Path, w: int, h: int, duracion: float) -> dict:
    """Color medio del clip (de 12 cuadros repartidos): tono, saturación y luz, como el catálogo de imágenes."""
    import colorsys

    hz = min(4.0, 12 / max(duracion, 0.5))
    alto = max(2, int(round(64 * h / w / 2)) * 2)
    crudo = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(ruta), "-vf", f"fps={hz},scale=64:{alto}:flags=area,format=rgb24", "-f", "rawvideo", "-"],
        capture_output=True, check=True,
    ).stdout
    rgb = np.frombuffer(crudo, dtype=np.uint8).reshape(-1, 3).astype(float) / 255
    media = rgb.mean(axis=0)
    tono, luz, sat = colorsys.rgb_to_hls(*media)
    return {"rgb": [round(float(v), 3) for v in media], "tono": round(tono * 360, 1), "sat": round(sat, 3), "luz": round(luz, 3)}


# ── El catálogo de clips ───────────────────────────────────────────────────

def carpetas(p: Proyecto) -> list[Path]:
    """Las carpetas de clips del proyecto: una (`"clips": "clips"`) o varias (`["clips", "transformados"]`)."""
    rel = p.cfg.get("clips")
    if not rel:
        salir('el proyecto no dice dónde están sus clips: agrega "clips": "<carpeta>" (relativa a la biblioteca)')
    rutas = [p.medios / r for r in ([rel] if isinstance(rel, str) else rel)]
    for ruta in rutas:
        if not ruta.is_dir():
            salir(f"no existe la carpeta de clips {ruta}")
    return rutas


def ruta_catalogo(p: Proyecto) -> Path:
    return p.medios / "analisis" / "clips.json"


def _prefijos(p: Proyecto) -> tuple[str, ...]:
    """Las carpetas de clips del proyecto como comienzo de ruta («clips/», «transformados/»)."""
    carpetas_ = []
    for clave in ("clips", "fotos"):
        rel = p.cfg.get(clave)
        carpetas_ += [rel] if isinstance(rel, str) else rel or []
    return tuple(str(r).replace("\\", "/").strip("/") + "/" for r in carpetas_)


def _foto(p: Proyecto, f: Path, rel: str, firma: list) -> dict:
    """Una foto como entrada del catálogo de clips: quieta, sin copia de trabajo, con su nitidez, su luz y su centro de interés."""
    import colorsys

    from PIL import Image, ImageOps

    with Image.open(f) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")  # como se ve: girada según la cámara
        w, h = im.size
        alto = max(2, int(round(ANCHO_ANALISIS * h / w / 2)) * 2)
        gris = np.asarray(im.convert("L").resize((ANCHO_ANALISIS, alto), Image.LANCZOS), dtype=np.float32) / 255
        media = np.asarray(im.resize((64, max(2, round(64 * h / w))), Image.BOX), dtype=float).reshape(-1, 3).mean(axis=0) / 255
    # Las mismas curvas que un clip, de doce cuadros iguales: movimiento y cámara en cero.
    cur = _curvas(np.stack([gris] * 12))
    tono, luz, sat = colorsys.rgb_to_hls(*media)
    clip = {
        "id": f.stem, "src": rel, "proxy": rel, "foto": True, "firma": firma, "w": w, "h": h, "ratio": round(w / h, 4), "fps": 0,
        "duracion": SEGUNDOS_FOTO, "audio": False, "hdr": False, "fecha": None,
        "color": {"rgb": [round(float(v), 3) for v in media], "tono": round(tono * 360, 1), "sat": round(sat, 3), "luz": round(luz, 3)},
        "hz": HZ, "curvas": {k: [round(float(v), 5) for v in cur[k]] for k in ("mov", "camara", "temblor", "nit", "luz", "cx", "cy")}, "cortes": [],
    }
    clip["resumen"] = _resumen(clip)
    return clip


def de_este_proyecto(p: Proyecto, clips: list[dict]) -> list[dict]:
    """Del catálogo de la biblioteca, lo que está en las carpetas de este proyecto.

    El catálogo es uno por biblioteca y lo comparten todos los experimentos que la usan: sin
    este filtro, sumar una carpeta en un experimento (los transformados, unas fotos) le
    cambiaba el reparto a todos los demás la próxima vez que se planificaran.
    """
    prefijos = _prefijos(p)
    propios = [c for c in clips if c["src"].startswith(prefijos)] if prefijos else clips
    elegidos = _elegidos(p)
    if elegidos is not None:
        propios = [c for c in propios if _es_elegido(c["id"], c["src"].startswith("transformados/"), elegidos)]
    return propios


def _elegidos(p: Proyecto) -> set[str] | None:
    """Lo que Miguel eligió en la mesa de selección (`proyectos/<p>/seleccion.json`); None si todavía no eligió."""
    eleccion = p.dir / "seleccion.json"
    return set(leer_json(eleccion)["elegidos"]) if eleccion.exists() else None


def _es_elegido(ident: str, transformado: bool, elegidos: set[str]) -> bool:
    """¿Es un clip elegido, o un transformado de uno elegido?"""
    return ident in elegidos or (transformado and any(ident.startswith(e + "-") for e in elegidos))


def copia_de(p: Proyecto, c: dict) -> Path:
    """La copia que se puede usar ahora: la interpolada si ya existe; si no, su borrador."""
    proxy = p.medios / c["proxy"]
    return proxy if proxy.exists() or c.get("foto") else p.medio("borradores", proxy.name)


def asegurar_copias(p: Proyecto, rutas: set[str]) -> None:
    """Las copias interpoladas que faltan de estas `rutas` («proxies/x.mp4»): para el final, sólo lo que quedó en el video."""
    if not rutas:
        # Un video sin clips del catálogo (modo planos: sus videos van directo de la biblioteca) no tiene catálogo que leer.
        return
    catalogo ={c["proxy"]: c for c in leer_json(ruta_catalogo(p))["clips"] if not c.get("foto")}
    faltan = [catalogo[r] for r in sorted(rutas) if r in catalogo and not (p.medios / r).exists()]
    if not faltan:
        return
    print(f"interpolando {len(faltan)} copias, {A_LA_VEZ} a la vez…", flush=True)

    def una(c: dict) -> None:
        origen = p.medios / c["src"]
        _hacer_proxy(origen, p.medios / c["proxy"], _sondear(origen), c["firma"][2])
        print(f"  ✓ {c['id']}", flush=True)

    with ThreadPoolExecutor(A_LA_VEZ) as pool:
        list(pool.map(una, faltan))


def analizar(p: Proyecto) -> Path:
    """Copias de trabajo, curvas y hojas de todos los clips. Lo ya hecho no se repite."""
    origenes = carpetas(p)
    archivos = sorted(f for o in origenes for f in o.iterdir() if f.is_file() and f.suffix.lower() in EXTENSIONES)
    if not archivos:
        salir(f"no hay clips en {', '.join(str(o) for o in origenes)}")
    # Con la elección hecha, sólo lo elegido: lo demás no tiene por qué esperar su copia.
    elegidos = _elegidos(p)
    if elegidos is not None:
        archivos = [f for f in archivos if _es_elegido(f.stem, f.parent.name == "transformados", elegidos)]
    destino = ruta_catalogo(p)
    previo = {c["src"]: c for c in leer_json(destino)["clips"]} if destino.exists() else {}

    interpolar = int(p.cfg.get("clips_interpolar", 1))

    def uno(f: Path) -> dict:
        rel = f.relative_to(p.medios).as_posix()
        # Los transformados salen de copias ya interpoladas: su copia no se interpola (y eso va en la firma).
        firma = [f.stat().st_size, int(f.stat().st_mtime), 1 if rel.startswith("transformados/") else interpolar]
        proxy = p.medio("proxies", f.stem + ".mp4")
        borrador = p.medio("borradores", f.stem + ".mp4")
        anterior = previo.get(rel)
        if anterior and anterior.get("firma") == firma and (proxy.exists() or borrador.exists()) and "cx" in anterior["curvas"]:
            print(f"  = {f.name}", flush=True)
            return anterior
        s = _sondear(f)
        print(f"  … {f.name}: {s['w']}×{s['h']}, {s['fps']:.2f} cps, {s['duracion']:.1f} s{', HDR→SDR' if s['hdr'] else ''}", flush=True)
        vencida = bool(anterior and anterior.get("firma") != firma)
        if firma[2] > 1 and s["fps"] <= 61:
            # Inventar cuadros es el 97 % del costo de una copia y un preview no los necesita: se hace
            # el borrador y la copia interpolada espera al final, sólo de lo que quedó (`asegurar_copias`).
            if proxy.exists() and (proxy.stat().st_mtime < f.stat().st_mtime or vencida):
                proxy.unlink()
            if not proxy.exists() and (not borrador.exists() or borrador.stat().st_mtime < f.stat().st_mtime or vencida):
                _hacer_proxy(f, borrador, s)
        elif not proxy.exists() or proxy.stat().st_mtime < f.stat().st_mtime or vencida:
            _hacer_proxy(f, proxy, s, firma[2])
        fuente = proxy if proxy.exists() else borrador
        sp = _sondear(fuente)
        pendiente = fuente == borrador
        cur = _curvas(_cuadros(fuente, sp["w"], sp["h"]))
        clip = {
            "id": f.stem,
            "src": rel,
            "proxy": proxy.relative_to(p.medios).as_posix(),
            "firma": firma,
            "w": sp["w"],
            "h": sp["h"],
            "ratio": round(sp["w"] / sp["h"], 4),
            # Lo que tendrá la copia interpolada, para que el plan no cambie cuando exista: inventar cuadros
            # le quita al clip casi dos cuadros del final (medido: 0,07 s a 24 cps).
            "fps": round(min(120, sp["fps"] * firma[2]) if pendiente else sp["fps"], 3),
            "duracion": round(sp["duracion"] - (2 / sp["fps"] if pendiente else 0), 3),
            "audio": s["audio"],
            "hdr": s["hdr"],
            "fecha": s["fecha"],
            "color": _color(fuente, sp["w"], sp["h"], sp["duracion"]),
            "hz": HZ,
            "curvas": {k: [round(float(v), 5) for v in cur[k]] for k in ("mov", "camara", "temblor", "nit", "luz", "cx", "cy")},
            "cortes": [round(t, 2) for t in cur["cortes"]],
        }
        clip["resumen"] = _resumen(clip)
        return clip

    with ThreadPoolExecutor(A_LA_VEZ) as pool:
        clips = list(pool.map(uno, archivos))

    # Las fotos del proyecto, si las pide: al mismo catálogo, como clips quietos.
    rel_fotos = p.cfg.get("fotos")
    for carpeta in ([rel_fotos] if isinstance(rel_fotos, str) else rel_fotos or []):
        if not (p.medios / carpeta).is_dir():
            salir(f"no existe la carpeta de fotos {p.medios / carpeta}")
        nuevas = 0
        for f in sorted(x for x in (p.medios / carpeta).iterdir() if x.is_file() and x.suffix.lower() in FOTOS):
            rel = f.relative_to(p.medios).as_posix()
            firma = [f.stat().st_size, int(f.stat().st_mtime), "foto"]
            anterior = previo.get(rel)
            if anterior and anterior.get("firma") == firma:
                clips.append(anterior)
            else:
                clips.append(_foto(p, f, rel, firma))
                nuevas += 1
        print(f"  fotos de {carpeta}/: {sum(c['src'].startswith(carpeta.strip('/') + '/') for c in clips)} ({nuevas} nuevas)")

    # El orden por fecha (la del teléfono si la hay; si no, el nombre).
    clips.sort(key=lambda c: (c["fecha"] or "~", c["id"]))
    # Lo que otros experimentos de la misma biblioteca tienen en otras carpetas se queda en el catálogo.
    vistos = {c["src"] for c in clips}
    # También lo que esta elección dejó afuera: otro experimento de la biblioteca puede estar usándolo.
    ajenos = [c for src, c in previo.items() if src not in vistos and (elegidos is not None or not src.startswith(_prefijos(p))) and copia_de(p, c).exists()]
    todos = sorted(clips + ajenos, key=lambda c: (c["fecha"] or "~", c["id"]))
    escribir_json(destino, {"generado": dt.datetime.now().isoformat(timespec="seconds"), "clips": todos})
    if ajenos:
        print(f"  (quedan en el catálogo {len(ajenos)} clips de otras carpetas de la biblioteca)")
    hojas = _hojas(p, [c for c in clips if not c.get("foto")])
    total = sum(c["duracion"] for c in clips if not c.get("foto"))
    print(f"{sum(not c.get('foto') for c in clips)} clips, {total:.0f} s de material, {sum(bool(c.get('foto')) for c in clips)} fotos → {destino}")
    for c in clips:
        if c.get("foto"):
            continue
        r = c["resumen"]
        forma = "vertical" if c["ratio"] < 0.9 else "horizontal" if c["ratio"] > 1.1 else "cuadrado"
        print(f"  {c['id'][:34]:34} {c['duracion']:5.1f} s  {forma:10}  movimiento {r['movimiento']:.2f}  "
              f"cámara {r['camara']:.2f}  temblor {r['temblor']:.2f}  nitidez {r['nitidez']:.2f}"
              f"{'  cortes ' + str(len(c['cortes'])) if c['cortes'] else ''}")
    print(f"→ {hojas}")
    return destino


def _resumen(c: dict) -> dict:
    """Números de todo el clip para comparar clips entre sí (medianas)."""
    cu = c["curvas"]
    return {
        "movimiento": round(float(np.median(cu["mov"])) * 20, 3),
        "camara": round(float(np.median(cu["camara"])), 3),
        "temblor": round(float(np.median(cu["temblor"])), 3),
        "nitidez": round(float(np.median(cu["nit"])) * 100, 3),
        "luz": round(float(np.mean(cu["luz"])), 3),
    }


def cargar(p: Proyecto) -> list[dict]:
    ruta = ruta_catalogo(p)
    if not ruta.exists():
        salir("falta el catálogo de clips; corre primero: python montaje.py clips " + p.nombre)
    return de_este_proyecto(p, leer_json(ruta)["clips"])


# ── Elegir qué segundos de un clip ─────────────────────────────────────────

def puntaje(c: dict, movimiento_buscado: float | None = None) -> np.ndarray:
    """Qué tan bueno es cada instante del clip (una muestra por 1/HZ s), en z (0 = lo típico del clip).

    Nítido suma; temblar resta; lo muy oscuro resta; si se pide un nivel de
    movimiento (0 quieto … 1 mucho), alejarse de él resta.
    """
    cu = c["curvas"]
    nit = np.array(cu["nit"])
    tem = np.array(cu["temblor"])
    luz = np.array(cu["luz"])
    mov = np.array(cu["mov"])
    z = lambda x: (x - np.median(x)) / (np.std(x) + 1e-9)  # noqa: E731
    s = 0.8 * z(np.log(nit + 1e-6)) - 1.0 * np.clip(z(tem), 0, None) - 2.0 * np.clip(0.12 - luz, 0, None) * 10
    if movimiento_buscado is not None:
        # El movimiento del clip llevado a 0..1 con los percentiles del propio clip.
        bajo, alto = np.percentile(mov, [10, 90])
        rel = np.clip((mov - bajo) / (alto - bajo + 1e-9), 0, 1)
        s -= 1.2 * np.abs(rel - movimiento_buscado)
    return s


def mejor_tramo(c: dict, largo: float, desde: float = 0.0, hasta: float | None = None,
                movimiento_buscado: float | None = None, evitar: list[tuple[float, float]] = (),
                borde: float = BORDE_TOMA) -> float:
    """El inicio (s) del mejor tramo de `largo` segundos dentro de [desde, hasta] del clip.

    El tramo no cruza un corte del clip, no toca el arranque ni el final de la toma
    y, si puede, no repite segundos ya usados (`evitar`). Si el clip es más corto que
    lo pedido, devuelve el mejor comienzo posible (el render lo congela al final).
    """
    if c.get("foto"):
        return 0.0  # una foto no tiene segundos que elegir
    hz = c["hz"]
    dur = c["duracion"]
    lo = max(desde, borde if dur > largo + 2 * borde else 0.0)
    hi = (hasta if hasta is not None else dur) - largo
    hi = min(hi, dur - largo - (borde if dur > largo + 2 * borde else 0.0))
    if hi <= lo:
        return round(max(0.0, min(lo, dur - largo)), 3) if dur > largo else 0.0
    s = puntaje(c, movimiento_buscado)
    acumulado = np.concatenate([[0.0], np.cumsum(s)])
    n = max(1, int(round(largo * hz)))
    mejor, mejor_t = -np.inf, lo
    for t in np.arange(lo, hi + 1e-9, 1 / hz):
        i = int(round(t * hz))
        j = min(len(s), i + n)
        if j <= i:
            continue
        valor = (acumulado[j] - acumulado[i]) / (j - i)
        if any(t < k < t + largo for k in c["cortes"]):
            valor -= 5
        solape = sum(max(0.0, min(t + largo, b) - max(t, a)) for a, b in evitar)
        valor -= 3 * solape / largo
        if valor > mejor:
            mejor, mejor_t = valor, float(t)
    return round(mejor_t, 3)


# ── Las hojas: el material a la vista ──────────────────────────────────────

def _hojas(p: Proyecto, clips: list[dict]) -> Path:
    """Una fila por clip: ocho cuadros y debajo sus curvas (movimiento, cámara, nitidez) y cortes."""
    from PIL import Image, ImageDraw, ImageFont

    try:
        letra = ImageFont.truetype("arial.ttf", 13)
    except OSError:
        letra = ImageFont.load_default()
    cuadros_por_fila, alto_cuadro, alto_curva, rotulo = 8, 150, 70, 22
    filas = []
    for c in clips:
        ancho_cuadro = int(round(alto_cuadro * c["ratio"]))
        fila = Image.new("RGB", (cuadros_por_fila * ancho_cuadro, rotulo + alto_cuadro + alto_curva), (14, 16, 20))
        d = ImageDraw.Draw(fila)
        d.text((6, 4), f"{c['id']} · {c['duracion']:.1f} s · {c['w']}x{c['h']} · {c['fps']:g} cps"
                       f"{' · cortes ' + ', '.join(f'{t:.1f}' for t in c['cortes']) if c['cortes'] else ''}",
               fill=(230, 222, 205), font=letra)
        for k in range(cuadros_por_fila):
            t = (k + 0.5) * c["duracion"] / cuadros_por_fila
            crudo = subprocess.run(
                ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(copia_de(p, c)), "-frames:v", "1",
                 "-vf", f"scale={ancho_cuadro}:{alto_cuadro}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                capture_output=True, check=True,
            ).stdout
            if len(crudo) == ancho_cuadro * alto_cuadro * 3:
                fila.paste(Image.frombytes("RGB", (ancho_cuadro, alto_cuadro), crudo), (k * ancho_cuadro, rotulo))
            d.text((k * ancho_cuadro + 4, rotulo + 3), f"{t:.1f}", fill=(255, 255, 255), font=letra)
        # Curvas: cada una normalizada a su propio rango en todo el catálogo.
        y0, W = rotulo + alto_cuadro, fila.width
        for nombre, color in (("nit", (243, 234, 212)), ("mov", (195, 103, 18)), ("camara", (33, 84, 197)), ("temblor", (182, 73, 36))):
            v = np.array(c["curvas"][nombre])
            todos = np.concatenate([np.array(x["curvas"][nombre]) for x in clips])
            bajo, alto = np.percentile(todos, [2, 98])
            v = np.clip((v - bajo) / (alto - bajo + 1e-9), 0, 1)
            puntos = [(i / max(1, len(v) - 1) * (W - 1), y0 + alto_curva - 4 - v[i] * (alto_curva - 8)) for i in range(len(v))]
            d.line(puntos, fill=color, width=2)
        for t in c["cortes"]:
            x = t / c["duracion"] * W
            d.line([(x, y0), (x, y0 + alto_curva)], fill=(230, 180, 60), width=2)
        filas.append(fila)
    ancho = max(f.width for f in filas)
    hoja = Image.new("RGB", (ancho, sum(f.height + 6 for f in filas) + 26), (8, 9, 12))
    d = ImageDraw.Draw(hoja)
    d.text((6, 6), "curvas: nitidez (hueso) · movimiento (ocre) · cámara (eléctrico) · temblor (rojo) · cortes (oro)", fill=(200, 200, 200), font=letra)
    y = 26
    for f in filas:
        hoja.paste(f, (0, y))
        y += f.height + 6
    destino = p.salida("hojas", "clips.png")
    hoja.save(destino)
    return destino
