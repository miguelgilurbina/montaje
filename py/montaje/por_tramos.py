"""El preview por tramos: corregir un tramo rehace sólo ese tramo.

Remotion dibuja cada cuadro en un navegador: un preview entero de una canción son minutos, y antes
se repetían enteros por un cambio chico. Aquí el video se parte por los tramos del guion (sin guion,
cada `LARGO_MAX` segundos) y cada pedazo se guarda con una huella de lo que lo dibuja: sus capas, las
capas de síntesis que lo tocan, los archivos que usan, los ajustes del render y el código de `src/`.
Si la huella ya está guardada, ese pedazo no se vuelve a dibujar. Después se cosen sin recomprimir y se
les pone la canción.

Sólo para previews: el final se dibuja entero, de corrido. Un video con sonido propio en alguna capa
(`volumen`) tampoco se parte, porque coser ese sonido dejaría saltos.
"""

from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path

from .rutas import RAIZ, Proyecto

LARGO_MAX = 45  # segundos: un tramo más largo se parte, para que corregir siga saliendo barato


def bordes(cfg: dict, fps: int, duracion: int) -> list[int]:
    """Los cuadros donde se parte el video, del 0 a `duracion`: los bordes de los tramos del guion."""
    marcas = {round(t[k] * fps) for t in cfg.get("montaje", {}).get("tramos") or [] for k in ("desde", "hasta") if t.get(k) is not None}
    base = sorted({0, duracion} | {m for m in marcas if 0 < m < duracion})
    salida: list[int] = []
    for a, b in zip(base, base[1:]):
        n = max(1, math.ceil((b - a) / (LARGO_MAX * fps)))
        salida += [a + (b - a) * i // n for i in range(n)]
    return salida + [duracion]


def _toca(capa: dict, a: int, b: int, duracion: int) -> bool:
    return capa.get("ini", 0) < b and capa.get("fin", duracion) > a


def _rutas(x, publico: Path, halladas: set[str]) -> None:
    """Las rutas de archivos que aparecen en una capa (con la misma idea que `cli._publico`)."""
    if isinstance(x, dict):
        for v in x.values():
            _rutas(v, publico, halladas)
    elif isinstance(x, list):
        for v in x:
            _rutas(v, publico, halladas)
    elif isinstance(x, str) and 0 < len(x) < 400 and not x.startswith(("#", "http")):
        try:
            if (publico / x).is_file():
                halladas.add(x)
        except (OSError, ValueError):  # un texto cualquiera no es una ruta
            pass


def huella_codigo() -> str:
    """El código que dibuja: si cambia, ningún pedazo guardado sirve."""
    h = hashlib.sha256()
    for f in sorted(p for p in (RAIZ / "src").rglob("*") if p.suffix in (".ts", ".tsx")):
        h.update(f.relative_to(RAIZ).as_posix().encode())
        h.update(f.read_bytes())
    return h.hexdigest()


def huella(tl: dict, a: int, b: int, publico: Path, ajustes: list[str], codigo: str) -> str:
    """Lo que hace falta saber para decir que el pedazo [a, b) saldría igual."""
    d = tl["duracion"]
    capas = [c for c in tl["capas"] if _toca(c, a, b, d)]
    sintesis = [s for s in tl.get("sintesis", []) if _toca(s, a, b, d)]
    resto = {k: v for k, v in tl.items() if k not in ("meta", "capas", "sintesis", "audio")}
    rutas: set[str] = set()
    _rutas(capas, publico, rutas)
    archivos = [[r, (publico / r).stat().st_size, int((publico / r).stat().st_mtime)] for r in sorted(rutas)]
    datos = {"a": a, "b": b, "capas": capas, "sintesis": sintesis, "resto": resto, "archivos": archivos, "ajustes": ajustes, "codigo": codigo}
    return hashlib.sha256(json.dumps(datos, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:20]


def tiene_sonido_propio(x) -> bool:
    if isinstance(x, dict):
        return bool(x.get("volumen")) or any(tiene_sonido_propio(v) for v in x.values())
    if isinstance(x, list):
        return any(tiene_sonido_propio(v) for v in x)
    return False


def _coser(p: Proyecto, tl: dict, piezas: list[Path], destino: Path) -> None:
    lista = destino.with_suffix(".lista.txt")
    lista.write_text("".join(f"file '{f.as_posix()}'\n" for f in piezas), encoding="utf-8")
    orden = ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lista)]
    au = tl.get("audio")
    if au:
        largo = tl["duracion"] / tl["fps"]
        entra, sale = au.get("fundido", [0, 0])
        desde = float(au.get("desde", 0))
        fin = float(au["hasta"]) if au.get("hasta") is not None else desde + largo
        fundidos = []
        if entra:
            fundidos.append(f"afade=t=in:st=0:d={entra}")
        if sale:
            fundidos.append(f"afade=t=out:st={fin - desde - sale}:d={sale}")
        orden += ["-ss", str(desde), "-t", str(min(largo, fin - desde)), "-i", str(p.medios / au["src"]), "-map", "0:v", "-map", "1:a"]
        orden += (["-af", ",".join(fundidos)] if fundidos else []) + ["-c:a", "aac", "-b:a", "192k"]
    orden += ["-c:v", "copy", "-movflags", "+faststart", str(destino)]
    subprocess.run(orden, check=True)
    lista.unlink()


def renderizar(p: Proyecto, tl: dict, destino: Path, publico: Path, remotion: str, ajustes: list[str]) -> None:
    """El preview entero: dibuja los pedazos que no estén guardados y los cose en `destino`."""
    guardados = p.salida("render", ".tramos", "x").parent
    marcas = bordes(p.cfg, tl["fps"], tl["duracion"])
    codigo = huella_codigo()
    piezas: list[Path] = []
    faltan: list[tuple[int, int, Path]] = []
    for a, b in zip(marcas, marcas[1:]):
        f = guardados / f"{huella(tl, a, b, publico, ajustes, codigo)}.mp4"
        piezas.append(f)
        if not f.exists():
            faltan.append((a, b, f))
    print(f"{len(piezas)} tramos: {len(piezas) - len(faltan)} guardados, {len(faltan)} por dibujar", flush=True)
    if faltan:
        # Una sola preparación para todos: por pedazo costaría varios segundos cada uno.
        paquete = p.salida("render", ".paquete", "x").parent
        shutil.rmtree(paquete, ignore_errors=True)
        subprocess.run([remotion, "bundle", "src/index.ts", f"--out-dir={paquete}", f"--public-dir={publico}", "--log=error"], cwd=RAIZ, check=True)
        for k, (a, b, f) in enumerate(faltan, 1):
            print(f"  dibujando {k}/{len(faltan)}: {a / tl['fps']:.1f}–{b / tl['fps']:.1f} s", flush=True)
            temporal = f.with_suffix(".tmp.mp4")
            orden = [remotion, "render", str(paquete), "Montaje", str(temporal), f"--props={p.timeline}", f"--frames={a}-{b - 1}", "--muted",
                     "--offthreadvideo-cache-size-in-bytes=1500000000", "--log=error", *ajustes]
            # Remotion a veces pierde un cuadro («Failed to fetch») y a la segunda sale.
            if subprocess.run(orden, cwd=RAIZ).returncode != 0:
                print("  (falló; una vez más)", flush=True)
                subprocess.run(orden, cwd=RAIZ, check=True)
            temporal.replace(f)
        shutil.rmtree(paquete, ignore_errors=True)
    _coser(p, tl, piezas, destino)
