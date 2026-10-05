"""Dónde vive cada cosa.

Dos raíces, a propósito separadas:

- El repo (en OneDrive) guarda lo que es decisión: proyecto.json, timeline.json
  y la FICHA.md de cada experimento.
- Los medios (fuera de OneDrive, ~/Videos/montaje; se cambia con la variable de
  entorno MONTAJE_MEDIOS) guardan lo pesado o regenerable, en dos niveles:
  - la **biblioteca** (`biblioteca` en proyecto.json): imágenes, miniaturas,
    audio y catálogo, compartidos por todos los experimentos que la usan;
  - las **salidas** de cada experimento (carpeta con su nombre): el análisis de
    su tramo de música, sus renders y sus hojas de contacto. Así un experimento
    nuevo nunca pisa lo que dejó otro.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PROYECTOS = RAIZ / "proyectos"
MEDIOS = Path(os.environ.get("MONTAJE_MEDIOS", Path.home() / "Videos" / "montaje"))


def salir(mensaje: str) -> None:
    raise SystemExit(f"montaje: {mensaje}")


class Proyecto:
    def __init__(self, nombre: str):
        self.nombre = nombre
        self.dir = PROYECTOS / nombre
        archivo = self.dir / "proyecto.json"
        if not archivo.exists():
            existentes = sorted(p.name for p in PROYECTOS.iterdir() if (p / "proyecto.json").exists())
            salir(f"no existe el proyecto «{nombre}». Hay: {', '.join(existentes) or 'ninguno'}")
        self.cfg = json.loads(archivo.read_text(encoding="utf-8"))
        self.medios = MEDIOS / self.cfg.get("biblioteca", nombre)
        self.salidas = MEDIOS / nombre

    @property
    def timeline(self) -> Path:
        return self.dir / "timeline.json"

    def medio(self, *partes: str) -> Path:
        """Ruta dentro de la biblioteca (imágenes, audio, catálogo), creando la carpeta madre."""
        ruta = self.medios.joinpath(*partes)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        return ruta

    def salida(self, *partes: str) -> Path:
        """Ruta dentro de las salidas propias del experimento (análisis, renders, hojas)."""
        ruta = self.salidas.joinpath(*partes)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        return ruta


def leer_json(ruta: Path):
    return json.loads(ruta.read_text(encoding="utf-8"))


def escribir_json(ruta: Path, datos, compacto: bool = False) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if compacto:
        texto = json.dumps(datos, ensure_ascii=False, separators=(",", ":"))
    else:
        texto = json.dumps(datos, ensure_ascii=False, indent=1)
    ruta.write_text(texto + "\n", encoding="utf-8")
