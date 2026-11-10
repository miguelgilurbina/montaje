"""Traer de Cantera: las piezas de una serie, en su orden, a la biblioteca de un proyecto.

Cantera (repo hermano, `../cantera`) guarda y clasifica el material: series de Midjourney, clips, fotos,
documentos. Esto copia una serie a una carpeta de la biblioteca del proyecto, con el orden adelante del
nombre («03-pareja-en-la-playa.mp4»; las tomas numeradas de `tomas`, «T3-02 …», quedan como están):

    python montaje.py traer <p> --serie anoranza [--carpeta cantera-anoranza] [--tipo video]

Lo que ya estaba igual no se copia otra vez. Después: sumar la carpeta a `clips` en proyecto.json y
correr `clips <p>`. Cantera se busca en `CANTERA_DIR` o junto a este repo; sus datos, donde diga
`CANTERA_DATOS` (por defecto ~/Videos/cantera).
"""

from __future__ import annotations

import os
import re
import subprocess
import unicodedata
from pathlib import Path

from .rutas import RAIZ, Proyecto, salir


def carpeta_de(serie: str) -> str:
    a = unicodedata.normalize("NFKD", serie).encode("ascii", "ignore").decode().lower()
    return "cantera-" + (re.sub(r"[^a-z0-9]+", "-", a).strip("-") or "serie")


def traer(p: Proyecto, serie: str, carpeta: str | None = None, tipo: str | None = None) -> Path:
    cantera = Path(os.environ.get("CANTERA_DIR") or RAIZ.parent / "cantera")
    if not (cantera / "scripts" / "exportar.ts").exists():
        salir(f"no encuentro Cantera en {cantera} (ponla junto a montaje o dime dónde con CANTERA_DIR)")
    destino = p.medios / (carpeta or carpeta_de(serie))
    orden = ["node", "--disable-warning=ExperimentalWarning", "scripts/exportar.ts", "--serie", serie, "--a", str(destino)]
    if tipo:
        orden += ["--tipo", tipo]
    r = subprocess.run(orden, cwd=cantera)
    if r.returncode:
        salir("Cantera no pudo exportar la serie (arriba dice por qué)")
    rel = destino.relative_to(p.medios).as_posix()
    clips = p.cfg.get("clips")
    ya = rel in ([clips] if isinstance(clips, str) else clips or [])
    print(f"→ {destino}")
    if not ya:
        print(f'Para usarlos: suma "{rel}" a "clips" en proyectos/{p.nombre}/proyecto.json y corre `python montaje.py clips {p.nombre}`.')
    return destino
