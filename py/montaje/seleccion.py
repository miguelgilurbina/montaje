"""Elegir el material antes de editar: la mesa de selección.

Cuando hay más clips que los que un video puede llevar, Miguel elige a mano. Esto le
prepara la mesa: de cada clip de las carpetas del proyecto saca una **muestra** muda y
liviana y un **cuadro fijo**, lo mide (nitidez, temblor, movimiento) y le pone un **grupo**
por su nombre (mar, campo, gente, ciudad, historia, petróleo, ficción) para poder filtrar.
No decide nada y no toca los originales.

    python montaje.py seleccion <p>

Deja `<biblioteca>/seleccion/` (muestras y cuadros) y `<biblioteca>/analisis/seleccion-<p>.json`.
Lo elegido se guarda en `proyectos/<p>/seleccion.json` (`{"elegidos": ["id", …]}`): desde que
ese archivo existe, el proyecto sólo ve esos clips (`clips.de_este_proyecto`).
"""

from __future__ import annotations

import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from . import clips as catalogo_clips
from .rutas import Proyecto, escribir_json, leer_json, salir

#: En orden: el primero que calza gana (un «slice of life in Caracas» es ciudad antes que gente).
GRUPOS = [
    ("ficción", r"sci-?fi|spaceship|spacial|martian|cyborg|cyberpunk|psychedelic|vortex|futuris|8bit|fibonacci|podcast|witches|surre|portal|eyes|sickly|"
                r"operating|tuareg|album|intergalactic|3d.graphics|enhancement|kissing"),
    ("petróleo", r"\boil\b|morbid"),
    ("historia", r"arawak|ind.?genous|ind.?gena|idigenous|prehispanic|spanish|juan.de|carabobo|curiana|medieval"),
    ("ciudad", r"caracas|\bmetro\b|tokyo|\bcity\b|street"),
    ("mar", r"boat|fishing|curiara|canoe|ocean|\bsea\b|carib|coast|crab|lancha|playa|pesquero"),
    ("campo", r"\btree|palm|vista|panoram|country|horse|ciclist|campo|guacamaya|birds|flamenco|burro|chivo"),
    ("gente", r"slice.of.life|\bmen\b|woman|women|\bman\b|character|cafe|portrait|cooking|quintet|stilt|person|diner|arepera|hamaca|chinchorro"),
]


def grupo_de(texto: str) -> str:
    t = texto.lower()
    return next((nombre for nombre, patron in GRUPOS if re.search(patron, t)), "otros")


def _muestra(origen: Path, video: Path, cuadro: Path, duracion: float) -> None:
    """Cinco segundos mudos a 360 de alto y un cuadro del medio: lo justo para reconocer el clip en un teléfono."""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-t", "5", "-i", str(origen), "-an", "-vf", "scale=-2:360:flags=lanczos,fps=24",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "31", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{min(1.5, duracion / 2):.2f}", "-i", str(origen), "-frames:v", "1",
                    "-vf", "scale=420:-2:flags=lanczos", "-q:v", "6", str(cuadro)], check=True)


def _uno(p: Proyecto, f: Path, prompts: dict[str, str], ya_usados: set[str]) -> dict:
    rel = f.relative_to(p.medios).as_posix()
    video, cuadro = p.medio("seleccion", f.stem + ".mp4"), p.medio("seleccion", f.stem + ".jpg")
    s = catalogo_clips._sondear(f)
    if not video.exists() or not cuadro.exists():
        _muestra(f, video, cuadro, s["duracion"])
    cu = catalogo_clips._curvas(catalogo_clips._cuadros(f, s["w"], s["h"]))
    texto = prompts.get(f.name) or f.stem.replace("-", " ")
    return {
        "id": f.stem, "src": rel, "prompt": texto, "grupo": grupo_de(texto), "w": s["w"], "h": s["h"], "duracion": round(s["duracion"], 2),
        "usado": rel in ya_usados,
        "nitidez": round(float(np.median(cu["nit"])) * 100, 2),
        "temblor": round(float(np.median(cu["temblor"])), 3),
        "movimiento": round(float(np.median(cu["mov"])) * 20, 2),
    }


def preparar(p: Proyecto) -> Path:
    archivos = sorted(f for o in catalogo_clips.carpetas(p) for f in o.iterdir() if f.is_file() and f.suffix.lower() in catalogo_clips.EXTENSIONES)
    if not archivos:
        salir("el proyecto no tiene clips que seleccionar")
    prompts: dict[str, str] = {}
    mapa = p.medios / "analisis" / "clips-mj.json"
    if mapa.exists():
        prompts = {x["archivo"]: x["prompt"] for x in leer_json(mapa)}
    # Lo que ya entró en un video de esta biblioteca, para que se vea al elegir.
    catalogo = catalogo_clips.ruta_catalogo(p)
    ya_usados = {c["src"] for c in leer_json(catalogo)["clips"]} if catalogo.exists() else set()
    with ThreadPoolExecutor(max_workers=6) as hilos:
        filas = list(hilos.map(lambda f: _uno(p, f, prompts, ya_usados), archivos))
    filas.sort(key=lambda c: ([*(g for g, _ in GRUPOS[::-1]), "otros"].index(c["grupo"]), c["id"]))
    destino = p.medio("analisis", f"seleccion-{p.nombre}.json")
    escribir_json(destino, {"proyecto": p.nombre, "candidatos": filas})
    cuenta: dict[str, int] = {}
    for c in filas:
        cuenta[c["grupo"]] = cuenta.get(c["grupo"], 0) + 1
    print(f"{len(filas)} candidatos: " + ", ".join(f"{k} {v}" for k, v in sorted(cuenta.items(), key=lambda x: -x[1])))
    print(f"→ {destino}\n→ {p.medios / 'seleccion'}")
    return destino


def guardar(p: Proyecto, elegidos: list[str]) -> Path:
    """Escribe lo que Miguel eligió. Desde ahí, el proyecto sólo ve esos clips."""
    destino = p.dir / "seleccion.json"
    escribir_json(destino, {"elegidos": sorted(set(elegidos))})
    return destino
