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
    """Un experimento. Con `version`, una de las variantes con nombre de su `montaje`
    (`"versiones": {"b": {...}}` en proyecto.json): sus parámetros se suman a los del
    montaje (y su `sintesis`, si trae, reemplaza a la del proyecto) y su timeline es
    `timeline-<version>.json`, para comparar sin pisarse.

    Una versión también puede decir cómo se prueba (lo lee `ejercicio`): `prueba`
    ([desde, hasta] en segundos: el tramo que se renderiza), `estilo` (el id del
    estilo de la galería que muestra) y `muestra` ([desde, hasta] dentro de ese render)."""

    def __init__(self, nombre: str, version: str | None = None):
        self.nombre = nombre
        self.dir = PROYECTOS / nombre
        archivo = self.dir / "proyecto.json"
        if not archivo.exists():
            existentes = sorted(p.name for p in PROYECTOS.iterdir() if (p / "proyecto.json").exists())
            salir(f"no existe el proyecto «{nombre}». Hay: {', '.join(existentes) or 'ninguno'}")
        self.cfg = json.loads(archivo.read_text(encoding="utf-8"))
        self.medios = MEDIOS / self.cfg.get("biblioteca", nombre)
        self.salidas = MEDIOS / nombre
        self.version = version
        self.prueba: list[float] | None = None
        self.estilo: str | None = None
        self.muestra: list[float] | None = None
        if version:
            versiones = self.cfg.get("versiones", {})
            if version not in versiones:
                salir(f"«{nombre}» no tiene la versión «{version}». Tiene: {', '.join(versiones) or 'ninguna'}")
            propios = dict(versiones[version])
            # Cómo se prueba la versión no es una perilla del montaje.
            self.prueba, self.estilo, self.muestra = (propios.pop(k, None) for k in ("prueba", "estilo", "muestra"))
            # Una versión puede traer sus propias capas de síntesis y su propio lienzo
            # (reemplazan a los del proyecto): así un mismo tramo se prueba en 9:16, 1:1…
            for clave in ("sintesis", "salida"):
                if clave in propios:
                    self.cfg[clave] = propios.pop(clave)
            self.cfg["montaje"] = {**self.cfg.get("montaje", {}), **propios}

    @property
    def timeline(self) -> Path:
        return self.dir / (f"timeline-{self.version}.json" if self.version else "timeline.json")

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


def timeline_de(p: Proyecto) -> tuple[Proyecto, dict]:
    """El timeline que vale para un experimento: el suyo o, si se arma sobre otro
    (`base`), el del primero de la cadena que lo tenga (10 → 09 → 05)."""
    vistos = []
    while not p.timeline.exists():
        base = p.cfg.get("base")
        if not base or p.nombre in vistos:
            salir(f"ni {p.nombre} ni su cadena de `base` tienen timeline ({' → '.join(vistos + [p.nombre])})")
        vistos.append(p.nombre)
        p = Proyecto(base["proyecto"])
    return p, leer_json(p.timeline)


def escribir_json(ruta: Path, datos, compacto: bool = False) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if compacto:
        texto = json.dumps(datos, ensure_ascii=False, separators=(",", ":"))
    else:
        texto = json.dumps(datos, ensure_ascii=False, indent=1)
    ruta.write_text(texto + "\n", encoding="utf-8")
