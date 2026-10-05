"""Ensamblar: un programa con interludios, como las cortinas de un canal de TV.

Miguel pensó sus videos de Curiana Radio hechos con Gemini como **interludios**,
«estilo las propagandas de Locomotion»: piezas con su propio sonido que cortan
el programa. Aquí no se re-renderiza nada: se toma el render de otro experimento
(el «programa»), se corta en compases y se intercalan los interludios con su
audio. La canción se detiene mientras pasa un interludio y retoma donde quedó.

Configuración en proyecto.json:

    "base": {"proyecto": "05-collage-curiana", "render": "curiana-3x2.mp4"},
    "ensamblaje": [
      {"interludio": "video/intro-gemini.mp4", "recorte": [280, 0, 720, 720]},
      {"programa": [0, 9]},           # compases [desde, hasta) del programa
      {"interludio": "video/logo-destellos.mp4", "recorte": [280, 0, 720, 720]},
      {"programa": [12, "fin"]}
    ]

Los interludios se recortan, se agrandan al alto del cuadro y se centran sobre
el fondo; su audio se nivela al volumen del programa (`loudnorm`), y cada empalme
lleva un fundido de audio cortísimo para que no chasquee.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import numpy as np

from .rutas import MEDIOS, Proyecto, leer_json, salir

FUNDIDO = 0.04  # segundos de fundido de audio en cada empalme


def _ffmpeg(*args: str) -> None:
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *args], capture_output=True, text=True)
    if r.returncode:
        salir(f"ffmpeg falló: {r.stderr.strip()[-800:]}")


def _sonoridad(ruta: Path) -> float:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(ruta), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True)
    for linea in reversed(r.stderr.splitlines()):
        if linea.strip().startswith("I:"):
            return float(linea.split()[1])
    salir(f"no pude medir la sonoridad de {ruta}")


def _compases(base: Proyecto) -> list[float]:
    """Comienzo de cada compás del programa (segundos del render) y su final."""
    m = leer_json(base.salidas / "analisis" / "musica.json")
    beats = np.array(m["beats"])
    inicios = [float(beats[i]) for i in range(m["fase_compas"], len(beats), 4)]
    inicios[0] = 0.0
    return inicios + [m["duracion"]]


def ensamblar(p: Proyecto) -> Path:
    cfg_base = p.cfg.get("base")
    if not cfg_base:
        salir("falta `base` (el proyecto y el render que hacen de programa)")
    base = Proyecto(cfg_base["proyecto"])
    programa = base.salidas / "render" / cfg_base["render"]
    if not programa.exists():
        salir(f"no existe el render del programa: {programa}")
    out = {"ancho": 1920, "alto": 1080, "fps": 30, "fondo": "#08080a", **p.cfg.get("salida", {})}
    W, H, fps, fondo = out["ancho"], out["alto"], out["fps"], out["fondo"].lstrip("#")
    compases = _compases(base)
    objetivo = _sonoridad(programa)

    partes = []
    with tempfile.TemporaryDirectory() as tmp:
        for k, paso in enumerate(p.cfg["ensamblaje"]):
            destino = Path(tmp) / f"parte{k:02d}.mp4"
            if "interludio" in paso:
                ruta = base.medios / paso["interludio"]
                if not ruta.exists():
                    salir(f"no existe el interludio {ruta}")
                sx, sy, sw, sh = paso.get("recorte", [0, 0, -1, -1])
                recorte = f"crop={sw}:{sh}:{sx}:{sy}," if sw > 0 else ""
                dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(ruta)], capture_output=True, text=True).stdout)
                video = f"{recorte}scale=-2:{H}:flags=lanczos,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x{fondo},fps={fps},format=yuv420p,setsar=1"
                audio = (
                    f"loudnorm=I={objetivo:.1f}:TP=-1.0:LRA=11,aresample=48000,"
                    f"afade=t=in:d={FUNDIDO},afade=t=out:st={dur - FUNDIDO:.3f}:d={FUNDIDO}"
                )
                _ffmpeg("-i", str(ruta), "-vf", video, "-af", audio, "-ac", "2", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-c:a", "aac", "-b:a", "256k", str(destino))
                partes.append((destino, f"interludio {paso['interludio']} ({dur:.1f} s)"))
            elif "programa" in paso:
                desde, hasta = paso["programa"]
                t0 = compases[desde]
                t1 = compases[-1] if hasta == "fin" else compases[hasta]
                dur = t1 - t0
                audio = f"afade=t=in:d={FUNDIDO},afade=t=out:st={dur - FUNDIDO:.3f}:d={FUNDIDO},aresample=48000"
                _ffmpeg(
                    "-ss", f"{t0:.3f}", "-i", str(programa), "-t", f"{dur:.3f}",
                    "-vf", f"fps={fps},format=yuv420p,setsar=1", "-af", audio, "-ac", "2",
                    "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-c:a", "aac", "-b:a", "256k", str(destino),
                )
                partes.append((destino, f"programa compases {desde}–{hasta} ({t0:.2f}–{t1:.2f} s, {dur:.1f} s)"))
            else:
                salir(f"paso de ensamblaje desconocido: {paso}")

        lista = Path(tmp) / "lista.txt"
        lista.write_text("".join(f"file '{d.as_posix()}'\n" for d, _ in partes), encoding="utf-8")
        nombre = p.cfg.get("nombre_salida", p.nombre)
        final = p.salida("render", f"{nombre}.mp4")
        _ffmpeg("-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", "-movflags", "+faststart", str(final))

    print(f"programa: {programa.name} ({objetivo:.1f} LUFS; los interludios se nivelan a eso)")
    for _, d in partes:
        print(f"  · {d}")
    print(f"→ {final}")
    return final
